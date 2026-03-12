"""Week 2 cross-trait bleed threshold sensitivity analysis."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"

DEFAULT_ARTIFACT_MAP = {
    "sycophancy_primary_prompt_last": "results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260227T191157Z.json",
    "evil_primary_prompt_last": "results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260227T171643Z.json",
    "sycophancy_rollout5_response_mean": "results/stage1_extraction/week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json",
    "evil_rollout5_response_mean": "results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260303T081318Z.json",
}
DEFAULT_THRESHOLDS = [0.2, 0.25, 0.3, 0.35, 0.4, 0.5]


def _parse_artifact_map(spec: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for chunk in [c.strip() for c in spec.split(",") if c.strip()]:
        if "=" not in chunk:
            raise ValueError(f"Invalid artifact map chunk: {chunk}")
        label, path = chunk.split("=", 1)
        out[label.strip()] = Path(path.strip())
    return out


def _parse_thresholds(spec: str) -> list[float]:
    vals = sorted({float(x.strip()) for x in spec.split(",") if x.strip()})
    if not vals:
        raise ValueError("No thresholds provided")
    if any(v < 0.0 for v in vals):
        raise ValueError("Thresholds must be non-negative")
    return vals


def _infer_trait_from_label_or_payload(label: str, payload: dict[str, Any]) -> str:
    trait = payload.get("trait")
    if isinstance(trait, str) and trait:
        return trait
    lowered = label.lower()
    for name in ("sycophancy", "evil", "hallucination"):
        if name in lowered:
            return name
    return "unknown"


def _entry_for_artifact(label: str, payload: dict[str, Any], thresholds: list[float]) -> dict[str, Any]:
    ratio = payload.get("cross_trait_bleed_gate", {}).get("off_target_to_target_ratio")
    if ratio is None:
        raise KeyError(f"Artifact {label} missing cross_trait_bleed_gate.off_target_to_target_ratio")

    ratio_f = float(ratio)
    selected = payload.get("selected", {})
    metric = payload.get("selected_test_evaluation", {}).get("metric", {})
    existing_threshold = payload.get("cross_trait_bleed_gate", {}).get("max_allowed_fraction")

    threshold_pass = {
        f"{thr:.2f}": bool(ratio_f <= float(thr))
        for thr in thresholds
    }
    min_passing_threshold = next((thr for thr in thresholds if ratio_f <= float(thr)), None)

    return {
        "label": label,
        "trait": _infer_trait_from_label_or_payload(label, payload),
        "selected": {
            "layer": selected.get("layer"),
            "alpha": selected.get("alpha"),
        },
        "bidirectional_effect": metric.get("bidirectional_effect"),
        "off_target_to_target_ratio": ratio_f,
        "artifact_threshold": existing_threshold,
        "artifact_cross_trait_bleed_pass": payload.get("quality_gates", {}).get("cross_trait_bleed_pass"),
        "threshold_pass": threshold_pass,
        "min_passing_threshold": min_passing_threshold,
    }


def _summary(entries: list[dict[str, Any]], thresholds: list[float]) -> dict[str, Any]:
    by_trait: dict[str, dict[str, Any]] = {}
    for entry in entries:
        trait = entry["trait"]
        trait_rows = by_trait.setdefault(trait, {"entries": []})["entries"]
        trait_rows.append(entry)

    trait_summary: dict[str, Any] = {}
    for trait, payload in by_trait.items():
        rows = payload["entries"]
        ratios = np.array([float(r["off_target_to_target_ratio"]) for r in rows], dtype=np.float64)
        trait_summary[trait] = {
            "n_lanes": int(len(rows)),
            "ratio_min": float(np.min(ratios)),
            "ratio_max": float(np.max(ratios)),
            "ratio_mean": float(np.mean(ratios)),
            "passes_by_threshold": {
                f"{thr:.2f}": int(sum(1 for r in rows if bool(r["threshold_pass"][f"{thr:.2f}"])))
                for thr in thresholds
            },
        }

    return {
        "n_entries": int(len(entries)),
        "thresholds": thresholds,
        "traits": trait_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-map",
        default=",".join(f"{k}={v}" for k, v in DEFAULT_ARTIFACT_MAP.items()),
        help="label=path CSV",
    )
    parser.add_argument(
        "--thresholds",
        default=",".join(str(x) for x in DEFAULT_THRESHOLDS),
        help="CSV float thresholds to evaluate",
    )
    args = parser.parse_args()

    artifact_map = _parse_artifact_map(args.artifact_map)
    thresholds = _parse_thresholds(args.thresholds)

    entries: list[dict[str, Any]] = []
    for label, path in artifact_map.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries.append(_entry_for_artifact(label, payload, thresholds))

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_cross_trait_bleed_sensitivity",
        "inputs": {
            "artifact_map": {k: str(v) for k, v in artifact_map.items()},
            "thresholds": thresholds,
        },
        "entries": entries,
        "summary": _summary(entries, thresholds),
        "evidence_status": {
            "entry_metrics": "known",
            "sensitivity_interpretation": "inferred",
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_cross_trait_bleed_sensitivity_{ts}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_path": str(out_path),
                "n_entries": len(entries),
                "thresholds": thresholds,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
