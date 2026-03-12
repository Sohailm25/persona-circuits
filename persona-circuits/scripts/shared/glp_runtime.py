"""Runtime helpers for loading and applying GLP projectors in sidecar lanes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml


@dataclass
class GLPProjector:
    enabled: bool
    weights_folder: str
    checkpoint: str
    u: float
    num_timesteps: int
    default_layer_idx: int | None
    metadata: dict[str, Any]
    _project_fn: Callable[[Any, int | None, Any | None], Any]
    _cache: dict[int | None, Callable[[Any], Any]] = field(default_factory=dict)

    def postprocess(
        self,
        acts_edit: Any,
        *,
        layer_idx: int | None = None,
        condition_acts: Any | None = None,
    ) -> Any:
        resolved_layer_idx = self.default_layer_idx if layer_idx is None else layer_idx
        return self._project_fn(acts_edit, resolved_layer_idx, condition_acts)


def _read_config_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    class _PathAwareSafeLoader(yaml.SafeLoader):
        pass

    def _construct_path(loader: yaml.SafeLoader, node: yaml.Node) -> str:
        if isinstance(node, yaml.SequenceNode):
            parts = loader.construct_sequence(node)
            return str(Path(*[str(part) for part in parts]))
        return str(loader.construct_scalar(node))

    _PathAwareSafeLoader.add_constructor(
        "tag:yaml.org,2002:python/object/apply:pathlib.PosixPath",
        _construct_path,
    )
    _PathAwareSafeLoader.add_constructor(
        "tag:yaml.org,2002:python/object/apply:pathlib.WindowsPath",
        _construct_path,
    )

    raw = yaml.load(path.read_text(encoding="utf-8"), Loader=_PathAwareSafeLoader)
    return raw if isinstance(raw, dict) else {}


def resolve_glp_metadata(
    *,
    weights_folder: str,
    checkpoint: str,
    metadata_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "weights_folder": str(weights_folder),
        "checkpoint": str(checkpoint),
    }
    if metadata_override:
        metadata.update(metadata_override)

    weights_path = Path(weights_folder)
    if not weights_path.exists() or not weights_path.is_dir():
        metadata.setdefault("config_available", False)
        return metadata

    config_payload = _read_config_yaml(weights_path / "config.yaml")
    if not config_payload:
        metadata.setdefault("config_available", False)
        return metadata

    metadata["config_available"] = True
    metadata["local_weights_dir"] = str(weights_path.resolve())
    metadata["run_name"] = config_payload.get("run_name")
    glp_kwargs = config_payload.get("glp_kwargs", {})
    if isinstance(glp_kwargs, dict):
        tracedict_config = glp_kwargs.get("tracedict_config", {})
        if isinstance(tracedict_config, dict):
            metadata["training_layers"] = tracedict_config.get("layers")
            metadata["training_layer_prefix"] = tracedict_config.get("layer_prefix")
            metadata["training_retain"] = tracedict_config.get("retain")
        denoiser_config = glp_kwargs.get("denoiser_config", {})
        if isinstance(denoiser_config, dict):
            metadata["multi_layer_n_layers"] = denoiser_config.get("multi_layer_n_layers")
            metadata["d_input"] = denoiser_config.get("d_input")
            metadata["n_layers"] = denoiser_config.get("n_layers")
        conditional_config = glp_kwargs.get("conditional_config", {})
        if isinstance(conditional_config, dict) and conditional_config:
            metadata["conditional_config"] = deepcopy(conditional_config)
            metadata["conditional"] = True
            metadata["condition_dim"] = conditional_config.get("condition_dim")
            metadata["target_dim"] = conditional_config.get("target_dim")
            metadata["concat_order"] = conditional_config.get("concat_order")
    metadata["training_model_name"] = config_payload.get("model_name")
    return metadata


def _prepare_conditional_latents(
    *,
    condition_acts: Any,
    target_acts: Any,
    conditional_config: dict[str, Any],
) -> tuple[Any, bool, slice]:
    import torch

    condition_dim = int(conditional_config["condition_dim"])
    target_dim = int(conditional_config["target_dim"])
    concat_order = str(conditional_config.get("concat_order") or "")
    if concat_order != "condition_then_target":
        raise ValueError(f"Unsupported conditional concat_order: {concat_order!r}")

    target = torch.as_tensor(target_acts)
    condition = torch.as_tensor(condition_acts, device=target.device, dtype=target.dtype)
    target_has_seq_dim = target.ndim == 3

    if target.ndim == 2:
        target = target[:, None, :]
    elif target.ndim != 3:
        raise ValueError(f"Expected target acts to have ndim 2 or 3, got {target.ndim}")

    if condition.ndim == 2:
        condition = condition[:, None, :]
    elif condition.ndim != 3:
        raise ValueError(f"Expected condition acts to have ndim 2 or 3, got {condition.ndim}")

    if int(condition.shape[-1]) != condition_dim:
        raise ValueError(f"Expected condition dim {condition_dim}, got {int(condition.shape[-1])}")
    if int(target.shape[-1]) != target_dim:
        raise ValueError(f"Expected target dim {target_dim}, got {int(target.shape[-1])}")
    if int(condition.shape[0]) != int(target.shape[0]):
        raise ValueError(
            f"Condition batch {int(condition.shape[0])} does not match target batch {int(target.shape[0])}"
        )

    if int(condition.shape[1]) != int(target.shape[1]):
        if int(condition.shape[1]) == 1:
            condition = condition.expand(-1, int(target.shape[1]), -1)
        elif int(target.shape[1]) == 1:
            target = target.expand(-1, int(condition.shape[1]), -1)
        else:
            raise ValueError(
                f"Condition seq {int(condition.shape[1])} does not match target seq {int(target.shape[1])}"
            )

    concat = torch.cat([condition, target], dim=-1)
    condition_slice = slice(0, condition_dim)
    return concat, target_has_seq_dim, condition_slice


def _resolve_conditional_target_slice(conditional_config: dict[str, Any]) -> tuple[int, int]:
    condition_dim = conditional_config.get("condition_dim")
    target_dim = conditional_config.get("target_dim")
    target_slice_start = conditional_config.get("target_slice_start")
    target_slice_end = conditional_config.get("target_slice_end")
    missing = [
        key
        for key, value in (
            ("condition_dim", condition_dim),
            ("target_dim", target_dim),
            ("target_slice_start", target_slice_start),
            ("target_slice_end", target_slice_end),
        )
        if value is None
    ]
    if missing:
        raise ValueError(
            "Conditional GLP config missing required fields: "
            + ", ".join(sorted(missing))
        )
    try:
        condition_dim_int = int(condition_dim)
        target_dim_int = int(target_dim)
        slice_start = int(target_slice_start)
        slice_end = int(target_slice_end)
    except (TypeError, ValueError) as exc:
        raise ValueError("Conditional GLP target slice fields must be integer-like") from exc
    if condition_dim_int <= 0 or target_dim_int <= 0:
        raise ValueError("Conditional GLP requires positive condition_dim and target_dim")
    if slice_start != condition_dim_int:
        raise ValueError(
            f"Conditional GLP target_slice_start={slice_start} must equal condition_dim={condition_dim_int}"
        )
    if slice_end != condition_dim_int + target_dim_int:
        raise ValueError(
            "Conditional GLP target_slice_end must equal "
            f"condition_dim + target_dim ({condition_dim_int + target_dim_int}), got {slice_end}"
        )
    if slice_end <= slice_start:
        raise ValueError(
            f"Conditional GLP target slice must be increasing, got start={slice_start}, end={slice_end}"
        )
    return slice_start, slice_end


def _sample_on_manifold_conditional(
    model: Any,
    latents: Any,
    *,
    condition_latents: Any,
    condition_slice: slice,
    num_timesteps: int,
    start_timestep: int | None,
    layer_idx: int | None,
) -> Any:
    import torch

    start_latents = latents.clone()
    model.scheduler.set_timesteps(num_timesteps)
    for timestep in model.scheduler.timesteps:
        if start_timestep is not None and timestep > start_timestep:
            continue
        # Keep the condition half fixed before denoising, zero any condition-side
        # noise prediction, and clamp again after the scheduler update so the
        # target half is the only part that can move over the trajectory.
        latents[..., condition_slice] = condition_latents
        timesteps = timestep[None, ...]
        noise_pred = model.denoiser(
            latents=latents,
            timesteps=timesteps.repeat(latents.shape[0], 1, 1),
            layer_idx=layer_idx,
        )
        noise_pred[..., condition_slice] = 0.0
        latents = model.scheduler.step(noise_pred, timesteps, latents, return_dict=False)[0]
        latents[..., condition_slice] = condition_latents
    return latents


def build_identity_projector(
    *,
    label: str = "identity",
    weights_folder: str = "identity",
    checkpoint: str = "identity",
    u: float = 0.0,
    num_timesteps: int = 0,
    default_layer_idx: int | None = None,
    metadata_override: dict[str, Any] | None = None,
) -> GLPProjector:
    metadata = resolve_glp_metadata(
        weights_folder=weights_folder,
        checkpoint=checkpoint,
        metadata_override=metadata_override,
    )
    metadata.update(
        {
            "projector_mode": label,
            "enabled": False,
        }
    )
    return GLPProjector(
        enabled=False,
        weights_folder=str(weights_folder),
        checkpoint=str(checkpoint),
        u=float(u),
        num_timesteps=int(num_timesteps),
        default_layer_idx=default_layer_idx,
        metadata=metadata,
        _project_fn=lambda acts_edit, layer_idx, condition_acts: acts_edit,
    )


def _supports_layer_conditioning(*, metadata: dict[str, Any], model: Any) -> bool:
    denoiser = getattr(model, "denoiser", None)
    denoiser_model = getattr(denoiser, "model", None)
    runtime_multi_layer_n_layers = getattr(denoiser_model, "multi_layer_n_layers", None)
    if runtime_multi_layer_n_layers is not None:
        try:
            return int(runtime_multi_layer_n_layers) > 1
        except (TypeError, ValueError):
            return False

    metadata_multi_layer_n_layers = metadata.get("multi_layer_n_layers")
    if metadata_multi_layer_n_layers is not None:
        try:
            return int(metadata_multi_layer_n_layers) > 1
        except (TypeError, ValueError):
            return False

    training_layers = metadata.get("training_layers")
    if isinstance(training_layers, list):
        return len(training_layers) > 1
    return False


def load_glp_projector(
    *,
    weights_folder: str,
    checkpoint: str,
    device: str,
    u: float,
    num_timesteps: int,
    default_layer_idx: int | None = None,
    enabled: bool = True,
    metadata_override: dict[str, Any] | None = None,
) -> GLPProjector:
    if not enabled:
        return build_identity_projector(
            label="disabled",
            weights_folder=weights_folder,
            checkpoint=checkpoint,
            u=u,
            num_timesteps=num_timesteps,
            default_layer_idx=default_layer_idx,
            metadata_override=metadata_override,
        )

    try:
        from glp.denoiser import GLP, load_glp  # type: ignore[import-not-found]
        from glp import flow_matching  # type: ignore[import-not-found]
        from glp.script_steer import postprocess_on_manifold_wrapper  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "GLP runtime dependencies are unavailable. Install the GLP package and its inference dependencies."
        ) from exc

    metadata = resolve_glp_metadata(
        weights_folder=weights_folder,
        checkpoint=checkpoint,
        metadata_override=metadata_override,
    )
    metadata.update(
        {
            "projector_mode": "glp",
            "enabled": True,
            "device": str(device),
            "u": float(u),
            "num_timesteps": int(num_timesteps),
            "default_layer_idx": default_layer_idx,
        }
    )

    weights_path = Path(weights_folder)
    if weights_path.exists() and weights_path.is_dir():
        config_payload = _read_config_yaml(weights_path / "config.yaml")
        glp_kwargs = config_payload.get("glp_kwargs") if isinstance(config_payload, dict) else None
        if not isinstance(glp_kwargs, dict):
            raise ValueError(f"Local GLP config missing glp_kwargs: {weights_path / 'config.yaml'}")
        local_glp_kwargs = deepcopy(glp_kwargs)
        conditional_config = (
            deepcopy(local_glp_kwargs.pop("conditional_config"))
            if isinstance(local_glp_kwargs.get("conditional_config"), dict)
            else None
        )
        normalizer_cfg = local_glp_kwargs.setdefault("normalizer_config", {})
        if not isinstance(normalizer_cfg, dict):
            raise ValueError("Local GLP config normalizer_config must be a mapping")
        normalizer_cfg["rep_statistic"] = str(weights_path / "rep_statistics.pt")
        model = GLP(**local_glp_kwargs)
        if conditional_config is not None:
            setattr(model, "conditional_config", conditional_config)
        model.to(device)
        model.load_pretrained(str(weights_path), name=checkpoint)
        metadata["load_source"] = "local_dir"
    else:
        model = load_glp(weights_folder, device=device, checkpoint=checkpoint)
        metadata["load_source"] = "huggingface_or_cache"
    layer_conditioned = _supports_layer_conditioning(metadata=metadata, model=model)
    metadata["layer_conditioned"] = bool(layer_conditioned)
    metadata.setdefault(
        "layer_conditioning_mode",
        "multi_layer" if layer_conditioned else "single_layer_or_unknown",
    )
    conditional_config = metadata.get("conditional_config")
    is_conditional = isinstance(conditional_config, dict) and bool(conditional_config)
    metadata["conditional"] = bool(is_conditional)
    if is_conditional:
        metadata.setdefault("projector_conditioning_mode", "fixed_clean_condition_clamp")
    cache: dict[int | None, Callable[[Any], Any]] = {}

    def _project(acts_edit: Any, layer_idx: int | None, condition_acts: Any | None) -> Any:
        import torch

        resolved_layer_idx = default_layer_idx if layer_idx is None else layer_idx
        projector_layer_idx = resolved_layer_idx if layer_conditioned else None
        if is_conditional:
            if condition_acts is None:
                raise ValueError("Conditional GLP projector requires condition_acts")
            concat, target_has_seq_dim, condition_slice = _prepare_conditional_latents(
                condition_acts=condition_acts,
                target_acts=acts_edit,
                conditional_config=conditional_config,
            )
            normalized_concat = model.normalizer.normalize(concat, layer_idx=projector_layer_idx)
            noise = normalized_concat.new_zeros(normalized_concat.shape)
            target_slice_start, target_slice_end = _resolve_conditional_target_slice(conditional_config)
            noise[..., target_slice_start:target_slice_end] = torch.randn_like(
                normalized_concat[..., target_slice_start:target_slice_end]
            )
            noisy_latents, _, timesteps, _ = flow_matching.fm_prepare(
                model.scheduler,
                normalized_concat,
                noise,
                u=torch.ones(normalized_concat.shape[0]) * float(u),
            )
            sampled = _sample_on_manifold_conditional(
                model,
                noisy_latents,
                condition_latents=normalized_concat[..., condition_slice],
                condition_slice=condition_slice,
                num_timesteps=int(num_timesteps),
                start_timestep=int(timesteps[0].item()),
                layer_idx=projector_layer_idx,
            )
            denormalized = model.normalizer.denormalize(sampled, layer_idx=projector_layer_idx)
            projected = denormalized[..., target_slice_start:target_slice_end]
            if not target_has_seq_dim:
                projected = projected[:, 0, :]
            return projected.to(device=acts_edit.device, dtype=acts_edit.dtype)

        if projector_layer_idx not in cache:
            cache[projector_layer_idx] = postprocess_on_manifold_wrapper(
                model,
                u=float(u),
                num_timesteps=int(num_timesteps),
                layer_idx=projector_layer_idx,
            )
        return cache[projector_layer_idx](acts_edit)

    return GLPProjector(
        enabled=True,
        weights_folder=str(weights_folder),
        checkpoint=str(checkpoint),
        u=float(u),
        num_timesteps=int(num_timesteps),
        default_layer_idx=default_layer_idx,
        metadata=metadata,
        _project_fn=_project,
    )


def build_glp_alignment_report(
    *,
    metadata: dict[str, Any],
    target_model_name: str,
    target_layer: int | None,
) -> dict[str, Any]:
    training_model_name = metadata.get("training_model_name")
    training_layers = metadata.get("training_layers")
    model_match = None
    layer_match = None
    if isinstance(training_model_name, str) and training_model_name.strip():
        model_match = bool(training_model_name.strip() == str(target_model_name).strip())
    if isinstance(training_layers, list) and target_layer is not None:
        try:
            layer_match = int(target_layer) in [int(x) for x in training_layers]
        except (TypeError, ValueError):
            layer_match = None
    return {
        "target_model_name": str(target_model_name),
        "target_layer": target_layer,
        "training_model_name": training_model_name,
        "training_layers": training_layers,
        "model_match": model_match,
        "layer_match": layer_match,
        "claim_grade_ready": bool(model_match is True and (layer_match in {True, None})),
    }
