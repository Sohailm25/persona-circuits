#!/usr/bin/env python3
"""Week 3 exploratory GLP meta-neuron screen.

This runner is intentionally isolated from the primary Week 3/4/5 lanes. It treats GLP
internal activations as exploratory sensors for persona subfacet discovery, not as direct
causal claims about base-model circuits.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

try:
    from scripts import week3_stage4_behavioral_ablation as base
except ModuleNotFoundError:  # pragma: no cover - direct script invocation fallback
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import week3_stage4_behavioral_ablation as base

from scripts.shared.glp_metrics import cosine_similarity
from scripts.shared.glp_runtime import build_glp_alignment_report, resolve_glp_metadata

APP_NAME = "persona-circuits-week3-glp-meta-neuron-screen"

ROOT = base.ROOT
SIDECAR_CONFIG_PATH = ROOT / "configs" / "glp_sidecar.yaml"
OUT_DIR = ROOT / "results" / "glp_sidecar"
DEFAULT_TRAITS = ["sycophancy", "evil"]
DEFAULT_LOCATION = "input"
ALLOWED_CAPTURE_LOCATIONS = {"input", "output"}

app = modal.App(APP_NAME)
vol = base.vol
image = modal.Image.debian_slim(python_version="3.11").apt_install("git").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "pyyaml",
        "numpy",
        "omegaconf",
        "diffusers",
        "einops",
        "safetensors",
        "huggingface_hub",
        "git+https://github.com/davidbau/baukit.git",
        "git+https://github.com/g-luo/generative_latent_prior.git",
    ]
).add_local_dir(ROOT / "scripts", remote_path="/root/scripts")


def _load_sidecar_config() -> dict[str, Any]:
    raw = yaml.safe_load(SIDECAR_CONFIG_PATH.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _hash_json_rows(rows: list[dict[str, Any]]) -> str:
    canonical = "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_behavioral_source_settings(
    *,
    payload: dict[str, Any],
    trait: str,
    source_artifact_path: str,
) -> dict[str, Any]:
    trait_payload: dict[str, Any]
    run_metadata: dict[str, Any]

    if isinstance(payload.get("traits"), dict) and trait in payload["traits"]:
        trait_payload = payload["traits"][trait]
        run_metadata = payload.get("run_metadata", {}) if isinstance(payload.get("run_metadata"), dict) else {}
    else:
        payload_trait = str(payload.get("trait", trait))
        if payload_trait != trait:
            raise ValueError(
                f"Behavioral source trait mismatch for {source_artifact_path}: expected {trait}, found {payload_trait}"
            )
        trait_payload = payload
        run_metadata = payload.get("run_metadata", {}) if isinstance(payload.get("run_metadata"), dict) else {}

    selected = trait_payload.get("selected", {})
    if not isinstance(selected, dict) or "layer" not in selected or "alpha" not in selected:
        raise ValueError(f"Missing selected.layer/selected.alpha in {source_artifact_path}")

    return {
        "trait": trait,
        "source_artifact": source_artifact_path,
        "layer": int(selected["layer"]),
        "alpha": float(selected["alpha"]),
        "max_new_tokens": int(run_metadata.get("max_new_tokens", base.DEFAULT_MAX_NEW_TOKENS)),
        "temperature": float(run_metadata.get("temperature", base.DEFAULT_TEMPERATURE)),
    }


def _resolve_u_values(raw: str, fallback: Any) -> list[float]:
    if str(raw).strip():
        values = [float(x.strip()) for x in str(raw).split(",") if x.strip()]
    elif isinstance(fallback, list):
        values = [float(x) for x in fallback]
    elif isinstance(fallback, str) and fallback.strip():
        values = [float(x.strip()) for x in fallback.split(",") if x.strip()]
    else:
        values = [0.5]
    deduped: list[float] = []
    seen: set[float] = set()
    for value in values:
        if value < 0.0 or value > 1.0:
            raise ValueError("u_values must be in [0, 1].")
        if value not in seen:
            deduped.append(float(value))
            seen.add(float(value))
    if not deduped:
        raise ValueError("u_values cannot be empty")
    return deduped


def _resolve_capture_sites(fallback: Any) -> list[dict[str, str]]:
    if not isinstance(fallback, list) or not fallback:
        return [
            {
                "label": "down_proj_input",
                "layer_prefix": "denoiser.model.layers.{i}.down_proj",
                "location": DEFAULT_LOCATION,
            }
        ]
    out: list[dict[str, str]] = []
    for row in fallback:
        if not isinstance(row, dict):
            continue
        layer_prefix = str(row.get("layer_prefix", "")).strip()
        location = str(row.get("location", DEFAULT_LOCATION)).strip().lower()
        label = str(row.get("label", f"{layer_prefix}:{location}")).strip()
        if not layer_prefix:
            continue
        if location not in ALLOWED_CAPTURE_LOCATIONS:
            raise ValueError(
                f"Unsupported capture site location={location}. Allowed: {sorted(ALLOWED_CAPTURE_LOCATIONS)}"
            )
        out.append(
            {
                "label": label,
                "layer_prefix": layer_prefix,
                "location": location,
            }
        )
    if not out:
        raise ValueError("capture_sites must contain at least one valid site")
    return out


def _build_capture_targets(num_denoiser_layers: int, capture_sites: list[dict[str, str]]) -> list[dict[str, Any]]:
    if int(num_denoiser_layers) <= 0:
        raise ValueError("num_denoiser_layers must be > 0")
    targets: list[dict[str, Any]] = []
    for site_idx, site in enumerate(capture_sites):
        layer_prefix = str(site["layer_prefix"])
        location = str(site["location"])
        label = str(site["label"])
        for denoiser_layer in range(int(num_denoiser_layers)):
            targets.append(
                {
                    "capture_target_index": int(len(targets)),
                    "site_index": int(site_idx),
                    "site_label": label,
                    "layer_name": layer_prefix.format(i=denoiser_layer),
                    "location": location,
                    "denoiser_layer": int(denoiser_layer),
                }
            )
    return targets


def _feature_identifier(*, u_index: int, capture_target_index: int, neuron_dim: int) -> str:
    return f"u{int(u_index)}:c{int(capture_target_index)}:d{int(neuron_dim)}"


def _rank_meta_neurons(
    *,
    meta_features: Any,
    labels: Any,
    capture_targets: list[dict[str, Any]],
    u_values: list[float],
    top_k: int,
) -> dict[str, Any]:
    arr = np.asarray(meta_features, dtype=np.float64)
    label_arr = np.asarray(labels, dtype=np.int64).reshape(-1)
    if arr.ndim != 4:
        raise ValueError("meta_features must have shape [n_samples, n_u, n_capture_targets, d_model]")
    if arr.shape[0] != label_arr.shape[0]:
        raise ValueError("labels length must match n_samples")
    if set(np.unique(label_arr).tolist()) - {0, 1}:
        raise ValueError("labels must be binary 0/1")
    positives = arr[label_arr == 1]
    negatives = arr[label_arr == 0]
    if positives.size == 0 or negatives.size == 0:
        raise ValueError("meta-neuron screen requires both positive and negative labels")

    mean_high = np.mean(positives, axis=0)
    mean_low = np.mean(negatives, axis=0)
    mean_delta = mean_high - mean_low
    abs_delta = np.abs(mean_delta)
    flat_abs = abs_delta.reshape(-1)
    resolved_top_k = max(1, min(int(top_k), int(flat_abs.size)))
    top_indices = np.argpartition(-flat_abs, resolved_top_k - 1)[:resolved_top_k]
    top_indices = top_indices[np.argsort(-flat_abs[top_indices])]

    top_rows: list[dict[str, Any]] = []
    top_feature_ids: list[str] = []
    for rank, flat_idx in enumerate(top_indices, start=1):
        u_idx, capture_idx, neuron_dim = np.unravel_index(int(flat_idx), abs_delta.shape)
        high_vals = positives[:, u_idx, capture_idx, neuron_dim]
        low_vals = negatives[:, u_idx, capture_idx, neuron_dim]
        capture_target = capture_targets[int(capture_idx)]
        feature_id = _feature_identifier(
            u_index=int(u_idx),
            capture_target_index=int(capture_idx),
            neuron_dim=int(neuron_dim),
        )
        top_feature_ids.append(feature_id)
        top_rows.append(
            {
                "rank": int(rank),
                "feature_identifier": feature_id,
                "u_index": int(u_idx),
                "u_value": float(u_values[int(u_idx)]),
                "capture_target_index": int(capture_idx),
                "site_label": capture_target["site_label"],
                "layer_name": capture_target["layer_name"],
                "location": capture_target["location"],
                "denoiser_layer": int(capture_target["denoiser_layer"]),
                "neuron_dim": int(neuron_dim),
                "mean_low": float(mean_low[u_idx, capture_idx, neuron_dim]),
                "mean_high": float(mean_high[u_idx, capture_idx, neuron_dim]),
                "mean_delta": float(mean_delta[u_idx, capture_idx, neuron_dim]),
                "abs_mean_delta": float(abs_delta[u_idx, capture_idx, neuron_dim]),
                "cohens_d": base._cohens_d(high_vals, low_vals),
                "a12": base._a12(high_vals, low_vals),
            }
        )

    capture_score_sums = np.sum(abs_delta, axis=(0, 2))
    capture_score_means = np.mean(abs_delta, axis=(0, 2))
    concentration_by_capture_target = []
    for capture_idx, capture_target in enumerate(capture_targets):
        concentration_by_capture_target.append(
            {
                "capture_target_index": int(capture_idx),
                "site_label": capture_target["site_label"],
                "layer_name": capture_target["layer_name"],
                "location": capture_target["location"],
                "denoiser_layer": int(capture_target["denoiser_layer"]),
                "score_sum": float(capture_score_sums[capture_idx]),
                "score_mean": float(capture_score_means[capture_idx]),
            }
        )
    concentration_by_capture_target.sort(key=lambda row: row["score_sum"], reverse=True)

    u_score_sums = np.sum(abs_delta, axis=(1, 2))
    u_score_means = np.mean(abs_delta, axis=(1, 2))
    concentration_by_u = []
    for u_idx, u_value in enumerate(u_values):
        concentration_by_u.append(
            {
                "u_index": int(u_idx),
                "u_value": float(u_value),
                "score_sum": float(u_score_sums[u_idx]),
                "score_mean": float(u_score_means[u_idx]),
            }
        )
    concentration_by_u.sort(key=lambda row: row["score_sum"], reverse=True)

    flat_delta = mean_delta.reshape(-1)
    centroid_low = mean_low.reshape(-1)
    centroid_high = mean_high.reshape(-1)
    screening_summary = {
        "n_examples": int(arr.shape[0]),
        "n_positive_examples": int(positives.shape[0]),
        "n_negative_examples": int(negatives.shape[0]),
        "mean_delta_summary": base._array_summary(flat_delta),
        "abs_mean_delta_summary": base._array_summary(flat_abs),
        "topk_abs_mean_delta_sum": float(np.sum([row["abs_mean_delta"] for row in top_rows])),
        "topk_abs_mean_delta_mean": float(np.mean([row["abs_mean_delta"] for row in top_rows])),
        "centroid_cosine_low_vs_high": cosine_similarity(centroid_low, centroid_high),
    }
    return {
        "top_meta_neurons": top_rows,
        "top_feature_identifiers": top_feature_ids,
        "concentration_by_capture_target": concentration_by_capture_target,
        "concentration_by_u": concentration_by_u,
        "screening_summary": screening_summary,
    }


def _build_cross_trait_overlap(results_by_trait: dict[str, Any]) -> dict[str, Any]:
    traits = sorted(results_by_trait.keys())
    pairwise: dict[str, Any] = {}
    for idx, trait_a in enumerate(traits):
        set_a = set(results_by_trait[trait_a].get("top_feature_identifiers", []))
        for trait_b in traits[idx + 1 :]:
            set_b = set(results_by_trait[trait_b].get("top_feature_identifiers", []))
            union = set_a | set_b
            shared = set_a & set_b
            key = f"{trait_a}__{trait_b}"
            pairwise[key] = {
                "trait_a": trait_a,
                "trait_b": trait_b,
                "top_feature_count_a": int(len(set_a)),
                "top_feature_count_b": int(len(set_b)),
                "shared_feature_count": int(len(shared)),
                "jaccard": (float(len(shared)) / float(len(union))) if union else 0.0,
                "shared_feature_preview": sorted(shared)[:20],
            }
    return {
        "pairwise_top_feature_overlap": pairwise,
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=8 * 60 * 60,
    secrets=[modal.Secret.from_name("hf-token")],
    volumes={"/models": vol},
)
def run_week3_glp_meta_neuron_screen_remote(
    *,
    config: dict[str, Any],
    sidecar_config: dict[str, Any],
    traits: list[str],
    heldout_pairs_by_trait: dict[str, list[dict[str, Any]]],
    heldout_hashes_by_trait: dict[str, str],
    behavioral_source_by_trait: dict[str, dict[str, Any]],
    glp_weights_folder: str,
    glp_checkpoint: str,
    u_values: list[float],
    top_k_neurons: int,
    batch_size: int,
    capture_sites: list[dict[str, str]],
    seed: int,
    output_suffix: str,
) -> dict[str, Any]:
    import torch
    from baukit import TraceDict
    from glp.denoiser import load_glp
    from sae_lens import HookedSAETransformer

    base._set_modal_cache_env()
    base._seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    model_name = str(config["models"]["primary"]["name"])
    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    model.eval()

    glp_model = load_glp(glp_weights_folder, device="cuda", checkpoint=glp_checkpoint)
    glp_metadata = resolve_glp_metadata(
        weights_folder=glp_weights_folder,
        checkpoint=glp_checkpoint,
        metadata_override=sidecar_config.get("glp", {}).get("metadata") if isinstance(sidecar_config.get("glp"), dict) else None,
    )
    num_denoiser_layers = int(len(glp_model.denoiser.model.layers))
    capture_targets = _build_capture_targets(num_denoiser_layers, capture_sites)

    def _extract_meta_tensor(*, resid_matrix: Any, layer_idx: int) -> Any:
        generator = torch.Generator().manual_seed(int(seed))
        x = resid_matrix.to(device="cuda", dtype=torch.float32)
        n_samples = int(x.shape[0])
        n_u = int(len(u_values))
        u_tensor = torch.tensor(u_values, dtype=torch.float32, device="cuda")[:, None]
        x_expanded = x[:, None, :].repeat(1, n_u, 1).reshape(n_samples * n_u, x.shape[-1])
        u_expanded = u_tensor[None, :, :].repeat(n_samples, 1, 1).reshape(n_samples * n_u, 1)
        latents = glp_model.normalizer.normalize(x_expanded[:, None, :], layer_idx=int(layer_idx))
        traced_layers = list(dict.fromkeys(target["layer_name"] for target in capture_targets))
        batches: list[Any] = []
        resolved_batch_size = max(1, int(batch_size))
        for start in range(0, latents.shape[0], resolved_batch_size):
            batch_latents = latents[start : start + resolved_batch_size]
            batch_u = u_expanded[start : start + resolved_batch_size]
            with TraceDict(glp_model, layers=traced_layers, retain_input=True, retain_output=True) as traced:
                _ = glp_model(
                    latents=batch_latents,
                    u=batch_u,
                    layer_idx=int(layer_idx),
                    generator=generator,
                )
            batch_rows = []
            for target in capture_targets:
                value = getattr(traced[target["layer_name"]], target["location"])
                if isinstance(value, (tuple, list)):
                    value = value[0]
                tensor = value.detach().to("cpu")
                if tensor.ndim == 3:
                    tensor = tensor[:, -1, :]
                elif tensor.ndim != 2:
                    raise ValueError(
                        f"Unexpected captured tensor shape for {target['layer_name']}: {tuple(tensor.shape)}"
                    )
                batch_rows.append(tensor)
            batch_stack = torch.stack(batch_rows, dim=1)  # [batch, n_capture_targets, d_model]
            batches.append(batch_stack)
        stacked = torch.cat(batches, dim=0)
        return stacked.reshape(n_samples, n_u, len(capture_targets), stacked.shape[-1]).numpy()

    results_by_trait: dict[str, Any] = {}
    top_feature_ids_by_trait: dict[str, list[str]] = {}

    for trait in traits:
        if trait not in behavioral_source_by_trait:
            raise ValueError(f"Missing behavioral source settings for trait={trait}")
        rows = heldout_pairs_by_trait[trait]
        source = behavioral_source_by_trait[trait]
        layer = int(source["layer"])
        glp_alignment = build_glp_alignment_report(
            metadata=glp_metadata,
            target_model_name=model_name,
            target_layer=layer,
        )
        hook_name = base._hook_name_for_layer(layer)
        residual_rows = []
        labels = []
        prompt_rows = []
        for row_index, row in enumerate(rows):
            for state_label, state_key in ((0, "system_low"), (1, "system_high")):
                prompt_text = base._format_chat_prompt(
                    model.tokenizer,
                    str(row[state_key]),
                    str(row["user_query"]),
                )
                with torch.no_grad():
                    tokens = model.to_tokens(prompt_text, prepend_bos=True)
                    _, cache = model.run_with_cache(
                        tokens,
                        names_filter=lambda name, target=hook_name: name == target,
                    )
                    resid_last = cache[hook_name][0, -1, :].to(torch.float32).detach().cpu()
                residual_rows.append(resid_last)
                labels.append(int(state_label))
                prompt_rows.append(
                    {
                        "pair_index": int(row_index),
                        "label": int(state_label),
                        "state_key": state_key,
                        "user_query": str(row["user_query"]),
                    }
                )
        residual_matrix = torch.stack(residual_rows, dim=0)
        meta_features = _extract_meta_tensor(resid_matrix=residual_matrix, layer_idx=layer)
        ranked = _rank_meta_neurons(
            meta_features=meta_features,
            labels=np.asarray(labels, dtype=np.int64),
            capture_targets=capture_targets,
            u_values=u_values,
            top_k=int(top_k_neurons),
        )
        top_feature_ids_by_trait[trait] = ranked["top_feature_identifiers"]
        results_by_trait[trait] = {
            "claim_trait_name": base._trait_label(trait),
            "n_pairs": int(len(rows)),
            "n_examples": int(len(labels)),
            "heldout_hash": heldout_hashes_by_trait[trait],
            "steering_source": {
                "source_artifact": source["source_artifact"],
                "layer": int(layer),
                "alpha": float(source["alpha"]),
            },
            "glp_alignment": glp_alignment,
            "capture_schema": {
                "n_capture_targets": int(len(capture_targets)),
                "capture_targets": capture_targets,
                "u_values": [float(x) for x in u_values],
                "batch_size": int(batch_size),
            },
            "label_definition": {
                "0": "system_low_activation",
                "1": "system_high_activation",
            },
            **ranked,
            "prompt_rows_preview": prompt_rows[: min(10, len(prompt_rows))],
            "evidence_status": {
                "meta_neuron_screen": "observed",
                "causal_base_model_interpretation": "no",
                "claim_grade_ready": "no" if not glp_alignment.get("claim_grade_ready") else "partial",
            },
            "limitations": [
                "GLP meta-neurons are exploratory learned features, not direct causal units of the base model.",
                "Screen uses prompt-state contrasts (system_low vs system_high), not generation-time behavioral interventions.",
                "Model/layer mismatch keeps this diagnostic unless a matched GLP is trained.",
            ],
        }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_glp_meta_neuron_screen",
        "analysis_target": "exploratory_glp_meta_neuron_screen",
        "inputs": {
            "traits": traits,
            "glp_weights_folder": glp_weights_folder,
            "glp_checkpoint": glp_checkpoint,
            "u_values": [float(x) for x in u_values],
            "top_k_neurons": int(top_k_neurons),
            "batch_size": int(batch_size),
            "capture_sites": capture_sites,
            "seed": int(seed),
            "output_suffix": output_suffix,
        },
        "results_by_trait": results_by_trait,
        "cross_trait_overlap": _build_cross_trait_overlap(
            {trait: {"top_feature_identifiers": ids} for trait, ids in top_feature_ids_by_trait.items()}
        ),
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    behavioral_source_artifact_map: str = "",
    n_prompts: int = -1,
    heldout_start_index: int = -1,
    glp_weights_folder: str = "",
    glp_checkpoint: str = "",
    u_values: str = "",
    top_k_neurons: int = -1,
    batch_size: int = -1,
    output_suffix: str = "",
    seed: int = 42,
) -> None:
    config = base._load_config()
    sidecar_config = _load_sidecar_config()
    glp_cfg = sidecar_config.get("glp", {}) if isinstance(sidecar_config.get("glp"), dict) else {}
    meta_cfg = sidecar_config.get("week3_meta_neuron_sidecar", {}) if isinstance(sidecar_config.get("week3_meta_neuron_sidecar"), dict) else {}

    selected_traits = base._parse_traits(traits)
    source_map_raw = base._parse_artifact_map(behavioral_source_artifact_map)
    source_paths_by_trait: dict[str, Path] = {}
    for trait in selected_traits:
        if trait in source_map_raw:
            source_paths_by_trait[trait] = base._resolve_path(source_map_raw[trait])
        else:
            source_paths_by_trait[trait] = base._latest_result_path(
                base.STAGE1_RESULTS_DIR,
                f"week2_behavioral_validation_upgrade_{trait}_*.json",
            )

    resolved_n_prompts = int(n_prompts) if int(n_prompts) > 0 else int(meta_cfg.get("n_prompts", 12))
    resolved_heldout_start_index = int(heldout_start_index) if int(heldout_start_index) >= 0 else int(meta_cfg.get("heldout_start_index", 0))
    heldout_pairs_by_trait = {
        trait: base._load_heldout_pairs(
            trait=trait,
            max_pairs=resolved_n_prompts,
            start_index=resolved_heldout_start_index,
        )
        for trait in selected_traits
    }
    heldout_hashes_by_trait = {
        trait: _hash_json_rows(rows) for trait, rows in heldout_pairs_by_trait.items()
    }

    behavioral_source_by_trait: dict[str, dict[str, Any]] = {}
    for trait in selected_traits:
        payload = json.loads(source_paths_by_trait[trait].read_text(encoding="utf-8"))
        behavioral_source_by_trait[trait] = _extract_behavioral_source_settings(
            payload=payload,
            trait=trait,
            source_artifact_path=str(source_paths_by_trait[trait]),
        )

    resolved_glp_weights_folder = str(glp_weights_folder or glp_cfg.get("weights_folder", ""))
    resolved_glp_checkpoint = str(glp_checkpoint or glp_cfg.get("checkpoint", "final"))
    resolved_u_values = _resolve_u_values(u_values, meta_cfg.get("u_values"))
    resolved_top_k_neurons = int(top_k_neurons) if int(top_k_neurons) > 0 else int(meta_cfg.get("top_k_neurons", 20))
    resolved_batch_size = int(batch_size) if int(batch_size) > 0 else int(meta_cfg.get("batch_size", 16))
    resolved_capture_sites = _resolve_capture_sites(meta_cfg.get("capture_sites"))

    report = run_week3_glp_meta_neuron_screen_remote.remote(
        config=config,
        sidecar_config=sidecar_config,
        traits=selected_traits,
        heldout_pairs_by_trait=heldout_pairs_by_trait,
        heldout_hashes_by_trait=heldout_hashes_by_trait,
        behavioral_source_by_trait=behavioral_source_by_trait,
        glp_weights_folder=resolved_glp_weights_folder,
        glp_checkpoint=resolved_glp_checkpoint,
        u_values=resolved_u_values,
        top_k_neurons=resolved_top_k_neurons,
        batch_size=resolved_batch_size,
        capture_sites=resolved_capture_sites,
        seed=int(seed),
        output_suffix=output_suffix,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{output_suffix.strip()}" if output_suffix.strip() else ""
    out_path = OUT_DIR / f"week3_glp_meta_neuron_screen_{ts}{suffix}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "artifact": str(out_path),
                "traits": selected_traits,
                "behavioral_source_artifacts_by_trait": {trait: str(path) for trait, path in source_paths_by_trait.items()},
                "u_values": resolved_u_values,
                "top_k_neurons": resolved_top_k_neurons,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
