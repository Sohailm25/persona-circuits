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

## [2026-02-25T05:07:49-0600] DECISION: Treat Week2 behavioral run `8b3fp37q` as diagnostic, not final selection evidence
- Trigger: Frozen rerun completed with valid artifacts but failed reliability checks (cross-rater kappa <0.6 for all traits; hallucination parse-fallback flag).
- Original approach: Accept selected layer/alpha directly from first completed frozen rerun.
- New approach: Keep selected combinations as provisional only and require judge/rubric calibration + rerun before Week 2 closeout.
- Rationale: Proposal Appendix C reliability standards and our implementation checks require trustworthy judge behavior before claiming validated steering.
- Impact: Week 2 remains in-progress; final layer/alpha lock deferred pending calibrated rerun.

## [2026-02-25T05:42:58-0600] PIVOT: Upgrade Week 2 validation from top-2 quick sweep to full calibrated per-trait sweep with confirm split
- Trigger: Prior frozen run (`8b3fp37q`) produced provisional layer/alpha picks but failed reliability gates (kappa <0.6; hallucination parse risk), making quick top-2 selection insufficient evidence.
- Original approach: Single job across all traits using top-2 layers per trait from extraction margins, selecting best combo directly from the same prompt pool used for sweeping.
- New approach: Introduce upgraded per-trait Week 2 runner (`scripts/week2_behavioral_validation_upgrade.py`) with full layer sweep over configured steering layers, extended alpha grid, sweep/confirm held-out split, and confirm-based final selection.
- Rationale: This reduces layer-selection bias, supports parallel trait execution, and enforces a stricter evidence path before accepting final layer/alpha claims.
- Impact: Week 2 closeout now depends on upgraded calibration+sweep runs; prior selections remain diagnostic only.

## [2026-02-25T05:43:10-0600] DECISION: Treat judge parse robustness and control separation as hard quality gates for Week 2 acceptance
- Trigger: Hallucination trait showed elevated fallback-like behavior under loose parsing in prior run; literature and guidance emphasize judge fragility and control baselines.
- Original approach: Parse first integer with implicit fallback score behavior and rely mainly on kappa + steering deltas.
- New approach: Use strict JSON-first judge prompting/parsing with explicit parse-failure accounting, plus required random/shuffled-vector control separation and cross-trait bleed measurement in upgraded validation.
- Rationale: Prevent silent parse artifacts from masquerading as trait effects and enforce that selected vectors outperform null controls before acceptance.
- Impact: Added quality gates (`judge_parse_fail_rate`, `control_separation_pass`) and expanded outputs in Week 2 upgraded reports; launch planning now includes these criteria explicitly.

## [2026-02-25T05:43:24-0600] DECISION: Generate an explicit parallel launch matrix artifact before any upgraded run execution
- Trigger: User requested a broad parallel sweep map and explicit check-in before launch.
- Original approach: Launch ad hoc modal commands trait-by-trait.
- New approach: Build `scripts/week2_upgrade_parallel_plan.py` to emit a traceable job matrix (primary + replication + stress tiers), call/runtime estimates, input hashes, and ready-to-run commands without execution.
- Rationale: Separates planning from execution, exposes compute/API footprint up front, and improves reproducibility/traceability of what will be launched.
- Impact: Plan artifact written to `results/stage1_extraction/week2_upgrade_parallel_plan_20260225T113925Z.json`; launch script written to `scratch/week2_upgrade_launch_commands.sh`.

## [2026-02-25T06:00:40-0600] PIVOT: Add judge-side throttle and retry/backoff resilience before any broad Week 2 parallel launch
- Trigger: User raised explicit concern about rate limits/backoff; planned launch matrix includes high concurrent judge traffic (~47k+ primary calls).
- Original approach: Fixed-RPM pacing without robust handling of transient API failures/429 retry windows.
- New approach: Add per-model sliding-window throttles, configurable global-RPM budget split across assumed parallel runs, retryability detection (429/5xx/timeouts/connectivity), Retry-After honoring, and exponential backoff+jitter with bounded attempts.
- Rationale: Large multi-job sweeps need resilient judge I/O or reliability conclusions become confounded by transport/API instability.
- Impact: `scripts/week2_behavioral_validation_upgrade.py` and `scripts/week2_upgrade_parallel_plan.py` now include throttle/backoff controls in execution and plan artifacts.

