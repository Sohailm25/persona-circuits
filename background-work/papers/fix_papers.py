#!/usr/bin/env python3
# ABOUTME: Fixes paper downloads: strips base64 bloat, re-downloads failed papers, adds new papers.
# ABOUTME: Run after download_papers.py to patch all known issues.

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

# ─── New / fixed papers to download ────────────────────────────────────────────
FIXES = [
    # Circuit tracing: original URL was a meta-refresh redirect to biology.html
    (
        "lindsey2025_circuit_tracing.md",
        "https://transformer-circuits.pub/2025/attribution-graphs/biology.html",
        "circuit",
        "lindsey",
        1,
        "Circuit tracing / attribution graphs",
    ),
    # Failed arXiv HTML → ar5iv fallback
    (
        "chen2025_persona_vectors.md",
        "https://ar5iv.labs.arxiv.org/html/2507.21509",
        "persona vectors",
        "chen",
        1,
        "Persona vector extraction methodology",
    ),
    (
        "conmy2023_acdc.md",
        "https://ar5iv.labs.arxiv.org/html/2304.14997",
        "circuit discovery",
        "conmy",
        2,
        "ACDC — automated circuit discovery",
    ),
    (
        "wang2022_ioi_circuit.md",
        "https://ar5iv.labs.arxiv.org/html/2211.00593",
        "indirect object",
        "wang",
        2,
        "IOI circuit — faithfulness standard (>=80%)",
    ),
    # New paper added by Sohail
    (
        "andreas2022_lm_agent_models.md",
        "https://ar5iv.labs.arxiv.org/html/2212.01681",
        "agent models",
        "andreas",
        2,
        "LMs as agent models — theoretical grounding for persona simulation",
    ),
]


