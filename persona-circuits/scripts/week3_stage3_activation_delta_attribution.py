"""Week 3 Stage 3 first attribution pass (activation-delta over selected SAE features)."""

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

APP_NAME = "persona-circuits-week3-stage3-activation-delta-attribution"
MODEL_VOLUME_NAME = "persona-circuits-models"

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
OUT_DIR = ROOT / "results" / "stage3_attribution"
DEFAULT_CANDIDATE_ARTIFACT = (
    "results/stage3_attribution/week3_stage3_candidate_selection_20260304T163200Z.json"
)
DEFAULT_TRAITS = ["sycophancy", "evil"]

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


def _to_nonnegative_array(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return arr
    return np.abs(arr)


def _top_p_mass(values: np.ndarray, p_fraction: float) -> float | None:
    arr = _to_nonnegative_array(values)
    if arr.size == 0:
        return None
    total = float(np.sum(arr))
    if total <= 0.0:
        return 0.0
    p_fraction = float(max(0.0, min(1.0, p_fraction)))
    k = int(max(1, math.ceil(arr.size * p_fraction)))
    return float(np.sum(np.sort(arr)[-k:]) / total)


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
    ent = -float(np.sum(p * np.log(p + 1e-12)))
    return float(ent / math.log(arr.size))


def _gini(values: np.ndarray) -> float | None:
    arr = _to_nonnegative_array(values)
    if arr.size == 0:
        return None
    total = float(np.sum(arr))
    if total <= 0.0:
        return 0.0
    sorted_arr = np.sort(arr)
    n = sorted_arr.size
    idx = np.arange(1, n + 1, dtype=np.float64)
    g = (2.0 * np.sum(idx * sorted_arr) / (n * total)) - ((n + 1.0) / n)
    return float(g)


def _concentration_summary(values: np.ndarray) -> dict[str, float | None]:
    return {
        "gini": _gini(values),
        "entropy_normalized": _normalized_entropy(values),
        "top_10pct_mass": _top_p_mass(values, 0.10),
        "top_20pct_mass": _top_p_mass(values, 0.20),
    }


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return float(len(a & b) / len(union))


def _mean_pairwise_jaccard(sets: list[set[int]]) -> float | None:
    if len(sets) < 2:
        return None
    vals: list[float] = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            vals.append(_jaccard(sets[i], sets[j]))
    if not vals:
        return None
    return float(np.mean(np.asarray(vals, dtype=np.float64)))


def _parse_traits(raw: str) -> list[str]:
    traits = [x.strip() for x in raw.split(",") if x.strip()]
    if not traits:
        raise ValueError("Trait list cannot be empty.")
    return traits


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
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _load_candidate_features(
    *,
    artifact_path: Path,
    traits: list[str],
    per_trait_k: int,
) -> dict[str, list[int]]:
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    by_trait: dict[str, list[int]] = {}
    for trait in traits:
        rows = (
            payload.get("results_by_trait", {})
            .get(trait, {})
            .get("selected_first_pass_features", [])
        )
        if not rows:
            raise ValueError(f"No selected features found for trait={trait} in {artifact_path}")
        by_trait[trait] = [int(r["feature_id"]) for r in rows[:per_trait_k]]
    return by_trait


def _load_heldout_pairs(trait: str, max_pairs: int) -> list[dict[str, Any]]:
    path = ROOT / "prompts" / "heldout" / f"{trait}_heldout_pairs.jsonl"
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"No heldout rows found for trait={trait}")
    return rows[: min(int(max_pairs), len(rows))]


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=8 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_stage3_attribution_remote(
    *,
    config: dict[str, Any],
    traits: list[str],
    selected_features_by_trait: dict[str, list[int]],
    heldout_pairs_by_trait: dict[str, list[dict[str, Any]]],
    seed: int,
) -> dict[str, Any]:
    from sae_lens import SAE, HookedSAETransformer

    _set_modal_cache_env()
    _seed_everything(seed)

    model_name = str(config["models"]["primary"]["name"])
    layer = 12
    hook_name = f"blocks.{layer}.hook_resid_post"

    sae_cfg = config["sae"]["primary"]
    if int(layer) not in [int(x) for x in sae_cfg["layers"]]:
        raise ValueError(f"Layer {layer} unavailable in primary SAE config.")
    sae_release = str(sae_cfg["release"])
    sae_id = str(sae_cfg["sae_id_format"]).format(layer=layer)

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

    out_by_trait: dict[str, Any] = {}
    for trait in traits:
        selected = selected_features_by_trait.get(trait, [])
        rows = heldout_pairs_by_trait.get(trait, [])
        if not selected:
            raise ValueError(f"No selected features for trait={trait}")
        if not rows:
            raise ValueError(f"No heldout rows for trait={trait}")

        feat_tensor = torch.tensor(selected, dtype=torch.long, device="cuda")
        prompt_top_sets: list[set[int]] = []
        prompt_maps: list[dict[str, Any]] = []
        per_prompt_delta = []

        for row in rows:
            high_prompt = _format_chat_prompt(model.tokenizer, row["system_high"], row["user_query"])
            low_prompt = _format_chat_prompt(model.tokenizer, row["system_low"], row["user_query"])

            with torch.no_grad():
                high_tok = model.to_tokens(high_prompt, prepend_bos=True)
                low_tok = model.to_tokens(low_prompt, prepend_bos=True)
                _, high_cache = model.run_with_cache(high_tok, names_filter=lambda n: n == hook_name)
                _, low_cache = model.run_with_cache(low_tok, names_filter=lambda n: n == hook_name)
                high_act = high_cache[hook_name][0, -1, :].to(torch.float32)
                low_act = low_cache[hook_name][0, -1, :].to(torch.float32)
                feats = sae.encode(torch.stack([high_act, low_act], dim=0))
                delta = (feats[0, feat_tensor] - feats[1, feat_tensor]).detach().cpu().numpy()

            per_prompt_delta.append(delta)
            top_local = np.argsort(np.abs(delta))[-10:]
            top_feature_ids = [selected[int(i)] for i in top_local[::-1]]
            prompt_top_sets.append(set(top_feature_ids))
            prompt_maps.append(
                {
                    "prompt_id": row.get("id"),
                    "top10_feature_ids_by_abs_delta": top_feature_ids,
                    "top10_feature_abs_delta": [
                        float(abs(delta[int(i)])) for i in top_local[::-1]
                    ],
                }
            )

        delta_matrix = np.asarray(per_prompt_delta, dtype=np.float64)
        mean_delta = np.mean(delta_matrix, axis=0)
        mean_abs_delta = np.mean(np.abs(delta_matrix), axis=0)
        top_global_idx = np.argsort(mean_abs_delta)[-10:][::-1]
        top_global = [
            {
                "feature_id": int(selected[int(i)]),
                "mean_delta": float(mean_delta[int(i)]),
                "mean_abs_delta": float(mean_abs_delta[int(i)]),
            }
            for i in top_global_idx
        ]

        out_by_trait[trait] = {
            "claim_trait_name": trait if trait != "evil" else "machiavellian_disposition",
            "n_prompts": int(len(rows)),
            "n_selected_features": int(len(selected)),
            "attribution_method": "activation_delta_proxy",
            "feature_attribution_summary": {
                "top10_by_mean_abs_delta": top_global,
                "mean_abs_delta_concentration": _concentration_summary(mean_abs_delta),
                "prompt_top10_pairwise_jaccard_mean": _mean_pairwise_jaccard(prompt_top_sets),
            },
            "prompt_level_maps": prompt_maps,
            "evidence_status": {
                "feature_deltas": "observed",
                "gradient_edges": "unknown",
                "causal_necessity": "unknown",
            },
        }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "model_name": model_name,
            "sae_release": sae_release,
            "sae_id": sae_id,
            "layer": layer,
            "traits": traits,
            "seed": int(seed),
            "attribution_method": "activation_delta_proxy",
        },
        "evidence_status": {
            "stage3_proxy_attribution": "observed",
            "full_gradient_attribution_graph": "unknown",
            "causal_validation": "unknown",
        },
        "results_by_trait": out_by_trait,
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    candidate_artifact: str = DEFAULT_CANDIDATE_ARTIFACT,
    per_trait_k: int = 50,
    n_prompts: int = 20,
    seed: int = 42,
) -> None:
    cfg = _load_config()
    selected_traits = _parse_traits(traits)
    cand_path = _resolve_path(candidate_artifact)
    selected_features_by_trait = _load_candidate_features(
        artifact_path=cand_path,
        traits=selected_traits,
        per_trait_k=int(per_trait_k),
    )
    heldout_pairs_by_trait = {
        trait: _load_heldout_pairs(trait=trait, max_pairs=int(n_prompts))
        for trait in selected_traits
    }

    report = run_stage3_attribution_remote.remote(
        config=cfg,
        traits=selected_traits,
        selected_features_by_trait=selected_features_by_trait,
        heldout_pairs_by_trait=heldout_pairs_by_trait,
        seed=int(seed),
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"week3_stage3_activation_delta_attribution_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "artifact": str(out_path),
                "traits": selected_traits,
                "n_prompts": int(n_prompts),
                "per_trait_k": int(per_trait_k),
            },
            indent=2,
        )
    )


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


if __name__ == "__main__":
    main()

