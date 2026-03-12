import unittest

from scripts.week3_stage4_sufficiency_preflight import (
    _parse_dose_response,
    _preserved_effect_fraction,
    build_preflight_report,
)


class SufficiencyPreflightUtilsTests(unittest.TestCase):
    def test_parse_dose_response_validates_bounds(self):
        self.assertEqual(_parse_dose_response("0.25,0.5,1.0"), [0.25, 0.5, 1.0])
        with self.assertRaises(ValueError):
            _parse_dose_response("0.0,0.5")
        with self.assertRaises(ValueError):
            _parse_dose_response("1.2")

    def test_preserved_effect_fraction_handles_low_denominator(self):
        self.assertIsNone(_preserved_effect_fraction(0.0, 0.0))
        self.assertAlmostEqual(_preserved_effect_fraction(10.0, 7.5), 0.75)


class SufficiencyPreflightReportTests(unittest.TestCase):
    def test_build_preflight_report_smoke(self):
        config = {"thresholds": {"sufficiency": 0.6, "random_baseline_samples": 100}}
        target_payload = {
            "targets_by_trait": {
                "sycophancy": {
                    "target_feature_ids": [1, 2, 3],
                    "candidate_pool_size": 10,
                    "prompt_count_used": 50,
                },
                "evil": {
                    "target_feature_ids": [4, 5, 6],
                    "candidate_pool_size": 12,
                    "prompt_count_used": 50,
                },
            }
        }
        ingestion_payload = {
            "traits": {
                "sycophancy": {
                    "selected": {"layer": 12, "alpha": 3.0, "test_bidirectional_effect": 60.0}
                },
                "evil": {
                    "selected": {"layer": 12, "alpha": 3.0, "test_bidirectional_effect": 65.0}
                },
            }
        }
        report = build_preflight_report(
            config=config,
            target_payload=target_payload,
            ingestion_payload=ingestion_payload,
            traits=["sycophancy", "evil"],
            methods=["resample", "mean"],
            dose_response=[0.25, 0.5, 0.75, 1.0],
            heldout_counts={"sycophancy": 50, "evil": 50},
            heldout_prompts_per_trait=30,
            seed=42,
        )

        self.assertEqual(report["artifact_type"], "week3_stage4_sufficiency_preflight")
        self.assertTrue(report["target_set_validation"]["top_k_consistent"])
        self.assertTrue(report["heldout_availability"]["heldout_ready_for_requested_prompts"])
        self.assertEqual(report["condition_matrix"]["rows_per_trait"], 10)
        self.assertEqual(report["condition_matrix"]["n_rows_total"], 20)
        self.assertFalse(report["readiness"]["launch_recommended_now"])
        self.assertTrue(report["readiness"]["dryrun_path_exercised"])
        self.assertIn(
            "remote_circuit_only_execution_not_run_dryrun_only",
            report["readiness"]["blocking_items"],
        )


if __name__ == "__main__":
    unittest.main()
