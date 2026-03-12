"""Tests for week2_rollout_stability_sensitivity helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_rollout_stability_sensitivity import _compare_reports  # noqa: E402


class Week2RolloutStabilitySensitivityTests(unittest.TestCase):
    def test_compare_reports_metrics_and_gates(self) -> None:
        r3 = {
            "selected": {"layer": 12, "alpha": 2.0},
            "selected_test_evaluation": {"metric": {"bidirectional_effect": 30.0, "steering_shift_mean": 8.0, "reversal_shift_mean": 22.0}},
            "quality_gates": {"overall_pass": False, "coherence_pass": False, "cross_trait_bleed_pass": True, "bidirectional_effect_pass": True},
            "run_metadata": {"confirm_rollouts_per_prompt": 3},
        }
        r5 = {
            "selected": {"layer": 12, "alpha": 2.0},
            "selected_test_evaluation": {"metric": {"bidirectional_effect": 28.0, "steering_shift_mean": 7.0, "reversal_shift_mean": 21.0}},
            "quality_gates": {"overall_pass": False, "coherence_pass": False, "cross_trait_bleed_pass": True, "bidirectional_effect_pass": True},
            "run_metadata": {"confirm_rollouts_per_prompt": 5},
        }
        out = _compare_reports("sycophancy", r3, r5)
        self.assertEqual(out["trait"], "sycophancy")
        self.assertEqual(
            out["metrics"]["bidirectional_effect"]["delta_rollout5_minus_rollout3"],
            -2.0,
        )
        self.assertFalse(out["quality_gates"]["overall_pass"]["rollout5"])
        self.assertNotIn("plus_mean", out["metrics"])
        self.assertNotIn("minus_mean", out["metrics"])

    def test_compare_reports_raises_when_required_metric_missing(self) -> None:
        r3 = {
            "selected_test_evaluation": {
                "metric": {
                    "bidirectional_effect": 30.0,
                    "steering_shift_mean": 8.0,
                    "reversal_shift_mean": 22.0,
                }
            },
            "quality_gates": {},
            "run_metadata": {},
        }
        r5 = {
            "selected_test_evaluation": {
                "metric": {
                    "bidirectional_effect": 28.0,
                    "steering_shift_mean": 7.0,
                }
            },
            "quality_gates": {},
            "run_metadata": {},
        }
        with self.assertRaises(KeyError):
            _compare_reports("sycophancy", r3, r5)


if __name__ == "__main__":
    unittest.main()
