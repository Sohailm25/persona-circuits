"""Unit tests for Stage4 threshold-binding diagnostics."""

from __future__ import annotations

import unittest

from scripts.week3_stage4_threshold_binding_diagnostic import _method_binding_snapshot


class ThresholdBindingTests(unittest.TestCase):
    def test_method_binding_snapshot_flags_failures(self) -> None:
        thresholds = {"necessity": 0.8, "significance": 0.01, "a12_minimum": 0.71}
        method_payload = {
            "observed_mean_reduction": 0.25,
            "selectivity_vs_random": {"p_value_one_sided_ge": 0.0476},
            "effect_sizes_vs_random_prompt_distribution": {"a12": 0.56},
            "necessity_threshold_pass": False,
            "selectivity_p_threshold_pass": False,
            "a12_threshold_pass": False,
        }
        out = _method_binding_snapshot(method_payload, thresholds)
        self.assertAlmostEqual(out["margins"]["necessity_margin"], -0.55)
        self.assertAlmostEqual(out["margins"]["significance_margin"], -0.0376)
        self.assertAlmostEqual(out["margins"]["a12_margin"], -0.15)
        self.assertEqual(set(out["failed_gates"]), {"necessity", "significance", "a12"})
        self.assertEqual(out["binding_gate"], "necessity")

    def test_method_binding_snapshot_handles_missing_observations(self) -> None:
        thresholds = {"necessity": 0.8, "significance": 0.01, "a12_minimum": 0.71}
        method_payload = {
            "observed_mean_reduction": None,
            "selectivity_vs_random": {},
            "effect_sizes_vs_random_prompt_distribution": {},
            "necessity_threshold_pass": False,
            "selectivity_p_threshold_pass": False,
            "a12_threshold_pass": False,
        }
        out = _method_binding_snapshot(method_payload, thresholds)
        self.assertIsNone(out["margins"]["necessity_margin"])
        self.assertIsNone(out["margins"]["significance_margin"])
        self.assertIsNone(out["margins"]["a12_margin"])
        self.assertIsNone(out["binding_gate"])


if __name__ == "__main__":
    unittest.main()

