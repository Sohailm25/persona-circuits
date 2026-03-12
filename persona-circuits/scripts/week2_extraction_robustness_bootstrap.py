"""Week 2 extraction robustness closure: bootstrap subset stability + train-vs-heldout agreement."""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
INFRA_AUDIT_PATH = ROOT / "results" / "infrastructure" / "week1_prompt_audit_report.json"
EXPERIMENT_CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
HELDOUT_DIR = PROMPTS_DIR / "heldout"
DEFAULT_TRAITS = ("sycophancy", "evil")
DEFAULT_EXTRACTION_METHOD = "prompt_last"
ALLOWED_EXTRACTION_METHODS = {"prompt_last", "response_mean", "response_last"}
DEFAULT_TRAIT_SCOPE_ARTIFACT = ROOT / "results" / "stage1_extraction" / "week2_trait_scope_resolution_20260301T030203Z.json"

app = modal.App("persona-circuits-week2-extraction-robustness-bootstrap")
vol = modal.Volume.from_name("persona-circuits-models", create_if_missing=True)
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "wandb",
        "numpy",
        "pyyaml",
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


def _resolve_extraction_method(config: dict[str, Any], extraction_method: str) -> str:
    method = extraction_method.strip().lower()
    if not method:
        steering_cfg = config.get("steering", {})
        if isinstance(steering_cfg, dict):
            method = str(steering_cfg.get("extraction_method", DEFAULT_EXTRACTION_METHOD)).strip().lower()
        else:
            method = DEFAULT_EXTRACTION_METHOD
    if method not in ALLOWED_EXTRACTION_METHODS:
        raise ValueError(
            f"Unsupported extraction method {method!r}; expected one of {sorted(ALLOWED_EXTRACTION_METHODS)}"
        )
    return method


def _load_prompt_pairs(traits: list[str]) -> dict[str, list[dict[str, Any]]]:
    prompt_pairs: dict[str, list[dict[str, Any]]] = {}
    for trait in traits:
        path = PROMPTS_DIR / f"{trait}_pairs.jsonl"
        prompt_pairs[trait] = _load_jsonl(path)
    return prompt_pairs


