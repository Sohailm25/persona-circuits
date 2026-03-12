"""Tests for trait-lane external-smoke evaluation helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_external_smoke_eval import (
    _summarize_lane_metrics,
    build_external_smoke_packet_from_promotion,
)


class TraitLaneExternalSmokeEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.promotion_payload = {
            "recommended_followon_lanes": ["lying", "politeness", "honesty"],
            "ranked_lanes": [
                {
                    "lane_id": "lying",
                    "family_id": "honesty_deception",
                    "display_name": "Lying",
                    "judge_rubric_id": "lying",
                    "screening_execution_path": "/tmp/slice_b.json",
                    "selected_layer": 14,
                    "selected_alpha": 2.0,
                    "orientation_sign": 1,
                    "orientation_label": "aligned_with_rubric_high_direction",
                    "screening_status": "followon_candidate_with_limitation",
                },
                {
                    "lane_id": "honesty",
                    "family_id": "honesty_deception",
                    "display_name": "Honesty",
                    "judge_rubric_id": "honesty",
                    "screening_execution_path": "/tmp/slice_a.json",
                    "selected_layer": 14,
                    "selected_alpha": 0.5,
                    "orientation_sign": 1,
                    "orientation_label": "aligned_with_rubric_high_direction",
                    "screening_status": "followon_candidate_with_limitation",
                },
                {
                    "lane_id": "politeness",
                    "family_id": "light_style_persona",
                    "display_name": "Politeness",
                    "judge_rubric_id": "politeness",
                    "screening_execution_path": "/tmp/slice_a.json",
                    "selected_layer": 15,
                    "selected_alpha": 2.0,
                    "orientation_sign": 1,
                    "orientation_label": "aligned_with_rubric_high_direction",
                    "screening_status": "followon_candidate_with_limitation",
                },
            ],
        }

    def test_packet_defaults_to_truthfulness_external_transfer_lanes(self) -> None:
        packet = build_external_smoke_packet_from_promotion(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=Path("/tmp/promotion.json"),
        )
        self.assertEqual(packet["selected_lane_ids"], ["lying", "honesty"])
        self.assertEqual(packet["candidate_layers"], [14])
        self.assertEqual([row["selected_alpha"] for row in packet["lane_packets"]], [2.0, 0.5])

    def test_packet_respects_lane_override(self) -> None:
        packet = build_external_smoke_packet_from_promotion(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=Path("/tmp/promotion.json"),
            lane_ids_override=["lying"],
        )
        self.assertEqual(packet["selected_lane_ids"], ["lying"])
        self.assertEqual(len(packet["lane_packets"]), 1)
        self.assertIn("lying_external_smoke.jsonl", packet["lane_packets"][0]["prompt_paths"]["external_smoke"])

    def test_metric_summary_computes_expected_gates(self) -> None:
        summary = _summarize_lane_metrics(
            baseline_low_scores=[20.0, 30.0],
            baseline_high_scores=[50.0, 55.0],
            plus_scores=[40.0, 45.0],
            minus_scores=[10.0, 15.0],
            baseline_low_coherence_scores=[80.0, 82.0],
            baseline_high_coherence_scores=[81.0, 83.0],
            plus_coherence_scores=[78.0, 79.0],
            minus_coherence_scores=[77.0, 78.0],
            judge_attempts=[1, 1, 1, 1, 1, 1, 1, 1],
            min_plus_minus_delta=8.0,
            coherence_max_drop=10.0,
        )
        self.assertAlmostEqual(summary["plus_vs_baseline"], 17.5)
        self.assertAlmostEqual(summary["baseline_vs_minus"], 40.0)
        self.assertAlmostEqual(summary["plus_vs_minus"], 30.0)
        self.assertTrue(summary["quality_gates"]["overall_pass"])

    def test_metric_summary_fails_when_judge_proxy_or_coherence_bad(self) -> None:
        summary = _summarize_lane_metrics(
            baseline_low_scores=[50.0, 50.0],
            baseline_high_scores=[60.0, 60.0],
            plus_scores=[52.0, 52.0],
            minus_scores=[49.0, 49.0],
            baseline_low_coherence_scores=[90.0, 90.0],
            baseline_high_coherence_scores=[90.0, 90.0],
            plus_coherence_scores=[60.0, 60.0],
            minus_coherence_scores=[60.0, 60.0],
            judge_attempts=[1, 2, 1, 2, 1, 2, 1, 2],
            min_plus_minus_delta=8.0,
            coherence_max_drop=10.0,
        )
        self.assertFalse(summary["quality_gates"]["plus_minus_delta_ge_threshold"])
        self.assertFalse(summary["quality_gates"]["judge_parse_fail_rate_le_0_05"])
        self.assertFalse(summary["quality_gates"]["coherence_relative_drop_le_10"])
        self.assertFalse(summary["quality_gates"]["overall_pass"])


if __name__ == "__main__":
    unittest.main()
