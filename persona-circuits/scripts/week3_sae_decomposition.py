"""Week 3 Stage 2: SAE feature decomposition (direct projection + differential activation)."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import torch
import yaml

APP_NAME = "persona-circuits-week3-sae-decomposition"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ["sycophancy", "evil"]
DEFAULT_LAYER = 12
DEFAULT_TOP_K = 100
DEFAULT_MAX_PAIRS = 100

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
RESULTS_DIR = ROOT / "results" / "stage2_decomposition"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "pyyaml",
        "numpy",
    ]
)


def _to_nonnegative_array(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return arr
    return np.abs(arr)


def _gini_coefficient(values: np.ndarray) -> float | None:
    arr = _to_nonnegative_array(values)
    if arr.size == 0:
        return None
    total = float(np.sum(arr))
    if total <= 0.0:
        return 0.0
    sorted_arr = np.sort(arr)
    n = sorted_arr.size
    idx = np.arange(1, n + 1, dtype=np.float64)
    gini = (2.0 * np.sum(idx * sorted_arr) / (n * total)) - ((n + 1.0) / n)
    return float(gini)


def _normalized_entropy(values: np.ndarray) -> float | None:
    arr = _to_nonnegative_array(values)
    if arr.size == 0:
        return None
    total = float(np.sum(arr))
    if total <= 0.0:
        return 0.0
    if arr.size == 1:
        return 0.0
    p = arr / total
    entropy = -float(np.sum(p * np.log(p + 1e-12)))
    return float(entropy / math.log(arr.size))


def _top_p_mass(values: np.ndarray, p_fraction: float) -> float | None:
    arr = _to_nonnegative_array(values)
    if arr.size == 0:
        return None
    total = float(np.sum(arr))
    if total <= 0.0:
        return 0.0
    p_fraction = float(max(0.0, min(1.0, p_fraction)))
    k = int(max(1, math.ceil(arr.size * p_fraction)))
    top = np.sort(arr)[-k:]
    return float(np.sum(top) / total)


def concentration_summary(values: np.ndarray) -> dict[str, float | None]:
    return {
        "gini": _gini_coefficient(values),
        "entropy_normalized": _normalized_entropy(values),
        "top_1pct_mass": _top_p_mass(values, 0.01),
        "top_5pct_mass": _top_p_mass(values, 0.05),
        "top_10pct_mass": _top_p_mass(values, 0.10),
    }


def _set_modal_cache_env() -> None:
    os.environ["HF_HOME"] = "/models/huggingface"
    os.environ["TRANSFORMERS_CACHE"] = "/models/huggingface"
    os.environ["HF_HUB_CACHE"] = "/models/huggingface"
    os.environ["HUGGINGFACE_HUB_CACHE"] = "/models/huggingface"
    Path("/models/huggingface").mkdir(parents=True, exist_ok=True)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


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


def _parse_traits(raw: str) -> list[str]:
    values = [x.strip() for x in raw.split(",") if x.strip()]
    if not values:
        raise ValueError("Trait list cannot be empty.")
    return values


def _parse_trait_alias_map(raw: str) -> dict[str, str]:
    if not raw.strip():
        return {}
    out: dict[str, str] = {}
    for item in raw.split(","):
        token = item.strip()
        if not token:
            continue
        if ":" not in token:
            raise ValueError(f"Invalid alias token {token!r}; expected trait:alias")
        trait, alias = token.split(":", 1)
        t = trait.strip()
        a = alias.strip()
        if not t or not a:
            raise ValueError(f"Invalid alias token {token!r}; empty trait/alias")
        out[t] = a
    return out


def _load_prompt_pairs(trait: str, max_pairs: int) -> list[dict[str, Any]]:
    path = PROMPTS_DIR / f"{trait}_pairs.jsonl"
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"No prompt pairs found for trait={trait}")
    return rows[: min(max_pairs, len(rows))]


def _load_layer_vector(vectors_path: Path, trait: str, layer: int) -> torch.Tensor:
    payload = torch.load(vectors_path, map_location="cpu")
    if trait not in payload:
        raise KeyError(f"Trait {trait!r} missing in vectors file {vectors_path}")
    by_layer = payload[trait]
    if str(layer) in by_layer:
        vector = by_layer[str(layer)]
    elif layer in by_layer:
        vector = by_layer[layer]
    else:
        raise KeyError(f"Layer {layer} missing for trait {trait!r} in {vectors_path}")
    return torch.as_tensor(vector, dtype=torch.float32)


def _load_layer_vectors_for_traits(
    *,
    vectors_path: Path,
    traits: list[str],
    layer: int,
) -> dict[str, list[float]]:
    payload = torch.load(vectors_path, map_location="cpu")
    out: dict[str, list[float]] = {}
    for trait in traits:
        if trait not in payload:
            raise KeyError(f"Trait {trait!r} missing in vectors file {vectors_path}")
        by_layer = payload[trait]
        if str(layer) in by_layer:
            vec = by_layer[str(layer)]
        elif layer in by_layer:
            vec = by_layer[layer]
        else:
            raise KeyError(f"Layer {layer} missing for trait {trait!r} in {vectors_path}")
        out[trait] = torch.as_tensor(vec, dtype=torch.float32).tolist()
    return out


def _select_topk_indices(values: torch.Tensor, k: int) -> list[int]:
    if values.ndim != 1:
        raise ValueError("Expected 1D tensor for top-k selection")
    topk = min(int(k), int(values.shape[0]))
    if topk <= 0:
        return []
    idx = torch.topk(values, k=topk).indices
    return [int(x) for x in idx.detach().cpu().tolist()]


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return float(len(a & b) / len(union))


def _rank_union_features(
    *,
    union_features: set[int],
    direct_top: list[int],
    diff_top: list[int],
    direct_cos: torch.Tensor,
    diff_mean: torch.Tensor,
    top_n: int,
) -> list[dict[str, Any]]:
    direct_rank = {feat: rank for rank, feat in enumerate(direct_top)}
    diff_rank = {feat: rank for rank, feat in enumerate(diff_top)}
    k_direct = max(1, len(direct_top))
    k_diff = max(1, len(diff_top))

    rows: list[dict[str, Any]] = []
    for feat in union_features:
        d_rank = direct_rank.get(feat)
        f_rank = diff_rank.get(feat)
        d_score = (k_direct - d_rank) / k_direct if d_rank is not None else 0.0
        f_score = (k_diff - f_rank) / k_diff if f_rank is not None else 0.0
        combined = 0.5 * (d_score + f_score)
        rows.append(
            {
                "feature_id": int(feat),
                "combined_rank_score": float(combined),
                "in_direct_topk": bool(d_rank is not None),
                "in_differential_topk": bool(f_rank is not None),
                "direct_rank": None if d_rank is None else int(d_rank + 1),
                "differential_rank": None if f_rank is None else int(f_rank + 1),
                "direct_cosine": float(direct_cos[feat].item()),
                "differential_mean": float(diff_mean[feat].item()),
                "differential_abs_mean": float(abs(diff_mean[feat].item())),
            }
        )

    rows.sort(
        key=lambda x: (
            x["combined_rank_score"],
            x["differential_abs_mean"],
            x["direct_cosine"],
        ),
        reverse=True,
    )
    return rows[: min(int(top_n), len(rows))]


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=8 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_decomposition_remote(
    *,
    config: dict[str, Any],
    traits: list[str],
    trait_alias_map: dict[str, str],
    prompt_pairs_by_trait: dict[str, list[dict[str, Any]]],
    layer_vectors_by_trait: dict[str, list[float]],
    layer: int,
    top_k: int,
    max_pairs: int,
    sae_source: str,
    vectors_artifact_path: str,
    seed: int,
) -> dict[str, Any]:
    from sae_lens import SAE, HookedSAETransformer

    _set_modal_cache_env()
    _seed_everything(seed)

    if sae_source not in {"primary", "cross_check"}:
        raise ValueError(f"Unsupported sae_source={sae_source}")

    model_name = str(config["models"]["primary"]["name"])
    sae_block = config["sae"][sae_source]
    available_layers = [int(x) for x in sae_block["layers"]]
    if int(layer) not in available_layers:
        raise ValueError(
            f"Layer {layer} not available for sae_source={sae_source}; available={available_layers}"
        )

    sae_release = str(sae_block["release"])
    sae_id = str(sae_block["sae_id_format"]).format(layer=int(layer))
    hook_name = f"blocks.{int(layer)}.hook_resid_post"

    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    model.eval()

    sae, _, _ = SAE.from_pretrained(
        release=sae_release,
        sae_id=sae_id,
        device="cuda",
    )
    sae = sae.to(dtype=torch.float32)
    sae.eval()

    decoder = sae.W_dec.detach().to(torch.float32)
    decoder_norm = decoder.norm(dim=1).clamp_min(1e-8)

    out_by_trait: dict[str, Any] = {}
    for trait in traits:
        rows = prompt_pairs_by_trait.get(trait, [])
        if not rows:
            raise ValueError(f"No prompt pairs provided for trait={trait}")
        raw_vec = layer_vectors_by_trait.get(trait)
        if raw_vec is None:
            raise KeyError(f"Trait {trait!r} missing from layer_vectors_by_trait payload")
        vec = torch.as_tensor(raw_vec, dtype=torch.float32, device="cuda")
        vec_norm = vec.norm().clamp_min(1e-8)
        unit_vec = vec / vec_norm

        direct_dot = decoder @ unit_vec
        direct_cos = direct_dot / decoder_norm
        top_direct_ids = _select_topk_indices(direct_cos, top_k)

        diff_sum = torch.zeros(decoder.shape[0], dtype=torch.float32, device="cuda")
        for row in rows:
            high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])
            low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])

            with torch.no_grad():
                high_tokens = model.to_tokens(high_prompt, prepend_bos=True)
                low_tokens = model.to_tokens(low_prompt, prepend_bos=True)
                _, high_cache = model.run_with_cache(high_tokens, names_filter=lambda n: n == hook_name)
                _, low_cache = model.run_with_cache(low_tokens, names_filter=lambda n: n == hook_name)
                high_act = high_cache[hook_name][0, -1, :].to(torch.float32)
                low_act = low_cache[hook_name][0, -1, :].to(torch.float32)
                feats = sae.encode(torch.stack([high_act, low_act], dim=0))
                diff_sum = diff_sum + (feats[0] - feats[1])

        diff_mean = diff_sum / float(len(rows))
        diff_abs = diff_mean.abs()
        top_diff_ids = _select_topk_indices(diff_abs, top_k)

        union_set = set(top_direct_ids) | set(top_diff_ids)
        ranked_union = _rank_union_features(
            union_features=union_set,
            direct_top=top_direct_ids,
            diff_top=top_diff_ids,
            direct_cos=direct_cos,
            diff_mean=diff_mean,
            top_n=top_k,
        )
        candidate_ids = [int(x["feature_id"]) for x in ranked_union]

        direct_abs_np = direct_cos.abs().detach().cpu().numpy()
        candidate_abs_np = direct_cos[torch.tensor(candidate_ids, device="cuda")].abs().detach().cpu().numpy()

        alias = trait_alias_map.get(trait, trait)
        out_by_trait[trait] = {
            "claim_trait_name": alias,
            "evidence_status": {
                "direct_projection": "observed",
                "differential_activation": "observed",
                "candidate_union": "observed",
                "concentration_metrics": "observed",
            },
            "n_pairs": int(len(rows)),
            "layer": int(layer),
            "top_k": int(top_k),
            "direct_projection": {
                "top_feature_ids": top_direct_ids,
                "top_preview": [
                    {
                        "feature_id": int(fid),
                        "direct_cosine": float(direct_cos[fid].item()),
                        "direct_dot": float(direct_dot[fid].item()),
                    }
                    for fid in top_direct_ids[:10]
                ],
            },
            "differential_activation": {
                "top_feature_ids": top_diff_ids,
                "top_preview": [
                    {
                        "feature_id": int(fid),
                        "differential_mean": float(diff_mean[fid].item()),
                        "differential_abs_mean": float(diff_abs[fid].item()),
                    }
                    for fid in top_diff_ids[:10]
                ],
            },
            "candidate_union": {
                "direct_topk_count": int(len(top_direct_ids)),
                "differential_topk_count": int(len(top_diff_ids)),
                "union_count": int(len(union_set)),
                "direct_vs_differential_jaccard": _jaccard(set(top_direct_ids), set(top_diff_ids)),
                "ranked_candidates_topk": ranked_union,
            },
            "concentration": {
                "direct_cosine_abs_all_features": concentration_summary(direct_abs_np),
                "direct_cosine_abs_candidate_features": concentration_summary(candidate_abs_np),
            },
        }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "model_name": model_name,
            "sae_source": sae_source,
            "sae_release": sae_release,
            "sae_id": sae_id,
            "layer": int(layer),
            "traits": traits,
            "trait_alias_map": trait_alias_map,
            "top_k": int(top_k),
            "max_pairs": int(max_pairs),
            "seed": int(seed),
            "vectors_artifact_path": str(vectors_artifact_path),
        },
        "evidence_status": {
            "feature_lists": "observed",
            "concentration_metrics": "observed",
            "feature_interpretations": "unknown",
            "cross_source_validation": "unknown",
        },
        "results_by_trait": out_by_trait,
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    trait_alias_map: str = "evil:machiavellian_disposition",
    layer: int = DEFAULT_LAYER,
    top_k: int = DEFAULT_TOP_K,
    max_pairs: int = DEFAULT_MAX_PAIRS,
    sae_source: str = "primary",
    vectors_path: str = "results/stage1_extraction/week2_persona_vectors_20260225T170852Z.pt",
    seed: int = 42,
) -> None:
    cfg = _load_config()
    selected_traits = _parse_traits(traits)
    aliases = _parse_trait_alias_map(trait_alias_map)
    vectors_resolved = (
        (ROOT / vectors_path).resolve()
        if not str(vectors_path).startswith("/")
        else Path(vectors_path).resolve()
    )
    prompt_pairs_by_trait = {
        trait: _load_prompt_pairs(trait=trait, max_pairs=int(max_pairs))
        for trait in selected_traits
    }
    layer_vectors_by_trait = _load_layer_vectors_for_traits(
        vectors_path=vectors_resolved,
        traits=selected_traits,
        layer=int(layer),
    )

    report = run_decomposition_remote.remote(
        config=cfg,
        traits=selected_traits,
        trait_alias_map=aliases,
        prompt_pairs_by_trait=prompt_pairs_by_trait,
        layer_vectors_by_trait=layer_vectors_by_trait,
        layer=int(layer),
        top_k=int(top_k),
        max_pairs=int(max_pairs),
        sae_source=sae_source,
        vectors_artifact_path=str(vectors_resolved),
        seed=int(seed),
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week3_sae_decomposition_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "traits": selected_traits,
                "layer": int(layer),
                "sae_source": sae_source,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
