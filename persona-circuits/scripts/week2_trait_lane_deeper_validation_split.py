"""Split extraction and validation launches for branch-local deeper Week 2 validation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import torch
import yaml

try:
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
    )
    from scripts.week2_behavioral_validation_upgrade import (
        DEFAULT_MAX_NEW_TOKENS,
        DEFAULT_TEMPERATURE,
        _hash_prompt_rows,
        run_trait_validation_remote,
    )
    from scripts.week2_extract_persona_vectors import (
        DEFAULT_EXTRACTION_METHOD,
        DEFAULT_RESPONSE_MAX_NEW_TOKENS,
        DEFAULT_RESPONSE_TEMPERATURE,
        extract_vectors_remote,
    )
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        load_trait_lane_registry,
        parse_id_csv,
    )
    from scripts.week2_behavioral_validation_upgrade import (
        DEFAULT_MAX_NEW_TOKENS,
        DEFAULT_TEMPERATURE,
        _hash_prompt_rows,
        run_trait_validation_remote,
    )
    from scripts.week2_extract_persona_vectors import (
        DEFAULT_EXTRACTION_METHOD,
        DEFAULT_RESPONSE_MAX_NEW_TOKENS,
        DEFAULT_RESPONSE_TEMPERATURE,
        extract_vectors_remote,
    )


APP_NAME = "persona-circuits-week2-trait-lane-deeper-validation-split"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_DEEPER_PACKET_PATTERN = "week2_trait_lane_deeper_validation_packet_*.json"
DEFAULT_JUDGE_RPM_LIMIT = 180
DEFAULT_JUDGE_MIN_INTERVAL_SECONDS = 0.25
DEFAULT_JUDGE_GLOBAL_RPM_BUDGET = 180
DEFAULT_ASSUMED_PARALLEL_RUNS = 1
DEFAULT_JUDGE_MAX_ATTEMPTS = 6
DEFAULT_JUDGE_RETRY_BASE_SECONDS = 0.75
DEFAULT_JUDGE_RETRY_MAX_SECONDS = 30.0
DEFAULT_JUDGE_RETRY_JITTER_FRACTION = 0.2
DEFAULT_JUDGE_PARSE_FAIL_THRESHOLD = 0.05
DEFAULT_JUDGE_DIRECTIONALITY_THRESHOLD = 0.7
DEFAULT_MIN_BIDIRECTIONAL_EFFECT = 20.0
DEFAULT_CONTROL_TEST_MAX_SCORE = 20.0
DEFAULT_SPECIFICITY_MAX_ABS_SHIFT = 10.0
DEFAULT_PROGRESS_LOG_EVERY_ROWS = 3
DEFAULT_PROGRESS_LOG_EVERY_COMBOS = 1
DEFAULT_PROGRESS_MIN_INTERVAL_SECONDS = 15.0
DEFAULT_CHECKPOINT_WRITE_EVERY_ROWS = 3
DEFAULT_CHECKPOINT_WRITE_EVERY_COMBOS = 1

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
            "scipy",
            "scikit-learn",
            "datasets",
        ]
    )
    .add_local_dir(ROOT / "scripts", remote_path="/root/scripts")
)


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


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
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _normalize_vectors(raw_vectors: dict[str, dict[str, list[float]]]) -> dict[str, dict[int, list[float]]]:
    normalized: dict[str, dict[int, list[float]]] = {}
    for trait, by_layer in raw_vectors.items():
        normalized[trait] = {}
        for layer, vec in by_layer.items():
            normalized[trait][int(layer)] = list(vec)
    return normalized


def _load_vectors_pt(path: Path) -> dict[str, dict[int, list[float]]]:
    payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, dict):
        raise ValueError(f"Vector payload at {path} must be a dict.")
    normalized: dict[str, dict[int, list[float]]] = {}
    for trait, by_layer in payload.items():
        if not isinstance(by_layer, dict):
            raise ValueError(f"Vector payload for trait={trait} must be a dict.")
        normalized[str(trait)] = {}
        for layer, tensor in by_layer.items():
            layer_idx = int(layer)
            if hasattr(tensor, "tolist"):
                normalized[str(trait)][layer_idx] = list(tensor.tolist())
            else:
                normalized[str(trait)][layer_idx] = list(tensor)
    return normalized


def _resolve_cross_trait_bleed_traits(*, lane_id: str, profile: dict[str, Any]) -> list[str]:
    traits = [str(lane_id)]
    for value in profile.get("cross_trait_bleed_reference_traits", []):
        trait = str(value).strip()
        if trait and trait not in traits:
            traits.append(trait)
    return traits


def _resolve_selected_lane_packets(
    *,
    deeper_payload: dict[str, Any],
    lane_ids_override: list[str] | None,
) -> list[dict[str, Any]]:
    lane_packets = deeper_payload.get("lane_packets")
    if not isinstance(lane_packets, list) or not lane_packets:
        raise ValueError("Deeper-validation payload missing lane_packets.")
    lane_by_id = {
        str(packet["lane_id"]): packet
        for packet in lane_packets
        if isinstance(packet, dict) and packet.get("lane_id")
    }
    lane_ids = lane_ids_override or [str(x) for x in deeper_payload.get("selected_lane_ids", [])]
    if not lane_ids:
        raise ValueError("No lane ids resolved for deeper validation.")
    selected: list[dict[str, Any]] = []
    for lane_id in lane_ids:
        if lane_id not in lane_by_id:
            raise ValueError(f"Lane {lane_id} missing from deeper-validation payload.")
        packet = lane_by_id[lane_id]
        readiness = packet.get("readiness") or {}
        if not bool(readiness.get("deeper_validation_sidecar_ready", False)):
            raise ValueError(f"Lane {lane_id} is not deeper_validation_sidecar_ready.")
        selected.append(packet)
    return selected


def _build_extraction_packet(
    *,
    registry: dict[str, Any],
    deeper_payload: dict[str, Any],
    deeper_path: Path,
    selected_lane_packets: list[dict[str, Any]],
    extraction_method: str,
    response_max_new_tokens: int,
    response_temperature: float,
    run_token: str,
) -> dict[str, Any]:
    lane_ids = [str(packet["lane_id"]) for packet in selected_lane_packets]
    screening_plan = build_lane_screening_plan(registry, lane_ids=lane_ids)
    plan_by_lane = {str(row["lane_id"]): row for row in screening_plan}
    extraction_candidate_layers = sorted(
        {int(layer) for row in screening_plan for layer in row["screening_layers"]}
    )
    lane_rows: list[dict[str, Any]] = []
    for lane_packet in selected_lane_packets:
        lane_id = str(lane_packet["lane_id"])
        plan_row = plan_by_lane[lane_id]
        lane_rows.append(
            {
                "lane_id": lane_id,
                "family_id": str(lane_packet["family_id"]),
                "display_name": str(lane_packet["display_name"]),
                "screening_layers": [int(x) for x in plan_row["screening_layers"]],
                "screening_alpha_grid": [float(x) for x in plan_row["screening_alpha_grid"]],
                "prompt_paths": dict(lane_packet["current_prompt_paths"]),
                "prompt_counts": dict(lane_packet["current_prompt_counts"]),
            }
        )
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_deeper_validation_split_extract_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "deeper_validation_packet_path": str(deeper_path),
        "selected_lane_ids": lane_ids,
        "run_token": str(run_token),
        "response_phase_policy_snapshot": dict(deeper_payload.get("response_phase_policy_snapshot", {})),
        "execution_policy": dict(deeper_payload.get("execution_policy", {})),
        "extraction_method": str(extraction_method),
        "response_max_new_tokens": int(response_max_new_tokens),
        "response_temperature": float(response_temperature),
        "candidate_layers": extraction_candidate_layers,
        "lane_packets": lane_rows,
        "launch_recommended_now": bool(selected_lane_packets),
        "notes": [
            "This is the extraction-only launch contract for split trait-lane deeper validation.",
            "Vectors produced here should be persisted and reused by the validation-only launch.",
        ],
    }


def _build_validation_packet(
    *,
    registry: dict[str, Any],
    deeper_payload: dict[str, Any],
    deeper_path: Path,
    selected_lane_packets: list[dict[str, Any]],
    vectors_pt: Path | None,
    extraction_report_json: Path | None,
    run_token: str,
) -> dict[str, Any]:
    lane_ids = [str(packet["lane_id"]) for packet in selected_lane_packets]
    screening_plan = build_lane_screening_plan(registry, lane_ids=lane_ids)
    plan_by_lane = {str(row["lane_id"]): row for row in screening_plan}
    profile = dict(deeper_payload["profiles"]["deeper_validation_sidecar"])
    blockers: list[str] = []
    if vectors_pt is None:
        blockers.append("missing_vectors_pt")
    elif not vectors_pt.exists():
        blockers.append(f"vectors_pt_missing:{vectors_pt}")
    lane_rows: list[dict[str, Any]] = []
    for lane_packet in selected_lane_packets:
        lane_id = str(lane_packet["lane_id"])
        plan_row = plan_by_lane[lane_id]
        lane_rows.append(
            {
                "lane_id": lane_id,
                "family_id": str(lane_packet["family_id"]),
                "display_name": str(lane_packet["display_name"]),
                "judge_rubric_id": str(lane_packet["judge_rubric_id"]),
                "selected_layer_screening": int(lane_packet["selected_layer"]),
                "selected_alpha_screening": float(lane_packet["selected_alpha"]),
                "orientation_sign": int(lane_packet["orientation_sign"]),
                "screening_layers": [int(x) for x in plan_row["screening_layers"]],
                "screening_alpha_grid": [float(x) for x in plan_row["screening_alpha_grid"]],
                "prompt_paths": dict(lane_packet["current_prompt_paths"]),
                "prompt_counts": dict(lane_packet["current_prompt_counts"]),
            }
        )
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_deeper_validation_split_validate_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "deeper_validation_packet_path": str(deeper_path),
        "selected_lane_ids": lane_ids,
        "run_token": str(run_token),
        "response_phase_policy_snapshot": dict(deeper_payload.get("response_phase_policy_snapshot", {})),
        "execution_policy": dict(deeper_payload.get("execution_policy", {})),
        "profile": profile,
        "vectors_input": {
            "vectors_pt": str(vectors_pt) if vectors_pt is not None else "",
            "extraction_report_json": str(extraction_report_json) if extraction_report_json is not None else "",
        },
        "lane_packets": lane_rows,
        "blockers": blockers,
        "launch_recommended_now": bool(selected_lane_packets) and not blockers,
        "notes": [
            "This is the validation-only launch contract for split trait-lane deeper validation.",
            "It consumes a persisted vectors artifact rather than relying on in-memory extraction handoff.",
        ],
    }


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
def run_trait_lane_deeper_validation_extract_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    train_prompt_pairs: dict[str, list[dict[str, Any]]],
    run_name: str,
) -> dict[str, Any]:
    extract_result = extract_vectors_remote.get_raw_f()(
        config=config,
        prompt_pairs=train_prompt_pairs,
        traits=list(packet["selected_lane_ids"]),
        layers=[int(x) for x in packet["candidate_layers"]],
        extraction_method=str(packet["extraction_method"]),
        response_max_new_tokens=int(packet["response_max_new_tokens"]),
        response_temperature=float(packet["response_temperature"]),
        run_name=f"{run_name}-extract",
    )
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_deeper_validation_extraction",
        "deeper_validation_packet_path": packet["deeper_validation_packet_path"],
        "extraction_packet": packet,
        "extract_vectors": extract_result["summary"],
        "extract_modal_artifacts": extract_result["modal_artifacts"],
        "vectors": extract_result["vectors"],
    }


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
def run_trait_lane_deeper_validation_validate_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    heldout_prompt_pairs: dict[str, list[dict[str, Any]]],
    vectors: dict[str, dict[int, list[float]]],
    judge_rpm_limit_per_run: int,
    judge_min_interval_seconds: float,
    judge_global_rpm_budget: int,
    assumed_parallel_runs: int,
    judge_max_attempts: int,
    run_name: str,
) -> dict[str, Any]:
    profile = packet["profile"]
    lane_reports: list[dict[str, Any]] = []
    for lane_packet in packet["lane_packets"]:
        lane_id = str(lane_packet["lane_id"])
        heldout_rows = heldout_prompt_pairs[lane_id]
        heldout_hash = _hash_prompt_rows(heldout_rows)
        checkpoint_key = f"{packet['run_token']}-{lane_id}-upgrade"
        validation_result = run_trait_validation_remote.get_raw_f()(
            config=config,
            vectors={lane_id: vectors[lane_id]},
            heldout_rows=heldout_rows,
            heldout_hash=heldout_hash,
            trait=lane_id,
            layers=[int(x) for x in lane_packet["screening_layers"]],
            alphas=[float(x) for x in lane_packet["screening_alpha_grid"]],
            sweep_prompts_per_trait=int(profile["sweep_prompts_per_trait"]),
            confirm_prompts_per_trait=int(profile["confirm_prompts_per_trait"]),
            test_prompts_per_trait=int(profile["test_prompts_per_trait"]),
            confirm_top_k=int(profile["confirm_top_k"]),
            cross_rater_samples=int(profile["cross_rater_samples"]),
            random_control_prompts=int(profile["random_control_prompts"]),
            random_control_vectors=int(profile["random_control_vectors"]),
            shuffled_control_permutations=int(profile["shuffled_control_permutations"]),
            sweep_rollouts_per_prompt=int(profile["sweep_rollouts_per_prompt"]),
            confirm_rollouts_per_prompt=int(profile["confirm_rollouts_per_prompt"]),
            baseline_rollouts_per_prompt=int(profile["baseline_rollouts_per_prompt"]),
            rollout_temperature=float(profile["rollout_temperature"]),
            max_new_tokens=DEFAULT_MAX_NEW_TOKENS,
            temperature=DEFAULT_TEMPERATURE,
            judge_parse_fail_threshold=DEFAULT_JUDGE_PARSE_FAIL_THRESHOLD,
            judge_directionality_threshold=DEFAULT_JUDGE_DIRECTIONALITY_THRESHOLD,
            min_bidirectional_effect=DEFAULT_MIN_BIDIRECTIONAL_EFFECT,
            combo_selection_policy=str(profile["combo_selection_policy"]),
            control_test_max_score=DEFAULT_CONTROL_TEST_MAX_SCORE,
            specificity_max_abs_shift=DEFAULT_SPECIFICITY_MAX_ABS_SHIFT,
            truthfulqa_samples=0,
            truthfulqa_min_plus_minus_delta=0.0,
            truthfulqa_objective_min_minus_plus_delta=0.0,
            coherence_min_score=float(profile["coherence_min_score"]),
            coherence_max_drop=float(profile["coherence_max_drop"]),
            coherence_gate_mode=str(profile["coherence_gate_mode"]),
            cross_trait_bleed_max_fraction=float(profile["cross_trait_bleed_max_fraction"]),
            judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
            judge_min_interval_seconds=float(judge_min_interval_seconds),
            judge_global_rpm_budget=int(judge_global_rpm_budget),
            assumed_parallel_runs=int(assumed_parallel_runs),
            judge_max_attempts=int(judge_max_attempts),
            judge_retry_base_seconds=DEFAULT_JUDGE_RETRY_BASE_SECONDS,
            judge_retry_max_seconds=DEFAULT_JUDGE_RETRY_MAX_SECONDS,
            judge_retry_jitter_fraction=DEFAULT_JUDGE_RETRY_JITTER_FRACTION,
            progress_log_every_rows=DEFAULT_PROGRESS_LOG_EVERY_ROWS,
            progress_log_every_combos=DEFAULT_PROGRESS_LOG_EVERY_COMBOS,
            progress_min_interval_seconds=DEFAULT_PROGRESS_MIN_INTERVAL_SECONDS,
            resume_from_checkpoint=True,
            checkpoint_reload_before_resume=True,
            checkpoint_key=checkpoint_key,
            checkpoint_write_every_rows=DEFAULT_CHECKPOINT_WRITE_EVERY_ROWS,
            checkpoint_write_every_combos=DEFAULT_CHECKPOINT_WRITE_EVERY_COMBOS,
            require_capability_available=bool(profile["capability_proxy_required"]),
            run_name=f"{run_name}-{lane_id}",
            cross_trait_bleed_enabled=bool(profile["cross_trait_bleed_enabled"]),
            cross_trait_bleed_traits=_resolve_cross_trait_bleed_traits(lane_id=lane_id, profile=profile),
        )
        lane_reports.append(
            {
                "lane_id": lane_id,
                "family_id": str(lane_packet["family_id"]),
                "selected_layer_screening": int(lane_packet["selected_layer_screening"]),
                "selected_alpha_screening": float(lane_packet["selected_alpha_screening"]),
                "validation_report": validation_result["report"],
                "validation_modal_report_path": str(validation_result["modal_report_path"]),
                "checkpoint_key": checkpoint_key,
            }
        )
    combined_report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_deeper_validation_validation",
        "deeper_validation_packet_path": packet["deeper_validation_packet_path"],
        "validation_packet": packet,
        "lane_reports": lane_reports,
        "summary": {
            "n_lanes": len(lane_reports),
            "n_overall_pass": int(
                sum(1 for lane in lane_reports if bool(lane["validation_report"]["quality_gates"]["overall_pass"]))
            ),
        },
        "notes": [
            "This is validation-only output for split trait-lane deeper validation.",
            "Cross-trait bleed is evaluated against branch-local reference rubrics.",
        ],
    }
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_report_path = (
        Path("/models/persona-circuits/trait-lanes-v2")
        / f"deeper_validation_validation_{timestamp}.json"
    )
    modal_report_path.parent.mkdir(parents=True, exist_ok=True)
    modal_report_path.write_text(json.dumps(combined_report, indent=2), encoding="utf-8")
    return {"report": combined_report, "modal_report_path": str(modal_report_path)}


@app.local_entrypoint()
def main(
    phase: str = "extract",
    deeper_packet_json: str = "",
    lane_ids: str = "",
    extraction_method: str = DEFAULT_EXTRACTION_METHOD,
    response_max_new_tokens: int = DEFAULT_RESPONSE_MAX_NEW_TOKENS,
    response_temperature: float = DEFAULT_RESPONSE_TEMPERATURE,
    judge_rpm_limit_per_run: int = DEFAULT_JUDGE_RPM_LIMIT,
    judge_min_interval_seconds: float = DEFAULT_JUDGE_MIN_INTERVAL_SECONDS,
    judge_global_rpm_budget: int = DEFAULT_JUDGE_GLOBAL_RPM_BUDGET,
    assumed_parallel_runs: int = DEFAULT_ASSUMED_PARALLEL_RUNS,
    judge_max_attempts: int = DEFAULT_JUDGE_MAX_ATTEMPTS,
    dry_run: bool = False,
    run_token: str = "",
    run_name: str = "",
    output_json: str = "",
    vectors_pt: str = "",
    extraction_report_json: str = "",
) -> None:
    resolved_phase = phase.strip().lower()
    if resolved_phase not in {"extract", "validate"}:
        raise ValueError("--phase must be one of: extract, validate")

    config = _load_config()
    deeper_path = (
        Path(deeper_packet_json).resolve()
        if deeper_packet_json.strip()
        else _latest_result_path(DEFAULT_DEEPER_PACKET_PATTERN)
    )
    deeper_payload = _load_json(deeper_path)
    registry = load_trait_lane_registry(REGISTRY_PATH)
    selected_lane_packets = _resolve_selected_lane_packets(
        deeper_payload=deeper_payload,
        lane_ids_override=parse_id_csv(lane_ids),
    )
    resolved_run_token = run_token.strip() or (
        f"trait-lane-deeper-split-{resolved_phase}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if resolved_phase == "extract":
        packet = _build_extraction_packet(
            registry=registry,
            deeper_payload=deeper_payload,
            deeper_path=deeper_path,
            selected_lane_packets=selected_lane_packets,
            extraction_method=extraction_method,
            response_max_new_tokens=int(response_max_new_tokens),
            response_temperature=float(response_temperature),
            run_token=resolved_run_token,
        )
        suffix = "extract_dryrun_packet" if dry_run else "extract_packet"
        packet_path = RESULTS_DIR / f"week2_trait_lane_deeper_validation_split_{suffix}_{timestamp}.json"
        packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        if dry_run:
            print(json.dumps({"output_json": str(packet_path), "launch_recommended_now": packet["launch_recommended_now"]}, indent=2))
            return
        train_prompt_pairs = {
            str(packet_row["lane_id"]): _load_jsonl(Path(packet_row["prompt_paths"]["extraction"]))
            for packet_row in packet["lane_packets"]
        }
        result = run_trait_lane_deeper_validation_extract_remote.remote(
            config=config,
            packet=packet,
            train_prompt_pairs=train_prompt_pairs,
            run_name=run_name or resolved_run_token,
        )
        local_vectors_path = RESULTS_DIR / f"week2_trait_lane_deeper_validation_vectors_{timestamp}.pt"
        torch.save(
            {
                trait: {int(layer): torch.tensor(vec, dtype=torch.float32) for layer, vec in by_layer.items()}
                for trait, by_layer in result["vectors"].items()
            },
            local_vectors_path,
        )
        report = {
            k: v for k, v in result.items() if k != "vectors"
        }
        report["local_artifacts"] = {"vectors_path": str(local_vectors_path)}
        final_path = RESULTS_DIR / f"week2_trait_lane_deeper_validation_extraction_{timestamp}.json"
        final_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"packet_json": str(packet_path), "output_json": str(final_path), "vectors_pt": str(local_vectors_path)}, indent=2))
        return

    vectors_pt_path: Path | None = Path(vectors_pt).resolve() if vectors_pt.strip() else None
    extraction_report_path: Path | None = (
        Path(extraction_report_json).resolve() if extraction_report_json.strip() else None
    )
    if vectors_pt_path is None and extraction_report_path is not None:
        extraction_payload = _load_json(extraction_report_path)
        local_artifacts = extraction_payload.get("local_artifacts") or {}
        resolved_vectors = local_artifacts.get("vectors_path")
        if resolved_vectors:
            vectors_pt_path = Path(str(resolved_vectors)).resolve()
    packet = _build_validation_packet(
        registry=registry,
        deeper_payload=deeper_payload,
        deeper_path=deeper_path,
        selected_lane_packets=selected_lane_packets,
        vectors_pt=vectors_pt_path,
        extraction_report_json=extraction_report_path,
        run_token=resolved_run_token,
    )
    suffix = "validate_dryrun_packet" if dry_run else "validate_packet"
    packet_path = RESULTS_DIR / f"week2_trait_lane_deeper_validation_split_{suffix}_{timestamp}.json"
    packet_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    if dry_run:
        print(json.dumps({"output_json": str(packet_path), "launch_recommended_now": packet["launch_recommended_now"], "blockers": packet["blockers"]}, indent=2))
        return
    if not packet["launch_recommended_now"]:
        raise ValueError(f"Validation launch blocked: {packet['blockers']}")
    assert vectors_pt_path is not None
    vectors = _load_vectors_pt(vectors_pt_path)
    heldout_prompt_pairs = {
        str(packet_row["lane_id"]): _load_jsonl(Path(packet_row["prompt_paths"]["heldout"]))
        for packet_row in packet["lane_packets"]
    }
    result = run_trait_lane_deeper_validation_validate_remote.remote(
        config=config,
        packet=packet,
        heldout_prompt_pairs=heldout_prompt_pairs,
        vectors=vectors,
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_global_rpm_budget=int(judge_global_rpm_budget),
        assumed_parallel_runs=int(assumed_parallel_runs),
        judge_max_attempts=int(judge_max_attempts),
        run_name=run_name or resolved_run_token,
    )
    final_path = RESULTS_DIR / f"week2_trait_lane_deeper_validation_validation_{timestamp}.json"
    final_path.write_text(json.dumps(result["report"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"packet_json": str(packet_path), "output_json": str(final_path)}, indent=2))


if __name__ == "__main__":
    main()
