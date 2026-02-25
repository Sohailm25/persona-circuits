# Decision Log

Architectural and methodological decisions made during execution, with rationale.

**Rules:**
- Record every non-trivial decision (threshold changes, methodology pivots, scope changes)
- Include: decision, alternatives considered, rationale, date
- Decisions here override the proposal if they conflict (proposal is the starting plan; this is the living record)
- Reference the proposal section being modified

---

## Decisions

## [2026-02-24T14:40:21-0600] DECISION: Keep existing Modal secrets and add canonical Appendix G.1 names
- Trigger: `modal secret list` showed existing secrets with non-canonical names (`wandb-secret`, `hf-secret`) and missing required names used in proposal code (`anthropic-key`, `wandb-key`, `hf-token`).
- Original approach: Reuse existing secret names and adapt scripts ad hoc.
- New approach: Create missing canonical secret names while keeping old secrets intact.
- Rationale: Proposal Appendix G.1/G.2 code expects canonical names; adding them avoids name drift and future setup ambiguity.
- Impact: Modal secrets now include canonical names required for experiment scripts.

## [2026-02-24T14:45:00-0600] PIVOT: Repair local arm64 Python environment during toolchain verification
- Trigger: Import validation failed for `sae_lens` due x86_64 wheels (`safetensors`, `xxhash`, `tokenizers`) on an arm64 machine.
- Original approach: Assume existing package install was sufficient after cloning dependencies.
- New approach: Reinstall incompatible binary packages with arm64 wheels and re-run import checks until all required modules pass.
- Rationale: Toolchain validation is a Day 1 requirement; unresolved binary mismatches would invalidate local checks and later runs.
- Impact: Local imports now pass for `sae_lens`, `transformer_lens`, and `circuit_tracer`; environment warning/conflict notes preserved in logs.

## [2026-02-24T14:46:30-0600] PIVOT: Modal A100 spec update in smoke-test script
- Trigger: `modal run scripts/modal_gpu_smoke_test.py` failed with `TypeError: A100.__init__() got an unexpected keyword argument 'memory'`.
- Original approach: Use proposal snippet form `modal.gpu.A100(memory=80)` directly.
- New approach: Use the modal client 1.3.2-compatible API for A100-80GB (`modal.gpu.A100(size="80GB")`).
- Rationale: We need a successful Day 1 GPU validation and the installed Modal SDK differs from the proposal pseudocode.
- Impact: Smoke-test script updated; no change to experiment logic.

## [2026-02-24T14:48:55-0600] DECISION: Use `gpu=\"A100-80GB\"` string syntax in Modal script
- Trigger: Successful smoke test emitted a deprecation warning for `modal.gpu.A100(...)`.
- Original approach: Keep the API-compatible object form after the failure fix.
- New approach: Move to string syntax (`gpu=\"A100-80GB\"`) recommended by current Modal runtime.
- Rationale: Reduce deprecation churn and keep scripts forward-compatible with current Modal guidance.
- Impact: `scripts/modal_gpu_smoke_test.py` now uses deprecation-safe GPU specification.

## [2026-02-24T15:49:10-0600] PIVOT: Add `git` system dependency to Modal Week1 image
- Trigger: Modal image build failed for `scripts/week1_day3_5_modal_setup.py` with `/bin/sh: git: not found` during circuit-tracer clone.
- Original approach: Build from `modal.Image.debian_slim(...).pip_install(...).run_commands(git clone ...)` without apt packages.
- New approach: Add `.apt_install("git")` before run commands.
- Rationale: circuit-tracer installation from source requires git in image build context.
- Impact: Rebuild image and rerun Week 1 Day 3-5 validation jobs.

## [2026-02-24T16:08:16-0600] PIVOT: Instrument cache path handling before Gemma run
- Trigger: Llama validation reported successful loads but `/models/huggingface` cache summary showed only ~2MB, suggesting downloads may bypass persistent volume.
- Original approach: Assume `HF_HOME` + `TRANSFORMERS_CACHE` + `HUGGINGFACE_HUB_CACHE` were sufficient.
- New approach: Add explicit `HF_HUB_CACHE` and log both `/models/huggingface` and `/root/.cache/huggingface` summaries for verification.
- Rationale: Week 1 infrastructure requires persistent model storage on Modal volume; this must be verified directly.
- Impact: Week1 Modal setup script updated before Gemma/CLT validation run.

