"""Week 3/4 first Stage4 necessity proxy run with multi-method ablation + random baselines."""

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

APP_NAME = "persona-circuits-week3-stage4-necessity-proxy-ablation"
MODEL_VOLUME_NAME = "persona-circuits-models"

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
OUT_DIR = ROOT / "results" / "stage4_ablation"
DEFAULT_TARGET_FREEZE_ARTIFACT = (
    "results/stage4_ablation/week3_stage4_target_set_freeze_20260304T164918Z.json"
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


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _parse_traits(raw: str) -> list[str]:
    traits = [x.strip() for x in raw.split(",") if x.strip()]
    if not traits:
        raise ValueError("Trait list cannot be empty.")
    return traits


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


def _cohens_d(sample_a: np.ndarray, sample_b: np.ndarray) -> float | None:
    a = np.asarray(sample_a, dtype=np.float64).reshape(-1)
    b = np.asarray(sample_b, dtype=np.float64).reshape(-1)
    if a.size < 2 or b.size < 2:
        return None
    mean_delta = float(np.mean(a) - np.mean(b))
    var_a = float(np.var(a, ddof=1))
    var_b = float(np.var(b, ddof=1))
    pooled_var = ((a.size - 1) * var_a + (b.size - 1) * var_b) / float(a.size + b.size - 2)
    if pooled_var <= 0.0:
        return 0.0
    return float(mean_delta / math.sqrt(pooled_var))


def _a12(sample_a: np.ndarray, sample_b: np.ndarray) -> float | None:
    a = np.asarray(sample_a, dtype=np.float64).reshape(-1)
    b = np.asarray(sample_b, dtype=np.float64).reshape(-1)
    if a.size == 0 or b.size == 0:
        return None
    a_rep = np.repeat(a, b.size)
    b_tile = np.tile(b, a.size)
    greater = float(np.sum(a_rep > b_tile))
    ties = float(np.sum(a_rep == b_tile))
    total = float(a.size * b.size)
    return float((greater + 0.5 * ties) / total)


def _effect_size_summary(
    sample_a: np.ndarray,
    sample_b: np.ndarray,
    *,
    seed: int,
    n_bootstrap: int,
) -> dict[str, Any]:
    a = np.asarray(sample_a, dtype=np.float64).reshape(-1)
    b = np.asarray(sample_b, dtype=np.float64).reshape(-1)
    d = _cohens_d(a, b)
    a12_val = _a12(a, b)
    if a.size == 0 or b.size == 0:
        return {
            "n_a": int(a.size),
            "n_b": int(b.size),
            "cohens_d": d,
            "a12": a12_val,
            "cohens_d_ci95": None,
            "a12_ci95": None,
        }

    rng = np.random.default_rng(int(seed))
    d_draws: list[float] = []
    a12_draws: list[float] = []
    for _ in range(int(n_bootstrap)):
        a_draw = rng.choice(a, size=a.size, replace=True)
        b_draw = rng.choice(b, size=b.size, replace=True)
        d_boot = _cohens_d(a_draw, b_draw)
        a12_boot = _a12(a_draw, b_draw)
        if d_boot is not None:
            d_draws.append(float(d_boot))
        if a12_boot is not None:
            a12_draws.append(float(a12_boot))

    d_ci = (
        {
            "lower": float(np.percentile(np.asarray(d_draws, dtype=np.float64), 2.5)),
            "upper": float(np.percentile(np.asarray(d_draws, dtype=np.float64), 97.5)),
        }
        if d_draws
        else None
    )
    a12_ci = (
        {
            "lower": float(np.percentile(np.asarray(a12_draws, dtype=np.float64), 2.5)),
            "upper": float(np.percentile(np.asarray(a12_draws, dtype=np.float64), 97.5)),
        }
        if a12_draws
        else None
    )

    return {
        "n_a": int(a.size),
        "n_b": int(b.size),
        "cohens_d": d,
        "a12": a12_val,
        "cohens_d_ci95": d_ci,
        "a12_ci95": a12_ci,
    }


def _random_baseline_selectivity(observed_effect: float, random_effects: np.ndarray) -> dict[str, Any]:
    rand = np.asarray(random_effects, dtype=np.float64).reshape(-1)
    if rand.size == 0:
        return {
            "n_random": 0,
            "observed_effect": float(observed_effect),
            "percentile_rank": None,
            "p_value_one_sided_ge": None,
            "top_1pct_pass": None,
        }
    percentile_rank = float(np.mean(rand <= observed_effect))
    p_value = float((np.sum(rand >= observed_effect) + 1.0) / (rand.size + 1.0))
    return {
        "n_random": int(rand.size),
        "observed_effect": float(observed_effect),
        "percentile_rank": percentile_rank,
        "p_value_one_sided_ge": p_value,
        "top_1pct_pass": bool(percentile_rank >= 0.99),
    }


def _bootstrap_mean_ci(values: np.ndarray, *, seed: int, n_bootstrap: int) -> dict[str, float] | None:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return None
    rng = np.random.default_rng(int(seed))
    draws = rng.choice(arr, size=(int(n_bootstrap), arr.size), replace=True)
    means = np.mean(draws, axis=1)
    return {
        "lower": float(np.percentile(means, 2.5)),
        "upper": float(np.percentile(means, 97.5)),
    }


def _sample_random_feature_sets(
    *,
    d_sae: int,
    exclude_ids: list[int],
    set_size: int,
    n_sets: int,
    seed: int,
) -> np.ndarray:
    if int(set_size) <= 0:
        raise ValueError("set_size must be > 0")
    exclude = set(int(x) for x in exclude_ids)
    pool = np.asarray([i for i in range(int(d_sae)) if i not in exclude], dtype=np.int64)
    if pool.size < int(set_size):
        raise ValueError(
            f"Insufficient feature pool: pool={pool.size}, set_size={set_size}, excluded={len(exclude)}"
        )
    rng = np.random.default_rng(int(seed))
    out = np.empty((int(n_sets), int(set_size)), dtype=np.int64)
    for i in range(int(n_sets)):
        out[i] = rng.choice(pool, size=int(set_size), replace=False)
    return out


def _reduction_fraction(baseline_abs: float, ablated_abs: float) -> float:
    denom = max(float(baseline_abs), 1e-8)
    return float((float(baseline_abs) - float(ablated_abs)) / denom)


def _apply_feature_ablation(
    high_vec: torch.Tensor,
    *,
    donor_vec: torch.Tensor,
    mean_vec: torch.Tensor,
    feature_ids: np.ndarray,
    method: str,
) -> torch.Tensor:
    out = high_vec.clone()
    idx = np.asarray(feature_ids, dtype=np.int64)
    if method == "zero":
        out[idx] = 0.0
    elif method == "mean":
        out[idx] = mean_vec[idx]
    elif method == "resample":
        out[idx] = donor_vec[idx]
    else:
        raise ValueError(f"Unknown method={method}")
    return out


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=8 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_stage4_necessity_proxy_remote(
    *,
    config: dict[str, Any],
    traits: list[str],
    target_sets_by_trait: dict[str, list[int]],
    heldout_pairs_by_trait: dict[str, list[dict[str, Any]]],
    random_baseline_samples: int,
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    from sae_lens import SAE, HookedSAETransformer

    _set_modal_cache_env()
    _seed_everything(seed)

    model_name = str(config["models"]["primary"]["name"])
    layer = 12
    hook_name = f"blocks.{layer}.hook_resid_post"

    sae_cfg = config["sae"]["primary"]
    sae_release = str(sae_cfg["release"])
    sae_id = str(sae_cfg["sae_id_format"]).format(layer=layer)

    thresholds = config.get("thresholds", {})
    necessity_threshold = float(thresholds.get("necessity", 0.80))
    significance_threshold = float(thresholds.get("significance", 0.01))

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

    # `W_dec` shape: [d_sae, d_model]
    d_sae = int(sae.W_dec.shape[0])

    rng = np.random.default_rng(int(seed))
    methods = ["resample", "mean", "zero"]

    results_by_trait: dict[str, Any] = {}

    for trait in traits:
        target_ids = [int(x) for x in target_sets_by_trait.get(trait, [])]
        if not target_ids:
            raise ValueError(f"Missing target IDs for trait={trait}")
        rows = heldout_pairs_by_trait.get(trait, [])
        if not rows:
            raise ValueError(f"Missing heldout rows for trait={trait}")

        target_tensor = torch.tensor(target_ids, dtype=torch.long, device="cuda")

        feats_high_list: list[torch.Tensor] = []
        feats_low_list: list[torch.Tensor] = []
        baseline_abs_list: list[float] = []

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
                feats = sae.encode(torch.stack([high_act, low_act], dim=0)).to(torch.float32)
                feats_high = feats[0]
                feats_low = feats[1]

            feats_high_list.append(feats_high.detach().cpu())
            feats_low_list.append(feats_low.detach().cpu())

            baseline_abs = float(
                torch.mean(torch.abs(feats_high[target_tensor] - feats_low[target_tensor])).item()
            )
            baseline_abs_list.append(baseline_abs)

        feats_high = torch.stack(feats_high_list, dim=0)  # [n, d_sae]
        feats_low = torch.stack(feats_low_list, dim=0)    # [n, d_sae]
        n_rows = int(feats_high.shape[0])

        # Mean-ablation reference over all observed high/low rows.
        feature_mean = torch.mean(torch.cat([feats_high, feats_low], dim=0), dim=0)

        # Resample donors (different row index required).
        donors = []
        for i in range(n_rows):
            if n_rows == 1:
                donors.append(0)
                continue
            j = int(rng.integers(low=0, high=n_rows))
            while j == i:
                j = int(rng.integers(low=0, high=n_rows))
            donors.append(j)

        observed_reductions_by_method: dict[str, list[float]] = {m: [] for m in methods}

        for i in range(n_rows):
            base_abs = float(baseline_abs_list[i])
            high_vec = feats_high[i].clone()
            low_vec = feats_low[i]
            donor_vec = feats_high[donors[i]]

            for method in methods:
                idx = np.asarray(target_ids, dtype=np.int64)
                high_ab = _apply_feature_ablation(
                    high_vec,
                    donor_vec=donor_vec,
                    mean_vec=feature_mean,
                    feature_ids=idx,
                    method=method,
                )
                ablated_abs = float(torch.mean(torch.abs(high_ab[idx] - low_vec[idx])).item())
                observed_reductions_by_method[method].append(
                    _reduction_fraction(base_abs, ablated_abs)
                )

        random_feature_sets = _sample_random_feature_sets(
            d_sae=d_sae,
            exclude_ids=target_ids,
            set_size=len(target_ids),
            n_sets=int(random_baseline_samples),
            seed=int(seed) + 17,
        )

        random_set_means_by_method: dict[str, list[float]] = {m: [] for m in methods}
        random_prompt_reductions_by_method: dict[str, list[float]] = {m: [] for m in methods}

        for rand_ids_np in random_feature_sets:
            rand_ids = rand_ids_np.astype(np.int64)
            method_reductions: dict[str, list[float]] = {m: [] for m in methods}

            for i in range(n_rows):
                base_abs = float(
                    torch.mean(torch.abs(feats_high[i, rand_ids] - feats_low[i, rand_ids])).item()
                )
                high_vec = feats_high[i].clone()
                low_vec = feats_low[i]
                donor_vec = feats_high[donors[i]]

                for method in methods:
                    high_ab = _apply_feature_ablation(
                        high_vec,
                        donor_vec=donor_vec,
                        mean_vec=feature_mean,
                        feature_ids=rand_ids,
                        method=method,
                    )
                    ablated_abs = float(
                        torch.mean(torch.abs(high_ab[rand_ids] - low_vec[rand_ids])).item()
                    )
                    r = _reduction_fraction(base_abs, ablated_abs)
                    method_reductions[method].append(r)
                    random_prompt_reductions_by_method[method].append(r)

            for method in methods:
                random_set_means_by_method[method].append(float(np.mean(method_reductions[method])))

        method_report: dict[str, Any] = {}
        for method in methods:
            observed = np.asarray(observed_reductions_by_method[method], dtype=np.float64)
            random_means = np.asarray(random_set_means_by_method[method], dtype=np.float64)
            random_flat = np.asarray(random_prompt_reductions_by_method[method], dtype=np.float64)

            observed_mean = float(np.mean(observed)) if observed.size else None
            selectivity = (
                _random_baseline_selectivity(observed_mean, random_means)
                if observed_mean is not None
                else _random_baseline_selectivity(0.0, np.asarray([], dtype=np.float64))
            )

            effect_sizes = _effect_size_summary(
                observed,
                random_flat,
                seed=int(seed),
                n_bootstrap=int(n_bootstrap),
            )

            method_report[method] = {
                "observed_mean_reduction": observed_mean,
                "observed_median_reduction": float(np.median(observed)) if observed.size else None,
                "observed_mean_ci95": _bootstrap_mean_ci(
                    observed,
                    seed=int(seed),
                    n_bootstrap=int(n_bootstrap),
                ),
                "selectivity_vs_random": selectivity,
                "effect_sizes_vs_random_prompt_distribution": effect_sizes,
                "necessity_threshold_pass": bool(
                    observed_mean is not None and observed_mean >= necessity_threshold
                ),
                "selectivity_p_threshold_pass": bool(
                    selectivity.get("p_value_one_sided_ge") is not None
                    and float(selectivity["p_value_one_sided_ge"]) <= significance_threshold
                ),
            }

        claim_name = "machiavellian_disposition" if trait == "evil" else trait
        results_by_trait[trait] = {
            "claim_trait_name": claim_name,
            "n_prompts": n_rows,
            "target_set_size": len(target_ids),
            "target_feature_ids": target_ids,
            "methods": method_report,
            "evidence_status": {
                "necessity_proxy_feature_space": "observed",
                "behavioral_necessity": "unknown",
                "sufficiency": "unknown",
            },
            "limitations": [
                "Measures feature-space proxy necessity, not direct behavioral trait-score shift.",
                "Layer12 cross-SAE overlap limitation remains in force for cross-source claims.",
            ],
        }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "model_name": model_name,
            "sae_release": sae_release,
            "sae_id": sae_id,
            "layer": layer,
            "traits": traits,
            "random_baseline_samples": int(random_baseline_samples),
            "n_bootstrap": int(n_bootstrap),
            "seed": int(seed),
            "methods": methods,
        },
        "thresholds": {
            "necessity": necessity_threshold,
            "significance": significance_threshold,
        },
        "evidence_status": {
            "stage4_proxy_necessity": "observed",
            "behavioral_causal_validation": "unknown",
            "sufficiency_validation": "unknown",
        },
        "results_by_trait": results_by_trait,
    }


