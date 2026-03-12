#!/usr/bin/env python3
"""Build Stage5 policy closure packet for comparability + multiple-testing gates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "stage5_cross_persona"

DEFAULT_STAGE5_ANALYSIS = (
    "results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T195835Z.json"
)
DEFAULT_ROUTER_PVALUES = (
    "results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_20260310T195815Z.json"
)
DEFAULT_PLANNING_STUB = (
    "results/stage5_cross_persona/week3_stage5_planning_stub_20260310T143354Z.json"
)


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _s5g2_status(stage5_analysis: Dict[str, Any]) -> Dict[str, Any]:
    policy = stage5_analysis.get("comparability_policy", {}).get("candidate_union", {})
    mixed_source = bool(policy.get("mixed_source_detected", False))
    source_consistent = bool(policy.get("source_consistent_gradient_available", False))
    interp = str(policy.get("cross_layer_gradient_interpretation", "unknown"))

    if not mixed_source:
        return {
            "status": "pass",
            "reason": "single_source_gradient_comparability",
            "mixed_source_detected": mixed_source,
            "source_consistent_gradient_available": source_consistent,
            "cross_layer_gradient_interpretation": interp,
        }
    if source_consistent:
        return {
            "status": "pass_with_limitation",
            "reason": "mixed_source_but_source_consistent_gradients_available",
            "mixed_source_detected": mixed_source,
            "source_consistent_gradient_available": source_consistent,
            "cross_layer_gradient_interpretation": interp,
        }
    return {
        "status": "fail",
        "reason": "mixed_source_without_source_consistent_gradient_support",
        "mixed_source_detected": mixed_source,
        "source_consistent_gradient_available": source_consistent,
        "cross_layer_gradient_interpretation": interp,
    }


def _s5g4_status(stage5_analysis: Dict[str, Any]) -> Dict[str, Any]:
    hook = stage5_analysis.get("router_multiple_testing_hooks", {}).get("candidate_union", {})
    available = bool(hook.get("available", False))
    if not available:
        return {
            "status": "fail",
            "reason": str(hook.get("reason", "hook_unavailable")),
            "available": False,
            "n_tested": None,
            "n_rejected": None,
            "fdr_alpha": hook.get("fdr_alpha"),
        }

    n_tested = int(hook.get("n_tested", 0))
    n_rejected = int(hook.get("n_rejected", 0))
    fdr_alpha = float(hook.get("fdr_alpha", 0.01))
    if n_tested <= 0:
        return {
            "status": "fail",
            "reason": "no_tested_candidates",
            "available": True,
            "n_tested": n_tested,
            "n_rejected": n_rejected,
            "fdr_alpha": fdr_alpha,
        }
    if n_rejected == 0:
        return {
            "status": "exploratory_null",
            "reason": "no_fdr_significant_router_candidates",
            "available": True,
            "n_tested": n_tested,
            "n_rejected": n_rejected,
            "fdr_alpha": fdr_alpha,
            "min_q_value": hook.get("min_q_value"),
        }
    return {
        "status": "pass_signal",
        "reason": "fdr_significant_router_candidates_detected",
        "available": True,
        "n_tested": n_tested,
        "n_rejected": n_rejected,
        "fdr_alpha": fdr_alpha,
        "min_q_value": hook.get("min_q_value"),
    }


def _recommendation(s5g2: Dict[str, Any], s5g4: Dict[str, Any]) -> Dict[str, Any]:
    g2 = str(s5g2.get("status", "unknown"))
    g4 = str(s5g4.get("status", "unknown"))

    if g2 == "fail" or g4 == "fail":
        return {
            "policy_decision": "blocked_pending_remediation",
            "launch_recommended_now": False,
            "rationale": "at least one required Stage5 gate is unresolved",
        }
    if g4 == "exploratory_null":
        return {
            "policy_decision": "lock_exploratory_null_with_optional_sensitivity_lane",
            "launch_recommended_now": False,
            "rationale": (
                "comparability gate is acceptable with explicit limitation; "
                "multiple-testing executed with no FDR-significant router candidates"
            ),
        }
    return {
        "policy_decision": "proceed_router_candidate_followup_lane",
        "launch_recommended_now": True,
        "rationale": "multiple-testing found router candidates; run follow-up causal checks",
    }


def build_policy_packet(
    *,
    stage5_analysis: Dict[str, Any],
    router_pvalues_payload: Dict[str, Any],
    planning_stub_payload: Dict[str, Any],
    stage5_analysis_path: str,
    router_pvalues_path: str,
    planning_stub_path: str,
) -> Dict[str, Any]:
    s5g2 = _s5g2_status(stage5_analysis)
    s5g4 = _s5g4_status(stage5_analysis)
    recommendation = _recommendation(s5g2, s5g4)

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage5_policy_decision_packet",
        "inputs": {
            "stage5_analysis_artifact": stage5_analysis_path,
            "router_pvalues_artifact": router_pvalues_path,
            "planning_stub_artifact": planning_stub_path,
        },
        "gate_closure": {
            "S5-G2_cross_layer_comparability": s5g2,
            "S5-G4_router_multiple_testing": s5g4,
        },
        "supporting_context": {
            "planning_blocking_items": planning_stub_payload.get("readiness", {}).get(
                "blocking_items", []
            ),
            "router_pvalue_summary": router_pvalues_payload.get("summary", {}),
            "analysis_gradient_summary_candidate_union": stage5_analysis.get(
                "gradient_summary", {}
            ).get("candidate_union", {}),
        },
        "recommendation": recommendation,
        "evidence_status": {
            "input_artifacts": "known",
            "gate_statuses": "known",
            "policy_recommendation": "inferred",
        },
    }


def _default_output_path() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OUT_DIR / f"week3_stage5_policy_decision_packet_{ts}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage5-analysis-artifact", default=DEFAULT_STAGE5_ANALYSIS)
    parser.add_argument("--router-pvalues-artifact", default=DEFAULT_ROUTER_PVALUES)
    parser.add_argument("--planning-stub-artifact", default=DEFAULT_PLANNING_STUB)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    stage5_path = _resolve_path(args.stage5_analysis_artifact)
    pvalues_path = _resolve_path(args.router_pvalues_artifact)
    planning_path = _resolve_path(args.planning_stub_artifact)

    stage5_analysis = _load_json(stage5_path)
    router_pvalues_payload = _load_json(pvalues_path)
    planning_stub_payload = _load_json(planning_path)

    packet = build_policy_packet(
        stage5_analysis=stage5_analysis,
        router_pvalues_payload=router_pvalues_payload,
        planning_stub_payload=planning_stub_payload,
        stage5_analysis_path=str(stage5_path),
        router_pvalues_path=str(pvalues_path),
        planning_stub_path=str(planning_path),
    )

    out_path = Path(args.output) if args.output else _default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