## [2026-02-24T16:23:42-0600] PIVOT: Rework cache initialization + CLT sanity settings
- Trigger: Gemma run loaded assets but reported CLT graph nodes/edges = 0 and showed cache writes primarily in `/root/.cache/huggingface` instead of `/models/huggingface`.
- Original approach: Set cache env variables after importing HF-dependent libraries; use minimal CLT attribution params (`max_n_logits=1`, `max_feature_nodes=128`).
- New approach: Set cache env before HF-related imports and increase CLT attribution budget for sanity run; fail fast if CLT graph remains empty.
- Rationale: Week 1 requires persistent model storage and usable CLT setup, not just successful imports.
- Impact: Modal setup script patched and Gemma/CLT validation rerun.

## [2026-02-24T16:39:44-0600] PIVOT: Align CLT graph sanity check with circuit-tracer Graph API
- Trigger: Gemma retry failed on empty-graph assertion using `graph.nodes`/`graph.edges`; local source inspection showed `Graph` stores `adjacency_matrix`, `selected_features`, and related tensors instead.
- Original approach: Treat missing `nodes`/`edges` dict attributes as empty graph.
- New approach: Compute graph non-emptiness from `adjacency_matrix` nonzero entries plus selected-feature counts.
- Rationale: Prior assertion could falsely fail even when attribution data exists.
- Impact: Update CLT validation metrics and rerun Gemma/CLT setup check.

## [2026-02-24T16:52:30-0600] PIVOT: Hold Week 2 start until prompt quality defects are fixed
- Trigger: Critical audit found spec violations in generated prompts (notably many `evil` prompts explicitly requesting harmful instructions; also minor sycophancy explicit-agreement and hallucination ground-truth quality issues).
- Original approach: Move directly into Week 2 extraction based on count/schema checks only.
- New approach: Treat prompt quality as a Week 1 milestone gate; regenerate/patch prompts and re-audit before extraction.
- Rationale: Label/prompt contamination at Stage 1 would invalidate downstream vector extraction and causal claims.
- Impact: Week 2 script start deferred until post-fix prompt audit passes.

## [2026-02-24T18:54:10-0600] PIVOT: Harden evil-prompt quality rules after manual false-negative discovery
- Trigger: Manual sample review found a still-noncompliant `evil` query ("How do people in abusive relationships control their partners...") even though automated audit passed.
- Original approach: Regex checks limited to explicit harm lexemes (revenge/blackmail/etc.) and a narrow manipulation pattern.
- New approach: Introduce shared `scripts/prompt_quality_rules.py` used by both generator and auditor, with stronger detection for instructional harm requests, coercive-control prompts, and fictionalized malicious roleplay prompts.
- Rationale: A passed automated audit is insufficient evidence if it misses obvious harmful-instruction requests; audit/generation must share one rule source to avoid drift.
- Impact: Regenerated `evil_pairs.jsonl`, reran full audit, and re-ran manual spot-check sampling before allowing Week 2 start.

## [2026-02-24T19:03:15-0600] DECISION: Week 2 extraction script selects only a preliminary best layer via activation-margin proxy
- Trigger: Week 2 Days 1-3 requires layer sweep implementation before full behavioral judge validation is ready.
- Original approach: Leave layer ranking undefined until full Claude-judge steering eval exists.
- New approach: Compute and log preliminary best layer per trait via mean projection margin `(high @ v - low @ v)` across extraction pairs, and mark it as preliminary.
- Rationale: Provides deterministic day-1 extraction diagnostics while preserving proposal requirement that final layer/alpha decisions come from behavioral validation (§6.2.3).
- Impact: `scripts/week2_extract_persona_vectors.py` now logs preliminary layer ranking; final optimal layer remains a Week 2 validation task.

## [2026-02-24T19:05:20-0600] PIVOT: Add tokenizer-template fallback in extraction prompt formatter
- Trigger: Week 2 local spot-check failed for `gpt2` with `ValueError` from `apply_chat_template` (tokenizer has no chat template).
- Original approach: Always call `tokenizer.apply_chat_template(...)` when the method exists.
- New approach: Use chat template only when `tokenizer.chat_template` is present; otherwise fall back to plain `System/User/Assistant` formatted text.
- Rationale: Extraction pipeline should be model-agnostic for local instrumentation checks and avoid false failures on non-chat tokenizers.
- Impact: Spot-check path now succeeds; extraction script is robust to both chat and non-chat tokenizers.
