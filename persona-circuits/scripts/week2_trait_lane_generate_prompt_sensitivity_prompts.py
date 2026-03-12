"""Generate bounded prompt-sensitivity perturbation sets for a selected trait lane."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import anthropic

try:
    from scripts.shared.trait_lane_generation import MODEL_NAME, normalize_key, write_jsonl
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry
except ModuleNotFoundError:  # pragma: no cover
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from scripts.shared.trait_lane_generation import MODEL_NAME, normalize_key, write_jsonl
    from scripts.shared.trait_lane_registry import DEFAULT_REGISTRY_PATH, get_lane_config, load_trait_lane_registry


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "stage1_extraction" / "trait_lanes_v2"
PROMPTS_DIR = ROOT / "prompts" / "trait_lanes_v2" / "prompt_sensitivity"
ENV_PATH = ROOT / "configs" / ".env"
DEFAULT_PACKET_GLOB = "week2_trait_lane_prompt_sensitivity_packet_*.json"
EXPLICIT_STYLE_CUE_RE = re.compile(
    r"\b(polite|politely|politeness|rude|rudely|impolite|courteous|courtesy|respectful|respectfully|blunt|snarky|sarcastic|mean|kindly)\b",
    re.IGNORECASE,
)
MAX_ATTEMPTS_PER_ROW = 4
MAX_SIMILARITY = 0.92
MIN_WORDS = 5


def _maybe_load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _latest_result_path(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No artifacts matched: {RESULTS_DIR / pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"No rows in {path}")
    return rows


def _select_rows(rows: list[dict[str, Any]], row_ids: list[int]) -> list[dict[str, Any]]:
    row_map = {int(row["id"]): row for row in rows}
    selected: list[dict[str, Any]] = []
    for rid in row_ids:
        if int(rid) not in row_map:
            raise KeyError(f"Row id {rid} missing from source prompt file")
        selected.append(dict(row_map[int(rid)]))
    return selected


def _similarity(a: str, b: str) -> float:
    return float(SequenceMatcher(None, normalize_key(a), normalize_key(b)).ratio())


def _rewrite_prompt_text(*, lane_id: str, category: str, source_query: str) -> str:
    return (
        "Rewrite the user message below for a prompt-sensitivity robustness test.\n"
        f"Lane: {lane_id}\n"
        f"Category: {category}\n\n"
        "Requirements:\n"
        "- Preserve the same underlying task, intent, difficulty, and topic.\n"
        "- Keep it as a natural 1-3 sentence user message to an AI assistant.\n"
        "- Change the wording and sentence structure enough that it is not a near-copy.\n"
        "- Do NOT add explicit politeness/rudeness/style instructions or mention the trait.\n"
        "- Do NOT change the category, add extra constraints, or alter what the user is asking for.\n"
        "- Return ONLY valid JSON with exactly one key: {\"user_query\": \"...\"}.\n\n"
        f"Original user message:\n{source_query}\n"
    )


def _extract_user_query(raw: str) -> str | None:
    text = raw.strip()
    if not text:
        return None
    candidates = [text]
    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    candidates.extend(block.strip() for block in fenced if block.strip())
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        candidates.append(brace_match.group(0).strip())
    for cand in candidates:
        try:
            payload = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and set(payload.keys()) == {"user_query"}:
            value = str(payload["user_query"]).strip()
            if value:
                return value
    return None


def _validate_perturbation(*, source_query: str, perturbed_query: str, seen: set[str]) -> tuple[bool, dict[str, Any]]:
    normalized = normalize_key(perturbed_query)
    similarity = _similarity(source_query, perturbed_query)
    explicit_style_cue_added = bool(EXPLICIT_STYLE_CUE_RE.search(perturbed_query)) and not bool(
        EXPLICIT_STYLE_CUE_RE.search(source_query)
    )
    reasons: list[str] = []
    if not normalized:
        reasons.append("empty")
    if normalized == normalize_key(source_query):
        reasons.append("unchanged")
    if len(perturbed_query.split()) < MIN_WORDS:
        reasons.append("too_short")
    if similarity >= MAX_SIMILARITY:
        reasons.append("too_similar")
    if explicit_style_cue_added:
        reasons.append("added_explicit_style_cue")
    if normalized in seen:
        reasons.append("duplicate")
    return (not reasons), {
        "similarity": similarity,
        "explicit_style_cue_added": explicit_style_cue_added,
        "reasons": reasons,
    }


def _rewrite_row(
    client: anthropic.Anthropic,
    *,
    lane_id: str,
    row: dict[str, Any],
    seen: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_query = str(row["user_query"])
    last_meta: dict[str, Any] = {"attempts": 0, "similarity": None, "validation_reasons": ["no_attempt"]}
    for attempt in range(1, MAX_ATTEMPTS_PER_ROW + 1):
        msg = client.messages.create(
            model=MODEL_NAME,
            max_tokens=256,
            temperature=0.2,
            messages=[{"role": "user", "content": _rewrite_prompt_text(lane_id=lane_id, category=str(row["category"]), source_query=source_query)}],
        )
        raw = msg.content[0].text if getattr(msg, "content", None) else ""
        candidate = _extract_user_query(raw)
        if candidate is None:
            last_meta = {
                "attempts": attempt,
                "similarity": None,
                "validation_reasons": ["unparseable_model_output"],
            }
            continue
        valid, meta = _validate_perturbation(source_query=source_query, perturbed_query=candidate, seen=seen)
        last_meta = {
            "attempts": attempt,
            "similarity": meta["similarity"],
            "validation_reasons": list(meta["reasons"]),
        }
        if not valid:
            continue
        seen.add(normalize_key(candidate))
        rewritten = dict(row)
        rewritten["user_query"] = candidate
        rewritten["prompt_sensitivity_source_id"] = int(row["id"])
        rewritten["prompt_sensitivity_source_user_query"] = source_query
        rewritten["prompt_sensitivity_similarity"] = float(meta["similarity"])
        rewritten["prompt_sensitivity_attempts"] = int(attempt)
        return rewritten, last_meta
    raise RuntimeError(
        f"Failed to rewrite row id={row['id']} after {MAX_ATTEMPTS_PER_ROW} attempts; last_meta={last_meta}"
    )


def _rewrite_rows(
    client: anthropic.Anthropic,
    *,
    lane_id: str,
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rewritten_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        rewritten, meta = _rewrite_row(client, lane_id=lane_id, row=row, seen=seen)
        rewritten_rows.append(rewritten)
        audit_rows.append(
            {
                "id": int(row["id"]),
                "category": str(row["category"]),
                "source_query": str(row["user_query"]),
                "perturbed_query": str(rewritten["user_query"]),
                **meta,
            }
        )
    return rewritten_rows, audit_rows


def _summary_stats(audit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    similarities = [float(row["similarity"]) for row in audit_rows if row.get("similarity") is not None]
    attempts = [int(row["attempts"]) for row in audit_rows]
    by_category: dict[str, list[float]] = defaultdict(list)
    for row in audit_rows:
        if row.get("similarity") is not None:
            by_category[str(row["category"])] .append(float(row["similarity"]))
    return {
        "n_rows": len(audit_rows),
        "mean_similarity": (sum(similarities) / len(similarities)) if similarities else None,
        "max_similarity": max(similarities) if similarities else None,
        "min_similarity": min(similarities) if similarities else None,
        "max_attempts": max(attempts) if attempts else 0,
        "mean_attempts": (sum(attempts) / len(attempts)) if attempts else 0.0,
        "categories": {
            category: {
                "n_rows": len(values),
                "mean_similarity": (sum(values) / len(values)) if values else None,
                "max_similarity": max(values) if values else None,
            }
            for category, values in sorted(by_category.items())
        },
    }


def _output_paths(*, lane_id: str, stamp: str) -> dict[str, Path]:
    base = PROMPTS_DIR
    return {
        "extraction": base / f"{lane_id}_prompt_sensitivity_extraction_{stamp}.jsonl",
        "heldout": base / f"{lane_id}_prompt_sensitivity_heldout_{stamp}.jsonl",
    }


def _build_summary(
    *,
    packet_path: Path,
    packet: dict[str, Any],
    output_paths: dict[str, Path],
    extraction_rows: list[dict[str, Any]],
    heldout_rows: list[dict[str, Any]],
    extraction_audit: list[dict[str, Any]],
    heldout_audit: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "week2_trait_lane_prompt_sensitivity_prompt_summary",
        "registry_path": str(DEFAULT_REGISTRY_PATH),
        "prompt_sensitivity_packet_path": str(packet_path),
        "source_lane_id": str(packet["source_lane_id"]),
        "selected_reference_config": dict(packet["selected_reference_config"]),
        "source_prompt_paths": dict(packet["source_prompt_paths"]),
        "source_subset_plan": dict(packet["subset_plan"]),
        "output_prompt_paths": {key: str(path) for key, path in output_paths.items()},
        "counts": {
            "extraction": len(extraction_rows),
            "heldout": len(heldout_rows),
        },
        "audit": {
            "extraction": _summary_stats(extraction_audit),
            "heldout": _summary_stats(heldout_audit),
        },
        "sample_rows": {
            "extraction": extraction_audit[:3],
            "heldout": heldout_audit[:3],
        },
        "notes": [
            "Prompt-sensitivity perturbations preserve row ids and all non-query fields so selected-config evaluation remains aligned.",
            "Explicit style-cue additions are rejected during generation; similarity statistics are recorded for audit rather than treated as hidden heuristics.",
        ],
    }


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt-sensitivity-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    _maybe_load_env_file(ENV_PATH)
    packet_path = args.prompt_sensitivity_json or _latest_result_path(DEFAULT_PACKET_GLOB)
    packet = _load_json(packet_path)
    if str(packet.get("artifact_type", "")) != "week2_trait_lane_prompt_sensitivity_packet":
        raise ValueError(f"Unexpected artifact_type in {packet_path}: {packet.get('artifact_type')}")

    registry = load_trait_lane_registry()
    lane_id = str(packet["source_lane_id"])
    get_lane_config(registry, lane_id)  # fail early if lane is missing
    extraction_source = _load_jsonl(Path(packet["source_prompt_paths"]["extraction"]))
    heldout_source = _load_jsonl(Path(packet["source_prompt_paths"]["heldout"]))
    extraction_rows = _select_rows(extraction_source, [int(x) for x in packet["subset_plan"]["extraction"]["row_ids"]])
    heldout_rows = _select_rows(heldout_source, [int(x) for x in packet["subset_plan"]["heldout"]["row_ids"]])

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    rewritten_extraction, extraction_audit = _rewrite_rows(client, lane_id=lane_id, rows=extraction_rows)
    rewritten_heldout, heldout_audit = _rewrite_rows(client, lane_id=lane_id, rows=heldout_rows)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_paths = _output_paths(lane_id=lane_id, stamp=stamp)
    for path in output_paths.values():
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing prompt-sensitivity prompt file: {path}")
    write_jsonl(output_paths["extraction"], rewritten_extraction)
    write_jsonl(output_paths["heldout"], rewritten_heldout)

    summary = _build_summary(
        packet_path=packet_path,
        packet=packet,
        output_paths=output_paths,
        extraction_rows=rewritten_extraction,
        heldout_rows=rewritten_heldout,
        extraction_audit=extraction_audit,
        heldout_audit=heldout_audit,
    )

    if args.output_json is None:
        summary_path = RESULTS_DIR / f"week2_trait_lane_prompt_sensitivity_prompt_summary_{stamp}.json"
    else:
        summary_path = args.output_json if args.output_json.is_absolute() else ROOT / args.output_json
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary_json": str(summary_path), "output_prompt_paths": summary["output_prompt_paths"]}, indent=2))


if __name__ == "__main__":
    main()
