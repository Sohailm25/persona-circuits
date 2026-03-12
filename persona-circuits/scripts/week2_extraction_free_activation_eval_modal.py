"""Week 2: Modal runner for extraction-free activation evaluation."""

from __future__ import annotations

import json
import math
import os
import random
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import torch
import yaml

APP_NAME = "persona-circuits-week2-extraction-free-activation-eval"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ["sycophancy", "evil", "hallucination"]
ROW_KEYS = ("id", "source_row_id", "category")
REQUIRED_GATES = (
    "mean_cosine",
    "positive_fraction",
    "projection_delta",
    "set_count",
    "set_mean_cv",
    "std_control",
    "non_empty_rows",
    "non_empty_set_stats",
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
PROMPTS_DIR = ROOT / "prompts" / "heldout"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "numpy",
        "pyyaml",
    ]
)


@dataclass
class EvalArgs:
    eval_dir: Path
    eval_suffix: str
    limit_per_trait: int
    cosine_threshold: float
    min_positive_fraction: float
    directional_threshold: float
    min_set_count: int
    max_set_mean_cv: float
    max_set_std_ratio: float
    max_cosine_std: float
    seed: int


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
    Path("/models/persona-circuits/week2").mkdir(parents=True, exist_ok=True)


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {pattern}")
    return matches[-1]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _format_chat_prompt(
    tokenizer: Any,
    system_prompt: str,
    examples: list[dict[str, str]],
    user_query: str,
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for example in examples:
        messages.append({"role": "user", "content": example.get("user", "")})
        messages.append({"role": "assistant", "content": example.get("assistant", "")})
    messages.append({"role": "user", "content": user_query})
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except (TypeError, ValueError):
            pass
    return "\n".join(
        f"{msg['role'].capitalize()}: {msg['content'].strip()}"
        for msg in messages
        if msg["content"].strip()
    )


def _capture_activation(model: Any, prompt: str, hook_name: str) -> torch.Tensor:
    tokens = model.to_tokens(prompt, prepend_bos=True)
    _, cache = model.run_with_cache(tokens, names_filter=lambda name: name in {hook_name})
    return cache[hook_name][0, -1, :].detach().to(torch.float32)


def _fewshot_signature(high: list[dict[str, str]], low: list[dict[str, str]]) -> str:
    canonical = json.dumps({"high": high, "low": low}, sort_keys=True, ensure_ascii=True)
    return __import__("hashlib").sha256(canonical.encode("utf-8")).hexdigest()


def _stats(values: Iterable[float]) -> dict[str, Any]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return {"mean": None, "median": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _binomial_two_sided_p_value(n_trials: int, n_success: int, p_success: float = 0.5) -> float | None:
    if n_trials <= 0:
        return None
    lower_tail = 0.0
    upper_tail = 0.0
    for i in range(0, n_success + 1):
        lower_tail += math.comb(n_trials, i) * (p_success ** i) * ((1.0 - p_success) ** (n_trials - i))
    for i in range(n_success, n_trials + 1):
        upper_tail += math.comb(n_trials, i) * (p_success ** i) * ((1.0 - p_success) ** (n_trials - i))
    return float(min(1.0, 2.0 * min(lower_tail, upper_tail)))


def _ttest_vs_zero_normal_approx(values: Iterable[float]) -> dict[str, Any]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return {
            "n": 0,
            "mean": None,
            "sample_std": None,
            "t_stat": None,
            "p_value_two_sided_normal_approx": None,
        }
    mean = float(np.mean(arr))
    if arr.size < 2:
        return {
            "n": int(arr.size),
            "mean": mean,
            "sample_std": None,
            "t_stat": None,
            "p_value_two_sided_normal_approx": None,
        }
    sample_std = float(np.std(arr, ddof=1))
    if sample_std <= 1e-12:
        return {
            "n": int(arr.size),
            "mean": mean,
            "sample_std": sample_std,
            "t_stat": None,
            "p_value_two_sided_normal_approx": None,
        }
    se = sample_std / math.sqrt(float(arr.size))
    t_stat = mean / se if se > 0 else 0.0
    p_value = float(math.erfc(abs(t_stat) / math.sqrt(2.0)))
    return {
        "n": int(arr.size),
        "mean": mean,
        "sample_std": sample_std,
        "t_stat": float(t_stat),
        "p_value_two_sided_normal_approx": p_value,
    }


def _bootstrap_mean_ci(values: Iterable[float], *, seed: int, n_bootstrap: int = 4000) -> dict[str, Any]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return {"n": 0, "n_bootstrap": int(n_bootstrap), "mean_ci95": None}
    rng = np.random.default_rng(seed)
    draws = rng.choice(arr, size=(n_bootstrap, arr.size), replace=True)
    means = np.mean(draws, axis=1)
    return {
        "n": int(arr.size),
        "n_bootstrap": int(n_bootstrap),
        "mean_ci95": {
            "lower": float(np.percentile(means, 2.5)),
            "upper": float(np.percentile(means, 97.5)),
        },
    }


def _parse_layer_arg(input_value: str, trait_count: int) -> list[int]:
    parsed = [p.strip() for p in input_value.split(",") if p.strip()]
    if not parsed:
        raise ValueError("layer argument is empty")
    if len(parsed) == 1:
        return [int(parsed[0])] * trait_count
    if len(parsed) != trait_count:
        raise ValueError("layer list length must match trait count")
    return [int(p) for p in parsed]


def _project_onto(vec: np.ndarray, direction: np.ndarray) -> float:
    return float(np.dot(vec, direction))


def _ensure_division(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _load_vectors(path: Path) -> dict[str, dict[int, np.ndarray]]:
    payload = torch.load(path, map_location="cpu")
    parsed: dict[str, dict[int, np.ndarray]] = {}
    for trait, layers in payload.items():
        parsed[trait] = {}
        for layer, value in layers.items():
            parsed[trait][int(layer)] = np.asarray(value, dtype=np.float64)
    return parsed


def _serialize_vectors_for_remote(vectors: dict[str, dict[int, np.ndarray]]) -> dict[str, dict[str, list[float]]]:
    out: dict[str, dict[str, list[float]]] = {}
    for trait, by_layer in vectors.items():
        out[trait] = {}
        for layer, arr in by_layer.items():
            out[trait][str(layer)] = np.asarray(arr, dtype=np.float64).tolist()
    return out


def _deserialize_vectors_from_payload(
    payload: dict[str, dict[str, list[float]]],
) -> dict[str, dict[int, np.ndarray]]:
    out: dict[str, dict[int, np.ndarray]] = {}
    for trait, by_layer in payload.items():
        out[trait] = {}
        for layer, values in by_layer.items():
            out[trait][int(layer)] = np.asarray(values, dtype=np.float64)
    return out


def _evaluate_trait(
    trait: str,
    layer: int,
    persona_vectors: dict[str, dict[int, np.ndarray]],
    eval_rows: list[dict[str, Any]],
    model: Any,
    tokenizer: Any,
    args: EvalArgs,
) -> dict[str, Any]:
    persona_by_layer = persona_vectors.get(trait, {})
    if layer not in persona_by_layer:
        raise KeyError(f"trait={trait} missing vector for layer {layer}")

    persona_vec = persona_by_layer[layer]
    norm = float(np.linalg.norm(persona_vec))
    if norm <= 1e-10:
        raise ValueError(f"zero-norm persona vector for trait={trait} layer={layer}")
    persona_dir = persona_vec / norm

    rows = list(eval_rows)
    if args.limit_per_trait > 0:
        rows = rows[: args.limit_per_trait]

    hook_name = f"blocks.{layer}.hook_resid_post"
    row_summaries: list[dict[str, Any]] = []
    cosines: list[float] = []
    projection_deltas: list[float] = []
    set_buckets: dict[str, list[float]] = {}

    for row in rows:
        high_prompt = _format_chat_prompt(
            tokenizer,
            row.get("neutral_system_prompt", ""),
            row.get("fewshot_high", []),
            row.get("user_query", ""),
        )
        low_prompt = _format_chat_prompt(
            tokenizer,
            row.get("neutral_system_prompt", ""),
            row.get("fewshot_low", []),
            row.get("user_query", ""),
        )
        with torch.no_grad():
            high_act = _capture_activation(model, high_prompt, hook_name).cpu()
            low_act = _capture_activation(model, low_prompt, hook_name).cpu()

        delta = high_act - low_act
        delta_np = delta.numpy()
        delta_norm = float(torch.norm(delta).item())
        cosine = _ensure_division(float(np.dot(delta_np, persona_dir)), delta_norm)
        high_proj = _project_onto(high_act.numpy(), persona_dir)
        low_proj = _project_onto(low_act.numpy(), persona_dir)
        projection_delta = high_proj - low_proj
        explicit_set_id = str(row.get("fewshot_set_id", "")).strip()
        set_id = explicit_set_id or _fewshot_signature(row.get("fewshot_high", []), row.get("fewshot_low", []))

        cosines.append(cosine)
        projection_deltas.append(projection_delta)
        set_buckets.setdefault(set_id, []).append(cosine)

        row_summaries.append(
            {key: row.get(key) for key in ROW_KEYS}
            | {
                "cosine": cosine,
                "projection_delta": projection_delta,
                "fewshot_set_id": set_id,
                "fewshot_selection_hash": row.get("fewshot_selection_hash"),
            }
        )

    set_stats = []
    set_means = []
    set_stds = []
    for signature, bucket in set_buckets.items():
        arr = np.asarray(bucket, dtype=np.float64)
        set_stats.append(
            {
                "signature": signature,
                "count": int(arr.size),
                "mean_cosine": float(np.mean(arr)),
                "std_cosine": float(np.std(arr)),
            }
        )
        set_means.append(float(np.mean(arr)))
        set_stds.append(float(np.std(arr)))

    global_std = float(np.std(cosines)) if cosines else 0.0
    max_set_std = float(max(set_stds)) if set_stds else 0.0
    set_std_ratio = _ensure_division(max_set_std, global_std)
    set_mean_arr = np.asarray(set_means, dtype=np.float64) if set_means else np.asarray([], dtype=np.float64)

    cosine_stats = _stats(cosines)
    projection_stats = _stats(projection_deltas)
    positive_fraction = float(np.mean(np.asarray([c > 0 for c in cosines]))) if cosines else 0.0
    set_mean_std = float(np.std(set_mean_arr)) if set_mean_arr.size else 0.0
    global_mean_abs = abs(float(cosine_stats["mean"])) if cosine_stats["mean"] is not None else 0.0
    set_mean_cv = _ensure_division(set_mean_std, global_mean_abs)
    set_mean_positive_fraction = float(np.mean(set_mean_arr > 0.0)) if set_mean_arr.size else 0.0
    set_mean_range = float(np.max(set_mean_arr) - np.min(set_mean_arr)) if set_mean_arr.size else 0.0
    n_positive = int(np.sum(np.asarray(cosines, dtype=np.float64) > 0.0)) if cosines else 0
    sign_test_p = _binomial_two_sided_p_value(len(cosines), n_positive, p_success=0.5)
    ttest_summary = _ttest_vs_zero_normal_approx(cosines)
    bootstrap_summary = _bootstrap_mean_ci(
        cosines,
        seed=int(args.seed) + int(layer) * 1009 + len(trait),
        n_bootstrap=4000,
    )
    ci95 = bootstrap_summary.get("mean_ci95")
    mean_ci_excludes_zero = bool(ci95 is not None and ci95["lower"] > 0.0)

    gate_map = {
        "mean_cosine": cosine_stats["mean"] is not None and cosine_stats["mean"] >= args.cosine_threshold,
        "positive_fraction": positive_fraction >= args.min_positive_fraction,
        "projection_delta": projection_stats["mean"] is not None
        and projection_stats["mean"] >= args.directional_threshold,
        "set_count": len(set_stats) >= args.min_set_count,
        "set_mean_cv": set_mean_cv <= args.max_set_mean_cv,
        "legacy_set_std_ratio": set_std_ratio <= args.max_set_std_ratio,
        "std_control": global_std <= args.max_cosine_std,
        "non_empty_rows": len(rows) > 0,
        "non_empty_set_stats": len(set_stats) > 0,
    }
    gate_map["mean_ci_excludes_zero"] = mean_ci_excludes_zero
    passes = all(bool(gate_map.get(name, False)) for name in REQUIRED_GATES)

    return {
        "evidence_status": {
            "activation_deltas": "observed",
            "set_variance": "observed",
            "gate_interpretation": "inferred",
        },
        "n_rows": len(rows),
        "cosine_stats": cosine_stats,
        "projection_delta_stats": projection_stats,
        "positive_cosine_fraction": positive_fraction,
        "global_cosine_std": global_std,
        "set_variance": {
            "unique_sets": len(set_stats),
            "set_std_ratio": set_std_ratio,
            "set_mean_std": set_mean_std,
            "set_mean_cv": set_mean_cv,
            "set_mean_range": set_mean_range,
            "set_mean_positive_fraction": set_mean_positive_fraction,
            "set_means_all_positive": bool(set_mean_arr.size > 0 and np.all(set_mean_arr > 0.0)),
            "per_set_stats": set_stats,
        },
        "alignment_significance": {
            "n_positive_cosines": n_positive,
            "sign_test_two_sided_p": sign_test_p,
            "ttest_vs_zero": ttest_summary,
            "mean_bootstrap_ci95": ci95,
            "mean_ci_excludes_zero": mean_ci_excludes_zero,
        },
        "rows": row_summaries,
        "gates": gate_map,
        "required_gates": list(REQUIRED_GATES),
        "passes": passes,
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_eval_remote(
    *,
    traits: list[str],
    layer_list: list[int],
    model_name: str,
    vectors_payload: dict[str, dict[str, list[float]]],
    eval_rows_payload: dict[str, list[dict[str, Any]]],
    limit_per_trait: int,
    cosine_threshold: float,
    min_positive_fraction: float,
    directional_threshold: float,
    min_set_count: int,
    max_set_mean_cv: float,
    max_set_std_ratio: float,
    max_cosine_std: float,
    seed: int,
) -> dict[str, Any]:
    from sae_lens import HookedSAETransformer

    _set_modal_cache_env()
    _seed_everything(seed)

    persona_vectors = _deserialize_vectors_from_payload(vectors_payload)
    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    tokenizer = model.tokenizer

    eval_args = EvalArgs(
        eval_dir=Path("/dev/null"),
        eval_suffix="",
        limit_per_trait=limit_per_trait,
        cosine_threshold=cosine_threshold,
        min_positive_fraction=min_positive_fraction,
        directional_threshold=directional_threshold,
        min_set_count=min_set_count,
        max_set_mean_cv=max_set_mean_cv,
        max_set_std_ratio=max_set_std_ratio,
        max_cosine_std=max_cosine_std,
        seed=seed,
    )

    results: dict[str, Any] = {}
    for trait, layer in zip(traits, layer_list):
        if trait not in eval_rows_payload:
            raise KeyError(f"Missing eval rows payload for trait={trait}")
        results[trait] = _evaluate_trait(
            trait=trait,
            layer=layer,
            persona_vectors=persona_vectors,
            eval_rows=eval_rows_payload[trait],
            model=model,
            tokenizer=tokenizer,
            args=eval_args,
        )

    artifact = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": {
            "trait_metrics": "observed",
            "overall_pass": "inferred",
        },
        "model": model_name,
        "layer_map": dict(zip(traits, layer_list)),
        "vector_artifact": "in_memory_payload_from_local_vectors",
        "seed": int(seed),
        "traits": results,
        "overall_pass": all(val["passes"] for val in results.values()),
        "gates": {trait: val["gates"] for trait, val in results.items()},
        "gate_policy": {
            "version": "v2_overlap_gradient",
            "required_gates": list(REQUIRED_GATES),
            "thresholds": {
                "mean_cosine_min": float(cosine_threshold),
                "positive_fraction_min": float(min_positive_fraction),
                "projection_delta_min": float(directional_threshold),
                "set_count_min": int(min_set_count),
                "set_mean_cv_max": float(max_set_mean_cv),
                "max_cosine_std": float(max_cosine_std),
                "legacy_set_std_ratio_max": float(max_set_std_ratio),
            },
        },
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_out = Path("/models/persona-circuits/week2") / f"extraction_free_activation_eval_{timestamp}.json"
    modal_out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    return {
        "artifact": artifact,
        "modal_artifact_path": str(modal_out),
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    layer: str = "16",
    model_name: str = "",
    vectors_path: str = "",
    eval_dir: str = str(PROMPTS_DIR),
    eval_suffix: str = "v2_rotating_20260225",
    limit_per_trait: int = 0,
    cosine_threshold: float = 0.1,
    min_positive_fraction: float = 0.75,
    directional_threshold: float = 0.15,
    min_set_count: int = 2,
    max_set_mean_cv: float = 0.8,
    max_set_std_ratio: float = 0.8,
    max_cosine_std: float = 0.35,
    seed: int = 42,
) -> None:
    selected_traits = [t.strip() for t in traits.split(",") if t.strip()]
    if not selected_traits:
        raise ValueError("At least one trait must be configured.")

    normalized_suffix = eval_suffix.strip()
    if normalized_suffix and not normalized_suffix.startswith("_"):
        normalized_suffix = f"_{normalized_suffix}"

    layer_list = _parse_layer_arg(layer, len(selected_traits))
    config = _load_config()
    selected_model = model_name or str(config["models"]["primary"]["name"])

    vector_path = (
        Path(vectors_path)
        if vectors_path
        else _latest_result_path("week2_persona_vectors_*.pt")
    )
    local_vectors = _load_vectors(vector_path)
    vectors_payload = _serialize_vectors_for_remote(local_vectors)

    result = run_eval_remote.remote(
        traits=selected_traits,
        layer_list=layer_list,
        model_name=selected_model,
        vectors_payload=vectors_payload,
        eval_rows_payload={
            trait: _load_jsonl(Path(eval_dir) / f"{trait}_extraction_free_eval{normalized_suffix}.jsonl")
            for trait in selected_traits
        },
        limit_per_trait=int(limit_per_trait),
        cosine_threshold=float(cosine_threshold),
        min_positive_fraction=float(min_positive_fraction),
        directional_threshold=float(directional_threshold),
        min_set_count=int(min_set_count),
        max_set_mean_cv=float(max_set_mean_cv),
        max_set_std_ratio=float(max_set_std_ratio),
        max_cosine_std=float(max_cosine_std),
        seed=int(seed),
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_extraction_free_activation_eval_{timestamp}.json"
    out_path.write_text(json.dumps(result["artifact"], indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "artifact_path": str(out_path),
                "modal_artifact_path": result["modal_artifact_path"],
                "overall_pass": result["artifact"]["overall_pass"],
                "traits": selected_traits,
                "layers": layer_list,
                "eval_suffix": normalized_suffix,
            },
            indent=2,
        )
    )
