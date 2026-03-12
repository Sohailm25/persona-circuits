"""Compute overlap/distinctness diagnostics between a branch lane and a core trait vector."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"


def _load_vectors(path: Path) -> dict[str, dict[int, torch.Tensor]]:
    payload = torch.load(path, map_location="cpu")
    out: dict[str, dict[int, torch.Tensor]] = {}
    for trait, by_layer in payload.items():
        trait_key = str(trait)
        out[trait_key] = {}
        for layer, vec in by_layer.items():
            out[trait_key][int(layer)] = torch.as_tensor(vec, dtype=torch.float32)
    return out


def _cosine(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0).item())


def _same_layer_cosines(
    *,
    core_vectors: dict[int, torch.Tensor],
    branch_vectors: dict[int, torch.Tensor],
) -> dict[str, float]:
    common_layers = sorted(set(core_vectors).intersection(branch_vectors))
    return {str(layer): _cosine(core_vectors[layer], branch_vectors[layer]) for layer in common_layers}


def _cross_layer_cosines(
    *,
    core_vectors: dict[int, torch.Tensor],
    branch_vectors: dict[int, torch.Tensor],
) -> dict[str, dict[str, float]]:
    matrix: dict[str, dict[str, float]] = {}
    for core_layer in sorted(core_vectors):
        row: dict[str, float] = {}
        for branch_layer in sorted(branch_vectors):
            row[str(branch_layer)] = _cosine(core_vectors[core_layer], branch_vectors[branch_layer])
        matrix[str(core_layer)] = row
    return matrix


def _max_abs_entry(matrix: dict[str, dict[str, float]]) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for row_layer, row in matrix.items():
        for col_layer, value in row.items():
            candidate = {
                "core_layer": int(row_layer),
                "branch_layer": int(col_layer),
                "cosine": float(value),
                "abs_cosine": abs(float(value)),
            }
            if best is None or candidate["abs_cosine"] > best["abs_cosine"]:
                best = candidate
    if best is None:
        raise ValueError("Cross-layer matrix is empty.")
    return best


def _selected_pair(
    *,
    core_vectors: dict[int, torch.Tensor],
    branch_vectors: dict[int, torch.Tensor],
    core_layer: int,
    branch_layer: int,
) -> dict[str, Any]:
    if core_layer not in core_vectors:
        raise KeyError(f"Missing core selected layer: {core_layer}")
    if branch_layer not in branch_vectors:
        raise KeyError(f"Missing branch selected layer: {branch_layer}")
    cosine = _cosine(core_vectors[core_layer], branch_vectors[branch_layer])
    return {
        "core_layer": int(core_layer),
        "branch_layer": int(branch_layer),
        "cosine": float(cosine),
        "abs_cosine": abs(float(cosine)),
    }


def _branch_reference_overlap(
    *,
    branch_summary: dict[str, Any] | None,
    branch_trait: str,
    reference_trait: str | None,
) -> dict[str, Any] | None:
    if branch_summary is None or not reference_trait:
        return None
    matrices = branch_summary.get("cross_trait_vector_cosines_by_layer")
    if not isinstance(matrices, dict):
        return None
    values: dict[str, float] = {}
    for layer_key, matrix in matrices.items():
        try:
            value = float(matrix[branch_trait][reference_trait])
        except Exception:
            continue
        values[str(layer_key)] = value
    if not values:
        return None
    max_layer, max_value = max(values.items(), key=lambda kv: abs(kv[1]))
    return {
        "reference_trait": reference_trait,
        "same_layer_cosines_by_layer": values,
        "max_abs_same_layer_overlap": {
            "layer": int(max_layer),
            "cosine": float(max_value),
            "abs_cosine": abs(float(max_value)),
        },
    }


def _threshold_flags(
    *,
    same_layer: dict[str, float],
    cross_layer_max: dict[str, Any],
    selected_pair: dict[str, Any] | None,
    threshold: float,
) -> dict[str, Any]:
    same_layer_max_abs = max((abs(v) for v in same_layer.values()), default=0.0)
    return {
        "overlap_threshold": float(threshold),
        "same_layer_max_abs_exceeds_threshold": bool(same_layer_max_abs >= threshold),
        "cross_layer_max_abs_exceeds_threshold": bool(float(cross_layer_max["abs_cosine"]) >= threshold),
        "selected_pair_abs_exceeds_threshold": (
            bool(float(selected_pair["abs_cosine"]) >= threshold) if selected_pair is not None else None
        ),
    }


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-vectors-path", required=True)
    parser.add_argument("--branch-vectors-path", required=True)
    parser.add_argument("--core-trait", default="sycophancy")
    parser.add_argument("--branch-trait", default="politeness")
    parser.add_argument("--core-selected-layer", type=int, default=None)
    parser.add_argument("--branch-selected-layer", type=int, default=None)
    parser.add_argument("--branch-summary-path", default="")
    parser.add_argument("--branch-reference-trait", default="")
    parser.add_argument("--overlap-threshold", type=float, default=0.4)
    args = parser.parse_args()

    core_vectors_all = _load_vectors(Path(args.core_vectors_path))
    branch_vectors_all = _load_vectors(Path(args.branch_vectors_path))

    if args.core_trait not in core_vectors_all:
        raise KeyError(f"Core trait not found: {args.core_trait}")
    if args.branch_trait not in branch_vectors_all:
        raise KeyError(f"Branch trait not found: {args.branch_trait}")

    core_vectors = core_vectors_all[args.core_trait]
    branch_vectors = branch_vectors_all[args.branch_trait]
    same_layer = _same_layer_cosines(core_vectors=core_vectors, branch_vectors=branch_vectors)
    if not same_layer:
        raise ValueError("No common layers between core and branch vectors.")
    cross_layer = _cross_layer_cosines(core_vectors=core_vectors, branch_vectors=branch_vectors)
    cross_layer_max = _max_abs_entry(cross_layer)
    selected_pair = None
    if args.core_selected_layer is not None and args.branch_selected_layer is not None:
        selected_pair = _selected_pair(
            core_vectors=core_vectors,
            branch_vectors=branch_vectors,
            core_layer=int(args.core_selected_layer),
            branch_layer=int(args.branch_selected_layer),
        )

    branch_summary = _load_json(Path(args.branch_summary_path)) if args.branch_summary_path else None
    branch_reference = _branch_reference_overlap(
        branch_summary=branch_summary,
        branch_trait=args.branch_trait,
        reference_trait=args.branch_reference_trait.strip() or None,
    )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_overlap_diagnostic",
        "inputs": {
            "core_vectors_path": str(args.core_vectors_path),
            "branch_vectors_path": str(args.branch_vectors_path),
            "core_trait": str(args.core_trait),
            "branch_trait": str(args.branch_trait),
            "core_selected_layer": int(args.core_selected_layer) if args.core_selected_layer is not None else None,
            "branch_selected_layer": (
                int(args.branch_selected_layer) if args.branch_selected_layer is not None else None
            ),
            "branch_summary_path": str(args.branch_summary_path) if args.branch_summary_path else None,
            "branch_reference_trait": str(args.branch_reference_trait) if args.branch_reference_trait else None,
            "common_layers": sorted(int(x) for x in set(core_vectors).intersection(branch_vectors)),
        },
        "evidence_status": {
            "same_layer_cosines": "known",
            "cross_layer_cosines": "known",
            "selected_pair_cosine": "known" if selected_pair is not None else "unknown",
            "branch_reference_overlap": "known" if branch_reference is not None else "unknown",
        },
        "same_layer_cosines_by_layer": same_layer,
        "cross_layer_cosines": cross_layer,
        "max_abs_cross_layer_overlap": cross_layer_max,
        "selected_pair_overlap": selected_pair,
        "branch_reference_overlap": branch_reference,
        "threshold_flags": _threshold_flags(
            same_layer=same_layer,
            cross_layer_max=cross_layer_max,
            selected_pair=selected_pair,
            threshold=float(args.overlap_threshold),
        ),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"week2_trait_lane_overlap_diagnostic_{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
