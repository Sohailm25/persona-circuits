"""Week 3: investigate SAE reconstruction quality with explicit model/SAE alignment checks."""

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
import torch
import yaml

APP_NAME = "persona-circuits-week3-sae-reconstruction-investigation"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ["sycophancy", "evil", "hallucination"]
NEUTRAL_SYSTEM_PROMPT = "You are a helpful, honest, and concise assistant. Answer directly and accurately."

ROOT = Path(__file__).resolve().parents[1]
HELDOUT_DIR = ROOT / "prompts" / "heldout"
RESULTS_DIR = ROOT / "results" / "stage2_decomposition"
CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
STAGE1_RESULTS_DIR = ROOT / "results" / "stage1_extraction"

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


def _latest_result_path(glob_pattern: str) -> Path:
    matches = sorted(STAGE1_RESULTS_DIR.glob(glob_pattern))
    if not matches:
        raise FileNotFoundError(f"No files found for pattern: {glob_pattern}")
    return matches[-1]


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


def _format_chat_prompt(tokenizer: Any, user_query: str) -> str:
    messages = [
        {"role": "system", "content": NEUTRAL_SYSTEM_PROMPT},
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
    return f"System: {NEUTRAL_SYSTEM_PROMPT}\nUser: {user_query}\nAssistant:"


def _build_probe_rows(*, traits: list[str], samples_per_trait: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    output: list[dict[str, Any]] = []
    for trait in traits:
        path = HELDOUT_DIR / f"{trait}_heldout_pairs.jsonl"
        rows = _load_jsonl(path)
        idxs = list(range(len(rows)))
        rng.shuffle(idxs)
        selected = [rows[i] for i in idxs[: min(samples_per_trait, len(rows))]]
        for row in selected:
            output.append(
                {
                    "trait": trait,
                    "row_id": int(row.get("id", 0)),
                    "user_query": str(row.get("user_query", "")),
                }
            )
    if not output:
        raise ValueError("No probe rows selected.")
    return output


def _load_layer_vectors(*, vectors_path: Path, traits: list[str], layer: int) -> dict[str, list[float]]:
    payload = torch.load(vectors_path, map_location="cpu")
    by_trait: dict[str, list[float]] = {}
    for trait in traits:
        if trait not in payload:
            continue
        layer_payload = payload[trait]
        if str(layer) in layer_payload:
            vec = layer_payload[str(layer)]
        elif layer in layer_payload:
            vec = layer_payload[layer]
        else:
            continue
        arr = vec.tolist() if hasattr(vec, "tolist") else list(vec)
        by_trait[trait] = [float(x) for x in arr]
    return by_trait


def _summary_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "p10": None,
            "p90": None,
            "frac_lt_0_8": None,
            "frac_ge_0_9": None,
        }
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
        "frac_lt_0_8": float(np.mean(arr < 0.8)),
        "frac_ge_0_9": float(np.mean(arr >= 0.9)),
    }


def _pick_status(*, median_cos: float | None, median_ev: float | None) -> str:
    if median_cos is None or median_ev is None:
        return "unknown"
    if median_cos >= 0.9 and median_ev >= 0.9:
        return "pass"
    if median_cos >= 0.8 and median_ev >= 0.8:
        return "warning"
    return "fail"


