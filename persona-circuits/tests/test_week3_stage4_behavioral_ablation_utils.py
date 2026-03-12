"""Unit tests for Stage4 behavioral ablation helper utilities."""

from __future__ import annotations

import unittest

import numpy as np

from scripts.week3_stage4_behavioral_ablation import (
    _build_method_report,
    _parse_artifact_map,
    _parse_methods,
    _parse_traits,
    _reduction_fraction,
    _sample_random_feature_sets,
    _select_rows_window,
    _trait_label,
)


class ParseHelpersTests(unittest.TestCase):
    def test_parse_traits(self) -> None:
        self.assertEqual(_parse_traits("sycophancy, evil"), ["sycophancy", "evil"])
        with self.assertRaises(ValueError):
            _parse_traits(" , ")

    def test_parse_methods(self) -> None:
        self.assertEqual(_parse_methods("resample,mean,zero"), ["resample", "mean", "zero"])
        with self.assertRaises(ValueError):
            _parse_methods("resample,unknown")

    def test_parse_artifact_map_csv_and_json(self) -> None:
        csv_map = _parse_artifact_map("sycophancy:results/a.json,evil:results/b.json")
        self.assertEqual(csv_map["sycophancy"], "results/a.json")
        self.assertEqual(csv_map["evil"], "results/b.json")

        json_map = _parse_artifact_map('{"sycophancy":"x.json","evil":"y.json"}')
        self.assertEqual(json_map["sycophancy"], "x.json")
        self.assertEqual(json_map["evil"], "y.json")

    def test_trait_label(self) -> None:
        self.assertEqual(_trait_label("evil"), "machiavellian_disposition")
        self.assertEqual(_trait_label("sycophancy"), "sycophancy")


class SamplingTests(unittest.TestCase):
    def test_sample_random_feature_sets(self) -> None:
        draws = _sample_random_feature_sets(
            d_sae=20,
            exclude_ids=[1, 2, 3],
            set_size=4,
            n_sets=5,
            seed=42,
        )
        self.assertEqual(draws.shape, (5, 4))
        self.assertTrue(np.all(~np.isin(draws, np.asarray([1, 2, 3]))))

    def test_select_rows_window_no_wrap(self) -> None:
        rows = [{"i": i} for i in range(10)]
        out = _select_rows_window(rows, max_pairs=4, start_index=3)
        self.assertEqual([x["i"] for x in out], [3, 4, 5, 6])

    def test_select_rows_window_with_wrap(self) -> None:
        rows = [{"i": i} for i in range(6)]
        out = _select_rows_window(rows, max_pairs=4, start_index=4)
        self.assertEqual([x["i"] for x in out], [4, 5, 0, 1])

    def test_select_rows_window_validates_args(self) -> None:
        rows = [{"i": 0}]
        with self.assertRaises(ValueError):
            _select_rows_window(rows, max_pairs=0, start_index=0)
        with self.assertRaises(ValueError):
            _select_rows_window(rows, max_pairs=1, start_index=-1)


class MethodReportTests(unittest.TestCase):
    def test_build_method_report_contains_required_keys(self) -> None:
        observed_full = [0.8, None, 0.9, 0.7]
        valid_mask = np.asarray([True, False, True, True], dtype=bool)
        baseline_effect_abs = np.asarray([2.0, 0.1, 3.0, 4.0], dtype=np.float64)
        report = _build_method_report(
            observed_prompt_reductions_full=observed_full,
            valid_prompt_mask=valid_mask,
            baseline_effect_abs=baseline_effect_abs,
            random_set_means=np.asarray([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
            random_prompt_reductions=np.asarray([0.1, 0.2, 0.3, 0.2, 0.1], dtype=np.float64),
            observed_ablated_scores=np.asarray([60.0, 58.0, 61.0], dtype=np.float64),
            baseline_steered_scores=np.asarray([80.0, 79.0, 81.0], dtype=np.float64),
            n_random_sets_total=6,
            min_baseline_effect_for_reduction=1.0,
            thresholds={"necessity": 0.8, "significance": 0.01, "a12_minimum": 0.71},
            seed=42,
            n_bootstrap=100,
        )
        self.assertIn("observed_mean_reduction", report)
        self.assertIn("selectivity_vs_random", report)
        self.assertIn("effect_sizes_vs_random_prompt_distribution", report)
        self.assertIn("necessity_threshold_pass", report)
        self.assertIn("selectivity_p_threshold_pass", report)
        self.assertIn("a12_threshold_pass", report)
        self.assertIn("reduction_validity", report)
        self.assertEqual(report["reduction_validity"]["n_total_prompts"], 4)
        self.assertEqual(report["reduction_validity"]["n_valid_prompts"], 3)
        self.assertEqual(report["random_baseline_reduction_distribution"]["n_sets_total"], 6)
        self.assertEqual(report["random_baseline_reduction_distribution"]["n_sets_used"], 4)
        self.assertEqual(report["random_baseline_reduction_distribution"]["n_sets_skipped_no_valid_prompts"], 2)
        self.assertTrue(report["necessity_threshold_pass"])
        self.assertFalse(report["selectivity_p_threshold_pass"])

    def test_build_method_report_handles_no_valid_prompt_reductions(self) -> None:
        report = _build_method_report(
            observed_prompt_reductions_full=[None, None],
            valid_prompt_mask=np.asarray([False, False], dtype=bool),
            baseline_effect_abs=np.asarray([0.0, 0.2], dtype=np.float64),
            random_set_means=np.asarray([], dtype=np.float64),
            random_prompt_reductions=np.asarray([], dtype=np.float64),
            observed_ablated_scores=np.asarray([55.0, 57.0], dtype=np.float64),
            baseline_steered_scores=np.asarray([55.0, 57.0], dtype=np.float64),
            n_random_sets_total=3,
            min_baseline_effect_for_reduction=1.0,
            thresholds={"necessity": 0.8, "significance": 0.01, "a12_minimum": 0.71},
            seed=42,
            n_bootstrap=50,
        )
        self.assertIsNone(report["observed_mean_reduction"])
        self.assertFalse(report["thresholds_evaluable"])
        self.assertEqual(report["reduction_validity"]["n_valid_prompts"], 0)
        self.assertEqual(report["random_baseline_reduction_distribution"]["n_sets_used"], 0)
        self.assertEqual(report["random_baseline_reduction_distribution"]["n_sets_skipped_no_valid_prompts"], 3)

    def test_reduction_fraction_invalid_when_baseline_below_threshold(self) -> None:
        self.assertIsNone(
            _reduction_fraction(
                baseline_abs=0.2,
                ablated_abs=0.1,
                min_baseline_effect_for_reduction=1.0,
            )
        )
        self.assertIsNone(
            _reduction_fraction(
                baseline_abs=0.0,
                ablated_abs=0.0,
                min_baseline_effect_for_reduction=0.0,
            )
        )
        self.assertAlmostEqual(
            _reduction_fraction(
                baseline_abs=2.0,
                ablated_abs=1.0,
                min_baseline_effect_for_reduction=1.0,
            ),
            0.5,
        )


if __name__ == "__main__":
    unittest.main()
