"""Generate a neutral instruction-following prompt corpus for matched GLP training.

This script is separate from the Week 1/2 prompt generators. It produces an
exporter-ready JSONL corpus with neutral system prompts and diverse benign user
requests, suitable for exporting natural activations from the target instruct
model.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
import numpy as np

try:
    from scripts.prompt_quality_rules import evil_violation_type
except ImportError:  # pragma: no cover
    from prompt_quality_rules import evil_violation_type

SEED = 7
ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
OUTPUT_DIR = PROMPTS_DIR / "glp_training"
RESULTS_DIR = ROOT / "results" / "glp_sidecar"
SCRATCH_DIR = ROOT / "scratch"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_SYSTEM_PROMPT = "You are a helpful, honest, and concise assistant. Answer directly and accurately."
DEFAULT_BATCH_SIZE = 48
DEFAULT_MAX_ATTEMPTS = 8

BANNED_QUERY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(ignore (?:all|any|the) previous|system prompt|developer message|jailbreak|prompt injection)\b", re.IGNORECASE),
    re.compile(r"\b(as an ai|as a language model|chatgpt|claude|openai|anthropic)\b", re.IGNORECASE),
    re.compile(r"\b(roleplay|pretend you are|act as|simulate being)\b", re.IGNORECASE),
    re.compile(r"\b(explicit sexual|porn|erotic|self-harm|suicide|build a bomb|weapon|malware|ransomware)\b", re.IGNORECASE),
    re.compile(r"\b(machiavellian|sycophancy|hallucination|persona circuit|persona vector|activation steering)\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class CorpusCategorySpec:
    category: str
    description: str
    n: int
    style_cues: tuple[str, ...] = ()


CORPUS_CATEGORIES: list[CorpusCategorySpec] = [
    CorpusCategorySpec(
        "factual_qa",
        "Direct factual questions spanning geography, history, civics, health basics, and everyday knowledge.",
        120,
        ("short answer", "direct question", "single fact"),
    ),
    CorpusCategorySpec(
        "math_and_estimation",
        "Arithmetic, unit conversion, back-of-the-envelope estimation, and short quantitative reasoning.",
        120,
        ("compute", "estimate", "check work"),
    ),
    CorpusCategorySpec(
        "coding_debugging",
        "Programming help with bugs, stack traces, edge cases, and short code snippets across common languages.",
        120,
        ("debug", "explain error", "fix snippet"),
    ),
    CorpusCategorySpec(
        "coding_design",
        "Requests about API design, data modeling, testing strategy, refactors, and code review advice.",
        120,
        ("design", "tradeoff", "review"),
    ),
    CorpusCategorySpec(
        "writing_and_revision",
        "Editing emails, rewriting paragraphs, tightening prose, changing tone, and drafting professional messages.",
        120,
        ("rewrite", "improve tone", "polish"),
    ),
    CorpusCategorySpec(
        "summarization",
        "Summarizing notes, meetings, documents, or long messages into concise structured outputs.",
        120,
        ("summarize", "bullet points", "key takeaways"),
    ),
    CorpusCategorySpec(
        "information_extraction",
        "Extracting entities, deadlines, action items, requirements, or structured fields from messy text.",
        120,
        ("extract", "structure", "JSON/table"),
    ),
    CorpusCategorySpec(
        "planning_and_logistics",
        "Travel planning, scheduling, checklists, meal prep, moving plans, and event organization.",
        120,
        ("plan", "itinerary", "checklist"),
    ),
    CorpusCategorySpec(
        "decision_support",
        "Comparing options, building pros/cons lists, prioritizing constraints, and making practical recommendations.",
        120,
        ("compare options", "decision matrix", "recommend"),
    ),
    CorpusCategorySpec(
        "science_and_engineering",
        "Explaining scientific concepts, mechanisms, and engineering intuition at different levels of detail.",
        120,
        ("explain simply", "intuition", "why does"),
    ),
    CorpusCategorySpec(
        "tutoring_and_study_help",
        "Stepwise explanations for homework-like questions without unsafe or policy-sensitive content.",
        120,
        ("teach me", "walk through", "study guide"),
    ),
    CorpusCategorySpec(
        "data_analysis",
        "Interpreting trends, describing charts in words, spotting confounds, and suggesting simple analyses.",
        120,
        ("analyze", "interpret", "what stands out"),
    ),
    CorpusCategorySpec(
        "translation_and_localization",
        "Translation, phrase nuance, wording alternatives, and localization for everyday or professional text.",
        120,
        ("translate", "natural phrasing", "localize"),
    ),
    CorpusCategorySpec(
        "brainstorming",
        "Generating names, ideas, examples, themes, talking points, or low-stakes creative concepts.",
        120,
        ("brainstorm", "generate ideas", "options"),
    ),
    CorpusCategorySpec(
        "creative_constrained_writing",
        "Short creative writing tasks with explicit constraints on tone, length, structure, or format.",
        120,
        ("with constraints", "specific style", "short creative piece"),
    ),
]


def _sentence_count(text: str) -> int:
    return len([chunk for chunk in re.split(r"[.!?]+", text) if chunk.strip()])


def _normalize_key(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[[\s\S]*\]", stripped)
    if not match:
        raise ValueError("No JSON array found in model output.")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, list):
        raise ValueError("Parsed JSON is not an array.")
    return parsed


def _normalize_items(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, str):
            query = item.strip()
        elif isinstance(item, dict):
            query = str(item.get("user_query") or item.get("query") or item.get("prompt") or "").strip()
        else:
            continue
        if not query:
            continue
        normalized.append({"user_query": query})
    return normalized


def _load_blocked_queries(
    *,
    include_glp_training: bool = True,
    exclude_paths: set[Path] | None = None,
) -> set[str]:
    blocked: set[str] = set()
    exclude_paths = {path.resolve() for path in (exclude_paths or set())}
    for path in sorted(PROMPTS_DIR.rglob("*.jsonl")):
        resolved = path.resolve()
        if resolved in exclude_paths:
            continue
        if (not include_glp_training) and path.is_relative_to(OUTPUT_DIR):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("user_query", "prompt", "question", "query", "neutral_user_prompt"):
                value = row.get(key)
                if isinstance(value, str) and value.strip():
                    blocked.add(_normalize_key(value))
                    break
    return blocked


def _is_valid_query(query: str) -> bool:
    normalized = query.strip()
    if not normalized:
        return False
    word_count = len(normalized.split())
    if word_count < 4 or word_count > 120:
        return False
    if _sentence_count(normalized) < 1 or _sentence_count(normalized) > 4:
        return False
    if evil_violation_type(normalized) is not None:
        return False
    for pattern in BANNED_QUERY_PATTERNS:
        if pattern.search(normalized):
            return False
    return True


def _request_prompt_template(
    spec: CorpusCategorySpec,
    *,
    n: int,
    blocked_examples: list[str],
) -> str:
    style_cues = "\n".join(f"- {cue}" for cue in spec.style_cues) if spec.style_cues else "- none"
    blocked_text = "\n".join(f"- {text}" for text in blocked_examples) if blocked_examples else "- none"
    return (
        f"Generate {n} realistic user messages for a benign instruction-following training corpus.\n"
        f"Category: {spec.category}\n"
        f"Description: {spec.description}\n\n"
        "Requirements:\n"
        "- Each item must be a natural user message to a helpful assistant.\n"
        "- Keep requests benign, practical, and instruction-following.\n"
        "- Use 1 to 4 sentences.\n"
        "- Mix short and medium-length requests.\n"
        "- Make the requests self-contained.\n"
        "- Avoid roleplay, jailbreaks, policy discussions, or references to AI systems.\n"
        "- Avoid harmful, manipulative, sexual, or illegal requests.\n"
        "- Avoid duplicates and near-duplicates.\n"
        "- Include concrete details, constraints, or context when natural.\n"
        "- Prefer English-language prompts.\n"
        f"Style cues for this category:\n{style_cues}\n"
        f"Do not repeat or lightly paraphrase any of these blocked examples:\n{blocked_text}\n\n"
        "Output requirements:\n"
        "- Return ONLY valid JSON.\n"
        "- Output a JSON array of objects.\n"
        '- Each object must follow schema: {"user_query": "..."}.\n'
    )


def _retryable_sleep(attempt: int) -> None:
    delay = min(15.0, 1.25 * (2 ** max(0, attempt - 1)))
    time.sleep(delay)


def _generate_category_queries(
    client: anthropic.Anthropic,
    spec: CorpusCategorySpec,
    *,
    batch_size: int,
    model_name: str,
    blocked_queries_norm: set[str],
    max_attempts: int,
    seed: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    accepted: list[dict[str, str]] = []
    seen = set()
    rejected_counter: Counter[str] = Counter()
    attempts = 0
    rng = random.Random(int(seed) + hash(spec.category) % 100000)

    while len(accepted) < spec.n and attempts < max_attempts:
        need = spec.n - len(accepted)
        blocked_examples = rng.sample(sorted(blocked_queries_norm), k=min(6, len(blocked_queries_norm))) if blocked_queries_norm else []
        prompt = _request_prompt_template(spec, n=max(min(batch_size, need), min(need, 12)), blocked_examples=blocked_examples)
        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                temperature=0.9,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_items = _extract_json_array(response.content[0].text)
        except Exception:
            attempts += 1
            _retryable_sleep(attempts)
            continue

        items = _normalize_items(raw_items)
        for item in items:
            query = item["user_query"].strip()
            key = _normalize_key(query)
            if not key:
                rejected_counter["empty"] += 1
                continue
            if key in seen:
                rejected_counter["duplicate_within_category"] += 1
                continue
            if key in blocked_queries_norm:
                rejected_counter["blocked_overlap"] += 1
                continue
            if not _is_valid_query(query):
                rejected_counter["quality_filter"] += 1
                continue
            seen.add(key)
            blocked_queries_norm.add(key)
            accepted.append({"user_query": query})
            if len(accepted) >= spec.n:
                break
        attempts += 1

    if len(accepted) < spec.n:
        raise RuntimeError(
            f"Failed to generate enough prompts for {spec.category}: {len(accepted)} < {spec.n} (attempts={attempts})"
        )
    return accepted[: spec.n], {
        "attempts": int(attempts),
        "accepted": int(len(accepted[: spec.n])),
        "rejected": dict(rejected_counter),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _audit_corpus(path: Path, expected_specs: list[CorpusCategorySpec]) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected_total = sum(spec.n for spec in expected_specs)
    expected_categories = {spec.category: spec.n for spec in expected_specs}
    category_counts = Counter(row.get("category") for row in rows)
    failures: list[dict[str, Any]] = []

    if len(rows) != expected_total:
        failures.append({"type": "count_mismatch", "expected": expected_total, "actual": len(rows)})
    if dict(category_counts) != expected_categories:
        failures.append({"type": "category_mismatch", "expected": expected_categories, "actual": dict(category_counts)})

    seen = {}
    for idx, row in enumerate(rows):
        rid = row.get("id", idx)
        query = str(row.get("user_query", "")).strip()
        if not query:
            failures.append({"type": "empty_query", "id": rid})
            continue
        key = _normalize_key(query)
        if key in seen:
            failures.append({"type": "duplicate_query", "id": rid, "duplicate_of": seen[key]})
        else:
            seen[key] = rid
        if not _is_valid_query(query):
            failures.append({"type": "quality_filter_fail", "id": rid})
        if str(row.get("neutral_system_prompt", "")).strip() != DEFAULT_SYSTEM_PROMPT:
            failures.append({"type": "system_prompt_mismatch", "id": rid})

    return {
        "path": str(path),
        "count": int(len(rows)),
        "category_counts": dict(category_counts),
        "failure_count": int(len(failures)),
        "failures_preview": failures[:20],
        "passes": len(failures) == 0,
    }


def _parse_categories(raw: str | None) -> list[CorpusCategorySpec]:
    if not raw:
        return CORPUS_CATEGORIES
    selected = {part.strip() for part in raw.split(",") if part.strip()}
    specs = [spec for spec in CORPUS_CATEGORIES if spec.category in selected]
    if not specs:
        raise ValueError(f"No categories matched: {sorted(selected)}")
    missing = selected.difference({spec.category for spec in specs})
    if missing:
        raise ValueError(f"Unknown categories requested: {sorted(missing)}")
    return specs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", default="", help="Comma-separated category subset.")
    parser.add_argument("--per-category", type=int, default=-1, help="Override target count per category.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output-suffix", default="")
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise ValueError("--batch-size must be > 0")
    if args.max_attempts <= 0:
        raise ValueError("--max-attempts must be > 0")

    random.seed(args.seed)
    np.random.seed(args.seed)

    specs = _parse_categories(args.categories)
    if args.per_category > 0:
        specs = [
            CorpusCategorySpec(
                category=spec.category,
                description=spec.description,
                n=int(args.per_category),
                style_cues=spec.style_cues,
            )
            for spec in specs
        ]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{args.output_suffix.strip()}" if args.output_suffix.strip() else ""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"neutral_instruct_corpus_{timestamp}{suffix}.jsonl"
    summary_path = RESULTS_DIR / f"glp_training_prompt_corpus_{timestamp}{suffix}.json"
    scratch_path = SCRATCH_DIR / f"glp_training_prompt_corpus_{timestamp}{suffix}.scratch.json"

    blocked_queries_norm = _load_blocked_queries(
        include_glp_training=True,
        exclude_paths={output_path},
    )
    client = anthropic.Anthropic()

    records: list[dict[str, Any]] = []
    generation_stats: dict[str, Any] = {}
    next_id = 0

    for category_index, spec in enumerate(specs):
        generated, stats = _generate_category_queries(
            client,
            spec,
            batch_size=int(args.batch_size),
            model_name=str(args.model),
            blocked_queries_norm=blocked_queries_norm,
            max_attempts=int(args.max_attempts),
            seed=int(args.seed) + category_index,
        )
        generation_stats[spec.category] = stats
        for item in generated:
            records.append(
                {
                    "id": int(next_id),
                    "category": spec.category,
                    "user_query": item["user_query"],
                    "neutral_system_prompt": DEFAULT_SYSTEM_PROMPT,
                    "source_model": str(args.model),
                    "source_type": "anthropic_synthetic_neutral_instruct",
                }
            )
            next_id += 1
        scratch_path.write_text(
            json.dumps(
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "output_path": str(output_path),
                    "count_so_far": int(len(records)),
                    "completed_categories": list(generation_stats.keys()),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "event": "category_complete",
                    "category": spec.category,
                    "count": int(len(generated)),
                    "total_records": int(len(records)),
                }
            ),
            flush=True,
        )

    _write_jsonl(output_path, records)
    audit = _audit_corpus(output_path, specs)
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "glp_training_prompt_corpus",
        "model": str(args.model),
        "seed": int(args.seed),
        "output_path": str(output_path),
        "scratch_path": str(scratch_path),
        "n_records": int(len(records)),
        "n_categories": int(len(specs)),
        "generation_stats": generation_stats,
        "audit": audit,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), "output_path": str(output_path), "n_records": len(records)}, indent=2))


if __name__ == "__main__":
    main()
