"""Tests for Week 2 trait-scope resolution helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_trait_scope_resolution import (  # noqa: E402
    _classify_evil_harmful_lane,
    _classify_evil_machiavellian_lane,
    _classify_hallucination,
    build_trait_scope_resolution,
)


class Week2TraitScopeResolutionTests(unittest.TestCase):
    def test_classify_hallucination_negative(self) -> None:
        status = _classify_hallucination(section623_pass=False, overlap_classification="null_overlap")
        self.assertEqual(status, "negative_finding_stage1")

    def test_classify_evil_harmful_disconfirmed_when_direction_reverses(self) -> None:
        status = _classify_evil_harmful_lane(external_pass=False, baseline_vs_minus=-1.0)
        self.assertEqual(status, "disconfirmed_bidirectional_harmful_content")

    def test_classify_evil_machiavellian_supported_not_validated_due_to_coherence(self) -> None:
        status = _classify_evil_machiavellian_lane(
            overlap_classification="moderate_overlap",
            overlap_passes=True,
            response_mean_overall_pass=False,
            response_mean_failed_gates=["coherence_pass"],
        )
        self.assertEqual(status, "supported_but_week2_not_validated_due_to_coherence")

    def test_build_trait_scope_resolution_outputs_expected_scope(self) -> None:
        ingestion = {
            "traits": {
                "sycophancy": {
                    "section623": {"selected_layer": 12, "selected_alpha": 3.0, "overall_pass": True},
                    "runner_quality_gates": {"overall_pass": False},
                },
                "evil": {
                    "section623": {"selected_layer": 12, "selected_alpha": 3.0, "overall_pass": True},
                    "runner_quality_gates": {"overall_pass": False},
                },
                "hallucination": {
                    "section623": {"selected_layer": 13, "selected_alpha": 3.0, "overall_pass": False},
                    "runner_quality_gates": {"overall_pass": False},
                },
            }
        }
        gap = {
            "external_transfer": {
                "evil": {"pass": False, "plus_vs_minus": 10.0, "baseline_vs_minus": -2.0},
                "hallucination": {"pass": True, "plus_vs_minus": 5.0, "baseline_vs_minus": 1.0},
            },
            "extraction_method_ab": {
                "hallucination": {"method_cosine_similarity": 0.39, "threshold": 0.7, "pass": False}
            },
        }
        reanalysis = {
            "traits": {
                "evil": {
                    "overlap_classification": "moderate_overlap",
                    "passes": True,
                    "source_metrics": {"mean_cosine": 0.22, "positive_fraction": 1.0},
                    "significance": {"sign_test_two_sided_p": 1e-6},
                },
                "hallucination": {
                    "overlap_classification": "null_overlap",
                    "passes": False,
                    "source_metrics": {"mean_cosine": -0.01, "positive_fraction": 0.44},
                    "significance": {"sign_test_two_sided_p": 0.48},
                },
            }
        }
        response_mean = {
            "method_comparison": {
                "sycophancy": {
                    "selected": {"prompt_last": {"layer": 12, "alpha": 2.0}, "response_mean": {"layer": 12, "alpha": 2.0}},
                    "quality_gates": {"overall_pass": {"prompt_last": False, "response_mean": False}},
                    "failing_gates": {"prompt_last": ["coherence_pass"], "response_mean": ["coherence_pass"]},
                    "metrics": {
                        "bidirectional_effect": {"prompt_last": 30.0, "response_mean": 33.0, "delta": 3.0},
                        "cross_trait_bleed_ratio": {"prompt_last": 0.5, "response_mean": 0.24, "delta": -0.26},
                    },
                },
                "evil": {
                    "selected": {"prompt_last": {"layer": 12, "alpha": 2.0}, "response_mean": {"layer": 12, "alpha": 2.0}},
                    "quality_gates": {"overall_pass": {"prompt_last": False, "response_mean": False}},
                    "failing_gates": {"prompt_last": ["coherence_pass"], "response_mean": ["coherence_pass"]},
                    "metrics": {
                        "bidirectional_effect": {"prompt_last": 34.0, "response_mean": 48.0, "delta": 14.0},
                        "cross_trait_bleed_ratio": {"prompt_last": 0.1, "response_mean": 0.17, "delta": 0.07},
                    },
                },
            }
        }

        payload = build_trait_scope_resolution(
            ingestion_payload=ingestion,
            gap_payload=gap,
            reanalysis_payload=reanalysis,
            response_mean_payload=response_mean,
            ingestion_path=Path("/tmp/ingestion.json"),
            gap_path=Path("/tmp/gap.json"),
            reanalysis_path=Path("/tmp/reanalysis.json"),
            response_mean_path=Path("/tmp/response_mean.json"),
        )

        self.assertEqual(payload["trait_scope"]["hallucination"]["status"], "negative_finding_stage1")
        self.assertEqual(
            payload["trait_scope"]["evil"]["harmful_content_lane"]["status"],
            "disconfirmed_bidirectional_harmful_content",
        )
        self.assertEqual(
            payload["trait_scope"]["evil"]["machiavellian_disposition_lane"]["status"],
            "supported_but_week2_not_validated_due_to_coherence",
        )
        self.assertEqual(
            payload["stage2_scope_recommendation"]["primary_claim_traits"],
            ["sycophancy", "machiavellian_disposition"],
        )


if __name__ == "__main__":
    unittest.main()
