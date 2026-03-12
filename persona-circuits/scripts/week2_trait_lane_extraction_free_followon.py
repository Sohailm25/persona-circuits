"""Run trait-lane extraction-free overlap follow-ons for promoted screening candidates."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

try:
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry
    from scripts.week2_extract_persona_vectors import extract_vectors_remote
    from scripts.week2_extraction_free_activation_eval import (
        _binomial_two_sided_p_value,
        _bootstrap_mean_ci,
        _capture_activation,
        _ensure_division,
        _format_chat_prompt,
        _project_onto,
        _stats,
        _ttest_vs_zero_normal_approx,
    )
    from scripts.week2_extraction_free_reanalysis import _classify_overlap
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry
    from scripts.week2_extract_persona_vectors import extract_vectors_remote
    from scripts.week2_extraction_free_activation_eval import (
        _binomial_two_sided_p_value,
        _bootstrap_mean_ci,
        _capture_activation,
        _ensure_division,
        _format_chat_prompt,
        _project_onto,
        _stats,
        _ttest_vs_zero_normal_approx,
    )
    from scripts.week2_extraction_free_reanalysis import _classify_overlap

APP_NAME = "persona-circuits-week2-trait-lane-extraction-free-followon"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_PROMOTION_PACKET_PATTERN = "week2_trait_lane_promotion_packet_*.json"
DEFAULT_EXTRACTION_METHOD = "prompt_last"
DEFAULT_MAX_NEW_TOKENS = 96
DEFAULT_TEMPERATURE = 0.0
DEFAULT_REQUIRED_GATES = (
    "mean_cosine",
    "positive_fraction",
    "projection_delta",
    "set_count",
    "set_mean_cv",
    "std_control",
    "non_empty_rows",
    "non_empty_set_stats",
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
PROMPTS_DIR = ROOT / "prompts" / "trait_lanes_v2"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"

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
            "wandb",
            "numpy",
            "pyyaml",
        ]
    )
    .add_local_dir(ROOT / "scripts", remote_path="/root/scripts")
)


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


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


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


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


def _eval_gate_policy() -> dict[str, Any]:
    return {
        "required_gates": list(DEFAULT_REQUIRED_GATES),
        "thresholds": {
            "mean_cosine_min": 0.10,
            "positive_fraction_min": 0.75,
            "projection_delta_min": 0.15,
            "set_count_min": 2,
            "set_mean_cv_max": 0.80,
            "max_cosine_std": 0.35,
        },
    }


def _resolve_selected_lanes(
    *,
    registry: dict[str, Any],
    promotion_payload: dict[str, Any],
    lane_ids_override: list[str] | None,
) -> list[dict[str, Any]]:
    ranked_rows = promotion_payload.get("ranked_lanes")
    if not isinstance(ranked_rows, list) or not ranked_rows:
        raise ValueError("Promotion payload missing ranked_lanes.")
    ranked_by_lane = {
        str(row["lane_id"]): row
        for row in ranked_rows
        if isinstance(row, dict) and row.get("lane_id")
    }
    if lane_ids_override:
        lane_ids = lane_ids_override
    else:
        lane_ids = [str(x) for x in promotion_payload.get("recommended_followon_lanes", [])]
    if not lane_ids:
        raise ValueError("No follow-on lanes selected.")

    selected_rows: list[dict[str, Any]] = []
    for lane_id in lane_ids:
        if lane_id not in ranked_by_lane:
            raise ValueError(f"Lane {lane_id} missing from promotion packet.")
        lane_cfg = get_lane_config(registry, lane_id)
        if not bool(lane_cfg.get("supports_extraction_free", False)):
            raise ValueError(f"Lane {lane_id} does not support extraction-free follow-ons.")
        row = dict(ranked_by_lane[lane_id])
        row["supports_extraction_free"] = True
        row["supports_external_transfer"] = bool(lane_cfg.get("supports_external_transfer", False))
        selected_rows.append(row)
    return selected_rows


def build_followon_packet_from_promotion(
    *,
    registry: dict[str, Any],
    promotion_payload: dict[str, Any],
    promotion_path: Path,
    lane_ids_override: list[str] | None = None,
) -> dict[str, Any]:
    selected_rows = _resolve_selected_lanes(
        registry=registry,
        promotion_payload=promotion_payload,
        lane_ids_override=lane_ids_override,
    )
    lane_packets: list[dict[str, Any]] = []
    screening_paths: list[str] = []
    selected_layers: list[int] = []
    for row in selected_rows:
        lane_id = str(row["lane_id"])
        screening_path = str(row["screening_execution_path"])
        screening_paths.append(screening_path)
        selected_layer = int(row["selected_layer"])
        selected_layers.append(selected_layer)
        lane_packets.append(
            {
                "lane_id": lane_id,
                "family_id": str(row["family_id"]),
                "display_name": str(row["display_name"]),
                "judge_rubric_id": str(row["judge_rubric_id"]),
                "screening_status": str(row["screening_status"]),
                "selected_layer": selected_layer,
                "selected_alpha": float(row["selected_alpha"]),
                "response_phase_persistence": float(row["response_phase_persistence"]),
                "oriented_bidirectional_effect": float(row["oriented_bidirectional_effect"]),
                "screening_execution_path": screening_path,
                "prompt_paths": {
                    "extraction": str(PROMPTS_DIR / f"{lane_id}_pairs.jsonl"),
                    "extraction_free": str(PROMPTS_DIR / "extraction_free" / f"{lane_id}_eval.jsonl"),
                },
            }
        )
    gate_policy = _eval_gate_policy()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_extraction_free_followon_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "promotion_packet_path": str(promotion_path),
        "selected_lane_ids": [str(row["lane_id"]) for row in selected_rows],
        "screening_execution_paths": sorted(set(screening_paths)),
        "candidate_layers": sorted(set(selected_layers)),
        "lane_packets": lane_packets,
        "extraction_method": DEFAULT_EXTRACTION_METHOD,
        "response_max_new_tokens": DEFAULT_MAX_NEW_TOKENS,
        "response_temperature": DEFAULT_TEMPERATURE,
        "gate_policy": gate_policy,
        "launch_recommended_now": True,
        "notes": [
            "This follow-on packet re-extracts vectors for the selected branch lanes inside one remote app and then evaluates extraction-free overlap at the already-screened layers.",
            "Response-phase persistence remains a tracked limitation; this follow-on measures cross-induction overlap, not prompt-vs-response agreement.",
        ],
    }


def _resolve_direction(vectors: dict[str, dict[str, list[float]]], lane_id: str, layer: int) -> np.ndarray:
    by_layer = vectors.get(lane_id)
    if not isinstance(by_layer, dict):
        raise KeyError(f"Lane {lane_id} missing from extracted vectors.")
    value = by_layer.get(str(layer))
    if value is None:
        value = by_layer.get(layer)  # type: ignore[arg-type]
    if value is None:
        raise KeyError(f"Lane {lane_id} missing vector at layer {layer}.")
    arr = np.asarray(value, dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if norm <= 1e-10:
        raise ValueError(f"Zero-norm vector for lane={lane_id} layer={layer}")
    return arr / norm


def _evaluate_rows_against_direction(
    *,
    rows: list[dict[str, Any]],
    direction: np.ndarray,
    model: Any,
    tokenizer: Any,
    layer: int,
    gate_policy: dict[str, Any],
    seed: int,
    lane_id: str,
) -> dict[str, Any]:
    import torch

    hook_name = f"blocks.{int(layer)}.hook_resid_post"
    row_summaries: list[dict[str, Any]] = []
    cosines: list[float] = []
    projection_deltas: list[float] = []
    set_buckets: dict[str, list[float]] = {}

    for row in rows:
        high_prompt = _format_chat_prompt(
            tokenizer,
            row.get("neutral_system_prompt", ""),
            row.get("fewshot_high", []),
            row.get("user_query", ""),
        )
        low_prompt = _format_chat_prompt(
            tokenizer,
            row.get("neutral_system_prompt", ""),
            row.get("fewshot_low", []),
            row.get("user_query", ""),
        )
        high_act = _capture_activation(model, high_prompt, hook_name).to(dtype=torch.float32)
        low_act = _capture_activation(model, low_prompt, hook_name).to(dtype=torch.float32)
        delta_np = (high_act - low_act).cpu().numpy()
        delta_norm = float(np.linalg.norm(delta_np))
        cosine = _ensure_division(float(np.dot(delta_np, direction)), delta_norm)
        high_proj = _project_onto(high_act.cpu().numpy(), direction)
        low_proj = _project_onto(low_act.cpu().numpy(), direction)
        projection_delta = high_proj - low_proj
        set_id = str(row.get("fewshot_set_id") or row.get("fewshot_selection_hash") or "unknown_set")

        cosines.append(cosine)
        projection_deltas.append(projection_delta)
        set_buckets.setdefault(set_id, []).append(cosine)
        row_summaries.append(
            {
                "id": row.get("id"),
                "source_row_id": row.get("source_row_id"),
                "category": row.get("category"),
                "fewshot_set_id": set_id,
                "fewshot_selection_hash": row.get("fewshot_selection_hash"),
                "cosine": cosine,
                "projection_delta": projection_delta,
            }
        )

    set_stats: list[dict[str, Any]] = []
    set_means: list[float] = []
    for set_id, bucket in set_buckets.items():
        arr = np.asarray(bucket, dtype=np.float64)
        set_stats.append(
            {
                "signature": set_id,
                "count": int(arr.size),
                "mean_cosine": float(np.mean(arr)),
                "std_cosine": float(np.std(arr)),
            }
        )
        set_means.append(float(np.mean(arr)))

    cosine_stats = _stats(cosines)
    projection_stats = _stats(projection_deltas)
    positive_fraction = float(np.mean(np.asarray([c > 0 for c in cosines], dtype=np.float64))) if cosines else 0.0
    global_std = float(np.std(np.asarray(cosines, dtype=np.float64))) if cosines else 0.0
    set_mean_arr = np.asarray(set_means, dtype=np.float64) if set_means else np.asarray([], dtype=np.float64)
    set_mean_std = float(np.std(set_mean_arr)) if set_mean_arr.size else 0.0
    global_mean_abs = abs(float(cosine_stats["mean"])) if cosine_stats["mean"] is not None else 0.0
    set_mean_cv = _ensure_division(set_mean_std, global_mean_abs)
    projection_mean = float(projection_stats["mean"] or 0.0)
    n_positive = int(np.sum(np.asarray(cosines, dtype=np.float64) > 0.0)) if cosines else 0
    sign_test_p = _binomial_two_sided_p_value(len(cosines), n_positive, p_success=0.5)
    ttest_summary = _ttest_vs_zero_normal_approx(np.asarray(cosines, dtype=np.float64))
    bootstrap_summary = _bootstrap_mean_ci(
        np.asarray(cosines, dtype=np.float64),
        seed=int(seed) + int(layer) * 1009 + len(lane_id),
        n_bootstrap=4000,
    )
    ci95 = bootstrap_summary.get("mean_ci95")
    thresholds = gate_policy["thresholds"]
    gates = {
        "mean_cosine": cosine_stats["mean"] is not None and float(cosine_stats["mean"]) >= float(thresholds["mean_cosine_min"]),
        "positive_fraction": positive_fraction >= float(thresholds["positive_fraction_min"]),
        "projection_delta": projection_mean >= float(thresholds["projection_delta_min"]),
        "set_count": len(set_stats) >= int(thresholds["set_count_min"]),
        "set_mean_cv": set_mean_cv <= float(thresholds["set_mean_cv_max"]),
        "std_control": global_std <= float(thresholds["max_cosine_std"]),
        "non_empty_rows": len(rows) > 0,
        "non_empty_set_stats": len(set_stats) > 0,
    }
    overlap_classification = _classify_overlap(float(cosine_stats["mean"] or 0.0), positive_fraction, sign_test_p)
    return {
        "evidence_status": {
            "activation_deltas": "observed",
            "gate_interpretation": "inferred",
            "overlap_classification": "inferred",
        },
        "n_rows": len(rows),
        "cosine_stats": cosine_stats,
        "projection_delta_stats": projection_stats,
        "positive_cosine_fraction": positive_fraction,
        "global_cosine_std": global_std,
        "set_variance": {
            "unique_sets": len(set_stats),
            "set_mean_std": set_mean_std,
            "set_mean_cv": set_mean_cv,
            "per_set_stats": set_stats,
        },
        "alignment_significance": {
            "n_positive_cosines": n_positive,
            "sign_test_two_sided_p": sign_test_p,
            "ttest_vs_zero": ttest_summary,
            "mean_bootstrap_ci95": ci95,
        },
        "gates": gates,
        "required_gates": list(gate_policy["required_gates"]),
        "passes": all(bool(gates.get(name, False)) for name in gate_policy["required_gates"]),
        "overlap_classification": overlap_classification,
        "rows": row_summaries,
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token"), modal.Secret.from_name("wandb-key")],
    volumes={"/models": vol},
)
def run_trait_lane_extraction_free_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    train_prompt_pairs: dict[str, list[dict[str, Any]]],
    eval_rows_by_lane: dict[str, list[dict[str, Any]]],
    run_name: str,
) -> dict[str, Any]:
    import torch
    from sae_lens import HookedSAETransformer

    _set_modal_cache_env()
    seed = int(config["seeds"]["primary"])
    _seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    extract_result = extract_vectors_remote.get_raw_f()(
        config=config,
        prompt_pairs=train_prompt_pairs,
        traits=list(packet["selected_lane_ids"]),
        layers=list(packet["candidate_layers"]),
        extraction_method=str(packet["extraction_method"]),
        response_max_new_tokens=int(packet["response_max_new_tokens"]),
        response_temperature=float(packet["response_temperature"]),
        run_name=f"{run_name}-extract",
    )

    model_name = str(config["models"]["primary"]["name"])
    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    tokenizer = model.tokenizer

    lane_reports: list[dict[str, Any]] = []
    for lane_packet in packet["lane_packets"]:
        lane_id = str(lane_packet["lane_id"])
        layer = int(lane_packet["selected_layer"])
        direction = _resolve_direction(extract_result["vectors"], lane_id, layer)
        rows = eval_rows_by_lane[lane_id]
        metrics = _evaluate_rows_against_direction(
            rows=rows,
            direction=direction,
            model=model,
            tokenizer=tokenizer,
            layer=layer,
            gate_policy=packet["gate_policy"],
            seed=seed,
            lane_id=lane_id,
        )
        lane_reports.append(
            {
                "lane_id": lane_id,
                "family_id": str(lane_packet["family_id"]),
                "display_name": str(lane_packet["display_name"]),
                "judge_rubric_id": str(lane_packet["judge_rubric_id"]),
                "selected_layer": layer,
                "selected_alpha": float(lane_packet["selected_alpha"]),
                "screening_status_ref": str(lane_packet["screening_status"]),
                "response_phase_persistence_ref": float(lane_packet["response_phase_persistence"]),
                "oriented_bidirectional_effect_ref": float(lane_packet["oriented_bidirectional_effect"]),
                "metrics": metrics,
            }
        )

    summary = {
        "n_lanes": len(lane_reports),
        "n_pass": sum(1 for row in lane_reports if bool(row["metrics"].get("passes", False))),
        "n_moderate_overlap": sum(1 for row in lane_reports if row["metrics"].get("overlap_classification") == "moderate_overlap"),
        "n_weak_overlap": sum(1 for row in lane_reports if row["metrics"].get("overlap_classification") == "weak_overlap"),
        "n_null_overlap": sum(1 for row in lane_reports if row["metrics"].get("overlap_classification") == "null_overlap"),
    }
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_extraction_free_followon",
        "evidence_status": {
            "vector_reextraction": "observed",
            "followon_overlap_metrics": "observed",
            "overall_pass": "inferred",
        },
        "registry_path": packet["registry_path"],
        "promotion_packet_path": packet["promotion_packet_path"],
        "selected_lane_ids": list(packet["selected_lane_ids"]),
        "screening_execution_paths": list(packet["screening_execution_paths"]),
        "vector_extraction": extract_result["summary"],
        "lane_reports": lane_reports,
        "summary": summary,
        "overall_pass": all(bool(row["metrics"].get("passes", False)) for row in lane_reports),
        "modal_artifacts": extract_result["modal_artifacts"],
        "notes": [
            "Branch-local extraction-free follow-on for screened lanes only.",
            "Vectors are re-extracted inside the same app to avoid dependency on inaccessible prior remote vector artifacts.",
        ],
    }
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_report_path = Path("/models/persona-circuits/trait-lanes-v2") / f"extraction_free_followon_{timestamp}.json"
    modal_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"report": report, "modal_report_path": str(modal_report_path)}


@app.local_entrypoint()
def main(
    promotion_packet: str = "",
    lane_ids: str = "",
    run_name: str = "",
    output_json: str = "",
) -> None:
    registry = load_trait_lane_registry()
    promotion_path = Path(promotion_packet) if promotion_packet else _latest_result_path(DEFAULT_PROMOTION_PACKET_PATTERN)
    promotion_payload = _load_json(promotion_path)
    selected_ids = [chunk.strip() for chunk in lane_ids.split(",") if chunk.strip()]
    packet = build_followon_packet_from_promotion(
        registry=registry,
        promotion_payload=promotion_payload,
        promotion_path=promotion_path,
        lane_ids_override=selected_ids or None,
    )
    train_prompt_pairs = {
        str(row["lane_id"]): _load_jsonl(Path(row["prompt_paths"]["extraction"]))
        for row in packet["lane_packets"]
    }
    eval_rows_by_lane = {
        str(row["lane_id"]): _load_jsonl(Path(row["prompt_paths"]["extraction_free"]))
        for row in packet["lane_packets"]
    }
    config = _load_config()
    resolved_run_name = run_name or (
        "trait-lanes-v2-extraction-free-" + "+".join(str(x) for x in packet["selected_lane_ids"])
    )
    result = run_trait_lane_extraction_free_remote.remote(
        config=config,
        packet=packet,
        train_prompt_pairs=train_prompt_pairs,
        eval_rows_by_lane=eval_rows_by_lane,
        run_name=resolved_run_name,
    )
    report = result["report"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_json:
        out_path = Path(output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_extraction_free_followon_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "overall_pass": report["overall_pass"]}, indent=2))


if __name__ == "__main__":
    main()
