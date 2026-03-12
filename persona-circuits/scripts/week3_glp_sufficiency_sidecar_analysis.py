"""Aggregate Week 3 GLP sufficiency sidecar artifacts into a compact comparison report."""

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
    artifacts = sorted(INPUT_DIR.glob("week3_glp_sufficiency_sidecar_*.json"))
    if not artifacts:
        raise FileNotFoundError(f"No Week 3 GLP sidecar artifacts found in {INPUT_DIR}")
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
        spearman = _pearson(
            _rankdata(np.asarray(xs, dtype=np.float64)).tolist(),
            _rankdata(np.asarray(ys, dtype=np.float64)).tolist(),
        )
    return {
        "n": int(len(xs)),
        "pearson": _pearson(xs, ys),
        "spearman": spearman,
    }


def _condition_metric_validity(records: Any, *, target_key: str) -> dict[str, Any]:
    if not isinstance(records, list) or len(records) < 2:
        return {"status": "unavailable", "reason": "insufficient_records"}
    nll_values: list[float] = []
    repair_values: list[float] = []
    coherence_values: list[float] = []
    target_values: list[float] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        nll_value = _event_metric_mean(record, "next_token_loss_events", "delta_target_nll_vs_clean")
        repair_value = _event_metric_mean(record, "geometry_events", "repair_to_edit_ratio")
        coherence_value = record.get("coherence_score")
        target_value = record.get(target_key)
        if (
            nll_value is None
            or repair_value is None
            or coherence_value is None
            or target_value is None
        ):
            continue
        nll_values.append(float(nll_value))
        repair_values.append(float(repair_value))
        coherence_values.append(float(coherence_value))
        target_values.append(float(target_value))
    if len(nll_values) < 2:
        return {"status": "unavailable", "reason": "insufficient_numeric_rows", "n_rows": int(len(nll_values))}
    return {
        "status": "available",
        "n_rows": int(len(nll_values)),
        "nll_vs_coherence": _correlation_summary(nll_values, coherence_values),
        "nll_vs_target": _correlation_summary(nll_values, target_values),
        "repair_ratio_vs_coherence": _correlation_summary(repair_values, coherence_values),
        "repair_ratio_vs_target": _correlation_summary(repair_values, target_values),
    }


def _best_dose(method_payload: dict[str, Any]) -> dict[str, Any]:
    dose_reports = method_payload.get("dose_fraction_reports", {}) if isinstance(method_payload.get("dose_fraction_reports"), dict) else {}
    ranked: list[tuple[float, str, dict[str, Any]]] = []
    for dose_key, dose_payload in sorted(dose_reports.items()):
        if not isinstance(dose_payload, dict):
            continue
        conditions = dose_payload.get("conditions", {}) if isinstance(dose_payload.get("conditions"), dict) else {}
        glp_cond = conditions.get("circuit_only_glp", {}) if isinstance(conditions.get("circuit_only_glp"), dict) else {}
        raw_cond = conditions.get("circuit_only_raw", {}) if isinstance(conditions.get("circuit_only_raw"), dict) else {}
        score = glp_cond.get("preservation_vs_raw_full_mean")
        coherence = glp_cond.get("coherence_mean")
        if score is None or coherence is None:
            continue
        ranked.append((float(score), str(dose_key), {"glp": glp_cond, "raw": raw_cond, "dose": dose_payload}))
    if not ranked:
        return {}
    ranked.sort(key=lambda item: (item[0], item[2]["glp"].get("coherence_mean") or 0.0), reverse=True)
    _, best_key, best_payload = ranked[0]
    return {
        "dose_key": best_key,
        "preserved_fraction_target": best_payload["dose"].get("preserved_fraction_target"),
        "circuit_only_glp_preservation_vs_raw_full_mean": best_payload["glp"].get("preservation_vs_raw_full_mean"),
        "circuit_only_raw_preservation_vs_raw_full_mean": best_payload["raw"].get("preservation_vs_raw_full_mean"),
        "glp_minus_raw_preservation_vs_raw_full": _safe_delta(
            best_payload["glp"].get("preservation_vs_raw_full_mean"),
            best_payload["raw"].get("preservation_vs_raw_full_mean"),
        ),
        "circuit_only_glp_coherence_mean": best_payload["glp"].get("coherence_mean"),
        "circuit_only_raw_coherence_mean": best_payload["raw"].get("coherence_mean"),
    }


