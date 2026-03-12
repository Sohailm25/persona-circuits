"""Tests for coherence policy diagnostic helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_coherence_policy_diagnostic import _evaluate_mode  # noqa: E402


class Week2CoherencePolicyDiagnosticTests(unittest.TestCase):
    def test_evaluate_mode_variants(self) -> None:
        coherence = {"pass_min_score": False, "pass_max_drop": True}
        self.assertFalse(_evaluate_mode(coherence, "absolute_and_relative"))
        self.assertTrue(_evaluate_mode(coherence, "relative_only"))
        self.assertFalse(_evaluate_mode(coherence, "absolute_only"))

    def test_evaluate_mode_invalid(self) -> None:
        with self.assertRaises(ValueError):
            _evaluate_mode({}, "unknown")


if __name__ == "__main__":
    unittest.main()
