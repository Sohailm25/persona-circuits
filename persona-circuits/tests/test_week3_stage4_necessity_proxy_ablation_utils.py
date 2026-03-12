"""Unit tests for Stage4 necessity proxy helper utilities."""

from __future__ import annotations

import unittest

import numpy as np
import torch

from scripts.week3_stage4_necessity_proxy_ablation import (
    _apply_feature_ablation,
    _a12,
    _cohens_d,
    _parse_traits,
    _random_baseline_selectivity,
    _reduction_fraction,
    _sample_random_feature_sets,
)


class ParseTraitsTests(unittest.TestCase):
    def test_parse_traits_success(self) -> None:
        self.assertEqual(_parse_traits("sycophancy,evil"), ["sycophancy", "evil"])

    def test_parse_traits_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            _parse_traits(" ")


class ReductionTests(unittest.TestCase):
    def test_reduction_fraction_expected(self) -> None:
        self.assertAlmostEqual(_reduction_fraction(1.0, 0.25), 0.75)

    def test_reduction_fraction_handles_zero_baseline(self) -> None:
        self.assertAlmostEqual(_reduction_fraction(0.0, 0.0), 0.0)


class AblationSemanticsTests(unittest.TestCase):
    def test_apply_feature_ablation_zero(self) -> None:
        high = torch.tensor([1.0, 2.0, 3.0, 4.0])
        donor = torch.tensor([10.0, 20.0, 30.0, 40.0])
        mean = torch.tensor([0.5, 0.5, 0.5, 0.5])
        out = _apply_feature_ablation(
            high,
            donor_vec=donor,
            mean_vec=mean,
            feature_ids=np.asarray([1, 3]),
            method="zero",
        )
        self.assertListEqual(out.tolist(), [1.0, 0.0, 3.0, 0.0])

    def test_apply_feature_ablation_mean_and_resample(self) -> None:
        high = torch.tensor([1.0, 2.0, 3.0, 4.0])
        donor = torch.tensor([10.0, 20.0, 30.0, 40.0])
        mean = torch.tensor([0.5, 0.6, 0.7, 0.8])
        out_mean = _apply_feature_ablation(
            high,
            donor_vec=donor,
            mean_vec=mean,
            feature_ids=np.asarray([0, 2]),
            method="mean",
        )
        self.assertAlmostEqual(float(out_mean[0]), 0.5, places=6)
        self.assertAlmostEqual(float(out_mean[1]), 2.0, places=6)
        self.assertAlmostEqual(float(out_mean[2]), 0.7, places=6)
        self.assertAlmostEqual(float(out_mean[3]), 4.0, places=6)
        out_resample = _apply_feature_ablation(
            high,
            donor_vec=donor,
            mean_vec=mean,
            feature_ids=np.asarray([0, 2]),
            method="resample",
        )
        self.assertListEqual(out_resample.tolist(), [10.0, 2.0, 30.0, 4.0])


class RandomSetTests(unittest.TestCase):
    def test_sample_random_feature_sets_excludes_targets(self) -> None:
        draws = _sample_random_feature_sets(
            d_sae=20,
            exclude_ids=[1, 2, 3],
            set_size=4,
            n_sets=6,
            seed=42,
        )
        self.assertEqual(draws.shape, (6, 4))
        self.assertTrue(np.all(~np.isin(draws, np.asarray([1, 2, 3]))))

    def test_sample_random_feature_sets_rejects_oversize(self) -> None:
        with self.assertRaises(ValueError):
            _sample_random_feature_sets(
                d_sae=5,
                exclude_ids=[0, 1, 2],
                set_size=3,
                n_sets=2,
                seed=0,
            )


class MetricTests(unittest.TestCase):
    def test_cohens_d_and_a12_direction(self) -> None:
        a = np.asarray([0.8, 0.9, 1.0, 0.95])
        b = np.asarray([0.1, 0.2, 0.3, 0.25])
        self.assertGreater(_cohens_d(a, b), 0.0)
        self.assertGreater(_a12(a, b), 0.5)

    def test_random_baseline_selectivity(self) -> None:
        summary = _random_baseline_selectivity(
            observed_effect=0.8,
            random_effects=np.asarray([0.1, 0.2, 0.3, 0.4]),
        )
        self.assertEqual(summary["n_random"], 4)
        self.assertTrue(summary["percentile_rank"] >= 0.99)


if __name__ == "__main__":
    unittest.main()
