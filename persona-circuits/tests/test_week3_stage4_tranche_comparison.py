"""Tests for Stage4 tranche-vs-reference comparison helpers."""

from __future__ import annotations

import unittest

from scripts.week3_stage4_tranche_comparison import build_report


def _method_payload(mean_reduction: float, p_val: float, a12: float, n_valid: int, n_total: int) -> dict:
    return {
        "observed_mean_reduction": mean_reduction,
        "selectivity_vs_random": {"p_value_one_sided_ge": p_val},
        "effect_sizes_vs_random_prompt_distribution": {"a12": a12},
        "necessity_threshold_pass": mean_reduction >= 0.8,
        "selectivity_p_threshold_pass": p_val <= 0.01,
        "a12_threshold_pass": a12 >= 0.71,
        "reduction_validity": {
            "n_valid_prompts": n_valid,
            "n_total_prompts": n_total,
            "valid_fraction": n_valid / n_total,
        },
    }


class Stage4TrancheComparisonTests(unittest.TestCase):
    def test_build_report_computes_deltas(self) -> None:
        reference = {
            "inputs": {"n_prompts": 30, "heldout_start_index": 0, "random_baseline_samples": 20, "n_bootstrap": 200},
            "thresholds": {"necessity": 0.8, "significance": 0.01, "a12_minimum": 0.71},
            "results_by_trait": {
                "evil": {
                    "behavioral_score_baseline": {"steered_effect_abs_summary": {"mean": 12.0}},
                    "methods": {
                        "resample": _method_payload(0.26, 0.04, 0.56, 21, 30),
                        "mean": _method_payload(0.18, 0.04, 0.54, 21, 30),
                        "zero": _method_payload(0.56, 0.04, 0.70, 21, 30),
                    },
                }
            },
        }
        tranche = {
            "inputs": {"n_prompts": 30, "heldout_start_index": 20, "random_baseline_samples": 20, "n_bootstrap": 200},
            "thresholds": {"necessity": 0.8, "significance": 0.01, "a12_minimum": 0.71},
            "results_by_trait": {
                "evil": {
                    "behavioral_score_baseline": {"steered_effect_abs_summary": {"mean": 14.0}},
                    "methods": {
                        "resample": _method_payload(0.25, 0.62, 0.42, 20, 30),
                        "mean": _method_payload(0.28, 0.24, 0.41, 20, 30),
                        "zero": _method_payload(0.53, 0.04, 0.55, 20, 30),
                    },
                }
            },
        }
        out = build_report(
            reference_report=reference,
            tranche_report=tranche,
            trait="evil",
            reference_artifact_path="/tmp/reference.json",
            tranche_artifact_path="/tmp/tranche.json",
        )
        self.assertEqual(out["coverage_stability"]["label"], "stable")
        self.assertAlmostEqual(out["coverage_stability"]["delta"], -1 / 30)
        self.assertAlmostEqual(
            out["per_method"]["resample"]["deltas"]["p_value_delta"],
            0.58,
            places=6,
        )
        self.assertAlmostEqual(
            out["baseline_effect_abs_mean"]["delta"],
            2.0,
        )

    def test_missing_trait_raises(self) -> None:
        reference = {"results_by_trait": {"evil": {"methods": {}}}}
        tranche = {"results_by_trait": {}}
        with self.assertRaises(KeyError):
            build_report(
                reference_report=reference,
                tranche_report=tranche,
                trait="evil",
                reference_artifact_path="/tmp/r.json",
                tranche_artifact_path="/tmp/t.json",
            )


if __name__ == "__main__":
    unittest.main()

