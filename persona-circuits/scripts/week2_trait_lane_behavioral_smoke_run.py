"""Thin actual trait-lane screening runner using existing Week 2 kernels plus a small judge-smoke loop."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

try:
    from scripts.shared.behavioral_eval import (
        SlidingWindowRateLimiter,
        _format_chat_prompt,
        generate_response,
        judge_score,
    )
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
    )
    from scripts.week2_extract_persona_vectors import extract_vectors_remote
    from scripts.week2_extraction_position_ablation import run_position_ablation_remote
    from scripts.week2_extraction_robustness_bootstrap import extraction_robustness_remote
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.behavioral_eval import (
        SlidingWindowRateLimiter,
        _format_chat_prompt,
        generate_response,
        judge_score,
    )
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
    )
    from scripts.week2_extract_persona_vectors import extract_vectors_remote
    from scripts.week2_extraction_position_ablation import run_position_ablation_remote
    from scripts.week2_extraction_robustness_bootstrap import extraction_robustness_remote

APP_NAME = "persona-circuits-week2-trait-lane-behavioral-smoke"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_PROMPT_LIMIT = 4
DEFAULT_READINESS_PATTERN = "week2_trait_lane_screening_readiness_*.json"
DEFAULT_EXTRACTION_METHOD = "prompt_last"

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
REGISTRY_PATH = ROOT / "configs" / "trait_lanes_v2.yaml"

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        [
            "torch>=2.1.0",
            "transformers>=4.56.0,<=4.57.3",
            "sae-lens>=6.12.0",
            "transformer-lens>=1.11.0",
            "anthropic",
            "wandb",
            "numpy",
            "pyyaml",
        ]
    )
    .add_local_dir(ROOT / "scripts", remote_path="/root/scripts")
)


@dataclass(frozen=True)
class SmokeMetric:
    layer: int
    alpha: float
    steering_shift_mean: float
    reversal_shift_mean: float
    bidirectional_effect: float
    coherence_baseline_mean: float
    coherence_steered_mean: float
    coherence_drop: float
    coherence_pass: bool
    n_prompts: int


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _set_modal_cache_env() -> None:
    os.environ["HF_HOME"] = "/models/huggingface"
    os.environ["TRANSFORMERS_CACHE"] = "/models/huggingface"
    os.environ["HF_HUB_CACHE"] = "/models/huggingface"
    os.environ["HUGGINGFACE_HUB_CACHE"] = "/models/huggingface"
    Path("/models/huggingface").mkdir(parents=True, exist_ok=True)
    Path("/models/persona-circuits/trait-lanes-v2").mkdir(parents=True, exist_ok=True)


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload at {path} must be an object.")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _resolve_selected_lane_rows(
    *,
    readiness_payload: dict[str, Any],
    tranche_id: str,
    lane_ids_override: list[str] | None,
) -> list[dict[str, Any]]:
    lane_rows = readiness_payload.get("lane_rows")
    if not isinstance(lane_rows, list) or not lane_rows:
        raise ValueError("Readiness payload missing lane_rows.")
    lane_by_id = {str(row["lane_id"]): row for row in lane_rows if isinstance(row, dict) and "lane_id" in row}

    if lane_ids_override:
        lane_ids = lane_ids_override
    else:
        selected = None
        if tranche_id.strip() and tranche_id.strip().lower() != "recommended":
            for tranche in readiness_payload.get("recommended_tranches", []):
                if isinstance(tranche, dict) and str(tranche.get("tranche_id", "")).strip() == tranche_id.strip():
                    selected = tranche
                    break
            if selected is None:
                raise ValueError(f"Unknown tranche_id: {tranche_id}")
        else:
            selected = readiness_payload.get("recommended_first_tranche")
        if not isinstance(selected, dict):
            raise ValueError("Readiness payload missing recommended tranche.")
        lane_ids = [str(x) for x in selected.get("lane_ids", [])]

    rows: list[dict[str, Any]] = []
    for lane_id in lane_ids:
        if lane_id not in lane_by_id:
            raise ValueError(f"Lane {lane_id} missing from readiness payload.")
        row = lane_by_id[lane_id]
        if not bool(row.get("screen_ready", False)):
            raise ValueError(f"Lane {lane_id} is not screen_ready in readiness payload.")
        rows.append(row)
    if not rows:
        raise ValueError("No lane rows selected for screening.")
    return rows


def _build_execution_packet(
    *,
    registry: dict[str, Any],
    readiness_payload: dict[str, Any],
    readiness_path: Path,
    selected_lane_rows: list[dict[str, Any]],
    prompt_limit: int,
    judge_model: str,
) -> dict[str, Any]:
    lane_ids = [str(row["lane_id"]) for row in selected_lane_rows]
    plan_rows = build_lane_screening_plan(registry, lane_ids=lane_ids)
    plan_by_lane = {str(row["lane_id"]): row for row in plan_rows}
    defaults = registry.get("defaults") or {}
    smoke_profile = defaults.get("behavioral_smoke_profile") or {}
    promotion_profile_name = "persona_screen_v1"
    promotion_profile = (defaults.get("promotion_profiles") or {}).get(promotion_profile_name, {})
    condition_rows: list[dict[str, Any]] = []
    lane_packets: list[dict[str, Any]] = []

    for lane_row in selected_lane_rows:
        lane_id = str(lane_row["lane_id"])
        plan_row = plan_by_lane[lane_id]
        extraction_path = str(lane_row["prompt_quality"]["extraction"]["path"])
        heldout_path = str(lane_row["prompt_quality"]["heldout"]["path"])
        extraction_free_path = str(lane_row["ground_truth_stats"]["extraction_free"]["path"])
        for layer in plan_row["screening_layers"]:
            for alpha in plan_row["screening_alpha_grid"]:
                condition_rows.append(
                    {
                        "lane_id": lane_id,
                        "layer": int(layer),
                        "alpha": float(alpha),
                        "judge_rubric_id": plan_row["judge_rubric_id"],
                    }
                )
        lane_packets.append(
            {
                "lane_id": lane_id,
                "family_id": str(lane_row["family_id"]),
                "judge_rubric_id": str(lane_row["judge_rubric_id"]),
                "requires_ground_truth": bool(lane_row["requires_ground_truth"]),
                "supports_extraction_free": bool(lane_row["supports_extraction_free"]),
                "supports_external_transfer": bool(plan_row.get("supports_external_transfer", False)),
                "prompt_paths": {
                    "extraction": extraction_path,
                    "heldout": heldout_path,
                    "extraction_free": extraction_free_path,
                },
                "screening_layers": [int(x) for x in plan_row["screening_layers"]],
                "screening_alpha_grid": [float(x) for x in plan_row["screening_alpha_grid"]],
                "known_confounds": list(lane_row.get("known_confounds", [])),
            }
        )

    tranche = readiness_payload.get("recommended_first_tranche") or {}
    recommended_lane_ids = tranche.get("lane_ids", []) if isinstance(tranche, dict) else []
    selected_is_recommended = lane_ids == [str(x) for x in recommended_lane_ids]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_screening_execution_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "readiness_artifact_path": str(readiness_path),
        "selected_lane_ids": lane_ids,
        "selected_is_recommended_first_tranche": bool(selected_is_recommended),
        "prompt_limit_per_lane": int(prompt_limit),
        "judge_model": str(judge_model),
        "extraction_method": DEFAULT_EXTRACTION_METHOD,
        "behavioral_smoke_profile": smoke_profile,
        "promotion_profile": promotion_profile,
        "lane_packets": lane_packets,
        "condition_matrix": {
            "n_rows": len(condition_rows),
            "rows": condition_rows,
        },
        "launch_recommended_now": True,
        "notes": [
            "This packet is for a thin sidecar screening execution and reuses the existing Week 2 extraction/robustness/position kernels.",
            "Only the judge-smoke loop is branch-specific here; promotion remains gated on later follow-on screens.",
        ],
    }


def _build_coherence_summary(
    *,
    baseline_scores: list[float],
    steered_scores: list[float],
    coherence_gate_mode: str,
    coherence_max_drop: float,
    coherence_min_score: float = 0.0,
) -> dict[str, Any]:
    baseline_mean = float(np.mean(baseline_scores)) if baseline_scores else 0.0
    steered_mean = float(np.mean(steered_scores)) if steered_scores else 0.0
    drop = baseline_mean - steered_mean
    pass_min_score = bool(steered_mean >= float(coherence_min_score))
    pass_max_drop = bool(drop <= float(coherence_max_drop))
    mode = coherence_gate_mode.strip().lower()
    if mode == "relative_only":
        passed = pass_max_drop
    elif mode == "absolute_only":
        passed = pass_min_score
    else:
        passed = bool(pass_min_score and pass_max_drop)
    return {
        "baseline_mean": baseline_mean,
        "steered_mean": steered_mean,
        "drop_from_baseline": float(drop),
        "pass_min_score": pass_min_score,
        "pass_max_drop": pass_max_drop,
        "gate_mode": mode,
        "pass": bool(passed),
    }


def _rank_metric(metric: SmokeMetric) -> tuple[float, float, float, float]:
    feasible = 1.0 if metric.coherence_pass else 0.0
    min_dir = min(metric.steering_shift_mean, metric.reversal_shift_mean)
    alpha_penalty = -abs(metric.alpha - 1.0)
    return (feasible, metric.bidirectional_effect, min_dir, alpha_penalty)


def _select_best_metric(metrics: list[SmokeMetric]) -> SmokeMetric | None:
    if not metrics:
        return None
    return sorted(metrics, key=_rank_metric, reverse=True)[0]


def _safe_mean(values: list[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=np.float64))) if values else 0.0


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=8 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("anthropic-key"),
        modal.Secret.from_name("wandb-key"),
    ],
    volumes={"/models": vol},
)
def run_trait_lane_screening_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    train_prompt_pairs: dict[str, list[dict[str, Any]]],
    heldout_prompt_pairs: dict[str, list[dict[str, Any]]],
    candidate_layers: list[int],
    extraction_method: str,
    response_max_new_tokens: int,
    response_temperature: float,
    robustness_subset_size: int,
    robustness_n_bootstrap: int,
    position_ablation_pairs: int,
    judge_rpm_limit_per_run: int,
    judge_min_interval_seconds: float,
    judge_max_attempts: int,
    run_name: str,
) -> dict[str, Any]:
    extract_result = extract_vectors_remote.get_raw_f()(
        config=config,
        prompt_pairs=train_prompt_pairs,
        traits=list(packet["selected_lane_ids"]),
        layers=list(candidate_layers),
        extraction_method=extraction_method,
        response_max_new_tokens=int(response_max_new_tokens),
        response_temperature=float(response_temperature),
        run_name=f"{run_name}-extract",
    )
    extract_summary = extract_result["summary"]
    vectors = extract_result["vectors"]
    trait_layer_map = {
        lane_id: int(extract_summary["diagnostics"][lane_id]["prelim_best_layer_by_cosine_margin"])
        for lane_id in packet["selected_lane_ids"]
    }

    promotion_profile = packet["promotion_profile"]
    robustness_result = extraction_robustness_remote.get_raw_f()(
        config=config,
        train_prompt_pairs=train_prompt_pairs,
        heldout_prompt_pairs=heldout_prompt_pairs,
        trait_layer_map=trait_layer_map,
        extraction_method=extraction_method,
        response_max_new_tokens=int(response_max_new_tokens),
        response_temperature=float(response_temperature),
        subset_size=min(int(robustness_subset_size), min(len(rows) for rows in train_prompt_pairs.values())),
        n_bootstrap=int(robustness_n_bootstrap),
        bootstrap_seed=int(config["seeds"]["primary"]),
        min_bootstrap_p05_cosine=float(promotion_profile.get("min_bootstrap_p05_cosine", 0.8)),
        min_train_vs_heldout_cosine=float(promotion_profile.get("min_train_vs_heldout_cosine", 0.7)),
    )

    position_result = run_position_ablation_remote.get_raw_f()(
        config=config,
        traits=list(packet["selected_lane_ids"]),
        layers=list(candidate_layers),
        extraction_rows_by_trait=train_prompt_pairs,
        extraction_pairs=min(int(position_ablation_pairs), min(len(rows) for rows in train_prompt_pairs.values())),
        max_new_tokens=int(response_max_new_tokens),
        temperature=float(response_temperature),
        seed=int(config["seeds"]["primary"]),
    )

    smoke_result = run_behavioral_smoke_remote.get_raw_f()(
        config=config,
        packet=packet,
        vectors=vectors,
        trait_layer_map=trait_layer_map,
        heldout_prompt_pairs=heldout_prompt_pairs,
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=f"{run_name}-smoke",
    )

    combined_report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_screening_execution",
        "registry_path": packet["registry_path"],
        "readiness_artifact_path": packet["readiness_artifact_path"],
        "selected_lane_ids": list(packet["selected_lane_ids"]),
        "prompt_limit_per_lane": int(packet["prompt_limit_per_lane"]),
        "execution_packet": packet,
        "extract_vectors": extract_summary,
        "provisional_trait_layer_map": trait_layer_map,
        "bootstrap_robustness": robustness_result,
        "position_ablation": position_result["report"],
        "behavioral_smoke": smoke_result["report"],
        "modal_artifacts": {
            "extract_summary_path": extract_result["modal_artifacts"]["summary_path"],
            "extract_vectors_path": extract_result["modal_artifacts"]["vectors_path"],
            "position_report_path": position_result["modal_report_path"],
            "behavioral_smoke_report_path": smoke_result["modal_report_path"],
        },
        "notes": [
            "This is the first thin actual screening artifact for the trait_lanes_v2 branch.",
            "The runner reuses existing Week 2 extraction, robustness, and position-ablation kernels and adds only a small branch-specific judge smoke stage.",
            "Extraction-free overlap and external smoke are not executed in this first tranche yet.",
        ],
    }
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_report_path = (
        Path("/models/persona-circuits/trait-lanes-v2")
        / f"screening_execution_{timestamp}.json"
    )
    modal_report_path.write_text(json.dumps(combined_report, indent=2), encoding="utf-8")
    return {"report": combined_report, "modal_report_path": str(modal_report_path)}


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=6 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("anthropic-key"),
        modal.Secret.from_name("wandb-key"),
    ],
    volumes={"/models": vol},
)
def run_behavioral_smoke_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    vectors: dict[str, dict[str, list[float]]],
    trait_layer_map: dict[str, int],
    heldout_prompt_pairs: dict[str, list[dict[str, Any]]],
    judge_rpm_limit_per_run: int,
    judge_min_interval_seconds: float,
    judge_max_attempts: int,
    run_name: str,
) -> dict[str, Any]:
    import anthropic
    import torch
    import wandb
    from sae_lens import HookedSAETransformer

    _set_modal_cache_env()
    seed = int(config["seeds"]["primary"])
    _seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    model_name = str(config["models"]["primary"]["name"])
    smoke_profile = packet["behavioral_smoke_profile"]
    max_new_tokens = int(smoke_profile.get("max_new_tokens", 96))
    temperature = float(smoke_profile.get("temperature", 0.0))
    coherence_gate_mode = str(smoke_profile.get("coherence_mode", "relative_only"))
    coherence_max_drop = float(smoke_profile.get("max_relative_coherence_drop", 10.0))
    judge_model = str(packet["judge_model"])

    run = wandb.init(
        project=str(config["wandb"]["project"]),
        entity=str(config["wandb"]["entity"]),
        job_type="trait_lane_behavioral_smoke",
        name=run_name,
        config={
            "branch": "trait_lanes_v2",
            "selected_lane_ids": packet["selected_lane_ids"],
            "prompt_limit_per_lane": int(packet["prompt_limit_per_lane"]),
            "judge_model": judge_model,
            "screening_profile": smoke_profile,
            "trait_layer_map": trait_layer_map,
        },
    )

    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    anthropic_client = anthropic.Anthropic()
    rate_limiter = SlidingWindowRateLimiter(
        requests_per_minute=int(judge_rpm_limit_per_run),
        min_interval_seconds=float(judge_min_interval_seconds),
    )
    response_cache: dict[tuple[Any, ...], str] = {}
    score_cache: dict[tuple[Any, ...], Any] = {}

    lane_reports: list[dict[str, Any]] = []
    for lane_idx, lane_packet in enumerate(packet["lane_packets"], start=1):
        lane_id = str(lane_packet["lane_id"])
        judge_rubric_id = str(lane_packet["judge_rubric_id"])
        layer = int(trait_layer_map[lane_id])
        direction = torch.tensor(vectors[lane_id][str(layer)], dtype=torch.float32, device="cuda")
        heldout_rows = heldout_prompt_pairs[lane_id][: int(packet["prompt_limit_per_lane"])]
        screening_alphas = [float(x) for x in lane_packet["screening_alpha_grid"]]

        print(
            json.dumps(
                {
                    "event": "lane_start",
                    "lane_id": lane_id,
                    "lane_index": lane_idx,
                    "total_lanes": len(packet["lane_packets"]),
                    "layer": layer,
                    "n_heldout_rows": len(heldout_rows),
                }
            ),
            flush=True,
        )

        baseline_low_scores: dict[int, float] = {}
        baseline_high_scores: dict[int, float] = {}
        baseline_low_coherence: dict[int, float] = {}
        baseline_high_coherence: dict[int, float] = {}
        baseline_low_responses: dict[int, str] = {}
        baseline_high_responses: dict[int, str] = {}
        for row in heldout_rows:
            rid = int(row["id"])
            gt = str(row.get("ground_truth", "N/A"))
            low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])
            high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])

            low_resp = generate_response(
                model=model,
                prompt_text=low_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                response_cache=response_cache,
                cache_key=(lane_id, rid, "baseline_low"),
            )
            high_resp = generate_response(
                model=model,
                prompt_text=high_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                response_cache=response_cache,
                cache_key=(lane_id, rid, "baseline_high"),
            )
            low_trait = judge_score(
                anthropic_client=anthropic_client,
                anthropic_module=anthropic,
                judge_model=judge_model,
                score_trait=judge_rubric_id,
                user_query=row["user_query"],
                response=low_resp,
                ground_truth=gt,
                max_attempts=judge_max_attempts,
                rate_limiter=rate_limiter,
                score_cache=score_cache,
            )
            high_trait = judge_score(
                anthropic_client=anthropic_client,
                anthropic_module=anthropic,
                judge_model=judge_model,
                score_trait=judge_rubric_id,
                user_query=row["user_query"],
                response=high_resp,
                ground_truth=gt,
                max_attempts=judge_max_attempts,
                rate_limiter=rate_limiter,
                score_cache=score_cache,
            )
            low_coh = judge_score(
                anthropic_client=anthropic_client,
                anthropic_module=anthropic,
                judge_model=judge_model,
                score_trait="coherence",
                user_query=row["user_query"],
                response=low_resp,
                ground_truth=gt,
                max_attempts=judge_max_attempts,
                rate_limiter=rate_limiter,
                score_cache=score_cache,
            )
            high_coh = judge_score(
                anthropic_client=anthropic_client,
                anthropic_module=anthropic,
                judge_model=judge_model,
                score_trait="coherence",
                user_query=row["user_query"],
                response=high_resp,
                ground_truth=gt,
                max_attempts=judge_max_attempts,
                rate_limiter=rate_limiter,
                score_cache=score_cache,
            )
            baseline_low_scores[rid] = float(low_trait.score)
            baseline_high_scores[rid] = float(high_trait.score)
            baseline_low_coherence[rid] = float(low_coh.score)
            baseline_high_coherence[rid] = float(high_coh.score)
            baseline_low_responses[rid] = low_resp
            baseline_high_responses[rid] = high_resp

        metrics: list[SmokeMetric] = []
        condition_rows: list[dict[str, Any]] = []
        for alpha_idx, alpha in enumerate(screening_alphas, start=1):
            steering_deltas: list[float] = []
            reversal_deltas: list[float] = []
            baseline_coherence_scores: list[float] = []
            steered_coherence_scores: list[float] = []
            row_details: list[dict[str, Any]] = []

            for row in heldout_rows:
                rid = int(row["id"])
                gt = str(row.get("ground_truth", "N/A"))
                low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])
                high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])
                plus_resp = generate_response(
                    model=model,
                    prompt_text=low_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    layer=layer,
                    direction=direction,
                    alpha=float(alpha),
                    response_cache=response_cache,
                    cache_key=(lane_id, rid, layer, float(alpha), "plus"),
                )
                minus_resp = generate_response(
                    model=model,
                    prompt_text=high_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    layer=layer,
                    direction=direction,
                    alpha=float(-alpha),
                    response_cache=response_cache,
                    cache_key=(lane_id, rid, layer, float(alpha), "minus"),
                )
                plus_score = judge_score(
                    anthropic_client=anthropic_client,
                    anthropic_module=anthropic,
                    judge_model=judge_model,
                    score_trait=judge_rubric_id,
                    user_query=row["user_query"],
                    response=plus_resp,
                    ground_truth=gt,
                    max_attempts=judge_max_attempts,
                    rate_limiter=rate_limiter,
                    score_cache=score_cache,
                )
                minus_score = judge_score(
                    anthropic_client=anthropic_client,
                    anthropic_module=anthropic,
                    judge_model=judge_model,
                    score_trait=judge_rubric_id,
                    user_query=row["user_query"],
                    response=minus_resp,
                    ground_truth=gt,
                    max_attempts=judge_max_attempts,
                    rate_limiter=rate_limiter,
                    score_cache=score_cache,
                )
                plus_coh = judge_score(
                    anthropic_client=anthropic_client,
                    anthropic_module=anthropic,
                    judge_model=judge_model,
                    score_trait="coherence",
                    user_query=row["user_query"],
                    response=plus_resp,
                    ground_truth=gt,
                    max_attempts=judge_max_attempts,
                    rate_limiter=rate_limiter,
                    score_cache=score_cache,
                )
                minus_coh = judge_score(
                    anthropic_client=anthropic_client,
                    anthropic_module=anthropic,
                    judge_model=judge_model,
                    score_trait="coherence",
                    user_query=row["user_query"],
                    response=minus_resp,
                    ground_truth=gt,
                    max_attempts=judge_max_attempts,
                    rate_limiter=rate_limiter,
                    score_cache=score_cache,
                )
                steer_delta = float(plus_score.score) - baseline_low_scores[rid]
                rev_delta = baseline_high_scores[rid] - float(minus_score.score)
                steering_deltas.append(steer_delta)
                reversal_deltas.append(rev_delta)
                baseline_coherence_scores.extend([baseline_low_coherence[rid], baseline_high_coherence[rid]])
                steered_coherence_scores.extend([float(plus_coh.score), float(minus_coh.score)])
                row_details.append(
                    {
                        "id": rid,
                        "category": row.get("category"),
                        "user_query": row["user_query"],
                        "ground_truth": gt,
                        "baseline_low_score": baseline_low_scores[rid],
                        "baseline_high_score": baseline_high_scores[rid],
                        "plus_score": float(plus_score.score),
                        "minus_score": float(minus_score.score),
                        "baseline_low_coherence": baseline_low_coherence[rid],
                        "baseline_high_coherence": baseline_high_coherence[rid],
                        "plus_coherence": float(plus_coh.score),
                        "minus_coherence": float(minus_coh.score),
                        "steering_delta": steer_delta,
                        "reversal_delta": rev_delta,
                        "baseline_low_response": baseline_low_responses[rid],
                        "baseline_high_response": baseline_high_responses[rid],
                        "plus_response": plus_resp,
                        "minus_response": minus_resp,
                    }
                )

            coherence_summary = _build_coherence_summary(
                baseline_scores=baseline_coherence_scores,
                steered_scores=steered_coherence_scores,
                coherence_gate_mode=coherence_gate_mode,
                coherence_max_drop=coherence_max_drop,
            )
            metric = SmokeMetric(
                layer=int(layer),
                alpha=float(alpha),
                steering_shift_mean=_safe_mean(steering_deltas),
                reversal_shift_mean=_safe_mean(reversal_deltas),
                bidirectional_effect=float(_safe_mean(steering_deltas) + _safe_mean(reversal_deltas)),
                coherence_baseline_mean=float(coherence_summary["baseline_mean"]),
                coherence_steered_mean=float(coherence_summary["steered_mean"]),
                coherence_drop=float(coherence_summary["drop_from_baseline"]),
                coherence_pass=bool(coherence_summary["pass"]),
                n_prompts=len(heldout_rows),
            )
            metrics.append(metric)
            condition_rows.append({**asdict(metric), "coherence_summary": coherence_summary, "rows": row_details})
            print(
                json.dumps(
                    {
                        "event": "lane_condition_complete",
                        "lane_id": lane_id,
                        "condition_index": alpha_idx,
                        "total_conditions": len(screening_alphas),
                        "layer": layer,
                        "alpha": float(alpha),
                        "bidirectional_effect": float(metric.bidirectional_effect),
                        "coherence_pass": bool(metric.coherence_pass),
                    }
                ),
                flush=True,
            )

        best_metric = _select_best_metric(metrics)
        lane_report = {
            "lane_id": lane_id,
            "family_id": str(lane_packet["family_id"]),
            "judge_rubric_id": judge_rubric_id,
            "selected_layer": layer,
            "prompt_paths": lane_packet["prompt_paths"],
            "heldout_prompt_count_used": len(heldout_rows),
            "baseline_summary": {
                "low_score_mean": _safe_mean(list(baseline_low_scores.values())),
                "high_score_mean": _safe_mean(list(baseline_high_scores.values())),
                "coherence_mean": _safe_mean(
                    list(baseline_low_coherence.values()) + list(baseline_high_coherence.values())
                ),
            },
            "conditions": condition_rows,
            "selected_condition": asdict(best_metric) if best_metric is not None else None,
            "partial_metrics_for_promotion_packet": {
                "behavioral_shift": float(best_metric.bidirectional_effect) if best_metric is not None else None,
                "relative_coherence_drop": float(best_metric.coherence_drop) if best_metric is not None else None,
                "response_phase_persistence": None,
                "benchmark_smoke_pass": None,
                "bootstrap_p05_cosine": None,
                "train_vs_heldout_cosine": None,
            },
            "evidence_status": {
                "behavioral_smoke": "known",
                "coherence_smoke": "known",
                "promotion_interpretation": "inferred",
            },
        }
        lane_reports.append(lane_report)
        if best_metric is not None:
            wandb.log(
                {
                    f"trait_lane_smoke/{lane_id}/selected_layer": int(layer),
                    f"trait_lane_smoke/{lane_id}/best_alpha": float(best_metric.alpha),
                    f"trait_lane_smoke/{lane_id}/best_bidirectional_effect": float(best_metric.bidirectional_effect),
                    f"trait_lane_smoke/{lane_id}/best_coherence_drop": float(best_metric.coherence_drop),
                    f"trait_lane_smoke/{lane_id}/best_coherence_pass": float(best_metric.coherence_pass),
                }
            )

    run.finish()
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_behavioral_smoke_report",
        "selected_lane_ids": packet["selected_lane_ids"],
        "trait_layer_map": {k: int(v) for k, v in trait_layer_map.items()},
        "judge_model": judge_model,
        "prompt_limit_per_lane": int(packet["prompt_limit_per_lane"]),
        "behavioral_smoke_profile": smoke_profile,
        "lane_reports": lane_reports,
        "summary": {
            "n_lanes": len(lane_reports),
            "n_with_any_coherence_pass": int(
                sum(
                    1
                    for lane in lane_reports
                    if lane["selected_condition"] is not None and bool(lane["selected_condition"]["coherence_pass"])
                )
            ),
        },
        "notes": [
            "This is screening-depth behavioral smoke only at the provisional cosine-margin-selected layer per lane.",
            "External smoke and extraction-free overlap remain follow-on screens for the branch.",
        ],
    }
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_report_path = Path("/models/persona-circuits/trait-lanes-v2") / f"behavioral_smoke_report_{timestamp}.json"
    modal_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"report": report, "modal_report_path": str(modal_report_path)}


@app.local_entrypoint()
def main(
    readiness_json: str = "",
    tranche_id: str = "recommended",
    lane_ids: str = "",
    prompt_limit: int = DEFAULT_PROMPT_LIMIT,
    judge_model: str = DEFAULT_JUDGE_MODEL,
    judge_rpm_limit_per_run: int = 180,
    judge_min_interval_seconds: float = 0.25,
    judge_max_attempts: int = 6,
    robustness_subset_size: int = 20,
    robustness_n_bootstrap: int = 12,
    position_ablation_pairs: int = 12,
    dry_run: bool = False,
    output_json: str = "",
    run_name: str = "",
) -> None:
    if int(prompt_limit) <= 0:
        raise ValueError("prompt_limit must be > 0")
    readiness_path = Path(readiness_json).resolve() if readiness_json.strip() else _latest_result_path(DEFAULT_READINESS_PATTERN)
    readiness_payload = _load_json(readiness_path)
    registry = load_trait_lane_registry(REGISTRY_PATH)
    selected_lane_rows = _resolve_selected_lane_rows(
        readiness_payload=readiness_payload,
        tranche_id=tranche_id,
        lane_ids_override=parse_id_csv(lane_ids),
    )
    packet = _build_execution_packet(
        registry=registry,
        readiness_payload=readiness_payload,
        readiness_path=readiness_path,
        selected_lane_rows=selected_lane_rows,
        prompt_limit=int(prompt_limit),
        judge_model=judge_model,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path: Path
    if output_json.strip():
        out_path = Path(output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        suffix = "packet" if dry_run else "execution"
        out_path = RESULTS_DIR / f"week2_trait_lane_screening_{suffix}_{timestamp}.json"

    if dry_run:
        out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
        print(json.dumps({"output_json": str(out_path), "dry_run": True}, indent=2))
        return

    config = _load_config()
    lane_ids_list = list(packet["selected_lane_ids"])
    train_prompt_pairs = {
        lane_id: _load_jsonl(Path(next(lp for lp in packet["lane_packets"] if lp["lane_id"] == lane_id)["prompt_paths"]["extraction"]))
        for lane_id in lane_ids_list
    }
    heldout_prompt_pairs = {
        lane_id: _load_jsonl(Path(next(lp for lp in packet["lane_packets"] if lp["lane_id"] == lane_id)["prompt_paths"]["heldout"]))
        for lane_id in lane_ids_list
    }
    candidate_layers = sorted({int(layer) for lp in packet["lane_packets"] for layer in lp["screening_layers"]})
    extraction_method = str(packet["extraction_method"])
    smoke_profile = packet["behavioral_smoke_profile"]
    promotion_profile = packet["promotion_profile"]
    response_max_new_tokens = int(smoke_profile.get("max_new_tokens", 96))
    response_temperature = float(smoke_profile.get("temperature", 0.0))

    screening_run_name = run_name.strip() or (
        f"trait-lanes-v2-screen-{'+'.join(lane_ids_list)}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )
    screening_result = run_trait_lane_screening_remote.remote(
        config=config,
        packet=packet,
        train_prompt_pairs=train_prompt_pairs,
        heldout_prompt_pairs=heldout_prompt_pairs,
        candidate_layers=candidate_layers,
        extraction_method=extraction_method,
        response_max_new_tokens=response_max_new_tokens,
        response_temperature=response_temperature,
        robustness_subset_size=int(robustness_subset_size),
        robustness_n_bootstrap=int(robustness_n_bootstrap),
        position_ablation_pairs=int(position_ablation_pairs),
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=screening_run_name,
    )

    combined_report = screening_result["report"]
    out_path.write_text(json.dumps(combined_report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": str(out_path),
                "selected_lane_ids": lane_ids_list,
                "provisional_trait_layer_map": combined_report["provisional_trait_layer_map"],
                "modal_report_path": screening_result.get("modal_report_path"),
                "modal_artifacts": combined_report.get("modal_artifacts", {}),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
