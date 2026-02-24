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
