"""Week 3: root-cause diagnostics for SAE reconstruction mismatches."""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

APP_NAME = "persona-circuits-week3-sae-reconstruction-root-cause"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ["sycophancy", "evil", "hallucination"]
NEUTRAL_SYSTEM_PROMPT = "You are a helpful, honest, and concise assistant. Answer directly and accurately."

ROOT = Path(__file__).resolve().parents[1]
HELDOUT_DIR = ROOT / "prompts" / "heldout"
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


def _load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _normalize_csv_ints(raw: str) -> list[int]:
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    if not parts:
        raise ValueError("Seed schedule cannot be empty.")
    return [int(x) for x in parts]


def _resolve_seed_schedule(config: dict[str, Any], *, seed: int, seed_schedule: str) -> list[int]:
    if seed_schedule.strip():
        raw_values = _normalize_csv_ints(seed_schedule)
    elif seed >= 0:
        raw_values = [int(seed)]
    else:
        seed_cfg = config.get("seeds", {})
        primary = int(seed_cfg.get("primary", 42))
        replication = [int(x) for x in seed_cfg.get("replication", [])]
        raw_values = [primary, *replication]

    deduped: list[int] = []
    seen: set[int] = set()
    for value in raw_values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    if not deduped:
        raise ValueError("Resolved seed schedule is empty.")
    return deduped


