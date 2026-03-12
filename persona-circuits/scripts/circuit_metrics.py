"""Shared concentration and causal-effect metrics for Stage 3/4 analyses."""

from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np


def _to_nonnegative_array(values: list[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return arr
    arr = np.abs(arr)
    return arr


def gini_coefficient(values: list[float] | np.ndarray) -> float | None:
    arr = _to_nonnegative_array(values)
    if arr.size == 0:
        return None
    total = float(np.sum(arr))
    if total <= 0.0:
        return 0.0
    sorted_arr = np.sort(arr)
    n = sorted_arr.size
    index = np.arange(1, n + 1, dtype=np.float64)
    gini = (2.0 * np.sum(index * sorted_arr) / (n * total)) - ((n + 1.0) / n)
    return float(gini)


def normalized_shannon_entropy(values: list[float] | np.ndarray) -> float | None:
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


def top_p_mass(values: list[float] | np.ndarray, p_fraction: float) -> float | None:
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


def concentration_summary(values: list[float] | np.ndarray) -> dict[str, float | None]:
    return {
        "gini": gini_coefficient(values),
        "entropy_normalized": normalized_shannon_entropy(values),
        "top_1pct_mass": top_p_mass(values, 0.01),
        "top_5pct_mass": top_p_mass(values, 0.05),
        "top_10pct_mass": top_p_mass(values, 0.10),
    }


def cohens_d(sample_a: list[float] | np.ndarray, sample_b: list[float] | np.ndarray) -> float | None:
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


def vargha_delaney_a12(sample_a: list[float] | np.ndarray, sample_b: list[float] | np.ndarray) -> float | None:
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


def bootstrap_ci(
    values: list[float] | np.ndarray,
    *,
    estimator: Callable[[np.ndarray], float],
    seed: int = 42,
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        return {"n": 0, "n_bootstrap": int(n_bootstrap), "ci95": None}
    rng = np.random.default_rng(seed)
    draws = rng.choice(arr, size=(n_bootstrap, arr.size), replace=True)
    est = np.asarray([estimator(draw) for draw in draws], dtype=np.float64)
    return {
        "n": int(arr.size),
        "n_bootstrap": int(n_bootstrap),
        "ci95": {
            "lower": float(np.percentile(est, 2.5)),
            "upper": float(np.percentile(est, 97.5)),
        },
    }


def effect_size_summary(
    sample_a: list[float] | np.ndarray,
    sample_b: list[float] | np.ndarray,
    *,
    seed: int = 42,
    n_bootstrap: int = 1000,
) -> dict[str, Any]:
    a = np.asarray(sample_a, dtype=np.float64).reshape(-1)
    b = np.asarray(sample_b, dtype=np.float64).reshape(-1)
    d = cohens_d(a, b)
    a12 = vargha_delaney_a12(a, b)
    if a.size == 0 or b.size == 0:
        return {
            "n_a": int(a.size),
            "n_b": int(b.size),
            "cohens_d": d,
            "a12": a12,
            "cohens_d_ci95": None,
            "a12_ci95": None,
        }
    rng = np.random.default_rng(seed)
    d_samples: list[float] = []
    a12_samples: list[float] = []
    for _ in range(n_bootstrap):
        a_draw = rng.choice(a, size=a.size, replace=True)
        b_draw = rng.choice(b, size=b.size, replace=True)
        d_boot = cohens_d(a_draw, b_draw)
        a12_boot = vargha_delaney_a12(a_draw, b_draw)
        if d_boot is not None:
            d_samples.append(float(d_boot))
        if a12_boot is not None:
            a12_samples.append(float(a12_boot))
    d_ci = (
        {
            "lower": float(np.percentile(np.asarray(d_samples, dtype=np.float64), 2.5)),
            "upper": float(np.percentile(np.asarray(d_samples, dtype=np.float64), 97.5)),
        }
        if d_samples
        else None
    )
    a12_ci = (
        {
            "lower": float(np.percentile(np.asarray(a12_samples, dtype=np.float64), 2.5)),
            "upper": float(np.percentile(np.asarray(a12_samples, dtype=np.float64), 97.5)),
        }
        if a12_samples
        else None
    )
    return {
        "n_a": int(a.size),
        "n_b": int(b.size),
        "cohens_d": d,
        "a12": a12,
        "cohens_d_ci95": d_ci,
        "a12_ci95": a12_ci,
    }


def random_baseline_selectivity(
    observed_effect: float,
    random_effects: list[float] | np.ndarray,
) -> dict[str, Any]:
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
    # One-sided p-value (random >= observed), +1 correction.
    p_value = float((np.sum(rand >= observed_effect) + 1.0) / (rand.size + 1.0))
    return {
        "n_random": int(rand.size),
        "observed_effect": float(observed_effect),
        "percentile_rank": percentile_rank,
        "p_value_one_sided_ge": p_value,
        "top_1pct_pass": bool(percentile_rank >= 0.99),
    }

