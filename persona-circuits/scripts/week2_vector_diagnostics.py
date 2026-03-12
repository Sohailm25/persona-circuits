"""Week 2 vector diagnostics: cross-trait cosine structure + norm-aware margin backfill."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
DEFAULT_TRAITS = ["sycophancy", "evil", "hallucination"]


def _latest_result_path(glob_pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(glob_pattern))
    if not matches:
        raise FileNotFoundError(f"No files found for pattern: {glob_pattern}")
    return matches[-1]


def _load_vectors(path: Path) -> dict[str, dict[int, list[float]]]:
    payload = torch.load(path, map_location="cpu")
    vectors: dict[str, dict[int, list[float]]] = {}
    for trait, by_layer in payload.items():
        vectors[trait] = {}
        for layer, vec in by_layer.items():
            layer_int = int(layer)
            vectors[trait][layer_int] = vec.tolist() if hasattr(vec, "tolist") else list(vec)
    return vectors


def _load_summary(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_cross_trait_cosines(
    *,
    vectors: dict[str, dict[int, list[float]]],
    traits: list[str],
    layers: list[int],
) -> dict[str, dict[str, dict[str, float]]]:
    result: dict[str, dict[str, dict[str, float]]] = {}
    eps = 1e-8

    for layer in layers:
        layer_vectors: dict[str, np.ndarray] = {}
        missing = False
        for trait in traits:
            if trait not in vectors or layer not in vectors[trait]:
                missing = True
                break
            arr = np.asarray(vectors[trait][layer], dtype=np.float64)
            norm = float(np.linalg.norm(arr))
            if norm <= eps:
                raise ValueError(f"Zero-norm vector for trait={trait} layer={layer}")
            layer_vectors[trait] = arr / norm

        if missing:
            continue

        matrix: dict[str, dict[str, float]] = {}
        for trait_a in traits:
            row: dict[str, float] = {}
            for trait_b in traits:
                row[trait_b] = float(np.dot(layer_vectors[trait_a], layer_vectors[trait_b]))
            matrix[trait_a] = row
        result[str(layer)] = matrix

    return result


def _monotonic_non_decreasing(values: list[float]) -> bool:
    if len(values) <= 1:
        return True
    return all(values[i + 1] >= values[i] for i in range(len(values) - 1))


def _augment_summary_norm_diagnostics(summary: dict[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {}

    diagnostics = summary.get("diagnostics", {})
    out: dict[str, Any] = {}
    for trait, trait_payload in diagnostics.items():
        layers_payload = trait_payload.get("layers", {}) if isinstance(trait_payload, dict) else {}
        per_layer: dict[str, Any] = {}
        layer_keys_sorted = sorted(layers_payload.keys(), key=lambda x: int(x))

        raw_vector_norms: list[float] = []
        projection_margins: list[float] = []
        cosine_known_values: list[float] = []
        trait_cosine_data_present = False

        for layer_key in layer_keys_sorted:
            layer_entry = layers_payload[layer_key]
            if not isinstance(layer_entry, dict):
                continue
            raw_norm = float(layer_entry.get("raw_vector_norm", 0.0) or 0.0)
            proj_margin = float(layer_entry.get("projection_margin_mean", 0.0) or 0.0)
            cos_margin = layer_entry.get("cosine_margin_mean")

            raw_vector_norms.append(raw_norm)
            projection_margins.append(proj_margin)

            cosine_margin_evidence = "known" if cos_margin is not None else "unknown"
            if cos_margin is not None:
                cosine_known_values.append(float(cos_margin))
                trait_cosine_data_present = True

            per_layer[layer_key] = {
                "raw_vector_norm": raw_norm,
                "projection_margin_mean": proj_margin,
                "projection_margin_over_raw_vector_norm": (
                    float(proj_margin / (raw_norm + 1e-8)) if raw_norm > 0 else 0.0
                ),
                "cosine_margin_mean": float(cos_margin) if cos_margin is not None else None,
                "cosine_margin_evidence": cosine_margin_evidence,
            }

        out[trait] = {
            "layers": per_layer,
            "cosine_margin_data_present": trait_cosine_data_present,
            "trend_checks": {
                "raw_vector_norm_monotonic_non_decreasing": _monotonic_non_decreasing(raw_vector_norms),
                "projection_margin_monotonic_non_decreasing": _monotonic_non_decreasing(projection_margins),
                "cosine_margin_monotonic_non_decreasing": (
                    _monotonic_non_decreasing(cosine_known_values) if cosine_known_values else None
                ),
            },
        }
    return out


def _discover_common_layers(vectors: dict[str, dict[int, list[float]]], traits: list[str]) -> list[int]:
    layer_sets = [set(vectors[t].keys()) for t in traits if t in vectors]
    if not layer_sets:
        return []
    return sorted(set.intersection(*layer_sets))


def _risk_flags(
    cross_trait: dict[str, dict[str, dict[str, float]]],
    *,
    traits: list[str],
    cosine_abs_flag_threshold: float,
) -> dict[str, Any]:
    flagged_pairs: list[dict[str, Any]] = []
    for layer_key, matrix in cross_trait.items():
        for i, trait_a in enumerate(traits):
            for trait_b in traits[i + 1 :]:
                cosine = float(matrix[trait_a][trait_b])
                if abs(cosine) >= cosine_abs_flag_threshold:
                    flagged_pairs.append(
                        {
                            "layer": int(layer_key),
                            "trait_a": trait_a,
                            "trait_b": trait_b,
                            "cosine": cosine,
                            "abs_cosine": abs(cosine),
                            "threshold": cosine_abs_flag_threshold,
                        }
                    )
    return {
        "cosine_abs_flag_threshold": cosine_abs_flag_threshold,
        "high_alignment_pairs": flagged_pairs,
        "high_alignment_pair_count": len(flagged_pairs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vectors-path", type=str, default="")
    parser.add_argument("--summary-path", type=str, default="")
    parser.add_argument("--traits", type=str, default=",".join(DEFAULT_TRAITS))
    parser.add_argument("--cosine-abs-flag-threshold", type=float, default=0.6)
    args = parser.parse_args()

    vectors_path = Path(args.vectors_path) if args.vectors_path else _latest_result_path("week2_persona_vectors_*.pt")
    summary_path = (
        Path(args.summary_path)
        if args.summary_path
        else (_latest_result_path("week2_vector_extraction_summary_*.json") if not args.vectors_path else None)
    )

    vectors = _load_vectors(vectors_path)
    requested_traits = [t.strip() for t in args.traits.split(",") if t.strip()]
    traits = [t for t in requested_traits if t in vectors]
    if not traits:
        raise ValueError("No requested traits found in vectors artifact.")

    common_layers = _discover_common_layers(vectors, traits)
    if not common_layers:
        raise ValueError("No common layers across requested traits.")

    cross_trait = _compute_cross_trait_cosines(vectors=vectors, traits=traits, layers=common_layers)
    summary = _load_summary(summary_path)
    norm_diagnostics = _augment_summary_norm_diagnostics(summary)
    cosine_margin_data_known = any(
        trait_diag.get("cosine_margin_data_present") for trait_diag in norm_diagnostics.values()
    )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "vectors_path": str(vectors_path),
            "summary_path": str(summary_path) if summary_path is not None else None,
            "traits": traits,
            "layers": common_layers,
        },
        "evidence_status": {
            "cross_trait_vector_cosines_by_layer": "known",
            "norm_trend_diagnostics_from_summary": "known" if summary is not None else "unknown",
            "cosine_margin_from_summary": "known" if cosine_margin_data_known else "unknown",
        },
        "cross_trait_vector_cosines_by_layer": cross_trait,
        "norm_trend_diagnostics": norm_diagnostics,
        "risk_flags": _risk_flags(
            cross_trait,
            traits=traits,
            cosine_abs_flag_threshold=float(args.cosine_abs_flag_threshold),
        ),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_vector_diagnostics_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "vectors_path": str(vectors_path),
                "summary_path": str(summary_path) if summary_path is not None else None,
                "traits": traits,
                "layers": common_layers,
                "high_alignment_pair_count": report["risk_flags"]["high_alignment_pair_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
