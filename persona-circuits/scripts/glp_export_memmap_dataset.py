"""Export natural activation datasets for matched GLP training.

This exporter is intentionally isolated from the active experiment runners.
It reads existing prompt JSONL files, formats neutral chat prompts with the
current tokenizer template, captures layer activations, and writes a
GLP-compatible memmap dataset to the shared model volume.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import torch
import yaml

from scripts.shared.behavioral_eval import _format_chat_prompt

APP_NAME = "persona-circuits-glp-export-memmap-dataset"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_RESULTS_DIRNAME = "glp_sidecar"
DEFAULT_NEUTRAL_SYSTEM_PROMPT = (
    "You are a helpful, honest, and concise assistant. Answer directly and accurately."
)
DEFAULT_CAPTURE_MODE = "response_all"
DEFAULT_CONDITION_MODE = ""
DEFAULT_MAX_NEW_TOKENS = 64
DEFAULT_TEMPERATURE = 0.0
DEFAULT_SAMPLES_PER_SHARD = 32768
DEFAULT_SKIP_WARNING_FRACTION = 0.05
DEFAULT_VOLUME_DATASET_ROOT = "/models/persona-circuits/glp_datasets"
ALLOWED_CAPTURE_MODES = {"prompt_last", "response_last", "response_all", "all_tokens"}

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
SIDECAR_CONFIG_PATH = ROOT / "configs" / "glp_sidecar.yaml"
RESULTS_DIR = ROOT / "results" / DEFAULT_RESULTS_DIRNAME

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").apt_install("git").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "numpy",
        "pyyaml",
    ]
).add_local_dir(ROOT / "scripts", remote_path="/root/scripts")


@dataclass(frozen=True)
class PromptRecord:
    source_path: str
    row_id: str
    system_prompt: str
    user_query: str
    category: str | None
    trait: str | None
    source_row_id: str | None
    prompt_sha256: str


class FlatMemmapWriter:
    def __init__(
        self,
        *,
        output_dir: Path,
        vector_dim: int,
        dtype: np.dtype,
        samples_per_shard: int,
    ) -> None:
        if vector_dim <= 0:
            raise ValueError("vector_dim must be > 0")
        if samples_per_shard <= 0:
            raise ValueError("samples_per_shard must be > 0")
        self.output_dir = output_dir
        self.vector_dim = int(vector_dim)
        self.dtype = np.dtype(dtype)
        self.samples_per_shard = int(samples_per_shard)
        self.file_size = int(self.vector_dim * self.samples_per_shard)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.indices: list[tuple[int, int, int]] = []
        self.memmap_files: list[np.memmap] = []
        self.cur_offset = 0
        self.sample_count = 0
        self._new_memmap_file()
        (self.output_dir / "dtype.txt").write_text(str(self.dtype), encoding="utf-8")

    def _new_memmap_file(self) -> None:
        path = self.output_dir / f"data_{len(self.memmap_files):04d}.npy"
        memmap = np.memmap(path, mode="w+", dtype=self.dtype, shape=self.file_size)
        self.memmap_files.append(memmap)
        self.cur_offset = 0

    def write_vector(self, vector: np.ndarray) -> None:
        chunk = np.asarray(vector, dtype=self.dtype).reshape(-1)
        if chunk.size != self.vector_dim:
            raise ValueError(f"Expected vector_dim={self.vector_dim}, got {chunk.size}")
        if self.cur_offset + self.vector_dim > self.file_size:
            self._new_memmap_file()
        start = int(self.cur_offset)
        end = int(start + self.vector_dim)
        self.memmap_files[-1][start:end] = chunk
        self.indices.append((len(self.memmap_files) - 1, start, end))
        self.cur_offset = end
        self.sample_count += 1

    def flush(self) -> None:
        for memmap_file in self.memmap_files:
            memmap_file.flush()
        np.save(self.output_dir / "data_indices.npy", np.asarray(self.indices, dtype=np.uint64))


class RunningMoments:
    def __init__(self, vector_dim: int) -> None:
        self.vector_dim = int(vector_dim)
        self.count = 0
        self._sum = np.zeros(self.vector_dim, dtype=np.float64)
        self._sum_sq = np.zeros(self.vector_dim, dtype=np.float64)

    def update(self, vector: np.ndarray) -> None:
        arr = np.asarray(vector, dtype=np.float64).reshape(-1)
        if arr.size != self.vector_dim:
            raise ValueError(f"Expected vector_dim={self.vector_dim}, got {arr.size}")
        self._sum += arr
        self._sum_sq += arr * arr
        self.count += 1

    def finalize(self) -> tuple[np.ndarray, np.ndarray]:
        if self.count <= 0:
            raise ValueError("Cannot finalize empty running moments")
        mean = self._sum / float(self.count)
        var = np.maximum((self._sum_sq / float(self.count)) - (mean * mean), 0.0)
        return mean.astype(np.float32), var.astype(np.float32)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _set_modal_cache_env() -> None:
    os.environ["HF_HOME"] = "/models/huggingface"
    os.environ["TRANSFORMERS_CACHE"] = "/models/huggingface"
    os.environ["HF_HUB_CACHE"] = "/models/huggingface"
    os.environ["HUGGINGFACE_HUB_CACHE"] = "/models/huggingface"
    Path("/models/huggingface").mkdir(parents=True, exist_ok=True)
    Path(DEFAULT_VOLUME_DATASET_ROOT).mkdir(parents=True, exist_ok=True)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _hash_jsonable(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_prompt_row(
    row: dict[str, Any],
    *,
    default_system_prompt: str,
) -> tuple[str, str]:
    system_prompt = str(
        row.get("neutral_system_prompt")
        or row.get("system_low")
        or row.get("system_prompt")
        or default_system_prompt
    ).strip()
    user_query = str(
        row.get("user_query")
        or row.get("prompt")
        or row.get("question")
        or row.get("query")
        or row.get("neutral_user_prompt")
        or ""
    ).strip()
    if not system_prompt:
        system_prompt = default_system_prompt
    if not user_query:
        raise ValueError(f"Prompt row missing user query fields: {sorted(row.keys())}")
    return system_prompt, user_query


def _build_prompt_records(
    *,
    prompt_paths: list[Path],
    default_system_prompt: str,
    limit_per_file: int,
    seed: int,
    dedupe: bool,
) -> list[PromptRecord]:
    records: list[PromptRecord] = []
    seen_prompt_hashes: set[str] = set()
    for file_index, path in enumerate(prompt_paths):
        rows = _load_jsonl(path)
        if limit_per_file > 0 and len(rows) > limit_per_file:
            rng = random.Random(int(seed) + file_index)
            rows = rows.copy()
            rng.shuffle(rows)
            rows = rows[:limit_per_file]
        for row_index, row in enumerate(rows):
            system_prompt, user_query = _resolve_prompt_row(
                row,
                default_system_prompt=default_system_prompt,
            )
            prompt_sha256 = _hash_jsonable({"system": system_prompt, "user": user_query})
            if dedupe and prompt_sha256 in seen_prompt_hashes:
                continue
            seen_prompt_hashes.add(prompt_sha256)
            records.append(
                PromptRecord(
                    source_path=str(path),
                    row_id=str(row.get("id", row_index)),
                    system_prompt=system_prompt,
                    user_query=user_query,
                    category=(str(row["category"]) if row.get("category") is not None else None),
                    trait=(str(row["trait"]) if row.get("trait") is not None else None),
                    source_row_id=(
                        str(row["source_row_id"]) if row.get("source_row_id") is not None else None
                    ),
                    prompt_sha256=prompt_sha256,
                )
            )
    return records


def _select_capture_positions(prompt_length: int, full_length: int, capture_mode: str) -> list[int]:
    if prompt_length <= 0 or full_length <= 0:
        raise ValueError("prompt_length and full_length must be > 0")
    if full_length < prompt_length:
        raise ValueError("full_length cannot be smaller than prompt_length")
    if capture_mode == "prompt_last":
        return [prompt_length - 1]
    if capture_mode == "response_last":
        return [full_length - 1] if full_length > prompt_length else []
    if capture_mode == "response_all":
        return list(range(prompt_length, full_length))
    if capture_mode == "all_tokens":
        return list(range(full_length))
    raise ValueError(f"Unsupported capture_mode={capture_mode}")


def _sanitize_slug(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "dataset"


def _default_dataset_name(
    model_name: str,
    layer: int,
    capture_mode: str,
    prompt_count: int,
    *,
    condition_mode: str = "",
) -> str:
    model_slug = _sanitize_slug(model_name.split("/")[-1])
    if condition_mode.strip():
        cond_slug = _sanitize_slug(condition_mode)
        target_slug = _sanitize_slug(capture_mode)
        return f"glp-{model_slug}-l{int(layer)}-cond-{cond_slug}-to-{target_slug}-{int(prompt_count)}p"
    return f"glp-{model_slug}-l{int(layer)}-{capture_mode}-{int(prompt_count)}p"


def _format_export_prompt(tokenizer: Any, system_prompt: str, user_query: str) -> str:
    try:
        return _format_chat_prompt(tokenizer, system_prompt, user_query)
    except Exception as exc:  # noqa: BLE001
        text = str(exc).lower()
        if "system role not supported" in text and hasattr(tokenizer, "apply_chat_template"):
            merged_user = f"{system_prompt.strip()}\n\n{user_query.strip()}".strip()
            try:
                return tokenizer.apply_chat_template(
                    [{"role": "user", "content": merged_user}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:  # noqa: BLE001
                pass
        return f"System: {system_prompt}\nUser: {user_query}\nAssistant:"


def _load_hooked_model(model_name: str) -> Any:
    from sae_lens import HookedSAETransformer

    common_kwargs = {
        "device": "cuda",
        "dtype": torch.bfloat16,
    }
    try:
        return HookedSAETransformer.from_pretrained(model_name, **common_kwargs)
    except OSError as exc:
        text = str(exc).lower()
        if "gated repo" not in text and "401 client error" not in text and "cannot access gated repo" not in text:
            raise
        print(
            json.dumps(
                {
                    "event": "model_load_retry_local_files_only",
                    "model_name": model_name,
                }
            ),
            flush=True,
        )
        return HookedSAETransformer.from_pretrained(
            model_name,
            local_files_only=True,
            **common_kwargs,
        )


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=60 * 60 * 12,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def export_memmap_dataset(
    *,
    model_name: str,
    layer: int,
    capture_mode: str,
    condition_mode: str,
    max_new_tokens: int,
    temperature: float,
    dataset_volume_subdir: str,
    prompt_records_payload: list[dict[str, Any]],
    samples_per_shard: int,
    overwrite: bool,
    seed: int,
) -> dict[str, Any]:
    if capture_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"capture_mode must be one of {sorted(ALLOWED_CAPTURE_MODES)}")
    if condition_mode and condition_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"condition_mode must be one of {sorted(ALLOWED_CAPTURE_MODES)}")
    _set_modal_cache_env()
    _seed_everything(seed)

    dataset_dir = Path(DEFAULT_VOLUME_DATASET_ROOT) / dataset_volume_subdir
    if dataset_dir.exists() and any(dataset_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(f"Dataset path already exists and is non-empty: {dataset_dir}")
        for child in dataset_dir.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            else:
                import shutil
                shutil.rmtree(child)
    dataset_dir.mkdir(parents=True, exist_ok=True)

    model = _load_hooked_model(model_name)
    model.eval()

    hook_name = f"blocks.{int(layer)}.hook_resid_post"
    d_model = int(getattr(model.cfg, "d_model"))
    conditional_export = bool(str(condition_mode).strip())
    vector_dim = int(d_model * 2) if conditional_export else int(d_model)
    writer = FlatMemmapWriter(
        output_dir=dataset_dir,
        vector_dim=vector_dim,
        dtype=np.float32,
        samples_per_shard=int(samples_per_shard),
    )
    moments = RunningMoments(vector_dim=vector_dim)

    prompt_manifest: list[dict[str, Any]] = []
    skipped_no_response = 0

    for prompt_index, record in enumerate(prompt_records_payload):
        if prompt_index == 0 or (prompt_index + 1) % 25 == 0:
            print(
                json.dumps(
                    {
                        "event": "export_progress",
                        "prompt_index": int(prompt_index),
                        "prompt_count": int(len(prompt_records_payload)),
                        "sample_count": int(writer.sample_count),
                    }
                ),
                flush=True,
            )
        prompt_text = _format_export_prompt(
            model.tokenizer,
            str(record["system_prompt"]),
            str(record["user_query"]),
        )
        prompt_tokens = model.to_tokens(prompt_text, prepend_bos=True)
        prompt_length = int(prompt_tokens.shape[1])
        full_tokens = prompt_tokens
        completion_tokens = None
        cache_tokens = None
        cache = None
        resid = None
        generated_completion = ""

        if capture_mode != "prompt_last":
            with torch.inference_mode():
                full_tokens = model.generate(
                    prompt_tokens,
                    max_new_tokens=int(max_new_tokens),
                    temperature=float(temperature),
                    top_k=None,
                    stop_at_eos=True,
                    verbose=False,
                )
            completion_tokens = full_tokens[0, prompt_length:]
            generated_completion = model.to_string(completion_tokens)

        full_length = int(full_tokens.shape[1])
        target_capture_positions = _select_capture_positions(
            prompt_length=prompt_length,
            full_length=full_length,
            capture_mode=capture_mode,
        )
        if conditional_export:
            condition_capture_positions = _select_capture_positions(
                prompt_length=prompt_length,
                full_length=full_length,
                capture_mode=str(condition_mode),
            )
        else:
            condition_capture_positions = []
        if not target_capture_positions:
            skipped_no_response += 1
            del prompt_tokens, full_tokens, completion_tokens
            if torch.cuda.is_available() and (prompt_index + 1) % 16 == 0:
                torch.cuda.empty_cache()
            continue

        cache_tokens = full_tokens.detach().clone()
        with torch.inference_mode():
            _, cache = model.run_with_cache(cache_tokens, names_filter=lambda name: name == hook_name)
        resid = cache[hook_name][0].detach().to(torch.float32).cpu()

        start_sample_idx = int(writer.sample_count)
        if conditional_export:
            if len(target_capture_positions) != 1 or len(condition_capture_positions) != 1:
                raise ValueError(
                    "Conditional export currently requires exactly one condition position and one target position per prompt"
                )
            condition_vec = resid[int(condition_capture_positions[0])].numpy().astype(np.float32, copy=False)
            target_vec = resid[int(target_capture_positions[0])].numpy().astype(np.float32, copy=False)
            concat_vec = np.concatenate([condition_vec, target_vec], axis=0).astype(np.float32, copy=False)
            writer.write_vector(concat_vec)
            moments.update(concat_vec)
        else:
            for pos in target_capture_positions:
                vec = resid[int(pos)].numpy().astype(np.float32, copy=False)
                writer.write_vector(vec)
                moments.update(vec)
        end_sample_idx = int(writer.sample_count)

        prompt_manifest.append(
            {
                "prompt_index": int(prompt_index),
                "source_path": str(record["source_path"]),
                "row_id": str(record["row_id"]),
                "source_row_id": record.get("source_row_id"),
                "trait": record.get("trait"),
                "category": record.get("category"),
                "prompt_sha256": str(record["prompt_sha256"]),
                "prompt_length": int(prompt_length),
                "full_length": int(full_length),
                "capture_mode": capture_mode,
                "condition_mode": str(condition_mode) if conditional_export else None,
                "num_vectors": int(end_sample_idx - start_sample_idx),
                "start_sample_idx": start_sample_idx,
                "end_sample_idx": end_sample_idx,
                "generated_completion_preview": generated_completion[:200],
            }
        )

        del resid
        if cache is not None:
            del cache
        del cache_tokens, full_tokens, prompt_tokens, completion_tokens
        if torch.cuda.is_available() and (prompt_index + 1) % 16 == 0:
            torch.cuda.empty_cache()

    if writer.sample_count <= 0:
        raise RuntimeError("Export completed with zero vectors; no dataset written")

    writer.flush()
    mean, var = moments.finalize()
    torch.save(
        {
            "mean": torch.tensor(mean, dtype=torch.float32),
            "var": torch.tensor(var, dtype=torch.float32),
        },
        dataset_dir / "rep_statistics.pt",
    )
    with (dataset_dir / "prompt_manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in prompt_manifest:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "glp_memmap_export",
        "model_name": model_name,
        "layer": int(layer),
        "hook_name": hook_name,
        "capture_mode": capture_mode,
        "conditional_export": conditional_export,
        "condition_mode": str(condition_mode) if conditional_export else None,
        "target_mode": str(capture_mode),
        "condition_dim": int(d_model) if conditional_export else 0,
        "target_dim": int(d_model),
        "concat_order": "condition_then_target" if conditional_export else None,
        "max_new_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "dataset_dir": str(dataset_dir),
        "samples_per_shard": int(samples_per_shard),
        "prompt_count": int(len(prompt_records_payload)),
        "prompt_manifest_count": int(len(prompt_manifest)),
        "sample_count": int(writer.sample_count),
        "vector_dim": int(vector_dim),
        "skipped_no_response": int(skipped_no_response),
        "skipped_no_response_fraction": float(
            float(skipped_no_response) / float(len(prompt_records_payload))
            if prompt_records_payload
            else 0.0
        ),
    }
    (dataset_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if prompt_records_payload:
        skip_fraction = float(skipped_no_response) / float(len(prompt_records_payload))
        if skip_fraction >= DEFAULT_SKIP_WARNING_FRACTION:
            print(
                json.dumps(
                    {
                        "event": "export_skip_warning",
                        "skipped_no_response": int(skipped_no_response),
                        "prompt_count": int(len(prompt_records_payload)),
                        "skip_fraction": float(skip_fraction),
                        "capture_mode": capture_mode,
                        "condition_mode": str(condition_mode) if conditional_export else "",
                    }
                ),
                flush=True,
            )
        else:
            print(
                json.dumps(
                    {
                        "event": "export_skip_summary",
                        "skipped_no_response": int(skipped_no_response),
                        "prompt_count": int(len(prompt_records_payload)),
                        "skip_fraction": float(skip_fraction),
                    }
                ),
                flush=True,
            )

    try:
        vol.commit()
    except Exception:
        pass

    return metadata


@app.local_entrypoint()
def main(
    prompt_paths: str = "",
    dataset_name: str = "",
    layer: int = 12,
    capture_mode: str = DEFAULT_CAPTURE_MODE,
    condition_mode: str = DEFAULT_CONDITION_MODE,
    max_new_tokens: int = -1,
    temperature: float = -1.0,
    limit_per_file: int = 0,
    samples_per_shard: int = 0,
    seed: int = 0,
    model_name: str = "",
    overwrite: int = 0,
    output_suffix: str = "",
    dedupe: int = 1,
) -> None:
    experiment_config = _load_yaml(EXPERIMENT_CONFIG_PATH)
    sidecar_config = _load_yaml(SIDECAR_CONFIG_PATH)
    export_cfg = sidecar_config.get("glp_export", {}) if isinstance(sidecar_config.get("glp_export"), dict) else {}

    resolved_model_name = str(
        model_name
        or experiment_config.get("models", {}).get("primary", {}).get("name")
        or "meta-llama/Llama-3.1-8B-Instruct"
    )
    resolved_capture_mode = str(capture_mode or export_cfg.get("capture_mode", DEFAULT_CAPTURE_MODE))
    if resolved_capture_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"capture_mode must be one of {sorted(ALLOWED_CAPTURE_MODES)}")
    resolved_condition_mode = str(condition_mode or export_cfg.get("condition_mode", DEFAULT_CONDITION_MODE)).strip()
    if resolved_condition_mode and resolved_condition_mode not in ALLOWED_CAPTURE_MODES:
        raise ValueError(f"condition_mode must be one of {sorted(ALLOWED_CAPTURE_MODES)}")
    resolved_max_new_tokens = (
        int(max_new_tokens)
        if int(max_new_tokens) >= 0
        else int(export_cfg.get("max_new_tokens", DEFAULT_MAX_NEW_TOKENS))
    )
    resolved_temperature = (
        float(temperature)
        if float(temperature) >= 0.0
        else float(export_cfg.get("temperature", DEFAULT_TEMPERATURE))
    )
    resolved_samples_per_shard = (
        int(samples_per_shard)
        if int(samples_per_shard) > 0
        else int(export_cfg.get("samples_per_shard", DEFAULT_SAMPLES_PER_SHARD))
    )
    default_system_prompt = str(export_cfg.get("neutral_system_prompt", DEFAULT_NEUTRAL_SYSTEM_PROMPT))

    if prompt_paths.strip():
        resolved_prompt_paths = [Path(part.strip()) for part in prompt_paths.split(",") if part.strip()]
    else:
        resolved_prompt_paths = [Path(p) for p in export_cfg.get("prompt_paths", [])]
    if not resolved_prompt_paths:
        raise ValueError("No prompt_paths provided and no defaults configured")
    for path in resolved_prompt_paths:
        if not path.exists():
            raise FileNotFoundError(path)

    prompt_records = _build_prompt_records(
        prompt_paths=resolved_prompt_paths,
        default_system_prompt=default_system_prompt,
        limit_per_file=int(limit_per_file),
        seed=int(seed),
        dedupe=bool(int(dedupe)),
    )
    if not prompt_records:
        raise RuntimeError("No prompt records resolved for export")

    resolved_dataset_name = dataset_name or _default_dataset_name(
        model_name=resolved_model_name,
        layer=int(layer),
        capture_mode=resolved_capture_mode,
        prompt_count=len(prompt_records),
        condition_mode=resolved_condition_mode,
    )

    summary = export_memmap_dataset.remote(
        model_name=resolved_model_name,
        layer=int(layer),
        capture_mode=resolved_capture_mode,
        condition_mode=resolved_condition_mode,
        max_new_tokens=int(resolved_max_new_tokens),
        temperature=float(resolved_temperature),
        dataset_volume_subdir=resolved_dataset_name,
        prompt_records_payload=[record.__dict__ for record in prompt_records],
        samples_per_shard=int(resolved_samples_per_shard),
        overwrite=bool(int(overwrite)),
        seed=int(seed),
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{output_suffix.strip()}" if output_suffix.strip() else ""
    artifact_path = RESULTS_DIR / f"glp_export_memmap_dataset_{timestamp}{suffix}.json"
    artifact = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "glp_export_memmap_dataset_summary",
        "inputs": {
            "prompt_paths": [str(path) for path in resolved_prompt_paths],
            "prompt_hash": _hash_jsonable([record.__dict__ for record in prompt_records]),
            "model_name": resolved_model_name,
            "layer": int(layer),
            "capture_mode": resolved_capture_mode,
            "condition_mode": resolved_condition_mode or None,
            "max_new_tokens": int(resolved_max_new_tokens),
            "temperature": float(resolved_temperature),
            "limit_per_file": int(limit_per_file),
            "samples_per_shard": int(resolved_samples_per_shard),
            "seed": int(seed),
            "dedupe": bool(int(dedupe)),
            "dataset_name": resolved_dataset_name,
        },
        "export_summary": summary,
    }
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps({"artifact_path": str(artifact_path), "dataset_dir": summary["dataset_dir"]}, indent=2))
