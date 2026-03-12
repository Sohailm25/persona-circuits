"""Tests for the trait-lane redesign tranche packet."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.week2_trait_lane_redesign_packet import build_redesign_packet


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

ADJUDICATION_PATH = RESULTS / "week2_trait_lane_adjudication_packet_20260312T192833Z.json"
NULL_CONTROL_PATH = RESULTS / "week2_trait_lane_null_control_packet_20260312T000000Z.fixture.json"
PROMPT_SENSITIVITY_PATH = RESULTS / "week2_trait_lane_prompt_sensitivity_packet_20260312T000000Z.fixture.json"


class TraitLaneRedesignPacketTests(unittest.TestCase):
    def test_orders_redesign_work_after_adjudication(self) -> None:
        adjudication = json.loads(ADJUDICATION_PATH.read_text(encoding="utf-8"))
        null_control = {
            "artifact_type": "week2_trait_lane_null_control_packet",
        }
        prompt_sensitivity = {
            "artifact_type": "week2_trait_lane_prompt_sensitivity_packet",
        }
        packet = build_redesign_packet(
            adjudication_payload=adjudication,
            null_control_payload=null_control,
            prompt_sensitivity_payload=prompt_sensitivity,
            input_paths={},
        )
        self.assertEqual(packet["status"], "redesign_tranche_defined")
        self.assertEqual(packet["lead_lane"]["current_final_status"], "strong_non_distinct_assistant_style_lane")
        self.assertTrue(packet["launch_policy"]["launch_recommended_now"])
        self.assertEqual(packet["launch_policy"]["next_remote_priority"], "run_null_control_screen")
        self.assertEqual(packet["ordered_work_items"][0]["item"], "run_null_control_screen")


if __name__ == "__main__":
    unittest.main()
