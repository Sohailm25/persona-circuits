"""Unit tests for the Week 3 GLP sufficiency sidecar helpers."""

from __future__ import annotations

import unittest

from scripts.week3_glp_sufficiency_sidecar import (
    _build_random_control_summary,
    _extract_target_sets,
    _parse_methods,
    _resolve_dose_response,
    _summarize_records,
)


class Week3GLPSufficiencySidecarTests(unittest.TestCase):
    def test_parse_methods(self) -> None:
        self.assertEqual(_parse_methods("resample, mean"), ["resample", "mean"])
        with self.assertRaises(ValueError):
            _parse_methods("invalid")

    def test_resolve_dose_response(self) -> None:
        self.assertEqual(_resolve_dose_response("0.25,0.5,1.0", None), [0.25, 0.5, 1.0])
        self.assertEqual(_resolve_dose_response("", [0.25, 0.5, 0.5, 1.0]), [0.25, 0.5, 1.0])
        self.assertEqual(_resolve_dose_response("", "0.5,1.0"), [0.5, 1.0])

    def test_extract_target_sets(self) -> None:
        target_sets, candidate_pool = _extract_target_sets(
            {
                "targets_by_trait": {
                    "sycophancy": {
                        "target_feature_ids": [1, 2, 3],
                        "candidate_pool_feature_ids": [1, 2, 3, 4, 5],
                    },
                    "evil": {
                        "target_feature_ids": [7, 8],
                        "candidate_pool_feature_ids": [6, 7, 8, 9],
                    },
                }
            },
            ["sycophancy", "evil"],
        )
        self.assertEqual(target_sets["sycophancy"], [1, 2, 3])
        self.assertEqual(candidate_pool["evil"], [6, 7, 8, 9])

    def test_summarize_records(self) -> None:
        summary = _summarize_records(
            records=[
                {
                    "trait_score": 70.0,
                    "coherence_score": 80.0,
                    "effect_abs_vs_unsteered": 20.0,
                    "preservation_vs_raw_full": 0.8,
                    "preservation_vs_glp_full": 0.7,
                    "geometry_events": [{"repair_to_edit_ratio": 0.2}],
                    "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.3}],
                    "bleed_scores": {"evil": 10.0},
                    "capability_correct_fraction": 1.0,
                },
                {
                    "trait_score": 74.0,
                    "coherence_score": 78.0,
                    "effect_abs_vs_unsteered": 18.0,
                    "preservation_vs_raw_full": 0.6,
                    "preservation_vs_glp_full": 0.5,
                    "geometry_events": [{"repair_to_edit_ratio": 0.4}],
                    "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.5}],
                    "bleed_scores": {"evil": 14.0},
                    "capability_correct_fraction": 0.5,
                },
            ],
            comparison_baseline=None,
        )
        self.assertEqual(summary["n_rows"], 2)
        self.assertAlmostEqual(summary["trait_score_mean"], 72.0)
        self.assertAlmostEqual(summary["coherence_mean"], 79.0)
        self.assertAlmostEqual(summary["preservation_vs_raw_full_mean"], 0.7)
        self.assertAlmostEqual(summary["bleed_by_trait_mean"]["evil"], 12.0)
        self.assertAlmostEqual(summary["capability_correct_fraction_mean"], 0.75)
        self.assertEqual(summary["geometry_summary"]["repair_to_edit_ratio"]["n"], 2)
        self.assertEqual(summary["next_token_loss_summary"]["delta_target_nll_vs_clean"]["n"], 2)
        self.assertAlmostEqual(summary["next_token_loss_summary"]["delta_target_nll_vs_clean"]["mean"], 0.4)

    def test_build_random_control_summary(self) -> None:
        observed_records = [
            {"preservation_vs_raw_full": 0.8},
            {"preservation_vs_raw_full": 0.9},
            {"preservation_vs_raw_full": 0.7},
        ]
        random_records = [
            {
                "trait_score": 55.0,
                "coherence_score": 75.0,
                "effect_abs_vs_unsteered": 10.0,
                "preservation_vs_raw_full": 0.4,
                "preservation_vs_glp_full": 0.3,
                "geometry_events": [],
                "bleed_scores": {},
            },
            {
                "trait_score": 57.0,
                "coherence_score": 76.0,
                "effect_abs_vs_unsteered": 12.0,
                "preservation_vs_raw_full": 0.5,
                "preservation_vs_glp_full": 0.35,
                "geometry_events": [],
                "bleed_scores": {},
            },
        ]
        summary = _build_random_control_summary(
            observed_records=observed_records,
            random_records=random_records,
            preservation_key="preservation_vs_raw_full",
            random_set_means=[0.45, 0.5, 0.55],
            seed=42,
            n_bootstrap=100,
            comparison_baseline=None,
        )
        self.assertEqual(summary["n_rows"], 2)
        self.assertEqual(summary["random_same_size_set_distribution"]["n_sets"], 3)
        self.assertIn("selectivity_vs_observed", summary)
        self.assertIn("effect_sizes_vs_observed_prompt_distribution", summary)


if __name__ == "__main__":
    unittest.main()
