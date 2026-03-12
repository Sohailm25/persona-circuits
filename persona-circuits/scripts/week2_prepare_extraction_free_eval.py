"""Prepare extraction-free (few-shot) evaluation sets without explicit persona system prompts."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HELDOUT_DIR = ROOT / "prompts" / "heldout"
RESULTS_DIR = ROOT / "results" / "stage1_extraction"
EXEMPLAR_BANK_PATH = ROOT / "prompts" / "extraction_free_exemplar_bank.json"
DEFAULT_TRAITS = ["sycophancy", "evil", "hallucination"]

NEUTRAL_SYSTEM_PROMPT = (
    "You are a helpful, honest, and concise assistant. Answer directly and accurately."
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _hash_rows(rows: list[dict[str, Any]]) -> str:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=True) for r in rows)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _selection_hash(*, trait: str, source_row_id: int, seed: int, n_sets: int) -> str:
    key = f"{trait}:{source_row_id}:{seed}:{n_sets}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _select_set_index(*, trait: str, source_row_id: int, seed: int, n_sets: int) -> tuple[int, str]:
    if n_sets <= 0:
        raise ValueError("n_sets must be > 0")
    digest = _selection_hash(trait=trait, source_row_id=source_row_id, seed=seed, n_sets=n_sets)
    idx = int(digest[:16], 16) % n_sets
    return idx, digest


def _validate_example(example: Any) -> bool:
    if not isinstance(example, dict):
        return False
    user = str(example.get("user", "")).strip()
    assistant = str(example.get("assistant", "")).strip()
    return bool(user and assistant)


def _load_exemplar_bank(*, path: Path, min_examples_per_condition: int) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing exemplar bank: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    traits = payload.get("traits", {})
    if not isinstance(traits, dict):
        raise ValueError("Invalid exemplar bank: missing `traits` mapping.")

    bank: dict[str, list[dict[str, Any]]] = {}
    for trait, sets in traits.items():
        if not isinstance(sets, list) or not sets:
            raise ValueError(f"Invalid exemplar bank trait entry for {trait}: expected non-empty list.")

        normalized_sets: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for raw in sets:
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid exemplar set for trait={trait}: expected object.")

            set_id = str(raw.get("set_id", "")).strip()
            if not set_id:
                raise ValueError(f"Invalid exemplar set for trait={trait}: missing set_id.")
            if set_id in seen_ids:
                raise ValueError(f"Duplicate set_id for trait={trait}: {set_id}")
            seen_ids.add(set_id)

            high = raw.get("high", [])
            low = raw.get("low", [])
            if not isinstance(high, list) or not isinstance(low, list):
                raise ValueError(f"Invalid exemplar set for trait={trait}, set_id={set_id}: high/low must be lists.")
            if len(high) < min_examples_per_condition or len(low) < min_examples_per_condition:
                raise ValueError(
                    f"Exemplar set too small for trait={trait}, set_id={set_id}: "
                    f"high={len(high)}, low={len(low)}, min_required={min_examples_per_condition}"
                )
            if not all(_validate_example(x) for x in high):
                raise ValueError(f"Invalid high examples for trait={trait}, set_id={set_id}")
            if not all(_validate_example(x) for x in low):
                raise ValueError(f"Invalid low examples for trait={trait}, set_id={set_id}")

            normalized_sets.append(
                {
                    "set_id": set_id,
                    "high": [
                        {
                            "user": str(x["user"]).strip(),
                            "assistant": str(x["assistant"]).strip(),
                        }
                        for x in high
                    ],
                    "low": [
                        {
                            "user": str(x["user"]).strip(),
                            "assistant": str(x["assistant"]).strip(),
                        }
                        for x in low
                    ],
                }
            )

        bank[trait] = normalized_sets

    return bank


def _build_records(
    *,
    rows: list[dict[str, Any]],
    trait: str,
    n_eval: int,
    seed: int,
    exemplar_sets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rng = random.Random(seed + len(trait) * 101)
    idxs = list(range(len(rows)))
    rng.shuffle(idxs)
    selected = [rows[i] for i in idxs[: min(n_eval, len(rows))]]

    usage: dict[str, int] = {str(x["set_id"]): 0 for x in exemplar_sets}
    n_sets = len(exemplar_sets)

    out: list[dict[str, Any]] = []
    for i, row in enumerate(selected):
        source_row_id = int(row["id"])
        set_idx, digest = _select_set_index(
            trait=trait,
            source_row_id=source_row_id,
            seed=seed,
            n_sets=n_sets,
        )
        selected_set = exemplar_sets[set_idx]
        set_id = str(selected_set["set_id"])
        usage[set_id] = usage.get(set_id, 0) + 1

        rec = {
            "id": int(i),
            "source_row_id": source_row_id,
            "trait": trait,
            "category": row.get("category"),
            "user_query": row["user_query"],
            "ground_truth": row.get("ground_truth", "N/A"),
            "neutral_system_prompt": NEUTRAL_SYSTEM_PROMPT,
            "fewshot_set_id": set_id,
            "fewshot_set_index": int(set_idx),
            "fewshot_selection_hash": digest,
            "fewshot_high": selected_set["high"],
            "fewshot_low": selected_set["low"],
            "notes": {
                "purpose": "extraction_free_persona_probe",
                "explicit_persona_system_prompt_used": False,
                "selection_rule": "sha256(trait:source_row_id:seed:n_sets) % n_sets",
            },
        }
        out.append(rec)
    return out, usage


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traits", type=str, default=",".join(DEFAULT_TRAITS))
    parser.add_argument("--n-eval-per-trait", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--exemplar-bank-path", type=str, default=str(EXEMPLAR_BANK_PATH))
    parser.add_argument("--min-examples-per-condition", type=int, default=4)
    parser.add_argument(
        "--output-suffix",
        type=str,
        default="",
        help="Optional suffix appended to prompt filenames before .jsonl (e.g., v2 => trait_extraction_free_eval_v2.jsonl).",
    )
    args = parser.parse_args()

    traits = [t.strip() for t in args.traits.split(",") if t.strip()]
    for trait in traits:
        if trait not in DEFAULT_TRAITS:
            raise ValueError(f"Unsupported trait: {trait}")

    if args.n_eval_per_trait <= 0:
        raise ValueError("--n-eval-per-trait must be > 0")
    if args.min_examples_per_condition <= 0:
        raise ValueError("--min-examples-per-condition must be > 0")

    exemplar_bank = _load_exemplar_bank(
        path=Path(args.exemplar_bank_path),
        min_examples_per_condition=int(args.min_examples_per_condition),
    )

    manifest: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_eval_per_trait": int(args.n_eval_per_trait),
        "seed": int(args.seed),
        "exemplar_bank_path": str(Path(args.exemplar_bank_path)),
        "min_examples_per_condition": int(args.min_examples_per_condition),
        "output_suffix": str(args.output_suffix),
        "traits": {},
    }
    normalized_suffix = str(args.output_suffix).strip()
    if normalized_suffix and not normalized_suffix.startswith("_"):
        normalized_suffix = f"_{normalized_suffix}"

    for trait in traits:
        if trait not in exemplar_bank:
            raise KeyError(f"Trait={trait} missing in exemplar bank")

        in_path = HELDOUT_DIR / f"{trait}_heldout_pairs.jsonl"
        out_path = HELDOUT_DIR / f"{trait}_extraction_free_eval{normalized_suffix}.jsonl"
        rows = _load_jsonl(in_path)
        records, usage = _build_records(
            rows=rows,
            trait=trait,
            n_eval=args.n_eval_per_trait,
            seed=args.seed,
            exemplar_sets=exemplar_bank[trait],
        )
        _write_jsonl(out_path, records)

        set_ids = [str(x["set_id"]) for x in exemplar_bank[trait]]
        used_set_ids = sorted([k for k, v in usage.items() if v > 0])
        manifest["traits"][trait] = {
            "input_path": str(in_path),
            "output_path": str(out_path),
            "n_rows": len(records),
            "sha256": _hash_rows(records),
            "n_exemplar_sets_available": len(set_ids),
            "exemplar_set_ids_available": set_ids,
            "n_exemplar_sets_used": len(used_set_ids),
            "exemplar_set_ids_used": used_set_ids,
            "exemplar_set_usage_counts": usage,
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest_path = RESULTS_DIR / f"week2_extraction_free_prompt_manifest_{timestamp}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "manifest_path": str(manifest_path),
                "traits": traits,
                "n_eval_per_trait": int(args.n_eval_per_trait),
                "exemplar_bank_path": str(Path(args.exemplar_bank_path)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
