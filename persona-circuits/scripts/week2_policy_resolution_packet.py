"""Build explicit policy-resolution packet for second-pass blockers SP-F1 and SP-F3."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_spf1(stage2_audit: dict[str, Any]) -> dict[str, Any]:
    align = stage2_audit.get("model_sae_alignment", {})
    claim_layers = [int(x) for x in align.get("primary_claim_layers_unique", [])]
    cross_layers = [int(x) for x in align.get("cross_check_sae_layers", [])]
    steering_layers = [int(x) for x in align.get("current_steering_layers", [])]
    overlap_claim = [int(x) for x in align.get("overlap_crosscheck_vs_claim_layers", [])]
    overlap_steering = sorted(set(cross_layers).intersection(set(steering_layers)))

    return {
        "status": "resolved_via_explicit_claim_scope_policy",
        "known": {
            "claim_layers": claim_layers,
            "cross_check_layers": cross_layers,
            "overlap_crosscheck_vs_claim_layers": overlap_claim,
            "overlap_crosscheck_vs_steering_layers": overlap_steering,
            "cross_source_claim_gate_status": stage2_audit.get("stage2_cross_source_claim_gate", {}).get("status"),
        },
        "policy_decision": {
            "decomposition_start_path": "primary_sae_single_source_allowed_at_selected_claim_layer",
            "cross_source_claim_path": "restricted_to_overlap_capable_sensitivity_layers",
            "cross_source_claim_allowed_on_selected_claim_layer": bool(len(overlap_claim) > 0),
            "cross_source_sensitivity_layers": overlap_steering,
            "required_for_cross_source_claims": [
                "run matched decomposition on overlap-capable layers using both SAE sources",
                "report cross-source agreement only on overlap-capable layers",
                "do not claim cross-source support for non-overlap claim layers",
            ],
        },
        "inferred": {
            "resolution_rationale": (
                "The structural contradiction is governance-resolved by separating decomposition-start scope "
                "from cross-source claim scope."
            )
        },
        "unknown": {
            "future_cross_source_agreement_outcome": "pending Stage2 execution on overlap-capable layers"
        },
    }


def _resolve_spf3(coherence_diag: dict[str, Any]) -> dict[str, Any]:
    mode = coherence_diag.get("mode_summary", {})
    trait_snapshots = coherence_diag.get("trait_snapshots", {})

    return {
        "status": "resolved_via_explicit_dual_scorecard_policy",
        "known": {
            "mode_summary": mode,
            "trait_snapshots": trait_snapshots,
        },
        "policy_decision": {
            "hardening_reliability_coherence_mode": "absolute_and_relative",
            "proposal_compatibility_coherence_mode": "relative_only",
            "require_dual_scorecard_reporting": True,
            "interpretation_guardrail": (
                "Relative-only coherence pass can support degradation-focused interpretation but does not by itself "
                "supersede hardening NO-GO without explicit governance decision."
            ),
        },
        "inferred": {
            "resolution_rationale": (
                "The coherence blocker is no longer policy-ambiguous: both strict and degradation-focused views "
                "are frozen and must be reported together."
            )
        },
        "unknown": {
            "future_superseding_decision": "requires explicit governance action after dual-scorecard review"
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage2-audit-artifact",
        default="results/stage2_decomposition/week3_sae_reconstruction_audit_20260303T132222Z.json",
    )
    parser.add_argument(
        "--coherence-diagnostic-artifact",
        default="results/stage1_extraction/week2_coherence_policy_diagnostic_20260303T132222Z.json",
    )
    args = parser.parse_args()

    stage2_path = ROOT / args.stage2_audit_artifact
    coherence_path = ROOT / args.coherence_diagnostic_artifact
    stage2 = _load(stage2_path)
    coherence = _load(coherence_path)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_policy_resolution_packet",
        "inputs": {
            "stage2_audit_artifact": str(stage2_path.relative_to(ROOT)),
            "coherence_diagnostic_artifact": str(coherence_path.relative_to(ROOT)),
        },
        "sp_f1_resolution": _resolve_spf1(stage2),
        "sp_f3_resolution": _resolve_spf3(coherence),
        "evidence_status": {
            "input_artifacts": "known",
            "policy_freeze": "known",
            "future_outcome": "unknown",
        },
    }

    out_path = RESULTS_DIR / f"week2_policy_resolution_packet_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output_path": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
