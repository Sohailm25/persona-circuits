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
