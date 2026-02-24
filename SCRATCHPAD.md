# Scratchpad

Running notes, observations, hypotheses, and debugging logs during experiment execution.

**Rules:**
- Append-only during a session (never delete earlier entries)
- Each entry prefixed with ISO timestamp and session ID
- Use for: intermediate observations, unexpected results, debugging notes, quick calculations
- Transfer finalized findings to `results/` and update `CURRENT_STATE.md`

---

## Entries

(No entries yet — experiment not started)

## [2026-02-24T14:46:02-0600] PRE-RUN: modal_gpu_smoke_test
- THOUGHT_LOG pending actions reviewed: YES — no pending actions are required before Week 1 infrastructure checks.
- W&B run name: N/A (Modal smoke test only)
- Script: scripts/modal_gpu_smoke_test.py
- Config: gpu=A100-80GB, timeout=600s
- What I'm testing: Modal account can launch an A100 job and execute a minimal Torch CUDA check.
- Expected outcome: Modal run returns `cuda_available=true` with non-empty GPU device name.
- Expected duration: ~3-8 minutes
- Implementation verified: YES — local syntax validation passed via `python3 -m py_compile`.
- Adversarial self-questioning:
  - Most likely design flaw: false pass if function runs on CPU fallback.
  - Simplest confound: CUDA import succeeds but no actual allocated GPU.
  - Failure signature: `cuda_available=false`, device count 0, or Modal scheduling failure.
  - If expected result appears, probability of being wrong: low but non-zero; I will also verify reported device name and count.
- Status: LAUNCHING

## [2026-02-24T14:46:24-0600] POST-RUN: modal_gpu_smoke_test
- W&B URL: N/A
- Modal app ID: N/A (function did not launch)
- Outcome: FAILURE
- Key metric: launch_error=TypeError(A100.__init__() got unexpected keyword argument `memory`)
- Artifacts saved: none
- Anomalies: Modal GPU API mismatch with proposal snippet (`memory=80` invalid on modal client 1.3.2).
- Next step: Update Modal GPU spec to supported A100-80GB syntax and rerun smoke test.

## [2026-02-24T14:46:39-0600] PRE-RUN: modal_gpu_smoke_test_retry
- THOUGHT_LOG pending actions reviewed: YES — no pending actions are required before Week 1 infrastructure checks.
- W&B run name: N/A (Modal smoke test only)
- Script: scripts/modal_gpu_smoke_test.py
- Config: gpu=A100(size="80GB"), timeout=600s
- What I'm testing: Modal account can launch an A100-80GB job and execute a minimal Torch CUDA check.
- Expected outcome: Modal run returns `cuda_available=true` with non-empty GPU device name and device_count>=1.
- Expected duration: ~3-8 minutes
- Implementation verified: YES — local syntax validation passed via `python3 -m py_compile`.
- Adversarial self-questioning:
  - Most likely design flaw: successful launch but no CUDA context attached.
  - Simplest confound: stale cache output from prior failed run.
  - Failure signature: `cuda_available=false`, device count 0, or scheduling error.
  - If expected result appears, probability of being wrong: low; I will check app id and returned hardware metadata.
- Status: LAUNCHING

## [2026-02-24T14:48:47-0600] POST-RUN: modal_gpu_smoke_test_retry
- W&B URL: N/A
- Modal app ID: ap-eQJaykjaI4wUQ7Wt9ikRbT
- Outcome: SUCCESS
- Key metric: cuda_available=true, cuda_device_name="NVIDIA A100 80GB PCIe", device_count=1
- Artifacts saved: scripts/modal_gpu_smoke_test.py (validated by execution)
- Anomalies: Modal deprecation warning suggests using `gpu="A100-80GB"` string form; runtime warning indicates NumPy missing in smoke image (non-blocking for CUDA validation).
- Next step: Update smoke-test GPU spec to deprecation-safe syntax and continue Day 1 checklist execution.
