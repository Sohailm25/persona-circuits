"""Aggregate trait-lane screening evidence into a promotion packet."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
DEFAULT_READINESS_GLOB = "week2_trait_lane_screening_readiness_*.json"


REQUIRED_METRIC_KEYS = {
    "literature_support_score",
    "construct_clarity_score",
    "bootstrap_p05_cosine",
    "train_vs_heldout_cosine",
    "behavioral_shift",
    "relative_coherence_drop",
    "response_phase_persistence",
    "benchmark_smoke_pass",
    "confound_risk_penalty",
}


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Promotion source must be a JSON object: {path}")
    return raw


def _score_lane(metrics: dict[str, Any]) -> float:
    base = (
        float(metrics["literature_support_score"])
        + float(metrics["construct_clarity_score"])
        + float(metrics["bootstrap_p05_cosine"])
        + float(metrics["train_vs_heldout_cosine"])
        + float(metrics["behavioral_shift"])
        + float(metrics["response_phase_persistence"])
        + (1.0 if bool(metrics["benchmark_smoke_pass"]) else 0.0)
    )
    penalty = float(metrics["relative_coherence_drop"]) + float(metrics["confound_risk_penalty"])
    return base - penalty


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _reference_support_score(registry: dict[str, Any], lane_cfg: dict[str, Any]) -> float:
    family = (registry.get("families") or {}).get(str(lane_cfg["family_id"]), {})
    papers = family.get("reference_papers") or []
    return _clamp(float(len(papers)) / 2.0, 0.0, 1.0)


def _construct_clarity_score(readiness_row: dict[str, Any]) -> float:
    if not bool((readiness_row.get("checks") or {}).get("construct_card_present", False)):
        return 0.0
    confound_count = len(readiness_row.get("known_confounds", []))
    return _clamp(1.0 - 0.1 * confound_count, 0.0, 1.0)


def _prompt_quality_score(readiness_row: dict[str, Any]) -> float:
    prompt_quality = readiness_row.get("prompt_quality") or {}
    heldout_overlap = (prompt_quality.get("heldout_vs_extraction_overlap") or {})
    max_similarity = float(heldout_overlap.get("max_similarity", 1.0))
    duplicate_count = int((prompt_quality.get("extraction") or {}).get("duplicate_count", 0)) + int(
        (prompt_quality.get("heldout") or {}).get("duplicate_count", 0)
    )
    base = 1.0 if bool(prompt_quality.get("pass", False)) else 0.0
    overlap_penalty = _clamp((max_similarity - 0.5) / 0.3, 0.0, 1.0) * 0.5
    duplicate_penalty = 0.25 if duplicate_count > 0 else 0.0
    return _clamp(base - overlap_penalty - duplicate_penalty, 0.0, 1.0)


def _confound_risk_penalty(readiness_row: dict[str, Any]) -> float:
    confound_count = len(readiness_row.get("known_confounds", []))
    return _clamp(0.2 * confound_count, 0.0, 1.0)


def _readiness_lane_map(readiness_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lane_rows = readiness_payload.get("lane_rows")
    if not isinstance(lane_rows, list):
        raise ValueError("Readiness payload missing lane_rows.")
    output: dict[str, dict[str, Any]] = {}
    for row in lane_rows:
        if isinstance(row, dict) and row.get("lane_id"):
            output[str(row["lane_id"])] = row
    if not output:
        raise ValueError("Readiness payload contains no usable lane rows.")
    return output


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


def _screening_rank_key(row: dict[str, Any]) -> tuple[float, float, float, int, str]:
    status = str(row["screening_status"])
    status_rank = {
        "promotion_candidate_supported": 5.0,
        "promotion_candidate_strong": 4.0,
        "conditional_followon_candidate": 3.5,
        "followon_candidate_with_limitation": 3.0,
        "orientation_review": 2.0,
        "weak_positive_hold": 1.0,
        "deprioritized_after_followons": 0.5,
        "hold": 0.0,
    }.get(status, -1.0)
    return (
        status_rank,
        float(row["oriented_bidirectional_effect"]),
        float(row["bootstrap_p05_cosine"]),
        -int(row["priority_rank"]),
        str(row["lane_id"]),
    )


def _extract_screened_lane_rows(
    *,
    registry: dict[str, Any],
    readiness_payload: dict[str, Any],
    screening_executions: list[dict[str, Any]],
    screening_paths: list[Path],
) -> list[dict[str, Any]]:
    readiness_map = _readiness_lane_map(readiness_payload)
    rows: list[dict[str, Any]] = []
    for execution, execution_path in zip(screening_executions, screening_paths):
        lane_ids = execution.get("selected_lane_ids") or []
        bootstrap_traits = (execution.get("bootstrap_robustness") or {}).get("traits") or {}
        position_diags = (execution.get("position_ablation") or {}).get("diagnostics") or {}
        smoke_reports = (execution.get("behavioral_smoke") or {}).get("lane_reports") or []
        smoke_by_lane = {str(row["lane_id"]): row for row in smoke_reports if isinstance(row, dict) and row.get("lane_id")}

        for lane_id in lane_ids:
            lane_id = str(lane_id)
            lane_cfg = get_lane_config(registry, lane_id)
            readiness_row = readiness_map[lane_id]
            smoke_row = smoke_by_lane[lane_id]
            selected = smoke_row.get("selected_condition")
            if not isinstance(selected, dict):
                raise ValueError(f"Lane {lane_id} missing selected_condition in {execution_path}")
            selected_layer = int(selected["layer"])

            baseline = smoke_row.get("baseline_summary") or {}
            baseline_low = float(baseline.get("low_score_mean", 0.0))
            baseline_high = float(baseline.get("high_score_mean", 0.0))
            orientation_sign = 1.0 if baseline_high >= baseline_low else -1.0
            orientation_label = (
                "aligned_with_rubric_high_direction"
                if orientation_sign > 0
                else "inverted_relative_to_rubric_high_direction"
            )

            oriented_steering = orientation_sign * float(selected["steering_shift_mean"])
            oriented_reversal = orientation_sign * float(selected["reversal_shift_mean"])
            oriented_bidirectional = orientation_sign * float(selected["bidirectional_effect"])
            aligned_component_pass = bool(oriented_steering > 0.0 and oriented_reversal > 0.0)

            thresholds = _promotion_thresholds(registry, lane_cfg)
            bootstrap_trait = bootstrap_traits.get(lane_id) or {}
            bootstrap_p05 = float(
                (((bootstrap_trait.get("bootstrap") or {}).get("pairwise_cosine_summary") or {}).get("p05", 0.0))
            )
            train_vs_heldout = float(bootstrap_trait.get("train_vs_heldout_vector_cosine", 0.0))
            position_layer_diag = (((position_diags.get(lane_id) or {}).get("layers") or {}).get(str(selected_layer)) or {})
            response_phase_persistence = float(
                (((position_layer_diag.get("pairwise_cosines") or {}).get("prompt_last_vs_response_mean")) or 0.0)
            )

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

            pending_followons: list[str] = []
            if bool(lane_cfg.get("supports_extraction_free", False)):
                pending_followons.append("extraction_free_overlap_pending")
            if bool(lane_cfg.get("supports_external_transfer", False)):
                pending_followons.append("external_smoke_pending")

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

            rows.append(
                {
                    "lane_id": lane_id,
                    "display_name": readiness_row["display_name"],
                    "family_id": readiness_row["family_id"],
                    "priority_rank": int(readiness_row["priority_rank"]),
                    "persona_class": readiness_row["persona_class"],
                    "judge_rubric_id": readiness_row["judge_rubric_id"],
                    "screening_execution_path": str(execution_path),
                    "selected_layer": selected_layer,
                    "selected_alpha": float(selected["alpha"]),
                    "orientation_sign": int(orientation_sign),
                    "orientation_label": orientation_label,
                    "baseline_low_score_mean": baseline_low,
                    "baseline_high_score_mean": baseline_high,
                    "oriented_steering_shift_mean": oriented_steering,
                    "oriented_reversal_shift_mean": oriented_reversal,
                    "oriented_bidirectional_effect": oriented_bidirectional,
                    "aligned_component_pass": aligned_component_pass,
                    "coherence_drop": float(selected["coherence_drop"]),
                    "coherence_pass": coherence_pass,
                    "bootstrap_p05_cosine": bootstrap_p05,
                    "train_vs_heldout_cosine": train_vs_heldout,
                    "bootstrap_pass": bootstrap_pass,
                    "response_phase_persistence": response_phase_persistence,
                    "response_phase_persistence_pass": response_phase_persistence_pass,
                    "prompt_quality_audit_pass": bool((readiness_row.get("prompt_quality") or {}).get("pass", False)),
                    "prompt_quality_score": _prompt_quality_score(readiness_row),
                    "literature_support_score": _reference_support_score(registry, lane_cfg),
                    "construct_clarity_score": _construct_clarity_score(readiness_row),
                    "confound_risk_penalty": _confound_risk_penalty(readiness_row),
                    "thresholds": thresholds,
                    "screening_status": screening_status,
                    "pending_followons": pending_followons,
                }
            )
    return rows


def _classify_extraction_free_followon(report: dict[str, Any]) -> dict[str, Any]:
    metrics = report.get("metrics") or {}
    cosine_stats = metrics.get("cosine_stats") or {}
    projection_stats = metrics.get("projection_delta_stats") or {}
    classification = str(metrics.get("overlap_classification", "unknown"))
    passed = bool(metrics.get("passes", False))
    if passed:
        state = "pass"
    elif classification == "mixed_or_fragile":
        state = "mixed"
    elif classification == "weak_overlap":
        state = "weak"
    elif classification == "null_overlap":
        state = "fail"
    else:
        state = "mixed"
    return {
        "state": state,
        "pass": passed,
        "classification": classification,
        "mean_cosine": cosine_stats.get("mean"),
        "positive_fraction": metrics.get("positive_cosine_fraction"),
        "projection_delta_mean": projection_stats.get("mean"),
    }


def _classify_external_smoke_followon(report: dict[str, Any]) -> dict[str, Any]:
    metrics = report.get("metrics") or {}
    quality_gates = report.get("quality_gates") or metrics.get("quality_gates") or {}
    plus_vs_baseline = float(metrics.get("plus_vs_baseline", 0.0))
    baseline_vs_minus = float(metrics.get("baseline_vs_minus", 0.0))
    if bool(quality_gates.get("overall_pass", False)):
        state = "pass"
    elif bool(quality_gates.get("plus_vs_baseline_positive", False)) and bool(
        quality_gates.get("baseline_vs_minus_positive", False)
    ):
        state = "mixed"
    elif bool(quality_gates.get("plus_vs_baseline_positive", False)) or bool(
        quality_gates.get("baseline_vs_minus_positive", False)
    ):
        state = "one_sided"
    else:
        state = "fail"
    return {
        "state": state,
        "pass": bool(quality_gates.get("overall_pass", False)),
        "plus_vs_baseline": plus_vs_baseline,
        "baseline_vs_minus": baseline_vs_minus,
        "plus_vs_minus": metrics.get("plus_vs_minus"),
        "bidirectional_effect": metrics.get("bidirectional_effect"),
        "coherence_drop": metrics.get("coherence_drop"),
    }


def _lane_followon_state(
    *,
    row: dict[str, Any],
    extraction_free: dict[str, Any] | None,
    external_smoke: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    notes: list[str] = []
    if row["screening_status"] == "orientation_review":
        return "orientation_review", notes

    extraction_state = (extraction_free or {}).get("state", "not_applicable")
    external_state = (external_smoke or {}).get("state", "not_applicable")

    if extraction_state == "pass" and external_state in {"pass", "mixed", "one_sided", "not_applicable"}:
        if external_state != "pass" and external_state != "not_applicable":
            notes.append(f"external_smoke={external_state}")
        return "promotion_candidate_supported", notes

    if extraction_state == "fail" or external_state == "fail":
        notes.append(f"extraction_free={extraction_state}")
        notes.append(f"external_smoke={external_state}")
        return "deprioritized_after_followons", notes

    if extraction_state in {"mixed", "weak"} or external_state in {"mixed", "one_sided"}:
        notes.append(f"extraction_free={extraction_state}")
        notes.append(f"external_smoke={external_state}")
        return "conditional_followon_candidate", notes

    return row["screening_status"], notes


def _integrate_followon_artifacts(
    *,
    ranked_rows: list[dict[str, Any]],
    extraction_free_followons: list[tuple[Path, dict[str, Any]]],
    external_smoke_evals: list[tuple[Path, dict[str, Any]]],
) -> list[dict[str, Any]]:
    extraction_map: dict[str, dict[str, Any]] = {}
    for path, payload in extraction_free_followons:
        for report in payload.get("lane_reports", []):
            lane_id = str(report.get("lane_id", "")).strip()
            if not lane_id:
                continue
            extraction_map[lane_id] = {
                "artifact_path": str(path),
                **_classify_extraction_free_followon(report),
            }

    external_map: dict[str, dict[str, Any]] = {}
    for path, payload in external_smoke_evals:
        for report in payload.get("lane_reports", []):
            lane_id = str(report.get("lane_id", "")).strip()
            if not lane_id:
                continue
            external_map[lane_id] = {
                "artifact_path": str(path),
                **_classify_external_smoke_followon(report),
            }

    updated_rows: list[dict[str, Any]] = []
    for row in ranked_rows:
        lane_id = str(row["lane_id"])
        updated = dict(row)
        extraction_free = extraction_map.get(lane_id)
        external_smoke = external_map.get(lane_id)
        updated["followon_evidence"] = {
            "extraction_free": extraction_free,
            "external_smoke": external_smoke,
        }
        pending = list(updated.get("pending_followons", []))
        if extraction_free is not None:
            pending = [item for item in pending if item != "extraction_free_overlap_pending"]
        if external_smoke is not None:
            pending = [item for item in pending if item != "external_smoke_pending"]
        updated["pending_followons"] = pending

        if extraction_free is not None or external_smoke is not None:
            refreshed_status, status_notes = _lane_followon_state(
                row=updated,
                extraction_free=extraction_free,
                external_smoke=external_smoke,
            )
            updated["screening_status"] = refreshed_status
            updated["followon_status_notes"] = status_notes
        updated_rows.append(updated)
    return updated_rows


def build_promotion_packet_from_executions(
    *,
    registry: dict[str, Any],
    readiness_payload: dict[str, Any],
    screening_executions: list[dict[str, Any]],
    screening_paths: list[Path],
    readiness_path: Path,
    extraction_free_followons: list[tuple[Path, dict[str, Any]]] | None = None,
    external_smoke_evals: list[tuple[Path, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    screened_rows = _extract_screened_lane_rows(
        registry=registry,
        readiness_payload=readiness_payload,
        screening_executions=screening_executions,
        screening_paths=screening_paths,
    )
    ranked_rows = screened_rows
    extraction_free_followons = extraction_free_followons or []
    external_smoke_evals = external_smoke_evals or []
    if extraction_free_followons or external_smoke_evals:
        ranked_rows = _integrate_followon_artifacts(
            ranked_rows=ranked_rows,
            extraction_free_followons=extraction_free_followons,
            external_smoke_evals=external_smoke_evals,
        )
    ranked_rows = sorted(ranked_rows, key=_screening_rank_key, reverse=True)
    response_phase_pass_count = sum(1 for row in ranked_rows if row["response_phase_persistence_pass"])
    candidate_rows = [
        row
        for row in ranked_rows
        if row["screening_status"]
        in {
            "promotion_candidate_supported",
            "promotion_candidate_strong",
            "conditional_followon_candidate",
            "followon_candidate_with_limitation",
        }
    ]
    orientation_review = [row["lane_id"] for row in ranked_rows if row["screening_status"] == "orientation_review"]

    if response_phase_pass_count == 0 and candidate_rows:
        response_phase_policy = {
            "status": "tracked_limitation_not_hard_gate",
            "hard_gate_counterfactual_candidate_count": 0,
            "screening_candidate_count_without_hard_gate": len(candidate_rows),
            "rationale": "All screened lanes miss the legacy 0.7 prompt-vs-response persistence threshold while several lanes show positive bounded screening signal; keep persistence explicit but do not let it silently zero the branch at screening depth.",
        }
    else:
        response_phase_policy = {
            "status": "retain_as_hard_gate",
            "hard_gate_counterfactual_candidate_count": response_phase_pass_count,
            "screening_candidate_count_without_hard_gate": len(candidate_rows),
            "rationale": "At least one screened lane clears the response-phase threshold, so persistence can still function as a screening discriminator.",
        }

    recommended_followon = [row["lane_id"] for row in candidate_rows[:3]]
    deprioritized_lanes = [
        row["lane_id"] for row in ranked_rows if row["screening_status"] == "deprioritized_after_followons"
    ]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_promotion_packet",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "readiness_artifact_path": str(readiness_path),
        "screening_execution_paths": [str(path) for path in screening_paths],
        "extraction_free_followon_paths": [str(path) for path, _ in extraction_free_followons],
        "external_smoke_eval_paths": [str(path) for path, _ in external_smoke_evals],
        "n_screened_lanes": len(ranked_rows),
        "screening_summary": {
            "n_candidate_or_strong": len(candidate_rows),
            "n_orientation_review": len(orientation_review),
            "n_response_phase_pass": response_phase_pass_count,
            "n_deprioritized_after_followons": len(deprioritized_lanes),
        },
        "response_phase_policy": response_phase_policy,
        "orientation_policy": {
            "status": "empirical_polarity_normalization_required",
            "rationale": "At least one screened lane uses an inverted rubric orientation relative to its high-vs-low construct, so promotion synthesis must require polarity-normalized component alignment before ranking.",
            "orientation_review_lanes": orientation_review,
        },
        "ranked_lanes": ranked_rows,
        "recommended_followon_lanes": recommended_followon,
        "deprioritized_lanes": deprioritized_lanes,
        "hold_lanes": [
            row["lane_id"]
            for row in ranked_rows
            if row["screening_status"] in {"weak_positive_hold", "hold"}
        ],
        "notes": [
            "This packet ranks screening-depth follow-on candidates; it does not auto-promote any lane into the core claim set.",
            "Pending follow-ons remain explicit per lane (for example extraction-free overlap and external smoke where supported).",
        ],
        "status": "screening_ranked_followons_integrated"
        if (extraction_free_followons or external_smoke_evals)
        else "screening_ranked_pending_followons",
    }


def build_promotion_packet(
    *,
    registry: dict[str, Any],
    screening_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    if not screening_reports:
        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "registry_path": str(DEFAULT_REGISTRY_PATH),
            "n_reports": 0,
            "missing_metrics": {},
            "ranked_lanes": [],
            "recommended_promotions": [],
            "status": "awaiting_complete_screening",
        }

    lanes: list[dict[str, Any]] = []
    missing_metrics: dict[str, list[str]] = {}
    for report in screening_reports:
        lane_id = str(report.get("lane_id", "")).strip()
        if not lane_id:
            raise ValueError("Each screening report must include lane_id.")
        lane_cfg = get_lane_config(registry, lane_id)
        metrics = report.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"Screening report for {lane_id} missing metrics.")
        missing = sorted(REQUIRED_METRIC_KEYS - set(metrics))
        if missing:
            missing_metrics[lane_id] = missing
            readiness = "incomplete"
            total_score = None
        else:
            readiness = "screened"
            total_score = _score_lane(metrics)
        lanes.append(
            {
                "lane_id": lane_id,
                "family_id": lane_cfg["family_id"],
                "display_name": lane_cfg["display_name"],
                "priority_rank": lane_cfg["priority_rank"],
                "readiness": readiness,
                "promotion_gate_profile": lane_cfg["promotion_gate_profile"],
                "metrics": metrics,
                "total_score": total_score,
            }
        )
    ranked = sorted(
        lanes,
        key=lambda row: (
            row["total_score"] is None,
            -(row["total_score"] if row["total_score"] is not None else -10**9),
            int(row["priority_rank"]),
            row["lane_id"],
        ),
    )
    promoted = [row["lane_id"] for row in ranked if row["total_score"] is not None][:3]
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "n_reports": len(screening_reports),
        "missing_metrics": missing_metrics,
        "ranked_lanes": ranked,
        "recommended_promotions": promoted,
        "status": "awaiting_complete_screening" if missing_metrics else "ranked",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screening-report", action="append", default=[], help="Path to a screening report JSON.")
    parser.add_argument(
        "--screening-execution",
        action="append",
        default=[],
        help="Path to a completed week2_trait_lane_screening_execution JSON artifact.",
    )
    parser.add_argument(
        "--readiness-json",
        default="",
        help="Path to the screening-readiness JSON artifact (defaults to latest).",
    )
    parser.add_argument(
        "--extraction-free-followon",
        action="append",
        default=[],
        help="Path to a completed week2_trait_lane_extraction_free_followon JSON artifact.",
    )
    parser.add_argument(
        "--external-smoke-eval",
        action="append",
        default=[],
        help="Path to a completed week2_trait_lane_external_smoke_eval JSON artifact.",
    )
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    registry = load_trait_lane_registry()
    if args.screening_execution:
        readiness_path = (
            Path(args.readiness_json).resolve() if args.readiness_json.strip() else _latest_result_path(DEFAULT_READINESS_GLOB)
        )
        screening_paths = [Path(path).resolve() for path in args.screening_execution]
        extraction_free_paths = [Path(path).resolve() for path in args.extraction_free_followon]
        external_smoke_paths = [Path(path).resolve() for path in args.external_smoke_eval]
        readiness_payload = _load_json(readiness_path)
        screening_executions = [_load_json(path) for path in screening_paths]
        extraction_free_followons = [(path, _load_json(path)) for path in extraction_free_paths]
        external_smoke_evals = [(path, _load_json(path)) for path in external_smoke_paths]
        packet = build_promotion_packet_from_executions(
            registry=registry,
            readiness_payload=readiness_payload,
            screening_executions=screening_executions,
            screening_paths=screening_paths,
            readiness_path=readiness_path,
            extraction_free_followons=extraction_free_followons,
            external_smoke_evals=external_smoke_evals,
        )
        n_reports = len(screening_paths)
    else:
        screening_reports = [_load_json(Path(path)) for path in args.screening_report]
        packet = build_promotion_packet(registry=registry, screening_reports=screening_reports)
        n_reports = len(screening_reports)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = RESULTS_DIR / f"week2_trait_lane_promotion_packet_{timestamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({"output_json": str(out_path), "n_reports": n_reports}, indent=2))


if __name__ == "__main__":
    main()