def _assert_prompt_audit_passed() -> None:
    if not INFRA_AUDIT_PATH.exists():
        raise FileNotFoundError(
            "Prompt audit report is missing. Run scripts/audit_prompt_datasets.py first."
        )
    report = json.loads(INFRA_AUDIT_PATH.read_text(encoding="utf-8"))
    if not report.get("overall_pass", False):
        raise RuntimeError(
            "Prompt audit is not passing. Fix prompt defects before running robustness extraction."
        )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load_heldout_pairs(traits: list[str]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for trait in traits:
        out[trait] = _load_jsonl(HELDOUT_DIR / f"{trait}_heldout_pairs.jsonl")
    return out


def _normalize_trait_list(raw: str) -> list[str]:
    values = [x.strip() for x in raw.split(",") if x.strip()]
    dedup: list[str] = []
    for value in values:
        if value not in dedup:
            dedup.append(value)
    return dedup


def _normalize_trait_key(key: str) -> str:
    if key == "machiavellian_disposition":
        return "evil"
    return key


def _parse_trait_layer_map_spec(spec: str) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for chunk in [c.strip() for c in spec.split(",") if c.strip()]:
        if ":" not in chunk:
            raise ValueError(f"Invalid trait-layer spec chunk: {chunk}")
        trait_raw, layer_raw = chunk.split(":", 1)
        trait = _normalize_trait_key(trait_raw.strip())
        mapping[trait] = int(layer_raw.strip())
    return mapping


def _resolve_trait_layer_map(
    *,
    trait_scope_payload: dict[str, Any],
    traits: list[str],
    override_map: dict[str, int] | None,
) -> dict[str, int]:
    if override_map:
        missing = [trait for trait in traits if trait not in override_map]
        if missing:
            raise ValueError(f"Missing override trait-layer mapping for traits: {missing}")
        return {trait: int(override_map[trait]) for trait in traits}

    trait_scope = trait_scope_payload.get("trait_scope", {})
    resolved: dict[str, int] = {}
    for trait in traits:
        payload = trait_scope.get(trait, {})
        layer = payload.get("selected_primary_combo", {}).get("layer")
        if layer is None:
            raise ValueError(f"Trait scope artifact missing selected layer for trait={trait}")
        resolved[trait] = int(layer)
    return resolved


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def _bootstrap_indices(*, n_rows: int, subset_size: int, n_bootstrap: int, seed: int) -> list[list[int]]:
    if n_rows <= 0:
        raise ValueError("n_rows must be > 0")
    if subset_size <= 0:
        raise ValueError("subset_size must be > 0")
    if subset_size > n_rows:
        raise ValueError("subset_size cannot exceed n_rows")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be > 0")

    rng = np.random.default_rng(int(seed))
    draws: list[list[int]] = []
    for _ in range(int(n_bootstrap)):
        idx = rng.choice(n_rows, size=subset_size, replace=False)
        draws.append([int(x) for x in np.sort(idx)])
    return draws


def _pairwise_cosine_summary(vectors: list[np.ndarray]) -> dict[str, Any]:
    if len(vectors) < 2:
        return {
            "n_vectors": int(len(vectors)),
            "n_pairs": 0,
            "min": None,
            "p05": None,
            "mean": None,
            "p50": None,
            "p95": None,
            "max": None,
            "std": None,
        }

    cosines: list[float] = []
    for i, j in combinations(range(len(vectors)), 2):
        cosines.append(_cosine(vectors[i], vectors[j]))

    arr = np.array(cosines, dtype=np.float64)
    return {
        "n_vectors": int(len(vectors)),
        "n_pairs": int(arr.size),
        "min": float(np.min(arr)),
        "p05": float(np.percentile(arr, 5)),
        "mean": float(np.mean(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)),
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=6 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("wandb-key"),
    ],
    volumes={"/models": vol},
)
def extraction_robustness_remote(
    *,
    config: dict[str, Any],
    train_prompt_pairs: dict[str, list[dict[str, Any]]],
    heldout_prompt_pairs: dict[str, list[dict[str, Any]]],
    trait_layer_map: dict[str, int],
    extraction_method: str,
    response_max_new_tokens: int,
    response_temperature: float,
    subset_size: int,
    n_bootstrap: int,
    bootstrap_seed: int,
    min_bootstrap_p05_cosine: float,
    min_train_vs_heldout_cosine: float,
) -> dict[str, Any]:
    import torch
    import wandb
    from sae_lens import HookedSAETransformer

    def _unit_vector_from_stacks(high_stack: torch.Tensor, low_stack: torch.Tensor) -> np.ndarray:
        diff = high_stack.mean(dim=0) - low_stack.mean(dim=0)
        norm = float(diff.norm().item())
        if norm <= 1e-8:
            raise RuntimeError("Encountered near-zero vector norm while computing extraction vector.")
        unit = (diff / norm).to(torch.float32).cpu().numpy()
        return unit.astype(np.float64)

    def _collect_stacks(rows: list[dict[str, Any]], layer: int) -> tuple[torch.Tensor, torch.Tensor]:
        hook_name = f"blocks.{layer}.hook_resid_post"
        hook_set = {hook_name}
        high_acts: list[torch.Tensor] = []
        low_acts: list[torch.Tensor] = []

        for row in rows:
            high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])
            low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])

            with torch.no_grad():
                high_tokens = model.to_tokens(high_prompt, prepend_bos=True)
                low_tokens = model.to_tokens(low_prompt, prepend_bos=True)
                if extraction_method == "prompt_last":
                    _, high_cache = model.run_with_cache(
                        high_tokens,
                        names_filter=lambda name: name in hook_set,
                    )
                    _, low_cache = model.run_with_cache(
                        low_tokens,
                        names_filter=lambda name: name in hook_set,
                    )
                    high_act = high_cache[hook_name][0, -1, :].to(torch.float32).cpu()
                    low_act = low_cache[hook_name][0, -1, :].to(torch.float32).cpu()
                else:
                    high_gen = model.generate(
                        high_tokens,
                        max_new_tokens=int(response_max_new_tokens),
                        temperature=float(response_temperature),
                        top_k=None,
                        stop_at_eos=True,
                        verbose=False,
                    )
                    low_gen = model.generate(
                        low_tokens,
                        max_new_tokens=int(response_max_new_tokens),
                        temperature=float(response_temperature),
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
                    high_resp = high_gen_cache[hook_name][0, high_prompt_len:, :].to(torch.float32)
                    low_resp = low_gen_cache[hook_name][0, low_prompt_len:, :].to(torch.float32)
                    if high_resp.shape[0] == 0:
                        high_resp = high_gen_cache[hook_name][0, -1:, :].to(torch.float32)
                    if low_resp.shape[0] == 0:
                        low_resp = low_gen_cache[hook_name][0, -1:, :].to(torch.float32)

                    if extraction_method == "response_mean":
                        high_act = high_resp.mean(dim=0).cpu()
                        low_act = low_resp.mean(dim=0).cpu()
                    else:
                        high_act = high_resp[-1, :].cpu()
                        low_act = low_resp[-1, :].cpu()

                high_acts.append(high_act)
                low_acts.append(low_act)

        return torch.stack(high_acts, dim=0), torch.stack(low_acts, dim=0)

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
        job_type="stage1_extraction_robustness",
        name=f"week2-extraction-robustness-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        config={
            "phase": "week2_remediation_p1",
            "model_name": model_name,
            "traits": sorted(trait_layer_map.keys()),
            "trait_layer_map": {k: int(v) for k, v in trait_layer_map.items()},
            "extraction_method": extraction_method,
            "response_max_new_tokens": int(response_max_new_tokens),
            "response_temperature": float(response_temperature),
            "subset_size": int(subset_size),
            "n_bootstrap": int(n_bootstrap),
            "bootstrap_seed": int(bootstrap_seed),
            "min_bootstrap_p05_cosine": float(min_bootstrap_p05_cosine),
            "min_train_vs_heldout_cosine": float(min_train_vs_heldout_cosine),
        },
    )

    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )

    report_traits: dict[str, Any] = {}
    for trait, layer in trait_layer_map.items():
        train_rows = train_prompt_pairs[trait]
        heldout_rows = heldout_prompt_pairs[trait]
        if len(train_rows) < subset_size:
            raise ValueError(
                f"subset_size={subset_size} exceeds train rows={len(train_rows)} for trait={trait}"
            )

        train_high, train_low = _collect_stacks(train_rows, int(layer))
        heldout_high, heldout_low = _collect_stacks(heldout_rows, int(layer))

        train_vector = _unit_vector_from_stacks(train_high, train_low)
        heldout_vector = _unit_vector_from_stacks(heldout_high, heldout_low)

        bootstrap_vectors: list[np.ndarray] = []
        index_sets = _bootstrap_indices(
            n_rows=int(train_high.shape[0]),
            subset_size=int(subset_size),
            n_bootstrap=int(n_bootstrap),
            seed=int(bootstrap_seed) + (int(layer) * 17) + len(trait),
        )
        for idx in index_sets:
            idx_t = torch.tensor(idx, dtype=torch.long)
            sub_high = train_high.index_select(0, idx_t)
            sub_low = train_low.index_select(0, idx_t)
            bootstrap_vectors.append(_unit_vector_from_stacks(sub_high, sub_low))

        pairwise = _pairwise_cosine_summary(bootstrap_vectors)
        train_vs_heldout_cos = _cosine(train_vector, heldout_vector)

        trait_pass = bool(
            (pairwise.get("p05") is not None)
            and (float(pairwise["p05"]) >= float(min_bootstrap_p05_cosine))
            and (float(train_vs_heldout_cos) >= float(min_train_vs_heldout_cosine))
        )

        wandb.log(
            {
                f"robustness/{trait}/bootstrap_pairwise_p05": float(pairwise["p05"]),
                f"robustness/{trait}/bootstrap_pairwise_mean": float(pairwise["mean"]),
                f"robustness/{trait}/train_vs_heldout_cosine": float(train_vs_heldout_cos),
                f"robustness/{trait}/pass": float(trait_pass),
            }
        )

        report_traits[trait] = {
            "layer": int(layer),
            "n_train_pairs": int(train_high.shape[0]),
            "n_heldout_pairs": int(heldout_high.shape[0]),
            "bootstrap": {
                "subset_size": int(subset_size),
                "n_bootstrap": int(n_bootstrap),
                "pairwise_cosine_summary": pairwise,
            },
            "train_vs_heldout_vector_cosine": float(train_vs_heldout_cos),
            "quality_gates": {
                "bootstrap_pairwise_p05_ge_threshold": bool(
                    (pairwise.get("p05") is not None)
                    and (float(pairwise["p05"]) >= float(min_bootstrap_p05_cosine))
                ),
                "train_vs_heldout_cosine_ge_threshold": bool(
                    float(train_vs_heldout_cos) >= float(min_train_vs_heldout_cosine)
                ),
                "pass": trait_pass,
            },
        }

    overall_pass = bool(all(v["quality_gates"]["pass"] for v in report_traits.values()))
    run.finish()

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_extraction_robustness_bootstrap",
        "model_name": model_name,
        "extraction_method": extraction_method,
        "response_max_new_tokens": int(response_max_new_tokens),
        "response_temperature": float(response_temperature),
        "trait_layer_map": {k: int(v) for k, v in trait_layer_map.items()},
        "traits": report_traits,
        "quality_gates": {
            "min_bootstrap_pairwise_p05_cosine": float(min_bootstrap_p05_cosine),
            "min_train_vs_heldout_cosine": float(min_train_vs_heldout_cosine),
            "overall_pass": overall_pass,
        },
        "evidence_status": {
            "activation_capture": "known",
            "bootstrap_pairwise_cosines": "known",
            "train_vs_heldout_agreement": "known",
            "robustness_interpretation": "inferred",
        },
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    trait_layers: str = "",
    trait_scope_artifact: str = str(DEFAULT_TRAIT_SCOPE_ARTIFACT),
    extraction_method: str = "",
    response_max_new_tokens: int = 96,
    response_temperature: float = 0.0,
    subset_size: int = 80,
    n_bootstrap: int = 20,
    bootstrap_seed: int = 42,
    min_bootstrap_p05_cosine: float = 0.8,
    min_train_vs_heldout_cosine: float = 0.7,
) -> None:
    selected_traits = _normalize_trait_list(traits)
    if not selected_traits:
        raise ValueError("No traits selected.")

    config = _load_config()
    resolved_method = _resolve_extraction_method(config, extraction_method)

    _assert_prompt_audit_passed()
    train_prompt_pairs = _load_prompt_pairs(selected_traits)
    heldout_prompt_pairs = _load_heldout_pairs(selected_traits)

    trait_scope_payload = json.loads(Path(trait_scope_artifact).read_text(encoding="utf-8"))
    override_map = _parse_trait_layer_map_spec(trait_layers) if trait_layers.strip() else None
    trait_layer_map = _resolve_trait_layer_map(
        trait_scope_payload=trait_scope_payload,
        traits=selected_traits,
        override_map=override_map,
    )

    call_kwargs = {
        "config": config,
        "train_prompt_pairs": train_prompt_pairs,
        "heldout_prompt_pairs": heldout_prompt_pairs,
        "trait_layer_map": trait_layer_map,
        "extraction_method": resolved_method,
        "response_max_new_tokens": int(response_max_new_tokens),
        "response_temperature": float(response_temperature),
        "subset_size": int(subset_size),
        "n_bootstrap": int(n_bootstrap),
        "bootstrap_seed": int(bootstrap_seed),
        "min_bootstrap_p05_cosine": float(min_bootstrap_p05_cosine),
        "min_train_vs_heldout_cosine": float(min_train_vs_heldout_cosine),
    }
    # Local entrypoint is expected to run via `modal run ...`, so avoid nested app.run().
    report = extraction_robustness_remote.remote(**call_kwargs)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_extraction_robustness_bootstrap_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_path": str(out_path),
                "traits": selected_traits,
                "trait_layer_map": trait_layer_map,
                "quality_gates": report["quality_gates"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parsed = argparse.ArgumentParser()
    parsed.add_argument("--traits", default=",".join(DEFAULT_TRAITS))
    parsed.add_argument("--trait-layers", default="")
    parsed.add_argument("--trait-scope-artifact", default=str(DEFAULT_TRAIT_SCOPE_ARTIFACT))
    parsed.add_argument("--extraction-method", default="")
    parsed.add_argument("--response-max-new-tokens", type=int, default=96)
    parsed.add_argument("--response-temperature", type=float, default=0.0)
    parsed.add_argument("--subset-size", type=int, default=80)
    parsed.add_argument("--n-bootstrap", type=int, default=20)
    parsed.add_argument("--bootstrap-seed", type=int, default=42)
    parsed.add_argument("--min-bootstrap-p05-cosine", type=float, default=0.8)
    parsed.add_argument("--min-train-vs-heldout-cosine", type=float, default=0.7)
    args = parsed.parse_args()
    main(
        traits=args.traits,
        trait_layers=args.trait_layers,
        trait_scope_artifact=args.trait_scope_artifact,
        extraction_method=args.extraction_method,
        response_max_new_tokens=args.response_max_new_tokens,
        response_temperature=args.response_temperature,
        subset_size=args.subset_size,
        n_bootstrap=args.n_bootstrap,
        bootstrap_seed=args.bootstrap_seed,
        min_bootstrap_p05_cosine=args.min_bootstrap_p05_cosine,
        min_train_vs_heldout_cosine=args.min_train_vs_heldout_cosine,
    )
