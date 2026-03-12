"""Unit tests for the Week 3 GLP meta-neuron screen helpers."""

from __future__ import annotations

import unittest

import numpy as np

from scripts.week3_glp_meta_neuron_screen import (
    _build_capture_targets,
    _build_cross_trait_overlap,
    _rank_meta_neurons,
    _resolve_capture_sites,
    _resolve_u_values,
)


class Week3GLPMetaNeuronScreenTests(unittest.TestCase):
    def test_resolve_u_values_and_capture_sites(self) -> None:
        self.assertEqual(_resolve_u_values("0.3,0.5,0.5", None), [0.3, 0.5])
        sites = _resolve_capture_sites(
            [
                {
                    "label": "down_proj_input",
                    "layer_prefix": "denoiser.model.layers.{i}.down_proj",
                    "location": "input",
                }
            ]
        )
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites[0]["location"], "input")

    def test_build_capture_targets(self) -> None:
        targets = _build_capture_targets(
            2,
            [
                {
                    "label": "down_proj_input",
                    "layer_prefix": "denoiser.model.layers.{i}.down_proj",
                    "location": "input",
                }
            ],
        )
        self.assertEqual(len(targets), 2)
        self.assertEqual(targets[0]["layer_name"], "denoiser.model.layers.0.down_proj")
        self.assertEqual(targets[1]["denoiser_layer"], 1)

    def test_rank_meta_neurons(self) -> None:
        capture_targets = _build_capture_targets(
            2,
            [
                {
                    "label": "down_proj_input",
                    "layer_prefix": "denoiser.model.layers.{i}.down_proj",
                    "location": "input",
                }
            ],
        )
        meta = np.zeros((4, 2, 2, 3), dtype=np.float64)
        labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
        meta[2:, 1, 0, 2] = 5.0
        meta[2:, 0, 1, 1] = 3.0
        ranked = _rank_meta_neurons(
            meta_features=meta,
            labels=labels,
            capture_targets=capture_targets,
            u_values=[0.3, 0.7],
            top_k=2,
        )
        self.assertEqual(len(ranked["top_meta_neurons"]), 2)
        self.assertEqual(ranked["top_meta_neurons"][0]["u_index"], 1)
        self.assertEqual(ranked["top_meta_neurons"][0]["capture_target_index"], 0)
        self.assertEqual(ranked["top_meta_neurons"][0]["neuron_dim"], 2)
        self.assertEqual(ranked["concentration_by_u"][0]["u_index"], 1)
        self.assertEqual(ranked["concentration_by_capture_target"][0]["capture_target_index"], 0)

    def test_build_cross_trait_overlap(self) -> None:
        overlap = _build_cross_trait_overlap(
            {
                "sycophancy": {"top_feature_identifiers": ["u0:c0:d1", "u1:c0:d2"]},
                "evil": {"top_feature_identifiers": ["u1:c0:d2", "u1:c1:d0"]},
            }
        )
        pair = overlap["pairwise_top_feature_overlap"]["evil__sycophancy"] if "evil__sycophancy" in overlap["pairwise_top_feature_overlap"] else overlap["pairwise_top_feature_overlap"]["sycophancy__evil"]
        self.assertEqual(pair["shared_feature_count"], 1)
        self.assertAlmostEqual(pair["jaccard"], 1.0 / 3.0)


if __name__ == "__main__":
    unittest.main()
