"""Run the matched trait-lane null-control screen using the existing screening kernels."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import yaml

APP_NAME = "persona-circuits-week2-trait-lane-null-control"

try:
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        get_lane_config,
        load_trait_lane_registry,
    )
    from scripts.week2_trait_lane_behavioral_smoke_run import image, run_trait_lane_screening_remote, vol
except ModuleNotFoundError:  # pragma: no cover
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import (
        DEFAULT_REGISTRY_PATH,
        build_lane_screening_plan,
        get_lane_config,
        load_trait_lane_registry,
    )
    from scripts.week2_trait_lane_behavioral_smoke_run import image, run_trait_lane_screening_remote, vol

ROOT = Path(__file__).resolve().parents[1]
app = modal.App(APP_NAME)
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
DEFAULT_NULL_CONTROL_GLOB = "week2_trait_lane_null_control_packet_*.json"
DEFAULT_PROMPT_SUMMARY_GLOB = "week2_trait_lane_null_control_prompt_summary_*.json"
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_PROMPT_LIMIT = 4
DEFAULT_EXTRACTION_METHOD = "prompt_last"


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _latest_result_path_by_artifact_type(pattern: str, artifact_type: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    for path in reversed(matches):
        try:
            payload = _load_json(path)
        except Exception:
            continue
        if str(payload.get("artifact_type", "")) == artifact_type:
            return path
    raise FileNotFoundError(
        f"No artifacts matched pattern={pattern!r} with artifact_type={artifact_type!r} in {RESULTS_DIR}"
    )


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


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _promotion_thresholds(registry: dict[str, Any], lane_cfg: dict[str, Any]) -> dict[str, float]:
    defaults = registry.get("defaults") or {}
    profile_name = str(lane_cfg.get("promotion_gate_profile", "persona_screen_v1"))
    profile = (defaults.get("promotion_profiles") or {}).get(profile_name, {})
    if not isinstance(profile, dict):
        raise ValueError(f"Unknown promotion profile: {profile_name}")
    return {
        "min_bootstrap_p05_cosine": float(profile.get("min_bootstrap_p05_cosine", 0.8)),
        "min_train_vs_heldout_cosine": float(profile.get("min_train_vs_heldout_cosine", 0.7)),
        "min_behavioral_shift": float(profile.get("min_behavioral_shift", 10.0)),
        "max_relative_coherence_drop": float(profile.get("max_relative_coherence_drop", 10.0)),
    }


def build_null_control_execution_packet(
    *,
    registry: dict[str, Any],
    null_control_packet: dict[str, Any],
    null_control_packet_path: Path,
    prompt_summary: dict[str, Any],
    prompt_summary_path: Path,
    judge_model: str,
    prompt_limit: int,
) -> dict[str, Any]:
    source_lane_id = str(null_control_packet["source_lane_id"])
    control_id = str(prompt_summary["control_id"])
    source_lane_cfg = get_lane_config(registry, source_lane_id)
    source_plan = build_lane_screening_plan(registry, lane_ids=[source_lane_id])[0]
    defaults = registry.get("defaults") or {}
    smoke_profile = defaults.get("behavioral_smoke_profile") or {}
    promotion_profile_name = str(source_lane_cfg.get("promotion_gate_profile", "persona_screen_v1"))
    promotion_profile = (defaults.get("promotion_profiles") or {}).get(promotion_profile_name, {})
    prompt_paths = prompt_summary["output_prompt_paths"]

    condition_rows: list[dict[str, Any]] = []
    for layer in source_plan["screening_layers"]:
        for alpha in source_plan["screening_alpha_grid"]:
            condition_rows.append(
                {
                    "lane_id": control_id,
                    "source_lane_id": source_lane_id,
                    "layer": int(layer),
                    "alpha": float(alpha),
                    "judge_rubric_id": str(source_lane_cfg["judge_rubric_id"]),
                }
            )

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_null_control_execution_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "readiness_artifact_path": str(null_control_packet_path),
        "null_control_packet_path": str(null_control_packet_path),
        "prompt_summary_path": str(prompt_summary_path),
        "selected_lane_ids": [control_id],
        "source_lane_id": source_lane_id,
        "prompt_limit_per_lane": int(prompt_limit),
        "judge_model": str(judge_model),
        "extraction_method": DEFAULT_EXTRACTION_METHOD,
        "behavioral_smoke_profile": smoke_profile,
        "promotion_profile": promotion_profile,
        "lane_packets": [
            {
                "lane_id": control_id,
                "source_lane_id": source_lane_id,
                "family_id": "null_control",
                "display_name": f"{source_lane_cfg['display_name']} Null Control",
                "judge_rubric_id": str(source_lane_cfg["judge_rubric_id"]),
                "requires_ground_truth": bool(source_lane_cfg.get("requires_ground_truth", False)),
                "supports_extraction_free": False,
                "supports_external_transfer": False,
                "prompt_paths": {
                    "extraction": str(prompt_paths["extraction"]),
                    "heldout": str(prompt_paths["heldout"]),
                },
                "screening_layers": [int(x) for x in source_plan["screening_layers"]],
                "screening_alpha_grid": [float(x) for x in source_plan["screening_alpha_grid"]],
                "known_confounds": list(source_lane_cfg.get("known_confounds", [])),
                "control_metadata": {
                    "control_id": control_id,
                    "design_type": str(null_control_packet["recommended_control_design"]["design_type"]),
                    "source_lane_id": source_lane_id,
                },
            }
        ],
        "condition_matrix": {
            "n_rows": len(condition_rows),
            "rows": condition_rows,
        },
        "launch_recommended_now": True,
        "notes": [
            "This packet reuses the exact trait-lane screening kernels against a matched label-permutation control.",
            "It is deliberately written to a distinct artifact prefix so normal promotion-packet globbing cannot accidentally consume it.",
        ],
    }


def _evaluate_control_outcome(
    *,
    registry: dict[str, Any],
    source_lane_id: str,
    screening_report: dict[str, Any],
    null_control_packet: dict[str, Any],
) -> dict[str, Any]:
    control_id = screening_report["selected_lane_ids"][0]
    lane_cfg = get_lane_config(registry, source_lane_id)
    thresholds = _promotion_thresholds(registry, lane_cfg)
    lane_report = screening_report["behavioral_smoke"]["lane_reports"][0]
    selected = lane_report["selected_condition"] or {}
    if not selected:
        raise ValueError("Null-control screening report missing selected_condition")
    bootstrap_trait = ((screening_report.get("bootstrap_robustness") or {}).get("traits") or {}).get(control_id) or {}
    bootstrap_summary = ((bootstrap_trait.get("bootstrap") or {}).get("pairwise_cosine_summary") or {})
    position_layer = ((((screening_report.get("position_ablation") or {}).get("diagnostics") or {}).get(control_id) or {}).get("layers") or {}).get(str(selected["layer"])) or {}
    pairwise_cosines = position_layer.get("pairwise_cosines") or {}

    baseline = lane_report.get("baseline_summary") or {}
    baseline_low = float(baseline.get("low_score_mean", 0.0))
    baseline_high = float(baseline.get("high_score_mean", 0.0))
    orientation_sign = 1.0 if baseline_high >= baseline_low else -1.0
    oriented_steering = orientation_sign * float(selected["steering_shift_mean"])
    oriented_reversal = orientation_sign * float(selected["reversal_shift_mean"])
    oriented_bidirectional = orientation_sign * float(selected["bidirectional_effect"])
    aligned_component_pass = bool(oriented_steering > 0.0 and oriented_reversal > 0.0)

    bootstrap_p05 = float(bootstrap_summary.get("p05", 0.0))
    train_vs_heldout = float(bootstrap_trait.get("train_vs_heldout_vector_cosine", 0.0))
    response_phase_persistence = float(pairwise_cosines.get("prompt_last_vs_response_mean") or 0.0)
    bootstrap_pass = bool(
        bootstrap_p05 >= thresholds["min_bootstrap_p05_cosine"]
        and train_vs_heldout >= thresholds["min_train_vs_heldout_cosine"]
    )
    coherence_pass = bool(
        bool(selected.get("coherence_pass", False))
        and float(selected["coherence_drop"]) <= thresholds["max_relative_coherence_drop"]
    )
    behavioral_shift_pass = bool(
        oriented_bidirectional >= thresholds["min_behavioral_shift"] and aligned_component_pass
    )
    response_phase_persistence_pass = bool(response_phase_persistence >= 0.7)

    if behavioral_shift_pass and bootstrap_pass and coherence_pass and response_phase_persistence_pass:
        screening_status = "promotion_candidate_strong"
    elif behavioral_shift_pass and bootstrap_pass and coherence_pass:
        screening_status = "followon_candidate_with_limitation"
    elif oriented_bidirectional >= thresholds["min_behavioral_shift"] and not aligned_component_pass:
        screening_status = "orientation_review"
    elif oriented_bidirectional > 0.0 and bootstrap_pass and coherence_pass:
        screening_status = "weak_positive_hold"
    else:
        screening_status = "hold"

    alerts = null_control_packet["evaluation_plan"]["false_positive_alerts"]
    promotion_frontier_crossed = screening_status != "hold"
    overall_false_positive_alert = bool(
        promotion_frontier_crossed
        and oriented_bidirectional >= float(alerts["oriented_bidirectional_effect_ge"])
    )

    return {
        "source_lane_id": source_lane_id,
        "control_lane_id": control_id,
        "selected_layer": int(selected["layer"]),
        "selected_alpha": float(selected["alpha"]),
        "baseline_low_score_mean": baseline_low,
        "baseline_high_score_mean": baseline_high,
        "orientation_sign": int(orientation_sign),
        "oriented_steering_shift_mean": oriented_steering,
        "oriented_reversal_shift_mean": oriented_reversal,
        "oriented_bidirectional_effect": oriented_bidirectional,
        "absolute_bidirectional_effect": float(abs(float(selected["bidirectional_effect"]))),
        "aligned_component_pass": aligned_component_pass,
        "coherence_pass": coherence_pass,
        "coherence_drop": float(selected["coherence_drop"]),
        "bootstrap_p05_cosine": bootstrap_p05,
        "train_vs_heldout_cosine": train_vs_heldout,
        "bootstrap_pass": bootstrap_pass,
        "response_phase_persistence": response_phase_persistence,
        "response_phase_persistence_pass": response_phase_persistence_pass,
        "screening_status": screening_status,
        "promotion_frontier_crossed": promotion_frontier_crossed,
        "false_positive_alerts": {
            "promotion_status_not_hold": bool(promotion_frontier_crossed),
            "oriented_bidirectional_effect_ge_threshold": bool(
                oriented_bidirectional >= float(alerts["oriented_bidirectional_effect_ge"])
            ),
            "bootstrap_p05_cosine_ge_threshold": bool(
                bootstrap_p05 >= float(alerts["bootstrap_p05_cosine_ge"])
            ),
            "response_phase_persistence_ge_threshold": bool(
                response_phase_persistence >= float(alerts["response_phase_persistence_ge"])
            ),
            "overall_false_positive_alert": overall_false_positive_alert,
        },
        "thresholds": thresholds,
        "interpretation": (
            "potential_false_positive_pipeline_behavior"
            if overall_false_positive_alert
            else "null_control_remains_below_promotion_frontier"
        ),
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
def run_null_control_screening_remote(
    *,
    config: dict[str, Any],
    packet: dict[str, Any],
    train_prompt_pairs: dict[str, list[dict[str, Any]]],
    heldout_prompt_pairs: dict[str, list[dict[str, Any]]],
    candidate_layers: list[int],
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
    return run_trait_lane_screening_remote.get_raw_f()(
        config=config,
        packet=packet,
        train_prompt_pairs=train_prompt_pairs,
        heldout_prompt_pairs=heldout_prompt_pairs,
        candidate_layers=candidate_layers,
        extraction_method=str(packet["extraction_method"]),
        response_max_new_tokens=int(response_max_new_tokens),
        response_temperature=float(response_temperature),
        robustness_subset_size=int(robustness_subset_size),
        robustness_n_bootstrap=int(robustness_n_bootstrap),
        position_ablation_pairs=int(position_ablation_pairs),
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=run_name,
    )


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--null-control-json", type=Path, default=None)
    parser.add_argument("--prompt-summary-json", type=Path, default=None)
    parser.add_argument("--judge-model", type=str, default=DEFAULT_JUDGE_MODEL)
    parser.add_argument("--prompt-limit", type=int, default=DEFAULT_PROMPT_LIMIT)
    parser.add_argument("--judge-rpm-limit-per-run", type=int, default=180)
    parser.add_argument("--judge-min-interval-seconds", type=float, default=0.25)
    parser.add_argument("--judge-max-attempts", type=int, default=6)
    parser.add_argument("--robustness-subset-size", type=int, default=20)
    parser.add_argument("--robustness-n-bootstrap", type=int, default=12)
    parser.add_argument("--position-ablation-pairs", type=int, default=12)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--run-name", type=str, default="")
    return parser


def _execute(
    *,
    null_control_json: Path | None,
    prompt_summary_json: Path | None,
    judge_model: str,
    prompt_limit: int,
    judge_rpm_limit_per_run: int,
    judge_min_interval_seconds: float,
    judge_max_attempts: int,
    robustness_subset_size: int,
    robustness_n_bootstrap: int,
    position_ablation_pairs: int,
    dry_run: bool,
    output_json: Path | None,
    run_name: str,
) -> None:
    if int(prompt_limit) <= 0:
        raise ValueError("prompt_limit must be > 0")

    registry = load_trait_lane_registry()
    null_control_path = null_control_json or _latest_result_path_by_artifact_type(
        DEFAULT_NULL_CONTROL_GLOB, "week2_trait_lane_null_control_packet"
    )
    prompt_summary_path = prompt_summary_json or _latest_result_path_by_artifact_type(
        DEFAULT_PROMPT_SUMMARY_GLOB, "week2_trait_lane_null_control_prompt_summary"
    )
    null_control_packet = _load_json(null_control_path)
    prompt_summary = _load_json(prompt_summary_path)
    packet = build_null_control_execution_packet(
        registry=registry,
        null_control_packet=null_control_packet,
        null_control_packet_path=null_control_path,
        prompt_summary=prompt_summary,
        prompt_summary_path=prompt_summary_path,
        judge_model=judge_model,
        prompt_limit=int(prompt_limit),
    )

    if output_json is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = (
            f"week2_trait_lane_null_control_execution_packet_{timestamp}.json"
            if dry_run
            else f"week2_trait_lane_null_control_execution_{timestamp}.json"
        )
        out_path = RESULTS_DIR / filename
    else:
        out_path = output_json if output_json.is_absolute() else ROOT / output_json

    if dry_run:
        out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_json": str(out_path), "dry_run": True}, indent=2))
        return

    config = _load_config()
    control_id = str(prompt_summary["control_id"])
    train_prompt_pairs = {control_id: _load_jsonl(Path(prompt_summary["output_prompt_paths"]["extraction"]))}
    heldout_prompt_pairs = {control_id: _load_jsonl(Path(prompt_summary["output_prompt_paths"]["heldout"]))}
    candidate_layers = sorted({int(layer) for layer in packet["lane_packets"][0]["screening_layers"]})
    smoke_profile = packet["behavioral_smoke_profile"]
    resolved_run_name = run_name.strip() or f"trait-lane-null-control-{control_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    screening_result = run_null_control_screening_remote.remote(
        config=config,
        packet=packet,
        train_prompt_pairs=train_prompt_pairs,
        heldout_prompt_pairs=heldout_prompt_pairs,
        candidate_layers=candidate_layers,
        response_max_new_tokens=int(smoke_profile.get("max_new_tokens", 96)),
        response_temperature=float(smoke_profile.get("temperature", 0.0)),
        robustness_subset_size=int(robustness_subset_size),
        robustness_n_bootstrap=int(robustness_n_bootstrap),
        position_ablation_pairs=int(position_ablation_pairs),
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        run_name=resolved_run_name,
    )

    screening_report = screening_result["report"]
    evaluation = _evaluate_control_outcome(
        registry=registry,
        source_lane_id=str(packet["source_lane_id"]),
        screening_report=screening_report,
        null_control_packet=null_control_packet,
    )
    combined = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_null_control_execution",
        "null_control_packet_path": str(null_control_path),
        "prompt_summary_path": str(prompt_summary_path),
        "execution_packet": packet,
        "screening_execution": screening_report,
        "evaluation": evaluation,
        "modal_report_path": screening_result.get("modal_report_path"),
        "notes": [
            "This artifact is the matched false-positive control for the trait-lane branch redesign.",
            "Interpretation should compare the control outcome against the real politeness lane promotion frontier, not against deeper-validation gates.",
        ],
    }
    out_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": str(out_path),
                "control_lane_id": control_id,
                "screening_status": evaluation["screening_status"],
                "overall_false_positive_alert": evaluation["false_positive_alerts"]["overall_false_positive_alert"],
                "modal_report_path": screening_result.get("modal_report_path"),
            },
            indent=2,
        )
    )


@app.local_entrypoint()
def main(
    null_control_json: str = "",
    prompt_summary_json: str = "",
    judge_model: str = DEFAULT_JUDGE_MODEL,
    prompt_limit: int = DEFAULT_PROMPT_LIMIT,
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
    _execute(
        null_control_json=Path(null_control_json).resolve() if null_control_json.strip() else None,
        prompt_summary_json=Path(prompt_summary_json).resolve() if prompt_summary_json.strip() else None,
        judge_model=judge_model,
        prompt_limit=int(prompt_limit),
        judge_rpm_limit_per_run=int(judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(judge_min_interval_seconds),
        judge_max_attempts=int(judge_max_attempts),
        robustness_subset_size=int(robustness_subset_size),
        robustness_n_bootstrap=int(robustness_n_bootstrap),
        position_ablation_pairs=int(position_ablation_pairs),
        dry_run=bool(dry_run),
        output_json=Path(output_json) if output_json.strip() else None,
        run_name=run_name,
    )


def cli_main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    _execute(
        null_control_json=args.null_control_json,
        prompt_summary_json=args.prompt_summary_json,
        judge_model=args.judge_model,
        prompt_limit=int(args.prompt_limit),
        judge_rpm_limit_per_run=int(args.judge_rpm_limit_per_run),
        judge_min_interval_seconds=float(args.judge_min_interval_seconds),
        judge_max_attempts=int(args.judge_max_attempts),
        robustness_subset_size=int(args.robustness_subset_size),
        robustness_n_bootstrap=int(args.robustness_n_bootstrap),
        position_ablation_pairs=int(args.position_ablation_pairs),
        dry_run=bool(args.dry_run),
        output_json=args.output_json,
        run_name=args.run_name,
    )


if __name__ == "__main__":
    cli_main()