def _build_probe_rows(*, traits: list[str], samples_per_trait: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    out: list[dict[str, Any]] = []
    for trait in traits:
        rows = _load_jsonl(HELDOUT_DIR / f"{trait}_heldout_pairs.jsonl")
        idxs = list(range(len(rows)))
        rng.shuffle(idxs)
        selected = [rows[i] for i in idxs[: min(samples_per_trait, len(rows))]]
        for row in selected:
            out.append(
                {
                    "trait": trait,
                    "row_id": int(row.get("id", 0)),
                    "user_query": str(row.get("user_query", "")),
                }
            )
    return out


def _format_chat_prompt(tokenizer: Any, user_query: str) -> str:
    messages = [
        {"role": "system", "content": NEUTRAL_SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except (TypeError, ValueError):
            pass
    return f"System: {NEUTRAL_SYSTEM_PROMPT}\nUser: {user_query}\nAssistant:"


def _summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "std": None, "p10": None, "p90": None}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
    }


def _aggregate_seed_reports(seed_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    if not seed_reports:
        return summary
    model_names: set[str] = set()
    for report in seed_reports.values():
        model_names.update(report.get("model_results", {}).keys())
    for model_name in sorted(model_names):
        best_variants: list[str] = []
        best_medians: list[float] = []
        for report in seed_reports.values():
            model_payload = report.get("model_results", {}).get(model_name, {})
            variant = model_payload.get("best_variant_by_median_cosine")
            if variant is not None:
                best_variants.append(str(variant))
            median = model_payload.get("best_variant_median_cosine")
            if median is not None:
                best_medians.append(float(median))
        summary[model_name] = {
            "best_variant_by_seed": best_variants,
            "best_variant_unique": sorted(set(best_variants)),
            "best_variant_consistent": len(set(best_variants)) == 1 if best_variants else None,
            "best_variant_median_cosine_summary": (
                {
                    "n": len(best_medians),
                    "mean": float(np.mean(np.asarray(best_medians, dtype=np.float64))),
                    "median": float(np.median(np.asarray(best_medians, dtype=np.float64))),
                    "std": float(np.std(np.asarray(best_medians, dtype=np.float64))),
                }
                if best_medians
                else None
            ),
        }
    return summary


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_root_cause_probe_remote(
    *,
    config: dict[str, Any],
    sae_source: str,
    layer: int,
    model_names: list[str],
    probe_rows: list[dict[str, Any]],
    seed: int,
) -> dict[str, Any]:
    import gc

    import torch
    from sae_lens import SAE, HookedSAETransformer

    _set_modal_cache_env()
    _seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    if sae_source not in {"primary", "cross_check"}:
        raise ValueError(f"Unsupported sae_source={sae_source}")

    sae_block = config["sae"]["primary"] if sae_source == "primary" else config["sae"]["cross_check"]
    allowed_layers = [int(x) for x in sae_block["layers"]]
    if layer not in allowed_layers:
        raise ValueError(
            f"Layer {layer} unavailable for sae_source={sae_source}; available_layers={allowed_layers}"
        )

    sae_release = str(sae_block["release"])
    sae_id = str(sae_block["sae_id_format"]).format(layer=layer)
    configured_hook = f"blocks.{layer}.hook_resid_post"

    sae, _, _ = SAE.from_pretrained(
        release=sae_release,
        sae_id=sae_id,
        device="cuda",
    )
    sae = sae.to(dtype=torch.float32)
    sae.eval()

    sae_cfg = sae.cfg
    expected_hook_name = str(getattr(sae_cfg, "hook_name", "")) or None
    expected_hook_layer = getattr(sae_cfg, "hook_layer", None)
    expected_hook_head_index = getattr(sae_cfg, "hook_head_index", None)
    expected_prepend_bos = getattr(sae_cfg, "prepend_bos", None)
    expected_normalize_activations = getattr(sae_cfg, "normalize_activations", None)
    expected_activation_fn_str = str(getattr(sae_cfg, "activation_fn_str", "unknown"))

    hook_candidates = [configured_hook]
    if expected_hook_name and expected_hook_name not in hook_candidates:
        hook_candidates.append(expected_hook_name)

    per_model: dict[str, Any] = {}
    for model_name in model_names:
        model = HookedSAETransformer.from_pretrained(
            model_name,
            device="cuda",
            dtype=torch.bfloat16,
        )
        model.eval()

        rows_diag: list[dict[str, Any]] = []
        per_variant: dict[str, dict[str, list[float]]] = {}
        for hook_name in hook_candidates:
            for variant_name in ["raw_seq", "last_token", "token_centered", "token_unit_norm"]:
                key = f"{hook_name}::{variant_name}"
                per_variant[key] = {
                    "reconstruction_cosine": [],
                    "explained_variance": [],
                    "relative_error_norm": [],
                    "feature_l0_mean": [],
                    "act_norm_mean": [],
                    "recon_norm_mean": [],
                }

        for row in probe_rows:
            prompt = _format_chat_prompt(model.tokenizer, str(row["user_query"]))
            with torch.no_grad():
                tokens = model.to_tokens(prompt, prepend_bos=True)
                _, cache = model.run_with_cache(tokens, names_filter=lambda name: name in set(hook_candidates))

            row_record: dict[str, Any] = {
                "trait": row["trait"],
                "row_id": row["row_id"],
                "hooks_observed": sorted(cache.keys()),
                "hook_variant_metrics": {},
            }

            for hook_name in hook_candidates:
                if hook_name not in cache:
                    row_record["hook_variant_metrics"][hook_name] = {"missing": True}
                    continue

                acts_full = cache[hook_name][0].to(torch.float32)  # [seq, d_model]
                acts_variants = {
                    "raw_seq": acts_full,
                    "last_token": acts_full[-1:, :],
                    "token_centered": acts_full - acts_full.mean(dim=-1, keepdim=True),
                    "token_unit_norm": acts_full / (acts_full.norm(dim=-1, keepdim=True) + 1e-8),
                }
                row_record["hook_variant_metrics"][hook_name] = {}

                for variant_name, acts in acts_variants.items():
                    with torch.no_grad():
                        feats = sae.encode(acts)
                        recon = sae.decode(feats)
                        recon_cos = float(
                            (
                                torch.dot(acts.flatten(), recon.flatten())
                                / ((acts.flatten().norm() * recon.flatten().norm()) + 1e-8)
                            ).item()
                        )
                        ev = float(
                            (
                                1.0
                                - ((acts - recon).pow(2).sum() / (acts.pow(2).sum() + 1e-8))
                            ).item()
                        )
                        rel_err = float((((acts - recon).norm()) / (acts.norm() + 1e-8)).item())
                        l0_mean = float((feats.abs() > 1e-6).float().sum(dim=-1).mean().item())
                        act_norm_mean = float(acts.norm(dim=-1).mean().item())
                        recon_norm_mean = float(recon.norm(dim=-1).mean().item())

                    key = f"{hook_name}::{variant_name}"
                    per_variant[key]["reconstruction_cosine"].append(recon_cos)
                    per_variant[key]["explained_variance"].append(ev)
                    per_variant[key]["relative_error_norm"].append(rel_err)
                    per_variant[key]["feature_l0_mean"].append(l0_mean)
                    per_variant[key]["act_norm_mean"].append(act_norm_mean)
                    per_variant[key]["recon_norm_mean"].append(recon_norm_mean)

                    row_record["hook_variant_metrics"][hook_name][variant_name] = {
                        "reconstruction_cosine": recon_cos,
                        "explained_variance": ev,
                        "relative_error_norm": rel_err,
                        "feature_l0_mean": l0_mean,
                        "act_norm_mean": act_norm_mean,
                        "recon_norm_mean": recon_norm_mean,
                    }

            rows_diag.append(row_record)

        variants_summary: dict[str, Any] = {}
        for key, metrics in per_variant.items():
            variants_summary[key] = {
                "reconstruction_cosine": _summary(metrics["reconstruction_cosine"]),
                "explained_variance": _summary(metrics["explained_variance"]),
                "relative_error_norm": _summary(metrics["relative_error_norm"]),
                "feature_l0_mean": _summary(metrics["feature_l0_mean"]),
                "act_norm_mean": _summary(metrics["act_norm_mean"]),
                "recon_norm_mean": _summary(metrics["recon_norm_mean"]),
            }

        best_variant = None
        best_median = float("-inf")
        for key, payload in variants_summary.items():
            med = payload["reconstruction_cosine"]["median"]
            if med is not None and med > best_median:
                best_median = float(med)
                best_variant = key

        hook_delta = None
        if expected_hook_name:
            exp_key = f"{expected_hook_name}::raw_seq"
            cfg_key = f"{configured_hook}::raw_seq"
            exp_med = variants_summary.get(exp_key, {}).get("reconstruction_cosine", {}).get("median")
            cfg_med = variants_summary.get(cfg_key, {}).get("reconstruction_cosine", {}).get("median")
            if exp_med is not None and cfg_med is not None:
                hook_delta = float(exp_med - cfg_med)

        centered_gain = None
        unit_norm_gain = None
        raw_key = f"{configured_hook}::raw_seq"
        ctr_key = f"{configured_hook}::token_centered"
        un_key = f"{configured_hook}::token_unit_norm"
        raw_med = variants_summary.get(raw_key, {}).get("reconstruction_cosine", {}).get("median")
        ctr_med = variants_summary.get(ctr_key, {}).get("reconstruction_cosine", {}).get("median")
        un_med = variants_summary.get(un_key, {}).get("reconstruction_cosine", {}).get("median")
        if raw_med is not None and ctr_med is not None:
            centered_gain = float(ctr_med - raw_med)
        if raw_med is not None and un_med is not None:
            unit_norm_gain = float(un_med - raw_med)

        per_model[model_name] = {
            "rows": rows_diag,
            "variants_summary": variants_summary,
            "best_variant_by_median_cosine": best_variant,
            "best_variant_median_cosine": best_median if best_variant else None,
            "hook_rawseq_median_delta_expected_minus_configured": hook_delta,
            "configured_raw_to_centered_median_gain": centered_gain,
            "configured_raw_to_unitnorm_median_gain": unit_norm_gain,
            "inferred_flags": {
                "hook_mismatch_likely": bool(hook_delta is not None and hook_delta > 0.05),
                "centering_or_scale_mismatch_likely": bool(
                    (centered_gain is not None and centered_gain > 0.05)
                    or (unit_norm_gain is not None and unit_norm_gain > 0.05)
                ),
            },
        }

        del model
        gc.collect()
        torch.cuda.empty_cache()

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "sae_source": sae_source,
            "layer": int(layer),
            "sae_release": sae_release,
            "sae_id": sae_id,
            "configured_hook": configured_hook,
            "expected_hook_name": expected_hook_name,
            "model_names": model_names,
            "n_probe_rows": len(probe_rows),
            "probe_traits": sorted({str(row["trait"]) for row in probe_rows}),
            "seed": int(seed),
        },
        "sae_cfg_snapshot": {
            "hook_name": expected_hook_name,
            "hook_layer": expected_hook_layer,
            "hook_head_index": expected_hook_head_index,
            "prepend_bos": expected_prepend_bos,
            "normalize_activations": str(expected_normalize_activations),
            "activation_fn_str": expected_activation_fn_str,
            "d_in": int(getattr(sae_cfg, "d_in", 0)),
            "d_sae": int(getattr(sae_cfg, "d_sae", 0)),
        },
        "evidence_status": {
            "variant_metrics": "observed",
            "hook_name_alignment": "observed" if expected_hook_name else "unknown",
            "root_cause_flags": "inferred",
        },
        "model_results": per_model,
    }