def fetch_url(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            encoding = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(encoding, errors="replace")
    except Exception:
        return None


def clean_html(html: str, expected_title: str, expected_author: str) -> tuple[str | None, list[str]]:
    warnings = []
    soup = BeautifulSoup(html, "html.parser")

    article = (
        soup.find("article")
        or soup.find("div", class_="ltx_document")
        or soup.find("div", id="content")
        or soup.find("main")
        or soup.body
    )
    if not article:
        return None, ["Could not find article body"]

    for tag in article.find_all(["nav", "footer", "script", "style", "header", "aside"]):
        tag.decompose()

    # Remove img tags with base64 src before converting to markdown
    for img in article.find_all("img"):
        src = img.get("src", "")
        if src.startswith("data:"):
            img.decompose()

    full_text = article.get_text(separator=" ", strip=True).lower()

    if expected_title.lower() not in full_text:
        warnings.append(f"WARNING: Expected title fragment '{expected_title}' NOT found in page text")
    if expected_author.lower() not in full_text:
        warnings.append(f"WARNING: Expected author '{expected_author}' NOT found in page text")

    has_abstract = "abstract" in full_text
    has_end = any(w in full_text for w in ["conclusion", "references", "acknowledgment", "discussion"])
    if not has_abstract:
        warnings.append("WARNING: No 'abstract' found — page may be incomplete or wrong paper")
    if not has_end:
        warnings.append("WARNING: No conclusion/references section found — paper may be truncated")

    content_md = md(str(article), heading_style="ATX", strip=["script", "style"])

    # Strip any remaining base64 data URIs that slipped through markdownify
    content_md = re.sub(r"!\[.*?\]\(data:image/[^)]+\)", "[image removed]", content_md)
    content_md = re.sub(r'src=["\']data:image/[^"\']+["\']', 'src="[base64 removed]"', content_md)

    # Trim excessive blank lines
    content_md = re.sub(r"\n{4,}", "\n\n\n", content_md)

    return content_md, warnings


def strip_base64_from_file(filepath: Path) -> tuple[int, int]:
    """Strip base64 images from an already-downloaded file. Returns (old_size, new_size)."""
    text = filepath.read_text(encoding="utf-8")
    old_size = len(text)

    # Strip markdown image embeds with base64
    text = re.sub(r"!\[.*?\]\(data:image/[^)]+\)", "[image removed]", text)
    # Strip HTML src= base64
    text = re.sub(r'src=["\']data:image/[^"\']+["\']', 'src="[base64 removed]"', text)
    # Trim excessive blank lines
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    new_size = len(text)
    filepath.write_text(text, encoding="utf-8")
    return old_size, new_size


def download_paper(
    filename: str, url: str, expected_title: str, expected_author: str, tier: int, notes: str
) -> dict:
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
        print("  ✗ FETCH FAILED")
        return result

    print(f"  Downloaded {len(html):,} bytes of HTML")

    content_md, warnings = clean_html(html, expected_title, expected_author)
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
    print("Persona Circuits — Paper Fix Script")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # ── Step 1: Strip base64 from bloated existing files ──────────────────────
    BLOATED = [
        "marks2026_persona_selection_model.md",
        "bricken2023_monosemanticity.md",
        "elhage2022_toy_models_superposition.md",
    ]
    print("STEP 1: Stripping base64 images from bloated files")
    print("-" * 60)
    for fname in BLOATED:
        fpath = OUTPUT_DIR / fname
        if not fpath.exists():
            print(f"  SKIP (not found): {fname}")
            continue
        old, new = strip_base64_from_file(fpath)
        reduction_pct = (1 - new / old) * 100 if old > 0 else 0
        print(f"  {fname}")
        print(f"    Before: {old:,} chars  →  After: {new:,} chars  ({reduction_pct:.1f}% reduction)")

    # ── Step 2: Re-download / download new papers ─────────────────────────────
    print(f"\nSTEP 2: Downloading {len(FIXES)} papers (fixes + new)")
    print("-" * 60)
    results = []
    for paper_args in FIXES:
        result = download_paper(*paper_args)
        results.append(result)
        time.sleep(1.5)

    # ── Step 3: Summary ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("FIX SUMMARY")
    print(f"{'='*60}")

    ok = [r for r in results if r["status"] == "OK"]
    ok_warn = [r for r in results if r["status"] == "OK_WITH_WARNINGS"]
    failed = [r for r in results if r["status"] in ("FETCH_FAILED", "PARSE_FAILED")]

    print(f"\n✓  Clean downloads:         {len(ok)}")
    print(f"⚠  Downloads with warnings: {len(ok_warn)}")
    print(f"✗  Failed:                  {len(failed)}")

    if ok_warn:
        print("\nWarnings:")
        for r in ok_warn:
            print(f"  {r['filename']}:")
            for w in r["warnings"]:
                print(f"    {w}")

    if failed:
        print("\nFailed:")
        for r in failed:
            print(f"  {r['filename']} [{r['status']}] — {r['url']}")

    # ── Step 4: Regenerate manifest from all files on disk ────────────────────
    print(f"\n{'='*60}")
    print("Regenerating DOWNLOAD_MANIFEST.md from all files on disk")

    all_md_files = sorted(
        [f for f in OUTPUT_DIR.glob("*.md") if f.name != "DOWNLOAD_MANIFEST.md"],
        key=lambda p: p.name,
    )

    manifest_lines = ["# Papers Download Manifest\n\n"]
    manifest_lines.append("| File | Size | Notes |\n")
    manifest_lines.append("|------|------|-------|\n")

    for fpath in all_md_files:
        size = fpath.stat().st_size
        # Read the header comment to get notes
        try:
            text = fpath.read_text(encoding="utf-8")[:500]
            notes_match = re.search(r"Notes: (.+)", text)
            notes = notes_match.group(1).strip() if notes_match else ""
        except Exception:
            notes = ""
        size_str = f"{size / 1024:.0f}K" if size < 1_000_000 else f"{size / 1_000_000:.1f}M"
        manifest_lines.append(f"| {fpath.name} | {size_str} | {notes} |\n")

    manifest_lines.append("\n## Known Issues / Skipped\n\n")
    manifest_lines.append("- **chen2025_persona_vectors**: arXiv:2507.21509 — no arXiv HTML; using ar5iv fallback\n")
    manifest_lines.append("- **conmy2023_acdc**: arXiv:2304.14997 — no arXiv HTML; using ar5iv fallback\n")
    manifest_lines.append("- **wang2022_ioi_circuit**: arXiv:2211.00593 — no arXiv HTML; using ar5iv fallback\n")
    manifest_lines.append("- **lindsey2025_circuit_tracing**: index.html was meta-refresh; fixed to biology.html\n")
    manifest_lines.append("- **marks2026/bricken2023/elhage2022**: base64 images stripped (were 7–19M)\n")
    manifest_lines.append("\n## Skipped (no URL / paywalled)\n\n")
    skipped = [
        ("marks2026_psm", "URL confirmed but may require auth: alignment.anthropic.com/2026/psm/"),
        ("greenblatt2024_alignment_faking", "URL unverified: likely arXiv:2412.14093"),
        ("li2024_ablation_validity", "NeurIPS 2024 — no confirmed arXiv ID"),
        ("macdiarmd2025_poser", "arXiv ID unknown"),
        ("bailey2026_obfuscated_activations", "ICLR 2026 — arXiv ID unknown"),
        ("kantamneni2025_sae_safety", "ICML 2025 — arXiv ID unknown"),
        ("campbell2024_lying_circuits", "arXiv ID unknown"),
        ("venkatesh2026_identifiability", "arXiv ID unknown"),
        ("lu2026_assistant_axis", "arXiv ID unknown"),
        ("salminen2021_persona_survey", "DOI only — likely behind paywall"),
    ]
    for name, reason in skipped:
        manifest_lines.append(f"- **{name}**: {reason}\n")

    with open(OUTPUT_DIR / "DOWNLOAD_MANIFEST.md", "w") as f:
        f.writelines(manifest_lines)

    print("✓ Manifest written to DOWNLOAD_MANIFEST.md")
    print()
    print("All done. Run: ls -lh background-work/papers/ to verify file sizes.")


if __name__ == "__main__":
    main()
