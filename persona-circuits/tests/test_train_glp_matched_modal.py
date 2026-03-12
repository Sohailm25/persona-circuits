from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.train_glp_matched_modal import (
    _dataset_subdir_from_artifact,
    _default_run_name,
    _load_dataset_metadata,
    _load_dataset_metadata_from_artifacts,
    _prepare_training_config,
    _resolve_conditional_config,
    _resolve_epoch_size_override,
    _resolve_training_defaults,
)


class TrainGlpMatchedModalTests(unittest.TestCase):
    def test_resolve_training_defaults_uses_expected_fallbacks(self) -> None:
        defaults = _resolve_training_defaults({})
        self.assertEqual(defaults["gpu"], "A100-80GB")
        self.assertEqual(defaults["batch_size"], 512)
        self.assertEqual(defaults["num_epochs"], 1)
        self.assertFalse(defaults["overwrite"])
        self.assertFalse(defaults["save_opt_state"])
        self.assertFalse(defaults["save_epoch_checkpoints"])
        self.assertIsNone(defaults["epoch_size"])
        self.assertEqual(defaults["validation_fraction"], 0.05)
        self.assertEqual(defaults["validation_seed"], 42)

    def test_prepare_training_config_applies_runtime_overrides(self) -> None:
        template = {
            "model_name": "meta-llama/Llama-3.1-8B-Instruct",
            "save_root": ".",
            "run_name": "old-name",
            "output_path": "./runs/old-name",
            "train_dataset": "./data/old",
            "rep_statistic": "./data/old/rep_statistics.pt",
            "wandb_enabled": True,
            "glp_kwargs": {
                "normalizer_config": {"rep_statistic": "./data/old/rep_statistics.pt"},
                "denoiser_config": {"d_input": 4096},
            },
        }
        cfg = _prepare_training_config(
            template_cfg=template,
            dataset_dir="/models/persona-circuits/glp_datasets/sample-ds",
            dataset_metadata={},
            output_path="/models/persona-circuits/glp_runs/sample-run",
            run_name="sample-run",
            batch_size=256,
            gradient_accumulation_steps=2,
            num_epochs=3,
            learning_rate=1e-4,
            epoch_size=8192,
            save_every_n_steps=50,
            wandb_enabled=False,
            save_opt_state=False,
            save_epoch_checkpoints=False,
            validation_fraction=0.1,
            validation_seed=7,
            model_name_override="meta-llama/Llama-3.1-8B-Instruct",
        )
        self.assertEqual(cfg["run_name"], "sample-run")
        self.assertEqual(cfg["output_path"], "/models/persona-circuits/glp_runs/sample-run")
        self.assertEqual(cfg["save_root"], "/models/persona-circuits/glp_runs")
        self.assertEqual(cfg["train_dataset"], "/models/persona-circuits/glp_datasets/sample-ds")
        self.assertEqual(cfg["rep_statistic"], "/models/persona-circuits/glp_datasets/sample-ds/rep_statistics.pt")
        self.assertEqual(cfg["glp_kwargs"]["normalizer_config"]["rep_statistic"], cfg["rep_statistic"])
        self.assertEqual(cfg["batch_size"], 256)
        self.assertEqual(cfg["gradient_accumulation_steps"], 2)
        self.assertEqual(cfg["num_epochs"], 3)
        self.assertEqual(cfg["epoch_size"], 8192)
        self.assertEqual(cfg["save_every_n_steps"], 50)
        self.assertFalse(cfg["wandb_enabled"])
        self.assertFalse(cfg["save_opt_state"])
        self.assertEqual(cfg["save_epochs"], [])
        self.assertEqual(cfg["validation_fraction"], 0.1)
        self.assertEqual(cfg["validation_seed"], 7)

    def test_prepare_training_config_drops_optional_overrides_when_unused(self) -> None:
        template = {
            "glp_kwargs": {"normalizer_config": {}},
            "save_root": ".",
            "output_path": "./runs/x",
            "run_name": "x",
        }
        cfg = _prepare_training_config(
            template_cfg=template,
            dataset_dir="/models/persona-circuits/glp_datasets/sample-ds",
            dataset_metadata={},
            output_path="/models/persona-circuits/glp_runs/sample-run",
            run_name="sample-run",
            batch_size=512,
            gradient_accumulation_steps=1,
            num_epochs=1,
            learning_rate=5e-5,
            epoch_size=None,
            save_every_n_steps=None,
            wandb_enabled=False,
            save_opt_state=True,
            save_epoch_checkpoints=True,
            validation_fraction=0.05,
            validation_seed=42,
            model_name_override=None,
        )
        self.assertNotIn("epoch_size", cfg)
        self.assertNotIn("save_every_n_steps", cfg)
        self.assertTrue(cfg["save_opt_state"])
        self.assertEqual(cfg["save_epochs"], [1])

    def test_prepare_training_config_uses_dataset_metadata_for_conditional_export(self) -> None:
        template = {
            "glp_kwargs": {
                "normalizer_config": {},
                "denoiser_config": {"d_input": 4096},
            },
            "save_root": ".",
            "output_path": "./runs/x",
            "run_name": "x",
        }
        dataset_metadata = {
            "vector_dim": 8192,
            "conditional_export": True,
            "condition_dim": 4096,
            "target_dim": 4096,
            "concat_order": "condition_then_target",
        }
        cfg = _prepare_training_config(
            template_cfg=template,
            dataset_dir="/models/persona-circuits/glp_datasets/sample-ds",
            dataset_metadata=dataset_metadata,
            output_path="/models/persona-circuits/glp_runs/sample-run",
            run_name="sample-run",
            batch_size=512,
            gradient_accumulation_steps=1,
            num_epochs=1,
            learning_rate=5e-5,
            epoch_size=None,
            save_every_n_steps=None,
            wandb_enabled=False,
            save_opt_state=False,
            save_epoch_checkpoints=False,
            validation_fraction=0.05,
            validation_seed=42,
            model_name_override=None,
        )
        self.assertEqual(cfg["glp_kwargs"]["denoiser_config"]["d_input"], 8192)
        self.assertEqual(
            cfg["glp_kwargs"]["conditional_config"],
            {
                "condition_dim": 4096,
                "target_dim": 4096,
                "target_slice_start": 4096,
                "target_slice_end": 8192,
                "concat_order": "condition_then_target",
            },
        )

    def test_default_run_name_includes_dataset_stub(self) -> None:
        run_name = _default_run_name(
            dataset_volume_subdir="glp-llama31-instruct-l12-response-all-tranche1-20260311a",
            output_suffix="pilot smoke",
        )
        self.assertEqual(
            run_name,
            "matched-glp-llama31-instruct-l12-response-all-tranche1-20260311a-pilot-smoke",
        )

    def test_resolve_epoch_size_override_can_disable_default_cap(self) -> None:
        self.assertIsNone(_resolve_epoch_size_override(0, 16384))
        self.assertEqual(_resolve_epoch_size_override(32768, 16384), 32768)
        self.assertEqual(_resolve_epoch_size_override(-1, 16384), 16384)
        self.assertIsNone(_resolve_epoch_size_override(-1, None))

    def test_dataset_subdir_from_artifact_uses_export_summary_path(self) -> None:
        payload = {
            "export_summary": {
                "dataset_dir": "/models/persona-circuits/glp_datasets/glp-llama31-instruct-l12-response-all-tranche1-20260311a"
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "artifact.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                _dataset_subdir_from_artifact(path),
                "glp-llama31-instruct-l12-response-all-tranche1-20260311a",
            )

    def test_load_dataset_metadata_reads_json_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "metadata.json"
            path.write_text(json.dumps({"vector_dim": 8192}), encoding="utf-8")
            self.assertEqual(_load_dataset_metadata(tmpdir), {"vector_dim": 8192})

    def test_load_dataset_metadata_from_artifacts_matches_dataset_subdir(self) -> None:
        payload = {
            "export_summary": {
                "dataset_dir": "/models/persona-circuits/glp_datasets/sample-ds",
                "vector_dim": 8192,
                "conditional_export": True,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "glp_export_memmap_dataset_20260311T000000Z_test.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                _load_dataset_metadata_from_artifacts(Path(tmpdir), "sample-ds"),
                payload["export_summary"],
            )

    def test_resolve_conditional_config_requires_supported_concat_order(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_conditional_config(
                {
                    "conditional_export": True,
                    "condition_dim": 4096,
                    "target_dim": 4096,
                    "concat_order": "unsupported",
                }
            )


if __name__ == "__main__":
    unittest.main()