@app.local_entrypoint()
def main(
    sae_source: str = "primary",
    layer: int = 16,
    traits: str = ",".join(DEFAULT_TRAITS),
    samples_per_trait: int = 4,
    seed: int = -1,
    seed_schedule: str = "",
    model_names: str = "",
) -> None:
    selected_traits = [t.strip() for t in traits.split(",") if t.strip()]
    if not selected_traits:
        raise ValueError("No traits selected.")
    if samples_per_trait <= 0:
        raise ValueError("--samples-per-trait must be > 0")

    config = _load_config()
    resolved_seeds = _resolve_seed_schedule(config, seed=seed, seed_schedule=seed_schedule)

    if model_names.strip():
        selected_models = [m.strip() for m in model_names.split(",") if m.strip()]
    else:
        selected_models = []
        if sae_source == "primary":
            selected_models.append(str(config["sae"]["primary"]["model"]))
        selected_models.append(str(config["models"]["primary"]["name"]))
        selected_models = list(dict.fromkeys(selected_models))

    reports_by_seed: dict[str, dict[str, Any]] = {}
    for run_seed in resolved_seeds:
        probe_rows = _build_probe_rows(
            traits=selected_traits,
            samples_per_trait=samples_per_trait,
            seed=run_seed,
        )
        reports_by_seed[str(run_seed)] = run_root_cause_probe_remote.remote(
            config=config,
            sae_source=sae_source,
            layer=int(layer),
            model_names=selected_models,
            probe_rows=probe_rows,
            seed=run_seed,
        )

    if len(resolved_seeds) == 1:
        report = reports_by_seed[str(resolved_seeds[0])]
        report["seed_schedule"] = list(resolved_seeds)
    else:
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_status": {
                "seed_reports": "observed",
                "seed_aggregate": "inferred",
            },
            "seed_schedule": list(resolved_seeds),
            "seed_reports": reports_by_seed,
            "aggregate": _aggregate_seed_reports(reports_by_seed),
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week3_sae_reconstruction_root_cause_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "seed_schedule": list(resolved_seeds),
                "configured_hook": report.get("inputs", {}).get("configured_hook"),
                "expected_hook_name": report.get("inputs", {}).get("expected_hook_name"),
                "models": selected_models,
            },
            indent=2,
        )
    )
