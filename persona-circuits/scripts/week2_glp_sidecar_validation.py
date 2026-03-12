"""Week 2 GLP sidecar validation runner.

This script is intentionally isolated from the primary Week 2 runner so it can be
planned, tested, and launched without modifying active experiment lanes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal
import numpy as np
import yaml

from scripts.shared.behavioral_eval import (
    SlidingWindowRateLimiter,
    _format_chat_prompt,
    judge_score,
)
from scripts.shared.glp_metrics import (
    aggregate_geometry_metrics,
    aggregate_numeric_metrics,
    compute_geometry_metrics,
    compute_next_token_loss_metrics,
)
from scripts.shared.glp_runtime import build_glp_alignment_report, load_glp_projector

APP_NAME = "persona-circuits-week2-glp-sidecar-validation"
MODEL_VOLUME_NAME = "persona-circuits-models"
DEFAULT_TRAITS = ["sycophancy", "evil"]
DEFAULT_RESULTS_DIRNAME = "glp_sidecar"
ALLOWED_PROMPT_SCOPES = {"response_last", "all_tokens"}
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_NEW_TOKENS = 96
DEFAULT_TEMPERATURE = 0.0

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_CONFIG_PATH = ROOT / "configs" / "experiment.yaml"
SIDECAR_CONFIG_PATH = ROOT / "configs" / "glp_sidecar.yaml"
HELDOUT_DIR = ROOT / "prompts" / "heldout"
STAGE1_RESULTS_DIR = ROOT / "results" / "stage1_extraction"
RESULTS_DIR = ROOT / "results" / DEFAULT_RESULTS_DIRNAME

app = modal.App(APP_NAME)
vol = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").apt_install("git").pip_install(
    [
        "torch>=2.1.0",
        "transformers>=4.56.0,<=4.57.3",
        "sae-lens>=6.12.0",
        "transformer-lens>=1.11.0",
        "anthropic",
        "numpy",
        "pyyaml",
        "omegaconf",
        "diffusers",
        "einops",
        "safetensors",
        "huggingface_hub",
        "git+https://github.com/davidbau/baukit.git",
        "git+https://github.com/g-luo/generative_latent_prior.git",
    ]
).add_local_dir(ROOT / "scripts", remote_path="/root/scripts")


def _set_modal_cache_env() -> None:
    os.environ["HF_HOME"] = "/models/huggingface"
    os.environ["TRANSFORMERS_CACHE"] = "/models/huggingface"
    os.environ["HF_HUB_CACHE"] = "/models/huggingface"
    os.environ["HUGGINGFACE_HUB_CACHE"] = "/models/huggingface"
    Path("/models/huggingface").mkdir(parents=True, exist_ok=True)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _load_experiment_config() -> dict[str, Any]:
    return _load_yaml(EXPERIMENT_CONFIG_PATH)


def _load_sidecar_config() -> dict[str, Any]:
    return _load_yaml(SIDECAR_CONFIG_PATH)


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _latest_result_path(base_dir: Path, glob_pattern: str) -> Path:
    matches = sorted(base_dir.glob(glob_pattern))
    if not matches:
        raise FileNotFoundError(f"No files found for pattern: {base_dir / glob_pattern}")
    return matches[-1]


def _parse_traits(raw: str) -> list[str]:
    traits = [x.strip() for x in raw.split(",") if x.strip()]
    if not traits:
        raise ValueError("Trait list cannot be empty.")
    return traits


def _load_vectors(path: Path) -> dict[str, dict[int, list[float]]]:
    import torch

    payload = torch.load(path, map_location="cpu")
    vectors: dict[str, dict[int, list[float]]] = {}
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected vectors artifact schema at {path}")
    for trait, by_layer in payload.items():
        if not isinstance(by_layer, dict):
            continue
        vectors[str(trait)] = {}
        for layer, vec in by_layer.items():
            layer_int = int(layer)
            if hasattr(vec, "tolist"):
                vectors[str(trait)][layer_int] = [float(x) for x in vec.tolist()]
            else:
                vectors[str(trait)][layer_int] = [float(x) for x in vec]
    return vectors


def _load_heldout_pairs(trait: str, max_pairs: int, start_index: int = 0) -> list[dict[str, Any]]:
    path = HELDOUT_DIR / f"{trait}_heldout_pairs.jsonl"
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"No heldout rows found for trait={trait}")
    if int(max_pairs) <= 0:
        raise ValueError("max_pairs must be > 0")
    if int(start_index) < 0:
        raise ValueError("start_index must be >= 0")
    n_rows = len(rows)
    n_take = min(int(max_pairs), n_rows)
    start = int(start_index) % n_rows
    if start + n_take <= n_rows:
        return rows[start : start + n_take]
    return rows[start:] + rows[: (start + n_take - n_rows)]


def _hash_json_rows(rows: list[dict[str, Any]]) -> str:
    canonical = "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_string_list(values: list[str]) -> str:
    canonical = "\n".join(values)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_artifact_map(raw: str) -> dict[str, str]:
    text = raw.strip()
    if not text:
        return {}
    if text.startswith("{"):
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("JSON artifact map must be an object.")
        return {str(k).strip(): str(v).strip() for k, v in parsed.items()}
    out: dict[str, str] = {}
    for chunk in text.split(","):
        entry = chunk.strip()
        if not entry:
            continue
        if ":" not in entry:
            raise ValueError("Artifact map entries must be trait:path pairs.")
        trait, path = entry.split(":", 1)
        out[trait.strip()] = path.strip()
    return out


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
        "judge_model": str(judge_models.get("primary", DEFAULT_JUDGE_MODEL)),
        "max_new_tokens": int(run_metadata.get("max_new_tokens", DEFAULT_MAX_NEW_TOKENS)),
        "temperature": float(run_metadata.get("temperature", DEFAULT_TEMPERATURE)),
    }


def _resolve_generation_settings(
    *,
    source: dict[str, Any],
    sidecar_cfg: dict[str, Any],
    max_new_tokens_override: int | None = None,
) -> tuple[int, float]:
    if max_new_tokens_override is not None and int(max_new_tokens_override) > 0:
        max_new_tokens = int(max_new_tokens_override)
    else:
        max_new_tokens = int(source.get("max_new_tokens", sidecar_cfg.get("max_new_tokens", DEFAULT_MAX_NEW_TOKENS)))
    temperature = float(source.get("temperature", sidecar_cfg.get("temperature", DEFAULT_TEMPERATURE)))
    return max_new_tokens, temperature


def _resolve_alpha(
    *,
    source: dict[str, Any],
    alpha_override: float | None = None,
) -> float:
    if alpha_override is not None and np.isfinite(float(alpha_override)):
        return float(alpha_override)
    return float(source["alpha"])


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(np.mean(np.asarray(values, dtype=np.float64)))


def _safe_delta(lhs: float | None, rhs: float | None) -> float | None:
    if lhs is None or rhs is None:
        return None
    return float(lhs - rhs)


def _event_metric_mean(events: list[dict[str, Any]], key: str) -> float | None:
    values: list[float] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        value = event.get(key)
        if value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return _safe_mean(values)


def _summarize_draw_distribution(draw_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, float | None]] = []
    for summary in draw_summaries:
        rows.append(
            {
                "bidirectional_effect_mean": summary.get("bidirectional_effect_mean"),
                "coherence_mean": summary.get("coherence_mean"),
                "neutral_trait_shift_abs_mean": summary.get("neutral_trait_shift_abs_mean"),
                "capability_correct_fraction_mean": summary.get("capability_correct_fraction_mean"),
                "repair_to_edit_ratio_mean": (
                    summary.get("geometry_summary", {})
                    .get("repair_to_edit_ratio", {})
                    .get("mean")
                ),
                "delta_target_nll_vs_clean_mean": (
                    summary.get("next_token_loss_summary", {})
                    .get("delta_target_nll_vs_clean", {})
                    .get("mean")
                ),
            }
        )
    return aggregate_numeric_metrics(rows)


def _row_record_aliases(
    *,
    family_records: dict[str, list[dict[str, Any]]],
    random_family_records_by_draw: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "row_records_by_family": family_records,
        "random_glp_draw_row_records": {
            str(draw_idx): records for draw_idx, records in sorted(random_family_records_by_draw.items())
        },
        "row_record_schema_version": 1,
    }


def _simple_capability_match(response: str, expected_substrings: list[str]) -> bool:
    text = response.strip().lower()
    if not expected_substrings:
        return False
    return all(str(item).strip().lower() in text for item in expected_substrings)


def _summarize_condition_records(
    *,
    records: list[dict[str, Any]],
    comparison_baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    plus_trait_scores = [float(r["trait_plus_score"]) for r in records]
    minus_trait_scores = [float(r["trait_minus_score"]) for r in records]
    plus_coherence = [float(r["coherence_plus_score"]) for r in records]
    minus_coherence = [float(r["coherence_minus_score"]) for r in records]
    bidirectional = [float(r["trait_plus_score"] - r["trait_minus_score"]) for r in records]
    geometry_rows: list[dict[str, float | None]] = []
    next_token_loss_rows: list[dict[str, float | None]] = []
    for row in records:
        for detail in row.get("geometry_events", []):
            geometry_rows.append(detail)
        for detail in row.get("next_token_loss_events", []):
            next_token_loss_rows.append(detail)

    summary = {
        "n_rows": int(len(records)),
        "trait_plus_mean": _safe_mean(plus_trait_scores),
        "trait_minus_mean": _safe_mean(minus_trait_scores),
        "bidirectional_effect_mean": _safe_mean(bidirectional),
        "coherence_plus_mean": _safe_mean(plus_coherence),
        "coherence_minus_mean": _safe_mean(minus_coherence),
        "coherence_mean": _safe_mean(plus_coherence + minus_coherence),
        "geometry_summary": aggregate_geometry_metrics(geometry_rows),
        "next_token_loss_summary": aggregate_numeric_metrics(next_token_loss_rows),
    }

    bleed_traits: dict[str, list[float]] = {}
    for row in records:
        for bleed_trait, bleed_scores in row.get("bleed_scores", {}).items():
            bleed_traits.setdefault(bleed_trait, []).extend(float(x) for x in bleed_scores)
    summary["bleed_by_trait_mean"] = {
        trait: _safe_mean(scores) for trait, scores in sorted(bleed_traits.items())
    }

    neutral_rows = [row.get("neutral_trait_shift_abs") for row in records if row.get("neutral_trait_shift_abs") is not None]
    summary["neutral_trait_shift_abs_mean"] = _safe_mean([float(x) for x in neutral_rows])

    capability_rows = [row.get("capability_correct_fraction") for row in records if row.get("capability_correct_fraction") is not None]
    summary["capability_correct_fraction_mean"] = _safe_mean([float(x) for x in capability_rows])
    conditioning_regime_counts: dict[str, int] = {}
    for row in records:
        regime = str(row.get("conditioning_regime") or "").strip()
        if not regime:
            continue
        conditioning_regime_counts[regime] = conditioning_regime_counts.get(regime, 0) + 1
    if conditioning_regime_counts:
        summary["conditioning_regime_counts"] = dict(sorted(conditioning_regime_counts.items()))

    if comparison_baseline is not None:
        summary["comparison_vs_raw"] = {
            "bidirectional_effect_delta": _safe_delta(
                summary.get("bidirectional_effect_mean"),
                comparison_baseline.get("bidirectional_effect_mean"),
            ),
            "coherence_mean_delta": _safe_delta(
                summary.get("coherence_mean"),
                comparison_baseline.get("coherence_mean"),
            ),
            "neutral_trait_shift_abs_delta": _safe_delta(
                summary.get("neutral_trait_shift_abs_mean"),
                comparison_baseline.get("neutral_trait_shift_abs_mean"),
            ),
            "capability_correct_fraction_delta": _safe_delta(
                summary.get("capability_correct_fraction_mean"),
                comparison_baseline.get("capability_correct_fraction_mean"),
            ),
        }
    return summary


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=8 * 60 * 60,
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("anthropic-key"),
    ],
    volumes={"/models": vol},
)
def run_week2_glp_sidecar_remote(
    *,
    experiment_config: dict[str, Any],
    sidecar_config: dict[str, Any],
    traits: list[str],
    vectors: dict[str, dict[int, list[float]]],
    heldout_rows_by_trait: dict[str, list[dict[str, Any]]],
    behavioral_source_by_trait: dict[str, dict[str, Any]],
    heldout_hashes_by_trait: dict[str, str],
    neutral_user_prompts: list[str],
    neutral_prompt_hash: str,
    neutral_system_prompt: str,
    capability_proxy_rows: list[dict[str, Any]],
    capability_prompt_hash: str,
    glp_weights_folder: str,
    glp_checkpoint: str,
    glp_u: float,
    glp_num_timesteps: int,
    prompt_scope: str,
    glp_enabled: bool,
    random_direction_draws: int,
    max_new_tokens_override: int | None,
    alpha_override: float | None,
    next_token_loss_diagnostics_enabled: bool,
    seed: int,
    output_suffix: str,
) -> dict[str, Any]:
    import anthropic
    import torch
    from sae_lens import HookedSAETransformer

    if prompt_scope not in ALLOWED_PROMPT_SCOPES:
        raise ValueError(f"prompt_scope must be one of {sorted(ALLOWED_PROMPT_SCOPES)}")
    if int(random_direction_draws) <= 0:
        raise ValueError("random_direction_draws must be > 0")

    _set_modal_cache_env()
    _seed_everything(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    model_name = str(experiment_config["models"]["primary"]["name"])
    model = HookedSAETransformer.from_pretrained(
        model_name,
        device="cuda",
        dtype=torch.bfloat16,
    )
    model.eval()

    sidecar_cfg = sidecar_config.get("week2_sidecar", {}) if isinstance(sidecar_config.get("week2_sidecar"), dict) else {}
    judge_rpm_limit = int(sidecar_cfg.get("judge_rpm_limit_per_run", 120))
    judge_min_interval_seconds = float(sidecar_cfg.get("judge_min_interval_seconds", 0.25))
    judge_max_attempts = int(sidecar_cfg.get("judge_max_attempts", 6))
    judge_retry_base_seconds = float(sidecar_cfg.get("judge_retry_base_seconds", 0.75))
    judge_retry_max_seconds = float(sidecar_cfg.get("judge_retry_max_seconds", 30.0))
    judge_retry_jitter_fraction = float(sidecar_cfg.get("judge_retry_jitter_fraction", 0.2))

    anthropic_client = anthropic.Anthropic()
    judge_limiters: dict[str, SlidingWindowRateLimiter] = {}
    response_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    score_cache: dict[tuple[Any, ...], Any] = {}
    clean_last_logits_cache: dict[str, Any] = {}
    clean_prompt_last_cache: dict[str, Any] = {}

    def _rate_limiter_for(model_name_value: str) -> SlidingWindowRateLimiter:
        if model_name_value not in judge_limiters:
            judge_limiters[model_name_value] = SlidingWindowRateLimiter(
                requests_per_minute=judge_rpm_limit,
                min_interval_seconds=judge_min_interval_seconds,
            )
        return judge_limiters[model_name_value]

    results_by_trait: dict[str, Any] = {}

    for trait_index, trait in enumerate(traits):
        source = behavioral_source_by_trait[trait]
        layer = int(source["layer"])
        alpha = _resolve_alpha(source=source, alpha_override=alpha_override)
        judge_model = str(source.get("judge_model") or sidecar_cfg.get("judge_model", DEFAULT_JUDGE_MODEL))
        max_new_tokens, temperature = _resolve_generation_settings(
            source=source,
            sidecar_cfg=sidecar_cfg,
            max_new_tokens_override=max_new_tokens_override,
        )

        layer_vectors = vectors.get(trait, {})
        if layer not in layer_vectors:
            raise ValueError(f"Trait={trait} layer={layer} missing from vectors artifact")
        selected_direction = torch.tensor(layer_vectors[layer], dtype=torch.float32, device="cuda")
        selected_norm = float(torch.norm(selected_direction).item())
        if selected_norm <= 1e-12:
            raise ValueError(f"Trait={trait} layer={layer} vector has near-zero norm")
        selected_direction = selected_direction / selected_norm

        rng = np.random.default_rng(int(seed) + 1000 * trait_index + len(trait))
        random_directions: list[torch.Tensor] = []
        for _ in range(int(random_direction_draws)):
            random_direction = torch.tensor(
                rng.normal(size=selected_direction.shape[0]),
                dtype=torch.float32,
                device="cuda",
            )
            random_norm = float(torch.norm(random_direction).item())
            if random_norm <= 1e-12:
                raise ValueError("Random direction sampled with near-zero norm")
            random_directions.append(random_direction / random_norm)

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

        other_traits = [other for other in traits if other != trait]
        rows = heldout_rows_by_trait[trait]

        def _generate_with_intervention(
            *,
            prompt_text: str,
            condition_name: str,
            row_key: str,
            direction: torch.Tensor | None,
            alpha_value: float,
            use_glp: bool,
        ) -> dict[str, Any]:
            cache_key = (
                trait,
                condition_name,
                row_key,
                int(layer),
                float(alpha_value),
                bool(use_glp),
                prompt_scope,
                max_new_tokens,
                temperature,
            )
            if cache_key in response_cache:
                return response_cache[cache_key]

            tokens = model.to_tokens(prompt_text, prepend_bos=True)
            geometry_events: list[dict[str, float | None]] = []
            next_token_loss_events: list[dict[str, float | None]] = []
            hook_name = f"blocks.{int(layer)}.hook_resid_post"
            direction_runtime = None
            condition_runtime = None
            conditioning_regime = "unconditional_or_disabled"

            if direction is not None and abs(float(alpha_value)) > 1e-12:
                direction_runtime = direction.to(device=tokens.device, dtype=torch.float32)
                if direction_runtime.ndim == 1:
                    direction_runtime = direction_runtime[None, None, :]
                elif direction_runtime.ndim == 2:
                    direction_runtime = direction_runtime[:, None, :]

            if use_glp and bool(projector.metadata.get("conditional")):
                conditioning_regime = (
                    "clean_condition_edited_target"
                    if direction is not None and abs(float(alpha_value)) > 1e-12
                    else "clean_condition_clean_target"
                )
                if prompt_text not in clean_prompt_last_cache:
                    with torch.no_grad():
                        _, clean_prompt_cache = model.run_with_cache(
                            tokens,
                            names_filter=lambda name: name == hook_name,
                        )
                    clean_prompt_last_cache[prompt_text] = (
                        clean_prompt_cache[hook_name][:, -1:, :].detach().to(torch.float32).cpu()
                    )
                condition_runtime = clean_prompt_last_cache[prompt_text].to(
                    device=tokens.device,
                    dtype=torch.float32,
                )

            def _make_intervention_hook(*, record_metrics: bool) -> Any:
                def intervention_hook(resid_post: Any, hook: Any) -> Any:
                    del hook
                    resid_dtype = resid_post.dtype
                    resid_fp32 = resid_post.to(torch.float32)
                    if prompt_scope == "response_last":
                        original = resid_fp32[:, -1:, :].clone()
                    else:
                        original = resid_fp32.clone()
                    edited = original.clone()
                    if direction_runtime is not None:
                        edited = edited + float(alpha_value) * direction_runtime
                    projected = (
                        projector.postprocess(
                            edited,
                            layer_idx=int(layer),
                            condition_acts=condition_runtime,
                        )
                        if use_glp
                        else edited
                    )
                    if record_metrics:
                        geometry_events.append(
                            compute_geometry_metrics(
                                original=original,
                                edited=edited,
                                projected=projected,
                            )
                        )
                    out_fp32 = resid_fp32.clone()
                    if prompt_scope == "response_last":
                        out_fp32[:, -1:, :] = projected.to(dtype=torch.float32)
                    else:
                        out_fp32 = projected.to(dtype=torch.float32)
                    return out_fp32.to(dtype=resid_dtype)

                return intervention_hook

            has_intervention = direction is not None or use_glp
            if bool(next_token_loss_diagnostics_enabled) and has_intervention:
                clean_logits_key = prompt_text
                if clean_logits_key not in clean_last_logits_cache:
                    with torch.no_grad():
                        clean_logits = model(tokens, return_type="logits")
                    clean_last_logits_cache[clean_logits_key] = clean_logits[:, -1, :].detach().to(torch.float32).cpu()
                clean_last_logits = clean_last_logits_cache[clean_logits_key]
                metric_hooks = [(hook_name, _make_intervention_hook(record_metrics=True))]
                with torch.no_grad():
                    with model.hooks(fwd_hooks=metric_hooks):
                        hooked_logits = model(tokens, return_type="logits")
                next_token_loss_events.append(
                    compute_next_token_loss_metrics(
                        clean_logits=clean_last_logits[0],
                        hooked_logits=hooked_logits[0, -1, :].detach().to(torch.float32).cpu(),
                    )
                )
            elif has_intervention:
                with torch.no_grad():
                    with model.hooks(fwd_hooks=[(hook_name, _make_intervention_hook(record_metrics=True))]):
                        model(tokens, return_type="logits")

            generate_kwargs = {
                "max_new_tokens": int(max_new_tokens),
                "temperature": float(temperature),
                "top_k": None,
                "stop_at_eos": True,
                "verbose": False,
            }

            if has_intervention:
                with model.hooks(fwd_hooks=[(hook_name, _make_intervention_hook(record_metrics=False))]):
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
                "conditioning_regime": conditioning_regime,
            }
            response_cache[cache_key] = result
            return result

        def _score_response(*, score_trait: str, user_query: str, response_text: str, ground_truth: str) -> float:
            score = judge_score(
                anthropic_client=anthropic_client,
                anthropic_module=anthropic,
                judge_model=judge_model,
                score_trait=score_trait,
                user_query=user_query,
                response=response_text,
                ground_truth=ground_truth,
                max_attempts=judge_max_attempts,
                rate_limiter=_rate_limiter_for(judge_model),
                retry_base_seconds=judge_retry_base_seconds,
                retry_max_seconds=judge_retry_max_seconds,
                retry_jitter_fraction=judge_retry_jitter_fraction,
                score_cache=score_cache,
            )
            return float(score.score)

        deterministic_specs = [
            {
                "name": "selected_raw",
                "direction": selected_direction,
                "use_glp": False,
                "label": "selected_direction_raw",
            },
            {
                "name": "selected_glp",
                "direction": selected_direction,
                "use_glp": True,
                "label": "selected_direction_glp",
            },
            {
                "name": "baseline_glp_control",
                "direction": None,
                "use_glp": True,
                "label": "baseline_glp_control",
            },
        ]
        random_specs = [
            {
                "name": "random_glp",
                "direction": direction,
                "use_glp": True,
                "label": f"random_direction_glp_draw_{draw_idx}",
                "draw_idx": int(draw_idx),
            }
            for draw_idx, direction in enumerate(random_directions)
        ]

        family_records: dict[str, list[dict[str, Any]]] = {
            spec["name"]: [] for spec in deterministic_specs
        }
        family_records["random_glp"] = []
        random_family_records_by_draw: dict[int, list[dict[str, Any]]] = {
            int(spec["draw_idx"]): [] for spec in random_specs
        }
        neutral_baseline_scores: list[float] = []
        neutral_baseline_coherence: list[float] = []

        for row in rows:
            row_id = str(row.get("id", len(family_records["selected_raw"])))
            user_query = str(row["user_query"])
            ground_truth = str(row.get("ground_truth", "N/A"))
            low_prompt = _format_chat_prompt(model.tokenizer, str(row["system_low"]), user_query)
            high_prompt = _format_chat_prompt(model.tokenizer, str(row["system_high"]), user_query)

            raw_plus = _generate_with_intervention(
                prompt_text=low_prompt,
                condition_name="raw_reference_plus",
                row_key=f"{row_id}:plus",
                direction=selected_direction,
                alpha_value=float(alpha),
                use_glp=False,
            )
            raw_minus = _generate_with_intervention(
                prompt_text=high_prompt,
                condition_name="raw_reference_minus",
                row_key=f"{row_id}:minus",
                direction=selected_direction,
                alpha_value=float(-alpha),
                use_glp=False,
            )

            raw_plus_trait = _score_response(
                score_trait=trait,
                user_query=user_query,
                response_text=raw_plus["response"],
                ground_truth=ground_truth,
            )
            raw_minus_trait = _score_response(
                score_trait=trait,
                user_query=user_query,
                response_text=raw_minus["response"],
                ground_truth=ground_truth,
            )
            raw_plus_coherence = _score_response(
                score_trait="coherence",
                user_query=user_query,
                response_text=raw_plus["response"],
                ground_truth=ground_truth,
            )
            raw_minus_coherence = _score_response(
                score_trait="coherence",
                user_query=user_query,
                response_text=raw_minus["response"],
                ground_truth=ground_truth,
            )

            raw_bleed = {}
            for bleed_trait in other_traits:
                raw_bleed[bleed_trait] = [
                    _score_response(
                        score_trait=bleed_trait,
                        user_query=user_query,
                        response_text=raw_plus["response"],
                        ground_truth=ground_truth,
                    ),
                    _score_response(
                        score_trait=bleed_trait,
                        user_query=user_query,
                        response_text=raw_minus["response"],
                        ground_truth=ground_truth,
                    ),
                ]

            raw_record = {
                "row_id": row_id,
                "trait_plus_score": raw_plus_trait,
                "trait_minus_score": raw_minus_trait,
                "coherence_plus_score": raw_plus_coherence,
                "coherence_minus_score": raw_minus_coherence,
                "geometry_events": raw_plus["geometry_events"] + raw_minus["geometry_events"],
                "next_token_loss_events": raw_plus["next_token_loss_events"] + raw_minus["next_token_loss_events"],
                "bleed_scores": raw_bleed,
                "conditioning_regime": raw_plus.get("conditioning_regime"),
            }
            family_records["selected_raw"].append(raw_record)

            for spec in deterministic_specs[1:]:
                plus = _generate_with_intervention(
                    prompt_text=low_prompt,
                    condition_name=f"{spec['name']}_plus",
                    row_key=f"{row_id}:plus",
                    direction=spec["direction"],
                    alpha_value=float(alpha) if spec["direction"] is not None else 0.0,
                    use_glp=bool(spec["use_glp"]),
                )
                minus = _generate_with_intervention(
                    prompt_text=high_prompt,
                    condition_name=f"{spec['name']}_minus",
                    row_key=f"{row_id}:minus",
                    direction=spec["direction"],
                    alpha_value=float(-alpha) if spec["direction"] is not None else 0.0,
                    use_glp=bool(spec["use_glp"]),
                )
                plus_trait = _score_response(
                    score_trait=trait,
                    user_query=user_query,
                    response_text=plus["response"],
                    ground_truth=ground_truth,
                )
                minus_trait = _score_response(
                    score_trait=trait,
                    user_query=user_query,
                    response_text=minus["response"],
                    ground_truth=ground_truth,
                )
                plus_coherence = _score_response(
                    score_trait="coherence",
                    user_query=user_query,
                    response_text=plus["response"],
                    ground_truth=ground_truth,
                )
                minus_coherence = _score_response(
                    score_trait="coherence",
                    user_query=user_query,
                    response_text=minus["response"],
                    ground_truth=ground_truth,
                )
                bleed_scores = {}
                for bleed_trait in other_traits:
                    bleed_scores[bleed_trait] = [
                        _score_response(
                            score_trait=bleed_trait,
                            user_query=user_query,
                            response_text=plus["response"],
                            ground_truth=ground_truth,
                        ),
                        _score_response(
                            score_trait=bleed_trait,
                            user_query=user_query,
                            response_text=minus["response"],
                            ground_truth=ground_truth,
                        ),
                    ]
                family_records[spec["name"]].append(
                    {
                        "row_id": row_id,
                        "trait_plus_score": plus_trait,
                        "trait_minus_score": minus_trait,
                        "coherence_plus_score": plus_coherence,
                        "coherence_minus_score": minus_coherence,
                        "geometry_events": plus["geometry_events"] + minus["geometry_events"],
                        "next_token_loss_events": plus["next_token_loss_events"] + minus["next_token_loss_events"],
                        "bleed_scores": bleed_scores,
                        "conditioning_regime": plus.get("conditioning_regime"),
                    }
                )

            for spec in random_specs:
                plus = _generate_with_intervention(
                    prompt_text=low_prompt,
                    condition_name=f"{spec['name']}_draw{spec['draw_idx']}_plus",
                    row_key=f"{row_id}:plus",
                    direction=spec["direction"],
                    alpha_value=float(alpha),
                    use_glp=True,
                )
                minus = _generate_with_intervention(
                    prompt_text=high_prompt,
                    condition_name=f"{spec['name']}_draw{spec['draw_idx']}_minus",
                    row_key=f"{row_id}:minus",
                    direction=spec["direction"],
                    alpha_value=float(-alpha),
                    use_glp=True,
                )
                plus_trait = _score_response(
                    score_trait=trait,
                    user_query=user_query,
                    response_text=plus["response"],
                    ground_truth=ground_truth,
                )
                minus_trait = _score_response(
                    score_trait=trait,
                    user_query=user_query,
                    response_text=minus["response"],
                    ground_truth=ground_truth,
                )
                plus_coherence = _score_response(
                    score_trait="coherence",
                    user_query=user_query,
                    response_text=plus["response"],
                    ground_truth=ground_truth,
                )
                minus_coherence = _score_response(
                    score_trait="coherence",
                    user_query=user_query,
                    response_text=minus["response"],
                    ground_truth=ground_truth,
                )
                bleed_scores = {}
                for bleed_trait in other_traits:
                    bleed_scores[bleed_trait] = [
                        _score_response(
                            score_trait=bleed_trait,
                            user_query=user_query,
                            response_text=plus["response"],
                            ground_truth=ground_truth,
                        ),
                        _score_response(
                            score_trait=bleed_trait,
                            user_query=user_query,
                            response_text=minus["response"],
                            ground_truth=ground_truth,
                        ),
                    ]
                random_record = {
                    "row_id": row_id,
                    "random_draw_idx": int(spec["draw_idx"]),
                    "trait_plus_score": plus_trait,
                    "trait_minus_score": minus_trait,
                    "coherence_plus_score": plus_coherence,
                    "coherence_minus_score": minus_coherence,
                    "geometry_events": plus["geometry_events"] + minus["geometry_events"],
                    "next_token_loss_events": plus["next_token_loss_events"] + minus["next_token_loss_events"],
                    "bleed_scores": bleed_scores,
                    "conditioning_regime": plus.get("conditioning_regime"),
                }
                family_records["random_glp"].append(random_record)
                random_family_records_by_draw[int(spec["draw_idx"])].append(random_record)

        for neutral_prompt in neutral_user_prompts:
            neutral_text = _format_chat_prompt(model.tokenizer, neutral_system_prompt, neutral_prompt)
            baseline_response = _generate_with_intervention(
                prompt_text=neutral_text,
                condition_name="neutral_baseline",
                row_key=neutral_prompt,
                direction=None,
                alpha_value=0.0,
                use_glp=False,
            )
            neutral_baseline_scores.append(
                _score_response(
                    score_trait=trait,
                    user_query=neutral_prompt,
                    response_text=baseline_response["response"],
                    ground_truth="N/A",
                )
            )
            neutral_baseline_coherence.append(
                _score_response(
                    score_trait="coherence",
                    user_query=neutral_prompt,
                    response_text=baseline_response["response"],
                    ground_truth="N/A",
                )
            )

        neutral_baseline_mean = _safe_mean(neutral_baseline_scores)
        capability_family_summary: dict[str, float | None] = {}

        for spec in deterministic_specs + random_specs:
            neutral_shifts: list[float] = []
            capability_matches: list[float] = []
            for neutral_prompt in neutral_user_prompts:
                neutral_text = _format_chat_prompt(model.tokenizer, neutral_system_prompt, neutral_prompt)
                response = _generate_with_intervention(
                    prompt_text=neutral_text,
                    condition_name=f"{spec['name']}_neutral",
                    row_key=neutral_prompt,
                    direction=spec["direction"],
                    alpha_value=float(alpha) if spec["direction"] is not None else 0.0,
                    use_glp=bool(spec["use_glp"]),
                )
                neutral_trait = _score_response(
                    score_trait=trait,
                    user_query=neutral_prompt,
                    response_text=response["response"],
                    ground_truth="N/A",
                )
                if neutral_baseline_mean is not None:
                    neutral_shifts.append(abs(float(neutral_trait) - neutral_baseline_mean))
            for row in capability_proxy_rows:
                prompt = str(row["prompt"])
                expected_substrings = [str(x) for x in row.get("expected_substrings", [])]
                capability_prompt = _format_chat_prompt(model.tokenizer, neutral_system_prompt, prompt)
                response = _generate_with_intervention(
                    prompt_text=capability_prompt,
                    condition_name=f"{spec['name']}_capability",
                    row_key=prompt,
                    direction=spec["direction"],
                    alpha_value=float(alpha) if spec["direction"] is not None else 0.0,
                    use_glp=bool(spec["use_glp"]),
                )
                capability_matches.append(1.0 if _simple_capability_match(response["response"], expected_substrings) else 0.0)
            target_records = (
                random_family_records_by_draw[int(spec["draw_idx"])]
                if spec["name"] == "random_glp"
                else family_records[spec["name"]]
            )
            for record in target_records:
                record["neutral_trait_shift_abs"] = _safe_mean(neutral_shifts)
                record["capability_correct_fraction"] = _safe_mean(capability_matches)
            if spec["name"] != "random_glp":
                capability_family_summary[spec["name"]] = _safe_mean(capability_matches)

        random_capability_values = [
            record.get("capability_correct_fraction")
            for record in family_records["random_glp"]
            if record.get("capability_correct_fraction") is not None
        ]
        capability_family_summary["random_glp"] = _safe_mean([float(x) for x in random_capability_values])

        family_summaries: dict[str, Any] = {}
        raw_summary = _summarize_condition_records(
            records=family_records["selected_raw"],
            comparison_baseline=None,
        )
        family_summaries["selected_raw"] = raw_summary
        for spec in deterministic_specs[1:]:
            family_summaries[spec["name"]] = _summarize_condition_records(
                records=family_records[spec["name"]],
                comparison_baseline=raw_summary,
            )
        random_draw_summaries = [
            _summarize_condition_records(
                records=random_family_records_by_draw[int(draw_idx)],
                comparison_baseline=raw_summary,
            )
            for draw_idx in sorted(random_family_records_by_draw)
        ]
        family_summaries["random_glp"] = _summarize_condition_records(
            records=family_records["random_glp"],
            comparison_baseline=raw_summary,
        )
        family_summaries["random_glp"]["draw_count"] = int(len(random_draw_summaries))
        family_summaries["random_glp"]["draw_distribution"] = _summarize_draw_distribution(random_draw_summaries)

        results_by_trait[trait] = {
            "behavioral_source": source,
            "alpha_applied": float(alpha),
            "glp_alignment": glp_alignment,
            "heldout_hash": heldout_hashes_by_trait[trait],
            "n_rows": int(len(rows)),
            "prompt_scope": prompt_scope,
            "neutral_baseline_trait_mean": neutral_baseline_mean,
            "neutral_baseline_coherence_mean": _safe_mean(neutral_baseline_coherence),
            "capability_family_summary": capability_family_summary,
            "families": family_summaries,
            "family_records": family_records,
            "random_glp_draw_records": {
                str(draw_idx): records for draw_idx, records in sorted(random_family_records_by_draw.items())
            },
            **_row_record_aliases(
                family_records=family_records,
                random_family_records_by_draw=random_family_records_by_draw,
            ),
            "evidence_status": {
                "raw_vs_glp_comparison": "observed",
                "claim_grade_ready": "no" if not glp_alignment.get("claim_grade_ready") else "partial",
            },
        }

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_glp_sidecar_validation",
        "inputs": {
            "traits": traits,
            "glp_weights_folder": glp_weights_folder,
            "glp_checkpoint": glp_checkpoint,
            "glp_enabled": bool(glp_enabled),
            "glp_u": float(glp_u),
            "glp_num_timesteps": int(glp_num_timesteps),
            "prompt_scope": prompt_scope,
            "next_token_loss_diagnostics_enabled": bool(next_token_loss_diagnostics_enabled),
            "random_direction_draws": int(random_direction_draws),
            "seed": int(seed),
            "max_new_tokens_override": max_new_tokens_override,
            "alpha_override": None if alpha_override is None else float(alpha_override),
            "neutral_prompt_hash": neutral_prompt_hash,
            "capability_prompt_hash": capability_prompt_hash,
            "output_suffix": output_suffix,
        },
        "results_by_trait": results_by_trait,
    }


@app.local_entrypoint()
def main(
    traits: str = ",".join(DEFAULT_TRAITS),
    persona_vectors_artifact: str = "",
    behavioral_source_artifact_map: str = "",
    n_prompts: int = -1,
    heldout_start_index: int = -1,
    glp_weights_folder: str = "",
    glp_checkpoint: str = "",
    glp_u: float = float("nan"),
    glp_num_timesteps: int = -1,
    prompt_scope: str = "",
    glp_enabled: int = 1,
    max_new_tokens: int = -1,
    alpha_override: float = float("nan"),
    next_token_loss_diagnostics: int = -1,
    random_direction_draws: int = -1,
    seed: int = 42,
    output_suffix: str = "",
) -> None:
    experiment_config = _load_experiment_config()
    sidecar_config = _load_sidecar_config()
    week2_cfg = sidecar_config.get("week2_sidecar", {}) if isinstance(sidecar_config.get("week2_sidecar"), dict) else {}
    glp_cfg = sidecar_config.get("glp", {}) if isinstance(sidecar_config.get("glp"), dict) else {}

    selected_traits = _parse_traits(traits)
    vectors_path = _resolve_path(persona_vectors_artifact) if persona_vectors_artifact.strip() else _latest_result_path(
        STAGE1_RESULTS_DIR,
        "week2_persona_vectors_seed42_*.pt",
    )
    source_map_raw = _parse_artifact_map(behavioral_source_artifact_map)
    source_paths_by_trait: dict[str, Path] = {}
    for trait in selected_traits:
        if trait in source_map_raw:
            source_paths_by_trait[trait] = _resolve_path(source_map_raw[trait])
        else:
            source_paths_by_trait[trait] = _latest_result_path(
                STAGE1_RESULTS_DIR,
                f"week2_behavioral_validation_upgrade_{trait}_*.json",
            )

    vectors = _load_vectors(vectors_path)
    resolved_n_prompts = int(n_prompts) if int(n_prompts) > 0 else int(week2_cfg.get("n_prompts", 10))
    resolved_heldout_start_index = int(heldout_start_index) if int(heldout_start_index) >= 0 else int(week2_cfg.get("heldout_start_index", 0))
    heldout_rows_by_trait = {
        trait: _load_heldout_pairs(trait, max_pairs=resolved_n_prompts, start_index=resolved_heldout_start_index)
        for trait in selected_traits
    }
    heldout_hashes_by_trait = {
        trait: _hash_json_rows(rows) for trait, rows in heldout_rows_by_trait.items()
    }

    behavioral_source_by_trait: dict[str, dict[str, Any]] = {}
    for trait in selected_traits:
        payload = json.loads(source_paths_by_trait[trait].read_text(encoding="utf-8"))
        behavioral_source_by_trait[trait] = _extract_behavioral_source_settings(
            payload=payload,
            trait=trait,
            source_artifact_path=str(source_paths_by_trait[trait]),
        )

    neutral_user_prompts = [str(x) for x in week2_cfg.get("neutral_user_prompts", [])]
    neutral_system_prompt = str(
        week2_cfg.get(
            "neutral_system_prompt",
            "You are a helpful, honest, and concise assistant. Answer directly and accurately.",
        )
    )
    capability_proxy_rows = list(week2_cfg.get("capability_proxy", []))
    if not isinstance(capability_proxy_rows, list):
        raise ValueError("week2_sidecar.capability_proxy must be a list")

    resolved_glp_weights_folder = str(glp_weights_folder or glp_cfg.get("weights_folder", ""))
    resolved_glp_checkpoint = str(glp_checkpoint or glp_cfg.get("checkpoint", "final"))
    resolved_glp_u = float(glp_u) if not np.isnan(float(glp_u)) else float(glp_cfg.get("u", 0.5))
    resolved_glp_num_timesteps = int(glp_num_timesteps) if int(glp_num_timesteps) > 0 else int(glp_cfg.get("num_timesteps", 20))
    resolved_prompt_scope = str(prompt_scope or glp_cfg.get("prompt_scope", "response_last")).strip().lower()
    resolved_max_new_tokens_override = int(max_new_tokens) if int(max_new_tokens) > 0 else None
    resolved_alpha_override = float(alpha_override) if np.isfinite(float(alpha_override)) else None
    if int(next_token_loss_diagnostics) >= 0:
        resolved_next_token_loss_diagnostics = bool(int(next_token_loss_diagnostics))
    else:
        resolved_next_token_loss_diagnostics = bool(week2_cfg.get("next_token_loss_diagnostics", False))
    resolved_random_direction_draws = (
        int(random_direction_draws)
        if int(random_direction_draws) > 0
        else int(week2_cfg.get("random_direction_draws", 1))
    )
    if resolved_prompt_scope not in ALLOWED_PROMPT_SCOPES:
        raise ValueError(f"prompt_scope must be one of {sorted(ALLOWED_PROMPT_SCOPES)}")

    report = run_week2_glp_sidecar_remote.remote(
        experiment_config=experiment_config,
        sidecar_config=sidecar_config,
        traits=selected_traits,
        vectors=vectors,
        heldout_rows_by_trait=heldout_rows_by_trait,
        behavioral_source_by_trait=behavioral_source_by_trait,
        heldout_hashes_by_trait=heldout_hashes_by_trait,
        neutral_user_prompts=neutral_user_prompts,
        neutral_prompt_hash=_hash_string_list(neutral_user_prompts),
        neutral_system_prompt=neutral_system_prompt,
        capability_proxy_rows=capability_proxy_rows,
        capability_prompt_hash=_hash_json_rows([dict(row) for row in capability_proxy_rows]),
        glp_weights_folder=resolved_glp_weights_folder,
        glp_checkpoint=resolved_glp_checkpoint,
        glp_u=resolved_glp_u,
        glp_num_timesteps=resolved_glp_num_timesteps,
        prompt_scope=resolved_prompt_scope,
        glp_enabled=bool(int(glp_enabled)),
        random_direction_draws=resolved_random_direction_draws,
        max_new_tokens_override=resolved_max_new_tokens_override,
        alpha_override=resolved_alpha_override,
        next_token_loss_diagnostics_enabled=resolved_next_token_loss_diagnostics,
        seed=int(seed),
        output_suffix=output_suffix,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{output_suffix.strip()}" if output_suffix.strip() else ""
    out_path = RESULTS_DIR / f"week2_glp_sidecar_validation_{ts}{suffix}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "artifact": str(out_path),
                "traits": selected_traits,
                "persona_vectors_artifact": str(vectors_path),
                "behavioral_source_artifacts_by_trait": {trait: str(path) for trait, path in source_paths_by_trait.items()},
                "glp_enabled": bool(int(glp_enabled)),
                "prompt_scope": resolved_prompt_scope,
                "max_new_tokens_override": resolved_max_new_tokens_override,
                "alpha_override": resolved_alpha_override,
                "next_token_loss_diagnostics": resolved_next_token_loss_diagnostics,
                "random_direction_draws": resolved_random_direction_draws,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