@app.local_entrypoint()
def main(
    target_freeze_artifact: str = DEFAULT_TARGET_FREEZE_ARTIFACT,
    traits: str = ",".join(DEFAULT_TRAITS),
    n_prompts: int = 30,
    random_baseline_samples: int = 100,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> None:
    cfg = _load_config()
    selected_traits = _parse_traits(traits)

    freeze_path = _resolve_path(target_freeze_artifact)
    freeze_payload = json.loads(freeze_path.read_text(encoding="utf-8"))

    target_sets_by_trait: dict[str, list[int]] = {}
    for trait in selected_traits:
        target_sets_by_trait[trait] = [
            int(x)
            for x in freeze_payload.get("targets_by_trait", {})
            .get(trait, {})
            .get("target_feature_ids", [])
        ]
        if not target_sets_by_trait[trait]:
            raise ValueError(f"Missing target_feature_ids in freeze artifact for trait={trait}")

    heldout_pairs_by_trait = {
        trait: _load_heldout_pairs(trait=trait, max_pairs=int(n_prompts))
        for trait in selected_traits
    }

    report = run_stage4_necessity_proxy_remote.remote(
        config=cfg,
        traits=selected_traits,
        target_sets_by_trait=target_sets_by_trait,
        heldout_pairs_by_trait=heldout_pairs_by_trait,
        random_baseline_samples=int(random_baseline_samples),
        n_bootstrap=int(n_bootstrap),
        seed=int(seed),
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"week3_stage4_necessity_proxy_ablation_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "artifact": str(out_path),
                "traits": selected_traits,
                "n_prompts": int(n_prompts),
                "random_baseline_samples": int(random_baseline_samples),
                "n_bootstrap": int(n_bootstrap),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
