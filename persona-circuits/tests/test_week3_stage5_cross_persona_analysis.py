import json
import tempfile
import unittest
from pathlib import Path

from scripts.week3_stage5_cross_persona_analysis import _jaccard, run_analysis


def _artifact(
    layer: int,
    syc_ids,
    evil_ids,
    *,
    sae_source: str = "primary",
    sae_release: str = "release-a",
):
    def _candidate(ids):
        return [{"feature_id": x} for x in ids]

    return {
        "inputs": {"layer": layer, "sae_source": sae_source, "sae_release": sae_release},
        "results_by_trait": {
            "sycophancy": {
                "direct_projection": {"top_feature_ids": list(syc_ids)},
                "differential_activation": {"top_feature_ids": list(syc_ids)},
                "candidate_union": {"ranked_candidates_topk": _candidate(syc_ids)},
            },
            "evil": {
                "direct_projection": {"top_feature_ids": list(evil_ids)},
                "differential_activation": {"top_feature_ids": list(evil_ids)},
                "candidate_union": {"ranked_candidates_topk": _candidate(evil_ids)},
            },
        },
    }


class Stage5CrossPersonaAnalysisTests(unittest.TestCase):
    def test_jaccard_handles_empty(self):
        self.assertEqual(_jaccard(set(), set()), 0.0)
        self.assertAlmostEqual(_jaccard({1, 2}, {2, 3}), 1.0 / 3.0)

    def test_run_analysis_outputs_expected_gradient_and_router_stub(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            path11 = base / "layer11.json"
            path15 = base / "layer15.json"

            path11.write_text(
                json.dumps(_artifact(11, syc_ids=[1, 2, 3], evil_ids=[2, 3, 4]))
            )
            path15.write_text(
                json.dumps(_artifact(15, syc_ids=[10, 11], evil_ids=[11, 12]))
            )

            result = run_analysis(
                artifact_paths=[path11, path15],
                trait_a="sycophancy",
                trait_b="evil",
                early_layer_max=12,
            )

        candidate_rows = result["layerwise_overlap"]["candidate_union"]
        self.assertEqual([row["layer"] for row in candidate_rows], [11, 15])
        self.assertAlmostEqual(candidate_rows[0]["jaccard"], 2.0 / 4.0)
        self.assertAlmostEqual(candidate_rows[1]["jaccard"], 1.0 / 3.0)

        gradient = result["gradient_summary"]["candidate_union"]
        self.assertTrue(gradient["available"])
        self.assertEqual(gradient["early_layer"], 11)
        self.assertEqual(gradient["late_layer"], 15)
        self.assertGreater(gradient["delta_early_minus_late"], 0.0)

        router_stub = result["router_candidate_stub"]["candidate_union"]
        self.assertTrue(router_stub["available"])
        self.assertEqual(router_stub["layers_used"], [11])
        self.assertEqual(router_stub["candidate_union_count"], 2)
        self.assertEqual(router_stub["candidate_stable_count"], 2)
        self.assertEqual(sorted(router_stub["candidate_union_ids"]), [2, 3])

    def test_mixed_source_comparability_policy_and_source_consistent_gradients(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            p11 = base / "layer11.json"
            p12 = base / "layer12.json"
            p15 = base / "layer15.json"

            p11.write_text(
                json.dumps(
                    _artifact(
                        11,
                        syc_ids=[1, 2, 3],
                        evil_ids=[2, 3, 4],
                        sae_source="cross_check",
                        sae_release="x",
                    )
                )
            )
            p12.write_text(
                json.dumps(
                    _artifact(
                        12,
                        syc_ids=[5, 6, 7],
                        evil_ids=[6, 7, 8],
                        sae_source="primary",
                        sae_release="p",
                    )
                )
            )
            p15.write_text(
                json.dumps(
                    _artifact(
                        15,
                        syc_ids=[9, 10, 11],
                        evil_ids=[10, 11, 12],
                        sae_source="cross_check",
                        sae_release="x",
                    )
                )
            )

            result = run_analysis(
                artifact_paths=[p11, p12, p15],
                trait_a="sycophancy",
                trait_b="evil",
                early_layer_max=12,
                gradient_mode="source_consistent_only",
            )

        policy = result["comparability_policy"]["candidate_union"]
        self.assertTrue(policy["mixed_source_detected"])
        self.assertTrue(policy["source_consistent_gradient_available"])
        source_grad = result["gradient_summary_source_consistent"]["candidate_union"]
        self.assertIn("cross_check|x", source_grad)
        self.assertIn("primary|p", source_grad)
        self.assertTrue(source_grad["cross_check|x"]["available"])
        self.assertFalse(source_grad["primary|p"]["available"])

    def test_router_multiple_testing_hook_applies_bh_fdr(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            p11 = base / "layer11.json"
            p12 = base / "layer12.json"
            p11.write_text(json.dumps(_artifact(11, syc_ids=[1, 2, 3], evil_ids=[2, 3, 4])))
            p12.write_text(json.dumps(_artifact(12, syc_ids=[2, 3, 5], evil_ids=[2, 3, 6])))

            result = run_analysis(
                artifact_paths=[p11, p12],
                trait_a="sycophancy",
                trait_b="evil",
                early_layer_max=12,
                router_pvalues={2: 0.001, 3: 0.02, 4: 0.2},
                router_fdr_alpha=0.05,
            )

        hook = result["router_multiple_testing_hooks"]["candidate_union"]
        self.assertTrue(hook["available"])
        self.assertEqual(hook["method"], "benjamini_hochberg_fdr")
        self.assertEqual(hook["n_tested"], 2)
        self.assertEqual(hook["n_rejected"], 2)
        self.assertEqual(hook["rejected_feature_preview"], [2, 3])


if __name__ == "__main__":
    unittest.main()
