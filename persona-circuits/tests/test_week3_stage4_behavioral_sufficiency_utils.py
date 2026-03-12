import unittest

import numpy as np

from scripts.week3_stage4_behavioral_sufficiency import (
    _build_dose_monotonicity_summary,
    _build_sufficiency_dose_report,
    _minimum_random_sets_for_significance,
    _parse_ablation_scope,
    _parse_claim_mode,
    _parse_dose_response,
    _preserved_effect_fraction,
    _resolve_run_token,
    _sample_random_preserved_sets,
)


class Stage4BehavioralSufficiencyUtilsTests(unittest.TestCase):
    def test_parse_dose_response(self):
        self.assertEqual(_parse_dose_response("0.25,0.5,1.0"), [0.25, 0.5, 1.0])
        with self.assertRaises(ValueError):
            _parse_dose_response("0.0,0.5")
        with self.assertRaises(ValueError):
            _parse_dose_response("")

    def test_parse_scope_and_claim_mode(self):
        self.assertEqual(_parse_ablation_scope("full_sae_complement"), "full_sae_complement")
        self.assertEqual(_parse_claim_mode("claim_grade"), "claim_grade")
        with self.assertRaises(ValueError):
            _parse_ablation_scope("bad-scope")
        with self.assertRaises(ValueError):
            _parse_claim_mode("bad-mode")

    def test_resolve_run_token_preserves_explicit_value(self):
        self.assertEqual(_resolve_run_token("resume-token-123"), "resume-token-123")

    def test_preserved_effect_fraction_threshold(self):
        self.assertIsNone(
            _preserved_effect_fraction(
                baseline_delta=0.0,
                circuit_only_delta=0.0,
                min_baseline_effect_for_preservation=1.0,
            )
        )
        self.assertAlmostEqual(
            _preserved_effect_fraction(
                baseline_delta=10.0,
                circuit_only_delta=7.0,
                min_baseline_effect_for_preservation=1.0,
            ),
            0.7,
        )
        self.assertAlmostEqual(
            _preserved_effect_fraction(
                baseline_delta=-10.0,
                circuit_only_delta=-5.0,
                min_baseline_effect_for_preservation=1.0,
            ),
            0.5,
        )

    def test_preserved_effect_fraction_penalizes_sign_flip(self):
        self.assertLess(
            _preserved_effect_fraction(
                baseline_delta=20.0,
                circuit_only_delta=-20.0,
                min_baseline_effect_for_preservation=1.0,
            ),
            0.0,
        )

    def test_sample_random_preserved_sets_shape(self):
        out = _sample_random_preserved_sets(
            candidate_pool_ids=[1, 2, 3, 4, 5, 6],
            preserved_set_size=3,
            n_sets=5,
            seed=42,
        )
        self.assertEqual(out.shape, (5, 3))
        for row in out:
            self.assertEqual(len(set(row.tolist())), 3)
            self.assertTrue(all(int(x) in {1, 2, 3, 4, 5, 6} for x in row.tolist()))

    def test_build_sufficiency_dose_report_fields(self):
        report = _build_sufficiency_dose_report(
            observed_prompt_preservation_full=[1.4, 0.7, None, 0.9],
            valid_prompt_mask=np.asarray([True, True, False, True], dtype=bool),
            baseline_effect_abs=np.asarray([10.0, 12.0, 0.4, 15.0], dtype=np.float64),
            random_set_means=np.asarray([0.4] * 30, dtype=np.float64),
            random_prompt_preservations=np.asarray([0.3, 0.45, 0.6] * 10, dtype=np.float64),
            observed_circuit_only_scores=np.asarray([50.0, 55.0, 52.0, 58.0], dtype=np.float64),
            baseline_steered_scores=np.asarray([52.0, 58.0, 53.0, 60.0], dtype=np.float64),
            n_random_sets_total=30,
            min_baseline_effect_for_preservation=1.0,
            min_valid_prompt_count=3,
            min_valid_prompt_fraction=0.5,
            thresholds={"sufficiency": 0.6, "significance": 0.05, "a12_minimum": 0.6},
            seed=42,
            n_bootstrap=100,
        )
        self.assertIn("observed_mean_preservation", report)
        self.assertIn("sufficiency_threshold_pass", report)
        self.assertTrue(report["sufficiency_threshold_pass"])
        self.assertEqual(report["preservation_validity"]["n_valid_prompts"], 3)
        self.assertAlmostEqual(report["observed_mean_preservation"], (1.0 + 0.7 + 0.9) / 3.0)
        self.assertAlmostEqual(
            report["observed_mean_preservation_raw_ratio"], (1.4 + 0.7 + 0.9) / 3.0
        )
        self.assertEqual(report["over_preservation_diagnostic"]["n_raw_ratio_gt_1"], 1)
        self.assertTrue(report["selectivity_vs_random"]["significance_threshold_feasible"])

    def test_selectivity_infeasible_when_random_sets_too_shallow(self):
        report = _build_sufficiency_dose_report(
            observed_prompt_preservation_full=[0.8, 0.7, 0.9, 0.85, 0.75],
            valid_prompt_mask=np.asarray([True, True, True, True, True], dtype=bool),
            baseline_effect_abs=np.asarray([10.0, 12.0, 11.0, 13.0, 9.0], dtype=np.float64),
            random_set_means=np.asarray([0.4] * 5, dtype=np.float64),
            random_prompt_preservations=np.asarray([0.3, 0.45, 0.6, 0.35, 0.5], dtype=np.float64),
            observed_circuit_only_scores=np.asarray([50.0, 55.0, 52.0, 58.0, 49.0], dtype=np.float64),
            baseline_steered_scores=np.asarray([52.0, 58.0, 53.0, 60.0, 50.0], dtype=np.float64),
            n_random_sets_total=5,
            min_baseline_effect_for_preservation=1.0,
            min_valid_prompt_count=5,
            min_valid_prompt_fraction=0.5,
            thresholds={"sufficiency": 0.6, "significance": 0.01, "a12_minimum": 0.6},
            seed=42,
            n_bootstrap=100,
        )
        self.assertFalse(report["selectivity_vs_random"]["significance_threshold_feasible"])
        self.assertFalse(report["thresholds_evaluable_detail"]["selectivity"])
        self.assertFalse(report["selectivity_p_threshold_pass"])
        self.assertEqual(report["selectivity_vs_random"]["minimum_sets_required_for_significance"], 99)

    def test_sparse_valid_prompt_coverage_blocks_threshold_pass(self):
        report = _build_sufficiency_dose_report(
            observed_prompt_preservation_full=[0.95, None, None, None, None, None, None, None, None, None],
            valid_prompt_mask=np.asarray([True, False, False, False, False, False, False, False, False, False], dtype=bool),
            baseline_effect_abs=np.asarray([10.0, 0.2, 0.1, 0.1, 0.2, 0.4, 0.3, 0.1, 0.2, 0.1], dtype=np.float64),
            random_set_means=np.asarray([0.2] * 100, dtype=np.float64),
            random_prompt_preservations=np.asarray([0.2] * 100, dtype=np.float64),
            observed_circuit_only_scores=np.asarray([50.0] * 10, dtype=np.float64),
            baseline_steered_scores=np.asarray([52.0] * 10, dtype=np.float64),
            n_random_sets_total=100,
            min_baseline_effect_for_preservation=1.0,
            min_valid_prompt_count=5,
            min_valid_prompt_fraction=0.5,
            thresholds={"sufficiency": 0.6, "significance": 0.01, "a12_minimum": 0.6},
            seed=42,
            n_bootstrap=100,
        )
        self.assertFalse(report["preservation_validity"]["valid_prompt_threshold_pass"])
        self.assertFalse(report["thresholds_evaluable_detail"]["sufficiency"])
        self.assertFalse(report["sufficiency_threshold_pass"])

    def test_minimum_random_sets_for_significance(self):
        self.assertEqual(_minimum_random_sets_for_significance(0.05), 19)
        self.assertEqual(_minimum_random_sets_for_significance(0.01), 99)

    def test_dose_monotonicity_summary(self):
        passing = _build_dose_monotonicity_summary(
            dose_fraction_reports={
                "0.25": {"observed_mean_preservation": 0.40},
                "0.50": {"observed_mean_preservation": 0.52},
                "1.00": {"observed_mean_preservation": 0.60},
            },
            max_allowed_drop=0.05,
        )
        self.assertTrue(passing["evaluable"])
        self.assertTrue(passing["pass"])
        failing = _build_dose_monotonicity_summary(
            dose_fraction_reports={
                "0.25": {"observed_mean_preservation": 0.70},
                "0.50": {"observed_mean_preservation": 0.55},
                "1.00": {"observed_mean_preservation": 0.56},
            },
            max_allowed_drop=0.05,
        )
        self.assertTrue(failing["evaluable"])
        self.assertFalse(failing["pass"])
        self.assertAlmostEqual(failing["max_observed_drop"], 0.15)


if __name__ == "__main__":
    unittest.main()
