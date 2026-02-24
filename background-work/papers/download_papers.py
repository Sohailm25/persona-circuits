#!/usr/bin/env python3
# ABOUTME: Downloads all persona-circuits reference papers from arXiv HTML and web sources.
# ABOUTME: Validates each paper (title, authors, abstract, completeness) before saving.

import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
except ImportError:
    print("ERROR: Run: pip install beautifulsoup4 markdownify")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent
HEADERS = {"User-Agent": "Mozilla/5.0 (research download; persona-circuits experiment)"}

# Papers we can download: (filename, url, expected_title_fragment, expected_author_fragment, tier, notes)
PAPERS = [
    # === TIER 1 — Essential ===
    (
        "marks2026_persona_selection_model.md",
        "https://alignment.anthropic.com/2026/psm/",
        "persona selection",
        "marks",
        1,
        "PSM — the theory being tested",
    ),
    (
        "chen2025_persona_vectors.md",
        "https://arxiv.org/html/2507.21509",
        "persona vectors",
        "chen",
        1,
        "Persona vector extraction methodology",
    ),
    (
        "lindsey2025_circuit_tracing.md",
        "https://transformer-circuits.pub/2025/attribution-graphs/index.html",
        "circuit",
        "lindsey",
        1,
        "Circuit tracing / attribution graphs",
    ),
    # === TIER 2 — SAE Infrastructure ===
    (
        "lieberum2024_gemma_scope.md",
        "https://arxiv.org/html/2408.05147",
        "gemma scope",
        "lieberum",
        2,
        "GemmaScope SAEs",
    ),
    (
        "he2024_llama_scope.md",
        "https://arxiv.org/html/2410.20526",
        "llamascope",
        "he",
        2,
        "LlamaScope SAEs — primary SAEs for Llama 3.1 8B",
    ),
    (
        "bricken2023_monosemanticity.md",
        "https://transformer-circuits.pub/2023/monosemantic-features/index.html",
        "monosemantic",
        "bricken",
        2,
        "Foundational SAE paper",
    ),
    # === TIER 2 — Steering Methodology ===
    (
        "zou2023_representation_engineering.md",
        "https://arxiv.org/html/2310.01405",
        "representation engineering",
        "zou",
        2,
        "RepE — foundational steering method",
    ),
    (
        "rimsky2024_contrastive_activation_addition.md",
        "https://arxiv.org/html/2312.06681",
        "contrastive activation",
        "rimsky",
        2,
        "CAA — direct precursor to Persona Vectors",
    ),
    (
        "turner2024_activation_addition.md",
        "https://arxiv.org/html/2308.10248",
        "activation addition",
        "turner",
        2,
        "ActAdd — steering without optimization",
    ),
    # === TIER 2 — Circuit Analysis ===
    (
        "conmy2023_acdc.md",
        "https://arxiv.org/html/2304.14997",
        "circuit discovery",
        "conmy",
        2,
        "ACDC — automated circuit discovery",
    ),
    (
        "wang2022_ioi_circuit.md",
        "https://arxiv.org/html/2211.00593",
        "indirect object",
        "wang",
        2,
        "IOI circuit — faithfulness standard (>=80%)",
    ),
    # === TIER 2 — Behavioral Evaluation ===
    (
        "wang2025_emergent_misalignment.md",
        "https://arxiv.org/html/2502.17424",
        "misalignment",
        "wang",
        2,
        "Emergent misalignment — SAE decomposition of persona features",
    ),
    # === TIER 3 — Theory ===
    (
        "elhage2022_toy_models_superposition.md",
        "https://transformer-circuits.pub/2022/toy_model/index.html",
        "superposition",
        "elhage",
        3,
        "Superposition hypothesis — why SAE features exist",
    ),
    (
        "yang2024_sae_vs_repe_timescales.md",
        "https://arxiv.org/html/2410.10863",
        "personality traits",
        "yang",
        3,
        "SAE vs RepE timescale distinction",
    ),
    (
        "bhandari2026_trait_interference.md",
        "https://arxiv.org/html/2602.15847",
        "personality traits",
        "bhandari",
        3,
        "Geometric constraints on multi-trait steering",
    ),
    (
        "park2024_linear_representation_hypothesis.md",
        "https://arxiv.org/html/2311.03658",
        "linear representation",
        "park",
        3,
        "Linear representation hypothesis",
    ),
    # === TIER 4 — Surveys ===
    (
        "tseng2024_two_tales_persona.md",
        "https://aclanthology.org/2024.findings-emnlp.969/",
        "persona",
        "tseng",
        4,
        "Two Tales of Persona survey",
    ),
    (
        "survey2024_personality_persona_profile.md",
        "https://arxiv.org/html/2401.00609",
        "persona",
        "survey",
        4,
        "Personality/Persona/Profile in conversational agents survey",
    ),
    (
        "scope2025_socially_grounded_persona.md",
        "https://arxiv.org/html/2601.07110",
        "persona",
        "scope",
        4,
        "SCOPE framework",
    ),
    (
        "vaswani2017_attention_is_all_you_need.md",
        "https://arxiv.org/html/1706.03762",
        "attention",
        "vaswani",
        4,
        "Transformer foundation — only cite if needed",
    ),
]

