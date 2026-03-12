"""Unit tests for GLP sidecar runtime helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import torch

from scripts.shared.glp_runtime import (
    _prepare_conditional_latents,
    _resolve_conditional_target_slice,
    _supports_layer_conditioning,
    build_glp_alignment_report,
    build_identity_projector,
    resolve_glp_metadata,
)


class GLPRuntimeTests(unittest.TestCase):
    def test_resolve_glp_metadata_reads_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "config.yaml").write_text(
                """
model_name: meta-llama/Meta-Llama-3.1-8B
run_name: glp-demo
glp_kwargs:
  tracedict_config:
    layer_prefix: model.layers
    layers: [15]
    retain: output
  denoiser_config:
    d_input: 4096
    n_layers: 6
    multi_layer_n_layers: null
""".strip(),
                encoding="utf-8",
            )
            metadata = resolve_glp_metadata(weights_folder=str(path), checkpoint="final")
        self.assertTrue(metadata["config_available"])
        self.assertEqual(metadata["training_model_name"], "meta-llama/Meta-Llama-3.1-8B")
        self.assertEqual(metadata["training_layers"], [15])
        self.assertEqual(metadata["run_name"], "glp-demo")

    def test_resolve_glp_metadata_handles_pathlib_yaml_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "config.yaml").write_text(
                """
model_name: meta-llama/Llama-3.1-8B-Instruct
run_name: glp-demo
output_path: !!python/object/apply:pathlib.PosixPath
- /
- models
- persona-circuits
- glp_runs
- glp-demo
glp_kwargs:
  tracedict_config:
    layer_prefix: model.layers
    layers: [12]
    retain: output
""".strip(),
                encoding="utf-8",
            )
            metadata = resolve_glp_metadata(weights_folder=str(path), checkpoint="final")
        self.assertTrue(metadata["config_available"])
        self.assertEqual(metadata["training_model_name"], "meta-llama/Llama-3.1-8B-Instruct")
        self.assertEqual(metadata["training_layers"], [12])

    def test_build_identity_projector_is_passthrough(self) -> None:
        projector = build_identity_projector(label="disabled")
        payload = [[1.0, 2.0]]
        self.assertEqual(projector.postprocess(payload, condition_acts=[[3.0, 4.0]]), payload)
        self.assertFalse(projector.enabled)
        self.assertEqual(projector.metadata["projector_mode"], "disabled")

    def test_build_glp_alignment_report(self) -> None:
        report = build_glp_alignment_report(
            metadata={
                "training_model_name": "meta-llama/Meta-Llama-3.1-8B",
                "training_layers": [15],
            },
            target_model_name="meta-llama/Meta-Llama-3.1-8B-Instruct",
            target_layer=12,
        )
        self.assertFalse(report["claim_grade_ready"])
        self.assertFalse(report["model_match"])
        self.assertFalse(report["layer_match"])

    def test_supports_layer_conditioning_false_for_single_layer_metadata(self) -> None:
        class DummyModel:
            denoiser = object()

        self.assertFalse(
            _supports_layer_conditioning(
                metadata={"training_layers": [15], "multi_layer_n_layers": None},
                model=DummyModel(),
            )
        )

    def test_supports_layer_conditioning_true_for_runtime_multi_layer_model(self) -> None:
        class DummyInnerModel:
            multi_layer_n_layers = 32

        class DummyDenoiser:
            model = DummyInnerModel()

        class DummyModel:
            denoiser = DummyDenoiser()

        self.assertTrue(
            _supports_layer_conditioning(
                metadata={"training_layers": [15]},
                model=DummyModel(),
            )
        )

    def test_resolve_glp_metadata_reads_conditional_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "config.yaml").write_text(
                """
model_name: meta-llama/Llama-3.1-8B-Instruct
run_name: glp-cond-demo
glp_kwargs:
  tracedict_config:
    layer_prefix: model.layers
    layers: [12]
    retain: output
  denoiser_config:
    d_input: 8192
    n_layers: 6
    multi_layer_n_layers: null
  conditional_config:
    condition_dim: 4096
    target_dim: 4096
    target_slice_start: 4096
    target_slice_end: 8192
    concat_order: condition_then_target
""".strip(),
                encoding="utf-8",
            )
            metadata = resolve_glp_metadata(weights_folder=str(path), checkpoint="final")
        self.assertTrue(metadata["conditional"])
        self.assertEqual(metadata["condition_dim"], 4096)
        self.assertEqual(metadata["target_dim"], 4096)
        self.assertEqual(metadata["concat_order"], "condition_then_target")

    def test_prepare_conditional_latents_repeats_single_condition_token(self) -> None:
        condition = torch.ones(2, 1, 3)
        target = torch.zeros(2, 4, 5)
        concat, target_has_seq_dim, condition_slice = _prepare_conditional_latents(
            condition_acts=condition,
            target_acts=target,
            conditional_config={
                "condition_dim": 3,
                "target_dim": 5,
                "concat_order": "condition_then_target",
            },
        )
        self.assertTrue(target_has_seq_dim)
        self.assertEqual(tuple(concat.shape), (2, 4, 8))
        self.assertEqual(condition_slice.start, 0)
        self.assertEqual(condition_slice.stop, 3)
        self.assertTrue(torch.equal(concat[:, :, :3], torch.ones(2, 4, 3)))

    def test_prepare_conditional_latents_accepts_non_sequence_target(self) -> None:
        condition = torch.ones(1, 4)
        target = torch.zeros(1, 6)
        concat, target_has_seq_dim, condition_slice = _prepare_conditional_latents(
            condition_acts=condition,
            target_acts=target,
            conditional_config={
                "condition_dim": 4,
                "target_dim": 6,
                "concat_order": "condition_then_target",
            },
        )
        self.assertFalse(target_has_seq_dim)
        self.assertEqual(tuple(concat.shape), (1, 1, 10))
        self.assertEqual(condition_slice.stop, 4)

    def test_resolve_conditional_target_slice_validates_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_conditional_target_slice(
                {
                    "condition_dim": 4,
                    "target_dim": 6,
                    "target_slice_start": 4,
                }
            )

    def test_resolve_conditional_target_slice_validates_layout(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_conditional_target_slice(
                {
                    "condition_dim": 4,
                    "target_dim": 6,
                    "target_slice_start": 3,
                    "target_slice_end": 10,
                }
            )
        self.assertEqual(
            _resolve_conditional_target_slice(
                {
                    "condition_dim": 4,
                    "target_dim": 6,
                    "target_slice_start": 4,
                    "target_slice_end": 10,
                }
            ),
            (4, 10),
        )


if __name__ == "__main__":
    unittest.main()
