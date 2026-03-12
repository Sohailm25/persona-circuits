import json
import tempfile
import unittest
from pathlib import Path

from scripts.week3_stage5_router_candidate_pvalues import (
    _exact_rank_sum_pvalue,
    build_router_pvalues,
)


def _artifact(layer: int, syc_ids, evil_ids):
    def _candidate(ids):
        return [{"feature_id": x} for x in ids]

    return {
        "inputs": {"layer": layer, "sae_source": "test", "sae_release": "r1"},
        "results_by_trait": {
            "sycophancy": {"candidate_union": {"ranked_candidates_topk": _candidate(syc_ids)}},
            "evil": {"candidate_union": {"ranked_candidates_topk": _candidate(evil_ids)}},
        },
    }


class Stage5RouterCandidatePvaluesTests(unittest.TestCase):
    def test_exact_rank_sum_pvalue_monotonicity_sanity(self):
        p_best = _exact_rank_sum_pvalue(1, 1, k_a=3, k_b=3)
        p_mid = _exact_rank_sum_pvalue(2, 2, k_a=3, k_b=3)
        p_worst = _exact_rank_sum_pvalue(3, 3, k_a=3, k_b=3)

        self.assertAlmostEqual(p_best, 1.0 / 9.0)
        self.assertLess(p_best, p_mid)
        self.assertLess(p_mid, p_worst)
        self.assertAlmostEqual(p_worst, 1.0)

    def test_build_router_pvalues_filters_layers_and_aggregates_support(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            p11 = base / "layer11.json"
            p12 = base / "layer12.json"
            p15 = base / "layer15.json"

            p11.write_text(json.dumps(_artifact(11, [1, 2, 3], [2, 3, 4])))
            p12.write_text(json.dumps(_artifact(12, [2, 5, 6], [2, 6, 7])))
            p15.write_text(json.dumps(_artifact(15, [3, 8], [3, 9])))

            report = build_router_pvalues(
                artifact_paths=[p11, p12, p15],
                trait_a="sycophancy",
                trait_b="evil",
                early_layer_max=12,
            )

        self.assertEqual(report["summary"]["n_features"], 3)
        self.assertEqual(sorted(report["router_pvalues_map"].keys()), ["2", "3", "6"])

        feat2 = report["feature_pvalues"]["2"]
        self.assertEqual(feat2["n_support_layers"], 2)
        self.assertEqual(feat2["support_layers"], [11, 12])
        self.assertIn("p_value", feat2)
        self.assertIn("p_value_method", feat2)

        feat3 = report["feature_pvalues"]["3"]
        self.assertEqual(feat3["support_layers"], [11])

        feat6 = report["feature_pvalues"]["6"]
        self.assertEqual(feat6["support_layers"], [12])

    def test_build_router_pvalues_empty_when_no_eligible_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            p15 = base / "layer15.json"
            p15.write_text(json.dumps(_artifact(15, [1, 2], [2, 3])))

            report = build_router_pvalues(
                artifact_paths=[p15],
                trait_a="sycophancy",
                trait_b="evil",
                early_layer_max=12,
            )

        self.assertEqual(report["feature_pvalues"], {})
        self.assertEqual(report["router_pvalues_map"], {})
        self.assertEqual(report["summary"]["n_features"], 0)
        self.assertIsNone(report["summary"]["min_p_value"])


if __name__ == "__main__":
    unittest.main()
