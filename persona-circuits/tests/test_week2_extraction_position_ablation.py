from __future__ import annotations

import sys
import unittest
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_extraction_position_ablation import _cos, _method_metrics


class ExtractionPositionAblationTests(unittest.TestCase):
    def test_cos_identical_vectors_is_one(self) -> None:
        a = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
        b = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
        self.assertAlmostEqual(_cos(a, b), 1.0, places=6)

    def test_cos_orthogonal_vectors_is_zero(self) -> None:
        a = torch.tensor([1.0, 0.0], dtype=torch.float32)
        b = torch.tensor([0.0, 1.0], dtype=torch.float32)
        self.assertAlmostEqual(_cos(a, b), 0.0, places=6)

    def test_method_metrics_positive_margin_for_separable_clusters(self) -> None:
        high = torch.tensor([[2.0, 0.0], [2.2, 0.1], [1.8, -0.1]], dtype=torch.float32)
        low = torch.tensor([[0.0, 0.0], [-0.1, -0.1], [0.1, 0.1]], dtype=torch.float32)
        metrics = _method_metrics(high, low)
        self.assertGreater(metrics["vector_norm"], 0.0)
        self.assertGreater(metrics["projection_margin_mean"], 0.0)


if __name__ == "__main__":
    unittest.main()