def _aggregate_seed_reports(seed_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not seed_reports:
        return {"status_consistency_by_model": {}, "base_minus_instruct_median_cosine_by_seed": {}}

    status_by_model: dict[str, list[str]] = {}
    base_gap_by_seed: dict[str, float] = {}
    for seed_key, report in seed_reports.items():
        interp = report.get("interpretation", {})
        model_statuses = interp.get("status_by_model", {})
        for model_name, status in model_statuses.items():
            status_by_model.setdefault(str(model_name), []).append(str(status))
        gap = interp.get("base_minus_instruct_median_reconstruction_cosine")
        if gap is not None:
            base_gap_by_seed[seed_key] = float(gap)

    consistency: dict[str, Any] = {}
    for model_name, statuses in status_by_model.items():
        unique = sorted(set(statuses))
        consistency[model_name] = {
            "statuses": statuses,
            "unique_statuses": unique,
            "fully_consistent": len(unique) == 1,
        }

    gap_values = list(base_gap_by_seed.values())
    return {
        "status_consistency_by_model": consistency,
        "base_minus_instruct_median_cosine_by_seed": base_gap_by_seed,
        "base_minus_instruct_median_cosine_summary": (
            {
                "n": len(gap_values),
                "mean": float(np.mean(np.asarray(gap_values, dtype=np.float64))),
                "median": float(np.median(np.asarray(gap_values, dtype=np.float64))),
                "std": float(np.std(np.asarray(gap_values, dtype=np.float64))),
            }
            if gap_values
            else None
        ),
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=4 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_reconstruction_probe_remote(
    *,
    config: dict[str, Any],
    sae_source: str,
    layer: int,
    model_names: list[str],
    probe_rows: list[dict[str, Any]],
    trait_layer_vectors: dict[str, list[float]],
    seed: int,
) -> dict[str, Any]:
    import gc

    import torch
    import torch.nn.functional as F
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
    hook_name = f"blocks.{layer}.hook_resid_post"

    sae, _, _ = SAE.from_pretrained(
        release=sae_release,
        sae_id=sae_id,
        device="cuda",
    )
    sae = sae.to(dtype=torch.float32)
    sae.eval()

    decoder = sae.W_dec.detach().to(torch.float32)
    vector_projection: dict[str, Any] = {}
    for trait, values in trait_layer_vectors.items():
        direction = torch.tensor(values, dtype=torch.float32, device=decoder.device)
        direction_norm = float(direction.norm().item())
        if direction_norm <= 1e-8:
            vector_projection[trait] = {
                "evidence_status": "observed",
                "error": "zero_norm_trait_vector",
            }
            continue
        direction = direction / direction_norm
        coeff = torch.matmul(decoder, direction)
        coeff2 = coeff.pow(2)
        denom = float(coeff2.sum().item()) + 1e-8
        topk = min(100, int(coeff2.shape[0]))
        top_vals, top_idx = torch.topk(coeff2, k=topk)
        top_mass = float(top_vals.sum().item() / denom)

        selected = decoder[top_idx]
        selected = selected / (selected.norm(dim=1, keepdim=True) + 1e-8)
        if topk > 1:
            sim = selected @ selected.T
            mask = ~torch.eye(topk, device=sim.device, dtype=torch.bool)
            max_abs_cos = float(sim[mask].abs().max().item())
        else:
            max_abs_cos = 0.0

        vector_projection[trait] = {
            "evidence_status": "observed",
            "top_100_projection_mass": top_mass,
            "top_feature_pairwise_max_abs_cosine": max_abs_cos,
            "feature_splitting_risk_ge_0_4": bool(max_abs_cos >= 0.4),
        }

    per_model: dict[str, Any] = {}
    for model_name in model_names:
        model = HookedSAETransformer.from_pretrained(
            model_name,
            device="cuda",
            dtype=torch.bfloat16,
        )
        model.eval()

        per_trait: dict[str, dict[str, list[float]]] = {}
        overall_cos: list[float] = []
        overall_ev: list[float] = []
        overall_rel_err: list[float] = []
        overall_l0: list[float] = []
        overall_perm_cos: list[float] = []

        for row in probe_rows:
            trait = str(row["trait"])
            per_trait.setdefault(
                trait,
                {
                    "reconstruction_cosine": [],
                    "explained_variance": [],
                    "relative_error_norm": [],
                    "feature_l0_mean": [],
                    "permutation_recon_cosine": [],
                },
            )
            prompt = _format_chat_prompt(model.tokenizer, str(row["user_query"]))
            with torch.no_grad():
                tokens = model.to_tokens(prompt, prepend_bos=True)
                _, cache = model.run_with_cache(tokens, names_filter=lambda name: name == hook_name)
                acts = cache[hook_name][0].to(torch.float32)  # [seq, d_model]
                feats = sae.encode(acts)
                recon = sae.decode(feats)

                numerator = torch.dot(acts.flatten(), recon.flatten())
                denom = (acts.flatten().norm() * recon.flatten().norm()) + 1e-8
                recon_cos = float((numerator / denom).item())
                ev = float(
                    (
                        1.0
                        - ((acts - recon).pow(2).sum() / (acts.pow(2).sum() + 1e-8))
                    ).item()
                )
                rel_err = float((((acts - recon).norm()) / (acts.norm() + 1e-8)).item())
                l0_mean = float((feats.abs() > 1e-6).float().sum(dim=-1).mean().item())

                perm = torch.randperm(feats.shape[-1], device=feats.device)
                recon_perm = sae.decode(feats[:, perm])
                perm_num = torch.dot(acts.flatten(), recon_perm.flatten())
                perm_den = (acts.flatten().norm() * recon_perm.flatten().norm()) + 1e-8
                perm_cos = float((perm_num / perm_den).item())

            per_trait[trait]["reconstruction_cosine"].append(recon_cos)
            per_trait[trait]["explained_variance"].append(ev)
            per_trait[trait]["relative_error_norm"].append(rel_err)
            per_trait[trait]["feature_l0_mean"].append(l0_mean)
            per_trait[trait]["permutation_recon_cosine"].append(perm_cos)

            overall_cos.append(recon_cos)
            overall_ev.append(ev)
            overall_rel_err.append(rel_err)
            overall_l0.append(l0_mean)
            overall_perm_cos.append(perm_cos)

        trait_summaries: dict[str, Any] = {}
        for trait, metrics in per_trait.items():
            recon_stats = _summary_stats(metrics["reconstruction_cosine"])
            ev_stats = _summary_stats(metrics["explained_variance"])
            rel_err_stats = _summary_stats(metrics["relative_error_norm"])
            l0_stats = _summary_stats(metrics["feature_l0_mean"])
            perm_stats = _summary_stats(metrics["permutation_recon_cosine"])
            perm_gap = None
            if recon_stats["median"] is not None and perm_stats["median"] is not None:
                perm_gap = float(recon_stats["median"] - perm_stats["median"])

            trait_summaries[trait] = {
                "evidence_status": {
                    "reconstruction_metrics": "observed",
                    "permutation_control": "observed",
                },
                "reconstruction_cosine": recon_stats,
                "explained_variance": ev_stats,
                "relative_error_norm": rel_err_stats,
                "feature_l0_mean": l0_stats,
                "permutation_reconstruction_cosine": perm_stats,
                "permutation_median_gap": perm_gap,
                "status": _pick_status(
                    median_cos=recon_stats["median"],
                    median_ev=ev_stats["median"],
                ),
            }

        overall_recon = _summary_stats(overall_cos)
        overall_ev_stats = _summary_stats(overall_ev)
        overall_perm = _summary_stats(overall_perm_cos)
        overall_gap = None
        if overall_recon["median"] is not None and overall_perm["median"] is not None:
            overall_gap = float(overall_recon["median"] - overall_perm["median"])

        per_model[model_name] = {
            "evidence_status": {
                "overall_metrics": "observed",
                "trait_metrics": "observed",
            },
            "overall": {
                "reconstruction_cosine": overall_recon,
                "explained_variance": overall_ev_stats,
                "relative_error_norm": _summary_stats(overall_rel_err),
                "feature_l0_mean": _summary_stats(overall_l0),
                "permutation_reconstruction_cosine": overall_perm,
                "permutation_median_gap": overall_gap,
                "status": _pick_status(
                    median_cos=overall_recon["median"],
                    median_ev=overall_ev_stats["median"],
                ),
            },
            "by_trait": trait_summaries,
        }

        del model
        gc.collect()
        torch.cuda.empty_cache()

    status_map = {
        model_name: payload["overall"]["status"] for model_name, payload in per_model.items()
    }
    base_model_name = str(config["sae"]["primary"]["model"])
    instruct_model_name = str(config["models"]["primary"]["name"])
    base_recon = per_model.get(base_model_name, {}).get("overall", {}).get("reconstruction_cosine", {})
    instruct_recon = per_model.get(instruct_model_name, {}).get("overall", {}).get(
        "reconstruction_cosine", {}
    )
    base_med = base_recon.get("median")
    instruct_med = instruct_recon.get("median")
    median_gap = None
    if base_med is not None and instruct_med is not None:
        median_gap = float(base_med - instruct_med)

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "sae_source": sae_source,
            "layer": int(layer),
            "sae_release": sae_release,
            "sae_id": sae_id,
            "model_names": model_names,
            "n_probe_rows": len(probe_rows),
            "probe_traits": sorted({str(row["trait"]) for row in probe_rows}),
            "seed": int(seed),
        },
        "evidence_status": {
            "reconstruction_metrics": "observed",
            "permutation_control": "observed",
            "vector_projection_diagnostics": "observed" if vector_projection else "unknown",
            "base_vs_instruct_gap": "observed" if median_gap is not None else "unknown",
            "hook_mismatch_interpretation": "inferred",
        },
        "vector_projection_diagnostics": vector_projection,
        "model_results": per_model,
        "interpretation": {
            "status_by_model": status_map,
            "base_minus_instruct_median_reconstruction_cosine": median_gap,
            "possible_distribution_shift_signal": bool(median_gap is not None and median_gap > 0.1),
            "notes": [
                "known: pass/warning/fail thresholds follow policy: pass>=0.9, warning>=0.8, fail<0.8 for both median cosine and explained variance.",
                "inferred: large base-vs-instruct gap suggests model/SAE alignment risk rather than hook wiring failure.",
            ],
        },
    }


