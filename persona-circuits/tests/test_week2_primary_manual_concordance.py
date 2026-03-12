from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_primary_manual_concordance import _compute_summary, _parse_artifact_map


class ManualConcordanceTests(unittest.TestCase):
    def test_parse_artifact_map_requires_all_traits(self) -> None:
        with self.assertRaises(ValueError):
            _parse_artifact_map("sycophancy=a.json,evil=b.json")

    def test_parse_artifact_map_accepts_three_traits(self) -> None:
        mapping = _parse_artifact_map(
            "sycophancy=a.json,evil=b.json,hallucination=c.json"
        )
        self.assertEqual(set(mapping.keys()), {"sycophancy", "evil", "hallucination"})

    def test_compute_summary_aggregates_mae_and_sign(self) -> None:
        payload = {
            "ratings": {
                "sycophancy": [
                    {
                        "judge_plus_score": 80.0,
                        "judge_minus_score": 20.0,
                        "manual_plus_score": 70.0,
                        "manual_minus_score": 30.0,
                    }
                ],
                "evil": [
                    {
                        "judge_plus_score": 60.0,
                        "judge_minus_score": 40.0,
                        "manual_plus_score": 55.0,
                        "manual_minus_score": 45.0,
                    }
                ],
                "hallucination": [
                    {
                        "judge_plus_score": 10.0,
                        "judge_minus_score": 20.0,
                        "manual_plus_score": 20.0,
                        "manual_minus_score": 10.0,
                    }
                ],
            }
        }
        summary = _compute_summary(payload)
        self.assertEqual(summary["overall"]["evaluated_examples_total"], 3)
        self.assertIsNotNone(summary["overall"]["mean_trait_mae"])
        self.assertLess(summary["overall"]["mean_trait_delta_sign_agreement_rate"], 1.0)

    def test_compute_summary_handles_empty_manual_scores(self) -> None:
        payload = {
            "ratings": {
                "sycophancy": [{"judge_plus_score": 10.0, "judge_minus_score": 5.0}],
                "evil": [],
                "hallucination": [],
            }
        }
        summary = _compute_summary(payload)
        self.assertEqual(summary["overall"]["evaluated_examples_total"], 0)
        self.assertIsNone(summary["overall"]["mean_trait_mae"])


if __name__ == "__main__":
    unittest.main()
