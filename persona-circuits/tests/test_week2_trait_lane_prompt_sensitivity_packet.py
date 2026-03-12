"""Tests for the trait-lane prompt-sensitivity planning packet."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.week2_trait_lane_prompt_sensitivity_packet import build_prompt_sensitivity_packet


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

DEEPER_PACKET_PATH = RESULTS / "week2_trait_lane_deeper_validation_packet_20260312T133907Z.json"
ADJUDICATION_PATH = RESULTS / "week2_trait_lane_adjudication_packet_20260312T192833Z.json"


class TraitLanePromptSensitivityPacketTests(unittest.TestCase):
    def test_selects_balanced_prompt_subsets(self) -> None:
        packet = build_prompt_sensitivity_packet(
            deeper_packet=json.loads(DEEPER_PACKET_PATH.read_text(encoding="utf-8")),
            adjudication_packet=json.loads(ADJUDICATION_PATH.read_text(encoding="utf-8")),
            deeper_packet_path=DEEPER_PACKET_PATH,
            adjudication_packet_path=ADJUDICATION_PATH,
        )
        self.assertEqual(packet["status"], "prompt_sensitivity_defined")
        self.assertEqual(packet["selected_reference_config"]["layer"], 13)
        self.assertEqual(packet["selected_reference_config"]["alpha"], 2.0)
        self.assertEqual(packet["subset_plan"]["extraction"]["n_rows"], 12)
        self.assertEqual(packet["subset_plan"]["heldout"]["n_rows"], 8)
        self.assertEqual(len(packet["subset_plan"]["extraction"]["categories"]), 4)
        self.assertEqual(len(packet["subset_plan"]["heldout"]["categories"]), 4)


if __name__ == "__main__":
    unittest.main()
