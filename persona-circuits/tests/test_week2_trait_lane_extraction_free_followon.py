"""Tests for trait-lane extraction-free follow-on packet construction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_extraction_free_followon import build_followon_packet_from_promotion

ROOT = Path(__file__).resolve().parents[1]
PROMOTION_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_promotion_packet_20260312T002859Z.json"
)


class TraitLaneExtractionFreeFollowonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.promotion_payload = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    def test_default_packet_targets_recommended_followons(self) -> None:
        packet = build_followon_packet_from_promotion(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
        )
        self.assertEqual(packet["selected_lane_ids"], ["lying", "politeness", "honesty"])
        self.assertEqual(packet["candidate_layers"], [14, 15])
        self.assertTrue(packet["launch_recommended_now"])
        self.assertEqual(packet["extraction_method"], "prompt_last")

    def test_packet_resolves_expected_prompt_paths(self) -> None:
        packet = build_followon_packet_from_promotion(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
        )
        by_lane = {row["lane_id"]: row for row in packet["lane_packets"]}
        honesty = by_lane["honesty"]
        politeness = by_lane["politeness"]
        self.assertTrue(honesty["prompt_paths"]["extraction"].endswith("prompts/trait_lanes_v2/honesty_pairs.jsonl"))
        self.assertTrue(honesty["prompt_paths"]["extraction_free"].endswith("prompts/trait_lanes_v2/extraction_free/honesty_eval.jsonl"))
        self.assertEqual(politeness["selected_layer"], 15)
        self.assertAlmostEqual(politeness["selected_alpha"], 2.0)

    def test_explicit_lane_override_keeps_supported_subset_only(self) -> None:
        packet = build_followon_packet_from_promotion(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
            lane_ids_override=["honesty", "lying"],
        )
        self.assertEqual(packet["selected_lane_ids"], ["honesty", "lying"])
        self.assertEqual(packet["candidate_layers"], [14])
        self.assertEqual(len(packet["screening_execution_paths"]), 2)


if __name__ == "__main__":
    unittest.main()
