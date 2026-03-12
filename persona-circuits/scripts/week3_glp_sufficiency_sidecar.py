#!/usr/bin/env python3
"""Week 3 GLP sufficiency sidecar runner.

This runner is intentionally isolated from the primary Stage 4 sufficiency lane so it
can be built and launched without modifying active experiment files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import modal
import numpy as np
import yaml

try:
    from scripts import week3_stage4_behavioral_ablation as base
    from scripts import week3_stage4_behavioral_sufficiency as suff
except ModuleNotFoundError:  # pragma: no cover - direct script invocation fallback
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import week3_stage4_behavioral_ablation as base
    from scripts import week3_stage4_behavioral_sufficiency as suff

from scripts.shared.glp_metrics import (
    aggregate_geometry_metrics,
    aggregate_numeric_metrics,
    compute_geometry_metrics,
    compute_next_token_loss_metrics,
)
from scripts.shared.glp_runtime import build_glp_alignment_report, load_glp_projector

APP_NAME = "persona-circuits-week3-glp-sufficiency-sidecar"

ROOT = base.ROOT
CONFIG_PATH = base.CONFIG_PATH
SIDECAR_CONFIG_PATH = ROOT / "configs" / "glp_sidecar.yaml"
OUT_DIR = ROOT / "results" / "glp_sidecar"
STAGE4_RESULTS_DIR = ROOT / "results" / "stage4_ablation"

DEFAULT_TARGET_FREEZE_ARTIFACT = ""
DEFAULT_PERSONA_VECTORS_ARTIFACT = ""
DEFAULT_BEHAVIORAL_SOURCE_ARTIFACT_MAP = ""
DEFAULT_TRAITS = ["sycophancy", "evil"]
DEFAULT_METHODS = ["resample", "mean"]
ALLOWED_PROMPT_SCOPES = {"response_last", "all_tokens"}

app = modal.App(APP_NAME)
vol = base.vol
image = modal.Image.debian_slim(python_version="3.11").apt_install("git").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "anthropic",
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


def _hash_string_list(values: list[str]) -> str:
    canonical = "\n".join(values)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(np.mean(np.asarray(values, dtype=np.float64)))


def _safe_delta(lhs: float | None, rhs: float | None) -> float | None:
    if lhs is None or rhs is None:
        return None
    return float(lhs - rhs)


def _parse_methods(raw: str) -> list[str]:
    methods = [x.strip().lower() for x in raw.split(",") if x.strip()]
    if not methods:
        raise ValueError("Method list cannot be empty.")
    invalid = sorted(set(methods) - suff.ALLOWED_METHODS)
    if invalid:
        raise ValueError(f"Unsupported methods: {invalid}. Allowed: {sorted(suff.ALLOWED_METHODS)}")
    return methods


def _resolve_dose_response(raw: str, fallback: Any) -> list[float]:
    if str(raw).strip():
        return suff._parse_dose_response(str(raw))
    if isinstance(fallback, list):
        deduped: list[float] = []
        seen: set[float] = set()
        for value in fallback:
            frac = float(value)
            if frac <= 0.0 or frac > 1.0:
                raise ValueError("dose_response values must be in (0, 1].")
            if frac not in seen:
                deduped.append(frac)
                seen.add(frac)
        if deduped:
            return deduped
    if isinstance(fallback, str) and fallback.strip():
        return suff._parse_dose_response(fallback)
    return [1.0]


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

    judge_models = run_metadata.get("judge_models", {}) if isinstance(run_metadata.get("judge_models"), dict) else {}
    return {
        "trait": trait,
        "source_artifact": source_artifact_path,
        "layer": int(selected["layer"]),
        "alpha": float(selected["alpha"]),
        "judge_model": str(judge_models.get("primary", base.DEFAULT_JUDGE_MODEL)),
        "max_new_tokens": int(run_metadata.get("max_new_tokens", base.DEFAULT_MAX_NEW_TOKENS)),
        "temperature": float(run_metadata.get("temperature", base.DEFAULT_TEMPERATURE)),
    }


def _extract_target_sets(payload: dict[str, Any], traits: list[str]) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    targets_payload = payload.get("targets_by_trait", {})
    if not isinstance(targets_payload, dict):
        raise ValueError("Target freeze artifact missing targets_by_trait")
    target_sets_by_trait: dict[str, list[int]] = {}
    candidate_pool_by_trait: dict[str, list[int]] = {}
    for trait in traits:
        trait_payload = targets_payload.get(trait)
        if not isinstance(trait_payload, dict):
            raise ValueError(f"Target freeze artifact missing trait={trait}")
        target_ids = [int(x) for x in trait_payload.get("target_feature_ids", [])]
        candidate_pool_ids = [int(x) for x in trait_payload.get("candidate_pool_feature_ids", [])]
        if not target_ids:
            raise ValueError(f"Missing target_feature_ids for trait={trait}")
        if not candidate_pool_ids:
            raise ValueError(f"Missing candidate_pool_feature_ids for trait={trait}")
        target_sets_by_trait[trait] = target_ids
        candidate_pool_by_trait[trait] = candidate_pool_ids
    return target_sets_by_trait, candidate_pool_by_trait


def _simple_capability_match(response: str, expected_substrings: list[str]) -> bool:
    text = response.strip().lower()
    if not expected_substrings:
        return False
    return all(str(item).strip().lower() in text for item in expected_substrings)


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
        }
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _summarize_records(
    *,
    records: list[dict[str, Any]],
    comparison_baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    trait_scores = [float(row["trait_score"]) for row in records]
    coherence_scores = [float(row["coherence_score"]) for row in records]
    effect_abs = [float(row["effect_abs_vs_unsteered"]) for row in records if row.get("effect_abs_vs_unsteered") is not None]
    preservation_raw = [
        float(row["preservation_vs_raw_full"])
        for row in records
        if row.get("preservation_vs_raw_full") is not None
    ]
    preservation_glp = [
        float(row["preservation_vs_glp_full"])
        for row in records
        if row.get("preservation_vs_glp_full") is not None
    ]
    geometry_rows: list[dict[str, float | None]] = []
    next_token_loss_rows: list[dict[str, float | None]] = []
    bleed_by_trait: dict[str, list[float]] = {}
    capability_values: list[float] = []

    for row in records:
        for detail in row.get("geometry_events", []):
            geometry_rows.append(detail)
        for detail in row.get("next_token_loss_events", []):
            next_token_loss_rows.append(detail)
        for bleed_trait, score in row.get("bleed_scores", {}).items():
            bleed_by_trait.setdefault(bleed_trait, []).append(float(score))
        if row.get("capability_correct_fraction") is not None:
            capability_values.append(float(row["capability_correct_fraction"]))

    summary = {
        "n_rows": int(len(records)),
        "trait_score_mean": _safe_mean(trait_scores),
        "coherence_mean": _safe_mean(coherence_scores),
        "effect_abs_vs_unsteered_mean": _safe_mean(effect_abs),
        "preservation_vs_raw_full_mean": _safe_mean(preservation_raw),
        "preservation_vs_glp_full_mean": _safe_mean(preservation_glp),
        "geometry_summary": aggregate_geometry_metrics(geometry_rows),
        "next_token_loss_summary": aggregate_numeric_metrics(next_token_loss_rows),
        "bleed_by_trait_mean": {
            trait: _safe_mean(scores) for trait, scores in sorted(bleed_by_trait.items())
        },
        "capability_correct_fraction_mean": _safe_mean(capability_values),
    }
    if comparison_baseline is not None:
        summary["comparison_vs_reference"] = {
            "trait_score_mean_delta": _safe_delta(
                summary.get("trait_score_mean"),
                comparison_baseline.get("trait_score_mean"),
            ),
            "coherence_mean_delta": _safe_delta(
                summary.get("coherence_mean"),
                comparison_baseline.get("coherence_mean"),
            ),
            "preservation_vs_raw_full_mean_delta": _safe_delta(
                summary.get("preservation_vs_raw_full_mean"),
                comparison_baseline.get("preservation_vs_raw_full_mean"),
            ),
            "preservation_vs_glp_full_mean_delta": _safe_delta(
                summary.get("preservation_vs_glp_full_mean"),
                comparison_baseline.get("preservation_vs_glp_full_mean"),
            ),
        }
    return summary


def _build_random_control_summary(
    *,
    observed_records: list[dict[str, Any]],
    random_records: list[dict[str, Any]],
    preservation_key: str,
    random_set_means: list[float],
    seed: int,
    n_bootstrap: int,
    comparison_baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = _summarize_records(records=random_records, comparison_baseline=comparison_baseline)
    observed_values = [
        float(row[preservation_key])
        for row in observed_records
        if row.get(preservation_key) is not None
    ]
    random_prompt_values = [
        float(row[preservation_key])
        for row in random_records
        if row.get(preservation_key) is not None
    ]
    random_set_arr = np.asarray(random_set_means, dtype=np.float64)
    summary["random_same_size_set_distribution"] = {
        "n_sets": int(random_set_arr.size),
        "set_mean_summary": base._array_summary(random_set_arr),
        "prompt_level_summary": base._array_summary(np.asarray(random_prompt_values, dtype=np.float64)),
    }
    if random_set_arr.size and observed_values:
        observed_mean = float(np.mean(np.asarray(observed_values, dtype=np.float64)))
        summary["selectivity_vs_observed"] = base._random_baseline_selectivity(observed_mean, random_set_arr)
        summary["effect_sizes_vs_observed_prompt_distribution"] = base._effect_size_summary(
            np.asarray(observed_values, dtype=np.float64),
            np.asarray(random_prompt_values, dtype=np.float64),
            seed=int(seed),
            n_bootstrap=int(n_bootstrap),
        )
    else:
        summary["selectivity_vs_observed"] = base._random_baseline_selectivity(
            0.0,
            np.asarray([], dtype=np.float64),
        )
        summary["effect_sizes_vs_observed_prompt_distribution"] = base._effect_size_summary(
            np.asarray(observed_values, dtype=np.float64),
            np.asarray(random_prompt_values, dtype=np.float64),
            seed=int(seed),
            n_bootstrap=int(n_bootstrap),
        )
    return summary


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=12 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("anthropic-key"),
    ],
    volumes={"/models": vol},
)
def run_week3_glp_sufficiency_sidecar_remote(
    *,
    config: dict[str, Any],
    sidecar_config: dict[str, Any],
    traits: list[str],
    methods: list[str],
    dose_response: list[float],
    vectors: dict[str, dict[int, list[float]]],
    target_sets_by_trait: dict[str, list[int]],
    candidate_pool_by_trait: dict[str, list[int]],
    heldout_pairs_by_trait: dict[str, list[dict[str, Any]]],
    heldout_hashes_by_trait: dict[str, str],
    behavioral_source_by_trait: dict[str, dict[str, Any]],
    glp_weights_folder: str,
    glp_checkpoint: str,
    glp_u: float,
    glp_num_timesteps: int,
    prompt_scope: str,
    glp_enabled: bool,
    seed: int,
    random_baseline_samples: int,
    n_bootstrap: int,
    min_baseline_effect_for_preservation: float,
    coherence_max_drop: float,
    max_new_tokens_override: int | None,
    temperature_override: float | None,
    next_token_loss_diagnostics_enabled: bool,
    neutral_system_prompt: str,
    capability_proxy_rows: list[dict[str, Any]],
    capability_prompt_hash: str,
    output_suffix: str,
) -> dict[str, Any]:
    import anthropic
    import torch
    from sae_lens import SAE, HookedSAETransformer

    if prompt_scope not in ALLOWED_PROMPT_SCOPES:
        raise ValueError(f"prompt_scope must be one of {sorted(ALLOWED_PROMPT_SCOPES)}")

    base._set_modal_cache_env()
    base._seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    model_name = str(config["models"]["primary"]["name"])
    sae_cfg = config["sae"]["primary"]
    sae_release = str(sae_cfg["release"])
    sae_id_format = str(sae_cfg["sae_id_format"])

    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    model.eval()

    anthropic_client = anthropic.Anthropic()
    judge_rate_limiters: dict[str, base.SlidingWindowRateLimiter] = {}

    def _rate_limiter_for(model_name_value: str) -> base.SlidingWindowRateLimiter:
        if model_name_value not in judge_rate_limiters:
            judge_rate_limiters[model_name_value] = base.SlidingWindowRateLimiter(
                requests_per_minute=int(
                    sidecar_config.get("week3_sufficiency_sidecar", {}).get(
                        "judge_rpm_limit_per_run", base.DEFAULT_JUDGE_RPM_LIMIT_PER_RUN
                    )
                ),
                min_interval_seconds=float(
                    sidecar_config.get("week3_sufficiency_sidecar", {}).get(
                        "judge_min_interval_seconds", base.DEFAULT_JUDGE_MIN_INTERVAL_SECONDS
                    )
                ),
            )
        return judge_rate_limiters[model_name_value]

    sae_cache: dict[int, tuple[Any, str]] = {}

    def _get_sae(layer_value: int) -> tuple[Any, str]:
        layer_key = int(layer_value)
        if layer_key not in sae_cache:
            sae_id = sae_id_format.format(layer=layer_key)
            sae, _, _ = SAE.from_pretrained(
                release=sae_release,
                sae_id=sae_id,
                device="cuda",
            )
            sae = sae.to(dtype=torch.float32)
            sae.eval()
            sae_cache[layer_key] = (sae, sae_id)
        return sae_cache[layer_key]

    response_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    score_cache: dict[tuple[Any, ...], Any] = {}
    clean_last_logits_cache: dict[str, Any] = {}
    results_by_trait: dict[str, Any] = {}

    thresholds_cfg = config.get("thresholds", {}) if isinstance(config.get("thresholds"), dict) else {}
    thresholds = {
        "sufficiency": float(thresholds_cfg.get("sufficiency", 0.60)),
        "significance": float(thresholds_cfg.get("significance", 0.01)),
        "a12_minimum": float(thresholds_cfg.get("a12_minimum", 0.71)),
    }

    for trait_idx, trait in enumerate(traits):
        if trait not in vectors:
            raise ValueError(f"Missing vectors for trait={trait}")
        if trait not in target_sets_by_trait:
            raise ValueError(f"Missing target set for trait={trait}")
        if trait not in candidate_pool_by_trait:
            raise ValueError(f"Missing candidate pool for trait={trait}")
        if trait not in heldout_pairs_by_trait:
            raise ValueError(f"Missing heldout pairs for trait={trait}")
        if trait not in behavioral_source_by_trait:
            raise ValueError(f"Missing behavioral source settings for trait={trait}")

        source = behavioral_source_by_trait[trait]
        layer = int(source["layer"])
        alpha = float(source["alpha"])
        judge_model = str(
            source.get(
                "judge_model",
                sidecar_config.get("week3_sufficiency_sidecar", {}).get("judge_model", base.DEFAULT_JUDGE_MODEL),
            )
        )
        max_new_tokens = (
            int(max_new_tokens_override)
            if max_new_tokens_override is not None
            else int(source.get("max_new_tokens", base.DEFAULT_MAX_NEW_TOKENS))
        )
        temperature = (
            float(temperature_override)
            if temperature_override is not None
            else float(source.get("temperature", base.DEFAULT_TEMPERATURE))
        )

        layer_vectors = vectors.get(trait, {})
        if layer not in layer_vectors:
            raise ValueError(f"Trait={trait} vector missing layer={layer}")
        direction = torch.tensor(layer_vectors[layer], dtype=torch.float32, device="cuda")
        direction_norm = float(torch.norm(direction).item())
        if direction_norm <= 1e-12:
            raise ValueError(f"Trait={trait} layer={layer} vector has near-zero norm")
        direction = direction / direction_norm
        direction_runtime = direction[None, None, :]

        sae, sae_id = _get_sae(layer)
        hook_name = base._hook_name_for_layer(layer)
        d_sae = int(sae.W_dec.shape[0])

        target_ids = [int(x) for x in target_sets_by_trait[trait]]
        candidate_pool_ids = [int(x) for x in candidate_pool_by_trait[trait]]
        if any(x < 0 or x >= d_sae for x in target_ids + candidate_pool_ids):
            raise ValueError(f"Feature IDs out of range for trait={trait}; d_sae={d_sae}")
        if not set(target_ids).issubset(set(candidate_pool_ids)):
            raise ValueError(f"Target set must be subset of candidate pool for trait={trait}")

        projector = load_glp_projector(
            weights_folder=glp_weights_folder,
            checkpoint=glp_checkpoint,
            device="cuda",
            u=float(glp_u),
            num_timesteps=int(glp_num_timesteps),
            default_layer_idx=int(layer),
            enabled=bool(glp_enabled),
            metadata_override=sidecar_config.get("glp", {}).get("metadata") if isinstance(sidecar_config.get("glp"), dict) else None,
        )
        glp_alignment = build_glp_alignment_report(
            metadata=projector.metadata,
            target_model_name=model_name,
            target_layer=layer,
        )

        rows = heldout_pairs_by_trait[trait]
        prompts: list[str] = []
        user_queries: list[str] = []
        ground_truths: list[str] = []
        feature_rows: list[Any] = []
        other_traits = [other for other in traits if other != trait]

        for row in rows:
            prompt_text = base._format_chat_prompt(
                model.tokenizer,
                str(row["system_low"]),
                str(row["user_query"]),
            )
            prompts.append(prompt_text)
            user_queries.append(str(row["user_query"]))
            ground_truths.append(str(row.get("ground_truth", "N/A")))

            with torch.no_grad():
                tokens = model.to_tokens(prompt_text, prepend_bos=True)
                _, cache = model.run_with_cache(
                    tokens,
                    names_filter=lambda name, target=hook_name: name == target,
                )
                resid_last = cache[hook_name][0, -1, :].to(torch.float32)
                feat_last = sae.encode(resid_last.unsqueeze(0)).to(torch.float32)[0]
            feature_rows.append(feat_last.detach().cpu())

        feature_matrix = torch.stack(feature_rows, dim=0)
        feature_mean = torch.mean(feature_matrix, dim=0)
        n_rows = int(feature_matrix.shape[0])

        rng = np.random.default_rng(int(seed) + trait_idx * 1000 + len(trait))
        donors: list[int] = []
        for i in range(n_rows):
            if n_rows == 1:
                donors.append(0)
                continue
            j = int(rng.integers(low=0, high=n_rows))
            while j == i:
                j = int(rng.integers(low=0, high=n_rows))
            donors.append(j)

        def _scope_clone(tensor: Any) -> Any:
            if prompt_scope == "response_last":
                return tensor[:, -1:, :].clone()
            return tensor.clone()

        def _score_response(*, score_trait: str, user_query: str, response_text: str, ground_truth: str) -> float:
            score = base.judge_score(
                anthropic_client=anthropic_client,
                anthropic_module=anthropic,
                judge_model=judge_model,
                score_trait=score_trait,
                user_query=user_query,
                response=response_text,
                ground_truth=ground_truth,
                max_attempts=int(
                    sidecar_config.get("week3_sufficiency_sidecar", {}).get(
                        "judge_max_attempts", base.DEFAULT_JUDGE_MAX_ATTEMPTS
                    )
                ),
                rate_limiter=_rate_limiter_for(judge_model),
                retry_base_seconds=float(
                    sidecar_config.get("week3_sufficiency_sidecar", {}).get(
                        "judge_retry_base_seconds", base.DEFAULT_JUDGE_RETRY_BASE_SECONDS
                    )
                ),
                retry_max_seconds=float(
                    sidecar_config.get("week3_sufficiency_sidecar", {}).get(
                        "judge_retry_max_seconds", base.DEFAULT_JUDGE_RETRY_MAX_SECONDS
                    )
                ),
                retry_jitter_fraction=float(
                    sidecar_config.get("week3_sufficiency_sidecar", {}).get(
                        "judge_retry_jitter_fraction", base.DEFAULT_JUDGE_RETRY_JITTER_FRACTION
                    )
                ),
                score_cache=score_cache,
            )
            return float(score.score)

        def _generate_condition(
            *,
            prompt_text: str,
            cache_key: tuple[Any, ...],
            direction_alpha: float,
            circuit_hook: Callable[[Any, Any], Any] | None,
            use_glp_runtime: bool,
            geometry_reference: str,
        ) -> dict[str, Any]:
            if cache_key in response_cache:
                return response_cache[cache_key]

            tokens = model.to_tokens(prompt_text, prepend_bos=True)
            geometry_events: list[dict[str, float | None]] = []
            next_token_loss_events: list[dict[str, float | None]] = []
            fwd_hooks: list[tuple[str, Any]] = []
            needs_hook = circuit_hook is not None or use_glp_runtime or abs(float(direction_alpha)) > 1e-12

            if needs_hook:
                record_geometry = {"enabled": True}

                def intervention_hook(resid_post: Any, hook: Any) -> Any:
                    del hook
                    resid_dtype = resid_post.dtype
                    raw_fp32 = resid_post.to(torch.float32)
                    steered_full = raw_fp32.clone()
                    if abs(float(direction_alpha)) > 1e-12:
                        steered_full = steered_full + float(direction_alpha) * direction_runtime
                    transformed_full = steered_full
                    if circuit_hook is not None:
                        transformed_full = circuit_hook(steered_full, None).to(torch.float32)
                    output_full = transformed_full
                    if use_glp_runtime:
                        if geometry_reference == "raw":
                            original_scope = _scope_clone(raw_fp32)
                            edited_scope = _scope_clone(transformed_full)
                        elif geometry_reference == "steered":
                            original_scope = _scope_clone(steered_full)
                            edited_scope = _scope_clone(transformed_full)
                        else:
                            raise ValueError(f"Unknown geometry_reference={geometry_reference}")
                        projected_scope = projector.postprocess(edited_scope, layer_idx=int(layer))
                        if record_geometry["enabled"]:
                            metrics = compute_geometry_metrics(
                                original=original_scope,
                                edited=edited_scope,
                                projected=projected_scope,
                            )
                            metrics["reference_mode"] = geometry_reference
                            geometry_events.append(metrics)
                        if prompt_scope == "response_last":
                            output_full = transformed_full.clone()
                            output_full[:, -1:, :] = projected_scope.to(torch.float32)
                        else:
                            output_full = projected_scope.to(torch.float32)
                    return output_full.to(dtype=resid_dtype)

                fwd_hooks.append((hook_name, intervention_hook))

                if bool(next_token_loss_diagnostics_enabled):
                    clean_logits_key = prompt_text
                    if clean_logits_key not in clean_last_logits_cache:
                        with torch.no_grad():
                            clean_logits = model(tokens, return_type="logits")
                        clean_last_logits_cache[clean_logits_key] = clean_logits[:, -1, :].detach().to(torch.float32).cpu()
                    clean_last_logits = clean_last_logits_cache[clean_logits_key]
                    with torch.no_grad():
                        with model.hooks(fwd_hooks=fwd_hooks):
                            hooked_logits = model(tokens, return_type="logits")
                    next_token_loss_events.append(
                        compute_next_token_loss_metrics(
                            clean_logits=clean_last_logits[0],
                            hooked_logits=hooked_logits[0, -1, :].detach().to(torch.float32).cpu(),
                        )
                    )
                    # Prevent geometry events from accumulating over all generated tokens.
                    record_geometry["enabled"] = False

            generate_kwargs = {
                "max_new_tokens": int(max_new_tokens),
                "temperature": float(temperature),
                "top_k": None,
                "stop_at_eos": True,
                "verbose": False,
            }
            if fwd_hooks:
                with model.hooks(fwd_hooks=fwd_hooks):
                    generated = model.generate(tokens, **generate_kwargs)
            else:
                generated = model.generate(tokens, **generate_kwargs)
            completion = generated[0, tokens.shape[1] :]
            result = {
                "response": model.to_string(completion),
                "geometry_events": geometry_events,
                "geometry_summary": aggregate_geometry_metrics(geometry_events),
                "next_token_loss_events": next_token_loss_events,
                "next_token_loss_summary": aggregate_numeric_metrics(next_token_loss_events),
            }
            response_cache[cache_key] = result
            return result

        family_records: dict[str, list[dict[str, Any]]] = {
            "baseline_raw": [],
            "full_vector_raw": [],
            "full_vector_glp": [],
            "baseline_glp_control": [],
        }
        unsteered_trait_scores: list[float] = []
        full_vector_raw_effect_abs: list[float] = []
        full_vector_glp_effect_abs: list[float] = []

        for i in range(n_rows):
            base_result = _generate_condition(
                prompt_text=prompts[i],
                cache_key=("baseline_raw", trait, i, max_new_tokens, temperature),
                direction_alpha=0.0,
                circuit_hook=None,
                use_glp_runtime=False,
                geometry_reference="raw",
            )
            full_raw_result = _generate_condition(
                prompt_text=prompts[i],
                cache_key=("full_vector_raw", trait, i, layer, alpha, max_new_tokens, temperature),
                direction_alpha=float(alpha),
                circuit_hook=None,
                use_glp_runtime=False,
                geometry_reference="raw",
            )
            full_glp_result = _generate_condition(
                prompt_text=prompts[i],
                cache_key=("full_vector_glp", trait, i, layer, alpha, glp_checkpoint, glp_u, glp_num_timesteps, prompt_scope, max_new_tokens, temperature),
                direction_alpha=float(alpha),
                circuit_hook=None,
                use_glp_runtime=True,
                geometry_reference="raw",
            )
            baseline_glp_result = _generate_condition(
                prompt_text=prompts[i],
                cache_key=("baseline_glp_control", trait, i, glp_checkpoint, glp_u, glp_num_timesteps, prompt_scope, max_new_tokens, temperature),
                direction_alpha=0.0,
                circuit_hook=None,
                use_glp_runtime=True,
                geometry_reference="raw",
            )

            base_trait = _score_response(
                score_trait=trait,
                user_query=user_queries[i],
                response_text=base_result["response"],
                ground_truth=ground_truths[i],
            )
            base_coherence = _score_response(
                score_trait="coherence",
                user_query=user_queries[i],
                response_text=base_result["response"],
                ground_truth=ground_truths[i],
            )
            full_raw_trait = _score_response(
                score_trait=trait,
                user_query=user_queries[i],
                response_text=full_raw_result["response"],
                ground_truth=ground_truths[i],
            )
            full_raw_coherence = _score_response(
                score_trait="coherence",
                user_query=user_queries[i],
                response_text=full_raw_result["response"],
                ground_truth=ground_truths[i],
            )
            full_glp_trait = _score_response(
                score_trait=trait,
                user_query=user_queries[i],
                response_text=full_glp_result["response"],
                ground_truth=ground_truths[i],
            )
            full_glp_coherence = _score_response(
                score_trait="coherence",
                user_query=user_queries[i],
                response_text=full_glp_result["response"],
                ground_truth=ground_truths[i],
            )
            baseline_glp_trait = _score_response(
                score_trait=trait,
                user_query=user_queries[i],
                response_text=baseline_glp_result["response"],
                ground_truth=ground_truths[i],
            )
            baseline_glp_coherence = _score_response(
                score_trait="coherence",
                user_query=user_queries[i],
                response_text=baseline_glp_result["response"],
                ground_truth=ground_truths[i],
            )

            raw_effect_abs = abs(float(full_raw_trait) - float(base_trait))
            glp_effect_abs = abs(float(full_glp_trait) - float(base_trait))
            baseline_glp_effect_abs = abs(float(baseline_glp_trait) - float(base_trait))
            unsteered_trait_scores.append(float(base_trait))
            full_vector_raw_effect_abs.append(float(raw_effect_abs))
            full_vector_glp_effect_abs.append(float(glp_effect_abs))

            def _bleed_scores(response_text: str) -> dict[str, float]:
                return {
                    bleed_trait: _score_response(
                        score_trait=bleed_trait,
                        user_query=user_queries[i],
                        response_text=response_text,
                        ground_truth=ground_truths[i],
                    )
                    for bleed_trait in other_traits
                }

            family_records["baseline_raw"].append(
                {
                    "row_id": i,
                    "trait_score": float(base_trait),
                    "coherence_score": float(base_coherence),
                    "effect_abs_vs_unsteered": 0.0,
                    "preservation_vs_raw_full": 0.0,
                    "preservation_vs_glp_full": 0.0,
                    "geometry_events": [],
                    "next_token_loss_events": [],
                    "bleed_scores": _bleed_scores(base_result["response"]),
                }
            )
            family_records["full_vector_raw"].append(
                {
                    "row_id": i,
                    "trait_score": float(full_raw_trait),
                    "coherence_score": float(full_raw_coherence),
                    "effect_abs_vs_unsteered": float(raw_effect_abs),
                    "preservation_vs_raw_full": suff._preserved_effect_fraction(
                        raw_effect_abs,
                        raw_effect_abs,
                        min_baseline_effect_for_preservation=float(min_baseline_effect_for_preservation),
                    ),
                    "preservation_vs_glp_full": suff._preserved_effect_fraction(
                        glp_effect_abs,
                        raw_effect_abs,
                        min_baseline_effect_for_preservation=float(min_baseline_effect_for_preservation),
                    ),
                    "geometry_events": full_raw_result["geometry_events"],
                    "next_token_loss_events": full_raw_result["next_token_loss_events"],
                    "bleed_scores": _bleed_scores(full_raw_result["response"]),
                }
            )
            family_records["full_vector_glp"].append(
                {
                    "row_id": i,
                    "trait_score": float(full_glp_trait),
                    "coherence_score": float(full_glp_coherence),
                    "effect_abs_vs_unsteered": float(glp_effect_abs),
                    "preservation_vs_raw_full": suff._preserved_effect_fraction(
                        raw_effect_abs,
                        glp_effect_abs,
                        min_baseline_effect_for_preservation=float(min_baseline_effect_for_preservation),
                    ),
                    "preservation_vs_glp_full": suff._preserved_effect_fraction(
                        glp_effect_abs,
                        glp_effect_abs,
                        min_baseline_effect_for_preservation=float(min_baseline_effect_for_preservation),
                    ),
                    "geometry_events": full_glp_result["geometry_events"],
                    "next_token_loss_events": full_glp_result["next_token_loss_events"],
                    "bleed_scores": _bleed_scores(full_glp_result["response"]),
                }
            )
            family_records["baseline_glp_control"].append(
                {
                    "row_id": i,
                    "trait_score": float(baseline_glp_trait),
                    "coherence_score": float(baseline_glp_coherence),
                    "effect_abs_vs_unsteered": float(baseline_glp_effect_abs),
                    "preservation_vs_raw_full": suff._preserved_effect_fraction(
                        raw_effect_abs,
                        baseline_glp_effect_abs,
                        min_baseline_effect_for_preservation=float(min_baseline_effect_for_preservation),
                    ),
                    "preservation_vs_glp_full": suff._preserved_effect_fraction(
                        glp_effect_abs,
                        baseline_glp_effect_abs,
                        min_baseline_effect_for_preservation=float(min_baseline_effect_for_preservation),
                    ),
                    "geometry_events": baseline_glp_result["geometry_events"],
                    "next_token_loss_events": baseline_glp_result["next_token_loss_events"],
                    "bleed_scores": _bleed_scores(baseline_glp_result["response"]),
                }
            )

        baseline_summary = _summarize_records(records=family_records["baseline_raw"], comparison_baseline=None)
        full_vector_raw_summary = _summarize_records(
            records=family_records["full_vector_raw"],
            comparison_baseline=baseline_summary,
        )
        full_vector_glp_summary = _summarize_records(
            records=family_records["full_vector_glp"],
            comparison_baseline=full_vector_raw_summary,
        )
        baseline_glp_summary = _summarize_records(
            records=family_records["baseline_glp_control"],
            comparison_baseline=baseline_summary,
        )

        deterministic_generators: dict[str, Callable[[str, str], dict[str, Any]]] = {
            "baseline_raw": lambda prompt_text, prompt_key: _generate_condition(
                prompt_text=prompt_text,
                cache_key=("baseline_raw_capability", trait, prompt_key, max_new_tokens, temperature),
                direction_alpha=0.0,
                circuit_hook=None,
                use_glp_runtime=False,
                geometry_reference="raw",
            ),
            "full_vector_raw": lambda prompt_text, prompt_key: _generate_condition(
                prompt_text=prompt_text,
                cache_key=("full_vector_raw_capability", trait, prompt_key, layer, alpha, max_new_tokens, temperature),
                direction_alpha=float(alpha),
                circuit_hook=None,
                use_glp_runtime=False,
                geometry_reference="raw",
            ),
            "full_vector_glp": lambda prompt_text, prompt_key: _generate_condition(
                prompt_text=prompt_text,
                cache_key=("full_vector_glp_capability", trait, prompt_key, layer, alpha, glp_checkpoint, glp_u, glp_num_timesteps, prompt_scope, max_new_tokens, temperature),
                direction_alpha=float(alpha),
                circuit_hook=None,
                use_glp_runtime=True,
                geometry_reference="raw",
            ),
            "baseline_glp_control": lambda prompt_text, prompt_key: _generate_condition(
                prompt_text=prompt_text,
                cache_key=("baseline_glp_control_capability", trait, prompt_key, glp_checkpoint, glp_u, glp_num_timesteps, prompt_scope, max_new_tokens, temperature),
                direction_alpha=0.0,
                circuit_hook=None,
                use_glp_runtime=True,
                geometry_reference="raw",
            ),
        }

        for family_name, generator in deterministic_generators.items():
            capability_values: list[float] = []
            for row in capability_proxy_rows:
                prompt = str(row["prompt"])
                expected_substrings = [str(x) for x in row.get("expected_substrings", [])]
                capability_prompt = base._format_chat_prompt(model.tokenizer, neutral_system_prompt, prompt)
                response = generator(capability_prompt, prompt)
                capability_values.append(
                    1.0 if _simple_capability_match(response["response"], expected_substrings) else 0.0
                )
            for record in family_records[family_name]:
                record["capability_correct_fraction"] = _safe_mean(capability_values)

        deterministic_summaries = {
            "baseline_raw": _summarize_records(records=family_records["baseline_raw"], comparison_baseline=None),
            "full_vector_raw": _summarize_records(records=family_records["full_vector_raw"], comparison_baseline=baseline_summary),
            "full_vector_glp": _summarize_records(records=family_records["full_vector_glp"], comparison_baseline=full_vector_raw_summary),
            "baseline_glp_control": _summarize_records(records=family_records["baseline_glp_control"], comparison_baseline=baseline_summary),
        }

        methods_report: dict[str, Any] = {}
        for method_idx, method in enumerate(methods):
            dose_reports: dict[str, Any] = {}
            for dose_idx, fraction in enumerate(dose_response):
                dose_key = suff._dose_key(fraction)
                preserve_n = max(1, int(math.ceil(len(target_ids) * float(fraction))))
                preserved_ids = target_ids[:preserve_n]
                preserved_id_set = set(preserved_ids)
                ablated_ids = np.asarray(
                    [fid for fid in candidate_pool_ids if fid not in preserved_id_set],
                    dtype=np.int64,
                )
                if ablated_ids.size == 0:
                    raise ValueError(
                        f"Trait={trait} method={method} fraction={fraction} yields empty ablated set"
                    )

                observed_records = {
                    "circuit_only_raw": [],
                    "circuit_only_glp": [],
                }

                for i in range(n_rows):
                    circuit_hook = base._make_sae_ablation_hook(
                        sae=sae,
                        method=method,
                        feature_ids=ablated_ids,
                        donor_feature_values=feature_matrix[donors[i]],
                        mean_feature_values=feature_mean,
                    )
                    circuit_raw_result = _generate_condition(
                        prompt_text=prompts[i],
                        cache_key=(
                            "circuit_only_raw",
                            trait,
                            method,
                            dose_key,
                            i,
                            donors[i],
                            layer,
                            alpha,
                            max_new_tokens,
                            temperature,
                        ),
                        direction_alpha=float(alpha),
                        circuit_hook=circuit_hook,
                        use_glp_runtime=False,
                        geometry_reference="steered",
                    )
                    circuit_glp_result = _generate_condition(
                        prompt_text=prompts[i],
                        cache_key=(
                            "circuit_only_glp",
                            trait,
                            method,
                            dose_key,
                            i,
                            donors[i],
                            layer,
                            alpha,
                            glp_checkpoint,
                            glp_u,
                            glp_num_timesteps,
                            prompt_scope,
                            max_new_tokens,
                            temperature,
                        ),
                        direction_alpha=float(alpha),
                        circuit_hook=circuit_hook,
                        use_glp_runtime=True,
                        geometry_reference="steered",
                    )

                    circuit_raw_trait = _score_response(
                        score_trait=trait,
                        user_query=user_queries[i],
                        response_text=circuit_raw_result["response"],
                        ground_truth=ground_truths[i],
                    )
                    circuit_raw_coherence = _score_response(
                        score_trait="coherence",
                        user_query=user_queries[i],
                        response_text=circuit_raw_result["response"],
                        ground_truth=ground_truths[i],
                    )
                    circuit_glp_trait = _score_response(
                        score_trait=trait,
                        user_query=user_queries[i],
                        response_text=circuit_glp_result["response"],
                        ground_truth=ground_truths[i],
                    )
                    circuit_glp_coherence = _score_response(
                        score_trait="coherence",
                        user_query=user_queries[i],
                        response_text=circuit_glp_result["response"],
                        ground_truth=ground_truths[i],
                    )
                    circuit_raw_effect_abs = abs(float(circuit_raw_trait) - float(unsteered_trait_scores[i]))
                    circuit_glp_effect_abs = abs(float(circuit_glp_trait) - float(unsteered_trait_scores[i]))

                    observed_records["circuit_only_raw"].append(
                        {
                            "row_id": i,
                            "trait_score": float(circuit_raw_trait),
                            "coherence_score": float(circuit_raw_coherence),
                            "effect_abs_vs_unsteered": float(circuit_raw_effect_abs),
                            "preservation_vs_raw_full": suff._preserved_effect_fraction(
                                full_vector_raw_effect_abs[i],
                                circuit_raw_effect_abs,
                                min_baseline_effect_for_preservation=float(
                                    min_baseline_effect_for_preservation
                                ),
                            ),
                            "preservation_vs_glp_full": suff._preserved_effect_fraction(
                                full_vector_glp_effect_abs[i],
                                circuit_raw_effect_abs,
                                min_baseline_effect_for_preservation=float(
                                    min_baseline_effect_for_preservation
                                ),
                            ),
                            "geometry_events": circuit_raw_result["geometry_events"],
                            "next_token_loss_events": circuit_raw_result["next_token_loss_events"],
                            "bleed_scores": {
                                bleed_trait: _score_response(
                                    score_trait=bleed_trait,
                                    user_query=user_queries[i],
                                    response_text=circuit_raw_result["response"],
                                    ground_truth=ground_truths[i],
                                )
                                for bleed_trait in other_traits
                            },
                        }
                    )
                    observed_records["circuit_only_glp"].append(
                        {
                            "row_id": i,
                            "trait_score": float(circuit_glp_trait),
                            "coherence_score": float(circuit_glp_coherence),
                            "effect_abs_vs_unsteered": float(circuit_glp_effect_abs),
                            "preservation_vs_raw_full": suff._preserved_effect_fraction(
                                full_vector_raw_effect_abs[i],
                                circuit_glp_effect_abs,
                                min_baseline_effect_for_preservation=float(
                                    min_baseline_effect_for_preservation
                                ),
                            ),
                            "preservation_vs_glp_full": suff._preserved_effect_fraction(
                                full_vector_glp_effect_abs[i],
                                circuit_glp_effect_abs,
                                min_baseline_effect_for_preservation=float(
                                    min_baseline_effect_for_preservation
                                ),
                            ),
                            "geometry_events": circuit_glp_result["geometry_events"],
                            "next_token_loss_events": circuit_glp_result["next_token_loss_events"],
                            "bleed_scores": {
                                bleed_trait: _score_response(
                                    score_trait=bleed_trait,
                                    user_query=user_queries[i],
                                    response_text=circuit_glp_result["response"],
                                    ground_truth=ground_truths[i],
                                )
                                for bleed_trait in other_traits
                            },
                        }
                    )

                for family_name in ("circuit_only_raw", "circuit_only_glp"):
                    capability_values: list[float] = []
                    for row in capability_proxy_rows:
                        prompt = str(row["prompt"])
                        expected_substrings = [str(x) for x in row.get("expected_substrings", [])]
                        capability_prompt = base._format_chat_prompt(
                            model.tokenizer,
                            neutral_system_prompt,
                            prompt,
                        )
                        capability_hook = base._make_sae_ablation_hook(
                            sae=sae,
                            method=method,
                            feature_ids=ablated_ids,
                            donor_feature_values=feature_matrix[donors[0]],
                            mean_feature_values=feature_mean,
                        )
                        response = _generate_condition(
                            prompt_text=capability_prompt,
                            cache_key=(
                                family_name,
                                trait,
                                method,
                                dose_key,
                                "capability",
                                prompt,
                                layer,
                                alpha,
                                glp_checkpoint,
                                glp_u,
                                glp_num_timesteps,
                                prompt_scope,
                                max_new_tokens,
                                temperature,
                            ),
                            direction_alpha=float(alpha),
                            circuit_hook=capability_hook,
                            use_glp_runtime=(family_name == "circuit_only_glp"),
                            geometry_reference="steered",
                        )
                        capability_values.append(
                            1.0
                            if _simple_capability_match(response["response"], expected_substrings)
                            else 0.0
                        )
                    for record in observed_records[family_name]:
                        record["capability_correct_fraction"] = _safe_mean(capability_values)

                observed_summary_raw = _summarize_records(
                    records=observed_records["circuit_only_raw"],
                    comparison_baseline=deterministic_summaries["full_vector_raw"],
                )
                observed_summary_glp = _summarize_records(
                    records=observed_records["circuit_only_glp"],
                    comparison_baseline=deterministic_summaries["full_vector_glp"],
                )

                random_sets = suff._sample_random_preserved_sets(
                    candidate_pool_ids=candidate_pool_ids,
                    preserved_set_size=int(preserve_n),
                    n_sets=int(random_baseline_samples),
                    seed=int(seed) + trait_idx * 1000 + method_idx * 101 + dose_idx * 17 + len(trait),
                )
                random_records_raw: list[dict[str, Any]] = []
                random_records_glp: list[dict[str, Any]] = []
                random_set_means_raw: list[float] = []
                random_set_means_glp: list[float] = []

                for set_idx, random_preserved_ids in enumerate(random_sets):
                    random_preserved_set = set(int(x) for x in random_preserved_ids.tolist())
                    random_ablated_ids = np.asarray(
                        [fid for fid in candidate_pool_ids if fid not in random_preserved_set],
                        dtype=np.int64,
                    )
                    set_preservations_raw: list[float] = []
                    set_preservations_glp: list[float] = []
                    for i in range(n_rows):
                        random_hook = base._make_sae_ablation_hook(
                            sae=sae,
                            method=method,
                            feature_ids=random_ablated_ids,
                            donor_feature_values=feature_matrix[donors[i]],
                            mean_feature_values=feature_mean,
                        )
                        random_raw_result = _generate_condition(
                            prompt_text=prompts[i],
                            cache_key=(
                                "random_same_size_circuit_raw",
                                trait,
                                method,
                                dose_key,
                                set_idx,
                                i,
                                donors[i],
                                layer,
                                alpha,
                                max_new_tokens,
                                temperature,
                            ),
                            direction_alpha=float(alpha),
                            circuit_hook=random_hook,
                            use_glp_runtime=False,
                            geometry_reference="steered",
                        )
                        random_glp_result = _generate_condition(
                            prompt_text=prompts[i],
                            cache_key=(
                                "random_same_size_circuit_glp",
                                trait,
                                method,
                                dose_key,
                                set_idx,
                                i,
                                donors[i],
                                layer,
                                alpha,
                                glp_checkpoint,
                                glp_u,
                                glp_num_timesteps,
                                prompt_scope,
                                max_new_tokens,
                                temperature,
                            ),
                            direction_alpha=float(alpha),
                            circuit_hook=random_hook,
                            use_glp_runtime=True,
                            geometry_reference="steered",
                        )
                        random_raw_trait = _score_response(
                            score_trait=trait,
                            user_query=user_queries[i],
                            response_text=random_raw_result["response"],
                            ground_truth=ground_truths[i],
                        )
                        random_glp_trait = _score_response(
                            score_trait=trait,
                            user_query=user_queries[i],
                            response_text=random_glp_result["response"],
                            ground_truth=ground_truths[i],
                        )
                        random_raw_coherence = _score_response(
                            score_trait="coherence",
                            user_query=user_queries[i],
                            response_text=random_raw_result["response"],
                            ground_truth=ground_truths[i],
                        )
                        random_glp_coherence = _score_response(
                            score_trait="coherence",
                            user_query=user_queries[i],
                            response_text=random_glp_result["response"],
                            ground_truth=ground_truths[i],
                        )
                        random_raw_effect_abs = abs(float(random_raw_trait) - float(unsteered_trait_scores[i]))
                        random_glp_effect_abs = abs(float(random_glp_trait) - float(unsteered_trait_scores[i]))
                        preservation_raw = suff._preserved_effect_fraction(
                            full_vector_raw_effect_abs[i],
                            random_raw_effect_abs,
                            min_baseline_effect_for_preservation=float(
                                min_baseline_effect_for_preservation
                            ),
                        )
                        preservation_glp = suff._preserved_effect_fraction(
                            full_vector_glp_effect_abs[i],
                            random_glp_effect_abs,
                            min_baseline_effect_for_preservation=float(
                                min_baseline_effect_for_preservation
                            ),
                        )
                        if preservation_raw is not None:
                            set_preservations_raw.append(float(preservation_raw))
                        if preservation_glp is not None:
                            set_preservations_glp.append(float(preservation_glp))
                        random_records_raw.append(
                            {
                                "row_id": i,
                                "random_set_idx": int(set_idx),
                                "trait_score": float(random_raw_trait),
                                "coherence_score": float(random_raw_coherence),
                                "effect_abs_vs_unsteered": float(random_raw_effect_abs),
                                "preservation_vs_raw_full": preservation_raw,
                                "preservation_vs_glp_full": suff._preserved_effect_fraction(
                                    full_vector_glp_effect_abs[i],
                                    random_raw_effect_abs,
                                    min_baseline_effect_for_preservation=float(
                                        min_baseline_effect_for_preservation
                                    ),
                                ),
                                "geometry_events": random_raw_result["geometry_events"],
                                "next_token_loss_events": random_raw_result["next_token_loss_events"],
                                "bleed_scores": {},
                            }
                        )
                        random_records_glp.append(
                            {
                                "row_id": i,
                                "random_set_idx": int(set_idx),
                                "trait_score": float(random_glp_trait),
                                "coherence_score": float(random_glp_coherence),
                                "effect_abs_vs_unsteered": float(random_glp_effect_abs),
                                "preservation_vs_raw_full": suff._preserved_effect_fraction(
                                    full_vector_raw_effect_abs[i],
                                    random_glp_effect_abs,
                                    min_baseline_effect_for_preservation=float(
                                        min_baseline_effect_for_preservation
                                    ),
                                ),
                                "preservation_vs_glp_full": preservation_glp,
                                "geometry_events": random_glp_result["geometry_events"],
                                "next_token_loss_events": random_glp_result["next_token_loss_events"],
                                "bleed_scores": {},
                            }
                        )
                    if set_preservations_raw:
                        random_set_means_raw.append(
                            float(np.mean(np.asarray(set_preservations_raw, dtype=np.float64)))
                        )
                    if set_preservations_glp:
                        random_set_means_glp.append(
                            float(np.mean(np.asarray(set_preservations_glp, dtype=np.float64)))
                        )

                random_summary_raw = _build_random_control_summary(
                    observed_records=observed_records["circuit_only_raw"],
                    random_records=random_records_raw,
                    preservation_key="preservation_vs_raw_full",
                    random_set_means=random_set_means_raw,
                    seed=int(seed) + trait_idx * 1000 + method_idx * 17 + dose_idx * 13,
                    n_bootstrap=int(n_bootstrap),
                    comparison_baseline=deterministic_summaries["full_vector_raw"],
                )
                random_summary_glp = _build_random_control_summary(
                    observed_records=observed_records["circuit_only_glp"],
                    random_records=random_records_glp,
                    preservation_key="preservation_vs_glp_full",
                    random_set_means=random_set_means_glp,
                    seed=int(seed) + trait_idx * 1000 + method_idx * 31 + dose_idx * 19,
                    n_bootstrap=int(n_bootstrap),
                    comparison_baseline=deterministic_summaries["full_vector_glp"],
                )

                quality_controls = {
                    "circuit_only_raw": {
                        "steered_minus_circuit_only_mean": _safe_delta(
                            deterministic_summaries["full_vector_raw"].get("coherence_mean"),
                            observed_summary_raw.get("coherence_mean"),
                        ),
                        "max_allowed_drop": float(coherence_max_drop),
                    },
                    "circuit_only_glp": {
                        "steered_minus_circuit_only_mean": _safe_delta(
                            deterministic_summaries["full_vector_glp"].get("coherence_mean"),
                            observed_summary_glp.get("coherence_mean"),
                        ),
                        "max_allowed_drop": float(coherence_max_drop),
                    },
                }
                quality_controls["circuit_only_raw"]["relative_max_drop_pass"] = bool(
                    quality_controls["circuit_only_raw"]["steered_minus_circuit_only_mean"] is not None
                    and float(
                        quality_controls["circuit_only_raw"]["steered_minus_circuit_only_mean"]
                    )
                    <= float(coherence_max_drop)
                )
                quality_controls["circuit_only_glp"]["relative_max_drop_pass"] = bool(
                    quality_controls["circuit_only_glp"]["steered_minus_circuit_only_mean"] is not None
                    and float(
                        quality_controls["circuit_only_glp"]["steered_minus_circuit_only_mean"]
                    )
                    <= float(coherence_max_drop)
                )

                dose_reports[dose_key] = {
                    "preserved_fraction_target": float(fraction),
                    "preserved_feature_ids": [int(x) for x in preserved_ids],
                    "ablated_feature_ids": [int(x) for x in ablated_ids.tolist()],
                    "preserved_feature_count": int(len(preserved_ids)),
                    "conditions": {
                        "circuit_only_raw": observed_summary_raw,
                        "circuit_only_glp": observed_summary_glp,
                        "random_same_size_circuit_raw": random_summary_raw,
                        "random_same_size_circuit_glp": random_summary_glp,
                    },
                    "condition_records": {
                        "circuit_only_raw": observed_records["circuit_only_raw"],
                        "circuit_only_glp": observed_records["circuit_only_glp"],
                        "random_same_size_circuit_raw": random_records_raw,
                        "random_same_size_circuit_glp": random_records_glp,
                    },
                    "quality_controls": quality_controls,
                }

            methods_report[method] = {
                "analysis_target": "behavioral_sufficiency_glp_sidecar",
                "dose_fraction_reports": dose_reports,
            }

        results_by_trait[trait] = {
            "claim_trait_name": base._trait_label(trait),
            "n_prompts": int(n_rows),
            "heldout_hash": heldout_hashes_by_trait[trait],
            "target_feature_ids": [int(x) for x in target_ids],
            "candidate_pool_feature_ids": [int(x) for x in candidate_pool_ids],
            "steering_source": {
                "source_artifact": source["source_artifact"],
                "layer": int(layer),
                "alpha": float(alpha),
                "judge_model": judge_model,
                "sae_release": sae_release,
                "sae_id": sae_id,
            },
            "glp_alignment": glp_alignment,
            "prompt_scope": prompt_scope,
            "thresholds": thresholds,
            "deterministic_conditions": deterministic_summaries,
            "deterministic_records": family_records,
            "methods": methods_report,
            "evidence_status": {
                "full_vector_raw": "observed",
                "full_vector_glp": "observed",
                "dose_response_circuit_only_raw": "observed",
                "dose_response_circuit_only_glp": "observed",
                "dose_response_random_same_size_controls": "observed",
                "claim_grade_ready": "no" if not glp_alignment.get("claim_grade_ready") else "partial",
            },
            "limitations": [
                "Released GLP remains a diagnostic prior until model/layer alignment is matched.",
                "Circuit-only intervention uses candidate-pool complement ablation inherited from the Stage 4 sufficiency lane.",
                "Random same-size controls aggregate over prompt-level judge scores and may require larger samples for stable tails.",
            ],
        }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week3_glp_sufficiency_sidecar",
        "analysis_target": "behavioral_sufficiency_glp_sidecar",
        "inputs": {
            "config_path": str(CONFIG_PATH),
            "model_name": model_name,
            "traits": traits,
            "methods": methods,
            "dose_response": [float(x) for x in dose_response],
            "prompt_scope": prompt_scope,
            "glp_weights_folder": glp_weights_folder,
            "glp_checkpoint": glp_checkpoint,
            "glp_enabled": bool(glp_enabled),
            "glp_u": float(glp_u),
            "glp_num_timesteps": int(glp_num_timesteps),
            "next_token_loss_diagnostics_enabled": bool(next_token_loss_diagnostics_enabled),
            "random_baseline_samples": int(random_baseline_samples),
            "n_bootstrap": int(n_bootstrap),
            "min_baseline_effect_for_preservation": float(min_baseline_effect_for_preservation),
            "coherence_max_drop": float(coherence_max_drop),
            "max_new_tokens_override": max_new_tokens_override,
            "temperature_override": temperature_override,
            "seed": int(seed),
            "capability_prompt_hash": capability_prompt_hash,
            "output_suffix": output_suffix,
        },
        "thresholds": thresholds,
        "results_by_trait": results_by_trait,
    }


@app.local_entrypoint()
def main(
    target_freeze_artifact: str = DEFAULT_TARGET_FREEZE_ARTIFACT,
    persona_vectors_artifact: str = DEFAULT_PERSONA_VECTORS_ARTIFACT,
    behavioral_source_artifact_map: str = DEFAULT_BEHAVIORAL_SOURCE_ARTIFACT_MAP,
    traits: str = ",".join(DEFAULT_TRAITS),
    methods: str = ",".join(DEFAULT_METHODS),
    dose_response: str = "",
    n_prompts: int = -1,
    heldout_start_index: int = -1,
    random_baseline_samples: int = -1,
    n_bootstrap: int = -1,
    glp_weights_folder: str = "",
    glp_checkpoint: str = "",
    glp_u: float = float("nan"),
    glp_num_timesteps: int = -1,
    prompt_scope: str = "",
    glp_enabled: int = 1,
    max_new_tokens: int = -1,
    next_token_loss_diagnostics: int = -1,
    seed: int = 42,
    output_suffix: str = "",
) -> None:
    config = base._load_config()
    sidecar_config = _load_sidecar_config()
    glp_cfg = sidecar_config.get("glp", {}) if isinstance(sidecar_config.get("glp"), dict) else {}
    week3_cfg = sidecar_config.get("week3_sufficiency_sidecar", {}) if isinstance(sidecar_config.get("week3_sufficiency_sidecar"), dict) else {}

    selected_traits = base._parse_traits(traits)
    selected_methods = _parse_methods(methods)

    target_freeze_path = (
        base._resolve_path(target_freeze_artifact)
        if target_freeze_artifact.strip()
        else base._latest_result_path(STAGE4_RESULTS_DIR, "week3_stage4_target_set_freeze_*.json")
    )
    target_payload = base._load_json(target_freeze_path)
    target_sets_by_trait, candidate_pool_by_trait = _extract_target_sets(target_payload, selected_traits)

    if persona_vectors_artifact.strip():
        vectors_path = base._resolve_path(persona_vectors_artifact)
    else:
        try:
            vectors_path = base._latest_result_path(base.STAGE1_RESULTS_DIR, "week2_persona_vectors_seed42_*.pt")
        except FileNotFoundError:
            vectors_path = base._latest_result_path(base.STAGE1_RESULTS_DIR, "week2_persona_vectors_*.pt")

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

    vectors = base._load_vectors(vectors_path)
    resolved_n_prompts = int(n_prompts) if int(n_prompts) > 0 else int(week3_cfg.get("n_prompts", 8))
    resolved_heldout_start_index = int(heldout_start_index) if int(heldout_start_index) >= 0 else int(week3_cfg.get("heldout_start_index", 0))
    resolved_random_baseline_samples = int(random_baseline_samples) if int(random_baseline_samples) > 0 else int(week3_cfg.get("random_baseline_samples", 8))
    resolved_n_bootstrap = int(n_bootstrap) if int(n_bootstrap) > 0 else int(week3_cfg.get("n_bootstrap", 200))
    resolved_dose_response = _resolve_dose_response(dose_response, week3_cfg.get("dose_response"))
    resolved_prompt_scope = str(prompt_scope or week3_cfg.get("prompt_scope", "all_tokens")).strip().lower()
    if resolved_prompt_scope not in ALLOWED_PROMPT_SCOPES:
        raise ValueError(f"prompt_scope must be one of {sorted(ALLOWED_PROMPT_SCOPES)}")
    resolved_max_new_tokens = (
        int(max_new_tokens)
        if int(max_new_tokens) > 0
        else int(week3_cfg["max_new_tokens"])
        if week3_cfg.get("max_new_tokens") is not None
        else None
    )
    resolved_temperature = (
        float(week3_cfg["temperature"])
        if week3_cfg.get("temperature") is not None
        else None
    )
    if int(next_token_loss_diagnostics) >= 0:
        resolved_next_token_loss_diagnostics = bool(int(next_token_loss_diagnostics))
    else:
        resolved_next_token_loss_diagnostics = bool(week3_cfg.get("next_token_loss_diagnostics", False))

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

    capability_proxy_rows = list(sidecar_config.get("week2_sidecar", {}).get("capability_proxy", []))
    if not isinstance(capability_proxy_rows, list):
        raise ValueError("week2_sidecar.capability_proxy must be a list")
    neutral_system_prompt = str(
        sidecar_config.get("week2_sidecar", {}).get(
            "neutral_system_prompt",
            "You are a helpful, honest, and concise assistant. Answer directly and accurately.",
        )
    )

    resolved_glp_weights_folder = str(glp_weights_folder or glp_cfg.get("weights_folder", ""))
    resolved_glp_checkpoint = str(glp_checkpoint or glp_cfg.get("checkpoint", "final"))
    resolved_glp_u = float(glp_u) if not np.isnan(float(glp_u)) else float(glp_cfg.get("u", 0.5))
    resolved_glp_num_timesteps = int(glp_num_timesteps) if int(glp_num_timesteps) > 0 else int(glp_cfg.get("num_timesteps", 20))

    report = run_week3_glp_sufficiency_sidecar_remote.remote(
        config=config,
        sidecar_config=sidecar_config,
        traits=selected_traits,
        methods=selected_methods,
        dose_response=resolved_dose_response,
        vectors=vectors,
        target_sets_by_trait=target_sets_by_trait,
        candidate_pool_by_trait=candidate_pool_by_trait,
        heldout_pairs_by_trait=heldout_pairs_by_trait,
        heldout_hashes_by_trait=heldout_hashes_by_trait,
        behavioral_source_by_trait=behavioral_source_by_trait,
        glp_weights_folder=resolved_glp_weights_folder,
        glp_checkpoint=resolved_glp_checkpoint,
        glp_u=resolved_glp_u,
        glp_num_timesteps=resolved_glp_num_timesteps,
        prompt_scope=resolved_prompt_scope,
        glp_enabled=bool(int(glp_enabled)),
        seed=int(seed),
        random_baseline_samples=resolved_random_baseline_samples,
        n_bootstrap=resolved_n_bootstrap,
        min_baseline_effect_for_preservation=float(week3_cfg.get("min_baseline_effect_for_preservation", 1.0)),
        coherence_max_drop=float(week3_cfg.get("coherence_max_drop", 10.0)),
        max_new_tokens_override=resolved_max_new_tokens,
        temperature_override=resolved_temperature,
        next_token_loss_diagnostics_enabled=resolved_next_token_loss_diagnostics,
        neutral_system_prompt=neutral_system_prompt,
        capability_proxy_rows=capability_proxy_rows,
        capability_prompt_hash=_hash_json_rows([dict(row) for row in capability_proxy_rows]),
        output_suffix=output_suffix,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{output_suffix.strip()}" if output_suffix.strip() else ""
    out_path = OUT_DIR / f"week3_glp_sufficiency_sidecar_{ts}{suffix}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "artifact": str(out_path),
                "target_freeze_artifact": str(target_freeze_path),
                "persona_vectors_artifact": str(vectors_path),
                "behavioral_source_artifacts_by_trait": {trait: str(path) for trait, path in source_paths_by_trait.items()},
                "traits": selected_traits,
                "methods": selected_methods,
                "dose_response": resolved_dose_response,
                "glp_enabled": bool(int(glp_enabled)),
                "prompt_scope": resolved_prompt_scope,
                "max_new_tokens_override": resolved_max_new_tokens,
                "next_token_loss_diagnostics": resolved_next_token_loss_diagnostics,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
