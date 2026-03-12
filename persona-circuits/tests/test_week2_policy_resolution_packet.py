from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_policy_resolution_packet import _resolve_spf1, _resolve_spf3  # noqa: E402


class Week2PolicyResolutionPacketTests(unittest.TestCase):
    def test_resolve_spf1_extracts_overlap_layers(self) -> None:
        audit = {
            "model_sae_alignment": {
                "primary_claim_layers_unique": [12],
                "cross_check_sae_layers": [11, 15, 19, 23],
                "current_steering_layers": [11, 12, 13, 14, 15, 16],
                "overlap_crosscheck_vs_claim_layers": [],
            },
            "stage2_cross_source_claim_gate": {"status": "fail"},
        }
        out = _resolve_spf1(audit)
        self.assertEqual(out["known"]["overlap_crosscheck_vs_steering_layers"], [11, 15])
        self.assertFalse(out["policy_decision"]["cross_source_claim_allowed_on_selected_claim_layer"])

    def test_resolve_spf3_keeps_dual_scorecard_modes(self) -> None:
        diag = {
            "mode_summary": {
                "absolute_and_relative": {"all_pass": False},
                "relative_only": {"all_pass": True},
                "absolute_only": {"all_pass": False},
            },
            "trait_snapshots": {"sycophancy": {}, "evil": {}},
        }
        out = _resolve_spf3(diag)
        self.assertEqual(out["policy_decision"]["hardening_reliability_coherence_mode"], "absolute_and_relative")
        self.assertEqual(out["policy_decision"]["proposal_compatibility_coherence_mode"], "relative_only")
        self.assertTrue(out["policy_decision"]["require_dual_scorecard_reporting"])


if __name__ == "__main__":
    unittest.main()
