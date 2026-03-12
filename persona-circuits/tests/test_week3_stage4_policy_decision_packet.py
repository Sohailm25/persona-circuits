"""Tests for Stage4 policy decision packet generation."""

from __future__ import annotations

import unittest

from scripts.week3_stage4_policy_decision_packet import build_packet


def _method_block(mean_reduction: float, p_value: float, a12: float, n_valid: int, n_total: int) -> dict:
    return {
        "observed_mean_reduction": mean_reduction,
        "selectivity_vs_random": {"p_value_one_sided_ge": p_value},
        "effect_sizes_vs_random_prompt_distribution": {"a12": a12},
        "necessity_threshold_pass": mean_reduction >= 0.8,
        "selectivity_p_threshold_pass": p_value <= 0.01,
        "a12_threshold_pass": a12 >= 0.71,
        "reduction_validity": {"n_valid_prompts": n_valid, "n_total_prompts": n_total, "valid_fraction": n_valid / n_total},
    }


class Stage4PolicyDecisionPacketTests(unittest.TestCase):
    def test_build_packet_strict_fail_high_coverage_recommendation(self) -> None:
        reference = {
            "results_by_trait": {
                "evil": {
                    "behavioral_score_baseline": {"steered_effect_abs_summary": {"mean": 12.0}},
                    "methods": {
                        "resample": _method_block(0.25, 0.05, 0.56, 21, 30),
                        "mean": _method_block(0.18, 0.05, 0.54, 21, 30),
                        "zero": _method_block(0.56, 0.05, 0.70, 21, 30),
                    },
                }
            }
        }
        tranche = {
            "results_by_trait": {
                "evil": {
                    "behavioral_score_baseline": {"steered_effect_abs_summary": {"mean": 14.0}},
                    "methods": {
                        "resample": _method_block(0.24, 0.60, 0.43, 20, 30),
                        "mean": _method_block(0.28, 0.24, 0.41, 20, 30),
                        "zero": _method_block(0.53, 0.05, 0.55, 20, 30),
                    },
                }
            }
        }
        threshold_diag = {
            "analyses": [
                {
                    "artifact_path": "/tmp/ref.json",
                    "traits": {"evil": {"methods": {"resample": {"binding_gate": "necessity"}}}},
                }
            ]
        }
        comparison = {
            "coverage_stability": {"label": "stable"},
            "per_method": {
                "resample": {"deltas": {"p_value_delta": 0.55}, "gate_states": {"necessity": {"reference": False, "tranche": False}}},
                "mean": {"deltas": {"p_value_delta": 0.19}, "gate_states": {"necessity": {"reference": False, "tranche": False}}},
                "zero": {"deltas": {"p_value_delta": 0.0}, "gate_states": {"necessity": {"reference": False, "tranche": False}}},
            },
        }

        packet = build_packet(
            reference_report=reference,
            tranche_report=tranche,
            threshold_diag=threshold_diag,
            tranche_comparison=comparison,
            reference_path="/tmp/ref.json",
            tranche_path="/tmp/trn.json",
            threshold_diag_path="/tmp/diag.json",
            tranche_comparison_path="/tmp/cmp.json",
            trait="evil",
        )
        self.assertFalse(packet["strict_summary"]["any_method_strict_pass_either_run"])
        self.assertEqual(
            packet["recommendation"]["recommended_path"],
            "strict_fail_with_dual_scorecard_candidate",
        )
        self.assertEqual(packet["tranche_comparison_summary"]["coverage_stability"]["label"], "stable")

    def test_build_packet_missing_trait_raises(self) -> None:
        with self.assertRaises(KeyError):
            build_packet(
                reference_report={"results_by_trait": {}},
                tranche_report={"results_by_trait": {}},
                threshold_diag={"analyses": []},
                tranche_comparison={},
                reference_path="/tmp/ref.json",
                tranche_path="/tmp/trn.json",
                threshold_diag_path="/tmp/diag.json",
                tranche_comparison_path="/tmp/cmp.json",
                trait="evil",
            )


if __name__ == "__main__":
    unittest.main()
