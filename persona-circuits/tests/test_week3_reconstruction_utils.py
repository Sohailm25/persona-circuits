"""Unit tests for Week 3 reconstruction seed-schedule and summary helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week3_sae_reconstruction_investigation import (
    _aggregate_seed_reports as aggregate_investigation_reports,
)
from week3_sae_reconstruction_investigation import _resolve_seed_schedule as resolve_investigation_seeds
from week3_sae_reconstruction_root_cause import (
    _aggregate_seed_reports as aggregate_root_cause_reports,
)
from week3_sae_reconstruction_root_cause import _resolve_seed_schedule as resolve_root_cause_seeds


class Week3ReconstructionUtilsTests(unittest.TestCase):
    def test_resolve_seed_schedule_uses_config_primary_and_replication(self) -> None:
        cfg = {"seeds": {"primary": 42, "replication": [123, 456, 789]}}
        self.assertEqual(resolve_investigation_seeds(cfg, seed=-1, seed_schedule=""), [42, 123, 456, 789])
        self.assertEqual(resolve_root_cause_seeds(cfg, seed=-1, seed_schedule=""), [42, 123, 456, 789])

    def test_resolve_seed_schedule_prefers_csv_override(self) -> None:
        cfg = {"seeds": {"primary": 42, "replication": [123, 456, 789]}}
        self.assertEqual(resolve_investigation_seeds(cfg, seed=-1, seed_schedule="7,8,7"), [7, 8])
        self.assertEqual(resolve_root_cause_seeds(cfg, seed=-1, seed_schedule="9,10,9"), [9, 10])

    def test_aggregate_investigation_reports_detects_consistency(self) -> None:
        reports = {
            "42": {
                "interpretation": {
                    "status_by_model": {"m1": "warning", "m2": "fail"},
                    "base_minus_instruct_median_reconstruction_cosine": 0.02,
                }
            },
            "123": {
                "interpretation": {
                    "status_by_model": {"m1": "warning", "m2": "fail"},
                    "base_minus_instruct_median_reconstruction_cosine": 0.01,
                }
            },
        }
        out = aggregate_investigation_reports(reports)
        self.assertTrue(out["status_consistency_by_model"]["m1"]["fully_consistent"])
        self.assertEqual(out["base_minus_instruct_median_cosine_summary"]["n"], 2)

    def test_aggregate_root_cause_reports_detects_best_variant_consistency(self) -> None:
        reports = {
            "42": {
                "model_results": {
                    "m1": {
                        "best_variant_by_median_cosine": "hook::last_token",
                        "best_variant_median_cosine": 0.8,
                    }
                }
            },
            "123": {
                "model_results": {
                    "m1": {
                        "best_variant_by_median_cosine": "hook::last_token",
                        "best_variant_median_cosine": 0.79,
                    }
                }
            },
        }
        out = aggregate_root_cause_reports(reports)
        self.assertTrue(out["m1"]["best_variant_consistent"])
        self.assertEqual(out["m1"]["best_variant_median_cosine_summary"]["n"], 2)


if __name__ == "__main__":
    unittest.main()
