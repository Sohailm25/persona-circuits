"""Week 2: reanalyze extraction-free activation artifact with overlap-gradient metrics."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"


def _latest_artifact_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"no artifacts matched: {pattern}")
    return matches[-1]


def _binomial_two_sided_p_value(n_trials: int, n_success: int, p_success: float = 0.5) -> float | None:
    if n_trials <= 0:
        return None
    lower_tail = 0.0
    upper_tail = 0.0
    for i in range(0, n_success + 1):
        lower_tail += math.comb(n_trials, i) * (p_success ** i) * ((1.0 - p_success) ** (n_trials - i))
    for i in range(n_success, n_trials + 1):
        upper_tail += math.comb(n_trials, i) * (p_success ** i) * ((1.0 - p_success) ** (n_trials - i))
    return float(min(1.0, 2.0 * min(lower_tail, upper_tail)))


def _ttest_vs_zero_normal_approx(values: np.ndarray) -> dict[str, Any]:
    if values.size == 0:
        return {
            "n": 0,
            "mean": None,
            "sample_std": None,
            "t_stat": None,
            "p_value_two_sided_normal_approx": None,
        }
    mean = float(np.mean(values))
    if values.size < 2:
        return {
            "n": int(values.size),
            "mean": mean,
            "sample_std": None,
            "t_stat": None,
            "p_value_two_sided_normal_approx": None,
        }
    sample_std = float(np.std(values, ddof=1))
    if sample_std <= 1e-12:
        return {
            "n": int(values.size),
            "mean": mean,
            "sample_std": sample_std,
            "t_stat": None,
            "p_value_two_sided_normal_approx": None,
        }
    se = sample_std / math.sqrt(float(values.size))
    t_stat = mean / se if se > 0 else 0.0
    p_value = float(math.erfc(abs(t_stat) / math.sqrt(2.0)))
    return {
        "n": int(values.size),
        "mean": mean,
        "sample_std": sample_std,
        "t_stat": float(t_stat),
        "p_value_two_sided_normal_approx": p_value,
    }


def _bootstrap_mean_ci(values: np.ndarray, *, seed: int, n_bootstrap: int = 4000) -> dict[str, Any]:
    if values.size == 0:
        return {"n": 0, "n_bootstrap": int(n_bootstrap), "mean_ci95": None}
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(n_bootstrap, values.size), replace=True)
    means = np.mean(draws, axis=1)
    return {
        "n": int(values.size),
        "n_bootstrap": int(n_bootstrap),
        "mean_ci95": {
            "lower": float(np.percentile(means, 2.5)),
            "upper": float(np.percentile(means, 97.5)),
        },
    }


def _classify_overlap(mean_cosine: float, positive_fraction: float, sign_test_p: float | None) -> str:
    if sign_test_p is None:
        return "unknown"
    if mean_cosine >= 0.2 and positive_fraction >= 0.9 and sign_test_p < 0.01:
        return "moderate_overlap"
    if mean_cosine >= 0.1 and positive_fraction >= 0.8 and sign_test_p < 0.05:
        return "weak_overlap"
    if abs(mean_cosine) < 0.05 and 0.4 <= positive_fraction <= 0.6:
        return "null_overlap"
    return "mixed_or_fragile"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-path", type=str, default="")
    parser.add_argument("--cosine-threshold", type=float, default=0.1)
    parser.add_argument("--min-positive-fraction", type=float, default=0.75)
    parser.add_argument("--directional-threshold", type=float, default=0.15)
    parser.add_argument("--min-set-count", type=int, default=2)
    parser.add_argument("--max-set-mean-cv", type=float, default=0.8)
    parser.add_argument("--max-cosine-std", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    source_path = (
        Path(args.artifact_path)
        if args.artifact_path
        else _latest_artifact_path("week2_extraction_free_activation_eval_*.json")
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    trait_summaries: dict[str, Any] = {}

    for trait, payload in source.get("traits", {}).items():
        cosines = np.asarray([float(row.get("cosine", 0.0)) for row in payload.get("rows", [])], dtype=np.float64)
        n_positive = int(np.sum(cosines > 0.0))
        sign_test_p = _binomial_two_sided_p_value(int(cosines.size), n_positive, p_success=0.5)
        ttest_summary = _ttest_vs_zero_normal_approx(cosines)
        boot_summary = _bootstrap_mean_ci(cosines, seed=int(args.seed) + len(trait) * 1009, n_bootstrap=4000)
        ci95 = boot_summary.get("mean_ci95")
        mean_ci_excludes_zero = bool(ci95 is not None and ci95["lower"] > 0.0)

        set_stats = payload.get("set_variance", {}).get("per_set_stats", [])
        set_means = np.asarray([float(row.get("mean_cosine", 0.0)) for row in set_stats], dtype=np.float64)
        set_mean_std = float(np.std(set_means)) if set_means.size else 0.0
        mean_cosine = float(payload.get("cosine_stats", {}).get("mean") or 0.0)
        set_mean_cv = set_mean_std / abs(mean_cosine) if abs(mean_cosine) > 0 else 0.0
        positive_fraction = float(payload.get("positive_cosine_fraction") or 0.0)
        projection_mean = float(payload.get("projection_delta_stats", {}).get("mean") or 0.0)
        global_std = float(payload.get("global_cosine_std") or 0.0)

        gate_map = {
            "mean_cosine": mean_cosine >= float(args.cosine_threshold),
            "positive_fraction": positive_fraction >= float(args.min_positive_fraction),
            "projection_delta": projection_mean >= float(args.directional_threshold),
            "set_count": len(set_stats) >= int(args.min_set_count),
            "set_mean_cv": set_mean_cv <= float(args.max_set_mean_cv),
            "std_control": global_std <= float(args.max_cosine_std),
            "non_empty_rows": int(cosines.size) > 0,
            "non_empty_set_stats": len(set_stats) > 0,
        }
        required_gates = list(gate_map.keys())
        trait_summaries[trait] = {
            "evidence_status": {
                "source_metrics": "observed",
                "reanalysis_gates": "inferred",
                "significance_stats": "inferred",
            },
            "source_metrics": {
                "mean_cosine": mean_cosine,
                "median_cosine": payload.get("cosine_stats", {}).get("median"),
                "positive_fraction": positive_fraction,
                "projection_delta_mean": projection_mean,
                "set_mean_cv": set_mean_cv,
                "set_mean_std": set_mean_std,
                "set_count": len(set_stats),
            },
            "significance": {
                "n_positive_cosines": n_positive,
                "sign_test_two_sided_p": sign_test_p,
                "ttest_vs_zero": ttest_summary,
                "mean_bootstrap_ci95": ci95,
                "mean_ci_excludes_zero": mean_ci_excludes_zero,
            },
            "reanalysis_gates": gate_map,
            "required_gates": required_gates,
            "passes": all(gate_map.values()),
            "overlap_classification": _classify_overlap(mean_cosine, positive_fraction, sign_test_p),
        }

    output = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": {
            "source_artifact": "known",
            "trait_reanalysis": "inferred",
            "overall_pass": "inferred",
        },
        "source_artifact": str(source_path),
        "source_overall_pass": source.get("overall_pass"),
        "gate_policy": {
            "version": "v2_overlap_gradient_reanalysis",
            "thresholds": {
                "mean_cosine_min": float(args.cosine_threshold),
                "positive_fraction_min": float(args.min_positive_fraction),
                "projection_delta_min": float(args.directional_threshold),
                "set_count_min": int(args.min_set_count),
                "set_mean_cv_max": float(args.max_set_mean_cv),
                "max_cosine_std": float(args.max_cosine_std),
            },
        },
        "traits": trait_summaries,
        "overall_pass": all(trait_data.get("passes", False) for trait_data in trait_summaries.values()),
    }

    out_path = RESULTS_DIR / f"week2_extraction_free_reanalysis_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "overall_pass": output["overall_pass"]}, indent=2))


if __name__ == "__main__":
    main()
