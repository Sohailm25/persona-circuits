"""Tests for split extraction/validation packet building for branch-local deeper validation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_deeper_validation_packet import build_deeper_validation_packet
from scripts.week2_trait_lane_deeper_validation_split import (
    _build_extraction_packet,
    _build_validation_packet,
    _resolve_selected_lane_packets,
)


ROOT = Path(__file__).resolve().parents[1]
PROMOTION_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_promotion_packet_20260312T030612Z.json"
)
SLICE_A_VECTORS_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_persona_vectors_sliceA_20260311T224305Z.pt"
)


class TraitLaneDeeperValidationSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.promotion_payload = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
        self.deeper_payload = build_deeper_validation_packet(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
            current_extraction_suffix="deeperv1",
            current_heldout_suffix="deeperv1",
        )
        self.selected = _resolve_selected_lane_packets(
            deeper_payload=self.deeper_payload,
            lane_ids_override=None,
        )

    def test_build_extraction_packet_uses_split_policy(self) -> None:
        packet = _build_extraction_packet(
            registry=self.registry,
            deeper_payload=self.deeper_payload,
            deeper_path=PROMOTION_PATH,
            selected_lane_packets=self.selected,
            extraction_method="prompt_last",
            response_max_new_tokens=96,
            response_temperature=0.0,
            run_token="split-test",
        )
        self.assertTrue(packet["launch_recommended_now"])
        self.assertEqual(packet["selected_lane_ids"], ["politeness"])
        self.assertEqual(packet["execution_policy"]["preferred_launch_mode"], "split_extract_validate")
        self.assertIn("deeperv1", packet["lane_packets"][0]["prompt_paths"]["extraction"])

    def test_build_validation_packet_blocks_missing_vectors(self) -> None:
        packet = _build_validation_packet(
            registry=self.registry,
            deeper_payload=self.deeper_payload,
            deeper_path=PROMOTION_PATH,
            selected_lane_packets=self.selected,
            vectors_pt=None,
            extraction_report_json=None,
            run_token="split-test",
        )
        self.assertFalse(packet["launch_recommended_now"])
        self.assertIn("missing_vectors_pt", packet["blockers"])

    def test_build_validation_packet_accepts_existing_vectors_path(self) -> None:
        packet = _build_validation_packet(
            registry=self.registry,
            deeper_payload=self.deeper_payload,
            deeper_path=PROMOTION_PATH,
            selected_lane_packets=self.selected,
            vectors_pt=SLICE_A_VECTORS_PATH,
            extraction_report_json=None,
            run_token="split-test",
        )
        self.assertTrue(packet["launch_recommended_now"])
        self.assertEqual(packet["selected_lane_ids"], ["politeness"])
        self.assertEqual(packet["profile"]["cross_trait_bleed_reference_traits"], ["sycophancy", "assistant_likeness"])


if __name__ == "__main__":
    unittest.main()
