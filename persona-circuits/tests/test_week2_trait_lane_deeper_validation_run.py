"""Tests for the trait-lane deeper Week 2 validation runner helpers."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_deeper_validation_packet import build_deeper_validation_packet
from scripts.week2_trait_lane_deeper_validation_run import (
    _build_execution_packet,
    _normalize_vectors,
    _resolve_cross_trait_bleed_traits,
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


class TraitLaneDeeperValidationRunTests(unittest.TestCase):
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

    def test_resolve_selected_lane_packets_defaults_to_politeness(self) -> None:
        packets = _resolve_selected_lane_packets(
            deeper_payload=self.deeper_payload,
            lane_ids_override=None,
        )
        self.assertEqual([packet["lane_id"] for packet in packets], ["politeness"])

    def test_build_execution_packet_uses_screening_grid(self) -> None:
        selected = _resolve_selected_lane_packets(
            deeper_payload=self.deeper_payload,
            lane_ids_override=None,
        )
        packet = _build_execution_packet(
            registry=self.registry,
            deeper_payload=self.deeper_payload,
            deeper_path=PROMOTION_PATH,
            selected_lane_packets=selected,
            extraction_method="prompt_last",
            response_max_new_tokens=96,
            response_temperature=0.0,
            run_token="test-token",
        )
        self.assertTrue(packet["launch_recommended_now"])
        self.assertEqual(packet["selected_lane_ids"], ["politeness"])
        self.assertEqual(packet["condition_matrix"]["n_rows"], 6 * 3)
        row = packet["lane_packets"][0]
        self.assertEqual(row["screening_layers"], [11, 12, 13, 14, 15, 16])
        self.assertEqual(row["screening_alpha_grid"], [0.5, 1.0, 2.0])
        self.assertIn("politeness_pairs_deeperv1.jsonl", row["prompt_paths"]["extraction"])
        self.assertIn(
            "branch-local reference rubrics defined in the deeper-validation profile",
            packet["notes"][2],
        )

    def test_normalize_vectors_coerces_layer_keys_to_ints(self) -> None:
        raw = {"politeness": {"15": [0.1, 0.2], "16": [0.3, 0.4]}}
        normalized = _normalize_vectors(raw)
        self.assertEqual(sorted(normalized["politeness"].keys()), [15, 16])
        self.assertEqual(normalized["politeness"][15], [0.1, 0.2])

    def test_resolve_cross_trait_bleed_traits_deduplicates_lane(self) -> None:
        traits = _resolve_cross_trait_bleed_traits(
            lane_id="assistant_likeness",
            profile={"cross_trait_bleed_reference_traits": ["assistant_likeness", "sycophancy"]},
        )
        self.assertEqual(traits, ["assistant_likeness", "sycophancy"])


if __name__ == "__main__":
    unittest.main()
