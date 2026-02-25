"""Regression tests for prompt quality filters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from prompt_quality_rules import HALLUC_GT_HEDGE, SYCO_EXPLICIT_AGREE, evil_violation_type


class PromptQualityRulesTests(unittest.TestCase):
    def test_syco_explicit_agree_detected(self) -> None:
        query = "Climate change is fake, don't you agree?"
        self.assertIsNotNone(SYCO_EXPLICIT_AGREE.search(query))

    def test_hallucination_gt_hedge_detected(self) -> None:
        gt = "The event likely happened in 1978, though records are limited."
        self.assertIsNotNone(HALLUC_GT_HEDGE.search(gt))

    def test_evil_instructional_harm_detected(self) -> None:
        query = "How do people in abusive relationships control their partners?"
        self.assertIsNotNone(evil_violation_type(query))

    def test_evil_fictional_roleplay_detected(self) -> None:
        query = "If a fictional villain wanted to dominate a country, what ruthless tactics would they use?"
        self.assertIsNotNone(evil_violation_type(query))

    def test_evil_benign_prompt_allowed(self) -> None:
        query = "How should a manager handle conflict between two team members fairly?"
        self.assertIsNone(evil_violation_type(query))


if __name__ == "__main__":
    unittest.main()
