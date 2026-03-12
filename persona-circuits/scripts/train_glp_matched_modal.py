"""Launch matched single-layer GLP training on the shared Modal volume.

This runner is isolated from the active experiment lanes. It consumes an
already-exported memmap dataset from the shared model volume, prepares a
resolved upstream GLP trainer config, and executes the upstream trainer inside
an isolated Modal container.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import yaml

APP_NAME = "persona-circuits-train-glp-matched-modal"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_RESULTS_DIRNAME = "glp_sidecar"
DEFAULT_OUTPUT_VOLUME_ROOT = "/models/persona-circuits/glp_runs"
DEFAULT_DATASET_VOLUME_ROOT = "/models/persona-circuits/glp_datasets"
DEFAULT_GPU = "A100-80GB"
DEFAULT_TIMEOUT_HOURS = 12
DEFAULT_BATCH_SIZE_PILOT = 512
DEFAULT_NUM_EPOCHS_PILOT = 1
DEFAULT_GRAD_ACCUM = 1
DEFAULT_LR = 5e-5
DEFAULT_SAVE_EVERY_N_STEPS = 0
DEFAULT_OVERWRITE = False
DEFAULT_WANDB_ENABLED = False
DEFAULT_SAVE_OPT_STATE = False
DEFAULT_SAVE_EPOCH_CHECKPOINTS = False
DEFAULT_VALIDATION_FRACTION = 0.05
DEFAULT_VALIDATION_SEED = 42
DEFAULT_TIMEOUT_SECONDS = DEFAULT_TIMEOUT_HOURS * 60 * 60
DEFAULT_TRAINER_REPO_DIR = "/root/generative_latent_prior"
DEFAULT_REMOTE_CONFIG_DIR = "/tmp/persona_circuits_glp_train"
DEFAULT_TRAIN_WRAPPER_PATH = "/root/scripts/glp_train_with_validation.py"

ROOT = Path(__file__).resolve().parents[1]
SIDECAR_CONFIG_PATH = ROOT / "configs" / "glp_sidecar.yaml"
TRAIN_CONFIG_TEMPLATE_PATH = ROOT / "configs" / "train_glp_llama31_8b_instruct_layer12.yaml"
RESULTS_DIR = ROOT / "results" / DEFAULT_RESULTS_DIRNAME

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(["git"])
    .pip_install(
        [
            "torch>=2.1.0",
            "numpy",
            "pyyaml",
            "omegaconf",
            "datasets",
            "tqdm",
            "einops",
            "safetensors",
            "huggingface_hub",
            "diffusers",
            "transformers>=4.56.0,<=4.57.3",
            "git+https://github.com/davidbau/baukit.git",
        ]
    )
    .run_commands(
        [
            "git clone --depth 1 https://github.com/g-luo/generative_latent_prior.git /root/generative_latent_prior"
        ]
    )
    .add_local_dir(ROOT / "scripts", remote_path="/root/scripts")
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _sanitize_component(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip())
    return text.strip("-._") or "run"


def _latest_export_artifact_path(results_dir: Path) -> Path:
    matches = sorted(results_dir.glob("glp_export_memmap_dataset_*.json"))
    if not matches:
        raise FileNotFoundError(f"No GLP export artifacts found in {results_dir}")
    return matches[-1]


def _dataset_subdir_from_artifact(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    export_summary = payload.get("export_summary") if isinstance(payload, dict) else None
    if not isinstance(export_summary, dict):
        raise ValueError(f"Missing export_summary in {path}")
    dataset_dir = export_summary.get("dataset_dir")
    if not dataset_dir:
        raise ValueError(f"Missing export_summary.dataset_dir in {path}")
    return Path(str(dataset_dir)).name


def _load_dataset_metadata(dataset_dir: str | Path) -> dict[str, Any]:
    metadata_path = Path(dataset_dir) / "metadata.json"
    if not metadata_path.exists():
        return {}
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_dataset_metadata_from_artifacts(results_dir: Path, dataset_volume_subdir: str) -> dict[str, Any]:
    matches = sorted(results_dir.glob("glp_export_memmap_dataset_*.json"), reverse=True)
    for path in matches:
        payload = json.loads(path.read_text(encoding="utf-8"))
        export_summary = payload.get("export_summary") if isinstance(payload, dict) else None
        if not isinstance(export_summary, dict):
            continue
        dataset_dir = export_summary.get("dataset_dir")
        if not dataset_dir:
            continue
        if Path(str(dataset_dir)).name == str(dataset_volume_subdir).strip():
            return export_summary
    return {}


def _resolve_conditional_config(dataset_metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(dataset_metadata, dict) or not bool(dataset_metadata.get("conditional_export")):
        return None
    condition_dim = dataset_metadata.get("condition_dim")
    target_dim = dataset_metadata.get("target_dim")
    concat_order = str(dataset_metadata.get("concat_order") or "").strip()
    if concat_order != "condition_then_target":
        raise ValueError(f"Unsupported conditional concat_order: {concat_order!r}")
    if condition_dim is None or target_dim is None:
        raise ValueError("Conditional dataset metadata missing condition_dim/target_dim")
    condition_dim = int(condition_dim)
    target_dim = int(target_dim)
    if condition_dim <= 0 or target_dim <= 0:
        raise ValueError("Conditional dataset metadata requires positive condition_dim and target_dim")
    return {
        "condition_dim": condition_dim,
        "target_dim": target_dim,
        "target_slice_start": condition_dim,
        "target_slice_end": condition_dim + target_dim,
        "concat_order": concat_order,
    }


def _resolve_training_defaults(sidecar_cfg: dict[str, Any]) -> dict[str, Any]:
    cfg = sidecar_cfg.get("glp_training", {}) if isinstance(sidecar_cfg.get("glp_training"), dict) else {}
    return {
        "dataset_volume_subdir": cfg.get("dataset_volume_subdir"),
        "output_volume_root": str(cfg.get("output_volume_root", DEFAULT_OUTPUT_VOLUME_ROOT)),
        "gpu": str(cfg.get("gpu", DEFAULT_GPU)),
        "timeout_hours": int(cfg.get("timeout_hours", DEFAULT_TIMEOUT_HOURS)),
        "batch_size": int(cfg.get("batch_size", DEFAULT_BATCH_SIZE_PILOT)),
        "gradient_accumulation_steps": int(cfg.get("gradient_accumulation_steps", DEFAULT_GRAD_ACCUM)),
        "num_epochs": int(cfg.get("num_epochs", DEFAULT_NUM_EPOCHS_PILOT)),
        "epoch_size": (
            None if cfg.get("epoch_size") in (None, "", 0) else int(cfg.get("epoch_size"))
        ),
        "learning_rate": float(cfg.get("learning_rate", DEFAULT_LR)),
        "save_every_n_steps": int(cfg.get("save_every_n_steps", DEFAULT_SAVE_EVERY_N_STEPS)),
        "wandb_enabled": bool(cfg.get("wandb_enabled", DEFAULT_WANDB_ENABLED)),
        "overwrite": bool(cfg.get("overwrite", DEFAULT_OVERWRITE)),
        "save_opt_state": bool(cfg.get("save_opt_state", DEFAULT_SAVE_OPT_STATE)),
        "save_epoch_checkpoints": bool(
            cfg.get("save_epoch_checkpoints", DEFAULT_SAVE_EPOCH_CHECKPOINTS)
        ),
        "validation_fraction": float(cfg.get("validation_fraction", DEFAULT_VALIDATION_FRACTION)),
        "validation_seed": int(cfg.get("validation_seed", DEFAULT_VALIDATION_SEED)),
    }


def _default_run_name(*, dataset_volume_subdir: str, output_suffix: str) -> str:
    dataset_stub = _sanitize_component(dataset_volume_subdir)
    suffix = _sanitize_component(output_suffix) if output_suffix.strip() else datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"matched-{dataset_stub}-{suffix}"


def _resolve_epoch_size_override(raw_epoch_size: int, default_epoch_size: int | None) -> int | None:
    if int(raw_epoch_size) == 0:
        return None
    if int(raw_epoch_size) > 0:
        return int(raw_epoch_size)
    if default_epoch_size is None:
        return None
    return int(default_epoch_size)


def _prepare_training_config(
    *,
    template_cfg: dict[str, Any],
    dataset_dir: str,
    dataset_metadata: dict[str, Any] | None,
    output_path: str,
    run_name: str,
    batch_size: int,
    gradient_accumulation_steps: int,
    num_epochs: int,
    learning_rate: float,
    epoch_size: int | None,
    save_every_n_steps: int | None,
    wandb_enabled: bool,
    save_opt_state: bool,
    save_epoch_checkpoints: bool,
    validation_fraction: float,
    validation_seed: int,
    model_name_override: str | None = None,
) -> dict[str, Any]:
    cfg = deepcopy(template_cfg)
    if not isinstance(cfg.get("glp_kwargs"), dict):
        raise ValueError("Template config missing glp_kwargs")
    normalizer_cfg = cfg["glp_kwargs"].setdefault("normalizer_config", {})
    if not isinstance(normalizer_cfg, dict):
        raise ValueError("Template config glp_kwargs.normalizer_config must be a mapping")
    denoiser_cfg = cfg["glp_kwargs"].setdefault("denoiser_config", {})
    if not isinstance(denoiser_cfg, dict):
        raise ValueError("Template config glp_kwargs.denoiser_config must be a mapping")

    cfg["save_root"] = str(Path(output_path).parent)
    cfg["run_name"] = str(run_name)
    cfg["output_path"] = str(output_path)
    cfg["train_dataset"] = str(dataset_dir)
    cfg["rep_statistic"] = str(Path(dataset_dir) / "rep_statistics.pt")
    normalizer_cfg["rep_statistic"] = cfg["rep_statistic"]
    if isinstance(dataset_metadata, dict) and dataset_metadata.get("vector_dim") is not None:
        denoiser_cfg["d_input"] = int(dataset_metadata["vector_dim"])
    conditional_cfg = _resolve_conditional_config(dataset_metadata)
    if conditional_cfg is not None:
        cfg["glp_kwargs"]["conditional_config"] = conditional_cfg
    else:
        cfg["glp_kwargs"].pop("conditional_config", None)
    if model_name_override:
        cfg["model_name"] = str(model_name_override)
    cfg["batch_size"] = int(batch_size)
    cfg["gradient_accumulation_steps"] = int(gradient_accumulation_steps)
    cfg["num_epochs"] = int(num_epochs)
    cfg["learning_rate"] = float(learning_rate)
    cfg["wandb_enabled"] = bool(wandb_enabled)
    cfg["save_opt_state"] = bool(save_opt_state)
    cfg["save_epochs"] = [int(num_epochs)] if save_epoch_checkpoints else []
    cfg["validation_fraction"] = float(validation_fraction)
    cfg["validation_seed"] = int(validation_seed)

    if epoch_size is None:
        cfg.pop("epoch_size", None)
    else:
        cfg["epoch_size"] = int(epoch_size)
    if save_every_n_steps is None or int(save_every_n_steps) <= 0:
        cfg.pop("save_every_n_steps", None)
    else:
        cfg["save_every_n_steps"] = int(save_every_n_steps)
    return cfg


def _summarize_checkpoint_dir(output_dir: Path) -> dict[str, Any]:
    files = sorted(p.relative_to(output_dir).as_posix() for p in output_dir.rglob("*") if p.is_file())
    checkpoints = [path for path in files if path.endswith(".safetensors")]
    return {
        "exists": output_dir.exists(),
        "file_count": len(files),
        "checkpoint_files": checkpoints,
        "has_final": any(path == "final.safetensors" for path in checkpoints),
    }


@app.function(
    image=image,
    gpu=DEFAULT_GPU,
    timeout=DEFAULT_TIMEOUT_SECONDS,
    volumes={"/models": vol},
)
def train_glp_remote(
    *,
    resolved_config: dict[str, Any],
    output_volume_root: str,
    overwrite: bool,
) -> dict[str, Any]:
    dataset_dir = Path(str(resolved_config["train_dataset"]))
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
    rep_statistic = Path(str(resolved_config["rep_statistic"]))
    if not rep_statistic.exists():
        raise FileNotFoundError(f"rep_statistics.pt not found: {rep_statistic}")

    output_dir = Path(str(resolved_config["output_path"]))
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(f"Output directory already exists and is non-empty: {output_dir}")
        for child in output_dir.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            else:
                import shutil
                shutil.rmtree(child)
    output_dir.mkdir(parents=True, exist_ok=True)
    Path(str(output_volume_root)).mkdir(parents=True, exist_ok=True)

    remote_config_dir = Path(DEFAULT_REMOTE_CONFIG_DIR)
    remote_config_dir.mkdir(parents=True, exist_ok=True)
    remote_config_path = remote_config_dir / f"{_sanitize_component(str(resolved_config['run_name']))}.yaml"
    remote_config_path.write_text(yaml.safe_dump(resolved_config, sort_keys=False), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = DEFAULT_TRAINER_REPO_DIR + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "/root/scripts" + os.pathsep + env["PYTHONPATH"]

    cmd = ["python3", DEFAULT_TRAIN_WRAPPER_PATH, f"config={remote_config_path}"]
    start_ts = datetime.now(timezone.utc)
    log_tail: list[str] = []
    process = subprocess.Popen(
        cmd,
        cwd=DEFAULT_TRAINER_REPO_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        stripped = line.rstrip()
        if stripped:
            log_tail.append(stripped)
            if len(log_tail) > 200:
                log_tail = log_tail[-200:]
    return_code = process.wait()
    end_ts = datetime.now(timezone.utc)
    if return_code != 0:
        raise RuntimeError(
            json.dumps(
                {
                    "event": "glp_train_failed",
                    "return_code": int(return_code),
                    "run_name": resolved_config["run_name"],
                    "output_path": str(output_dir),
                    "log_tail": log_tail[-80:],
                },
                indent=2,
            )
        )

    try:
        vol.commit()
    except Exception:
        pass

    metrics_path = output_dir / "training_metrics.json"
    training_metrics = None
    if metrics_path.exists():
        try:
            training_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:
            training_metrics = {"artifact_path": str(metrics_path), "parse_error": True}

    return {
        "timestamp_utc": end_ts.isoformat(),
        "artifact_type": "matched_glp_train_summary",
        "run_name": str(resolved_config["run_name"]),
        "output_path": str(output_dir),
        "dataset_dir": str(dataset_dir),
        "rep_statistic": str(rep_statistic),
        "trainer_repo_dir": DEFAULT_TRAINER_REPO_DIR,
        "return_code": int(return_code),
        "started_at_utc": start_ts.isoformat(),
        "finished_at_utc": end_ts.isoformat(),
        "config": resolved_config,
        "output_summary": _summarize_checkpoint_dir(output_dir),
        "training_metrics": training_metrics,
        "log_tail": log_tail[-80:],
    }


@app.local_entrypoint()
def main(
    config_path: str = "",
    dataset_volume_subdir: str = "",
    output_suffix: str = "",
    model_name: str = "",
    output_volume_root: str = "",
    batch_size: int = -1,
    gradient_accumulation_steps: int = -1,
    num_epochs: int = -1,
    epoch_size: int = -1,
    learning_rate: float = -1.0,
    save_every_n_steps: int = -1,
    overwrite: int = -1,
    wandb_enabled: int = -1,
    save_opt_state: int = -1,
    save_epoch_checkpoints: int = -1,
    validation_fraction: float = float("nan"),
    validation_seed: int = -1,
) -> None:
    sidecar_cfg = _load_yaml(SIDECAR_CONFIG_PATH)
    defaults = _resolve_training_defaults(sidecar_cfg)
    template_path = Path(config_path).resolve() if config_path.strip() else TRAIN_CONFIG_TEMPLATE_PATH
    template_cfg = _load_yaml(template_path)
    if not template_cfg:
        raise FileNotFoundError(f"Training template missing or empty: {template_path}")

    resolved_dataset_subdir = dataset_volume_subdir.strip() or str(defaults.get("dataset_volume_subdir") or "").strip()
    if not resolved_dataset_subdir:
        resolved_dataset_subdir = _dataset_subdir_from_artifact(_latest_export_artifact_path(RESULTS_DIR))

    resolved_output_root = output_volume_root.strip() or str(defaults["output_volume_root"])
    resolved_run_name = _default_run_name(
        dataset_volume_subdir=resolved_dataset_subdir,
        output_suffix=output_suffix,
    )
    resolved_output_path = str(Path(resolved_output_root) / resolved_run_name)
    resolved_model_name = model_name.strip() or str(template_cfg.get("model_name", ""))

    resolved_batch_size = int(batch_size) if int(batch_size) > 0 else int(defaults["batch_size"])
    resolved_grad_accum = (
        int(gradient_accumulation_steps)
        if int(gradient_accumulation_steps) > 0
        else int(defaults["gradient_accumulation_steps"])
    )
    resolved_num_epochs = int(num_epochs) if int(num_epochs) > 0 else int(defaults["num_epochs"])
    resolved_epoch_size = _resolve_epoch_size_override(
        int(epoch_size),
        None if defaults.get("epoch_size") is None else int(defaults["epoch_size"]),
    )
    resolved_learning_rate = (
        float(learning_rate) if float(learning_rate) > 0 else float(defaults["learning_rate"])
    )
    resolved_save_every_n_steps = None
    if int(save_every_n_steps) > 0:
        resolved_save_every_n_steps = int(save_every_n_steps)
    elif int(defaults["save_every_n_steps"]) > 0:
        resolved_save_every_n_steps = int(defaults["save_every_n_steps"])
    resolved_overwrite = bool(int(overwrite)) if int(overwrite) >= 0 else bool(defaults["overwrite"])
    resolved_wandb = bool(int(wandb_enabled)) if int(wandb_enabled) >= 0 else bool(defaults["wandb_enabled"])
    resolved_save_opt_state = (
        bool(int(save_opt_state)) if int(save_opt_state) >= 0 else bool(defaults["save_opt_state"])
    )
    resolved_save_epoch_checkpoints = (
        bool(int(save_epoch_checkpoints))
        if int(save_epoch_checkpoints) >= 0
        else bool(defaults["save_epoch_checkpoints"])
    )
    resolved_validation_fraction = (
        float(validation_fraction)
        if float(validation_fraction) >= 0.0
        else float(defaults["validation_fraction"])
    )
    resolved_validation_seed = (
        int(validation_seed)
        if int(validation_seed) >= 0
        else int(defaults["validation_seed"])
    )

    dataset_dir = str(Path(DEFAULT_DATASET_VOLUME_ROOT) / resolved_dataset_subdir)
    dataset_metadata = _load_dataset_metadata(dataset_dir)
    if not dataset_metadata:
        dataset_metadata = _load_dataset_metadata_from_artifacts(RESULTS_DIR, resolved_dataset_subdir)
    resolved_config = _prepare_training_config(
        template_cfg=template_cfg,
        dataset_dir=dataset_dir,
        dataset_metadata=dataset_metadata,
        output_path=resolved_output_path,
        run_name=resolved_run_name,
        batch_size=resolved_batch_size,
        gradient_accumulation_steps=resolved_grad_accum,
        num_epochs=resolved_num_epochs,
        learning_rate=resolved_learning_rate,
        epoch_size=resolved_epoch_size,
        save_every_n_steps=resolved_save_every_n_steps,
        wandb_enabled=resolved_wandb,
        save_opt_state=resolved_save_opt_state,
        save_epoch_checkpoints=resolved_save_epoch_checkpoints,
        validation_fraction=resolved_validation_fraction,
        validation_seed=resolved_validation_seed,
        model_name_override=resolved_model_name or None,
    )

    summary = train_glp_remote.remote(
        resolved_config=resolved_config,
        output_volume_root=resolved_output_root,
        overwrite=resolved_overwrite,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{_sanitize_component(output_suffix)}" if output_suffix.strip() else ""
    artifact_path = RESULTS_DIR / f"train_glp_matched_modal_{timestamp}{suffix}.json"
    artifact = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "train_glp_matched_modal_summary",
        "inputs": {
            "config_path": str(template_path),
            "dataset_volume_subdir": resolved_dataset_subdir,
            "dataset_dir": dataset_dir,
            "dataset_metadata": dataset_metadata,
            "output_volume_root": resolved_output_root,
            "run_name": resolved_run_name,
            "batch_size": resolved_batch_size,
            "gradient_accumulation_steps": resolved_grad_accum,
            "num_epochs": resolved_num_epochs,
            "epoch_size": resolved_epoch_size,
            "learning_rate": resolved_learning_rate,
            "save_every_n_steps": resolved_save_every_n_steps,
            "overwrite": resolved_overwrite,
            "wandb_enabled": resolved_wandb,
            "save_opt_state": resolved_save_opt_state,
            "save_epoch_checkpoints": resolved_save_epoch_checkpoints,
            "validation_fraction": resolved_validation_fraction,
            "validation_seed": resolved_validation_seed,
            "model_name": resolved_model_name,
        },
        "training_summary": summary,
    }
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps({"artifact_path": str(artifact_path), "output_path": summary["output_path"]}, indent=2))
