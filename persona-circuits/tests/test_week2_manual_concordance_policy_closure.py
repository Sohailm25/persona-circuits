from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_manual_concordance_policy_closure import (  # noqa: E402
    _count_sign_matches,
    _wilson_interval,
)


class Week2ManualConcordancePolicyClosureTests(unittest.TestCase):
    def test_wilson_interval_bounds_are_valid(self) -> None:
        lo, hi = _wilson_interval(3, 5)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)
        self.assertLessEqual(lo, hi)

    def test_count_sign_matches_skips_missing_rows(self) -> None:
        rows = [
            {"judge_plus_score": 80, "judge_minus_score": 20, "manual_plus_score": 75, "manual_minus_score": 25},
            {"judge_plus_score": 20, "judge_minus_score": 80, "manual_plus_score": 10, "manual_minus_score": 90},
            {"judge_plus_score": None, "judge_minus_score": 80, "manual_plus_score": 10, "manual_minus_score": 90},
        ]
        successes, n = _count_sign_matches(rows)
        self.assertEqual(n, 2)
        self.assertEqual(successes, 2)


if __name__ == "__main__":
    unittest.main()
