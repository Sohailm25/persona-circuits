#!/usr/bin/env python3
"""Generate Stage4 H2 policy decision packet from latest diagnostic artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage4_ablation"
METHODS = ("resample", "mean", "zero")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _trait(report: dict[str, Any], trait: str) -> dict[str, Any]:
    payload = (report.get("results_by_trait", {}) or {}).get(trait)
    if not isinstance(payload, dict):
        raise KeyError(f"Missing trait={trait!r} in report.")
    return payload


def _method_block(trait_payload: dict[str, Any], method: str) -> dict[str, Any]:
    payload = (trait_payload.get("methods", {}) or {}).get(method)
    if not isinstance(payload, dict):
        raise KeyError(f"Missing method={method!r} in trait payload.")
    return payload


def _strict_pass_for_method(method_payload: dict[str, Any]) -> bool:
    return bool(
        method_payload.get("necessity_threshold_pass", False)
        and method_payload.get("selectivity_p_threshold_pass", False)
        and method_payload.get("a12_threshold_pass", False)
    )


def _run_snapshot(report: dict[str, Any], trait: str) -> dict[str, Any]:
    t = _trait(report, trait)
    out_methods: dict[str, Any] = {}
    any_full_pass = False
    for method in METHODS:
        block = _method_block(t, method)
        full_pass = _strict_pass_for_method(block)
        any_full_pass = any_full_pass or full_pass
        out_methods[method] = {
            "mean_reduction": block.get("observed_mean_reduction"),
            "p_value_one_sided_ge": (block.get("selectivity_vs_random", {}) or {}).get(
                "p_value_one_sided_ge"
            ),
            "a12": (block.get("effect_sizes_vs_random_prompt_distribution", {}) or {}).get("a12"),
            "strict_gate_pass": full_pass,
            "gate_flags": {
                "necessity": bool(block.get("necessity_threshold_pass", False)),
                "significance": bool(block.get("selectivity_p_threshold_pass", False)),
                "a12": bool(block.get("a12_threshold_pass", False)),
            },
        }

    coverage = (_method_block(t, "resample").get("reduction_validity", {}) or {}).get(
        "valid_fraction"
    )
    baseline_mean = ((t.get("behavioral_score_baseline", {}) or {}).get("steered_effect_abs_summary", {}) or {}).get("mean")

    return {
        "coverage_valid_fraction": coverage,
        "baseline_effect_abs_mean": baseline_mean,
        "any_method_strict_pass": any_full_pass,
        "methods": out_methods,
    }


def _find_analysis_for_artifact(
    threshold_diag: dict[str, Any],
    artifact_path: str,
    trait: str,
) -> dict[str, Any] | None:
    artifact_path_norm = str(Path(artifact_path).resolve())
    for row in threshold_diag.get("analyses", []) or []:
        if str(row.get("artifact_path")) == artifact_path_norm:
            return ((row.get("traits", {}) or {}).get(trait, {}) or {}).get("methods")
    return None


def _recommendation(snapshot: dict[str, Any]) -> dict[str, Any]:
    strict_pass = bool(snapshot["strict_summary"]["any_method_strict_pass_either_run"])
    ref_cov = snapshot["reference"]["coverage_valid_fraction"]
    trn_cov = snapshot["tranche"]["coverage_valid_fraction"]
    high_coverage = (
        ref_cov is not None
        and trn_cov is not None
        and float(ref_cov) >= 0.6
        and float(trn_cov) >= 0.6
    )
    if strict_pass:
        return {
            "recommended_path": "strict_go_path",
            "rationale": (
                "At least one method passes full strict Stage4 thresholds in observed runs."
            ),
            "evidence_status": "known",
        }
    if high_coverage:
        return {
            "recommended_path": "strict_fail_with_dual_scorecard_candidate",
            "rationale": (
                "Coverage is no longer limiting, but strict gates fail in both reference and tranche runs; "
                "policy choice should explicitly separate strict gate status from narrative interpretation."
            ),
            "evidence_status": "inferred",
        }
    return {
        "recommended_path": "collect_more_data_before_policy",
        "rationale": "Coverage remains low/uncertain and strict gates are unresolved.",
        "evidence_status": "inferred",
    }


def build_packet(
    *,
    reference_report: dict[str, Any],
    tranche_report: dict[str, Any],
    threshold_diag: dict[str, Any],
    tranche_comparison: dict[str, Any],
    reference_path: str,
    tranche_path: str,
    threshold_diag_path: str,
    tranche_comparison_path: str,
    trait: str,
) -> dict[str, Any]:
    reference = _run_snapshot(reference_report, trait)
    tranche = _run_snapshot(tranche_report, trait)
    strict_summary = {
        "any_method_strict_pass_reference": reference["any_method_strict_pass"],
        "any_method_strict_pass_tranche": tranche["any_method_strict_pass"],
        "any_method_strict_pass_either_run": bool(
            reference["any_method_strict_pass"] or tranche["any_method_strict_pass"]
        ),
    }
    threshold_methods = _find_analysis_for_artifact(threshold_diag, reference_path, trait)

    packet = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage4_policy_decision_packet",
        "trait": trait,
        "inputs": {
            "reference_artifact": str(Path(reference_path).resolve()),
            "tranche_artifact": str(Path(tranche_path).resolve()),
            "threshold_binding_diagnostic_artifact": str(Path(threshold_diag_path).resolve()),
            "tranche_comparison_artifact": str(Path(tranche_comparison_path).resolve()),
        },
        "reference": reference,
        "tranche": tranche,
        "strict_summary": strict_summary,
        "threshold_binding_reference_methods": threshold_methods,
        "tranche_comparison_summary": {
            "coverage_stability": tranche_comparison.get("coverage_stability"),
            "per_method_deltas": {
                method: ((tranche_comparison.get("per_method", {}) or {}).get(method, {}) or {}).get("deltas")
                for method in METHODS
            },
            "per_method_gate_states": {
                method: ((tranche_comparison.get("per_method", {}) or {}).get(method, {}) or {}).get("gate_states")
                for method in METHODS
            },
        },
        "policy_options": [
            {
                "id": "strict_only_continue",
                "description": "Keep strict thresholds authoritative and continue targeted reruns only.",
                "pros": ["Maintains strongest evidentiary bar", "Avoids interpretation drift"],
                "cons": ["May extend Stage4 loop with diminishing returns"],
            },
            {
                "id": "dual_scorecard_h2",
                "description": "Retain strict fail status while adding explicit secondary narrative interpretation lane.",
                "pros": [
                    "Acknowledges stable high-coverage effects",
                    "Preserves strict-governance traceability",
                ],
                "cons": ["Requires careful wording to avoid over-claiming"],
            },
        ],
        "recommendation": _recommendation(
            {"reference": reference, "tranche": tranche, "strict_summary": strict_summary}
        ),
        "evidence_status": {
            "input_artifacts": "known",
            "policy_recommendation": "inferred",
            "future_decision": "unknown",
        },
    }
    return packet


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Stage4 H2 policy decision packet.")
    parser.add_argument(
        "--reference-artifact",
        default="results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T001903Z.json",
    )
    parser.add_argument(
        "--tranche-artifact",
        default="results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T080841Z.json",
    )
    parser.add_argument(
        "--threshold-diagnostic-artifact",
        default="results/stage4_ablation/week3_stage4_threshold_binding_diagnostic_20260310T044638Z.json",
    )
    parser.add_argument(
        "--tranche-comparison-artifact",
        default="results/stage4_ablation/week3_stage4_tranche_comparison_20260310T141458Z.json",
    )
    parser.add_argument("--trait", default="evil")
    args = parser.parse_args()

    reference_path = (ROOT / args.reference_artifact).resolve()
    tranche_path = (ROOT / args.tranche_artifact).resolve()
    threshold_path = (ROOT / args.threshold_diagnostic_artifact).resolve()
    comparison_path = (ROOT / args.tranche_comparison_artifact).resolve()

    packet = build_packet(
        reference_report=_load(reference_path),
        tranche_report=_load(tranche_path),
        threshold_diag=_load(threshold_path),
        tranche_comparison=_load(comparison_path),
        reference_path=str(reference_path),
        tranche_path=str(tranche_path),
        threshold_diag_path=str(threshold_path),
        tranche_comparison_path=str(comparison_path),
        trait=str(args.trait),
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week3_stage4_policy_decision_packet_{ts}.json"
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "trait": args.trait}, indent=2))


if __name__ == "__main__":
    main()