## [2026-02-25T06:06:55-0600] PIVOT: Tighten Week 2 acceptance gates after exhaustive literature second pass
- Trigger: Second pass across Chen/Rimsky/Turner/Zou/Bhandari/Wang highlighted three remaining weaknesses: no explicit coherence gate, no calibration directionality gate, and single-sample random control.
- Original approach: Judge reliability gate = kappa + pairwise sign + parse-fail threshold; controls used one random vector plus one shuffled vector.
- New approach:
  - Add directionality calibration (`high > low`) pass-rate threshold for Sonnet+Opus on known contrast pairs.
  - Add coherence gate on selected combo outputs (minimum coherence mean + maximum allowed drop from baseline).
  - Replace single random control with multi-random distributional control (`random_control_vectors`, default 8) and require selected effect > random p95 and > shuffled control.
- Rationale: This better matches published steering-evaluation practice and reduces risk that noisy judges or lucky random controls produce false-positive layer/alpha selections.
- Impact: Upgraded runner and planner updated; launch command matrix regenerated with new flags and revised call/runtime estimates.

## [2026-02-25T06:27:35-06:00] PIVOT: Pass extraction prompt rows from local entrypoint to Modal remote for prelaunch gap checks
- Trigger: `week2_prelaunch_gap_checks_initial` failed in remote container with `FileNotFoundError: Missing extraction prompt file: /prompts/sycophancy_pairs.jsonl`.
- Original approach: Load `prompts/{trait}_pairs.jsonl` inside the remote Modal function using repo-relative paths.
- New approach: Load extraction rows locally in `main()` and pass `extraction_rows_by_trait` as a serialized argument to the remote function.
- Rationale: Modal remote runtime does not have local repo prompt files mounted by default; passing rows removes filesystem coupling and improves reproducibility.
- Impact: Prelaunch gap-check run can execute extraction-method A/B without path-dependent failures.

## [2026-02-25T06:32:34-06:00] PIVOT: Tighten Week 2 upgrade quality gates for closeout validity
- Trigger: Critical implementation audit found three acceptance-path weaknesses: secondary-judge parse failures were not required, non-trait control-test score had no gate, and capability proxy auto-passed when unavailable.
- Original approach: Require only primary parse-fail gate; log control/specificity as diagnostics; treat missing capability proxy as pass.
- New approach: Require both primary and secondary parse-fail passes, add hard gates for control-test score and specificity shift, and require capability proxy availability unless explicitly overridden via --allow-missing-capability-proxy.
- Rationale: These are direct reliability risks that can produce false-positive layer/alpha acceptance under judge/parser noise or missing capability evidence.
- Impact: Updated scripts/week2_behavioral_validation_upgrade.py and scripts/week2_upgrade_parallel_plan.py; regenerated launch matrix artifact and commands with new gate parameters.

## [2026-02-25T06:37:34-06:00] PIVOT: Add TruthfulQA known-fact check to Week 2 hallucination validation
- Trigger: Proposal §6.2.3 expects hallucination validation to include known-fact accuracy behavior, but upgraded runner only had generic MMLU capability proxy.
- Original approach: Use held-out rubric shifts + MMLU proxy as acceptance evidence for all traits.
- New approach: Add a TruthfulQA generation-split directional check for hallucination (baseline/plus/minus; require plus > baseline > minus with minimum plus-minus separation) and include it in quality gates when trait=hallucination.
- Rationale: Prevent Week 2 closeout from relying only on rubric shifts without an explicit known-fact benchmark for hallucination.
- Impact: Updated scripts/week2_behavioral_validation_upgrade.py and scripts/week2_upgrade_parallel_plan.py; regenerated launch plan with new CLI knobs and runtime estimates.

## [2026-02-25T06:46:45-06:00] PIVOT: Add stochastic multi-rollout averaging and steering-norm diagnostics to Week 2 validation
- Trigger: Pre-launch audit identified two unresolved rigor gaps: single deterministic rollout per prompt and no explicit steering-magnitude-to-residual diagnostic.
- Original approach: Single rollout per prompt at fixed decoding temperature; no direct logging of |alpha|*||v|| relative to residual norms.
- New approach: Add configurable rollout controls (sweep/confirm/baseline rollouts per prompt plus rollout temperature) and average scores across rollouts; add steering norm diagnostics reporting injection-to-residual norm ratios at selected layer/alpha.
- Rationale: Better aligns with literature that averages multiple generations for behavioral scoring stability (e.g., Chen) and analyzes intervention magnitude relative to native residual scales (Turner).
- Impact: Updated scripts/week2_behavioral_validation_upgrade.py and scripts/week2_upgrade_parallel_plan.py; launch matrix regenerated with revised call/runtime estimates.

## [2026-02-25T06:57:14-0600] PIVOT: Fix generation `top_k=0` incompatibility in upgraded Week 2 runner
- Trigger: Remote smoke run `week2-upgrade-smoke-sycophancy-post-rollout-norm` failed at generation with `AssertionError: top_k has to be greater than 0` from current `transformer_lens`.
- Original approach: Call `model.generate(..., top_k=0)` in both steered and unsteered paths.
- New approach: Use `top_k=None` (no top-k truncation) so generation is compatible with current library behavior.
- Rationale: This is an implementation breakage that would invalidate or block all upgraded Week 2 runs under the current runtime image.
- Impact: Patch required in `scripts/week2_behavioral_validation_upgrade.py`; rerun smoke check before trusting recent rollout/norm upgrades.

