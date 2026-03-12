from __future__ import annotations

import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_null_control_run import (
    _evaluate_control_outcome,
    build_null_control_execution_packet,
)


class TraitLaneNullControlRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.null_packet = {
            "source_lane_id": "politeness",
            "evaluation_plan": {
                "false_positive_alerts": {
                    "promotion_status_not_hold": True,
                    "oriented_bidirectional_effect_ge": 10.0,
                    "bootstrap_p05_cosine_ge": 0.8,
                    "response_phase_persistence_ge": 0.7,
                }
            },
            "recommended_control_design": {
                "control_id": "politeness_label_permutation_null_v1",
                "design_type": "category_stratified_label_permutation",
            },
        }
        self.prompt_summary = {
            "control_id": "politeness_label_permutation_null_v1",
            "output_prompt_paths": {
                "extraction": "/tmp/control_extract.jsonl",
                "heldout": "/tmp/control_heldout.jsonl",
            },
        }

    def test_execution_packet_uses_source_lane_screening_profile(self) -> None:
        packet = build_null_control_execution_packet(
            registry=self.registry,
            null_control_packet=self.null_packet,
            null_control_packet_path=Path("/tmp/null_packet.json"),
            prompt_summary=self.prompt_summary,
            prompt_summary_path=Path("/tmp/prompt_summary.json"),
            judge_model="claude-sonnet-4-6",
            prompt_limit=4,
        )
        self.assertEqual(packet["selected_lane_ids"], ["politeness_label_permutation_null_v1"])
        self.assertEqual(packet["readiness_artifact_path"], "/tmp/null_packet.json")
        self.assertEqual(packet["source_lane_id"], "politeness")
        self.assertEqual(packet["lane_packets"][0]["judge_rubric_id"], "politeness")
        self.assertEqual(len(packet["lane_packets"][0]["screening_layers"]), 6)
        self.assertEqual(packet["condition_matrix"]["n_rows"], 18)

    def test_evaluate_control_outcome_flags_promotion_like_null(self) -> None:
        screening_report = {
            "selected_lane_ids": ["politeness_label_permutation_null_v1"],
            "bootstrap_robustness": {
                "traits": {
                    "politeness_label_permutation_null_v1": {
                        "bootstrap": {"pairwise_cosine_summary": {"p05": 0.95}},
                        "train_vs_heldout_vector_cosine": 0.91,
                    }
                }
            },
            "position_ablation": {
                "diagnostics": {
                    "politeness_label_permutation_null_v1": {
                        "layers": {
                            "13": {"pairwise_cosines": {"prompt_last_vs_response_mean": 0.82}}
                        }
                    }
                }
            },
            "behavioral_smoke": {
                "lane_reports": [
                    {
                        "baseline_summary": {"low_score_mean": 20.0, "high_score_mean": 60.0},
                        "selected_condition": {
                            "layer": 13,
                            "alpha": 2.0,
                            "steering_shift_mean": 12.0,
                            "reversal_shift_mean": 10.0,
                            "bidirectional_effect": 22.0,
                            "coherence_pass": True,
                            "coherence_drop": 1.0,
                        },
                    }
                ]
            },
        }
        evaluation = _evaluate_control_outcome(
            registry=self.registry,
            source_lane_id="politeness",
            screening_report=screening_report,
            null_control_packet=self.null_packet,
        )
        self.assertEqual(evaluation["screening_status"], "promotion_candidate_strong")
        self.assertTrue(evaluation["promotion_frontier_crossed"])
        self.assertTrue(evaluation["false_positive_alerts"]["overall_false_positive_alert"])

    def test_evaluate_control_outcome_accepts_low_signal_null(self) -> None:
        screening_report = {
            "selected_lane_ids": ["politeness_label_permutation_null_v1"],
            "bootstrap_robustness": {
                "traits": {
                    "politeness_label_permutation_null_v1": {
                        "bootstrap": {"pairwise_cosine_summary": {"p05": 0.2}},
                        "train_vs_heldout_vector_cosine": 0.1,
                    }
                }
            },
            "position_ablation": {
                "diagnostics": {
                    "politeness_label_permutation_null_v1": {
                        "layers": {
                            "13": {"pairwise_cosines": {"prompt_last_vs_response_mean": 0.05}}
                        }
                    }
                }
            },
            "behavioral_smoke": {
                "lane_reports": [
                    {
                        "baseline_summary": {"low_score_mean": 40.0, "high_score_mean": 45.0},
                        "selected_condition": {
                            "layer": 13,
                            "alpha": 0.5,
                            "steering_shift_mean": 0.5,
                            "reversal_shift_mean": -0.2,
                            "bidirectional_effect": 0.3,
                            "coherence_pass": True,
                            "coherence_drop": 0.5,
                        },
                    }
                ]
            },
        }
        evaluation = _evaluate_control_outcome(
            registry=self.registry,
            source_lane_id="politeness",
            screening_report=screening_report,
            null_control_packet=self.null_packet,
        )
        self.assertEqual(evaluation["screening_status"], "hold")
        self.assertFalse(evaluation["promotion_frontier_crossed"])
        self.assertFalse(evaluation["false_positive_alerts"]["overall_false_positive_alert"])


if __name__ == "__main__":
    unittest.main()