@app.local_entrypoint()
def main(
    sae_source: str = "primary",
    layer: int = 16,
    traits: str = ",".join(DEFAULT_TRAITS),
    samples_per_trait: int = 16,
    seed: int = -1,
    seed_schedule: str = "",
    model_names: str = "",
    vectors_path: str = "",
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

    vectors_artifact_path = Path(vectors_path) if vectors_path else _latest_result_path("week2_persona_vectors_*.pt")
    trait_layer_vectors = _load_layer_vectors(
        vectors_path=vectors_artifact_path,
        traits=selected_traits,
        layer=layer,
    )

    reports_by_seed: dict[str, dict[str, Any]] = {}
    for run_seed in resolved_seeds:
        probe_rows = _build_probe_rows(
            traits=selected_traits,
            samples_per_trait=samples_per_trait,
            seed=run_seed,
        )
        reports_by_seed[str(run_seed)] = run_reconstruction_probe_remote.remote(
            config=config,
            sae_source=sae_source,
            layer=int(layer),
            model_names=selected_models,
            probe_rows=probe_rows,
            trait_layer_vectors=trait_layer_vectors,
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
    out_path = RESULTS_DIR / f"week3_sae_reconstruction_investigation_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if "interpretation" in report:
        status_by_model = report["interpretation"]["status_by_model"]
        base_gap = report["interpretation"]["base_minus_instruct_median_reconstruction_cosine"]
    else:
        status_by_model = report.get("aggregate", {}).get("status_consistency_by_model", {})
        base_gap = report.get("aggregate", {}).get("base_minus_instruct_median_cosine_summary", {})

    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "seed_schedule": list(resolved_seeds),
                "status_by_model": status_by_model,
                "base_minus_instruct_median_reconstruction_cosine": base_gap,
            },
            indent=2,
        )
    )
