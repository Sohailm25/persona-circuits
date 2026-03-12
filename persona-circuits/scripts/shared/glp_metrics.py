"""Geometry diagnostics for GLP sidecar interventions."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


DEFAULT_EPS = 1e-8


def _to_numpy_array(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    arr = np.asarray(value, dtype=np.float64)
    return arr


def _flatten_last_dim(value: Any) -> np.ndarray:
    arr = _to_numpy_array(value)
    if arr.size == 0:
        return np.zeros((0,), dtype=np.float64)
    return arr.reshape(-1)


def cosine_similarity(a: Any, b: Any, *, eps: float = DEFAULT_EPS) -> float | None:
    left = _flatten_last_dim(a)
    right = _flatten_last_dim(b)
    if left.size == 0 or right.size == 0 or left.shape != right.shape:
        return None
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm <= float(eps) or right_norm <= float(eps):
        return None
    return float(np.dot(left, right) / (left_norm * right_norm))


def compute_geometry_metrics(
    *,
    original: Any,
    edited: Any,
    projected: Any,
    eps: float = DEFAULT_EPS,
) -> dict[str, float | None]:
    original_arr = _flatten_last_dim(original)
    edited_arr = _flatten_last_dim(edited)
    projected_arr = _flatten_last_dim(projected)
    if not (original_arr.shape == edited_arr.shape == projected_arr.shape):
        raise ValueError("original, edited, and projected arrays must share the same flattened shape")

    edit_delta = edited_arr - original_arr
    projected_delta = projected_arr - original_arr
    repair_delta = projected_arr - edited_arr

    edit_norm = float(np.linalg.norm(edit_delta))
    projected_norm = float(np.linalg.norm(projected_delta))
    repair_norm = float(np.linalg.norm(repair_delta))
    has_nontrivial_edit = edit_norm > float(eps)

    return {
        "edit_norm": edit_norm,
        "projected_shift_norm": projected_norm,
        "repair_norm": repair_norm,
        "repair_to_edit_ratio": float(repair_norm / edit_norm) if has_nontrivial_edit else None,
        "projected_to_edit_ratio": float(projected_norm / edit_norm) if has_nontrivial_edit else None,
        "edit_retention_cosine": cosine_similarity(edit_delta, projected_delta, eps=eps),
        "repair_alignment_cosine": cosine_similarity(repair_delta, edit_delta, eps=eps),
        "projection_cosine_to_original": cosine_similarity(projected_arr, original_arr, eps=eps),
        "projection_cosine_to_edited": cosine_similarity(projected_arr, edited_arr, eps=eps),
    }


def _log_softmax(logits: np.ndarray) -> np.ndarray:
    flat = np.asarray(logits, dtype=np.float64).reshape(-1)
    if flat.size == 0:
        raise ValueError("logits must be non-empty")
    max_logit = float(np.max(flat))
    shifted = flat - max_logit
    log_denom = float(max_logit + math.log(float(np.sum(np.exp(shifted)))))
    return flat - log_denom


def _safe_probabilities_from_log_probs(log_probs: np.ndarray, *, eps: float = DEFAULT_EPS) -> np.ndarray:
    probs = np.exp(np.asarray(log_probs, dtype=np.float64))
    probs = np.clip(probs, float(eps), None)
    total = float(np.sum(probs))
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("Probability vector must have positive finite mass")
    return probs / total


def compute_next_token_loss_metrics(
    *,
    clean_logits: Any,
    hooked_logits: Any,
    target_token_id: int | None = None,
) -> dict[str, float | None]:
    clean_arr = _flatten_last_dim(clean_logits)
    hooked_arr = _flatten_last_dim(hooked_logits)
    if clean_arr.shape != hooked_arr.shape:
        raise ValueError("clean_logits and hooked_logits must share the same flattened shape")
    if clean_arr.size == 0:
        raise ValueError("logit arrays must be non-empty")

    clean_log_probs = _log_softmax(clean_arr)
    hooked_log_probs = _log_softmax(hooked_arr)
    resolved_target = int(np.argmax(clean_arr)) if target_token_id is None else int(target_token_id)
    if resolved_target < 0 or resolved_target >= clean_arr.size:
        raise ValueError("target_token_id is out of range for the provided logits")

    clean_probs = _safe_probabilities_from_log_probs(clean_log_probs)
    hooked_probs = _safe_probabilities_from_log_probs(hooked_log_probs)
    hooked_log_probs_safe = np.log(hooked_probs)
    clean_target_nll = float(-clean_log_probs[resolved_target])
    hooked_target_nll = float(-hooked_log_probs[resolved_target])

    return {
        "clean_target_nll": clean_target_nll,
        "hooked_target_nll": hooked_target_nll,
        "delta_target_nll_vs_clean": float(hooked_target_nll - clean_target_nll),
        "clean_target_prob": float(clean_probs[resolved_target]),
        "hooked_target_prob": float(hooked_probs[resolved_target]),
        "target_logit_delta": float(hooked_arr[resolved_target] - clean_arr[resolved_target]),
        "kl_clean_to_hooked": float(np.sum(clean_probs * (np.log(clean_probs) - hooked_log_probs_safe))),
    }


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "p90": None,
        }
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "p90": float(np.percentile(arr, 90)),
    }


def aggregate_numeric_metrics(rows: list[dict[str, float | None]]) -> dict[str, dict[str, float | int | None]]:
    if not rows:
        return {}
    metrics_by_key: dict[str, list[float]] = {}
    for row in rows:
        for key, value in row.items():
            if value is None:
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            metrics_by_key.setdefault(key, []).append(numeric_value)
    return {key: _numeric_summary(values) for key, values in sorted(metrics_by_key.items())}


def aggregate_geometry_metrics(rows: list[dict[str, float | None]]) -> dict[str, dict[str, float | int | None]]:
    return aggregate_numeric_metrics(rows)
