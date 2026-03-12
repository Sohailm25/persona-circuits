import unittest

from scripts.week3_stage5_policy_decision_packet import (
    _recommendation,
    _s5g2_status,
    _s5g4_status,
)


class Stage5PolicyDecisionPacketTests(unittest.TestCase):
    def test_s5g2_pass_with_limitation_on_mixed_source_with_source_consistency(self):
        stage5 = {
            "comparability_policy": {
                "candidate_union": {
                    "mixed_source_detected": True,
                    "source_consistent_gradient_available": True,
                    "cross_layer_gradient_interpretation": "limited_mixed_source",
                }
            }
        }
        status = _s5g2_status(stage5)
        self.assertEqual(status["status"], "pass_with_limitation")

    def test_s5g4_exploratory_null_when_no_rejections(self):
        stage5 = {
            "router_multiple_testing_hooks": {
                "candidate_union": {
                    "available": True,
                    "n_tested": 62,
                    "n_rejected": 0,
                    "fdr_alpha": 0.01,
                    "min_q_value": 0.0465,
                }
            }
        }
        status = _s5g4_status(stage5)
        self.assertEqual(status["status"], "exploratory_null")
        self.assertEqual(status["n_tested"], 62)

    def test_recommendation_blocks_when_any_gate_fails(self):
        rec = _recommendation(
            {"status": "fail"},
            {"status": "exploratory_null"},
        )
        self.assertEqual(rec["policy_decision"], "blocked_pending_remediation")
        self.assertFalse(rec["launch_recommended_now"])

    def test_recommendation_locks_exploratory_null_when_gates_closed_without_signal(self):
        rec = _recommendation(
            {"status": "pass_with_limitation"},
            {"status": "exploratory_null"},
        )
        self.assertEqual(
            rec["policy_decision"], "lock_exploratory_null_with_optional_sensitivity_lane"
        )
        self.assertFalse(rec["launch_recommended_now"])


if __name__ == "__main__":
    unittest.main()
