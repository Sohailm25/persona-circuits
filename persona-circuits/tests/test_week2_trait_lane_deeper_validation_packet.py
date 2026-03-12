from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_deeper_validation_packet import (
    DEFAULT_TARGET_EXTRACTION_PAIRS,
    DEFAULT_TARGET_HELDOUT_SPLIT,
    build_deeper_validation_packet,
)

ROOT = Path(__file__).resolve().parents[1]
PROMOTION_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_promotion_packet_20260312T030612Z.json"
)


class TraitLaneDeeperValidationPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.promotion_payload = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    def test_default_packet_selects_supported_lane_only(self) -> None:
        packet = build_deeper_validation_packet(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
        )
        self.assertEqual(packet["selected_lane_ids"], ["politeness"])
        self.assertFalse(packet["launch_recommended_now"])
        politeness = packet["lane_packets"][0]
        self.assertEqual(politeness["screening_status"], "promotion_candidate_supported")
        self.assertEqual(politeness["current_prompt_counts"]["extraction_pairs"], 24)
        self.assertEqual(politeness["current_prompt_counts"]["heldout_pairs"], 12)
        profile = packet["profiles"]["deeper_validation_sidecar"]
        self.assertTrue(profile["cross_trait_bleed_enabled"])
        self.assertEqual(profile["cross_trait_bleed_reference_traits"], ["sycophancy", "assistant_likeness"])
        self.assertEqual(profile["cross_trait_bleed_max_fraction"], 0.3)
        self.assertEqual(packet["response_phase_policy_snapshot"]["status"], "tracked_limitation_not_hard_gate")
        self.assertEqual(packet["execution_policy"]["preferred_launch_mode"], "split_extract_validate")
        self.assertFalse(packet["execution_policy"]["legacy_single_app_wrapper_allowed"])
        self.assertEqual(
            politeness["expansion_requirements"]["deeper_validation_sidecar"]["target_extraction_pairs"],
            DEFAULT_TARGET_EXTRACTION_PAIRS,
        )
        self.assertEqual(
            politeness["expansion_requirements"]["deeper_validation_sidecar"]["target_heldout_pairs"],
            sum(DEFAULT_TARGET_HELDOUT_SPLIT),
        )
        self.assertEqual(
            politeness["expansion_requirements"]["deeper_validation_sidecar"]["missing_extraction_pairs"],
            24,
        )
        self.assertEqual(
            politeness["expansion_requirements"]["deeper_validation_sidecar"]["missing_heldout_pairs"],
            18,
        )

    def test_include_conditional_adds_lying(self) -> None:
        packet = build_deeper_validation_packet(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
            include_conditional=True,
        )
        self.assertEqual(packet["selected_lane_ids"], ["politeness", "lying"])
        self.assertEqual(len(packet["lane_packets"]), 2)

    def test_explicit_override_can_target_conditional_lane_only(self) -> None:
        packet = build_deeper_validation_packet(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
            lane_ids_override=["lying"],
        )
        self.assertEqual(packet["selected_lane_ids"], ["lying"])
        self.assertFalse(packet["launch_recommended_now"])
        lying = packet["lane_packets"][0]
        self.assertEqual(lying["screening_status"], "conditional_followon_candidate")
        self.assertEqual(lying["followon_state"]["external_smoke"], "one_sided")

    def test_current_suffixes_can_mark_politeness_ready(self) -> None:
        packet = build_deeper_validation_packet(
            registry=self.registry,
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
            current_extraction_suffix="deeperv1",
            current_heldout_suffix="deeperv1",
        )
        self.assertTrue(packet["launch_recommended_now"])
        self.assertEqual(packet["current_prompt_suffixes"]["extraction"], "deeperv1")
        self.assertEqual(packet["current_prompt_suffixes"]["heldout"], "deeperv1")
        politeness = packet["lane_packets"][0]
        self.assertEqual(politeness["current_prompt_counts"]["extraction_pairs"], 48)
        self.assertEqual(politeness["current_prompt_counts"]["heldout_pairs"], 30)
        self.assertTrue(politeness["readiness"]["deeper_validation_sidecar_ready"])


if __name__ == "__main__":
    unittest.main()
