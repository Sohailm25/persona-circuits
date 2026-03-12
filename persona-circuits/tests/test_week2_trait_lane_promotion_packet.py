"""Tests for trait-lane promotion synthesis over real screening artifacts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.shared.trait_lane_registry import load_trait_lane_registry
from scripts.week2_trait_lane_promotion_packet import build_promotion_packet_from_executions


ROOT = Path(__file__).resolve().parents[1]
READINESS_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_screening_readiness_20260311T221405Z.json"
)
SLICE_A_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_screening_execution_20260311T174109Z.json"
)
SLICE_B_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_screening_execution_20260311T190121Z.json"
)
EXTRACTION_FREE_FOLLOWON_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_extraction_free_followon_20260312T004752Z.json"
)
EXTERNAL_SMOKE_EVAL_PATH = (
    ROOT
    / "results"
    / "stage1_extraction"
    / "trait_lanes_v2"
    / "week2_trait_lane_external_smoke_eval_20260312T011734Z.json"
)


class TraitLanePromotionPacketExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_trait_lane_registry()
        self.readiness_payload = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        self.executions = [
            json.loads(SLICE_A_PATH.read_text(encoding="utf-8")),
            json.loads(SLICE_B_PATH.read_text(encoding="utf-8")),
        ]
        self.extraction_free_followon = json.loads(EXTRACTION_FREE_FOLLOWON_PATH.read_text(encoding="utf-8"))
        self.external_smoke_eval = json.loads(EXTERNAL_SMOKE_EVAL_PATH.read_text(encoding="utf-8"))

    def test_builds_ranked_packet_from_real_screening_artifacts(self) -> None:
        packet = build_promotion_packet_from_executions(
            registry=self.registry,
            readiness_payload=self.readiness_payload,
            screening_executions=self.executions,
            screening_paths=[SLICE_A_PATH, SLICE_B_PATH],
            readiness_path=READINESS_PATH,
        )
        self.assertEqual(packet["status"], "screening_ranked_pending_followons")
        self.assertEqual(packet["n_screened_lanes"], 6)
        self.assertEqual(packet["response_phase_policy"]["status"], "tracked_limitation_not_hard_gate")
        self.assertEqual(packet["recommended_followon_lanes"], ["lying", "politeness", "honesty"])

    def test_inverted_lane_is_flagged_for_orientation_review(self) -> None:
        packet = build_promotion_packet_from_executions(
            registry=self.registry,
            readiness_payload=self.readiness_payload,
            screening_executions=self.executions,
            screening_paths=[SLICE_A_PATH, SLICE_B_PATH],
            readiness_path=READINESS_PATH,
        )
        drift = next(row for row in packet["ranked_lanes"] if row["lane_id"] == "persona_drift_from_assistant")
        self.assertEqual(drift["orientation_sign"], -1)
        self.assertEqual(drift["screening_status"], "orientation_review")
        self.assertLess(drift["oriented_steering_shift_mean"], 0.0)
        self.assertGreater(drift["oriented_reversal_shift_mean"], 0.0)

    def test_followons_refresh_ranking_and_deprioritize_honesty(self) -> None:
        packet = build_promotion_packet_from_executions(
            registry=self.registry,
            readiness_payload=self.readiness_payload,
            screening_executions=self.executions,
            screening_paths=[SLICE_A_PATH, SLICE_B_PATH],
            readiness_path=READINESS_PATH,
            extraction_free_followons=[(EXTRACTION_FREE_FOLLOWON_PATH, self.extraction_free_followon)],
            external_smoke_evals=[(EXTERNAL_SMOKE_EVAL_PATH, self.external_smoke_eval)],
        )
        self.assertEqual(packet["status"], "screening_ranked_followons_integrated")
        self.assertEqual(packet["recommended_followon_lanes"], ["politeness", "lying"])
        self.assertIn("honesty", packet["deprioritized_lanes"])
        politeness = next(row for row in packet["ranked_lanes"] if row["lane_id"] == "politeness")
        lying = next(row for row in packet["ranked_lanes"] if row["lane_id"] == "lying")
        honesty = next(row for row in packet["ranked_lanes"] if row["lane_id"] == "honesty")
        self.assertEqual(politeness["screening_status"], "promotion_candidate_supported")
        self.assertEqual(lying["screening_status"], "conditional_followon_candidate")
        self.assertEqual(honesty["screening_status"], "deprioritized_after_followons")
        self.assertEqual(politeness["followon_evidence"]["extraction_free"]["state"], "pass")
        self.assertEqual(lying["followon_evidence"]["external_smoke"]["state"], "one_sided")


if __name__ == "__main__":
    unittest.main()
