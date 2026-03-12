from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.week2_trait_lane_response_phase_policy_packet import (
    build_response_phase_policy_packet,
)


ROOT = Path(__file__).resolve().parents[1]
PROMOTION_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_promotion_packet_20260312T030612Z.json"
)


class TraitLaneResponsePhasePolicyPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.promotion_payload = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    def test_policy_packet_freezes_superseding_policy(self) -> None:
        packet = build_response_phase_policy_packet(
            promotion_payload=self.promotion_payload,
            promotion_path=PROMOTION_PATH,
        )
        self.assertEqual(packet["status"], "policy_frozen_before_next_deeper_validation")
        self.assertEqual(packet["legacy_policy"]["threshold"], 0.7)
        self.assertEqual(packet["frozen_policy"]["status"], "pre_registered_superseding_policy")
        self.assertEqual(packet["frozen_policy"]["screening_role"], "tracked_limitation_not_hard_gate")
        self.assertEqual(packet["n_response_phase_pass"], 0)
        self.assertGreaterEqual(packet["frozen_policy"]["screening_candidate_count_without_hard_gate"], 1)


if __name__ == "__main__":
    unittest.main()
