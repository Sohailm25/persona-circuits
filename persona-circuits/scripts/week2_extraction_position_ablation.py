"""Week 2 remediation: extraction-position robustness diagnostics across layers."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import torch
import yaml

APP_NAME = "persona-circuits-week2-extraction-position-ablation"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ("sycophancy", "evil", "hallucination")
DEFAULT_MAX_NEW_TOKENS = 96
DEFAULT_TEMPERATURE = 0.0

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
PROMPTS_DIR = ROOT / "prompts"
EXPERIMENT_CONFIG_PATH = ROOT / "configs" / "experiment.yaml"

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


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(EXPERIMENT_CONFIG_PATH.read_text(encoding="utf-8"))


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _format_chat_prompt(tokenizer: Any, system_prompt: str, user_query: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def _load_extraction_rows(trait: str) -> list[dict[str, Any]]:
    path = PROMPTS_DIR / f"{trait}_pairs.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Missing extraction prompt file: {path}")
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise ValueError(f"No rows in extraction prompt file: {path}")
    return rows


def _unit(vec: torch.Tensor) -> torch.Tensor:
    return vec / (vec.norm() + 1e-8)


def _cos(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(_unit(a).unsqueeze(0), _unit(b).unsqueeze(0)).item())


def _method_metrics(high_stack: torch.Tensor, low_stack: torch.Tensor) -> dict[str, Any]:
    vec = high_stack.mean(dim=0) - low_stack.mean(dim=0)
    unit = _unit(vec)
    margin = high_stack @ unit - low_stack @ unit
    return {
        "vector_norm": float(vec.norm().item()),
        "projection_margin_mean": float(margin.mean().item()),
        "projection_margin_std": float(margin.std(unbiased=False).item()),
        "vector": vec,
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_position_ablation_remote(
    *,
    config: dict[str, Any],
    traits: list[str],
    layers: list[int],
    extraction_rows_by_trait: dict[str, list[dict[str, Any]]],
    extraction_pairs: int,
    max_new_tokens: int,
    temperature: float,
    seed: int,
) -> dict[str, Any]:
    from sae_lens import HookedSAETransformer

    _seed_everything(seed)
    model_name = str(config["models"]["primary"]["name"])
    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )

    layer_hooks = {layer: f"blocks.{layer}.hook_resid_post" for layer in layers}
    hook_set = set(layer_hooks.values())
    output: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": model_name,
        "traits": traits,
        "layers": layers,
        "extraction_pairs_per_trait": int(extraction_pairs),
        "max_new_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "seed": int(seed),
        "diagnostics": {},
    }

    for trait in traits:
        rows_all = extraction_rows_by_trait.get(trait, [])
        if not rows_all:
            raise ValueError(f"No extraction rows provided for trait: {trait}")
        rng = random.Random(seed + len(trait) * 31)
        if len(rows_all) > extraction_pairs:
            idxs = list(range(len(rows_all)))
            rng.shuffle(idxs)
            rows = [rows_all[i] for i in idxs[:extraction_pairs]]
        else:
            rows = rows_all

        method_high = {
            "prompt_last": {layer: [] for layer in layers},
            "response_mean": {layer: [] for layer in layers},
            "response_last": {layer: [] for layer in layers},
        }
        method_low = {
            "prompt_last": {layer: [] for layer in layers},
            "response_mean": {layer: [] for layer in layers},
            "response_last": {layer: [] for layer in layers},
        }

        for row in rows:
            high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])
            low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])

            with torch.no_grad():
                high_tokens = model.to_tokens(high_prompt, prepend_bos=True)
                low_tokens = model.to_tokens(low_prompt, prepend_bos=True)
                _, high_cache = model.run_with_cache(
                    high_tokens,
                    names_filter=lambda name: name in hook_set,
                )
                _, low_cache = model.run_with_cache(
                    low_tokens,
                    names_filter=lambda name: name in hook_set,
                )
                for layer, hook_name in layer_hooks.items():
                    method_high["prompt_last"][layer].append(
                        high_cache[hook_name][0, -1, :].to(torch.float32).cpu()
                    )
                    method_low["prompt_last"][layer].append(
                        low_cache[hook_name][0, -1, :].to(torch.float32).cpu()
                    )

                high_gen = model.generate(
                    high_tokens,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=None,
                    stop_at_eos=True,
                    verbose=False,
                )
                low_gen = model.generate(
                    low_tokens,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=None,
                    stop_at_eos=True,
                    verbose=False,
                )
                _, high_gen_cache = model.run_with_cache(
                    high_gen,
                    names_filter=lambda name: name in hook_set,
                )
                _, low_gen_cache = model.run_with_cache(
                    low_gen,
                    names_filter=lambda name: name in hook_set,
                )
                high_prompt_len = int(high_tokens.shape[1])
                low_prompt_len = int(low_tokens.shape[1])
                for layer, hook_name in layer_hooks.items():
                    high_resp = high_gen_cache[hook_name][0, high_prompt_len:, :].to(torch.float32)
                    low_resp = low_gen_cache[hook_name][0, low_prompt_len:, :].to(torch.float32)
                    if high_resp.shape[0] == 0:
                        high_resp = high_gen_cache[hook_name][0, -1:, :].to(torch.float32)
                    if low_resp.shape[0] == 0:
                        low_resp = low_gen_cache[hook_name][0, -1:, :].to(torch.float32)
                    method_high["response_mean"][layer].append(high_resp.mean(dim=0).cpu())
                    method_low["response_mean"][layer].append(low_resp.mean(dim=0).cpu())
                    method_high["response_last"][layer].append(high_resp[-1, :].cpu())
                    method_low["response_last"][layer].append(low_resp[-1, :].cpu())

        per_layer: dict[str, Any] = {}
        prompt_response_cosines: list[float] = []
        for layer in layers:
            prompt_metrics = _method_metrics(
                torch.stack(method_high["prompt_last"][layer], dim=0),
                torch.stack(method_low["prompt_last"][layer], dim=0),
            )
            response_mean_metrics = _method_metrics(
                torch.stack(method_high["response_mean"][layer], dim=0),
                torch.stack(method_low["response_mean"][layer], dim=0),
            )
            response_last_metrics = _method_metrics(
                torch.stack(method_high["response_last"][layer], dim=0),
                torch.stack(method_low["response_last"][layer], dim=0),
            )
            cos_prompt_resp_mean = _cos(prompt_metrics["vector"], response_mean_metrics["vector"])
            cos_prompt_resp_last = _cos(prompt_metrics["vector"], response_last_metrics["vector"])
            cos_resp_mean_resp_last = _cos(response_mean_metrics["vector"], response_last_metrics["vector"])
            prompt_response_cosines.append(cos_prompt_resp_mean)
            per_layer[str(layer)] = {
                "n_pairs": len(rows),
                "methods": {
                    "prompt_last": {
                        "vector_norm": prompt_metrics["vector_norm"],
                        "projection_margin_mean": prompt_metrics["projection_margin_mean"],
                        "projection_margin_std": prompt_metrics["projection_margin_std"],
                    },
                    "response_mean": {
                        "vector_norm": response_mean_metrics["vector_norm"],
                        "projection_margin_mean": response_mean_metrics["projection_margin_mean"],
                        "projection_margin_std": response_mean_metrics["projection_margin_std"],
                    },
                    "response_last": {
                        "vector_norm": response_last_metrics["vector_norm"],
                        "projection_margin_mean": response_last_metrics["projection_margin_mean"],
                        "projection_margin_std": response_last_metrics["projection_margin_std"],
                    },
                },
                "pairwise_cosines": {
                    "prompt_last_vs_response_mean": cos_prompt_resp_mean,
                    "prompt_last_vs_response_last": cos_prompt_resp_last,
                    "response_mean_vs_response_last": cos_resp_mean_resp_last,
                },
                "passes": {
                    "prompt_last_vs_response_mean_ge_0_7": bool(cos_prompt_resp_mean >= 0.7),
                    "prompt_last_vs_response_last_ge_0_7": bool(cos_prompt_resp_last >= 0.7),
                    "response_mean_vs_response_last_ge_0_7": bool(cos_resp_mean_resp_last >= 0.7),
                },
            }

        output["diagnostics"][trait] = {
            "layers": per_layer,
            "summary": {
                "prompt_last_vs_response_mean": {
                    "mean": float(sum(prompt_response_cosines) / len(prompt_response_cosines)),
                    "min": float(min(prompt_response_cosines)),
                    "max": float(max(prompt_response_cosines)),
                    "all_layers_ge_0_7": bool(all(x >= 0.7 for x in prompt_response_cosines)),
                    "any_layer_ge_0_7": bool(any(x >= 0.7 for x in prompt_response_cosines)),
                }
            },
        }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    modal_report_path = Path("/models/persona-circuits/week2") / f"extraction_position_ablation_{timestamp}.json"
    modal_report_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return {"report": output, "modal_report_path": str(modal_report_path)}


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    layers: str = "",
    extraction_pairs: int = 12,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    seed: int = 42,
) -> None:
    selected_traits = [t.strip() for t in traits.split(",") if t.strip()]
    if not selected_traits:
        raise ValueError("No traits selected.")
    for trait in selected_traits:
        if trait not in DEFAULT_TRAITS:
            raise ValueError(f"Unsupported trait: {trait}")

    config = _load_config()
    selected_layers = (
        [int(x) for x in layers.split(",") if x.strip()]
        if layers.strip()
        else list(config["models"]["primary"]["optimal_steering_layers"])
    )
    if not selected_layers:
        raise ValueError("No layers provided.")
    extraction_rows_by_trait = {trait: _load_extraction_rows(trait) for trait in selected_traits}

    result = run_position_ablation_remote.remote(
        config=config,
        traits=selected_traits,
        layers=selected_layers,
        extraction_rows_by_trait=extraction_rows_by_trait,
        extraction_pairs=int(extraction_pairs),
        max_new_tokens=int(max_new_tokens),
        temperature=float(temperature),
        seed=int(seed),
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_extraction_position_ablation_{timestamp}.json"
    out_path.write_text(json.dumps(result["report"], indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "modal_report_path": result["modal_report_path"],
                "traits": selected_traits,
                "layers": selected_layers,
            },
            indent=2,
        )
    )
