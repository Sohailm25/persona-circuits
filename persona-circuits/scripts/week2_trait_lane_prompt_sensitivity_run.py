"""Run the bounded prompt-sensitivity sidecar for the lead trait-lane candidate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import torch
import yaml

APP_NAME = "persona-circuits-week2-trait-lane-prompt-sensitivity"

try:
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, load_trait_lane_registry
    from scripts.week2_extract_persona_vectors import extract_vectors_remote
    from scripts.week2_trait_lane_behavioral_smoke_run import image, run_behavioral_smoke_remote, vol
except ModuleNotFoundError:  # pragma: no cover
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, load_trait_lane_registry
    from scripts.week2_extract_persona_vectors import extract_vectors_remote
    from scripts.week2_trait_lane_behavioral_smoke_run import image, run_behavioral_smoke_remote, vol

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
DEFAULT_PACKET_GLOB = "week2_trait_lane_prompt_sensitivity_packet_*.json"
DEFAULT_PROMPT_SUMMARY_GLOB = "week2_trait_lane_prompt_sensitivity_prompt_summary_*.json"
DEFAULT_EXTRACTION_ARTIFACT_GLOB = "week2_trait_lane_deeper_validation_extraction_*.json"
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_JUDGE_RPM_LIMIT = 180
DEFAULT_JUDGE_MIN_INTERVAL_SECONDS = 0.25
DEFAULT_JUDGE_MAX_ATTEMPTS = 6

app = modal.App(APP_NAME)


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _load_vectors_pt(path: Path) -> dict[str, dict[int, list[float]]]:
    payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected vector payload in {path}")
    out: dict[str, dict[int, list[float]]] = {}
    for trait, by_layer in payload.items():
        out[str(trait)] = {}
        for layer, vec in by_layer.items():
            out[str(trait)][int(layer)] = list(torch.as_tensor(vec, dtype=torch.float32).tolist())
    return out


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _same_layer_cosines(*, source_vectors: dict[int, list[float]], perturbed_vectors: dict[str, list[float]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for layer, source in sorted(source_vectors.items()):
        layer_key = str(int(layer))
        if layer_key not in perturbed_vectors:
            continue
        source_tensor = torch.as_tensor(source, dtype=torch.float32)
        perturbed_tensor = torch.as_tensor(perturbed_vectors[layer_key], dtype=torch.float32)
        out[layer_key] = float(torch.nn.functional.cosine_similarity(source_tensor, perturbed_tensor, dim=0).item())
    return out


def _evaluate_vector_gate(*, same_layer_cosines: dict[str, float], selected_layer: int, gate_cfg: dict[str, Any]) -> dict[str, Any]:
    if not same_layer_cosines:
        raise ValueError("No same-layer cosine comparisons available")
    selected_cosine = float(same_layer_cosines[str(int(selected_layer))])
    abs_drops = {layer: float(1.0 - cosine) for layer, cosine in same_layer_cosines.items()}
    max_abs_drop = max(abs_drops.values()) if abs_drops else 1.0
    selected_pass = bool(selected_cosine >= float(gate_cfg["selected_layer_cosine_ge"]))
    max_drop_pass = bool(max_abs_drop <= float(gate_cfg["all_layers_max_abs_drop_le"]))
    return {
        "same_layer_cosines_by_layer": same_layer_cosines,
        "selected_layer": int(selected_layer),
        "selected_layer_cosine": selected_cosine,
        "all_layers_abs_drop_from_source": abs_drops,
        "all_layers_max_abs_drop": max_abs_drop,
        "selected_layer_pass": selected_pass,
        "all_layers_max_abs_drop_pass": max_drop_pass,
        "overall_pass": bool(selected_pass and max_drop_pass),
    }


def _extract_smoke_metrics(smoke_report: dict[str, Any]) -> dict[str, Any]:
    lane_reports = smoke_report.get("lane_reports") or []
    if len(lane_reports) != 1:
        raise ValueError("Expected exactly one lane report")
    lane = lane_reports[0]
    selected = lane.get("selected_condition")
    if not isinstance(selected, dict):
        raise ValueError("Missing selected_condition in smoke report")
    baseline = lane.get("baseline_summary") or {}
    return {
        "lane_id": str(lane["lane_id"]),
        "selected_layer": int(selected["layer"]),
        "selected_alpha": float(selected["alpha"]),
        "baseline_low_mean": float(baseline.get("low_score_mean", 0.0)),
        "baseline_high_mean": float(baseline.get("high_score_mean", 0.0)),
        "baseline_coherence_mean": float(baseline.get("coherence_baseline_mean", 0.0)),
        "plus_mean": float(selected.get("plus_mean", 0.0)),
        "minus_mean": float(selected.get("minus_mean", 0.0)),
        "steering_shift_mean": float(selected["steering_shift_mean"]),
        "reversal_shift_mean": float(selected["reversal_shift_mean"]),
        "bidirectional_effect": float(selected["bidirectional_effect"]),
        "coherence_drop": float(selected["coherence_drop"]),
        "coherence_pass": bool(selected["coherence_pass"]),
        "row_details": list(selected.get("rows", [])),
    }


def _evaluate_behavior_retention(*, original_metrics: dict[str, Any], perturbed_metrics: dict[str, Any], gate_cfg: dict[str, Any]) -> dict[str, Any]:
    reference_sign = 1.0 if float(original_metrics["baseline_high_mean"]) >= float(original_metrics["baseline_low_mean"]) else -1.0

    def orient(metrics: dict[str, Any]) -> dict[str, float]:
        steering = reference_sign * float(metrics["steering_shift_mean"])
        reversal = reference_sign * float(metrics["reversal_shift_mean"])
        return {
            "reference_orientation_sign": reference_sign,
            "oriented_steering_shift_mean": steering,
            "oriented_reversal_shift_mean": reversal,
            "oriented_bidirectional_effect": steering + reversal,
        }

    original_oriented = orient(original_metrics)
    perturbed_oriented = orient(perturbed_metrics)
    original_effect = float(original_oriented["oriented_bidirectional_effect"])
    perturbed_effect = float(perturbed_oriented["oriented_bidirectional_effect"])
    if original_effect > 0.0:
        retention_fraction = float(perturbed_effect / original_effect)
    else:
        retention_fraction = 0.0
    effect_drop = float(max(0.0, original_effect - perturbed_effect))
    sign_preserved = bool(
        perturbed_oriented["oriented_steering_shift_mean"] > 0.0
        and perturbed_oriented["oriented_reversal_shift_mean"] > 0.0
    )
    return {
        "reference_orientation_sign": int(reference_sign),
        "original_oriented": original_oriented,
        "perturbed_oriented": perturbed_oriented,
        "retention_fraction_of_original_bidirectional_effect": retention_fraction,
        "absolute_effect_drop": effect_drop,
        "steering_and_reversal_sign_preserved": sign_preserved,
        "retention_fraction_pass": bool(retention_fraction >= float(gate_cfg["minimum_fraction_of_original_bidirectional_effect"])),
        "absolute_effect_drop_pass": bool(effect_drop <= float(gate_cfg["maximum_absolute_effect_drop"])),
        "sign_preserved_pass": sign_preserved,
        "overall_pass": bool(
            retention_fraction >= float(gate_cfg["minimum_fraction_of_original_bidirectional_effect"])
            and effect_drop <= float(gate_cfg["maximum_absolute_effect_drop"])
            and sign_preserved
        ),
    }


def _build_behavior_packet(*, packet: dict[str, Any], judge_model: str) -> dict[str, Any]:
    lane_id = str(packet["source_lane_id"])
    layer = int(packet["selected_reference_config"]["layer"])
    alpha = float(packet["selected_reference_config"]["alpha"])
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_prompt_sensitivity_behavior_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "readiness_artifact_path": packet.get("input_paths", {}).get("deeper_validation_packet_json"),
        "selected_lane_ids": [lane_id],
        "prompt_limit_per_lane": int(packet["subset_plan"]["heldout"]["n_rows"]),
        "judge_model": str(judge_model),
        "behavioral_smoke_profile": {
            "max_new_tokens": 96,
            "temperature": 0.0,
            "coherence_mode": "relative_only",
            "max_relative_coherence_drop": 10.0,
        },
        "lane_packets": [
            {
                "lane_id": lane_id,
                "family_id": "prompt_sensitivity_sidecar",
                "judge_rubric_id": lane_id,
                "screening_layers": [layer],
                "screening_alpha_grid": [alpha],
                "known_confounds": ["prompt_sensitivity_sidecar_selected_config_only"],
            }
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
def run_prompt_sensitivity_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    source_vectors: dict[str, dict[int, list[float]]],
    original_extraction_rows: list[dict[str, Any]],
    perturbed_extraction_rows: list[dict[str, Any]],
    original_heldout_rows: list[dict[str, Any]],
    perturbed_heldout_rows: list[dict[str, Any]],
    judge_model: str,
    judge_rpm_limit_per_run: int,
    judge_min_interval_seconds: float,
    judge_max_attempts: int,
    run_name: str,
) -> dict[str, Any]:
    lane_id = str(packet["source_lane_id"])
    layers = sorted(int(x) for x in source_vectors[lane_id].keys())
    extract_result = extract_vectors_remote.get_raw_f()(
        config=config,
        prompt_pairs={lane_id: perturbed_extraction_rows},
        traits=[lane_id],
        layers=layers,
        extraction_method="prompt_last",
        response_max_new_tokens=96,
        response_temperature=0.0,
        run_name=f"{run_name}-extract",
    )
    vector_gate = _evaluate_vector_gate(
        same_layer_cosines=_same_layer_cosines(
            source_vectors=source_vectors[lane_id],
            perturbed_vectors=extract_result["vectors"][lane_id],
        ),
        selected_layer=int(packet["selected_reference_config"]["layer"]),
        gate_cfg=dict(packet["evaluation_plan"]["extraction_vector_gate"]),
    )

    behavior_packet = _build_behavior_packet(packet=packet, judge_model=judge_model)
    trait_layer_map = {lane_id: int(packet["selected_reference_config"]["layer"])}
    selected_vectors = {
        lane_id: {
            str(trait_layer_map[lane_id]): source_vectors[lane_id][trait_layer_map[lane_id]],
        }
    }
    original_smoke = run_behavioral_smoke_remote.get_raw_f()(
        config=config,
        packet=behavior_packet,
        vectors=selected_vectors,
        trait_layer_map=trait_layer_map,
        heldout_prompt_pairs={lane_id: original_heldout_rows},
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=f"{run_name}-original",
    )
    perturbed_smoke = run_behavioral_smoke_remote.get_raw_f()(
        config=config,
        packet=behavior_packet,
        vectors=selected_vectors,
        trait_layer_map=trait_layer_map,
        heldout_prompt_pairs={lane_id: perturbed_heldout_rows},
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=f"{run_name}-perturbed",
    )
    behavior_retention = _evaluate_behavior_retention(
        original_metrics=_extract_smoke_metrics(original_smoke["report"]),
        perturbed_metrics=_extract_smoke_metrics(perturbed_smoke["report"]),
        gate_cfg=dict(packet["evaluation_plan"]["behavior_retention_gate"]),
    )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_prompt_sensitivity_execution",
        "prompt_sensitivity_packet": packet,
        "perturbed_extract_vectors": extract_result["summary"],
        "vector_gate": vector_gate,
        "behavior_original": original_smoke["report"],
        "behavior_perturbed": perturbed_smoke["report"],
        "behavior_retention": behavior_retention,
        "overall_status": (
            "retained"
            if vector_gate["overall_pass"] and behavior_retention["overall_pass"]
            else "prompt_fragile"
        ),
        "modal_artifacts": {
            "perturbed_extract_summary_path": extract_result["modal_artifacts"]["summary_path"],
            "perturbed_extract_vectors_path": extract_result["modal_artifacts"]["vectors_path"],
            "original_smoke_report_path": original_smoke.get("modal_report_path"),
            "perturbed_smoke_report_path": perturbed_smoke.get("modal_report_path"),
        },
        "notes": [
            "Behavior retention reuses the original selected vector at the frozen selected layer/alpha; it does not re-select a new configuration on the perturbed prompts.",
            "Vector retention is evaluated against the persisted split-extraction source vectors, not a freshly re-extracted source baseline.",
        ],
    }
    modal_report_path = Path("/models/persona-circuits/trait-lanes-v2") / (
        f"prompt_sensitivity_execution_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    modal_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"report": report, "modal_report_path": str(modal_report_path)}


def build_prompt_sensitivity_execution_packet(
    *,
    packet: dict[str, Any],
    packet_path: Path,
    prompt_summary: dict[str, Any],
    prompt_summary_path: Path,
    extraction_artifact: dict[str, Any],
    extraction_artifact_path: Path,
    judge_model: str,
) -> dict[str, Any]:
    source_vectors_path = extraction_artifact["local_artifacts"]["vectors_path"]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_prompt_sensitivity_execution_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "prompt_sensitivity_packet_path": str(packet_path),
        "prompt_summary_path": str(prompt_summary_path),
        "source_extraction_artifact_path": str(extraction_artifact_path),
        "source_vectors_path": str(source_vectors_path),
        "source_lane_id": str(packet["source_lane_id"]),
        "selected_reference_config": dict(packet["selected_reference_config"]),
        "subset_plan": dict(packet["subset_plan"]),
        "evaluation_plan": dict(packet["evaluation_plan"]),
        "output_prompt_paths": dict(prompt_summary["output_prompt_paths"]),
        "judge_model": str(judge_model),
        "launch_recommended_now": True,
        "notes": [
            "This execution packet is bounded to the preselected politeness subset and the frozen selected config.",
            "The sidecar is diagnostic only; it does not reopen branch promotion by itself.",
        ],
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-sensitivity-json", type=Path, default=None)
    parser.add_argument("--prompt-summary-json", type=Path, default=None)
    parser.add_argument("--source-extraction-json", type=Path, default=None)
    parser.add_argument("--judge-model", type=str, default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--judge-rpm-limit-per-run", type=int, default=DEFAULT_JUDGE_RPM_LIMIT)
    parser.add_argument("--judge-min-interval-seconds", type=float, default=DEFAULT_JUDGE_MIN_INTERVAL_SECONDS)
    parser.add_argument("--judge-max-attempts", type=int, default=DEFAULT_JUDGE_MAX_ATTEMPTS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--run-name", type=str, default="")
    return parser


def _execute(
    *,
    prompt_sensitivity_json: Path | None,
    prompt_summary_json: Path | None,
    source_extraction_json: Path | None,
    judge_model: str,
    judge_rpm_limit_per_run: int,
    judge_min_interval_seconds: float,
    judge_max_attempts: int,
    dry_run: bool,
    output_json: Path | None,
    run_name: str,
) -> None:
    packet_path = prompt_sensitivity_json or _latest_result_path(DEFAULT_PACKET_GLOB)
    prompt_summary_path = prompt_summary_json or _latest_result_path(DEFAULT_PROMPT_SUMMARY_GLOB)
    extraction_artifact_path = source_extraction_json or _latest_result_path(DEFAULT_EXTRACTION_ARTIFACT_GLOB)
    packet = _load_json(packet_path)
    prompt_summary = _load_json(prompt_summary_path)
    extraction_artifact = _load_json(extraction_artifact_path)
    execution_packet = build_prompt_sensitivity_execution_packet(
        packet=packet,
        packet_path=packet_path,
        prompt_summary=prompt_summary,
        prompt_summary_path=prompt_summary_path,
        extraction_artifact=extraction_artifact,
        extraction_artifact_path=extraction_artifact_path,
        judge_model=judge_model,
    )

    if output_json is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = (
            f"week2_trait_lane_prompt_sensitivity_execution_packet_{stamp}.json"
            if dry_run
            else f"week2_trait_lane_prompt_sensitivity_execution_{stamp}.json"
        )
        out_path = RESULTS_DIR / filename
    else:
        out_path = output_json if output_json.is_absolute() else ROOT / output_json

    if dry_run:
        out_path.write_text(json.dumps(execution_packet, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_json": str(out_path), "dry_run": True}, indent=2))
        return

    config = _load_config()
    lane_id = str(packet["source_lane_id"])
    source_extraction_rows = _select_rows(
        _load_jsonl(Path(packet["source_prompt_paths"]["extraction"])),
        [int(x) for x in packet["subset_plan"]["extraction"]["row_ids"]],
    )
    source_heldout_rows = _select_rows(
        _load_jsonl(Path(packet["source_prompt_paths"]["heldout"])),
        [int(x) for x in packet["subset_plan"]["heldout"]["row_ids"]],
    )
    perturbed_extraction_rows = _load_jsonl(Path(prompt_summary["output_prompt_paths"]["extraction"]))
    perturbed_heldout_rows = _load_jsonl(Path(prompt_summary["output_prompt_paths"]["heldout"]))
    source_vectors = _load_vectors_pt(Path(execution_packet["source_vectors_path"]))
    registry = load_trait_lane_registry()
    load_trait_lane_registry()  # keep parity with branch scripts / fail early on config errors
    del registry

    resolved_run_name = run_name.strip() or f"trait-lane-prompt-sensitivity-{lane_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    result = run_prompt_sensitivity_remote.remote(
        config=config,
        packet=packet,
        source_vectors=source_vectors,
        original_extraction_rows=source_extraction_rows,
        perturbed_extraction_rows=perturbed_extraction_rows,
        original_heldout_rows=source_heldout_rows,
        perturbed_heldout_rows=perturbed_heldout_rows,
        judge_model=judge_model,
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=resolved_run_name,
    )
    combined = result["report"]
    combined["execution_packet"] = execution_packet
    combined["prompt_summary_path"] = str(prompt_summary_path)
    combined["source_extraction_artifact_path"] = str(extraction_artifact_path)
    out_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": str(out_path),
                "overall_status": combined["overall_status"],
                "vector_gate_pass": combined["vector_gate"]["overall_pass"],
                "behavior_retention_pass": combined["behavior_retention"]["overall_pass"],
                "modal_report_path": result.get("modal_report_path"),
            },
            indent=2,
        )
    )


def _select_rows(rows: list[dict[str, Any]], row_ids: list[int]) -> list[dict[str, Any]]:
    row_map = {int(row["id"]): row for row in rows}
    return [dict(row_map[int(rid)]) for rid in row_ids]


@app.local_entrypoint()
def main(
    prompt_sensitivity_json: str = "",
    prompt_summary_json: str = "",
    source_extraction_json: str = "",
    judge_model: str = DEFAULT_JUDGE_MODEL,
    judge_rpm_limit_per_run: int = DEFAULT_JUDGE_RPM_LIMIT,
    judge_min_interval_seconds: float = DEFAULT_JUDGE_MIN_INTERVAL_SECONDS,
    judge_max_attempts: int = DEFAULT_JUDGE_MAX_ATTEMPTS,
    dry_run: bool = False,
    output_json: str = "",
    run_name: str = "",
) -> None:
    _execute(
        prompt_sensitivity_json=Path(prompt_sensitivity_json).resolve() if prompt_sensitivity_json.strip() else None,
        prompt_summary_json=Path(prompt_summary_json).resolve() if prompt_summary_json.strip() else None,
        source_extraction_json=Path(source_extraction_json).resolve() if source_extraction_json.strip() else None,
        judge_model=judge_model,
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        dry_run=bool(dry_run),
        output_json=Path(output_json) if output_json.strip() else None,
        run_name=run_name,
    )


def cli_main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    _execute(
        prompt_sensitivity_json=args.prompt_sensitivity_json,
        prompt_summary_json=args.prompt_summary_json,
        source_extraction_json=args.source_extraction_json,
        judge_model=args.judge_model,
        judge_rpm_limit_per_run=int(args.judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(args.judge_min_interval_seconds),
        judge_max_attempts=int(args.judge_max_attempts),
        dry_run=bool(args.dry_run),
        output_json=args.output_json,
        run_name=args.run_name,
    )


if __name__ == "__main__":
    cli_main()
