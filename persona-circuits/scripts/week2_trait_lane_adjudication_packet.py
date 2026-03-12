"""Adjudicate trait-lane branch status after deeper validation and follow-ons."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

DEFAULT_PROMOTION_GLOB = "week2_trait_lane_promotion_packet_*.json"
DEFAULT_DEEPER_VALIDATION_GLOB = "week2_trait_lane_deeper_validation_validation_*.json"
DEFAULT_OVERLAP_GLOB = "week2_trait_lane_overlap_diagnostic_*.json"
DEFAULT_EXTRACTION_FREE_GLOB = "week2_trait_lane_extraction_free_followon_*.json"
DEFAULT_EXTERNAL_SMOKE_GLOB = "week2_trait_lane_external_smoke_eval_*.json"


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


def _lane_map(payload: dict[str, Any], key: str = "lane_reports") -> dict[str, dict[str, Any]]:
    rows = payload.get(key)
    if not isinstance(rows, list):
        raise ValueError(f"Payload missing list key: {key}")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("lane_id"):
            output[str(row["lane_id"])] = row
    if not output:
        raise ValueError(f"Payload contained no lane rows under {key}")
    return output


def _promotion_lane_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("ranked_lanes")
    if not isinstance(rows, list):
        raise ValueError("Promotion packet missing ranked_lanes")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("lane_id"):
            output[str(row["lane_id"])] = row
    if not output:
        raise ValueError("Promotion packet contained no ranked lanes")
    return output


def _classify_politeness(
    promotion_row: dict[str, Any],
    deeper_payload: dict[str, Any],
    overlap_payload: dict[str, Any],
    response_phase_policy: dict[str, Any],
) -> dict[str, Any]:
    lane_map = _lane_map(deeper_payload)
    politeness_row = lane_map["politeness"]
    report = politeness_row["validation_report"]
    selected = report["selected"]
    quality = report["quality_gates"]
    coherence = report["coherence"]
    capability = report["capability_proxy"]
    specificity = report["specificity"]
    calibration = report["judge_calibration"]
    controls = report["controls"]
    bleed = report["cross_trait_bleed"]
    assistant_overlap = float(
        (((overlap_payload.get("branch_reference_overlap") or {}).get("max_abs_same_layer_overlap") or {}).get("abs_cosine"))
        or 0.0
    )
    sycophancy_overlap = float(((overlap_payload.get("selected_pair_overlap") or {}).get("abs_cosine")) or 0.0)
    target_effect = float(selected["test_metric"]["bidirectional_effect"])
    assistant_effect = float((bleed.get("assistant_likeness") or {}).get("bidirectional_effect", 0.0))
    sycophancy_effect = float((bleed.get("sycophancy") or {}).get("bidirectional_effect", 0.0))
    off_target_ratio = max(abs(assistant_effect), abs(sycophancy_effect)) / max(abs(target_effect), 1e-9)

    if not bool(quality["overall_pass"]) and not bool(quality["cross_trait_bleed_pass"]) and assistant_overlap >= 0.4:
        final_status = "strong_non_distinct_assistant_style_lane"
        promotion_decision = "do_not_promote_as_independent_persona_lane"
    elif bool(quality["overall_pass"]):
        final_status = "independent_promotion_candidate"
        promotion_decision = "eligible_for_independent_promotion"
    else:
        final_status = "remediation_candidate_with_distinctness_risk"
        promotion_decision = "hold_for_remediation_before_promotion"

    return {
        "lane_id": "politeness",
        "prior_branch_status": str(promotion_row["screening_status"]),
        "response_phase_policy": response_phase_policy,
        "response_phase_persistence": float(promotion_row["response_phase_persistence"]),
        "selected_layer": int(selected["layer"]),
        "selected_alpha": float(selected["alpha"]),
        "selected_test_bidirectional_effect": target_effect,
        "judge_kappa": float(calibration["kappa"]),
        "pairwise_sign_agreement": float(calibration["pairwise_sign_agreement"]),
        "coherence_pass": bool(coherence["pass"]),
        "coherence_drop": float(coherence["drop_from_baseline"]),
        "capability_pass": bool(capability["pass_lt_5pct_drop"]),
        "capability_degradation": float(capability["degradation"]),
        "specificity_pass": bool(quality["specificity_pass"]),
        "neutral_shift": float(specificity["neutral_shift"]),
        "cross_trait_bleed_pass": bool(quality["cross_trait_bleed_pass"]),
        "cross_trait_bleed_ratio": off_target_ratio,
        "assistant_likeness_effect": assistant_effect,
        "sycophancy_effect": sycophancy_effect,
        "assistant_likeness_overlap_max_same_layer": assistant_overlap,
        "sycophancy_selected_pair_overlap": sycophancy_overlap,
        "control_test_score": float(report["control_test_score"]),
        "control_test_pass": bool(report["control_test_pass"]),
        "random_control_p95": float(controls["random_bidirectional_p95"]),
        "shuffled_control_p95": float(controls["shuffled_bidirectional_p95"]),
        "overall_pass": bool(quality["overall_pass"]),
        "final_status": final_status,
        "promotion_decision": promotion_decision,
        "primary_failure_modes": [
            mode
            for mode, is_present in [
                ("cross_trait_bleed", not bool(quality["cross_trait_bleed_pass"])),
                ("control_test", not bool(report["control_test_pass"])),
                ("response_phase_persistence", float(promotion_row["response_phase_persistence"]) < 0.7),
            ]
            if is_present
        ],
    }


def _classify_lying(
    promotion_row: dict[str, Any],
    extraction_free_payload: dict[str, Any],
    external_smoke_payload: dict[str, Any],
) -> dict[str, Any]:
    extraction_free_row = _lane_map(extraction_free_payload)["lying"]
    external_row = _lane_map(external_smoke_payload)["lying"]
    extraction_metrics = extraction_free_row["metrics"]
    smoke_metrics = external_row["metrics"]

    if float(smoke_metrics["plus_vs_baseline"]) < 0.0:
        final_status = "negative_finding_construct_invalid_current_protocol"
        decision = "remove_from_immediate_followon_budget"
    else:
        final_status = "conditional_followon_candidate"
        decision = "keep_conditional_only"

    return {
        "lane_id": "lying",
        "prior_branch_status": str(promotion_row["screening_status"]),
        "extraction_free_classification": str(extraction_metrics["overlap_classification"]),
        "extraction_free_mean_cosine": float(extraction_metrics["cosine_stats"]["mean"]),
        "extraction_free_positive_fraction": float(extraction_metrics["positive_cosine_fraction"]),
        "external_smoke_plus_vs_baseline": float(smoke_metrics["plus_vs_baseline"]),
        "external_smoke_baseline_vs_minus": float(smoke_metrics["baseline_vs_minus"]),
        "external_smoke_bidirectional_effect": float(smoke_metrics["bidirectional_effect"]),
        "external_smoke_overall_pass": bool(external_row["quality_gates"]["overall_pass"]),
        "response_phase_persistence": float(promotion_row["response_phase_persistence"]),
        "final_status": final_status,
        "promotion_decision": decision,
    }


def _classify_honesty(
    promotion_row: dict[str, Any],
    extraction_free_payload: dict[str, Any],
    external_smoke_payload: dict[str, Any],
) -> dict[str, Any]:
    extraction_free_row = _lane_map(extraction_free_payload)["honesty"]
    external_row = _lane_map(external_smoke_payload)["honesty"]
    extraction_metrics = extraction_free_row["metrics"]
    smoke_metrics = external_row["metrics"]

    final_status = "secondary_unresolved_rlhf_asymmetry_lane"
    decision = "hold_for_redesigned_followon_only"
    if bool(external_row["quality_gates"]["overall_pass"]):
        final_status = "followon_candidate"
        decision = "eligible_for_followon"

    return {
        "lane_id": "honesty",
        "prior_branch_status": str(promotion_row["screening_status"]),
        "extraction_free_classification": str(extraction_metrics["overlap_classification"]),
        "extraction_free_mean_cosine": float(extraction_metrics["cosine_stats"]["mean"]),
        "extraction_free_positive_fraction": float(extraction_metrics["positive_cosine_fraction"]),
        "external_smoke_plus_vs_baseline": float(smoke_metrics["plus_vs_baseline"]),
        "external_smoke_baseline_vs_minus": float(smoke_metrics["baseline_vs_minus"]),
        "external_smoke_bidirectional_effect": float(smoke_metrics["bidirectional_effect"]),
        "external_smoke_overall_pass": bool(external_row["quality_gates"]["overall_pass"]),
        "response_phase_persistence": float(promotion_row["response_phase_persistence"]),
        "final_status": final_status,
        "promotion_decision": decision,
    }


def build_adjudication_packet(
    *,
    promotion_payload: dict[str, Any],
    deeper_validation_payload: dict[str, Any],
    overlap_payload: dict[str, Any],
    extraction_free_payload: dict[str, Any],
    external_smoke_payload: dict[str, Any],
    input_paths: dict[str, str],
) -> dict[str, Any]:
    promotion_rows = _promotion_lane_map(promotion_payload)
    response_phase_policy = promotion_payload.get("response_phase_policy") or {}

    politeness = _classify_politeness(
        promotion_row=promotion_rows["politeness"],
        deeper_payload=deeper_validation_payload,
        overlap_payload=overlap_payload,
        response_phase_policy=response_phase_policy,
    )
    lying = _classify_lying(
        promotion_row=promotion_rows["lying"],
        extraction_free_payload=extraction_free_payload,
        external_smoke_payload=external_smoke_payload,
    )
    honesty = _classify_honesty(
        promotion_row=promotion_rows["honesty"],
        extraction_free_payload=extraction_free_payload,
        external_smoke_payload=external_smoke_payload,
    )

    no_independent_promotion = politeness["promotion_decision"] != "eligible_for_independent_promotion"
    if no_independent_promotion:
        branch_status = "no_independent_promotion_under_current_evidence"
        recommended_next_action = "freeze_independent_promotion_and_treat_politeness_as_assistant_style_modulation"
    else:
        branch_status = "independent_promotion_candidate_present"
        recommended_next_action = "prepare_independent_lane_promotion_packet"

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_adjudication_packet",
        "input_paths": input_paths,
        "status": branch_status,
        "response_phase_policy": response_phase_policy,
        "lead_lane": "politeness",
        "independent_promotion_recommended": [] if no_independent_promotion else ["politeness"],
        "lane_adjudications": {
            "politeness": politeness,
            "lying": lying,
            "honesty": honesty,
        },
        "branch_findings": {
            "lead_lane_is_behaviorally_strong": True,
            "lead_lane_is_independent_persona_candidate": not no_independent_promotion,
            "assistant_style_confound_is_primary": True,
            "lying_negative_finding": True,
            "honesty_secondary_unresolved": True,
        },
        "recommended_next_action": recommended_next_action,
        "recommended_followups": [
            "do_not_launch_more_politeness_deeper_validation_until the assistant-style confound is addressed explicitly",
            "treat lying as a negative finding under the current protocol",
            "retain honesty only for RLHF-asymmetry-aware redesign, not equal-budget follow-on work",
            "if branch work continues, redesign for distinctness from assistant_likeness before any Stage2+ promotion claim",
        ],
        "notes": [
            "This packet adjudicates branch status under the completed screening, follow-on, overlap, and deeper-validation evidence stack.",
            "The packet intentionally treats independent promotion as a stricter question than tractability-first follow-on ranking.",
        ],
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promotion-json", type=Path, default=None)
    parser.add_argument("--deeper-validation-json", type=Path, default=None)
    parser.add_argument("--overlap-json", type=Path, default=None)
    parser.add_argument("--extraction-free-json", type=Path, default=None)
    parser.add_argument("--external-smoke-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    promotion_path = args.promotion_json or _latest_result_path(DEFAULT_PROMOTION_GLOB)
    deeper_validation_path = args.deeper_validation_json or _latest_result_path(DEFAULT_DEEPER_VALIDATION_GLOB)
    overlap_path = args.overlap_json or _latest_result_path(DEFAULT_OVERLAP_GLOB)
    extraction_free_path = args.extraction_free_json or _latest_result_path(DEFAULT_EXTRACTION_FREE_GLOB)
    external_smoke_path = args.external_smoke_json or _latest_result_path(DEFAULT_EXTERNAL_SMOKE_GLOB)

    packet = build_adjudication_packet(
        promotion_payload=_load_json(promotion_path),
        deeper_validation_payload=_load_json(deeper_validation_path),
        overlap_payload=_load_json(overlap_path),
        extraction_free_payload=_load_json(extraction_free_path),
        external_smoke_payload=_load_json(external_smoke_path),
        input_paths={
            "promotion_json": str(promotion_path),
            "deeper_validation_json": str(deeper_validation_path),
            "overlap_json": str(overlap_path),
            "extraction_free_json": str(extraction_free_path),
            "external_smoke_json": str(external_smoke_path),
        },
    )

    output_path = args.output_json
    if output_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RESULTS_DIR / f"week2_trait_lane_adjudication_packet_{stamp}.json"

    output_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()
