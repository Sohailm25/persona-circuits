"""Tests for the trait-lane null-control planning packet."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.week2_trait_lane_null_control_packet import build_null_control_packet


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

DEEPER_PACKET_PATH = RESULTS / "week2_trait_lane_deeper_validation_packet_20260312T133907Z.json"
ADJUDICATION_PATH = RESULTS / "week2_trait_lane_adjudication_packet_20260312T192833Z.json"


class TraitLaneNullControlPacketTests(unittest.TestCase):
    def test_builds_label_permutation_control_for_politeness(self) -> None:
        packet = build_null_control_packet(
            deeper_packet=json.loads(DEEPER_PACKET_PATH.read_text(encoding="utf-8")),
            adjudication_packet=json.loads(ADJUDICATION_PATH.read_text(encoding="utf-8")),
            deeper_packet_path=DEEPER_PACKET_PATH,
            adjudication_packet_path=ADJUDICATION_PATH,
        )
        design = packet["recommended_control_design"]
        self.assertEqual(packet["status"], "null_control_defined")
        self.assertEqual(design["control_id"], "politeness_label_permutation_null_v1")
        self.assertEqual(design["design_type"], "category_stratified_label_permutation")
        self.assertEqual(packet["recommended_next_remote_action"], "run_label_permutation_null_control_before_any_new_lane_promotion_attempt")
        self.assertEqual(design["permutation_policy"]["seed"], 42)


if __name__ == "__main__":
    unittest.main()
