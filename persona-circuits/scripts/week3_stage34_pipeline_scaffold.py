"""Week 3/4 dry-run scaffold for attribution + ablation pipeline and artifact schema."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from circuit_metrics import concentration_summary, effect_size_summary, random_baseline_selectivity

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
OUT_DIR = ROOT / "results" / "stage3_attribution"


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _parse_traits(raw: str, default_traits: list[str]) -> list[str]:
    if not raw.strip():
        return list(default_traits)
    out = [x.strip() for x in raw.split(",") if x.strip()]
    if not out:
        raise ValueError("Trait list cannot be empty.")
    return out


def _empty_stage4_schema(*, random_baseline_samples: int) -> dict[str, Any]:
    return {
        "necessity": {
            "effect_reduction": {
                "resample": None,
                "mean": None,
                "zero": None,
            },
            "selectivity_vs_random": {
                "random_baseline_samples": int(random_baseline_samples),
                "resample": None,
                "mean": None,
                "zero": None,
            },
            "specificity_unrelated_task_drop": None,
        },
        "sufficiency": {
            "effect_preserved": {
                "resample": None,
                "mean": None,
                "zero": None,
            },
            "coherence_guard": None,
        },
        "effect_sizes": {
            "resample_vs_random": {
                "cohens_d": None,
                "cohens_d_ci95": None,
                "a12": None,
                "a12_ci95": None,
            },
            "mean_vs_random": {
                "cohens_d": None,
                "cohens_d_ci95": None,
                "a12": None,
                "a12_ci95": None,
            },
            "zero_vs_random": {
                "cohens_d": None,
                "cohens_d_ci95": None,
                "a12": None,
                "a12_ci95": None,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traits", type=str, default="")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    cfg = _load_config()
    traits = _parse_traits(args.traits, list(cfg.get("traits", [])))
    circuit_layers = [int(x) for x in cfg["models"]["primary"]["circuit_analysis_layers"]]
    random_baseline_samples = int(cfg["thresholds"]["random_baseline_samples"])

    # Dry-run synthetic arrays to validate metric plumbing and output schema.
    rng = np.random.default_rng(int(args.seed))
    synthetic_contrib = np.abs(rng.normal(loc=0.0, scale=1.0, size=128))
    synthetic_random = rng.uniform(low=0.1, high=0.7, size=random_baseline_samples)
    synthetic_observed = float(np.percentile(synthetic_random, 99.5))
    synthetic_effect_a = rng.normal(loc=0.62, scale=0.08, size=80)
    synthetic_effect_b = rng.normal(loc=0.31, scale=0.08, size=80)

    scaffold = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": {
            "scaffold_schema": "known",
            "synthetic_metric_demo": "inferred",
            "real_stage3_stage4_results": "unknown",
        },
        "inputs": {
            "config_path": str(CONFIG_PATH),
            "traits": traits,
            "circuit_analysis_layers": circuit_layers,
            "random_baseline_samples": random_baseline_samples,
            "seed": int(args.seed),
        },
        "pipeline_plan": {
            "stage3_attribution": {
                "steps": [
                    "collect feature candidates from SAE decomposition outputs",
                    "compute attribution graph edges over candidate features",
                    "select candidate circuit subsets per trait",
                ],
                "expected_artifacts": [
                    "results/stage3_attribution/<trait>_attribution_graph_*.json",
                    "results/stage3_attribution/<trait>_candidate_circuit_*.json",
                ],
            },
            "stage4_ablation": {
                "required_modalities": ["resample", "mean", "zero"],
                "random_same_size_baselines": int(random_baseline_samples),
                "steps": [
                    "evaluate necessity reductions for each modality",
                    "evaluate sufficiency preservation for each modality",
                    "compare observed reductions against random baseline distribution",
                    "compute concentration + effect-size metrics with bootstrap CIs",
                ],
                "expected_artifacts": [
                    "results/stage4_ablation/<trait>_necessity_sufficiency_*.json",
                    "results/stage4_ablation/<trait>_random_baseline_distribution_*.json",
                ],
            },
        },
        "trait_templates": {
            trait: {
                "candidate_layers": circuit_layers,
                "stage3_outputs": {
                    "attribution_graph": {"nodes": [], "edges": []},
                    "candidate_circuit_features": [],
                    "concentration_metrics": {
                        "gini": None,
                        "entropy_normalized": None,
                        "top_1pct_mass": None,
                        "top_5pct_mass": None,
                        "top_10pct_mass": None,
                    },
                },
                "stage4_outputs": _empty_stage4_schema(
                    random_baseline_samples=random_baseline_samples
                ),
            }
            for trait in traits
        },
        "synthetic_metric_demo": {
            "concentration_summary": concentration_summary(synthetic_contrib),
            "effect_size_summary": effect_size_summary(
                synthetic_effect_a,
                synthetic_effect_b,
                seed=int(args.seed),
                n_bootstrap=1000,
            ),
            "random_baseline_selectivity": random_baseline_selectivity(
                synthetic_observed,
                synthetic_random,
            ),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"week3_stage34_pipeline_scaffold_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(scaffold, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "traits": traits}, indent=2))


if __name__ == "__main__":
    main()
