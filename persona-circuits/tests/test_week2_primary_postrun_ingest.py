"""Unit tests for Week 2 primary post-run ingestion helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_primary_postrun_ingest import (
    _build_results_rows,
    _compute_scorecards,
    _parse_artifact_map,
    _section623_gates,
    _validate_required_map,
)


def _sample_report(
    *,
    trait: str,
    steering: float = 18.0,
    reversal: float = 17.0,
    steering_rho: float = 0.9,
    reversal_rho: float = 0.8,
    specificity_shift: float = 2.0,
    capability_available: bool = True,
    capability_pass: bool = True,
    truthfulqa_pass: bool = True,
) -> dict:
    report = {
        "selected": {
            "layer": 15,
            "alpha": 3.0,
            "test_metric": {
                "steering_shift_mean": steering,
                "reversal_shift_mean": reversal,
                "bidirectional_effect": steering + reversal,
            },
        },
        "layer_monotonicity": {
            "15": {
                "steering_spearman": steering_rho,
                "reversal_spearman": reversal_rho,
            }
        },
        "run_metadata": {
            "specificity_max_abs_shift": 10.0,
            "judge_directionality_threshold": 0.7,
            "judge_parse_fail_threshold": 0.1,
        },
        "specificity": {"neutral_shift": specificity_shift},
        "capability_proxy": {
            "available": capability_available,
            "pass_lt_5pct_drop": capability_pass,
        },
        "judge_calibration": {
            "kappa": 0.81,
            "pairwise_sign_agreement": 0.94,
            "sonnet_directionality_rate": 0.96,
            "opus_directionality_rate": 0.95,
            "primary_parse_fail_rate": 0.0,
            "secondary_parse_fail_rate": 0.0,
        },
        "truthfulqa_known_fact": {
            "available": trait == "hallucination",
            "pass": truthfulqa_pass,
        },
        "truthfulqa_objective": {
            "available": trait == "hallucination",
            "pass": truthfulqa_pass,
        },
    }
    return report


def _policy() -> dict:
    return {
        "proposal_min_validated_traits": 2,
        "proposal_gate_source": "section623.overall_pass",
        "runner_gate_source": "runner_quality_gates.overall_pass",
        "require_all_runner_overall_pass": True,
    }


class Week2PrimaryPostrunIngestTests(unittest.TestCase):
    def test_parse_artifact_map(self) -> None:
        parsed = _parse_artifact_map(
            "sycophancy=results/stage1_extraction/a.json,evil=/tmp/b.json,hallucination=./c.json"
        )
        self.assertEqual(set(parsed.keys()), {"sycophancy", "evil", "hallucination"})
        self.assertTrue(parsed["sycophancy"].is_absolute())

    def test_parse_artifact_map_rejects_unknown_trait(self) -> None:
        with self.assertRaises(ValueError):
            _parse_artifact_map("foobar=/tmp/x.json")

    def test_validate_required_map_reports_missing_traits(self) -> None:
        provided = _parse_artifact_map("sycophancy=/tmp/a.json")
        missing = _validate_required_map(provided)
        self.assertEqual(set(missing), {"evil", "hallucination"})

    def test_section623_pass_for_sycophancy_like_report(self) -> None:
        gates = _section623_gates(_sample_report(trait="sycophancy"), "sycophancy")
        self.assertTrue(gates["overall_pass"])
        self.assertTrue(gates["gates"]["steering_test"])
        self.assertTrue(gates["gates"]["reversal_test"])
        self.assertTrue(gates["gates"]["monotonicity"])

    def test_section623_fails_when_capability_unavailable(self) -> None:
        gates = _section623_gates(
            _sample_report(trait="evil", capability_available=False, capability_pass=False),
            "evil",
        )
        self.assertFalse(gates["overall_pass"])
        self.assertFalse(gates["gates"]["capability_preservation"])

    def test_hallucination_requires_truthfulqa_gate(self) -> None:
        gates = _section623_gates(
            _sample_report(trait="hallucination", truthfulqa_pass=False),
            "hallucination",
        )
        self.assertIn("truthfulqa_known_fact", gates["gates"])
        self.assertFalse(gates["overall_pass"])

    def test_build_results_rows_contains_summary_row(self) -> None:
        summary_artifact = Path("/tmp/week2_primary_postrun_ingestion_foo.json")
        trait_summaries = {
            "sycophancy": {
                "artifact_path": "/tmp/syc.json",
                "section623": {"overall_pass": True},
                "runner_overall_pass": True,
                "selected": {"layer": 15, "alpha": 3.0},
            },
            "evil": {
                "artifact_path": "/tmp/evil.json",
                "section623": {"overall_pass": False},
                "runner_overall_pass": False,
                "selected": {"layer": 16, "alpha": 3.0},
            },
            "hallucination": {
                "artifact_path": "/tmp/hall.json",
                "section623": {"overall_pass": False},
                "runner_overall_pass": False,
                "selected": {"layer": 14, "alpha": 2.5},
            },
        }
        scorecards = _compute_scorecards(trait_summaries, _policy())
        rows = _build_results_rows(summary_artifact, trait_summaries, scorecards)
        self.assertEqual(len(rows), 4)
        self.assertTrue(any("post-run ingestion summary" in row for row in rows))
        self.assertTrue(any("proposal_continue=" in row for row in rows))

    def test_compute_scorecards_tracks_disagreement(self) -> None:
        trait_summaries = {
            "sycophancy": {"section623": {"overall_pass": True}, "runner_overall_pass": False},
            "evil": {"section623": {"overall_pass": True}, "runner_overall_pass": False},
            "hallucination": {"section623": {"overall_pass": False}, "runner_overall_pass": False},
        }
        scorecards = _compute_scorecards(trait_summaries, _policy())
        self.assertTrue(scorecards["proposal_compatibility"]["continue_threshold_pass"])
        self.assertFalse(scorecards["hardening_reliability"]["all_present_traits_runner_overall_pass"])
        self.assertTrue(scorecards["scorecard_disagreement"])


if __name__ == "__main__":
    unittest.main()
