#!/usr/bin/env python3
"""Compare Stage4 behavioral-ablation reference vs tranche runs."""

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


def _trait_payload(report: dict[str, Any], trait: str) -> dict[str, Any]:
    block = (report.get("results_by_trait", {}) or {}).get(trait)
    if not isinstance(block, dict):
        raise KeyError(f"Trait {trait!r} missing from results_by_trait.")
    return block


def _method_snapshot(trait_block: dict[str, Any], method: str) -> dict[str, Any]:
    payload = (trait_block.get("methods", {}) or {}).get(method)
    if not isinstance(payload, dict):
        raise KeyError(f"Method {method!r} missing in trait payload.")
    validity = payload.get("reduction_validity", {}) or {}
    n_valid = validity.get("n_valid_prompts")
    n_total = validity.get("n_total_prompts")
    valid_fraction = validity.get("valid_fraction")
    return {
        "observed_mean_reduction": payload.get("observed_mean_reduction"),
        "p_value_one_sided_ge": (payload.get("selectivity_vs_random", {}) or {}).get(
            "p_value_one_sided_ge"
        ),
        "a12": (payload.get("effect_sizes_vs_random_prompt_distribution", {}) or {}).get("a12"),
        "gates": {
            "necessity": bool(payload.get("necessity_threshold_pass", False)),
            "significance": bool(payload.get("selectivity_p_threshold_pass", False)),
            "a12": bool(payload.get("a12_threshold_pass", False)),
        },
        "validity": {
            "n_valid_prompts": n_valid,
            "n_total_prompts": n_total,
            "valid_fraction": valid_fraction,
        },
    }


def _delta(after: float | None, before: float | None) -> float | None:
    if after is None or before is None:
        return None
    return float(after) - float(before)


def _method_comparison(
    ref_block: dict[str, Any],
    tranche_block: dict[str, Any],
    method: str,
) -> dict[str, Any]:
    ref = _method_snapshot(ref_block, method)
    trn = _method_snapshot(tranche_block, method)
    flips = {
        gate: {"reference": ref["gates"][gate], "tranche": trn["gates"][gate]}
        for gate in ("necessity", "significance", "a12")
    }
    return {
        "reference": ref,
        "tranche": trn,
        "deltas": {
            "mean_reduction_delta": _delta(
                trn["observed_mean_reduction"], ref["observed_mean_reduction"]
            ),
            "p_value_delta": _delta(trn["p_value_one_sided_ge"], ref["p_value_one_sided_ge"]),
            "a12_delta": _delta(trn["a12"], ref["a12"]),
            "valid_fraction_delta": _delta(
                trn["validity"]["valid_fraction"], ref["validity"]["valid_fraction"]
            ),
            "n_valid_prompts_delta": _delta(
                trn["validity"]["n_valid_prompts"], ref["validity"]["n_valid_prompts"]
            ),
        },
        "gate_states": flips,
    }


def _summary_label(reference_valid_fraction: float | None, tranche_valid_fraction: float | None) -> str:
    if reference_valid_fraction is None or tranche_valid_fraction is None:
        return "unknown"
    if abs(float(tranche_valid_fraction) - float(reference_valid_fraction)) <= 0.1:
        return "stable"
    return "shifted"


def build_report(
    *,
    reference_report: dict[str, Any],
    tranche_report: dict[str, Any],
    trait: str,
    reference_artifact_path: str,
    tranche_artifact_path: str,
) -> dict[str, Any]:
    ref_block = _trait_payload(reference_report, trait)
    trn_block = _trait_payload(tranche_report, trait)

    per_method = {
        method: _method_comparison(ref_block, trn_block, method)
        for method in METHODS
    }

    ref_inputs = reference_report.get("inputs", {}) or {}
    trn_inputs = tranche_report.get("inputs", {}) or {}
    ref_thresholds = reference_report.get("thresholds", {}) or {}
    trn_thresholds = tranche_report.get("thresholds", {}) or {}

    reference_valid_fraction = per_method["resample"]["reference"]["validity"]["valid_fraction"]
    tranche_valid_fraction = per_method["resample"]["tranche"]["validity"]["valid_fraction"]

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage4_tranche_comparison",
        "trait": trait,
        "inputs": {
            "reference_artifact": reference_artifact_path,
            "tranche_artifact": tranche_artifact_path,
            "reference_inputs": {
                "n_prompts": ref_inputs.get("n_prompts"),
                "heldout_start_index": ref_inputs.get("heldout_start_index"),
                "random_baseline_samples": ref_inputs.get("random_baseline_samples"),
                "n_bootstrap": ref_inputs.get("n_bootstrap"),
            },
            "tranche_inputs": {
                "n_prompts": trn_inputs.get("n_prompts"),
                "heldout_start_index": trn_inputs.get("heldout_start_index"),
                "random_baseline_samples": trn_inputs.get("random_baseline_samples"),
                "n_bootstrap": trn_inputs.get("n_bootstrap"),
            },
        },
        "thresholds": {
            "reference": ref_thresholds,
            "tranche": trn_thresholds,
        },
        "baseline_effect_abs_mean": {
            "reference": ((ref_block.get("behavioral_score_baseline", {}) or {}).get("steered_effect_abs_summary", {}) or {}).get("mean"),
            "tranche": ((trn_block.get("behavioral_score_baseline", {}) or {}).get("steered_effect_abs_summary", {}) or {}).get("mean"),
            "delta": _delta(
                ((trn_block.get("behavioral_score_baseline", {}) or {}).get("steered_effect_abs_summary", {}) or {}).get("mean"),
                ((ref_block.get("behavioral_score_baseline", {}) or {}).get("steered_effect_abs_summary", {}) or {}).get("mean"),
            ),
        },
        "coverage_stability": {
            "label": _summary_label(reference_valid_fraction, tranche_valid_fraction),
            "reference_valid_fraction": reference_valid_fraction,
            "tranche_valid_fraction": tranche_valid_fraction,
            "delta": _delta(tranche_valid_fraction, reference_valid_fraction),
        },
        "per_method": per_method,
        "evidence_status": {
            "input_artifacts": "known",
            "tranche_stability_interpretation": "inferred",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Stage4 reference vs tranche behavioral artifacts.")
    parser.add_argument("--reference-artifact", required=True)
    parser.add_argument("--tranche-artifact", required=True)
    parser.add_argument("--trait", default="evil")
    args = parser.parse_args()

    reference_path = Path(args.reference_artifact)
    tranche_path = Path(args.tranche_artifact)
    if not reference_path.is_absolute():
        reference_path = ROOT / reference_path
    if not tranche_path.is_absolute():
        tranche_path = ROOT / tranche_path

    reference_report = _load(reference_path)
    tranche_report = _load(tranche_path)
    report = build_report(
        reference_report=reference_report,
        tranche_report=tranche_report,
        trait=str(args.trait),
        reference_artifact_path=str(reference_path.resolve()),
        tranche_artifact_path=str(tranche_path.resolve()),
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week3_stage4_tranche_comparison_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "trait": args.trait}, indent=2))


if __name__ == "__main__":
    main()

