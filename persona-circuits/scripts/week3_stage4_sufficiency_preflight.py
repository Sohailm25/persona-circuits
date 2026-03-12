#!/usr/bin/env python3
"""Launch-free Stage4 sufficiency preflight + dry-run validation artifact."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Sequence

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
OUT_DIR = ROOT / "results" / "stage4_ablation"
HELDOUT_DIR = ROOT / "prompts" / "heldout"

DEFAULT_TARGET_FREEZE_ARTIFACT = (
    "results/stage4_ablation/week3_stage4_target_set_freeze_20260304T164918Z.json"
)
DEFAULT_INGESTION_ARTIFACT = (
    "results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json"
)
DEFAULT_TRAITS = "sycophancy,evil"
DEFAULT_METHODS = "resample,mean"
DEFAULT_DOSE_RESPONSE = "0.25,0.5,0.75,1.0"
DEFAULT_HELDOUT_PROMPTS = 30
MIN_EFFECT_DENOMINATOR = 1e-8
ALLOWED_METHODS = {"resample", "mean"}


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_config() -> Dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _parse_csv_list(raw: str) -> list[str]:
    values = [x.strip() for x in raw.split(",") if x.strip()]
    if not values:
        raise ValueError("CSV list cannot be empty.")
    return values


def _parse_methods(raw: str) -> list[str]:
    methods = [x.lower() for x in _parse_csv_list(raw)]
    invalid = sorted(set(methods) - ALLOWED_METHODS)
    if invalid:
        raise ValueError(f"Unsupported methods: {invalid}. Allowed: {sorted(ALLOWED_METHODS)}")
    return methods


def _parse_dose_response(raw: str) -> list[float]:
    values = [float(x) for x in _parse_csv_list(raw)]
    out: list[float] = []
    seen: set[float] = set()
    for value in values:
        if value <= 0.0 or value > 1.0:
            raise ValueError("Dose-response fractions must be in (0, 1].")
        if value not in seen:
            out.append(float(value))
            seen.add(float(value))
    return out


def _preserved_effect_fraction(
    steered_effect_abs: float,
    circuit_only_effect_abs: float,
    *,
    min_steered_effect: float = MIN_EFFECT_DENOMINATOR,
) -> float | None:
    steered = float(steered_effect_abs)
    denom_min = max(float(min_steered_effect), float(MIN_EFFECT_DENOMINATOR))
    if steered < denom_min:
        return None
    return float(float(circuit_only_effect_abs) / steered)


def _sufficiency_tier(
    preserved_fraction: float | None,
    *,
    threshold: float,
    partial_floor: float = 0.40,
) -> Dict[str, Any]:
    if preserved_fraction is None:
        return {"tier": "unevaluable", "pass": False}
    value = float(preserved_fraction)
    if value >= float(threshold):
        return {"tier": "strong", "pass": True}
    if value >= float(partial_floor):
        return {"tier": "partial", "pass": False}
    return {"tier": "fail", "pass": False}


def _extract_selected_combo_map(
    ingestion_payload: Dict[str, Any], traits: Sequence[str]
) -> Dict[str, Dict[str, float]]:
    traits_payload = ingestion_payload.get("traits", {})
    if not isinstance(traits_payload, dict):
        raise ValueError("Ingestion payload missing traits map.")

    selected_map: Dict[str, Dict[str, float]] = {}
    for trait in traits:
        trait_payload = traits_payload.get(trait)
        if not isinstance(trait_payload, dict):
            raise ValueError(f"Ingestion payload missing trait entry: {trait}")
        selected = trait_payload.get("selected", {})
        if not isinstance(selected, dict):
            raise ValueError(f"Ingestion trait entry missing selected combo: {trait}")
        layer = selected.get("layer")
        alpha = selected.get("alpha")
        if layer is None or alpha is None:
            raise ValueError(f"Selected combo missing layer/alpha for trait={trait}")
        selected_map[trait] = {
            "layer": float(layer),
            "alpha": float(alpha),
            "test_bidirectional_effect": float(selected.get("test_bidirectional_effect", 0.0)),
        }
    return selected_map


def _validate_target_sets(target_payload: Dict[str, Any], traits: Sequence[str]) -> Dict[str, Any]:
    targets = target_payload.get("targets_by_trait", {})
    if not isinstance(targets, dict):
        raise ValueError("Target freeze payload missing targets_by_trait.")

    trait_rows: Dict[str, Any] = {}
    top_k_values: set[int] = set()
    for trait in traits:
        trait_payload = targets.get(trait)
        if not isinstance(trait_payload, dict):
            raise ValueError(f"Target freeze payload missing trait={trait}")
        feature_ids = [int(x) for x in trait_payload.get("target_feature_ids", [])]
        if not feature_ids:
            raise ValueError(f"Target freeze payload has empty target_feature_ids for trait={trait}")
        top_k_values.add(len(feature_ids))
        trait_rows[trait] = {
            "target_feature_count": int(len(feature_ids)),
            "candidate_pool_size": int(trait_payload.get("candidate_pool_size", 0)),
            "prompt_count_used": int(trait_payload.get("prompt_count_used", 0)),
        }
    return {
        "traits": trait_rows,
        "top_k_values": sorted(int(x) for x in top_k_values),
        "top_k_consistent": bool(len(top_k_values) == 1),
    }


def _heldout_count(trait: str) -> int:
    path = HELDOUT_DIR / f"{trait}_heldout_pairs.jsonl"
    rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return int(len(rows))


def _build_condition_matrix(
    *,
    traits: Sequence[str],
    methods: Sequence[str],
    dose_response: Sequence[float],
) -> Dict[str, Any]:
    rows: list[Dict[str, Any]] = []
    for trait in traits:
        rows.append({"trait": trait, "condition": "baseline_unsteered"})
        rows.append({"trait": trait, "condition": "steered_no_ablation"})
        for method in methods:
            for fraction in dose_response:
                rows.append(
                    {
                        "trait": trait,
                        "condition": "circuit_only_preservation",
                        "method": method,
                        "preserved_fraction_target": float(fraction),
                    }
                )
    return {
        "n_rows_total": int(len(rows)),
        "rows": rows,
        "rows_per_trait": int(2 + len(methods) * len(dose_response)),
    }


def _simulate_sufficiency_dryrun(
    *,
    traits: Sequence[str],
    methods: Sequence[str],
    dose_response: Sequence[float],
    selected_map: Dict[str, Dict[str, float]],
    threshold: float,
    seed: int,
) -> Dict[str, Any]:
    rng = np.random.default_rng(int(seed))
    method_multiplier = {"resample": 0.90, "mean": 0.75}
    rows: list[Dict[str, Any]] = []
    summary: Dict[str, Dict[str, Any]] = {}

    for trait in traits:
        summary[trait] = {}
        steered_effect_abs = max(float(selected_map[trait]["test_bidirectional_effect"]), 1.0)
        for method in methods:
            per_fraction: list[Dict[str, Any]] = []
            for fraction in dose_response:
                noise = float(rng.normal(loc=0.0, scale=0.01))
                preserved_target = float(
                    np.clip(float(fraction) * method_multiplier[method] + noise, 0.0, 1.0)
                )
                circuit_only_effect_abs = float(steered_effect_abs * preserved_target)
                preserved = _preserved_effect_fraction(
                    steered_effect_abs,
                    circuit_only_effect_abs,
                )
                tier = _sufficiency_tier(preserved, threshold=float(threshold))
                row = {
                    "trait": trait,
                    "method": method,
                    "dose_fraction": float(fraction),
                    "steered_effect_abs": float(steered_effect_abs),
                    "circuit_only_effect_abs_simulated": float(circuit_only_effect_abs),
                    "preserved_effect_fraction": preserved,
                    "sufficiency_tier": tier["tier"],
                    "sufficiency_pass": bool(tier["pass"]),
                }
                rows.append(row)
                per_fraction.append(row)

            full_rows = [r for r in per_fraction if abs(float(r["dose_fraction"]) - 1.0) < 1e-9]
            full_preserved = [
                float(r["preserved_effect_fraction"])
                for r in full_rows
                if r["preserved_effect_fraction"] is not None
            ]
            summary[trait][method] = {
                "n_rows": int(len(per_fraction)),
                "full_fraction_preserved_mean": (
                    float(np.mean(np.asarray(full_preserved, dtype=np.float64)))
                    if full_preserved
                    else None
                ),
                "full_fraction_sufficiency_pass_any": bool(
                    any(bool(r["sufficiency_pass"]) for r in full_rows)
                ),
            }

    return {
        "rows": rows,
        "summary_by_trait_method": summary,
    }


def build_preflight_report(
    *,
    config: Dict[str, Any],
    target_payload: Dict[str, Any],
    ingestion_payload: Dict[str, Any],
    traits: Sequence[str],
    methods: Sequence[str],
    dose_response: Sequence[float],
    heldout_counts: Dict[str, int],
    heldout_prompts_per_trait: int,
    seed: int,
) -> Dict[str, Any]:
    threshold_cfg = config.get("thresholds", {})
    sufficiency_threshold = float(threshold_cfg.get("sufficiency", 0.60))
    random_baseline_samples = int(threshold_cfg.get("random_baseline_samples", 100))

    target_validation = _validate_target_sets(target_payload, traits)
    selected_map = _extract_selected_combo_map(ingestion_payload, traits)
    condition_matrix = _build_condition_matrix(
        traits=traits, methods=methods, dose_response=dose_response
    )
    simulation = _simulate_sufficiency_dryrun(
        traits=traits,
        methods=methods,
        dose_response=dose_response,
        selected_map=selected_map,
        threshold=sufficiency_threshold,
        seed=seed,
    )

    heldout_ready = all(
        int(heldout_counts.get(trait, 0)) >= int(heldout_prompts_per_trait) for trait in traits
    )
    blockers = []
    if not target_validation.get("top_k_consistent", False):
        blockers.append("target_feature_topk_inconsistent")
    if not heldout_ready:
        blockers.append("insufficient_heldout_pairs_for_requested_prompts")
    blockers.append("remote_circuit_only_execution_not_run_dryrun_only")

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_stage4_sufficiency_preflight",
        "inputs": {
            "traits": list(traits),
            "methods": list(methods),
            "dose_response": [float(x) for x in dose_response],
            "heldout_prompts_per_trait": int(heldout_prompts_per_trait),
            "seed": int(seed),
        },
        "thresholds": {
            "sufficiency": float(sufficiency_threshold),
            "partial_floor": 0.40,
            "random_baseline_samples": int(random_baseline_samples),
        },
        "target_set_validation": target_validation,
        "selected_combo_map": selected_map,
        "heldout_availability": {
            "counts_by_trait": {trait: int(heldout_counts.get(trait, 0)) for trait in traits},
            "heldout_ready_for_requested_prompts": bool(heldout_ready),
        },
        "condition_matrix": condition_matrix,
        "dryrun_validation": {
            "preserved_fraction_formula_smoke": {
                "example_preserved_10_to_7": _preserved_effect_fraction(10.0, 7.0),
                "example_unevaluable_zero_denominator": _preserved_effect_fraction(
                    0.0, 0.0
                ),
            },
            "synthetic_sufficiency_rows": simulation["rows"],
            "synthetic_summary_by_trait_method": simulation["summary_by_trait_method"],
        },
        "readiness": {
            "inputs_valid": bool(target_validation.get("top_k_consistent", False) and heldout_ready),
            "dryrun_path_exercised": True,
            "launch_recommended_now": False,
            "blocking_items": blockers,
        },
        "evidence_status": {
            "input_artifacts": "known",
            "dryrun_simulation": "inferred",
            "launch_readiness": "inferred",
        },
    }


def _default_output_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OUT_DIR / f"week3_stage4_sufficiency_preflight_{timestamp}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-freeze-artifact", default=DEFAULT_TARGET_FREEZE_ARTIFACT)
    parser.add_argument("--ingestion-artifact", default=DEFAULT_INGESTION_ARTIFACT)
    parser.add_argument("--traits", default=DEFAULT_TRAITS)
    parser.add_argument("--methods", default=DEFAULT_METHODS)
    parser.add_argument("--dose-response", default=DEFAULT_DOSE_RESPONSE)
    parser.add_argument("--heldout-prompts-per-trait", type=int, default=DEFAULT_HELDOUT_PROMPTS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    traits = _parse_csv_list(args.traits)
    methods = _parse_methods(args.methods)
    dose_response = _parse_dose_response(args.dose_response)

    config = _load_config()
    target_payload = _load_json(_resolve_path(args.target_freeze_artifact))
    ingestion_payload = _load_json(_resolve_path(args.ingestion_artifact))
    heldout_counts = {trait: _heldout_count(trait) for trait in traits}

    report = build_preflight_report(
        config=config,
        target_payload=target_payload,
        ingestion_payload=ingestion_payload,
        traits=traits,
        methods=methods,
        dose_response=dose_response,
        heldout_counts=heldout_counts,
        heldout_prompts_per_trait=int(args.heldout_prompts_per_trait),
        seed=int(args.seed),
    )

    out_path = Path(args.output) if args.output else _default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
