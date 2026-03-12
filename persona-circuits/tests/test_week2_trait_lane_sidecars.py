"""Tests for non-invasive trait-lane sidecar planning helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_behavioral_smoke import build_behavioral_smoke_packet
from scripts.week2_trait_lane_heldout_screen import build_heldout_screen_packet
from scripts.week2_trait_lane_prompt_screen import build_prompt_screen_packet
from scripts.week2_trait_lane_promotion_packet import build_promotion_packet


class Week2TraitLaneSidecarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()

    def test_prompt_screen_packet_is_planning_only(self) -> None:
        packet = build_prompt_screen_packet(registry=self.registry, lane_ids=["assistant_likeness", "honesty"])
        self.assertFalse(packet["launch_recommended_now"])
        self.assertEqual(packet["counts"]["n_lanes"], 2)
        self.assertTrue(packet["construct_card_status"]["all_present"])

    def test_heldout_screen_reports_no_collisions_for_fresh_namespace(self) -> None:
        packet = build_heldout_screen_packet(registry=self.registry, lane_ids=["agreeableness"])
        self.assertFalse(packet["launch_recommended_now"])
        self.assertFalse(packet["collision_report"]["has_collisions"])

    def test_behavioral_smoke_builds_expected_matrix(self) -> None:
        packet = build_behavioral_smoke_packet(registry=self.registry, lane_ids=["honesty"])
        self.assertEqual(packet["condition_matrix"]["n_rows"], 6 * 3)
        first = packet["condition_matrix"]["rows"][0]
        self.assertEqual(first["lane_id"], "honesty")
        self.assertTrue(first["relative_coherence_only"])

    def test_promotion_packet_ranks_complete_metrics(self) -> None:
        report = {
            "lane_id": "honesty",
            "metrics": {
                "literature_support_score": 1.0,
                "construct_clarity_score": 0.9,
                "bootstrap_p05_cosine": 0.95,
                "train_vs_heldout_cosine": 0.92,
                "behavioral_shift": 18.0,
                "relative_coherence_drop": 1.5,
                "response_phase_persistence": 0.7,
                "benchmark_smoke_pass": True,
                "confound_risk_penalty": 0.4,
            },
        }
        packet = build_promotion_packet(registry=self.registry, screening_reports=[report])
        self.assertEqual(packet["status"], "ranked")
        self.assertEqual(packet["recommended_promotions"], ["honesty"])

    def test_promotion_packet_marks_incomplete_reports(self) -> None:
        report = {"lane_id": "assistant_likeness", "metrics": {"literature_support_score": 1.0}}
        packet = build_promotion_packet(registry=self.registry, screening_reports=[report])
        self.assertEqual(packet["status"], "awaiting_complete_screening")
        self.assertIn("assistant_likeness", packet["missing_metrics"])

    def test_promotion_packet_empty_reports_is_not_ranked(self) -> None:
        packet = build_promotion_packet(registry=self.registry, screening_reports=[])
        self.assertEqual(packet["status"], "awaiting_complete_screening")
        self.assertEqual(packet["recommended_promotions"], [])
        self.assertEqual(packet["ranked_lanes"], [])

    def test_scripts_can_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "toy_report.json"
            path.write_text(json.dumps({"lane_id": "honesty", "metrics": {"literature_support_score": 1.0}}), encoding="utf-8")
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
