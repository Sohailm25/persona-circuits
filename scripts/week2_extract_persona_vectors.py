"""Week 2 Days 1-3: contrastive persona-vector extraction on Llama-3.1-8B-Instruct."""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

APP_NAME = "persona-circuits-week2-extract-vectors"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ["sycophancy", "evil", "hallucination"]

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
INFRA_AUDIT_PATH = ROOT / "results" / "infrastructure" / "week1_prompt_audit_report.json"
EXPERIMENT_CONFIG_PATH = ROOT / "configs" / "experiment.yaml"

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "wandb",
        "numpy",
    ]
)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _set_modal_cache_env() -> None:
    os.environ["HF_HOME"] = "/models/huggingface"
    os.environ["TRANSFORMERS_CACHE"] = "/models/huggingface"
    os.environ["HF_HUB_CACHE"] = "/models/huggingface"
    os.environ["HUGGINGFACE_HUB_CACHE"] = "/models/huggingface"
    Path("/models/huggingface").mkdir(parents=True, exist_ok=True)
    Path("/models/persona-circuits/week2").mkdir(parents=True, exist_ok=True)


def _format_chat_prompt(tokenizer: Any, system_prompt: str, user_query: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except (TypeError, ValueError):
            pass
    return f"System: {system_prompt}\nUser: {user_query}\nAssistant:"


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(EXPERIMENT_CONFIG_PATH.read_text(encoding="utf-8"))


def _load_prompt_pairs(traits: list[str]) -> dict[str, list[dict[str, Any]]]:
    prompt_pairs: dict[str, list[dict[str, Any]]] = {}
    for trait in traits:
        path = PROMPTS_DIR / f"{trait}_pairs.jsonl"
        rows = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        prompt_pairs[trait] = rows
    return prompt_pairs


def _assert_prompt_audit_passed() -> None:
    if not INFRA_AUDIT_PATH.exists():
        raise FileNotFoundError(
            "Prompt audit report is missing. Run scripts/audit_prompt_datasets.py first."
        )
    report = json.loads(INFRA_AUDIT_PATH.read_text(encoding="utf-8"))
    if not report.get("overall_pass", False):
        raise RuntimeError(
            "Prompt audit is not passing. Fix prompt defects before Week 2 extraction."
        )


def _local_spot_check(
    prompt_pairs: dict[str, list[dict[str, Any]]],
    trait: str,
    layer: int,
    model_name: str,
) -> None:
    import torch
    from sae_lens import HookedSAETransformer

    record = prompt_pairs[trait][0]
    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cpu",
        dtype=torch.float32,
    )
    hook_name = f"blocks.{layer}.hook_resid_post"
    hook_set = {hook_name}
    high_prompt = _format_chat_prompt(model.tokenizer, record["system_high"], record["user_query"])
    low_prompt = _format_chat_prompt(model.tokenizer, record["system_low"], record["user_query"])

    with torch.no_grad():
        high_tokens = model.to_tokens(high_prompt, prepend_bos=True)
        low_tokens = model.to_tokens(low_prompt, prepend_bos=True)
        _, high_cache = model.run_with_cache(high_tokens, names_filter=lambda name: name in hook_set)
        _, low_cache = model.run_with_cache(low_tokens, names_filter=lambda name: name in hook_set)
        high = high_cache[hook_name][0, -1, :].to(torch.float32)
        low = low_cache[hook_name][0, -1, :].to(torch.float32)
        diff = high - low

    print(
        json.dumps(
            {
                "mode": "local_spot_check",
                "trait": trait,
                "model_name": model_name,
                "layer": layer,
                "hook": hook_name,
                "activation_shape": list(high.shape),
                "diff_norm": float(diff.norm().item()),
                "nonzero_dims": int((diff != 0).sum().item()),
            },
            indent=2,
        )
    )


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("wandb-key"),
    ],
    volumes={"/models": vol},
)
def extract_vectors_remote(
    *,
    config: dict[str, Any],
    prompt_pairs: dict[str, list[dict[str, Any]]],
    traits: list[str],
    layers: list[int],
    run_name: str | None = None,
) -> dict[str, Any]:
    import torch
    import torch.nn.functional as F
    import wandb
    from sae_lens import HookedSAETransformer

    _set_modal_cache_env()
    seed = int(config["seeds"]["primary"])
    _seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    model_name = str(config["models"]["primary"]["name"])
    wandb_cfg = config["wandb"]
    run = wandb.init(
        project=wandb_cfg["project"],
        entity=wandb_cfg["entity"],
        job_type="stage1_extraction",
        name=run_name
        or f"week2-stage1-extract-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        config={
            "phase": "week2_day1_3_extraction",
            "model_name": model_name,
            "traits": traits,
            "layers": layers,
            "seed": seed,
        },
    )

    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    layer_hooks = {layer: f"blocks.{layer}.hook_resid_post" for layer in layers}
    hook_name_set = set(layer_hooks.values())

    vectors: dict[str, dict[str, list[float]]] = {}
    diagnostics: dict[str, Any] = {}

    for trait in traits:
        rows = prompt_pairs[trait]
        high_by_layer = {layer: [] for layer in layers}
        low_by_layer = {layer: [] for layer in layers}

        for row in rows:
            high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])
            low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])

            with torch.no_grad():
                high_tokens = model.to_tokens(high_prompt, prepend_bos=True)
                low_tokens = model.to_tokens(low_prompt, prepend_bos=True)
                _, high_cache = model.run_with_cache(
                    high_tokens,
                    names_filter=lambda name: name in hook_name_set,
                )
                _, low_cache = model.run_with_cache(
                    low_tokens,
                    names_filter=lambda name: name in hook_name_set,
                )

                for layer, hook_name in layer_hooks.items():
                    high_by_layer[layer].append(high_cache[hook_name][0, -1, :].to(torch.float32).cpu())
                    low_by_layer[layer].append(low_cache[hook_name][0, -1, :].to(torch.float32).cpu())

        vectors[trait] = {}
        diagnostics[trait] = {"layers": {}}
        best_layer = None
        best_gap = float("-inf")

        for layer in layers:
            high_stack = torch.stack(high_by_layer[layer], dim=0)
            low_stack = torch.stack(low_by_layer[layer], dim=0)
            raw_diff = high_stack.mean(dim=0) - low_stack.mean(dim=0)
            raw_norm = float(raw_diff.norm().item())
            if raw_norm <= 0.0:
                raise RuntimeError(f"Zero-norm persona vector for trait={trait} layer={layer}")

            unit = raw_diff / raw_norm
            proj_high = high_stack @ unit
            proj_low = low_stack @ unit
            pair_margin = proj_high - proj_low
            mean_margin = float(pair_margin.mean().item())
            std_margin = float(pair_margin.std(unbiased=False).item())
            diff_cos = F.cosine_similarity(high_stack - low_stack, unit.unsqueeze(0), dim=1)
            mean_pair_cos = float(diff_cos.mean().item())

            vectors[trait][str(layer)] = unit.tolist()
            diagnostics[trait]["layers"][str(layer)] = {
                "n_pairs": len(rows),
                "raw_vector_norm": raw_norm,
                "unit_vector_norm": float(unit.norm().item()),
                "projection_margin_mean": mean_margin,
                "projection_margin_std": std_margin,
                "mean_pair_diff_cosine_to_vector": mean_pair_cos,
            }
            if mean_margin > best_gap:
                best_gap = mean_margin
                best_layer = layer

            wandb.log(
                {
                    f"extraction/{trait}/layer_{layer}/raw_vector_norm": raw_norm,
                    f"extraction/{trait}/layer_{layer}/projection_margin_mean": mean_margin,
                    f"extraction/{trait}/layer_{layer}/projection_margin_std": std_margin,
                    f"extraction/{trait}/layer_{layer}/mean_pair_diff_cos": mean_pair_cos,
                }
            )

        diagnostics[trait]["prelim_best_layer_by_margin"] = best_layer
        wandb.log(
            {
                f"extraction/{trait}/prelim_best_layer": best_layer,
                f"extraction/{trait}/prelim_best_margin": best_gap,
            }
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_summary_path = Path("/models/persona-circuits/week2") / f"vector_extraction_summary_{timestamp}.json"
    modal_vectors_path = Path("/models/persona-circuits/week2") / f"persona_vectors_{timestamp}.pt"

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": model_name,
        "traits": traits,
        "layers": layers,
        "seed": seed,
        "diagnostics": diagnostics,
    }
    modal_summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    torch.save(
        {
            trait: {int(layer): torch.tensor(vec, dtype=torch.float32) for layer, vec in by_layer.items()}
            for trait, by_layer in vectors.items()
        },
        modal_vectors_path,
    )

    artifact = wandb.Artifact("week2-persona-vectors-prelim", type="stage1_extraction")
    artifact.add_file(str(modal_summary_path))
    artifact.add_file(str(modal_vectors_path))
    run.log_artifact(artifact)
    run.finish()

    return {
        "summary": summary,
        "vectors": vectors,
        "modal_artifacts": {
            "summary_path": str(modal_summary_path),
            "vectors_path": str(modal_vectors_path),
        },
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    layers: str = "",
    run_name: str = "",
    local_spot_check_model: str = "",
    local_spot_check_trait: str = "sycophancy",
    local_spot_check_layer: int = 1,
) -> None:
    selected_traits = [t.strip() for t in traits.split(",") if t.strip()]
    config = _load_config()

    if not selected_traits:
        raise ValueError("No traits selected.")

    prompt_pairs = _load_prompt_pairs(selected_traits)
    if local_spot_check_model:
        _local_spot_check(
            prompt_pairs=prompt_pairs,
            trait=local_spot_check_trait,
            layer=local_spot_check_layer,
            model_name=local_spot_check_model,
        )
        return

    _assert_prompt_audit_passed()

    candidate_layers = (
        [int(x) for x in layers.split(",") if x.strip()]
        if layers.strip()
        else list(config["models"]["primary"]["optimal_steering_layers"])
    )
    if not candidate_layers:
        raise ValueError("No candidate layers provided.")

    result = extract_vectors_remote.remote(
        config=config,
        prompt_pairs=prompt_pairs,
        traits=selected_traits,
        layers=candidate_layers,
        run_name=run_name or None,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = RESULTS_DIR / f"week2_vector_extraction_summary_{timestamp}.json"
    vectors_path = RESULTS_DIR / f"week2_persona_vectors_{timestamp}.pt"

    summary_path.write_text(json.dumps(result["summary"], indent=2), encoding="utf-8")
    import torch

    torch.save(
        {
            trait: {int(layer): torch.tensor(vec, dtype=torch.float32) for layer, vec in by_layer.items()}
            for trait, by_layer in result["vectors"].items()
        },
        vectors_path,
    )

    print(
        json.dumps(
            {
                "summary_path": str(summary_path),
                "vectors_path": str(vectors_path),
                "modal_artifacts": result["modal_artifacts"],
                "traits": selected_traits,
                "layers": candidate_layers,
            },
            indent=2,
        )
    )