# Papers we CANNOT download (no confirmed URL or paywalled)
SKIPPED = [
    ("marks2026_psm", "PSM — URL confirmed but may require auth: alignment.anthropic.com/2026/psm/"),
    ("greenblatt2024_alignment_faking", "URL unverified: likely arXiv:2412.14093"),
    ("li2024_ablation_validity", "NeurIPS 2024 — no confirmed arXiv ID; search NeurIPS 2024 proceedings"),
    ("macdiarmd2025_poser", "arXiv ID unknown"),
    ("bailey2026_obfuscated_activations", "ICLR 2026 — arXiv ID unknown"),
    ("kantamneni2025_sae_safety", "ICML 2025 — arXiv ID unknown"),
    ("campbell2024_lying_circuits", "arXiv ID unknown"),
    ("venkatesh2026_identifiability", "arXiv ID unknown"),
    ("lu2026_assistant_axis", "arXiv ID unknown"),
    ("salminen2021_persona_survey", "DOI only — likely behind paywall"),
]


def fetch_url(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            encoding = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(encoding, errors="replace")
    except urllib.error.HTTPError as e:
        return None
    except Exception as e:
        return None


def clean_arxiv_html(html: str, expected_title: str, expected_author: str) -> tuple[str | None, list[str]]:
    """Extract main content from arXiv HTML page. Returns (markdown, warnings)."""
    warnings = []
    soup = BeautifulSoup(html, "html.parser")

    # Try to find main article content
    article = (
        soup.find("article")
        or soup.find("div", class_="ltx_document")
        or soup.find("div", id="content")
        or soup.find("main")
        or soup.body
    )
    if not article:
        return None, ["Could not find article body"]

    # Remove nav, footer, script, style, header noise
    for tag in article.find_all(["nav", "footer", "script", "style", "header", "aside"]):
        tag.decompose()

    full_text = article.get_text(separator=" ", strip=True).lower()

    # Validate title
    if expected_title.lower() not in full_text:
        warnings.append(f"WARNING: Expected title fragment '{expected_title}' NOT found in page text")

    # Validate author
    if expected_author.lower() not in full_text:
        warnings.append(f"WARNING: Expected author '{expected_author}' NOT found in page text")

    # Validate completeness: should have an abstract and some kind of conclusion or references
    has_abstract = "abstract" in full_text
    has_end = any(w in full_text for w in ["conclusion", "references", "acknowledgment", "discussion"])
    if not has_abstract:
        warnings.append("WARNING: No 'abstract' found — page may be incomplete or wrong paper")
    if not has_end:
        warnings.append("WARNING: No conclusion/references section found — paper may be truncated")

    # Convert to markdown
    content_md = md(str(article), heading_style="ATX", strip=["script", "style"])

    # Trim excessive blank lines
    content_md = re.sub(r"\n{4,}", "\n\n\n", content_md)

    return content_md, warnings


def download_paper(filename: str, url: str, expected_title: str, expected_author: str, tier: int, notes: str) -> dict:
    result = {
        "filename": filename,
        "url": url,
        "tier": tier,
        "notes": notes,
        "status": None,
        "warnings": [],
        "char_count": 0,
    }

    print(f"\n{'='*60}")
    print(f"Fetching: {filename}")
    print(f"URL: {url}")

    html = fetch_url(url)
    if html is None:
        result["status"] = "FETCH_FAILED"
        print(f"  ✗ FETCH FAILED")
        return result

    print(f"  Downloaded {len(html):,} bytes of HTML")

    content_md, warnings = clean_arxiv_html(html, expected_title, expected_author)
    if content_md is None:
        result["status"] = "PARSE_FAILED"
        result["warnings"] = warnings
        print(f"  ✗ PARSE FAILED: {warnings}")
        return result

    result["warnings"] = warnings
    result["char_count"] = len(content_md)

    if warnings:
        for w in warnings:
            print(f"  ⚠ {w}")

    # Write file with header
    out_path = OUTPUT_DIR / filename
    header = f"""<!-- PAPER DOWNLOAD
Source: {url}
Tier: {tier}
Notes: {notes}
Expected title fragment: {expected_title}
Expected author fragment: {expected_author}
Downloaded: auto
Warnings at download time: {warnings if warnings else 'none'}
-->

"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + content_md)

    result["status"] = "OK" if not warnings else "OK_WITH_WARNINGS"
    print(f"  ✓ Saved {result['char_count']:,} chars → {filename}")
    return result


def main():
    print("Persona Circuits — Paper Downloader")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Papers to attempt: {len(PAPERS)}")
    print(f"Papers skipped (no URL / paywalled): {len(SKIPPED)}")

    results = []
    for paper_args in PAPERS:
        result = download_paper(*paper_args)
        results.append(result)
        time.sleep(1.5)  # Be polite to servers

    # Summary
    print(f"\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")

    ok = [r for r in results if r["status"] == "OK"]
    ok_warn = [r for r in results if r["status"] == "OK_WITH_WARNINGS"]
    failed = [r for r in results if r["status"] in ("FETCH_FAILED", "PARSE_FAILED")]

    print(f"\n✓  Clean downloads:      {len(ok)}")
    print(f"⚠  Downloads with warnings: {len(ok_warn)}")
    print(f"✗  Failed:               {len(failed)}")

    if ok_warn:
        print("\nWarnings to review:")
        for r in ok_warn:
            print(f"  {r['filename']}:")
            for w in r["warnings"]:
                print(f"    {w}")

    if failed:
        print("\nFailed downloads:")
        for r in failed:
            print(f"  {r['filename']} [{r['status']}] — {r['url']}")

    print(f"\nSkipped (no URL / paywalled):")
    for name, reason in SKIPPED:
        print(f"  {name}: {reason}")

    # Write a manifest
    manifest_lines = ["# Papers Download Manifest\n"]
    manifest_lines.append("| File | Tier | Status | Chars | Notes |\n")
    manifest_lines.append("|------|------|--------|-------|-------|\n")
    for r in results:
        status_icon = "✓" if r["status"] == "OK" else ("⚠" if "WARNINGS" in (r["status"] or "") else "✗")
        manifest_lines.append(
            f"| {r['filename']} | {r['tier']} | {status_icon} {r['status']} | {r['char_count']:,} | {r['notes']} |\n"
        )
    manifest_lines.append("\n## Skipped (no confirmed URL or paywalled)\n\n")
    for name, reason in SKIPPED:
        manifest_lines.append(f"- **{name}**: {reason}\n")

    with open(OUTPUT_DIR / "DOWNLOAD_MANIFEST.md", "w") as f:
        f.writelines(manifest_lines)
    print(f"\nManifest written to DOWNLOAD_MANIFEST.md")


if __name__ == "__main__":
    main()
