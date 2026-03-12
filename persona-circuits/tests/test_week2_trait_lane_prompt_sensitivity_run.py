from __future__ import annotations

import unittest

from scripts.week2_trait_lane_prompt_sensitivity_run import _evaluate_behavior_retention, _evaluate_vector_gate


class PromptSensitivityRunTests(unittest.TestCase):
    def test_vector_gate_requires_selected_and_all_layers(self) -> None:
        report = _evaluate_vector_gate(
            same_layer_cosines={"11": 0.91, "12": 0.83, "13": 0.79},
            selected_layer=12,
            gate_cfg={"selected_layer_cosine_ge": 0.8, "all_layers_max_abs_drop_le": 0.2},
        )
        self.assertTrue(report["selected_layer_pass"])
        self.assertFalse(report["all_layers_max_abs_drop_pass"])
        self.assertFalse(report["overall_pass"])

    def test_behavior_retention_requires_fraction_drop_and_sign(self) -> None:
        original = {
            "baseline_low_mean": 20.0,
            "baseline_high_mean": 60.0,
            "steering_shift_mean": 18.0,
            "reversal_shift_mean": 12.0,
        }
        perturbed = {
            "baseline_low_mean": 22.0,
            "baseline_high_mean": 61.0,
            "steering_shift_mean": 10.0,
            "reversal_shift_mean": 8.0,
        }
        report = _evaluate_behavior_retention(
            original_metrics=original,
            perturbed_metrics=perturbed,
            gate_cfg={
                "minimum_fraction_of_original_bidirectional_effect": 0.7,
                "maximum_absolute_effect_drop": 10.0,
                "steering_and_reversal_sign_preserved": True,
            },
        )
        self.assertLess(report["retention_fraction_of_original_bidirectional_effect"], 0.7)
        self.assertFalse(report["overall_pass"])

    def test_behavior_retention_passes_on_small_drop(self) -> None:
        original = {
            "baseline_low_mean": 20.0,
            "baseline_high_mean": 60.0,
            "steering_shift_mean": 18.0,
            "reversal_shift_mean": 12.0,
        }
        perturbed = {
            "baseline_low_mean": 21.0,
            "baseline_high_mean": 59.0,
            "steering_shift_mean": 16.0,
            "reversal_shift_mean": 10.0,
        }
        report = _evaluate_behavior_retention(
            original_metrics=original,
            perturbed_metrics=perturbed,
            gate_cfg={
                "minimum_fraction_of_original_bidirectional_effect": 0.7,
                "maximum_absolute_effect_drop": 10.0,
                "steering_and_reversal_sign_preserved": True,
            },
        )
        self.assertTrue(report["overall_pass"])


if __name__ == "__main__":
    unittest.main()