def _summarize_method(method_payload: dict[str, Any]) -> dict[str, Any]:
    dose_reports = method_payload.get("dose_fraction_reports", {}) if isinstance(method_payload.get("dose_fraction_reports"), dict) else {}
    summary_by_dose: dict[str, Any] = {}
    for dose_key, dose_payload in sorted(dose_reports.items()):
        if not isinstance(dose_payload, dict):
            continue
        conditions = dose_payload.get("conditions", {}) if isinstance(dose_payload.get("conditions"), dict) else {}
        condition_records = dose_payload.get("condition_records", {}) if isinstance(dose_payload.get("condition_records"), dict) else {}
        raw = conditions.get("circuit_only_raw", {}) if isinstance(conditions.get("circuit_only_raw"), dict) else {}
        glp = conditions.get("circuit_only_glp", {}) if isinstance(conditions.get("circuit_only_glp"), dict) else {}
        random_raw = conditions.get("random_same_size_circuit_raw", {}) if isinstance(conditions.get("random_same_size_circuit_raw"), dict) else {}
        random_glp = conditions.get("random_same_size_circuit_glp", {}) if isinstance(conditions.get("random_same_size_circuit_glp"), dict) else {}
        summary_by_dose[dose_key] = {
            "preserved_fraction_target": dose_payload.get("preserved_fraction_target"),
            "circuit_only_raw_preservation_vs_raw_full_mean": raw.get("preservation_vs_raw_full_mean"),
            "circuit_only_glp_preservation_vs_raw_full_mean": glp.get("preservation_vs_raw_full_mean"),
            "glp_minus_raw_preservation_vs_raw_full": _safe_delta(
                glp.get("preservation_vs_raw_full_mean"),
                raw.get("preservation_vs_raw_full_mean"),
            ),
            "circuit_only_raw_coherence_mean": raw.get("coherence_mean"),
            "circuit_only_glp_coherence_mean": glp.get("coherence_mean"),
            "glp_minus_raw_coherence": _safe_delta(
                glp.get("coherence_mean"),
                raw.get("coherence_mean"),
            ),
            "random_raw_selectivity_p": random_raw.get("selectivity_vs_observed", {}).get("p_value_one_sided_ge"),
            "random_glp_selectivity_p": random_glp.get("selectivity_vs_observed", {}).get("p_value_one_sided_ge"),
            "metric_validity": {
                "circuit_only_raw": _condition_metric_validity(
                    condition_records.get("circuit_only_raw"),
                    target_key="preservation_vs_raw_full",
                ),
                "circuit_only_glp": _condition_metric_validity(
                    condition_records.get("circuit_only_glp"),
                    target_key="preservation_vs_raw_full",
                ),
            },
        }
    return {
        "best_dose_by_glp_preservation": _best_dose(method_payload),
        "dose_fraction_reports": summary_by_dose,
    }


def _summarize_trait(payload: dict[str, Any]) -> dict[str, Any]:
    deterministic = payload.get("deterministic_conditions", {}) if isinstance(payload.get("deterministic_conditions"), dict) else {}
    deterministic_records = payload.get("deterministic_records", {}) if isinstance(payload.get("deterministic_records"), dict) else {}
    methods = payload.get("methods", {}) if isinstance(payload.get("methods"), dict) else {}
    return {
        "glp_alignment": payload.get("glp_alignment", {}),
        "prompt_scope": payload.get("prompt_scope"),
        "deterministic_conditions": {
            "full_vector_raw": {
                "trait_score_mean": deterministic.get("full_vector_raw", {}).get("trait_score_mean"),
                "coherence_mean": deterministic.get("full_vector_raw", {}).get("coherence_mean"),
            },
            "full_vector_glp": {
                "trait_score_mean": deterministic.get("full_vector_glp", {}).get("trait_score_mean"),
                "coherence_mean": deterministic.get("full_vector_glp", {}).get("coherence_mean"),
                "glp_minus_raw_trait_score": _safe_delta(
                    deterministic.get("full_vector_glp", {}).get("trait_score_mean"),
                    deterministic.get("full_vector_raw", {}).get("trait_score_mean"),
                ),
                "glp_minus_raw_coherence": _safe_delta(
                    deterministic.get("full_vector_glp", {}).get("coherence_mean"),
                    deterministic.get("full_vector_raw", {}).get("coherence_mean"),
                ),
                "metric_validity": _condition_metric_validity(
                    deterministic_records.get("full_vector_glp"),
                    target_key="effect_abs_vs_unsteered",
                ),
            },
        },
        "methods": {
            method: _summarize_method(method_payload)
            for method, method_payload in sorted(methods.items())
        },
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
        "artifact_type": "week3_glp_sufficiency_sidecar_analysis",
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
    out_path = OUTPUT_DIR / f"week3_glp_sufficiency_sidecar_analysis_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(out_path), "inputs": report["inputs"]}, indent=2))


if __name__ == "__main__":
    main()
