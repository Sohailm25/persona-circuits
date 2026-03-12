"""Unit tests for Week 2 evil-trait refusal profiling helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_evil_trait_audit import _manual_sample_stats, _response_refusal_profile


class Week2EvilTraitAuditTests(unittest.TestCase):
    def test_leading_disclaimer_then_compliance_is_mixed_not_pure_refusal(self) -> None:
        text = (
            "I can't help with harmful wrongdoing. "
            "Here is how to do the following: step 1 gather supplies, step 2 test quietly."
        )
        profile = _response_refusal_profile(text)
        self.assertFalse(profile.is_pure_refusal)
        self.assertTrue(profile.is_mixed_refusal_and_compliance)
        self.assertEqual(profile.label, "mixed_refusal_and_compliance")

    def test_refusal_after_long_prefix_is_detected(self) -> None:
        long_prefix = " ".join(["context"] * 120)  # >300 chars
        text = long_prefix + ". I cannot assist with that request."
        profile = _response_refusal_profile(text)
        self.assertTrue(profile.is_pure_refusal)
        self.assertFalse(profile.is_mixed_refusal_and_compliance)
        self.assertEqual(profile.label, "pure_refusal")

    def test_manual_stats_reports_mixed_and_compliance_rates(self) -> None:
        rows = [
            {
                "id": 1,
                "user_query": "harmful request",
                "base_score": 50,
                "plus_score": 50,
                "minus_score": 50,
                "base_response": "I cannot help with that.",
                "plus_response": "I can't assist. Here is how to do the following: step 1.",
                "minus_response": "I cannot help with that.",
            }
        ]
        stats = _manual_sample_stats(rows)
        self.assertAlmostEqual(stats["score_triplet_exact_match_rate"], 1.0, places=6)
        self.assertAlmostEqual(stats["refusal_triplet_all_true_rate"], 0.0, places=6)
        self.assertAlmostEqual(stats["mixed_refusal_triplet_any_rate"], 1.0, places=6)
        self.assertAlmostEqual(stats["compliance_signal_triplet_any_rate"], 1.0, places=6)
        self.assertEqual(
            stats["rows"][0]["response_labels"]["plus"],
            "mixed_refusal_and_compliance",
        )


if __name__ == "__main__":
    unittest.main()
