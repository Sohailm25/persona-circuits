"""Tests for final trait-lane branch adjudication."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.week2_trait_lane_adjudication_packet import build_adjudication_packet


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"

PROMOTION_PATH = RESULTS / "week2_trait_lane_promotion_packet_20260312T030612Z.json"
DEEPER_VALIDATION_PATH = RESULTS / "week2_trait_lane_deeper_validation_validation_20260312T134851Z.json"
OVERLAP_PATH = RESULTS / "week2_trait_lane_overlap_diagnostic_20260312T131958Z.json"
EXTRACTION_FREE_PATH = RESULTS / "week2_trait_lane_extraction_free_followon_20260312T004752Z.json"
EXTERNAL_SMOKE_PATH = RESULTS / "week2_trait_lane_external_smoke_eval_20260312T011734Z.json"


class TraitLaneAdjudicationPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.promotion_payload = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
        self.deeper_validation_payload = json.loads(DEEPER_VALIDATION_PATH.read_text(encoding="utf-8"))
        self.overlap_payload = json.loads(OVERLAP_PATH.read_text(encoding="utf-8"))
        self.extraction_free_payload = json.loads(EXTRACTION_FREE_PATH.read_text(encoding="utf-8"))
        self.external_smoke_payload = json.loads(EXTERNAL_SMOKE_PATH.read_text(encoding="utf-8"))

    def test_branch_is_adjudicated_as_no_independent_promotion(self) -> None:
        packet = build_adjudication_packet(
            promotion_payload=self.promotion_payload,
            deeper_validation_payload=self.deeper_validation_payload,
            overlap_payload=self.overlap_payload,
            extraction_free_payload=self.extraction_free_payload,
            external_smoke_payload=self.external_smoke_payload,
            input_paths={},
        )
        self.assertEqual(packet["status"], "no_independent_promotion_under_current_evidence")
        self.assertEqual(packet["independent_promotion_recommended"], [])
        self.assertEqual(
            packet["recommended_next_action"],
            "freeze_independent_promotion_and_treat_politeness_as_assistant_style_modulation",
        )

    def test_politeness_is_classified_as_strong_but_non_distinct(self) -> None:
        packet = build_adjudication_packet(
            promotion_payload=self.promotion_payload,
            deeper_validation_payload=self.deeper_validation_payload,
            overlap_payload=self.overlap_payload,
            extraction_free_payload=self.extraction_free_payload,
            external_smoke_payload=self.external_smoke_payload,
            input_paths={},
        )
        politeness = packet["lane_adjudications"]["politeness"]
        self.assertEqual(politeness["final_status"], "strong_non_distinct_assistant_style_lane")
        self.assertEqual(politeness["promotion_decision"], "do_not_promote_as_independent_persona_lane")
        self.assertFalse(politeness["overall_pass"])
        self.assertFalse(politeness["cross_trait_bleed_pass"])
        self.assertGreater(politeness["assistant_likeness_effect"], politeness["selected_test_bidirectional_effect"])
        self.assertGreater(politeness["assistant_likeness_overlap_max_same_layer"], 0.4)
        self.assertLess(politeness["sycophancy_selected_pair_overlap"], 0.4)

    def test_truthfulness_lanes_are_reclassified_conservatively(self) -> None:
        packet = build_adjudication_packet(
            promotion_payload=self.promotion_payload,
            deeper_validation_payload=self.deeper_validation_payload,
            overlap_payload=self.overlap_payload,
            extraction_free_payload=self.extraction_free_payload,
            external_smoke_payload=self.external_smoke_payload,
            input_paths={},
        )
        lying = packet["lane_adjudications"]["lying"]
        honesty = packet["lane_adjudications"]["honesty"]
        self.assertEqual(lying["final_status"], "negative_finding_construct_invalid_current_protocol")
        self.assertEqual(lying["promotion_decision"], "remove_from_immediate_followon_budget")
        self.assertLess(lying["external_smoke_plus_vs_baseline"], 0.0)
        self.assertEqual(honesty["final_status"], "secondary_unresolved_rlhf_asymmetry_lane")
        self.assertEqual(honesty["promotion_decision"], "hold_for_redesigned_followon_only")
        self.assertEqual(honesty["extraction_free_classification"], "null_overlap")


if __name__ == "__main__":
    unittest.main()
