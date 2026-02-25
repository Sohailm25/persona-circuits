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

## [2026-02-24T21:20:10-0600] PIVOT: Enforce strict disjointness between extraction and held-out validation prompts
- Trigger: exact-string overlap check found 2 duplicate hallucination queries between `prompts/hallucination_pairs.jsonl` and held-out set.
- Original approach: generate held-out prompts independently and rely on low collision probability.
- New approach: hard-block any held-out query whose normalized text appears in extraction prompts for the same trait.
- Rationale: Week 2 validation must be on truly held-out prompts to avoid contamination/overfitting risk.
- Impact: `scripts/generate_week2_heldout_prompts.py` updated; hallucination held-out regenerated; overlap now 0 for all traits.

## [2026-02-24T21:22:05-0600] DECISION: Behavioral sweep uses top-2 candidate layers per trait from extraction margins
- Trigger: full grid over 6 layers x 6 alphas x 50 prompts x 3 traits is computationally heavy and delays iteration.
- Original approach: evaluate all layers 11-16 uniformly in judge-based behavioral sweep.
- New approach: preselect top-2 layers per trait using extraction `projection_margin_mean`, then run full alpha sweep + held-out evaluation on those layers.
- Rationale: keeps behavioral selection grounded in measured signal while reducing compute enough to run reversal + cross-rater checks in one pass.
- Impact: Week 2 behavioral results are conditioned on top-2 layer preselection; if effects are weak/inconsistent, escalate to full 11-16 sweep.

## [2026-02-24T21:22:20-0600] PIVOT: Fix hook callback signature in behavioral validation script
- Trigger: local spot-check failed with `TypeError ... got an unexpected keyword argument 'hook'`.
- Original approach: hook callback accepted parameter name `_hook`.
- New approach: use `hook` parameter name (TransformerLens passes by keyword) and ignore it explicitly.
- Rationale: without this fix, steering hooks would silently fail at runtime.
- Impact: `scripts/week2_behavioral_validation.py` patched and local spot-check rerun successfully.

## [2026-02-24T21:24:10-0600] PIVOT: Add missing `anthropic` dependency to Week 2 behavioral validation image
- Trigger: First full behavioral validation run failed immediately with `ModuleNotFoundError: No module named 'anthropic'`.
- Original approach: Modal image installed model/analysis stack but omitted Anthropic client package.
- New approach: Add `anthropic` to `scripts/week2_behavioral_validation.py` Modal image dependencies and rerun.
- Rationale: Judge-based scoring is a required component of Week 2 validation; missing client blocks all trait metrics.
- Impact: Rebuild image and rerun behavioral validation job from scratch.

## [2026-02-24T21:56:41-0600] PIVOT: Abort in-flight behavioral run after held-out prompt mutation; rerun on frozen audited set
- Trigger: During run monitoring, I regenerated held-out prompts to restore complete 3-trait audit coverage; this changed on-disk prompt files after the in-flight validation job had already loaded an earlier prompt set.
- Original approach: Let the in-flight run continue and use its results.
- New approach: Stop the in-flight run, snapshot/verify the now-audited held-out prompts, and rerun behavioral validation so results map 1:1 to current artifacts.
- Rationale: Using results from prompts that no longer exist on disk breaks reproducibility/traceability and weakens evidence status.
- Impact: Current run marked invalid for milestone evidence; Week 2 behavioral validation rerun required before selecting final layer/alpha.

## [2026-02-24T22:09:29-0600] DECISION: Add held-out prompt hashing metadata to behavioral validation reports
- Trigger: Prompt mutation incident exposed that run outputs were not self-describing with respect to exact prompt inputs.
- Original approach: Save only behavioral metrics and selected examples; rely on external prompt files staying unchanged.
- New approach: Compute and store per-trait held-out prompt hashes/counts in the run report; also emit a standalone held-out prompt manifest artifact.
- Rationale: Traceability requires that results can be tied to exact input datasets even if files later change.
- Impact: `scripts/week2_behavioral_validation.py` now records `heldout_prompt_hashes` and `heldout_prompt_counts`; manifest artifact added under `results/stage1_extraction/`.
