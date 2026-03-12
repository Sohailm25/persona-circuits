"""Resolve Week 2 trait scope using existing closeout + remediation artifacts.

This script produces a traceable artifact that formalizes:
- hallucination status for Stage 1 claims,
- evil lane split (harmful-content vs machiavellian disposition),
- recommended Stage 2 decomposition scope.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def _latest_result_path(glob_pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(glob_pattern))
    if not matches:
        raise FileNotFoundError(f"No files found for pattern: {glob_pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_nested(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _trait_selected(ingestion_payload: dict[str, Any], trait: str) -> dict[str, Any]:
    trait_payload = _get_nested(ingestion_payload, ["traits", trait], {})
    return {
        "selected_layer": _get_nested(trait_payload, ["section623", "selected_layer"]),
        "selected_alpha": _get_nested(trait_payload, ["section623", "selected_alpha"]),
        "section623_pass": _get_nested(trait_payload, ["section623", "overall_pass"]),
        "runner_overall_pass": _get_nested(trait_payload, ["runner_quality_gates", "overall_pass"]),
    }


def _extract_external_transfer(gap_payload: dict[str, Any], trait: str) -> dict[str, Any]:
    trait_payload = _get_nested(gap_payload, ["external_transfer", trait], {})
    return {
        "pass": trait_payload.get("pass"),
        "plus_vs_minus": trait_payload.get("plus_vs_minus"),
        "baseline_vs_minus": trait_payload.get("baseline_vs_minus"),
    }


def _extract_ab_similarity(gap_payload: dict[str, Any], trait: str) -> dict[str, Any]:
    trait_payload = _get_nested(gap_payload, ["extraction_method_ab", trait], {})
    return {
        "method_cosine_similarity": trait_payload.get("method_cosine_similarity"),
        "threshold": trait_payload.get("threshold"),
        "pass": trait_payload.get("pass"),
    }


def _extract_overlap(reanalysis_payload: dict[str, Any], trait: str) -> dict[str, Any]:
    trait_payload = _get_nested(reanalysis_payload, ["traits", trait], {})
    return {
        "classification": trait_payload.get("overlap_classification"),
        "passes": trait_payload.get("passes"),
        "mean_cosine": _get_nested(trait_payload, ["source_metrics", "mean_cosine"]),
        "positive_fraction": _get_nested(trait_payload, ["source_metrics", "positive_fraction"]),
        "sign_test_p": _get_nested(trait_payload, ["significance", "sign_test_two_sided_p"]),
    }


def _extract_response_mean_lane(response_mean_payload: dict[str, Any], trait: str) -> dict[str, Any]:
    trait_payload = _get_nested(response_mean_payload, ["method_comparison", trait], {})
    return {
        "selected_prompt_last": _get_nested(trait_payload, ["selected", "prompt_last"]),
        "selected_response_mean": _get_nested(trait_payload, ["selected", "response_mean"]),
        "overall_pass_prompt_last": _get_nested(trait_payload, ["quality_gates", "overall_pass", "prompt_last"]),
        "overall_pass_response_mean": _get_nested(trait_payload, ["quality_gates", "overall_pass", "response_mean"]),
        "failing_gates_prompt_last": _get_nested(trait_payload, ["failing_gates", "prompt_last"], []),
        "failing_gates_response_mean": _get_nested(trait_payload, ["failing_gates", "response_mean"], []),
        "bidirectional_effect_prompt_last": _get_nested(trait_payload, ["metrics", "bidirectional_effect", "prompt_last"]),
        "bidirectional_effect_response_mean": _get_nested(trait_payload, ["metrics", "bidirectional_effect", "response_mean"]),
        "delta_bidirectional_effect": _get_nested(trait_payload, ["metrics", "bidirectional_effect", "delta"]),
        "cross_trait_bleed_prompt_last": _get_nested(trait_payload, ["metrics", "cross_trait_bleed_ratio", "prompt_last"]),
        "cross_trait_bleed_response_mean": _get_nested(trait_payload, ["metrics", "cross_trait_bleed_ratio", "response_mean"]),
        "delta_cross_trait_bleed": _get_nested(trait_payload, ["metrics", "cross_trait_bleed_ratio", "delta"]),
    }


def _classify_hallucination(*, section623_pass: Any, overlap_classification: str | None) -> str:
    if section623_pass is False and overlap_classification == "null_overlap":
        return "negative_finding_stage1"
    if section623_pass is True:
        return "provisionally_validated"
    return "unresolved"


def _classify_evil_harmful_lane(*, external_pass: Any, baseline_vs_minus: Any) -> str:
    if external_pass is False and isinstance(baseline_vs_minus, (int, float)) and baseline_vs_minus < 0:
        return "disconfirmed_bidirectional_harmful_content"
    if external_pass is True:
        return "supported"
    return "unresolved"


def _classify_evil_machiavellian_lane(
    *,
    overlap_classification: str | None,
    overlap_passes: Any,
    response_mean_overall_pass: Any,
    response_mean_failed_gates: list[str],
) -> str:
    if overlap_passes is True and overlap_classification in {"moderate_overlap", "weak_overlap"}:
        if response_mean_overall_pass is True:
            return "supported_and_week2_validated"
        if "coherence_pass" in response_mean_failed_gates:
            return "supported_but_week2_not_validated_due_to_coherence"
        return "supported_but_week2_not_validated"
    return "unresolved"


def build_trait_scope_resolution(
    *,
    ingestion_payload: dict[str, Any],
    gap_payload: dict[str, Any],
    reanalysis_payload: dict[str, Any],
    response_mean_payload: dict[str, Any],
    ingestion_path: Path,
    gap_path: Path,
    reanalysis_path: Path,
    response_mean_path: Path,
) -> dict[str, Any]:
    sycophancy_selected = _trait_selected(ingestion_payload, "sycophancy")
    evil_selected = _trait_selected(ingestion_payload, "evil")
    hallucination_selected = _trait_selected(ingestion_payload, "hallucination")

    hallucination_overlap = _extract_overlap(reanalysis_payload, "hallucination")
    hallucination_ab = _extract_ab_similarity(gap_payload, "hallucination")

    evil_external = _extract_external_transfer(gap_payload, "evil")
    evil_overlap = _extract_overlap(reanalysis_payload, "evil")
    evil_response_mean = _extract_response_mean_lane(response_mean_payload, "evil")

    syc_response_mean = _extract_response_mean_lane(response_mean_payload, "sycophancy")

    hallucination_status = _classify_hallucination(
        section623_pass=hallucination_selected["section623_pass"],
        overlap_classification=hallucination_overlap["classification"],
    )

    evil_harmful_status = _classify_evil_harmful_lane(
        external_pass=evil_external["pass"],
        baseline_vs_minus=evil_external["baseline_vs_minus"],
    )
    evil_machiavellian_status = _classify_evil_machiavellian_lane(
        overlap_classification=evil_overlap["classification"],
        overlap_passes=evil_overlap["passes"],
        response_mean_overall_pass=evil_response_mean["overall_pass_response_mean"],
        response_mean_failed_gates=list(evil_response_mean["failing_gates_response_mean"]),
    )

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_scope_resolution",
        "inputs": {
            "ingestion_artifact": str(ingestion_path),
            "gap_check_artifact": str(gap_path),
            "extraction_free_reanalysis_artifact": str(reanalysis_path),
            "response_mean_sensitivity_artifact": str(response_mean_path),
        },
        "evidence_status": {
            "input_artifacts": "known",
            "lane_classifications": "inferred",
            "stage2_scope_recommendation": "inferred",
        },
        "trait_scope": {
            "sycophancy": {
                "selected_primary_combo": {
                    "layer": sycophancy_selected["selected_layer"],
                    "alpha": sycophancy_selected["selected_alpha"],
                },
                "week2_section623_pass": sycophancy_selected["section623_pass"],
                "week2_runner_overall_pass": sycophancy_selected["runner_overall_pass"],
                "response_mean_lane": syc_response_mean,
                "status": "retain_as_primary_trait_pending_coherence_remediation",
            },
            "evil": {
                "selected_primary_combo": {
                    "layer": evil_selected["selected_layer"],
                    "alpha": evil_selected["selected_alpha"],
                },
                "harmful_content_lane": {
                    "external_transfer": evil_external,
                    "status": evil_harmful_status,
                },
                "machiavellian_disposition_lane": {
                    "extraction_free_overlap": evil_overlap,
                    "response_mean_lane": evil_response_mean,
                    "status": evil_machiavellian_status,
                },
                "lane_split_decision": "split_required",
            },
            "hallucination": {
                "selected_primary_combo": {
                    "layer": hallucination_selected["selected_layer"],
                    "alpha": hallucination_selected["selected_alpha"],
                },
                "week2_section623_pass": hallucination_selected["section623_pass"],
                "week2_runner_overall_pass": hallucination_selected["runner_overall_pass"],
                "extraction_free_overlap": hallucination_overlap,
                "extraction_ab_similarity": hallucination_ab,
                "status": hallucination_status,
            },
        },
        "stage2_scope_recommendation": {
            "primary_claim_traits": ["sycophancy", "machiavellian_disposition"],
            "exploratory_control_traits": ["hallucination_instruction_following_control"],
            "blocked_claim_lanes": ["evil_harmful_content_bidirectionality"],
        },
        "known": [
            "Hallucination fails Section 6.2.3 in primary ingestion and is null-overlap in extraction-free reanalysis.",
            "Evil harmful-content transfer fails directional reversal (baseline_vs_minus < 0).",
            "Evil machiavellian lane shows moderate extraction-free overlap but still fails Week 2 overall due to coherence.",
            "Response-mean switch improves selected metrics for sycophancy/evil but does not produce overall pass.",
        ],
        "unknown": [
            "Whether coherence failures can be resolved without collapsing steering effect in a superseding remediation tranche.",
            "Whether an evil construct-aligned external benchmark will show bidirectional transfer for the machiavellian lane.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingestion-artifact", default="")
    parser.add_argument("--gap-check-artifact", default="")
    parser.add_argument("--reanalysis-artifact", default="")
    parser.add_argument("--response-mean-artifact", default="")
    args = parser.parse_args()

    ingestion_path = (
        Path(args.ingestion_artifact)
        if args.ingestion_artifact
        else _latest_result_path("week2_primary_postrun_ingestion_*220017Z.json")
    )
    gap_path = (
        Path(args.gap_check_artifact)
        if args.gap_check_artifact
        else _latest_result_path("week2_prelaunch_gap_checks_*.json")
    )
    reanalysis_path = (
        Path(args.reanalysis_artifact)
        if args.reanalysis_artifact
        else _latest_result_path("week2_extraction_free_reanalysis_*.json")
    )
    response_mean_path = (
        Path(args.response_mean_artifact)
        if args.response_mean_artifact
        else _latest_result_path("week2_response_mean_sensitivity_*.json")
    )

    payload = build_trait_scope_resolution(
        ingestion_payload=_load_json(ingestion_path),
        gap_payload=_load_json(gap_path),
        reanalysis_payload=_load_json(reanalysis_path),
        response_mean_payload=_load_json(response_mean_path),
        ingestion_path=ingestion_path,
        gap_path=gap_path,
        reanalysis_path=reanalysis_path,
        response_mean_path=response_mean_path,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_trait_scope_resolution_{ts}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "hallucination_status": payload["trait_scope"]["hallucination"]["status"],
                "evil_harmful_lane_status": payload["trait_scope"]["evil"]["harmful_content_lane"]["status"],
                "evil_machiavellian_lane_status": payload["trait_scope"]["evil"]["machiavellian_disposition_lane"]["status"],
                "primary_claim_traits": payload["stage2_scope_recommendation"]["primary_claim_traits"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
