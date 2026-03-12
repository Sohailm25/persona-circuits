"""Aggregate Week 2 GLP sidecar artifacts into a compact comparison report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results" / "glp_sidecar"
OUTPUT_DIR = ROOT / "results" / "glp_sidecar"


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _latest_artifacts(limit: int) -> list[Path]:
    artifacts = sorted(INPUT_DIR.glob("week2_glp_sidecar_validation_*.json"))
    if not artifacts:
        raise FileNotFoundError(f"No GLP sidecar artifacts found in {INPUT_DIR}")
    return artifacts[-int(limit) :]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_delta(lhs: float | None, rhs: float | None) -> float | None:
    if lhs is None or rhs is None:
        return None
    return float(lhs - rhs)


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(np.mean(np.asarray(values, dtype=np.float64)))


def _record_effect_mean(record: dict[str, Any]) -> float | None:
    try:
        return float(record["trait_plus_score"]) - float(record["trait_minus_score"])
    except (KeyError, TypeError, ValueError):
        return None


def _record_coherence_mean(record: dict[str, Any]) -> float | None:
    try:
        values = [float(record["coherence_plus_score"]), float(record["coherence_minus_score"])]
    except (KeyError, TypeError, ValueError):
        return None
    return _safe_mean(values)


def _event_metric_mean(record: dict[str, Any], event_key: str, metric_key: str) -> float | None:
    events = record.get(event_key, [])
    if not isinstance(events, list):
        return None
    values: list[float] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        value = event.get(metric_key)
        if value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return _safe_mean(values)


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.shape[0], dtype=np.float64)
    sorted_vals = values[order]
    start = 0
    while start < sorted_vals.size:
        end = start + 1
        while end < sorted_vals.size and sorted_vals[end] == sorted_vals[start]:
            end += 1
        rank_value = 0.5 * (start + end - 1) + 1.0
        ranks[order[start:end]] = rank_value
        start = end
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x = np.asarray(xs, dtype=np.float64)
    y = np.asarray(ys, dtype=np.float64)
    if float(np.std(x)) <= 0.0 or float(np.std(y)) <= 0.0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _correlation_summary(xs: list[float], ys: list[float]) -> dict[str, float | int | None]:
    if len(xs) != len(ys):
        raise ValueError("correlation inputs must be aligned")
    spearman = None
    if len(xs) >= 2:
        x_rank = _rankdata(np.asarray(xs, dtype=np.float64))
        y_rank = _rankdata(np.asarray(ys, dtype=np.float64))
        spearman = _pearson(x_rank.tolist(), y_rank.tolist())
    return {
        "n": int(len(xs)),
        "pearson": _pearson(xs, ys),
        "spearman": spearman,
    }


def _align_records_by_row_id(
    lhs_records: list[dict[str, Any]],
    rhs_records: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    rhs_by_row: dict[str, dict[str, Any]] = {}
    for record in rhs_records:
        row_id = str(record.get("row_id"))
        rhs_by_row[row_id] = record
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for record in lhs_records:
        row_id = str(record.get("row_id"))
        if row_id in rhs_by_row:
            pairs.append((record, rhs_by_row[row_id]))
    return pairs


def _resolve_family_records(payload: dict[str, Any]) -> dict[str, Any] | None:
    family_records = payload.get("row_records_by_family")
    if isinstance(family_records, dict):
        return family_records
    family_records = payload.get("family_records")
    if isinstance(family_records, dict):
        return family_records
    return None


def _metric_validity_summary(payload: dict[str, Any]) -> dict[str, Any]:
    family_records = _resolve_family_records(payload)
    if family_records is None:
        return {"status": "unavailable", "reason": "artifact_missing_family_records"}
    raw_records = family_records.get("selected_raw")
    glp_records = family_records.get("selected_glp")
    if not isinstance(raw_records, list) or not isinstance(glp_records, list):
        return {"status": "unavailable", "reason": "selected_raw_or_selected_glp_records_missing"}
    pairs = _align_records_by_row_id(glp_records, raw_records)
    if len(pairs) < 2:
        return {"status": "unavailable", "reason": "insufficient_aligned_rows", "n_rows": int(len(pairs))}

    nll_means: list[float] = []
    repair_means: list[float] = []
    coherence_deltas: list[float] = []
    effect_deltas: list[float] = []
    glp_coherence: list[float] = []
    glp_effect: list[float] = []

    for glp_record, raw_record in pairs:
        nll_value = _event_metric_mean(glp_record, "next_token_loss_events", "delta_target_nll_vs_clean")
        repair_value = _event_metric_mean(glp_record, "geometry_events", "repair_to_edit_ratio")
        glp_coherence_value = _record_coherence_mean(glp_record)
        raw_coherence_value = _record_coherence_mean(raw_record)
        glp_effect_value = _record_effect_mean(glp_record)
        raw_effect_value = _record_effect_mean(raw_record)
        if (
            nll_value is None
            or repair_value is None
            or glp_coherence_value is None
            or raw_coherence_value is None
            or glp_effect_value is None
            or raw_effect_value is None
        ):
            continue
        nll_means.append(float(nll_value))
        repair_means.append(float(repair_value))
        coherence_deltas.append(float(glp_coherence_value - raw_coherence_value))
        effect_deltas.append(float(glp_effect_value - raw_effect_value))
        glp_coherence.append(float(glp_coherence_value))
        glp_effect.append(float(glp_effect_value))

    if len(nll_means) < 2:
        return {"status": "unavailable", "reason": "insufficient_numeric_rows", "n_rows": int(len(nll_means))}

    return {
        "status": "available",
        "n_rows": int(len(nll_means)),
        "nll_vs_coherence_delta": _correlation_summary(nll_means, coherence_deltas),
        "nll_vs_effect_delta": _correlation_summary(nll_means, effect_deltas),
        "repair_ratio_vs_coherence_delta": _correlation_summary(repair_means, coherence_deltas),
        "repair_ratio_vs_effect_delta": _correlation_summary(repair_means, effect_deltas),
        "nll_vs_glp_coherence": _correlation_summary(nll_means, glp_coherence),
        "nll_vs_glp_effect": _correlation_summary(nll_means, glp_effect),
    }


def _summarize_trait(payload: dict[str, Any]) -> dict[str, Any]:
    families = payload.get("families", {}) if isinstance(payload.get("families"), dict) else {}
    raw = families.get("selected_raw", {}) if isinstance(families.get("selected_raw"), dict) else {}
    glp = families.get("selected_glp", {}) if isinstance(families.get("selected_glp"), dict) else {}
    random_glp = families.get("random_glp", {}) if isinstance(families.get("random_glp"), dict) else {}
    baseline_glp = families.get("baseline_glp_control", {}) if isinstance(families.get("baseline_glp_control"), dict) else {}

    return {
        "raw_bidirectional_effect_mean": raw.get("bidirectional_effect_mean"),
        "glp_bidirectional_effect_mean": glp.get("bidirectional_effect_mean"),
        "raw_coherence_mean": raw.get("coherence_mean"),
        "glp_coherence_mean": glp.get("coherence_mean"),
        "glp_minus_raw_bidirectional": _safe_delta(
            glp.get("bidirectional_effect_mean"), raw.get("bidirectional_effect_mean")
        ),
        "glp_minus_raw_coherence": _safe_delta(
            glp.get("coherence_mean"), raw.get("coherence_mean")
        ),
        "glp_minus_raw_neutral_shift_abs": _safe_delta(
            glp.get("neutral_trait_shift_abs_mean"), raw.get("neutral_trait_shift_abs_mean")
        ),
        "glp_minus_raw_capability_fraction": _safe_delta(
            glp.get("capability_correct_fraction_mean"), raw.get("capability_correct_fraction_mean")
        ),
        "random_glp_bidirectional_effect_mean": random_glp.get("bidirectional_effect_mean"),
        "baseline_glp_bidirectional_effect_mean": baseline_glp.get("bidirectional_effect_mean"),
        "selected_glp_geometry_repair_ratio_mean": (
            glp.get("geometry_summary", {})
            .get("repair_to_edit_ratio", {})
            .get("mean")
        ),
        "selected_glp_geometry_retention_cosine_mean": (
            glp.get("geometry_summary", {})
            .get("edit_retention_cosine", {})
            .get("mean")
        ),
        "selected_glp_metric_validity": _metric_validity_summary(payload),
        "random_glp_draw_distribution": (
            families.get("random_glp", {}).get("draw_distribution")
            if isinstance(families.get("random_glp"), dict)
            else None
        ),
        "conditioning_regimes": {
            "selected_glp": glp.get("conditioning_regime_counts"),
            "baseline_glp_control": baseline_glp.get("conditioning_regime_counts"),
            "random_glp": random_glp.get("conditioning_regime_counts"),
        },
        "glp_alignment": payload.get("glp_alignment", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="*", help="Optional explicit artifact paths")
    parser.add_argument("--latest", type=int, default=0, help="Load the latest N artifacts if none are passed")
    args = parser.parse_args()

    if args.artifacts:
        artifact_paths = [_resolve_path(path) for path in args.artifacts]
    else:
        artifact_paths = _latest_artifacts(limit=max(1, int(args.latest or 1)))

    payloads = [(path, _load_json(path)) for path in artifact_paths]
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_glp_sidecar_analysis",
        "inputs": [str(path) for path, _ in payloads],
        "summary_by_artifact": {},
    }

    for path, payload in payloads:
        by_trait = payload.get("results_by_trait", {}) if isinstance(payload.get("results_by_trait"), dict) else {}
        report["summary_by_artifact"][str(path)] = {
            trait: _summarize_trait(trait_payload)
            for trait, trait_payload in sorted(by_trait.items())
        }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"week2_glp_sidecar_analysis_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "inputs": report["inputs"]}, indent=2))


if __name__ == "__main__":
    main()