## [2026-02-25T07:08:40-0600] PIVOT: Elevate sweep stage to multi-rollout defaults and expand oversteer diagnostics beyond means
- Trigger: Gap-focused literature pass found that sampled averaging is standard in comparable steering evaluations, and mean-only norm ratios can hide outlier oversteer.
- Original approach: Sweep defaults used 1 deterministic rollout per prompt; steering norm diagnostics reported mostly mean-ratio summaries.
- New approach: Set sweep default rollouts to 3 (planner + runner), and expand diagnostics with ratio distributions (median/p90/p95/max/min), exceedance fractions (>0.5, >1.0), and max-ratio warnings.
- Rationale: Reduces variance-sensitive selection risk at the sweep stage and improves detection of oversteer outliers that mean metrics can miss.
- Impact: Updated `scripts/week2_behavioral_validation_upgrade.py` and `scripts/week2_upgrade_parallel_plan.py`; regenerated plan artifact with revised call/runtime estimates.

## [2026-02-25T13:30:12Z] PIVOT: Norm-match null controls to selected steering vector magnitude
- Trigger: Review audit showed strengthened random/shuffled controls, but code inspection found null vectors were unit-normalized while selected steering vector kept native norm.
- Original approach: Compare selected vector effect against random/shuffled/random-text controls with mismatched intervention magnitudes.
- New approach: Scale all null directions to the selected direction norm and log `selected_direction_norm`/`control_direction_norm` in report controls.
- Rationale: Null controls must be magnitude-matched to avoid inflated apparent selectivity from weaker interventions.
- Impact: Updated `scripts/week2_behavioral_validation_upgrade.py` control block and report schema; rerun smoke validation required.

## [2026-02-25T13:43:32Z] PIVOT: Downshift smoke validation load to minimal fast-path while preserving upgraded code paths
- Trigger: First post-patch smoke (`ap-DlLAI2RQ3olafiRz2wYSUn`) remained long-running because it unintentionally used heavy defaults (`truthfulqa_samples=30`) despite being implementation-only validation.
- Original approach: Validate schema/gate wiring with full default evaluator loads.
- New approach: Run a reduced-sample smoke (`truthfulqa_samples=2`, same strict parser/split/gate/control features) to verify wiring quickly, then reserve heavy settings for primary tranche.
- Rationale: Implementation validation should minimize unnecessary runtime while still executing every critical code path.
- Impact: Initial smoke marked partial/stopped; new minimal smoke launch scheduled before primary tranche go/no-go.

## [2026-02-25T14:11:52Z] PIVOT: Enforce cross-rater/test alignment and primary-first launch safety
- Trigger: External reviewer found remaining prelaunch risk that `cross_rater_samples` exceeded `test_prompts` in v9 plan artifacts and warned against launching full multi-phase matrix before primary evidence review.
- Original approach: Allow `cross_rater_samples` to exceed `test_prompts` and silently cap calibration rows via `min(...)`; planner default launch script could include non-primary phases depending on flags.
- New approach:
  - Hard-fail when `cross_rater_samples > test_prompts` in both runner/planner.
  - Align default `cross_rater_samples` to 20 (matching default test prompts).
  - Add planner launch-script phase filter defaulting to `primary`.
  - Regenerate plan artifact with primary-only jobs (`week2_upgrade_parallel_plan_20260225T141045Z.json`).
- Rationale: Silent truncation can mask calibration design drift; primary-first sequencing reduces blast radius while prelaunch robustness gaps remain unresolved.
- Impact: Primary tranche commands are now explicit 3-job launch set with bounded calibration sampling; replication/stress remain deferred until primary gates are reviewed.

## [2026-02-25T15:11:21Z] DECISION: Freeze run-launch surface and enforce monitor-only handoff while primary tranche is in-flight
- Trigger: User requested robust cross-session handoff so a new agent does not relaunch, overwrite, or misalign active Week 2 primary work.
- Original approach: Track run launch metadata in scratch/current-state, but without an explicit monitor-only protocol block.
- New approach: Add explicit do-not-relaunch guardrails with canonical app IDs, resume commands, and completion-order requirements in `CURRENT_STATE.md` and `SCRATCHPAD.md`.
- Rationale: Prevent duplicated expensive runs and preserve clean causal interpretation of primary-tranche results.
- Impact: Next session can resume deterministically from active app IDs, collect terminal artifacts, then proceed to post-primary validation tasks without re-execution.
