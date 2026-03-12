"""Week 2 extraction multi-seed replication + stability summary."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import modal
import numpy as np

from week2_extract_persona_vectors import (  # noqa: E402
    RESULTS_DIR,
    _assert_prompt_audit_passed,
    _load_config,
    _load_prompt_pairs,
    _resolve_extraction_method,
    app as extract_app,
    extract_vectors_remote,
)

ROOT = Path(__file__).resolve().parents[1]
app = modal.App("persona-circuits-week2-extraction-seed-replication")


def _normalize_csv_ints(raw: str) -> list[int]:
    values = [int(x.strip()) for x in raw.split(",") if x.strip()]
    dedup: list[int] = []
    for v in values:
        if v not in dedup:
            dedup.append(v)
    return dedup


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def _pairwise_seed_cosines(
    vectors_by_seed: dict[int, dict[str, dict[str, list[float]]]],
    *,
    traits: list[str],
    layers: list[int],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    seed_list = sorted(vectors_by_seed.keys())
    for trait in traits:
        out[trait] = {"layers": {}}
        for layer in layers:
            key = str(layer)
            row_pairs: list[dict[str, Any]] = []
            cosines: list[float] = []
            for s1, s2 in combinations(seed_list, 2):
                v1 = np.array(vectors_by_seed[s1][trait][key], dtype=np.float32)
                v2 = np.array(vectors_by_seed[s2][trait][key], dtype=np.float32)
                cos = _cosine(v1, v2)
                cosines.append(cos)
                row_pairs.append({"seed_a": s1, "seed_b": s2, "cosine": cos})

            if cosines:
                out[trait]["layers"][key] = {
                    "n_pairs": len(cosines),
                    "pairwise_cosines": row_pairs,
                    "min_pairwise_cosine": float(min(cosines)),
                    "mean_pairwise_cosine": float(np.mean(cosines)),
                    "std_pairwise_cosine": float(np.std(cosines)),
                }
            else:
                out[trait]["layers"][key] = {
                    "n_pairs": 0,
                    "pairwise_cosines": [],
                    "min_pairwise_cosine": None,
                    "mean_pairwise_cosine": None,
                    "std_pairwise_cosine": None,
                }
    return out


@app.local_entrypoint()
def main(
    traits: str = "sycophancy,evil",
    layers: str = "12",
    seeds: str = "",
    extraction_method: str = "",
    response_max_new_tokens: int = 96,
    response_temperature: float = 0.0,
    min_pairwise_cosine_threshold: float = 0.7,
) -> None:
    selected_traits = [x.strip() for x in traits.split(",") if x.strip()]
    selected_layers = _normalize_csv_ints(layers)
    if not selected_traits:
        raise ValueError("No traits selected")
    if not selected_layers:
        raise ValueError("No layers selected")

    config = _load_config()
    if seeds.strip():
        selected_seeds = _normalize_csv_ints(seeds)
    else:
        selected_seeds = [
            int(config["seeds"]["primary"]),
            *[int(x) for x in config["seeds"].get("replication", [])],
        ]
        dedup: list[int] = []
        for seed in selected_seeds:
            if seed not in dedup:
                dedup.append(seed)
        selected_seeds = dedup

    _assert_prompt_audit_passed()
    prompt_pairs = _load_prompt_pairs(selected_traits)
    resolved_extraction_method = _resolve_extraction_method(config, extraction_method)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    vectors_by_seed: dict[int, dict[str, dict[str, list[float]]]] = {}
    per_seed_artifacts: dict[str, Any] = {}
    with extract_app.run():
        for seed in selected_seeds:
            seed_cfg = deepcopy(config)
            seed_cfg["seeds"]["primary"] = int(seed)
            run_name = f"week2-seed-repl-{resolved_extraction_method}-s{seed}-{run_timestamp}"
            result = extract_vectors_remote.remote(
                config=seed_cfg,
                prompt_pairs=prompt_pairs,
                traits=selected_traits,
                layers=selected_layers,
                extraction_method=resolved_extraction_method,
                response_max_new_tokens=int(response_max_new_tokens),
                response_temperature=float(response_temperature),
                run_name=run_name,
            )

            vectors_by_seed[int(seed)] = result["vectors"]

            seed_summary_path = RESULTS_DIR / f"week2_vector_extraction_summary_seed{seed}_{run_timestamp}.json"
            seed_vectors_path = RESULTS_DIR / f"week2_persona_vectors_seed{seed}_{run_timestamp}.pt"
            seed_summary_path.write_text(json.dumps(result["summary"], indent=2), encoding="utf-8")

            import torch

            torch.save(
                {
                    trait: {
                        int(layer): torch.tensor(vec, dtype=torch.float32)
                        for layer, vec in by_layer.items()
                    }
                    for trait, by_layer in result["vectors"].items()
                },
                seed_vectors_path,
            )

            per_seed_artifacts[str(seed)] = {
                "summary_path": str(seed_summary_path),
                "vectors_path": str(seed_vectors_path),
                "modal_artifacts": result["modal_artifacts"],
            }

    pairwise = _pairwise_seed_cosines(
        vectors_by_seed=vectors_by_seed,
        traits=selected_traits,
        layers=selected_layers,
    )

    trait_gate: dict[str, bool] = {}
    for trait in selected_traits:
        passed = True
        for layer in selected_layers:
            layer_payload = pairwise[trait]["layers"][str(layer)]
            min_cos = layer_payload["min_pairwise_cosine"]
            if min_cos is None or float(min_cos) < float(min_pairwise_cosine_threshold):
                passed = False
        trait_gate[trait] = passed

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_extraction_seed_replication",
        "traits": selected_traits,
        "layers": selected_layers,
        "seed_schedule": selected_seeds,
        "extraction_method": resolved_extraction_method,
        "response_max_new_tokens": int(response_max_new_tokens),
        "response_temperature": float(response_temperature),
        "per_seed_artifacts": per_seed_artifacts,
        "pairwise_seed_cosines": pairwise,
        "quality_gates": {
            "min_pairwise_cosine_threshold": float(min_pairwise_cosine_threshold),
            "trait_pass": trait_gate,
            "overall_pass": bool(all(trait_gate.values())),
        },
        "evidence_status": {
            "per_seed_extractions": "known",
            "pairwise_stability": "inferred",
        },
    }

    out_path = RESULTS_DIR / f"week2_extraction_seed_replication_{run_timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(out_path),
                "seed_schedule": selected_seeds,
                "traits": selected_traits,
                "layers": selected_layers,
                "quality_gates": report["quality_gates"],
            },
            indent=2,
        )
    )
