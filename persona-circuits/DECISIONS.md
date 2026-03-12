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

## [2026-02-25T09:12:38-0600] DECISION: Defer narrative-arc/trope/meme follow-up to a post-core extension and formalize implementation blueprint
- Trigger: User requested a sequencing decision for narrative-arc/trope/meme work and asked for a full implementation document that does not disrupt active Week 2 runs.
- Original approach: Potentially run a Week 2.5 exploratory tranche before core causal pipeline completion.
- New approach: Keep Week 2 focused on v9 primary closeout and place narrative/trope/meme work in a new post-core extension blueprint (`history/20260225-post-core-extension-narrative-arcs-tropes-memes.md`) that executes only after core phases are complete.
- Rationale: Core preregistered claims are currently bottlenecked on reliability/causal milestones; early semantic exploration risks scope drift and weaker causal interpretability.
- Impact: Added a dedicated extension spec with goals, hypothesis framing, implementation stages, controls, metrics, traceability extension rows, and integration details for later execution.

## [2026-02-25T15:23:54Z] PIVOT: Execute review-feedback hardening tasks that do not require new Modal launches
- Trigger: User requested action on external review while Week 2 primary tranche remains in-flight under a strict no-relaunch guardrail.
- Original approach: Keep session in pure monitor mode until primary apps become terminal.
- New approach: Implement only launch-independent work in parallel: (1) add extraction-time cross-trait cosine diagnostics, (2) add norm-aware layer diagnostics to reduce projection-margin confound risk, (3) add targeted unit tests for parser/split/ranking utilities, (4) generate a local vector-diagnostics artifact from existing Stage 1 vectors.
- Rationale: These changes improve implementation validity and methodological transparency immediately without altering or competing with active primary jobs.
- Impact: Added `scripts/week2_vector_diagnostics.py`, expanded diagnostics in `scripts/week2_extract_persona_vectors.py`, added tests `tests/test_week2_extract_vector_utils.py` and `tests/test_week2_validation_utils.py`, and produced `results/stage1_extraction/week2_vector_diagnostics_20260225T152342Z.json`.

## [2026-02-25T16:03:45Z] PIVOT: Advance review-requested pre-primary hardening in local/offline lane while primary Modal apps stay in-flight
- Trigger: User explicitly requested continuing all feasible review-driven work before primary evidence arrives, without violating no-relaunch guardrail.
- Original approach: Wait in monitor mode for primary terminal states before additional substantive work.
- New approach: Execute only launch-independent tasks now: evil trait validity audit, SAE reconstruction pre-audit, extraction-free evaluation set preparation, held-out expansion planning, and deeper unit tests for steering/retry/scaling utilities.
- Rationale: Improves methodological rigor and implementation confidence immediately while preserving clean interpretation of in-flight primary runs.
- Impact: Added scripts `week2_evil_trait_audit.py`, `week3_sae_reconstruction_audit.py`, `week2_prepare_extraction_free_eval.py`, `week2_heldout_expansion_plan.py`; extended `generate_week2_heldout_prompts.py` with scaling/dry-run plan mode; added test coverage and generated new pre-primary artifacts in `results/stage1_extraction/` and `results/stage2_decomposition/`.

## [2026-02-25T17:30:00-0600] DECISION: Formalize evil trait keep/replace rubric
- Trigger: Prelaunch gap checks and the recent evil-trait audit both flag the current directional delta as negative, the method similarity gate as failing, and refusal-invariance as dominant, so we need an explicit keep/replace rubric before the primary tranche closes.
- Original approach: Treat the current evil vector as provisionally actionable and defer any structural decision until after the remaining Stage 1 primary runs finish, without a documented list of acceptance thresholds.
- New approach: Adopt a formal rubric (thresholds below) driven by the latest artifacts and persona-vector literature; the rubric documents what “known” evidence supports keeping the vector, what gaps trigger replacement/re-extraction, and how to time the decision.
- Thresholds:
  1. External transfer directional gate—only keep the vector if `external_transfer.plus_vs_minus >= 8.0`, `bidirectional_effect > 0`, and `external_transfer.pass` is true (the same gate used in `week2_prelaunch_gap_checks_20260225T131521Z.json`).
  2. Extraction agreement gate—keep only when `extraction_method_ab.method_similarity >= 0.7` (the `method_similarity_pass_ge_0_7` flag from the same artifact) so we know the vector is not a one-off spike.
  3. Manual concordance gate—keep only if `manual_concordance_sample_stats_evil.plus_minus_abs_diff_mean >= 15` and `refusal_triplet_all_true_rate <= 0.2`, ensuring the vector produces substantial harm scoring differences without merely flipping refusal tokens (per the Chen et al. persona construct, see evidence table below).
  Otherwise, schedule a replacement extraction/validation pass and do not promote the vector to Stage 2.
- Evidence table:
  | Evidence | Source | Status | Notes |
  | --- | --- | --- | --- |
  | Negative `external_transfer.plus_vs_minus` (-0.75) and `bidirectional_effect` in `week2_prelaunch_gap_checks_20260225T131521Z.json`; gate requires ≥8.0 | `results/stage1_extraction/week2_prelaunch_gap_checks_20260225T131521Z.json` | known | Reports show `pass=false` despite using CLI-selected `(L16, α=3.0)` combo. |
  | Extraction method similarity 0.592 < 0.7 (and flag `method_similarity_pass_ge_0_7=false`) in the same artifact | `results/stage1_extraction/week2_prelaunch_gap_checks_20260225T131521Z.json` | known | We do not yet have a directionally consistent SAE match. |
  | Manual sample statistics show `plus_minus_abs_diff_mean=0.0` and `refusal_triplet_all_true_rate=0.8` | `results/stage1_extraction/week2_evil_trait_audit_20260225T160326Z.json` | known | Even the curated harmful prompts refuse symmetrically across plus/minus; no meaningful score shift. |
  | Evil audit risk flags (external bidirectional nonpositive, manual score/refusal invariance, similarity fail) and severity=high | `results/stage1_extraction/week2_evil_trait_audit_20260225T160326Z.json` | known | Six flags recommend treating the vector as provisional. |
  | Chen et al. definition of “evil” as clear harmful intent/manipulation and the expectation of stark plus/minus differences in judge scores | `background-work/papers/chen2025_persona_vectors.md:2810-2815` | known | The persona literature requires a differentiated behavioral shift rather than uniform refusal. |
  | Wang et al. misalignment thresholds (alignment ≤ 30, coherence ≥ 50) for declaring the “evil” prompt set misaligned | `background-work/papers/wang2025_emergent_misalignment.md:994-1006` | known | Provides a benchmark for what counts as malicious output in judge evaluations. |
  | Negative delta + high refusal-invariance imply the current direction is reacting to refusal tone, not harm-seeking behavior | combination of artifacts above | inferred | By inference, the vector is likely capturing refusal compliance rather than a causal evil circuit. |
  | Terminal primary-run outcomes (app IDs `ap-kqV4eWSGwrVt8nKE4ZA3NF`, `ap-SAFulvrYqaddpusCHafEzB`, `ap-Ae34zytuXoYv11ksGBM5XH`) and their post-run artifacts | currently in-flight | unknown | No gate data yet; must be observed before final decision. |
- Recommended decision timing: Do not finalize keep/replace until the three primary apps reach terminal states, their artifacts capture final quality gates, and a fresh prelaunch-gap check (external transfer + extraction A/B) on the final combos passes; once those outputs exist, rerun this rubric, follow the `post-run` SCRATCHPAD checklist, and then decide.
- Rationale: The vector currently violates all three rubric thresholds, the audit flags are high severity, and the persona literature (Chen et al., Wang et al.) insists on measurable plus/minus separation; a documented rubric prevents ad-hoc justification while the primary tranche is still unresolved.
- Impact: Evil-trait evaluation stays in monitor-only mode until final artifacts arrive, we know exactly what “passing” evidence looks like, and any next run must produce a new vector that satisfies this rubric or explicitly document why the thresholds were relaxed.

## [2026-02-25T10:44:08-0600] PIVOT: Move from pre-audit documentation to execution-grade pre-primary fixes
- Trigger: External hardening review identified that prior tranche outputs were mostly planning/pre-audit artifacts and requested substantive execution work before primary evidence lands.
- Original approach: Keep producing non-execution audit artifacts (taxonomy/pre-audit/plan files) while waiting for primary jobs.
- New approach: Implement and validate execution-grade fixes in parallel-safe lanes: (1) upgraded evil refusal profiling with mixed refusal+compliance detection, (2) rotating extraction-free exemplar-set generation with non-overwriting prompt outputs, (3) concrete extraction-free activation evaluation runner, and (4) modal reconstruction investigation script that directly measures base-vs-instruct reconstruction under the same SAE/hook.
- Rationale: This closes high-priority review gaps without violating the no-primary-relaunch guardrail, and produces falsifiable evidence rather than only restating known issues.
- Impact:
  - Added `scripts/week2_extraction_free_activation_eval.py` and `scripts/week3_sae_reconstruction_investigation.py`.
  - Upgraded `scripts/week2_evil_trait_audit.py` refusal logic to full-response profiling and emitted refreshed artifact `results/stage1_extraction/week2_evil_trait_audit_20260225T163523Z.json`.
  - Regenerated extraction-free manifest with rotating sets and versioned prompt files: `results/stage1_extraction/week2_extraction_free_prompt_manifest_20260225T163517Z.json` + `prompts/heldout/*_extraction_free_eval_v2_rotating_20260225.jsonl`.
  - Ran modal reconstruction investigation (`ap-Q9eYKHJZbbY2FCW9Wha3eg`), producing `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260225T164322Z.json` (both models fail with near-identical low cosine; explained variance strongly negative).

## [2026-02-25T11:08:23-0600] DECISION: Replace current `evil` trait for downstream (Week3+) claims
- Trigger: Independent evidence streams converge on zero behavioral differentiation and failed robustness for the current `evil` vector:
  - `known`: external transfer gate fail with `plus_vs_minus=-0.75`, `bidirectional_effect<=0` (`week2_prelaunch_gap_checks_20260225T131521Z.json`).
  - `known`: extraction-method similarity fail (`0.592 < 0.7`) on same artifact.
  - `known`: manual concordance invariance (`score_triplet_exact_match_rate=1.0`, `plus_minus_abs_diff_mean=0.0`) in evil audit (`week2_evil_trait_audit_20260225T163523Z.json`).
  - `inferred`: additional data on this exact vector has low expected information value for causal interpretation.
- Original approach: Keep `evil` as a live Week3 decomposition target, pending in-flight primary outcomes.
- New approach:
  1. Mark the current `evil` vector as disconfirmed for persona-circuit claims.
  2. Allow currently in-flight primary app `ap-SAFulvrYqaddpusCHafEzB` to finish for traceability only.
  3. Do not launch any new runs that treat this `evil` vector as a candidate for Week3+ decomposition/circuit claims.
  4. Open a replacement trait lane (`manipulativeness` / non-safety-blocked Machiavellian social-control framing) after primary terminalization and post-run documentation.
- Rationale: All preregistered-style validity gates relevant to trait viability are currently failing in the same direction, with no observed bidirectional effect; continuing as if viable would inflate false-positive risk.
- Impact:
  - Week3 decomposition scope updates from `{sycophancy, evil, hallucination}` to `{sycophancy, hallucination}` until replacement-trait Stage1 is completed.
  - `evil` remains in results as a negative finding (explicit disconfirmation), not a dropped/hidden run.

## [2026-02-25T11:10:54-0600] PIVOT: Treat token-level reconstruction as the relevant Stage2 reliability gate
- Trigger: Root-cause probe artifact `week3_sae_reconstruction_root_cause_20260225T170255Z.json` showed that reconstruction quality is highly path-dependent:
  - `known`: full-sequence path (`raw_seq`) remains catastrophic.
  - `known`: token-level path (`last_token`) yields much stronger reconstruction (`median_cos~0.82/0.77`, positive EV) on both base and instruct models.
- Original approach: Interpret catastrophic full-sequence reconstruction as a global Stage2 SAE failure mode.
- New approach: Align reconstruction reliability checks with the extraction target path (token-level activations), and treat full-sequence flatten metrics as a separate stress diagnostic rather than the primary gate.
- Rationale: Stage1 persona extraction and steering use token-level representations; reliability gating should measure the same object to avoid category errors.
- Impact:
  - Stage2 go/no-go diagnostics now prioritize token-level reconstruction reruns at larger sample sizes.
  - Existing catastrophic full-sequence findings remain logged as an implementation/pathology warning, not discarded.

## [2026-02-25T11:40:16-0600] DECISION: Treat extraction-free activation result as disconfirming evidence for current Week 3 persona-selection interpretation
- Trigger: Completed Modal extraction-free activation eval (`ap-ueBHf5QMX2Vb45ROBxySK5`) produced artifact `week2_extraction_free_activation_eval_20260225T173752Z.json` with `overall_pass=false`.
- Original approach: Keep extraction-free validation as an open pending action before Week 3 interpretation.
- New approach:
  1. Mark extraction-free validation as executed and currently failing.
  2. Do not use this artifact as positive support for "persona selection beyond explicit system instruction."
  3. Open a dedicated remediation lane (diagnose low cosine alignment + high set-variance ratio) before making Week 3 interpretation claims.
- Evidence:
  - `known`: all traits fail `mean_cosine`; all traits fail `set_std_ratio`.
  - `known`: hallucination additionally fails `positive_fraction` and `projection_delta`.
  - `inferred`: instruction-conditioned vectors and extraction-free few-shot deltas are not currently aligned under the present setup.
  - `unknown`: exact cause split between extraction-method sensitivity vs genuine regime mismatch.
- Rationale: Pre-registered interpretation quality requires explicit evidence for persona signal beyond direct system instruction; this run currently fails that burden.
- Impact:
  - Week 3 interpretation language must stay conservative until remediation is completed.
  - Added follow-up action to THOUGHT_LOG pending queue for extraction-free diagnostics/remediation.

## [2026-02-25T11:50:12-0600] PIVOT: Recalibrate extraction-free overlap gates from binary strictness to trait-gradient overlap policy
- Trigger: Reanalysis of `week2_extraction_free_activation_eval_20260225T173752Z.json` showed highly consistent positive overlap for sycophancy/evil but near-null overlap for hallucination, while the initial gate suite (`mean_cosine>=0.4`, legacy `set_std_ratio<=0.8`) collapsed this into a single global fail.
- Original approach: Use a high overlap threshold (`0.4`) and within-set dispersion ratio (`max set std / global std`) as hard required gates for all traits.
- New approach:
  1. Lower overlap threshold to a weak-overlap floor (`mean_cosine>=0.1`) for cross-induction comparability.
  2. Replace required set-variance gate with between-set mean divergence (`set_mean_cv<=0.8`).
  3. Keep legacy `set_std_ratio` as diagnostic only (not required).
  4. Add significance diagnostics (exact sign test, zero-mean t-stat normal approximation, bootstrap mean CI).
- Rationale: Cross-method overlap should detect directional consistency above chance, not parity with explicit system instruction strength; between-set mean divergence is the relevant confound signal for exemplar-set dependence.
- Impact:
  - Updated scripts: `scripts/week2_extraction_free_activation_eval.py`, `scripts/week2_extraction_free_activation_eval_modal.py`.
  - Added reanalysis script: `scripts/week2_extraction_free_reanalysis.py`.
  - Generated artifact: `results/stage1_extraction/week2_extraction_free_reanalysis_20260225T174958Z.json`.

## [2026-02-25T11:50:12-0600] DECISION: Reopen "evil" as a Week 3 candidate under a Machiavellian-disposition framing
- Trigger: Reanalysis artifact `week2_extraction_free_reanalysis_20260225T174958Z.json` shows `evil` has the strongest cross-induction alignment (`mean_cosine=0.223`, `positive_fraction=1.0`, `sign_test_p~1.8e-15`, `set_mean_cv=0.234`), while harmful-content external transfer remains failed.
- Original approach: Fully replace the current evil vector for Week3+ claims due harmful transfer failures.
- New approach:
  1. Keep harmful-content claims disconfirmed for this vector.
  2. Reframe trait axis as `Machiavellian/manipulative disposition` (workplace/social-control framing) for decomposition candidacy.
  3. Treat harmful-content external transfer gate as non-diagnostic for this reframed axis; use axis-matched behavioral checks instead.
  4. Maintain traceability of the earlier negative harmful-transfer evidence in reporting.
- Rationale: Current evidence separates two axes: refusal-bound harmful content (failed) vs manipulative-disposition behavior (cross-method overlap positive). Collapsing both into one "evil" label obscures the actual measured construct.
- Impact:
  - Week3 candidate set is provisionally `{sycophancy, machiavellian_disposition, hallucination(control)}` pending primary post-run closeout tasks.
  - Reporting language must explicitly distinguish harmful-content failure from manipulative-disposition overlap evidence.

## [2026-02-25T11:56:28-0600] CLARIFICATION: Scope supersession for prior `evil` replacement decision
- Trigger: Documentation review found active ambiguity between the earlier replacement decision (`2026-02-25T11:08:23-0600`) and the later reframed reinstatement decision (`2026-02-25T11:50:12-0600`).
- Clarification:
  1. `2026-02-25T11:50:12-0600` supersedes the Week 3 scope component of `2026-02-25T11:08:23-0600`.
  2. The harmful-content negative finding from `2026-02-25T11:08:23-0600` remains valid and is not withdrawn.
  3. The active interpretation is axis-split:
     - harmful-content "evil" behavior: disconfirmed for this vector,
     - machiavellian/manipulative disposition: retained as a decomposition candidate pending primary closeout checks.
- Impact: CURRENT_STATE/THOUGHT_LOG scope notes and pending actions were aligned to remove conflicting instructions.

## [2026-02-25T12:05:13-0600] PIVOT: Make Week 2 alpha sweep config-authoritative
- Trigger: Reviewer identified mismatch between proposal/config steering coefficients and hardcoded runner defaults (`config: 0.5..3.0` vs runner hardcoded `0.25..4.0`).
- Original approach: If `--alpha-grid` was omitted, upgraded runner defaulted to a hardcoded local constant.
- New approach: Default alpha grid now loads from `configs/experiment.yaml -> steering.coefficients`; CLI override remains supported for explicit experiments.
- Rationale: Keeps one source-of-truth for sweep bounds and aligns Week 2 execution behavior with proposal/config governance.
- Impact:
  - Updated `scripts/week2_behavioral_validation_upgrade.py` (`_alpha_grid_from_config`).
  - Added tests in `tests/test_week2_validation_utils.py`.

## [2026-02-25T12:05:13-0600] PIVOT: Wire config seed schedules into Week 3 reconstruction scripts
- Trigger: Reviewer flagged that replication seeds defined in config were not consumed by Week 3 reconstruction scripts.
- Original approach: Week 3 scripts accepted a single seed (default 42), with no native schedule consumption.
- New approach:
  1. Added config-aware seed schedule resolution (`primary + replication`) when no explicit seed override is given.
  2. Added optional CSV seed-schedule override.
  3. Added multi-seed report wrappers + seed aggregate summaries for investigation/root-cause scripts.
- Rationale: Makes Week 3 probe runs reproducible and replication-aware without requiring manual orchestration logic.
- Impact:
  - Updated `scripts/week3_sae_reconstruction_investigation.py`.
  - Updated `scripts/week3_sae_reconstruction_root_cause.py`.
  - Added helper tests in `tests/test_week3_reconstruction_utils.py`.

## [2026-02-25T12:05:13-0600] PIVOT: Replace Stage 2 audit placeholders with computed readiness checks and add Stage 3/4 dry-run scaffold
- Trigger: Reviewer flagged that Stage 2 audit still emitted hardcoded `pending` checks and that Stage 3/4 execution path lacked concrete local scaffolding.
- Original approach: Audit script relabeled historical infra values and listed pending checks without evaluating latest probe artifacts.
- New approach:
  1. Rewrote audit to compute pass/fail/unknown checks from latest investigation + root-cause artifacts.
  2. Added explicit `stage2_readiness_gate` with required check statuses.
  3. Added reusable metrics module for concentration/effect-size/selectivity (`circuit_metrics.py`).
  4. Added dry-run Stage 3/4 pipeline scaffold script with artifact schema and synthetic metric demo.
- Rationale: Converts Stage 2 validation from narrative placeholders into machine-evaluated gates and unblocks local implementation work for Stage 3/4 without launching remote jobs.
- Impact:
  - Replaced `scripts/week3_sae_reconstruction_audit.py` with computed-gate implementation.
  - Added `scripts/circuit_metrics.py`.
  - Added `scripts/week3_stage34_pipeline_scaffold.py`.
  - Produced artifacts:
    - `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T180446Z.json`
    - `results/stage3_attribution/week3_stage34_pipeline_scaffold_20260225T180446Z.json`

## [2026-02-25T12:20:49-0600] PIVOT: Resolve Stage2 cross-source overlap precondition by configuring overlap-capable andyrdt layers
- Trigger: Latest computed Stage2 audit failed only on cross-source overlap precondition (`overlap_crosscheck_vs_steering_layers=[]`) while token-level reconstruction and hook-integrity checks already passed.
- Original approach: Keep cross-check layers at `[19, 23]`, which have no overlap with current steering layer window `[11..16]`.
- New approach:
  1. Update config cross-check layer list to include overlap-capable layers from the same andyrdt release: `[11, 15, 19, 23]`.
  2. Re-run computed Stage2 audit locally to verify precondition state.
- Rationale: The blocker was a configuration precondition mismatch, not a measured reconstruction failure. Adding overlap-capable layers enables cross-source agreement checks in the same steering window without launching new primary jobs.
- Impact:
  - Updated `configs/experiment.yaml` (`sae.cross_check.layers`).
  - New audit artifact: `results/stage2_decomposition/week3_sae_reconstruction_audit_20260225T181955Z.json` (`stage2_readiness_gate=pass`).

## [2026-02-25T12:20:49-0600] DECISION: Add a post-run ingestion script with apply-mode doc updates and preflight-safe partial mode
- Trigger: Pre-primary hardening checklist required immediate closeout once the three in-flight primaries terminalize: parse artifacts, compute §6.2.3 gate outcomes, and update `RESULTS_INDEX.md` + `CURRENT_STATE.md`.
- Original approach: Manual post-run closeout steps described in prose and scratchpad checklist.
- New approach:
  1. Add `scripts/week2_primary_postrun_ingest.py` to ingest primary artifacts per trait, compute §6.2.3 gate outcomes, and emit a timestamped summary artifact.
  2. Default to non-destructive mode; require explicit `--apply` to update `results/RESULTS_INDEX.md` and `CURRENT_STATE.md`.
  3. Support `--allow-partial` preflight while primaries are still in-flight.
- Rationale: Reduces manual closeout latency and transcription risk at terminalization while preserving guardrails (no auto-doc mutation without explicit apply and all three artifacts present).
- Impact:
  - Added script: `scripts/week2_primary_postrun_ingest.py`.
  - Added tests: `tests/test_week2_primary_postrun_ingest.py`.
  - Preflight artifact (partial by design while primaries active): `results/stage1_extraction/week2_primary_postrun_ingestion_20260225T182017Z.json`.

## [2026-02-25T12:28:12-0600] PIVOT: Enforce deterministic post-run ingestion option with explicit trait artifact map
- Trigger: Reviewer caveat requested deterministic ingestion with explicit trait artifact mapping instead of latest-file fallback.
- Original approach: Ingestion script defaulted to latest trait artifacts when mapping was omitted.
- New approach:
  1. Add `--require-artifact-map` flag to enforce explicit mapping for all three traits (`sycophancy`, `evil`, `hallucination`).
  2. Keep latest-file fallback for non-strict preflight mode.
  3. Update `CURRENT_STATE.md` handoff/next-action commands to use explicit-map deterministic mode for terminalization.
- Rationale: Eliminates ambiguity/race risk at closeout when multiple artifacts per trait may exist.
- Impact:
  - Updated `scripts/week2_primary_postrun_ingest.py`.
  - Expanded `tests/test_week2_primary_postrun_ingest.py`.

## [2026-02-26T13:30:27-0600] PIVOT: Increase Week2 primary timeout and add granular progress checkpoint logging before rerun
- Trigger: All three latest primary runs (`ty3k95jg`, `1gjwij50`, `4qdhwpfu`) reached terminal `finished` states with cancellation signals near the 10h function cap and without final selection/gate summary fields.
- Original approach: Week2 upgraded validator used a fixed 10h Modal timeout and sparse stage-level logs, making long-run stall vs timeout diagnosis ambiguous.
- New approach:
  1. Make Week2 Modal timeout configurable from `configs/experiment.yaml` runtime section (`runtime.week2_behavioral_validation_upgrade.modal_timeout_hours`) with env override support (`WEEK2_UPGRADE_MODAL_TIMEOUT_HOURS`), and set runtime config to 20h.
  2. Add structured `emit_progress(...)` checkpoints across baseline, sweep, confirm, calibration, controls, coherence, cross-trait bleed, capability, TruthfulQA, and finalization stages.
  3. Persist progress in both Modal stdout and W&B (summary + numeric progress metrics).
  4. Add a guarded detached rerun command set script: `scratch/week2_upgrade_rerun_commands_20260226.sh`.
- Rationale: Raises likelihood that primaries reach final artifact write and makes in-flight diagnosis observable in real time rather than inferred post-timeout.
- Impact:
  - Updated `scripts/week2_behavioral_validation_upgrade.py`.
  - Updated `configs/experiment.yaml` runtime section.
  - Added `scratch/week2_upgrade_rerun_commands_20260226.sh`.

## [2026-02-26T13:43:39-0600] PIVOT: Use per-trait detached TTY launch instead of sequential launcher shell for Week2 rerun tranche
- Trigger: `scratch/week2_upgrade_rerun_commands_20260226.sh` executed sequential `modal run -d ...` local entrypoint calls that still block until remote completion, preventing immediate parallel launch of all three traits.
- Original approach: one shell script invoking three sequential detached local-entrypoint commands.
- New approach:
  1. Launch sycophancy first via guarded script.
  2. Launch evil/hallucination with direct detached per-trait commands using TTY sessions.
  3. Interrupt local clients after app creation (`^C`) so detached Modal apps continue independently.
- Rationale: Achieves true parallel in-flight trait runs while preserving launch safety and observability.
- Impact:
  - Active rerun app IDs: `ap-kUx2doeoy9vvaH4es6Fpi7`, `ap-9i5FMKW3ZL1mOm3TRGDvhx`, `ap-zoT1TUKLBYfbGSGqNqpFTU`.
  - Active W&B runs: `ccgxgpk3`, `ok616mrn`, `s7ieih7y`.

## [2026-02-26T14:04:57-0600] PIVOT: prioritize resumability + incremental local checkpoint pulls before full rerun
- Trigger: user requested to stop long-running reruns and avoid end-of-run-only observability/data capture risk.
- Original approach: run full 3-trait reruns end-to-end and rely on final artifact write + W&B telemetry.
- New approach:
  1. Add checkpoint persistence/resume at major stages in `week2_behavioral_validation_upgrade.py`.
  2. Add explicit checkpoint identity/cadence controls (`--checkpoint-key`, write cadence flags) to make resumed reruns deterministic.
  3. Add remote checkpoint fetch mode + local pull script so in-flight state is copied to `results/stage1_extraction/checkpoints/` during execution.
- Rationale: reduces expected wasted compute/API usage on interruptions and creates near-real-time recoverability/traceability independent of final artifact completion.
- Impact:
  - Week2 rerun app IDs `ap-kUx2doeoy9vvaH4es6Fpi7`, `ap-9i5FMKW3ZL1mOm3TRGDvhx`, `ap-zoT1TUKLBYfbGSGqNqpFTU` were intentionally stopped.
  - Relaunch commands now include checkpoint controls in `scratch/week2_upgrade_rerun_commands_20260226.sh`.
  - Pull helper added: `scratch/week2_pull_live_checkpoints_20260226.sh`.

## [2026-02-26T14:18:21-0600] PIVOT: enforce Modal volume commit/reload for in-flight checkpoint visibility and make 3-trait launch non-blocking
- Trigger: second readiness pass reproduced two reliability hazards:
  1. checkpoint files remained absent after stopped reruns despite checkpoint-write calls;
  2. `modal run -d` local entrypoint client can block for long durations, preventing single-shell parallel launch.
- Original approach:
  - checkpoint writes relied on file writes only (no explicit Modal volume commit/reload).
  - launcher invoked three sequential `modal run -d` calls in one shell.
- New approach:
  1. Add `vol.commit()` after checkpoint writes and `vol.reload()` before checkpoint reads/fetch.
  2. Launch per-trait rerun commands via `nohup ... &` with per-trait log/pid capture so all three launch clients start in parallel without blocking the parent shell.
  3. Add optional pull watch mode (`WATCH=1`) for periodic local checkpoint snapshots.
- Rationale: guarantees checkpoint state becomes externally readable during execution and removes known launch-client blocking risk that previously required manual TTY interruption.
- Impact:
  - Updated `scripts/week2_behavioral_validation_upgrade.py` and `scratch/week2_upgrade_rerun_commands_20260226.sh` and `scratch/week2_pull_live_checkpoints_20260226.sh`.
  - Full local tests remain green (`62 passed`).

## [2026-02-26T14:28:47-0600] PIVOT: replace background batch-launch attempt with explicit per-trait detached launches
- Trigger: initial `RUN=1` launcher background batch created three new week2 apps with `Tasks=0`, indicating idle/non-executing state for launch attempt (non-terminal but not running payload).
- Original approach: single `RUN=1 bash scratch/week2_upgrade_rerun_commands_20260226.sh` invocation with internal background launch clients.
- New approach:
  1. Stop the idle apps from the failed launch attempt.
  2. Relaunch each trait explicitly with full arg set via `modal run -d ... --trait <trait> --checkpoint-key <key>`.
  3. Confirm each app reaches `ephemeral(detached)` with `Tasks=1` before declaring launch success.
  4. Start checkpoint pull watcher loop in background for incremental local sync.
- Rationale: ensures we only treat launch as successful when each trait has an active task, not merely a created app shell.
- Impact:
  - Active run app IDs: `ap-zPUs3Y8gIuLv0iOBvIbKMl` (sycophancy), `ap-TWjaeZTPuTCH8T2jBnLWCd` (evil), `ap-s5mJbgdlhCwCod8Rxw1H9M` (hallucination).
  - Watcher log: `scratch/launch_logs/checkpoint_pull_watch_20260226T142803Z.log`.

## [2026-02-27T14:53:37-0600] PIVOT: Complete Week2 post-primary closeout checks before any replication/stress launch (manual concordance + selected-combo gap rerun)
- Trigger: all three primary reruns terminalized and deterministic ingestion completed, but closeout checklist still required manual concordance and post-primary gap-check rerun.
- Original approach: closeout state captured through ingestion only, with remaining checks deferred.
- New approach:
  1. Add a reproducible manual concordance utility (`scripts/week2_primary_manual_concordance.py`) and execute deterministic 5-example/trait scoring on primary `selected_test_evaluation` rows.
  2. Re-run `scripts/week2_prelaunch_gap_checks.py` with explicit primary-selected combos (`sycophancy:12:3.0, evil:12:3.0, hallucination:13:3.0`).
  3. Update state/index docs immediately after artifacts are written.
- Rationale: satisfies the explicit post-terminal checklist and removes ambiguity before any launch decision.
- Impact:
  - Manual concordance artifact: `results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json` (`mean_trait_mae=4.744`, guideline pass).
  - Gap-check artifact: `results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json` (`overall_pass=false`; extraction A/B robustness fails all traits).
  - Replication/stress remains blocked pending explicit go/no-go decision against these gate outcomes.

## [2026-02-27T15:31:15-0600] DECISION: Week 2 closeout is NO-GO for replication/stress launches under current gate policy
- Trigger: Post-terminal closeout checklist is complete (deterministic ingestion + manual concordance + post-primary selected-combo gap checks), and evidence still shows unresolved robustness failures.
- Original approach: After primary terminalization, consider progressing to replication/stress if closeout checks were complete.
- New approach:
  1. Set Week 2 closeout verdict to `NO-GO` for replication/stress launch.
  2. Freeze current primary evidence as the Week 2 closeout snapshot (do not relaunch broad replication/stress now).
  3. Allow only a minimal remediation lane before any new launch decision: (a) extraction-method robustness A/B remediation, (b) evil directional-reversal criterion remediation or explicit trait-framing gate update.
- Evidence status summary:
  - `known`: Ingestion summary artifact shows `section623_all_pass=false` and `runner_overall_all_pass=false` (`results/stage1_extraction/week2_primary_postrun_ingestion_20260227T202336Z.json`).
  - `known`: Manual concordance spot-check passes guideline threshold (`mean_trait_mae=4.744`, 15 evaluated examples) (`results/stage1_extraction/week2_primary_manual_concordance_ratings_20260227T202822Z.json`).
  - `known`: Post-primary gap checks fail overall (`overall_pass=false`) with all-trait extraction A/B similarity failures and evil external-transfer directional failure (`results/stage1_extraction/week2_prelaunch_gap_checks_20260227T205237Z.json`).
  - `inferred`: Launching replication/stress before resolving method-sensitivity and directional-gate failures would increase cost while preserving the primary validity confounds.
  - `unknown`: Whether a minimal remediation tranche can raise extraction A/B similarity to threshold without degrading behavioral effects.
- Rationale: Week 2 reliability gates are not yet met under the current preregistered-style closeout policy; proceeding directly to replication/stress would be methodologically weak.
- Impact:
  - Replication/stress launch is explicitly blocked as of this decision.
  - Next launch decision requires a new decision entry referencing remediation outcomes and updated gate status.

## [2026-02-27T15:32:52-0600] DECISION: Lock reviewer reconciliation workflow before remediation runs (verbatim logs + master plan + completion checklist)
- Trigger: User provided two additional detailed reviewer critiques and requested reconciliation planning before any further end-to-end fixes.
- Original approach: Proceed with ad-hoc remediation planning from summarized reviewer claims.
- New approach:
  1. Log both reviewer comments verbatim in immutable files under `history/reviews/`.
  2. Create a single remediation master plan covering all findings and execution order.
  3. Create an explicit one-to-one reviewer finding checklist that must be audited at remediation end.
  4. Keep Week 2 `NO-GO` launch status in force until checklist-critical items are no longer pending and a superseding decision is logged.
- Rationale: Prevents omission/interpretation drift and gives a deterministic "did we miss anything?" mechanism at closeout.
- Impact:
  - Added verbatim logs:
    - `history/reviews/20260227-reviewer1-verbatim.md`
    - `history/reviews/20260227-reviewer2-verbatim.md`
  - Added remediation plan:
    - `history/20260227-week2-remediation-master-plan-v1.md`
  - Added reconciliation checklist:
    - `history/20260227-reviewer-reconciliation-checklist-v1.md`

## [2026-02-27T16:19:49-0600] DECISION: Freeze Week 2 remediation governance on dual-scorecard reporting (proposal-compatibility + hardening-reliability)
- Trigger: Reviewer reconciliation highlighted governance-drift risk between proposal Week 2 continuation criteria and stricter hardening gates.
- Original approach: Single-scorecard closeout summaries mixed proposal semantics with upgraded runner gate outcomes.
- New approach:
  1. Add config-anchored governance policy section (`governance.week2_remediation_policy_v1`) in `configs/experiment.yaml`.
  2. Emit both scorecards in ingestion artifacts:
     - `proposal_compatibility` (proposal continuation semantics),
     - `hardening_reliability` (strict upgraded runner semantics).
  3. Require explicit disagreement reporting before any superseding launch decision.
- Evidence status summary:
  - `known`: Updated ingestion artifact reports scorecard disagreement (`proposal_continue=true`, `hardening_runner_all=false`, `scorecard_disagreement=true`) at `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json`.
  - `known`: Ingestion implementation now computes scorecards from frozen config policy (`scripts/week2_primary_postrun_ingest.py`).
  - `inferred`: dual-scorecard output reduces interpretation drift risk but does not itself resolve failing reliability gates.
- Rationale: Preserve prereg comparability while keeping hardening signal visible, without silently moving goalposts.
- Impact:
  - WS-A governance-freeze deliverable is implemented.
  - Future closeout decisions must cite both scorecards and rationale for any mismatch.

## [2026-02-27T16:19:49-0600] PIVOT: Make extraction-position ablation remote-safe by passing prompt rows as payload
- Trigger: WS-B first Modal run failed pre-metric with missing prompt path (`/prompts/sycophancy_pairs.jsonl`) because remote container could not access host-local files.
- Original approach: Remote function loaded prompt files from host-derived paths.
- New approach:
  1. Load extraction rows locally in the entrypoint.
  2. Pass `extraction_rows_by_trait` directly into remote function payload.
  3. Keep remote sampling/diagnostic logic unchanged.
- Evidence status summary:
  - `known`: failure app `ap-fqkoMTLnvqOWmd4UGGfc7a` terminated with FileNotFoundError before diagnostics.
  - `known`: rerun app `ap-TpixiBPB3LEILoVRUZiV77` completed successfully after payload patch.
  - `known`: artifact `results/stage1_extraction/week2_extraction_position_ablation_20260227T221817Z.json` now exists and contains per-layer pairwise method cosines.
  - `observed`: prompt-last vs response-mean agreement remains below 0.7 for all traits/layers in this small run (means: sycophancy~0.49, evil~0.48, hallucination~0.34).
- Rationale: Fixes execution-path validity so WS-B diagnostics measure extraction behavior rather than filesystem integration errors.
- Impact:
  - WS-B small-run execution is now unblocked and reproducible.
  - Next WS-B step is full-run/expanded diagnostics for root-cause interpretation depth.

## [2026-02-27T16:53:52-0600] PIVOT: Promote WS-B evidence from small-run to expanded-run before extraction-method policy lock
- Trigger: WS-B small-run showed persistent A/B disagreement but sample size was limited (12 pairs/trait), leaving room for sampling noise in interpretation.
- Original approach: use small-run artifact as provisional WS-B evidence and move immediately into WS-C.
- New approach:
  1. Run expanded extraction-position ablation with `50` pairs/trait and same layer grid (`11..16`).
  2. Reassess whether disagreement is robust and whether it is prompt-vs-response phase specific.
  3. Defer extraction-method policy lock until expanded evidence is logged.
- Evidence status summary:
  - `known`: expanded run app `ap-jE51jRViY2RdepUgmT3Fe4` completed successfully.
  - `known`: artifact `results/stage1_extraction/week2_extraction_position_ablation_20260227T225251Z.json` confirms no trait/layer reaches `prompt_last_vs_response_mean >= 0.7`.
  - `observed`: response-mean vs response-last agreement is high for sycophancy/evil (`~0.75/~0.74`) and low for hallucination (`~0.33`).
  - `inferred`: for sycophancy/evil, disagreement is more likely prompt-vs-response phase driven than purely response-statistic choice (mean vs last); hallucination remains unstable across response variants.
- Rationale: avoids overfitting policy decisions to a small diagnostic sample and strengthens reviewer-facing root-cause evidence.
- Impact:
  - WS-B now has expanded evidence and remains `partial` pending explicit extraction-method policy lock.
  - WS-C implementation can proceed next, with policy note to be finalized in parallel.

## [2026-02-27T16:55:11-0600] PIVOT: Implement constrained confirm-combo selection policy before remediation reruns
- Trigger: Reviewer findings flagged alpha-maximizing selection behavior as a likely oversteer source; WS-C required smallest-feasible-alpha policy before new reruns.
- Original approach: Final combo selection on confirm set ranked by directional feasibility + maximum bidirectional effect.
- New approach:
  1. Add config-driven selection policy `steering.combo_selection_policy` with values:
     - `smallest_feasible_alpha` (default),
     - `max_bidirectional_effect` (fallback-compatible legacy behavior).
  2. Implement `_select_confirm_combo(...)` so default policy picks the smallest alpha among combos meeting directional feasibility and `min_bidirectional_effect`.
  3. Preserve deterministic fallback to max-bidirectional ranking when no combo meets feasibility threshold.
  4. Expose selection-policy metadata in report (`confirm_selection`) and W&B metrics (`selected_confirm_fallback_used`, `selected_confirm_eligible_count`).
- Evidence status summary:
  - `known`: implementation landed in `scripts/week2_behavioral_validation_upgrade.py` and config in `configs/experiment.yaml`.
  - `known`: unit coverage expanded in `tests/test_week2_validation_utils.py` for policy parsing and selection behavior.
  - `known`: full local suite passes (`Ran 74 tests ... OK`).
  - `unknown`: behavioral impact on coherence/capability gates until targeted WS-C reruns are executed.
- Rationale: Moves selection objective from pure effect-maximization toward a working-alpha policy while retaining fallback behavior for sparse-signal regimes.
- Impact:
  - WS-C implementation is now started with code+tests complete.
  - Next step is targeted rerun evidence (alpha 2.0/2.5 lanes) to evaluate oversteer mitigation.

## [2026-02-27T16:59:57-0600] DECISION: Freeze extraction-method policy for WS-C alpha reruns as prompt-last primary (response-mean sensitivity lane deferred)
- Trigger: WS-B expanded diagnostics confirmed persistent prompt-vs-response disagreement (<0.7 on all traits/layers), but WS-C requires isolating alpha-selection effects first.
- Original approach: unresolved whether to switch immediately to response-token extraction before lower-alpha reruns.
- New approach:
  1. For WS-C lower-alpha reruns, keep existing prompt-last extracted vectors as primary to isolate alpha-policy changes.
  2. Treat response-mean extraction as a separate sensitivity lane to run after WS-C alpha evidence lands, avoiding alpha+extraction confounding.
  3. Keep prompt-last vs response-mean disagreement explicitly reported as an unresolved robustness limitation during this tranche.
- Evidence status summary:
  - `known`: WS-B expanded artifact `week2_extraction_position_ablation_20260227T225251Z.json` shows no trait/layer with prompt-last vs response-mean cosine >=0.7.
  - `observed`: response-only agreement is high for sycophancy/evil and low for hallucination.
  - `inferred`: changing both extraction method and alpha policy in one step would weaken attribution of any WS-C effect changes.
  - `unknown`: whether response-mean extraction will improve final reliability gates once run as a separate lane.
- Rationale: preserve interpretability of WS-C outcomes while keeping extraction-method sensitivity explicitly visible and queued for direct follow-up.
- Impact:
  - WS-C reruns can proceed immediately with constrained-alpha policy on frozen vectors.
  - R1-F2 / R2-C2 / R2-G5 remain partial until the response-mean sensitivity lane is executed.

## [2026-02-27T17:00:48-0600] PIVOT: Downscope WS-C targeted control-volume to avoid likely timeout while preserving checkpoint progress
- Trigger: live checkpoint counters during `week2_ws_c_targeted_sycophancy_l12_alpha2to3` show slow control-loop throughput (`random_controls=20/64` after multiple hours), making timeout risk high at current settings.
- Original approach: run targeted WS-C lane with default control volume (`random_control_vectors=64`, `shuffled_control_permutations=10`).
- New approach:
  1. Stop the in-flight app before timeout.
  2. Resume from the same checkpoint key with reduced control counts for targeted evidence (`random_control_vectors=20`, `shuffled_control_permutations=5`).
  3. Mark this run class as remediation-targeted evidence (not final closeout-grade control-separation evidence).
- Evidence status summary:
  - `known`: checkpoint snapshots show active progress but low throughput in random-control stage.
  - `inferred`: keeping default control volume in this targeted lane has high chance of timeout without adding proportionate decision value for WS-C alpha triage.
  - `unknown`: whether reduced-control evidence will materially change selection/gate interpretation versus full-control runs.
- Rationale: preserve already-computed checkpoint progress while making the targeted alpha-tradeoff tranche operationally finishable.
- Impact:
  - WS-C sycophancy run will be resumed with smaller control counts under same checkpoint key.
  - Reviewer checklist items tied to final control-separation rigor remain `partial` until full-control confirmation is available.

## [2026-02-28T07:12:29-0600] DECISION: WS-C lower-alpha constrained reruns do not supersede NO-GO; proceed to extraction-method sensitivity lane
- Trigger: Completed targeted constrained-selection reruns for sycophancy and evil now provide direct alpha-tradeoff evidence.
- Outcome evidence summary:
  - `known`: sycophancy constrained run selected `alpha=2.0` and remained `overall_pass=false` (failed coherence + cross-trait bleed) in `week2_behavioral_validation_upgrade_sycophancy_20260228T070200Z.json`.
  - `known`: evil constrained run selected `alpha=2.0` and remained `overall_pass=false` (failed coherence) in `week2_behavioral_validation_upgrade_evil_20260228T131128Z.json`.
  - `known`: combined summary artifact `week2_alpha_constrained_selection_20260228T131217Z.json` shows substantial bidirectional-effect reduction vs prior alpha3 runs for both traits.
  - `inferred`: lower-alpha selection alone does not resolve the current reliability-gate bottleneck.
- Decision:
  1. Keep Week 2 NO-GO status unchanged.
  2. Advance to response-mean extraction sensitivity lane as the next high-value discriminator.
  3. Keep constrained-selection implementation in place (it remains methodologically preferable to raw effect-maximization).
- Rationale: updated evidence disconfirms the simple "alpha too high is the primary blocker" explanation under current protocol.
- Impact:
  - Reviewer checklist alpha-related items remain `partial` (implementation + evidence done, reliability issue unresolved).
  - Next tranche focus shifts to extraction-method sensitivity and trait-scope decisions.


## [2026-02-28T21:32:51-0600] DECISION: WS-B response-mean sensitivity lane does not supersede Week 2 NO-GO
- Trigger: Response-mean extraction sensitivity lane completed for sycophancy+evil with constrained selection (`alpha=2.0` on layer 12 for both traits).
- Original approach: Keep WS-B response-mean lane as pending before any further trait-scope or Stage2 gate updates.
- New approach:
  1. Mark response-mean lane as completed evidence.
  2. Keep Week 2 NO-GO in force because overall reliability still fails (coherence gate remains failing for both traits).
  3. Carry response-mean improvements as supporting evidence for trait-scope interpretation, not as closeout pass evidence.
- Evidence status summary:
  - `known`: response-mean sensitivity summary artifact exists: `results/stage1_extraction/week2_response_mean_sensitivity_20260301T025554Z.json`.
  - `known`: sycophancy response-mean lane improves cross-trait bleed (fail->pass) and slightly increases bidirectional effect, but `overall_pass` remains false due coherence.
  - `known`: evil response-mean lane increases bidirectional effect substantially vs prompt-last constrained lane (`+13.42`) but `overall_pass` remains false due coherence.
  - `inferred`: extraction-method switch helps some metrics but does not clear the dominant reliability bottleneck under current gate policy.
- Rationale: This avoids over-claiming method remediation while preserving informative directional evidence for later scope decisions.
- Impact:
  - WS-B response-mean action is closed.
  - NO-GO remains active pending additional remediation outcomes.


## [2026-02-28T21:32:52-0600] DECISION: Formalize WS-D trait scope (hallucination negative finding + evil lane split)
- Trigger: Reviewer reconciliation required explicit hallucination status and evil construct split before Week 3 scope lock.
- Original approach: Carry trait-scope interpretations in narrative notes across CURRENT_STATE/THOUGHT_LOG without a dedicated scope artifact.
- New approach:
  1. Emit an explicit trait-scope resolution artifact (`week2_trait_scope_resolution_<timestamp>.json`).
  2. Classify hallucination as a Stage 1 negative finding under current protocol.
  3. Split evil into two lanes:
     - harmful-content lane (external safety-transfer framing),
     - machiavellian-disposition lane (manipulative social-control framing).
  4. Set recommended Stage2 claim scope to `sycophancy + machiavellian_disposition`; keep hallucination as exploratory control.
- Evidence status summary:
  - `known`: artifact `results/stage1_extraction/week2_trait_scope_resolution_20260301T030203Z.json` created.
  - `known`: hallucination status=`negative_finding_stage1` (primary Section 6.2.3 fail + extraction-free null overlap).
  - `known`: evil harmful-content lane status=`disconfirmed_bidirectional_harmful_content` (baseline_vs_minus < 0 in external transfer).
  - `known`: evil machiavellian lane status=`supported_but_week2_not_validated_due_to_coherence`.
  - `unknown`: whether construct-aligned external transfer for machiavellian lane will satisfy bidirectionality.
- Rationale: Separates construct-misaligned negative evidence from construct-aligned positive overlap evidence without conflating claims.
- Impact:
  - Reviewer items on hallucination formalization and evil lane semantics are materially addressed.
  - Stage2 gate integrity now targets claim layers derived from this scope artifact.


## [2026-02-28T21:32:53-0600] PIVOT: Rebuild Stage2 readiness gate around claim-layer + multi-seed integrity (WS-E)
- Trigger: Reviewer concern that Stage2 readiness could pass despite layer/probe/seed mismatch with active Week 2 trait scope.
- Original approach: Stage2 audit used steering-layer overlap and non-required seed schedule warning; selected-claim-layer alignment was not required.
- New approach:
  1. Update audit to consume latest trait-scope resolution artifact and derive selected primary-claim layers.
  2. Require all of the following for `stage2_readiness_gate=pass`:
     - token-level reconstruction gate pass,
     - hook-integrity pass,
     - selected claim-layer coverage in primary SAE source,
     - selected claim layers probed by both investigation and root-cause artifacts,
     - cross-source overlap on selected claim layers,
     - multi-seed schedule consumed by investigation artifact.
  3. Execute multi-seed layer-12 probes and rerun audit.
- Evidence status summary:
  - `known`: new artifacts:
    - `results/stage2_decomposition/week3_sae_reconstruction_investigation_20260301T031743Z.json` (seed schedule `[42,123,456,789]`)
    - `results/stage2_decomposition/week3_sae_reconstruction_root_cause_20260301T033002Z.json`
    - `results/stage2_decomposition/week3_sae_reconstruction_audit_20260301T033046Z.json`
  - `known`: updated audit now returns `stage2_readiness_gate=fail` with required-statuses:
    - token gate=`fail` (min cos/EV below threshold at claim layer 12),
    - hook integrity=`pass`,
    - claim-layer coverage=`pass`,
    - claim-layer probe coverage=`pass`,
    - cross-source claim-layer overlap=`fail` (no overlap at layer12),
    - seed schedule=`pass`.
  - `inferred`: previous Stage2 pass state was optimistic for claim-layer scope; false-positive path is removed.
- Rationale: Aligns readiness gating with actual claim conditions and replication requirements.
- Impact:
  - Stage2 remains blocked until token gate and cross-source claim-layer overlap issues are resolved or explicitly scoped down by policy.


## [2026-03-02T11:42:20-0600] DECISION: Lock WS-E policy on cross-SAE claim-layer overlap (blocking for cross-source claims, non-blocking for targeted Week 2 remediation runs)
- Trigger: Updated Stage2 audit (`week3_sae_reconstruction_audit_20260301T033046Z.json`) now fails due empty cross-source overlap at active claim layer 12 and token-gate miss, while Week 2 remediation still requires additional trait-lane and stability evidence.
- Original approach: Treat Stage2 readiness failure as a blanket blocker for all subsequent remediation execution work.
- New approach:
  1. Keep cross-SAE overlap as a **blocking requirement for cross-source Stage2 claims**.
  2. Allow Week 2 remediation evidence generation (machiavellian external transfer + WS-F stability) to proceed in parallel, since these do not assert cross-source SAE agreement.
  3. Require explicit policy re-check before any Stage2 decomposition claim or Week2 NO-GO superseding decision.
- Evidence status summary:
  - `known`: claim-layer audit fails on `cross_source_overlap_on_selected_claim_layers` and `token_gate`.
  - `known`: seed-schedule and claim-layer probe coverage now pass.
  - `inferred`: collecting remaining Week2 remediation evidence now reduces decision uncertainty without weakening Stage2 claim standards.
- Rationale: prevents methodological drift while avoiding unnecessary stall on unrelated remediation lanes.
- Impact:
  - WS-D/WS-F/construct-aligned transfer tasks can continue.
  - Cross-source Stage2 claims remain blocked until overlap strategy is resolved.

## [2026-03-02T17:46:10-0600] PIVOT: Run long WS-F rollout-depth jobs in detached-resume mode
- Trigger: Sycophancy rollout5 run (`ap-CU86fvnqVzHNTiECWoKd4m`) stopped mid-controls with explicit Modal log reason `Stopping app - local client disconnected` after ~316.9 minutes.
- Original approach: Launch long `modal run` jobs in attached mode and monitor with awaiter sessions.
- New approach:
  1. For long Week2 remediation jobs, launch with `modal run --detach`.
  2. Keep `run_name` stable so checkpoint resume (`resume_from_checkpoint=true`) continues deterministic state progression.
  3. If attached runs are interrupted for client/session reasons, resume via detached relaunch instead of restarting from scratch.
- Evidence status summary:
  - `known`: attached sycophancy run stopped due client disconnect (Modal app logs).
  - `known`: checkpoint snapshots for both runs exist and include resumable stage state (`week2-wsf-rollout5-syc-l12-a2-rm`, `week2-wsf-rollout5-evil-l12-a2-rm`).
  - `known`: detached relaunch apps started (`ap-j87Kw5fwW1yYn6WmxvAd6z`, `ap-vJsFv6H7b0X5vof3Dm36xb`).
  - `inferred`: detached mode materially reduces wasted compute risk for >3h remediation runs.
- Rationale: preserves completed work and mitigates a reproducible operations failure mode without changing scientific gates.
- Impact:
  - WS-F rollout5 runs continue from checkpoints instead of full reruns.
  - Documentation and closeout updates deferred until detached runs terminalize and artifacts are written.

## [2026-03-03T06:18:30-0600] DECISION: WS-F completion does not supersede Week2 NO-GO by itself
- Trigger: WS-F rollout-depth reruns (rollout=5) are now terminalized and compared against rollout3, alongside completed construct-aligned transfer and seed-replication artifacts.
- Original approach: treat WS-F completion as the last missing operational tranche before drafting a superseding closeout decision.
- New approach:
  1. Mark WS-F tranche as completed evidence collection.
  2. Keep replication/stress launch block in force until an explicit superseding decision evaluates all updated remediation evidence together.
  3. Carry forward the coherence bottleneck as the dominant unresolved reliability gate for sycophancy and evil under current policy.
- Evidence status summary:
  - `known`: rollout5 artifacts exist for sycophancy/evil (`20260303T082321Z`, `20260303T081318Z`) and checkpoint stage is `final_report_written` for both.
  - `known`: rollout sensitivity summary exists (`week2_rollout_stability_sensitivity_20260303T121253Z.json`).
  - `observed`: sycophancy bidirectional effect is stable; evil bidirectional effect decreases at rollout5; both still fail `coherence_pass` and `overall_pass`.
  - `inferred`: additional rollout depth reduces uncertainty in effect estimates but does not resolve the governing closeout failure mode.
- Rationale: avoids implicit criterion drift and preserves governance discipline under the frozen NO-GO policy.
- Impact:
  - WS-F checklist items can be closed as evidence-generated.
  - Replication/stress launches remain blocked pending an explicit integrated closeout decision.

## [2026-03-03T06:24:10-0600] DECISION: Reaffirm Week2 NO-GO after WS-D/WS-F completion (replication/stress remains blocked)
- Trigger: WS-D construct-aligned benchmark, WS-F seed replication, and WS-F rollout-depth sensitivity are all complete and indexed.
- Original approach: hold closeout status open until WS-F evidence lands.
- New approach:
  1. Reassess closeout with integrated WS-A..WS-F evidence.
  2. Keep NO-GO in force for replication/stress launches.
  3. Treat current tranche as remediation evidence complete but not sufficient for gate supersession.
- Evidence status summary:
  - `known`: WS-D construct-aligned machiavellian transfer passes (`week2_machiavellian_external_transfer_20260302T180239Z.json`).
  - `known`: WS-F seed replication passes (`week2_extraction_seed_replication_20260302T180612Z.json`).
  - `known`: WS-F rollout5 runs terminalize and comparison artifact exists (`week2_rollout_stability_sensitivity_20260303T121253Z.json`).
  - `observed`: sycophancy and evil remain `overall_pass=false` under rollout5 due `coherence_pass=false`.
  - `known`: extraction A/B robustness remains failed in latest gap checks (`week2_prelaunch_gap_checks_20260227T205237Z.json`).
  - `known`: Stage2 claim-layer integrity remains failed (`week3_sae_reconstruction_audit_20260301T033046Z.json`).
- Rationale: remediation improved construct alignment and stability confidence but did not clear dominant reliability blockers under frozen gate policy.
- Impact:
  - Replication/stress launches remain blocked.
  - Next tranche should explicitly target coherence-gate bottleneck and extraction-method robustness resolution, with governance criteria frozen before reruns.

## [2026-03-03T07:18:30-0600] DECISION: Second-pass reviewer reconciliation freeze (status corrections + phased execution plan)
- Trigger: New second-pass external reviews identify unresolved structural blockers and one over-claimed remediation status.
- Original approach: treat current remediation checklist as near-closeout with several items already marked resolved.
- New approach:
  1. Preserve both second-pass reviews verbatim as immutable source records.
  2. Downgrade `R2-G6` from `resolved` -> `partial` because current evidence supports determinism under fixed inputs, not full stochastic robustness.
  3. Freeze a phased execution sequence from the structured analysis artifact:
     - `P0`: policy decisions (`coherence` gate binding and Stage2 claim-layer cross-SAE policy),
     - `P1`: robustness/reporting closure work,
     - `P2`: pending reviewer item closure (`R1-F6`, `R2-C5`, `R2-G8`).
  4. Keep Week 2 NO-GO in force and prohibit superseding launch decisions until P0/P1/P2 preconditions are satisfied.
- Evidence status summary:
  - `known`: second-pass reviewer files are logged in `history/reviews/20260303-reviewer{1,2}-second-pass-verbatim.md`.
  - `known`: structured analysis artifact generated: `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T131331Z.json`.
  - `known`: Stage2 claim-layer overlap remains empty at layer 12 and coherence gate remains failing under rollout5 artifacts.
  - `inferred`: advancing without this freeze would reintroduce criterion ambiguity and risk reviewer-misaligned reruns.
- Rationale: converts reviewer feedback into traceable, execution-ready governance without overwriting prior evidence.
- Impact:
  - Checklist and CURRENT_STATE now reflect corrected status and explicit next-step phases.
  - Reviewer update memo drafting remains blocked until pending second-pass items are closed or explicitly scoped as limitations.

## [2026-03-03T07:35:10-0600] DECISION: Freeze Week2 coherence policy as explicit mode-controlled gate with dual-scorecard visibility
- Trigger: Second-pass reviewers identified coherence failures as potentially dominated by absolute threshold calibration rather than steering-induced degradation.
- Original approach: coherence gate logic was hard-coded to `pass_min_score AND pass_max_drop` with no explicit policy mode field.
- New approach:
  1. Add configurable coherence gate mode in runner/config (`absolute_and_relative`, `relative_only`, `absolute_only`).
  2. Keep default mode at `absolute_and_relative` in `experiment.yaml` to preserve hardening continuity.
  3. Emit all coherence pass variants in artifacts (`pass_absolute_and_relative`, `pass_relative_only`, `pass_absolute_only`) plus selected `gate_mode`.
  4. Add policy diagnostic artifact comparing outcomes under all three modes on rollout5 selected runs.
- Evidence status summary:
  - `known`: code update in `scripts/week2_behavioral_validation_upgrade.py` and config key `steering.coherence_gate_mode`.
  - `known`: diagnostic artifact `results/stage1_extraction/week2_coherence_policy_diagnostic_20260303T132222Z.json` shows mode summary: `absolute_and_relative=0/2`, `relative_only=2/2`, `absolute_only=0/2`.
  - `inferred`: coherence bottleneck is policy-sensitive and must be handled explicitly in governance rather than implicitly inside fixed code.
  - `unknown`: whether future superseding Week2 closeout should switch primary gate mode or retain strict hardening mode with dual-scorecard interpretation.
- Rationale: makes gate semantics auditable and prevents hidden criterion drift.
- Impact:
  - Future reruns can evaluate coherence under pre-registered explicit mode.
  - Reviewer-facing reporting can distinguish strict hardening vs degradation-focused interpretations using the same raw metrics.

## [2026-03-03T07:35:40-0600] DECISION: Resolve Stage2 policy contradiction via explicit split gates (decomposition-start vs cross-source-claim)
- Trigger: Second-pass reviewers flagged that claim layer 12 has no cross-check overlap, making a single aggregate Stage2 readiness gate structurally ambiguous for next-step decisions.
- Original approach: Stage2 audit had one aggregate `stage2_readiness_gate` requiring all checks, including cross-source overlap.
- New approach:
  1. Add explicit Stage2 policy keys in config:
     - `governance.week3_stage2_policy.decomposition_start_requires_cross_source_overlap=false`
     - `governance.week3_stage2_policy.cross_source_claims_require_overlap=true`
  2. Extend audit output with:
     - `stage2_decomposition_start_gate`
     - `stage2_cross_source_claim_gate`
     - existing strict `stage2_readiness_gate` retained.
  3. Regenerate Stage2 audit under this policy split.
- Evidence status summary:
  - `known`: updated audit artifact `results/stage2_decomposition/week3_sae_reconstruction_audit_20260303T132222Z.json` now reports policy and split gates.
  - `known`: `stage2_decomposition_start_gate=fail` due token gate miss (`min cos/EV`), independent of overlap requirement.
  - `known`: `stage2_cross_source_claim_gate=fail` with required overlap and `overlap_layers=[]` at claim layer 12.
  - `inferred`: governance contradiction is now explicit and machine-traceable; remaining blocker is evidence/policy closure, not hidden gate coupling.
- Rationale: clarifies what is blocked for decomposition execution vs what is blocked for cross-source claim strength.
- Impact:
  - Stage2 progression discussions can reference explicit gate purpose.
  - Cross-source claims remain blocked until overlap strategy is resolved; decomposition-start viability remains gated by token-level reconstruction quality.

## [2026-03-03T10:49:00-0600] PIVOT: Repair extraction-robustness runner execution path before P1 evidence launch
- Trigger: new robustness script failed twice before remote execution (nested app context under `modal run`, then container import failure for sibling module).
- Original approach: reuse Week2 extraction helpers by importing `week2_extract_persona_vectors` and wrap remote call in `with app.run()`.
- New approach:
  1. Remove nested `app.run()` from local entrypoint and call remote directly under `modal run`.
  2. Make script self-contained (inline config/prompt/audit helpers + image/volume definitions) so Modal container does not depend on sibling module imports.
  3. Relaunch robustness run only after local helper tests pass.
- Evidence status summary:
  - `known`: failure app IDs `ap-eYMPajAqtsE089mItUibcU` (nested app) and `ap-br5lv3RY9hoWnTPAW3doB7` (module import).
  - `known`: patched run succeeded on app `ap-I8m0e5l5pGK1UeRbcD4oqe`, W&B `bzu4kdxo`, artifact `week2_extraction_robustness_bootstrap_20260303T164652Z.json`.
  - `inferred`: failure mode was implementation/runtime packaging, not scientific protocol.
- Rationale: unblock critical P1 evidence without changing scientific intent.
- Impact: extraction robustness closure artifact is now generated and usable for reviewer reconciliation.

## [2026-03-03T10:49:00-0600] DECISION: Replace extraction A/B hard-blocker role with content-robustness evidence; keep prompt-vs-response mismatch as documented limitation
- Trigger: second-pass reviewers requested robustness tests that isolate content stability rather than cross-regime activation-position agreement.
- Original approach: treat prompt-last vs response-mean cosine failure (`<0.7`) as primary extraction robustness blocker.
- New approach:
  1. Keep prompt-vs-response A/B mismatch as a limitation diagnostic.
  2. Promote content-robustness checks as primary closure evidence:
     - bootstrap subset stability on extraction pairs (`80/100`, 20 draws),
     - train-vs-heldout extraction agreement.
  3. Gate robustness on `bootstrap_pairwise_p05>=0.8` and `train_vs_heldout_cosine>=0.7`.
- Evidence status summary:
  - `known`: `week2_extraction_robustness_bootstrap_20260303T164652Z.json` passes overall.
    - sycophancy: `p05=0.9988`, train-vs-heldout `0.9957`.
    - evil: `p05=0.9991`, train-vs-heldout `0.9965`.
  - `known`: prompt-vs-response A/B remains failed in prior artifacts (`week2_prelaunch_gap_checks_20260227T205237Z.json`, `week2_extraction_position_ablation_20260227T225251Z.json`).
  - `inferred`: extraction directions are highly content-stable under prompt-last protocol even though cross-regime position agreement is low.
- Rationale: aligns robustness interpretation with reviewer-requested diagnostics and avoids conflating different computational regimes.
- Impact:
  - SP-F2 and SP-F4 can be reconciled via explicit evidence split (content robustness pass, regime mismatch limitation retained).
  - Week2 NO-GO is not automatically superseded; coherence and Stage2 claim-layer issues still govern launch blocking.

## [2026-03-03T10:49:00-0600] DECISION: Close pending P2 governance items with explicit artifacts (bleed sensitivity, capability boundary, manual concordance scope)
- Trigger: remaining checklist blockers were `R1-F6`, `R2-C5`, and `R2-G8`.
- Original approach: leave these items pending until additional reruns or larger manual annotation pass.
- New approach:
  1. Resolve cross-trait bleed threshold sensitivity with explicit sweep artifact.
  2. Freeze capability-claim boundary artifact distinguishing Week2 proxy gate from broader capability suite requirements.
  3. Close manual concordance concern via explicit weighting policy: sanity-check role only; kappa remains primary reliability evidence.
- Evidence status summary:
  - `known`: bleed sensitivity artifact `week2_cross_trait_bleed_sensitivity_20260303T164726Z.json`.
    - sycophancy prompt-last primary ratio `0.3165` fails at `0.30` but passes from `0.35` onward.
    - all response-mean rollout5 lanes pass at `0.30`.
  - `known`: capability boundary artifact `week2_capability_suite_spec_20260303T164726Z.json`.
  - `known`: manual scope artifact `week2_manual_concordance_policy_closure_20260303T164726Z.json` (`claim_ready_for_primary_reliability=false`, role=`sanity_check_only`).
  - `inferred`: pending-item closure is now documentation/governance-complete without introducing new unsupported claim strength.
- Rationale: closes reviewer reconciliation gaps using explicit, auditable policy artifacts instead of implicit assumptions.
- Impact:
  - `R1-F6`, `R2-C5`, and `R2-G8` can be moved out of pending status in the reconciliation checklist.
  - Reviewer update packet can now be prepared after docs/index synchronization and full-test verification.

## [2026-03-03T13:03:50-0600] DECISION: Close SP-F1 and SP-F3 via explicit policy-resolution packet
- Trigger: After P1/P2 closure artifacts, the remaining high-severity second-pass items were policy-ambiguity blockers (`SP-F1`, `SP-F3`).
- Original approach: leave both items as partial while relying on dispersed decisions/artifacts.
- New approach:
  1. Produce a single policy-resolution artifact consolidating closure logic for `SP-F1` and `SP-F3`.
  2. Freeze Stage2 claim-scope policy explicitly:
     - decomposition-start allowed at selected claim layer as single-source,
     - cross-source claims restricted to overlap-capable sensitivity layers (`11,15`),
     - no cross-source claim at non-overlap selected claim layer (`12`).
  3. Freeze coherence dual-scorecard policy explicitly:
     - hardening reliability uses `absolute_and_relative`,
     - proposal-compatibility interpretation uses `relative_only`,
     - dual-scorecard reporting is mandatory.
- Evidence status summary:
  - `known`: policy artifact `results/stage1_extraction/week2_policy_resolution_packet_20260303T190245Z.json`.
  - `known`: SP-F1/SP-F3 status updates in `history/20260227-reviewer-reconciliation-checklist-v1.md` are now `resolved`.
  - `inferred`: second-pass blocker set is now reduced to residual partials rather than unresolved policy ambiguity.
- Rationale: removes interpretation ambiguity and preserves auditable governance before any future superseding launch decision.
- Impact:
  - reviewer update packet is now unblocked from a checklist-completeness standpoint.
  - replication/stress remains blocked until explicit superseding decision.

## [2026-03-03T13:08:46-0600] PIVOT: Refresh second-pass synthesis tooling to consume latest closure artifacts
- Trigger: existing reconciliation synthesis artifact still reflected stale statuses (`SP-F1`/`SP-F3` unresolved) after policy and P1/P2 closure artifacts were produced.
- Original approach: keep prior synthesis artifact and update checklist/docs manually.
- New approach:
  1. Extend `week2_second_pass_reconciliation_analysis.py` inputs to include robustness, bleed-sensitivity, capability-spec, manual-policy, and policy-resolution artifacts.
  2. Make reconciled finding statuses artifact-aware for SP-F1/SP-F3/SP-F4/SP-F5/SP-F7/SP-F8.
  3. Regenerate synthesis artifact as the active source for reviewer packet prep.
- Evidence status summary:
  - `known`: refreshed synthesis artifact `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T190514Z.json`.
  - `known`: refreshed artifact now marks `SP-F1=resolved`, `SP-F3=resolved`, `SP-F2=partial`.
  - `inferred`: synthesis output now matches checklist/governance state and reduces handoff ambiguity.
- Rationale: keep machine-readable reconciliation aligned with document-level decisions.
- Impact: reviewer update drafting can use a single up-to-date synthesis artifact.

## [2026-03-03T13:16:30-0600] PIVOT: Refresh second-pass synthesis artifact with schema-fixed rollout sensitivity input
- Trigger: active synthesis artifact `week2_second_pass_reconciliation_analysis_20260303T190514Z.json` still consumed pre-patch rollout sensitivity input (`...121253Z`), which re-opened `SP-F6` despite the schema fix already landing in `...132222Z`.
- Original approach: keep `190514Z` synthesis as active reference for reviewer packet prep.
- New approach:
  1. Update default `--rollout-sensitivity-artifact` in `scripts/week2_second_pass_reconciliation_analysis.py` to `results/stage1_extraction/week2_rollout_stability_sensitivity_20260303T132222Z.json`.
  2. Regenerate synthesis artifact and use it as the active reference.
  3. Produce reviewer-facing memo from the refreshed synthesis and checklist.
- Evidence status summary:
  - `known`: refreshed synthesis artifact generated: `results/stage1_extraction/week2_second_pass_reconciliation_analysis_20260303T191356Z.json`.
  - `known`: refreshed status now records `SP-F6=resolved` with `SP-F2=partial` and `SP-F9=document_limitation`.
  - `known`: reviewer memo generated: `history/20260303-reviewer-update-memo-v1.md`.
- Rationale: keep machine-readable synthesis aligned with patched schema outputs and avoid reviewer confusion from stale-status artifacts.
- Impact:
  - active second-pass artifact is now schema-consistent.
  - reviewer handoff packet is complete and traceable.

## [2026-03-03T14:00:00-0600] DECISION: Supersede Week2 NO-GO for phase transition under proposal-compatibility scorecard; proceed to Stage2 decomposition with explicit caveats
- Trigger: latest external superseding recommendation and internal evidence synthesis show Week2 proposal-compatibility criterion is met while hardening absolute-coherence remains model-baseline-limited.
- Original approach: retain global Week2 NO-GO block (2026-02-27T15:31:15-0600) for all progression until all hardening gates pass.
- New approach:
  1. Supersede NO-GO **for phase transition only**: proceed to Stage2 decomposition for `sycophancy` and `machiavellian_disposition`.
  2. Keep hardening scorecard in reporting: absolute-and-relative coherence remains failing and must be reported as a limitation, not hidden.
  3. Keep claim-scope policy frozen:
     - decomposition-start at selected claim layer as single-source,
     - cross-source claims restricted to overlap-capable sensitivity layers (`11`, `15`),
     - no cross-source claim at non-overlap selected claim layer (`12`).
  4. Keep `hallucination` out of primary claim lane (exploratory control only).
- Evidence status summary:
  - `known`: proposal compatibility scorecard shows `validated_traits_count=2` (`sycophancy`, `evil`) and `continue_threshold_pass=true` in `results/stage1_extraction/week2_primary_postrun_ingestion_20260227T220017Z.json`.
  - `known`: coherence policy diagnostic shows `relative_only` passes `2/2`, while `absolute_and_relative` passes `0/2` due baseline-level absolute floor mismatch (`results/stage1_extraction/week2_coherence_policy_diagnostic_20260303T132222Z.json`).
  - `known`: extraction content-robustness passes strongly (`overall_pass=true`; bootstrap and train-vs-heldout gates pass) in `results/stage1_extraction/week2_extraction_robustness_bootstrap_20260303T164652Z.json`.
  - `known`: construct-aligned external transfer for machiavellian lane passes (`overall_pass=true`) in `results/stage1_extraction/week2_machiavellian_external_transfer_20260302T180239Z.json`.
  - `inferred`: remaining partial items (`SP-F2`, `R2-C6`, `R2-G4`, `R2-G6`) are limitations/caveats rather than blockers to start H1 evidence collection.
- Rationale: advances the program to hypothesis-testing while preserving strict transparency about unresolved limitations and scorecard disagreement.
- Impact:
  - Phase focus moves from Week2 gate refinement to Stage2 decomposition execution.
  - Week2 replication/stress expansion is no longer the critical path for progressing H1/H2 evidence.
  - All Stage2 outputs must carry the explicit caveat block (absolute coherence floor, prompt-vs-response regime mismatch, cross-SAE layer-12 limitation, determinism-vs-stochastic robustness distinction).

## [2026-03-03T14:21:30-0600] PIVOT: Make Stage2 decomposition run self-contained across Modal boundary (prompts + vectors passed as payload)
- Trigger: first three Stage2 launch attempts failed before decomposition due Modal boundary assumptions:
  - attempt 1: remote import of local helper module failed,
  - attempt 2: remote prompt-file path lookup failed (`/prompts/...`),
  - attempt 3: remote vectors absolute local path failed (`/Users/.../week2_persona_vectors_...pt`).
- Original approach: have remote function read local workspace modules/files by path.
- New approach:
  1. Inline concentration helpers directly in `scripts/week3_sae_decomposition.py` (remove remote dependency on sibling module imports).
  2. Load prompt pairs locally and pass `prompt_pairs_by_trait` payload to remote function.
  3. Load layer vectors locally and pass `layer_vectors_by_trait` payload to remote function; keep artifact-path string metadata only for traceability.
- Rationale: Modal worker runtime cannot rely on local workspace filesystem paths unless explicitly mounted; payload-first design removes path-coupling failures.
- Impact:
  - Stage2 decomposition primary lane run succeeds (`ap-fA5SmEmYa8AfRxorlWLFNy`), producing `results/stage2_decomposition/week3_sae_decomposition_20260303T202729Z.json`.
  - Future cross-source sensitivity launches can reuse the same execution path without filesystem-path regressions.

## [2026-03-04T10:31:30-0600] PIVOT: Stage3 candidate-selection policy changed from cross-layer feature-ID support to claim-layer primary-only selection
- Trigger: First Stage3 candidate-selection artifact (`week3_stage3_candidate_selection_20260304T163025Z.json`) showed `selected_with_support_ge1=0` for both traits under feature-ID overlap logic across layers 12/11/15.
- Original approach: prioritize claim-layer features that also appear in overlap-layer cross-source top-k sets using feature-ID intersections.
- New approach:
  1. Do not use cross-layer feature-ID intersections as feature-level support evidence (IDs are not comparable across layers/sources for causal interpretation).
  2. Select first-pass Stage3 features from claim-layer primary ranked candidates only (top-K by claim-layer combined rank score).
  3. Preserve overlap-layer artifacts as lane-level context/sensitivity evidence, not per-feature support.
- Rationale: avoids invalid feature correspondence assumptions and keeps Stage3 selection epistemically clean.
- Impact:
  - supersedes the intermediate artifact `results/stage3_attribution/week3_stage3_candidate_selection_20260304T163025Z.json` for policy definition.
  - Stage3 first-pass attribution will proceed using claim-layer-selected features with explicit cross-layer comparability caveat.

## [2026-03-04T10:47:30-0600] DECISION: Freeze initial Stage4 target-set source to Stage3 pass2 depth-sensitivity artifact
- Trigger: Stage3 depth-sensitivity run (`n_prompts=50`) completed and preserved the same-order concentration/stability pattern observed in pass1 (`n_prompts=20`).
- Original approach: keep Stage3 in iterative attribution mode before defining Stage4 targets.
- New approach:
  1. Treat `results/stage3_attribution/week3_stage3_activation_delta_attribution_20260304T164549Z.json` as the Stage4 target-freeze source artifact.
  2. Build Stage4 necessity/sufficiency ablation set from this artifact (top-k per trait + matched random same-size baselines).
  3. Keep pass1 artifact as supportive corroboration, not the freeze source.
- Evidence status summary:
  - `known`: pass2 artifact exists and is terminalized from app `ap-oW62P2TsDS7TMlLw0BHIHw`.
  - `known`: sycophancy metrics are stable from pass1->pass2 (`gini 0.5853 -> 0.5771`, Jaccard `0.3296 -> 0.3254`).
  - `known`: machiavellian metrics are stable from pass1->pass2 (`gini 0.6612 -> 0.6476`, Jaccard `0.3698 -> 0.3744`).
  - `inferred`: further Stage3 depth-only reruns have diminishing information value relative to starting Stage4 causal tests.
- Rationale: move from proxy-attribution accumulation to causal hypothesis testing while preserving traceable target-freeze provenance.
- Impact:
  - Next critical-path work is Stage4 execution, not additional Stage3 depth sweeps.
  - Stage4 artifacts must retain the limitation block (`SP-F2`, `SP-F9`, layer12 reconstruction/cross-SAE caveat, determinism-vs-stochastic robustness caveat).

## [2026-03-04T11:13:20-0600] DECISION: Treat Stage4 proxy-necessity outputs as exploratory-only (non-claim) until behavioral ablation path is executed
- Trigger: post-refactor full Stage4 proxy run (`week3_stage4_necessity_proxy_ablation_20260304T171200Z.json`) remained method-divergent and showed negative primary resample reductions for both active traits.
- Original approach: use proxy Stage4 reductions as early H2 directional evidence while preparing full behavioral ablation implementation.
- New approach:
  1. Keep proxy artifacts as exploratory diagnostics only (`behavioral_necessity=unknown`).
  2. Do not use proxy outputs as claim-grade evidence for H2 in summaries or reviewer updates.
  3. Require full behavioral ablation runner (judge-scored steering-output reduction under resample/mean/zero + random same-size baselines) for claim-grade H2 evidence.
- Evidence status summary:
  - `known`: primary resample reductions are negative in the post-refactor full run (`syc=-0.0203`, `evil=-0.1352`).
  - `known`: method disagreement persists (mean positive both traits; zero mixed signs).
  - `known`: post-refactor implementation validation passed (unit tests + smoke run), so this is not a crash/serialization artifact.
  - `inferred`: proxy metric either fails to capture behavioral necessity or indicates weak/anti-necessity of current top-10 sets under resample semantics.
- Rationale: maintain claim-evidence discipline and prevent proxy-based causal overreach.
- Impact:
  - H2 remains low-confidence and behaviorally untested.
  - Next high-value work is building and running the behavioral Stage4 ablation path, not additional proxy-only iterations.

## [2026-03-04T11:36:51-0600] PIVOT: Stage4 behavioral ablation remote import path made self-contained
- Trigger: first behavioral Stage4 launch (`ap-qGsg9jGO9PWD709AjrcLhm`) failed during Modal module import with `ModuleNotFoundError: No module named 'scripts'` from `from scripts.shared.behavioral_eval import ...`.
- Original approach: import shared behavioral helper module via package path (`scripts.shared.behavioral_eval`) from `scripts/week3_stage4_behavioral_ablation.py`.
- New approach:
  1. Inline required behavioral-eval helper primitives directly in `week3_stage4_behavioral_ablation.py` (judge prompt/parse/retry + response generation + rate limiter).
  2. Keep shared module tests intact, but remove remote runtime dependency on cross-file package imports.
- Rationale: detached Modal run imported script as `/root/week3_stage4_behavioral_ablation.py` without `scripts` package context; self-contained script removes Modal boundary packaging risk.
- Impact:
  - first behavioral Stage4 app is a known failed attempt (no artifact produced).
  - patched runner is ready for immediate relaunch under same config tranche after passing local tests.

## [2026-03-04T11:52:40-0600] DECISION: Add explicit progress logging checkpoints to Stage4 behavioral ablation runner
- Trigger: long-running detached Stage4 behavioral jobs were hard to distinguish between healthy progress vs silent stall from Modal logs alone.
- Decision: instrument `scripts/week3_stage4_behavioral_ablation.py` with timestamped progress logs at:
  - model load completion,
  - per-trait start/end,
  - baseline scoring progress,
  - per-method start/end,
  - random-baseline set progress every 5 sets,
  - overall completion.
- Rationale: improve operational observability and reduce wasted runtime on silent failures; aligns with prior requirement for granular checkpoint logging.
- Impact: current in-flight app (`ap-OcpIPgzEsMcFCs968fCyxW`) is unaffected; future launches will surface real-time execution stages in `modal app logs`.

## [2026-03-05T09:56:30-0600] PIVOT: Stage4 behavioral reduction metric requires low-baseline guard before claim use
- Trigger: first completed behavioral Stage4 artifact (`week3_stage4_behavioral_ablation_20260304T192718Z.json`) produced extreme reduction magnitudes (order `1e8-1e9`) when baseline steering effect was near zero for some prompts/traits.
- Original approach: compute per-prompt reduction as `(baseline_abs - ablated_abs) / max(baseline_abs, 1e-8)` and aggregate means directly.
- New approach:
  1. Treat low-baseline prompts as a separate validity lane for necessity reduction (do not let near-zero denominators dominate aggregated reduction means).
  2. Add explicit reporting of valid/invalid prompt counts for reduction metrics.
  3. Rerun the same deterministic small tranche and supersede this artifact for claim interpretation.
- Rationale: current formulation is execution-valid but numerically unstable for low-baseline prompts, causing non-interpretable effect-size/selectivity summaries.
- Impact:
  - artifact `week3_stage4_behavioral_ablation_20260304T192718Z.json` remains traceable as first execution success, but interpretation is limited.
  - next critical path is metric-stability patch + rerun before using Stage4 behavioral outputs as H2 evidence.

## [2026-03-05T10:03:40-0600] DECISION: Add Hewitt (2026) residual-stream linearity note as methodological framing reference
- Trigger: request to assess relevance of `https://www.cs.columbia.edu/~johnhew/residual-stream-isnt-linear.html` for current remediation and Stage2+ claim framing.
- Decision: include this source in local background references and use it as a wording/interpretation guardrail (empirical validation over architectural linearity assumptions).
- Scope: framing/caveat source only; does not change preregistered gates or acceptance thresholds by itself.
- Impact:
  - supports current interpretation of extraction A/B mismatch as computational-regime dependence.
  - reinforces requirement that Stage4 claims be justified by measured controls (resample/mean/zero + random baselines), not assumed linearity.

## [2026-03-05T10:11:20-0600] DECISION: Stage4 reduction aggregation now uses low-baseline validity masking
- Trigger: first behavioral Stage4 artifact showed reduction blow-ups when baseline steering effect was near zero.
- Decision:
  1. Define `min_baseline_effect_for_reduction` (default `1.0`) and mark prompt-level reductions invalid when `baseline_effect_abs < threshold`.
  2. Exclude invalid prompts from reduction/effect-size/selectivity aggregates.
  3. Emit explicit validity accounting (`n_valid`, `n_invalid`, indices, valid fraction) and random-set usage (`n_sets_used`, `n_sets_skipped_no_valid_prompts`).
- Rationale: prevents denominator-driven artifacts from dominating Stage4 necessity summaries while preserving full traceability of excluded prompts.
- Impact:
  - superseding behavioral rerun required for claim interpretation.
  - if valid-prompt coverage is too low, artifact should be treated as insufficient evidence rather than forced into unstable reduction statistics.

## [2026-03-06T06:45:44-0600] DECISION: Treat Stage4 behavioral pass3 as metric-stable but coverage-limited; prioritize threshold-sensitivity + prompt-depth follow-up
- Trigger: superseding artifact `results/stage4_ablation/week3_stage4_behavioral_ablation_20260305T091059Z.json` removed low-baseline reduction blowups but yielded sparse validity coverage on evil lane.
- Evidence summary:
  - `known`: denominator-instability issue is mitigated under `min_baseline_effect_for_reduction=1.0`.
  - `known`: validity coverage is asymmetric (`sycophancy 8/10`, `evil 1/10`).
  - `known`: no method passes full necessity/selectivity threshold bundle in this tranche.
- Decision:
  1. Do not treat pass3 as claim-grade H2 evidence.
  2. Next tranche must include threshold sensitivity (`min_baseline_effect_for_reduction`) and/or larger prompt count for evil lane to avoid `n_valid=1` underpower.
- Rationale: stability without adequate valid coverage can still produce misleading necessity summaries.
- Impact: H2 remains `in_progress` with low confidence; Stage4 requires one more calibration tranche before sufficiency/necessity claims.

## [2026-03-06T08:53:06-0600] PIVOT: Guard zero-baseline reductions in Stage4 threshold-sensitivity lane
- Trigger: evil threshold-sensitivity run (`ap-6cyPCePw9R4wIkimKetVXp`, `min_baseline_effect_for_reduction=0.0`) failed with `ZeroDivisionError` in `_reduction_fraction` when baseline steering effect was exactly zero.
- Original approach: validity mask and reduction formula both accepted baseline `0.0` when threshold was `0.0`.
- New approach:
  1. Introduce a hard denominator floor (`MIN_REDUCTION_DENOMINATOR=1e-8`) in `_reduction_fraction` so zero-baseline prompts return `None` (invalid), never divide.
  2. Align validity mask to `max(min_baseline_effect_for_reduction, MIN_REDUCTION_DENOMINATOR)` so mask/reporting matches reduction semantics.
  3. Add explicit regression test (`baseline=0.0`, threshold `0.0` returns `None`).
- Rationale: maintain threshold-sensitivity exploration while preventing deterministic crash/undefined reductions at zero baseline.
- Impact:
  - prior run is a failed attempt with no artifact output.
  - patched run can resume the same threshold condition (`0.0`) for coverage characterization without divide-by-zero failure.

## [2026-03-09T14:42:58-0500] DECISION: Promote evil source setting to alpha3 for Stage4 necessity confirmation lane
- Trigger: Stage4 threshold-sensitivity run at alpha2 source remained coverage-limited (`4/30` valid prompts) and blocked interpretable H2 evidence.
- Decision:
  1. Run a source-sensitivity calibration using evil source artifact `results/stage1_extraction/week2_behavioral_validation_upgrade_evil_20260227T171643Z.json` (`selected layer=12, alpha=3.0`) with `min_baseline_effect_for_reduction=0.0`.
  2. Treat this run as calibration-only due reduced random baseline depth (`n_random=5`) and use it to decide whether full-depth confirmation is worthwhile.
  3. Set next critical-path action to full-depth confirmation on this source setting if coverage improves.
- Evidence summary:
  - `known`: calibration artifact `results/stage4_ablation/week3_stage4_behavioral_ablation_20260309T194229Z.json` completed successfully.
  - `known`: evil valid-prompt coverage improved from prior `4/30` (alpha2 source) to `13/20` (alpha3 source).
  - `known`: selectivity remained non-significant in calibration (`p=0.1667`), so claim-grade H2 is still not met.
  - `inferred`: source-setting mismatch was a larger limiter than threshold choice alone for evil-lane coverage.
- Rationale: This isolates a high-value source-setting change before committing full-cost Stage4 reruns and reduces risk of repeating low-coverage runs.
- Impact:
  - Stage4 is still `in_progress` and `interpretation-limited`.
  - Next run should keep alpha3 source and restore full random-baseline depth (`>=20`) for selectivity-strength evaluation.

## [2026-03-09T23:37:21-0500] DECISION: Stage4 evil alpha3 full-depth confirmation improves coverage but does not clear strict necessity/selectivity gates
- Trigger: full-depth relaunch artifact landed (`results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T001903Z.json`) after source-sensitivity calibration.
- Decision:
  1. Keep alpha3 source setting as the active Stage4 evil lane baseline because it resolves the prior low-coverage blocker.
  2. Do not upgrade H2 to claim-ready; strict threshold bundle remains unmet (`necessity/selectivity/A12` all false across methods).
  3. Prioritize threshold-binding diagnosis + prompt-tranche sensitivity before changing trait/layer policy again.
- Evidence summary:
  - `known`: valid coverage improved to `21/30` (`0.70`) with baseline effect mean `12.3333`.
  - `known`: selectivity p-value improved to `0.0476` (vs `0.1667` calibration), but current strict `selectivity_p_threshold_pass` still evaluates false.
  - `known`: no method passes full strict gate bundle in this artifact.
  - `inferred`: remaining blocker is threshold-policy/method-selectivity alignment, not baseline-effect sparsity.
- Rationale: this preserves empirical progress without overstating H2 evidence quality.
- Impact:
  - Stage4 remains `in_progress` and `interpretation-limited`.
  - Next tranche should isolate threshold binders and confirm whether failure is robust across heldout slices.

## [2026-03-09T23:47:20-0500] DECISION: Add deterministic heldout tranche control and run Stage4 prompt-tranche sensitivity
- Trigger: after full-depth alpha3 confirmation, strict thresholds remained unmet and tranche dependence became the highest-value unresolved question.
- Decision:
  1. Add `--heldout-start-index` to `week3_stage4_behavioral_ablation.py` so heldout prompt slices can be shifted deterministically without altering source setting/gates.
  2. Launch prompt-tranche sensitivity run with `heldout_start_index=20`, keeping all other full-depth settings fixed (`n_prompts=30`, `n_random=20`, alpha3 source).
  3. Generate a threshold-binding diagnostic artifact from latest Stage4 runs to quantify dominant gate binders before policy discussion.
- Evidence summary:
  - `known`: tranche-control patch + tests pass (`test_week3_stage4_behavioral_ablation_utils.py`, `Ran 11 tests ... OK`).
  - `known`: run `ap-bC1z6ABhVa7hUSNBsJ0cpe` launched and reached active baseline scoring checkpoints.
  - `known`: diagnostic artifact `results/stage4_ablation/week3_stage4_threshold_binding_diagnostic_20260310T044638Z.json` shows necessity margin is currently the dominant blocker across methods.
- Rationale: isolates prompt-slice effects and avoids policy decisions based on a single heldout tranche.
- Impact:
  - Stage4 next critical path is run terminalization + tranche comparison.
  - H2 remains low-confidence until tranche sensitivity is resolved and strict thresholds are met.

## [2026-03-10T09:09:13-0500] DECISION: Treat tranche-sensitivity outcome as evidence of method-level selectivity instability; keep strict H2 gate unchanged for now
- Trigger: prompt-tranche sensitivity artifact `results/stage4_ablation/week3_stage4_behavioral_ablation_20260310T080841Z.json` landed under same source/gates as full-depth reference.
- Decision:
  1. Keep strict Stage4 threshold bundle unchanged for immediate interpretation (`necessity=0.8`, `significance=0.01`, `a12=0.71`).
  2. Do not elevate H2 confidence; strict flags still fail across methods in both reference and tranche runs.
  3. Treat selectivity behavior as tranche-sensitive and require a dedicated tranche-vs-reference comparison artifact before any threshold-policy change.
- Evidence summary:
  - `known`: coverage remains high (`20/30` tranche vs `21/30` reference), so coverage scarcity is not the current blocker.
  - `known`: selectivity shifts by method across tranches (resample/mean degrade; zero remains `p=0.0476`).
  - `known`: all methods remain below strict threshold passes in tranche artifact.
  - `inferred`: threshold-policy discussion should be informed by stability evidence, not a single full-depth run.
- Rationale: preserves rigor while preventing premature gate recalibration.
- Impact:
  - H2 remains `in_progress` / low confidence.
  - Next critical output is tranche-vs-reference threshold-margin comparison summary.

## [2026-03-10T09:16:04-0500] DECISION: Use tranche-vs-reference comparison as policy-decision anchor; defer new Stage4 launches pending H2 scorecard decision
- Trigger: comparison artifact `results/stage4_ablation/week3_stage4_tranche_comparison_20260310T141458Z.json` completed with method-level deltas and gate-state parity.
- Decision:
  1. Do not launch another Stage4 behavioral run immediately.
  2. Use the pair (`week3_stage4_threshold_binding_diagnostic_20260310T044638Z.json`, `week3_stage4_tranche_comparison_20260310T141458Z.json`) as the decision basis for H2 policy direction.
  3. Keep strict gate status as authoritative until an explicit dual-scorecard policy update is logged.
- Evidence summary:
  - `known`: coverage remains stable/high across reference and tranche runs.
  - `known`: gate states remain unchanged (all strict gates fail across methods in both runs).
  - `known`: selectivity strength is tranche-sensitive (resample/mean degrade on tranche).
  - `inferred`: additional immediate reruns are lower value than resolving the policy interpretation path now.
- Rationale: avoid unbounded rerun loops while preserving evidence quality and decision traceability.
- Impact:
  - Next work is policy-packet synthesis, not new launches.
  - H2 remains `in_progress` / low confidence.

## [2026-03-10T09:20:37-0500] DECISION: Freeze new Stage4 launches pending explicit H2 policy lock; policy packet accepted as decision basis
- Trigger: policy packet artifact generated (`results/stage4_ablation/week3_stage4_policy_decision_packet_20260310T142000Z.json`) after threshold-binding + tranche comparison artifacts.
- Decision:
  1. Treat the new policy packet as the authoritative decision basis for immediate H2 governance lock.
  2. Do not launch another Stage4 run until the strict-only vs dual-scorecard path is explicitly logged.
  3. Preserve strict gate failure status as known regardless of narrative-path choice.
- Evidence summary:
  - `known`: strict summary remains fail across both full-depth runs.
  - `known`: coverage is high/stable across runs.
  - `known`: tranche-sensitivity exists in effect strength.
  - `inferred`: additional launches before policy lock are lower expected value than resolving scorecard interpretation.
- Rationale: prevents further run loops without a clear acceptance-policy target.
- Impact:
  - immediate next step is policy lock entry, not execution.
  - H2 remains `in_progress` / low confidence.

## [2026-03-10T09:24:10-0500] DECISION: Lock H2 policy to dual-scorecard lane while preserving strict-fail status as primary
- Trigger: policy packet artifact `results/stage4_ablation/week3_stage4_policy_decision_packet_20260310T142000Z.json` completed with stable high coverage, strict gate failures in both runs, and tranche-sensitive method strength.
- Decision:
  1. Adopt `dual-scorecard` interpretation lane for H2 narrative reporting.
  2. Preserve strict Stage4 threshold outcome (`fail`) as the authoritative gate status for claim-grade necessity.
  3. Do not run additional Stage4 launches until a new, explicitly-scoped strict-threshold remediation question is defined.
- Evidence summary:
  - `known`: strict summary remains fail across both full-depth runs.
  - `known`: coverage remains high/stable (`0.70`, `0.6667`).
  - `known`: tranche sensitivity affects margin strength, not gate-state pass/fail.
  - `inferred`: additional immediate reruns have lower expected value than advancing with caveated interpretation.
- Rationale: resolves policy ambiguity, prevents unbounded rerun loops, and keeps governance rigor explicit.
- Impact:
  - H2 remains `in_progress` and `low confidence` under strict scorecard.
  - Stage4 can transition from run-generation to synthesis/reporting and path-consistent next-phase work.

## [2026-03-10T09:31:40-0500] DECISION: Accept Stage4 H2 synthesis memo as tranche closeout; prioritize downstream design work over new Stage4 launches
- Trigger: synthesis memo `history/20260310-stage4-h2-synthesis-memo-v1.md` completed and indexed after policy lock + diagnostic artifact trio.
- Decision:
  1. Treat the synthesis memo as the canonical summary for current Stage4 H2 interpretation.
  2. Keep default launch freeze for Stage4 behavioral reruns unless a strict-threshold remediation question is explicitly pre-registered with stop criteria.
  3. Move immediate execution focus to path-consistent downstream work (H3 sufficiency design and Stage5 planning stub).
- Evidence summary:
  - `known`: strict scorecard status remains fail in both full-depth runs.
  - `known`: dual-scorecard interpretation lock is already in force.
  - `known`: synthesis memo now consolidates threshold-binding, tranche-comparison, and policy-packet outputs in one artifact-backed document.
  - `inferred`: marginal value of another immediate Stage4 rerun is lower than advancing hypothesis-testing design with explicit caveats.
- Rationale: prevents looped reruns and preserves traceable transition from diagnostic closure to next-phase execution planning.
- Impact:
  - Stage4 remains `in_progress` but run generation is paused by default.
  - Next deliverables are planning/scope artifacts, not additional Stage4 run artifacts.

## [2026-03-10T09:32:30-0500] DECISION: Generate launch-free H3 sufficiency and Stage5 planning artifacts before any new remote execution
- Trigger: Stage4 policy lock + synthesis memo completion established a no-rerun default and left downstream implementation tasks as the critical path.
- Decision:
  1. Create explicit H3 sufficiency execution plan artifact with protocol controls, fallback claims, and readiness blockers.
  2. Create explicit Stage5 planning stub with H4/H5 target patterns, required inputs, and gate checklist.
  3. Keep `launch_recommended_now=false` in both artifacts and preserve Stage4 launch freeze.
- Evidence summary:
  - `known`: H2 strict status remains fail; interpretation lane is already locked.
  - `known`: no new data dependency is required to draft implementation-ready planning artifacts.
  - `inferred`: producing these artifacts now reduces restart overhead and prevents ad hoc execution drift in the next tranche.
- Rationale: maintain momentum while respecting governance lock and avoiding unnecessary remote spend.
- Impact:
  - downstream implementation scope is now concretely defined for H3/Stage5.
  - no remote jobs were launched under this decision.

## [2026-03-10T09:34:35-0500] PIVOT: Supersede first H3/Stage5 planning artifacts to preserve append-only integrity while correcting decision-reference metadata
- Trigger: first H3 planning artifact referenced an interim decision timestamp after chronology normalization.
- Original approach: keep first planning artifacts as-is and update only docs.
- New approach: append superseding planning artifacts with corrected decision-reference list and mark first drafts as superseded in `RESULTS_INDEX.md`.
- Rationale: respects the no-overwrite artifact rule and preserves a clean traceable audit chain.
- Impact:
  - active planning references now point to:
    - `results/stage4_ablation/week3_h3_sufficiency_execution_plan_20260310T143354Z.json`
    - `results/stage5_cross_persona/week3_stage5_planning_stub_20260310T143354Z.json`
  - first drafts remain retained and explicitly superseded.

## [2026-03-10T09:39:00-0500] DECISION: Implement Stage5 launch-free overlap utility now to convert planning stubs into executable diagnostics
- Trigger: H3/Stage5 planning artifacts completed with open checklist items (`S5-G2`, `S5-G4`) and no immediate need for remote execution.
- Decision:
  1. Implement a local utility to compute layerwise cross-trait Jaccard overlap and a router-candidate stub from existing Stage2 artifacts.
  2. Add focused unit tests for overlap/gradient/router computations.
  3. Run utility once on current decomposition artifacts to establish baseline diagnostic output before further hardening.
- Evidence summary:
  - `known`: script/tests/artifact produced:
    - `scripts/week3_stage5_cross_persona_analysis.py`
    - `tests/test_week3_stage5_cross_persona_analysis.py`
    - `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T143805Z.json`
  - `observed`: early>late overlap trend exists for some feature sources, but proposal threshold pattern is not fully met and router stable pool is empty.
  - `inferred`: next Stage5 step should harden comparability/multiple-testing controls before claim-level interpretation.
- Rationale: keeps momentum with low-cost executable diagnostics while respecting launch freeze and governance constraints.
- Impact:
  - Stage5 planning is now partially operationalized.
  - no new Modal runs launched.

## [2026-03-10T09:56:51-0500] DECISION: Close launch-free H3/H4 tooling gap with sufficiency preflight and Stage5 comparability/multiple-testing hooks before new remote runs
- Trigger: prior `Next Action` items required implementing sufficiency dry-run path and extending Stage5 utility policy controls (`S5-G2`/`S5-G4`).
- Decision:
  1. Add launch-free Stage4 sufficiency preflight utility with deterministic dry-run validation artifact.
  2. Extend Stage5 cross-persona utility with source comparability diagnostics and BH-FDR router testing hooks.
  3. Keep Stage4 launch freeze unchanged; do not treat dry-run outputs as empirical sufficiency evidence.
- Evidence summary:
  - `known`: new artifacts landed:
    - `results/stage4_ablation/week3_stage4_sufficiency_preflight_20260310T145632Z.json`
    - `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T145632Z.json`
  - `known`: tests pass:
    - `tests/test_week3_stage4_sufficiency_preflight.py` (`Ran 3 tests ... OK`)
    - `tests/test_week3_stage5_cross_persona_analysis.py` (`Ran 4 tests ... OK`)
  - `observed`: Stage5 BH-FDR hook is wired but unevaluated in this run (`missing_router_pvalues`).
  - `inferred`: next high-value step is remote sufficiency lane integration + router p-value production, not more planning-only artifacts.
- Rationale: maximizes progress under no-launch default and reduces execution risk for the next remote tranche.
- Impact:
  - H3/H4 statuses move from untested to in-progress (tooling/exploratory execution only).
  - Immediate backlog narrows to data-producing execution work.

## [2026-03-10T14:59:29-0500] DECISION: Execute Stage5 router-pvalue lane now and treat zero BH rejections as an evidence update, not a blocker
- Trigger: Stage5 BH-FDR hook was wired but unevaluated (`missing_router_pvalues`) in `week3_stage5_cross_persona_analysis_20260310T145632Z.json`, leaving checklist closures (`S5-G2`/`S5-G4`) incomplete.
- Decision:
  1. Add dedicated tests for `scripts/week3_stage5_router_candidate_pvalues.py` before artifact generation.
  2. Generate a timestamped router p-value artifact + normalized map from current Stage2 decomposition artifacts (layers 11/12/15, early-layer cap 12).
  3. Re-run Stage5 cross-persona analysis with `--router-pvalues-json` and keep current FDR policy (`alpha=0.01`) for this launch-free pass.
- Evidence summary:
  - `known`: new test file `tests/test_week3_stage5_router_candidate_pvalues.py` added; Stage5 suite passes (`python3 -m unittest discover -s tests -p 'test_week3_stage5_*py'` -> `Ran 7 tests ... OK`).
  - `known`: router p-value artifacts generated:
    - `results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_20260310T195815Z.json`
    - `results/stage5_cross_persona/week3_stage5_router_candidate_pvalues_map_20260310T195815Z.json`
  - `observed`: Stage5 rerun with map produced `results/stage5_cross_persona/week3_stage5_cross_persona_analysis_20260310T195835Z.json`; BH hook now evaluates (`n_tested=62`, `n_rejected=0`, `min_q=0.0465`, candidate_union).
  - `inferred`: the open gap is now policy interpretation and potential sensitivity design (if desired), not missing implementation.
- Rationale: closes the highest-priority launch-free Stage5 execution gap with append-only artifacts and test-backed code paths.
- Impact:
  - Stage5 H5 status moves from `untested` to `in_progress` in governance docs.
  - `week3_stage5_cross_persona_analysis_20260310T145632Z.json` is superseded by `...195835Z` for BH-hook evidence references.

## [2026-03-10T15:15:09-0500] DECISION: Treat Stage5 gate closure as exploratory-null lock and wire H3 to remote-capable execution without immediate launch
- Trigger: remaining `Next Action` items in `CURRENT_STATE.md` were (a) Stage5 `S5-G2/S5-G4` closure and (b) integration of sufficiency preflight into a remote-executable circuit-only lane.
- Decision:
  1. Close Stage5 gates via a policy packet sourced from executed BH-hook evidence, not narrative-only notes.
  2. Add a dedicated Stage4 behavioral sufficiency runner with a default `dry_run` packet mode to validate remote execution wiring before any launch.
  3. Keep launch freeze behavior unchanged by default: no automatic remote sufficiency execution in this tranche.
- Evidence summary:
  - `known`: Stage5 policy artifact landed: `results/stage5_cross_persona/week3_stage5_policy_decision_packet_20260310T200937Z.json`.
  - `observed`: policy packet closes gates as `S5-G2=pass_with_limitation`, `S5-G4=exploratory_null`, recommendation=`lock_exploratory_null_with_optional_sensitivity_lane`.
  - `known`: new H3 runner script + tests + dry-run artifact landed:
    - `scripts/week3_stage4_behavioral_sufficiency.py`
    - `tests/test_week3_stage4_behavioral_sufficiency_utils.py`
    - `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260310T201431Z.json`
  - `observed`: H3 dry-run packet reports `inputs_valid=true`, `launch_recommended_now=true`, `blocking_items=[]`.
- Rationale: resolves remaining execution-path/tooling blockers while preserving conservative launch governance.
- Impact:
  - H3 now has a remote-capable execution path (dry-run validated).
  - Stage5 gate closure is explicitly recorded as exploratory-null under current FDR policy.
  - Next work is an explicit run/no-run decision, not more scaffolding.

## [2026-03-10T15:24:10-0500] PIVOT: H3 sufficiency launch command switched from file-path invocation to module invocation after Modal mount/import failure
- Trigger: first remote H3 launch app `ap-6BWjuSAxvqB0s3axc7YsRC` failed before execution with repeated container import error `ModuleNotFoundError: No module named 'scripts'`.
- Original approach: `modal run scripts/week3_stage4_behavioral_sufficiency.py --no-dry-run ...`.
- New approach: launch the same pre-registered run via module entrypoint (`modal run -m scripts.week3_stage4_behavioral_sufficiency --no-dry-run ...`) so `scripts.*` imports resolve in the container package context.
- Rationale: failure was packaging/mount semantics, not experiment design; module invocation is the minimal deterministic fix without changing run parameters.
- Impact: pre-registered run config remains unchanged; only launch command form changes.

## [2026-03-10T18:15:15-0500] PIVOT: Stabilize H3 remote checkpoint identity with explicit run token before retrying after preemption
- Trigger: detached H3 app `ap-EvoMUuBIRRlMXBHxvtLrvB` encountered Modal worker preemption before durable checkpoint recovery was guaranteed; the checkpoint/final artifact path depended on a timestamp generated inside the remote function, so restarts could miss prior partial state.
- Original approach: rely on remote timestamp-derived checkpoint filenames plus detached execution.
- New approach: thread an explicit `run_token` from local entrypoint through dry-run packet and remote execution, persist remote checkpoint/final artifacts under token-stable filenames, and relaunch one replacement run under that fixed token.
- Rationale: this is the minimal change that makes preemption recovery coherent and inspectable without altering the scientific config.
- Impact: H3 tranche1 remains the same experiment scientifically; operational semantics now support checkpoint reuse and deterministic remote artifact retrieval.

## [2026-03-10T18:21:02-0500] PIVOT: Move H3 checkpoint reload ahead of model load after Modal volume conflict on detached retry
- Trigger: replacement H3 app `ap-0G5330JQuwPuHQqTYjlWuK` stopped with `RuntimeError: there are open files preventing the operation` at `vol.reload()`, caused by an open Hugging Face/Xet log file on the mounted volume after model load.
- Original approach: load model first, then call `vol.reload()` before checking for an existing checkpoint.
- New approach: reload/checkpoint-read the volume before model loading, and retain a warning log path if reload still fails unexpectedly.
- Rationale: checkpoint discovery only depends on the volume state and does not require model objects; moving it earlier removes the open-file conflict while preserving resume semantics.
- Impact: H3 detached retry can be relaunched under the same scientific config with one more operational fix; prior app `ap-0G5330JQuwPuHQqTYjlWuK` is invalid for evidence and should be treated as infrastructure failure.

## 2026-03-10T22:05:00-0500 PIVOT: H3 pilot semantics/gating remediation before any second sufficiency run
- Trigger: first full H3 remote artifact (`results/stage4_ablation/week3_stage4_behavioral_sufficiency_remote_week3-stage4-h3-tranche1-20260310T2321Z.json`) showed three implementation-path validity issues: unbounded preservation ratios yielding `>1.0`, infeasible selectivity p-value gating at `n_random=5` with `alpha=0.01`, and cells marked evaluable/pass despite extremely sparse valid-prompt coverage.
- Original approach: treat the completed tranche as the first substantive H3 result and decide between strict fail vs exploratory null directly from the emitted gate counts.
- New approach: patch the H3 runner before any rerun so that (1) proposal-facing preservation is bounded and separated from raw ratio diagnostics, (2) selectivity gating is explicitly disabled when the random-baseline count cannot realize the configured alpha, (3) a minimum-valid-prompts floor is required for claim-facing threshold evaluation, and (4) a small raw-output audit sample is persisted for coherence inspection.
- Rationale: the current artifact is execution-valid but not claim-valid. Without these fixes, the runner can emit misleading `pass` flags for conditions that are mathematically unevaluable or semantically mis-specified.
- Impact: Stage4 H3 remains interpretation-pending; no second sufficiency launch should occur until the patched runner passes local validation and a fresh dry-run/preflight packet is emitted.

## 2026-03-10T22:43:00-0500 DECISION: H3 claim-facing sufficiency uses bounded preservation plus explicit evaluability gates
- Context: the first full H3 remote tranche emitted `observed_mean_preservation > 1.0` values, impossible selectivity gates at low `n_random`, and apparent sufficiency passes for cells with only `1/10` valid prompts.
- Decision:
  1. Treat the proposal-facing sufficiency metric as a bounded fraction of steered-effect preservation, capped at `1.0`.
  2. Preserve the uncapped ratio as a diagnostic-only field.
  3. Require minimum valid-prompt coverage before any sufficiency/selectivity/A12 threshold can pass (`min_valid_prompt_count=5`, `min_valid_prompt_fraction=0.5`).
  4. Treat selectivity as unevaluable unless the realized random-baseline count can attain the configured alpha (`n_random >= ceil(1/alpha)-1`; for `alpha=0.01`, `>=99`).
  5. Persist a small sample of raw circuit-only outputs per cell for coherence inspection.
- Rationale: this aligns the runner with proposal semantics (`preserves >=60%`) and prevents mathematically unevaluable or semantically inflated cells from being reported as H3 passes.
- Consequences: prior H3 artifacts remain execution-valid but must be interpreted under the old semantics; any future H3 launch should use the patched runner and the new dry-run packet `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260311T023909Z.json`.

## 2026-03-10T22:48:00-0500 DECISION: H3 preservation metric must be sign-aware, not absolute-magnitude only
- Context: side audit after the first semantics patch identified that H3 preservation still treated sign-flipped circuit-only responses as fully preserved because the ratio used absolute deltas from the unsteered baseline.
- Decision: preservation is now computed on signed trait deltas (`circuit_only_delta / steered_delta`), with claim-facing preservation then clipped into `[0,1]` and opposite-direction effects collapsing toward `0` rather than counting as preserved.
- Rationale: H3 is about preserving the same steering effect, not merely preserving a large deviation from baseline in either direction.
- Consequences: old H3 artifacts cannot be fully reinterpreted under the final metric unless signed delta information is present; the scratch reanalysis from `20260311T0240Z` remains a bounded+coverage-only approximation, not a final sign-aware re-score.

## [2026-03-11T08:31:00-0500] DECISION: Upgrade H3 runner to explicit claim-grade mode before any second sufficiency launch
- Trigger: the next planned Stage4 H3 step required closing the last implementation blockers identified after the first pilot: candidate-pool-only scope, absent on-run capability/perplexity-style controls, and missing monotonicity gating.
- Decision:
  1. Add explicit `claim_mode` and `ablation_scope` parameters to `scripts/week3_stage4_behavioral_sufficiency.py`.
  2. Implement `full_sae_complement` support and require it when `claim_mode=claim_grade`.
  3. Add lightweight on-run unrelated-task controls per dose cell: capability-proxy generations plus next-token-loss diagnostics on neutral prompts.
  4. Add method-level dose-monotonicity summaries and pass/fail gating.
  5. Revalidate locally and emit a fresh claim-grade dry-run packet before any remote relaunch.
- Evidence summary:
  - `known`: local validation now passes:
    - `python3 -m py_compile scripts/week3_stage4_behavioral_sufficiency.py`
    - `python3 -m unittest discover -s tests -p 'test_week3_stage4_behavioral_sufficiency_utils.py'` -> `Ran 11 tests ... OK`
    - `python3 -m unittest discover -s tests -p 'test_week3_stage4_*py'` -> `Ran 46 tests ... OK`
  - `known`: fresh claim-grade dry-run packet landed at `results/stage4_ablation/week3_stage4_behavioral_sufficiency_dryrun_packet_20260311T132932Z.json`.
  - `observed`: that packet records `claim_mode=claim_grade`, `ablation_scope=full_sae_complement`, `next_token_loss_diagnostics_enabled=true`, and `launch_recommended_now=true` for code-path readiness.
- Rationale: closes the remaining H3 implementation gaps with the smallest viable extension of the existing runner, without creating a parallel execution path.
- Impact:
  - H3 claim-grade code readiness is now materially stronger.
  - The remaining blocker is empirical/runtime feasibility under a judge-heavy full matrix, not missing instrumentation.

## [2026-03-11T08:42:00-0500] DECISION: Stage H3 claim-grade execution as a bounded sycophancy-resample tranche before any wider matrix
- Trigger: after H3 claim-grade hardening, the naive full matrix (`2 traits x 2 methods x 4 doses x 30 prompts x 100 random sets`) is inferred to be runtime-prohibitive under judge-heavy evaluation.
- Decision:
  1. Do not launch the full claim-grade matrix first.
  2. Launch a bounded calibration tranche instead: `trait=sycophancy`, `method=resample`, `dose_response={0.25,0.50,1.00}`, `n_prompts=10`, `random_baseline_samples=100`, `claim_mode=claim_grade`, `ablation_scope=full_sae_complement`.
  3. Use this tranche as the decisive feasibility read on full-complement H3 before widening to additional traits/methods.
- Evidence summary:
  - `known`: prior H3 pilot (`10 prompts`, `5 random sets`, `2 traits x 2 methods x 4 doses`) already required multi-hour detached execution.
  - `inferred`: scaling random-baseline depth from `5 -> 100` dominates runtime; reducing traits/methods/doses is the only responsible way to get a claim-grade read without an uncontrolled budget/time blowout.
- Rationale: preserves the most important scientific property (claim-grade full-complement H3) while converting an impractically large matrix into a tractable calibration tranche.
- Impact:
  - Next remote launch is now well-defined and bounded.
  - Expansion to evil/mean is contingent on this tranche producing coherent, interpretable outputs.

## [2026-03-11T10:06:00-0500] DECISION: New trait-lane work will proceed as an isolated Stage-1/Week-2 screening branch, not a core-pivot
- Trigger: trait-choice concern raised explicitly; local paper library plus March 11, 2026 literature refresh indicate additional paper-backed lane families worth screening (`honesty/lying/deception`, `assistant_likeness`, `politeness/optimism/apathy/humor`, `agreeableness`, `refusal/harmfulness`).
- Decision:
  1. Keep the current core claim line unchanged for now: `sycophancy`, `machiavellian_disposition`, `hallucination` as exploratory negative-control lane.
  2. Add a separate lane-expansion branch at Stage-1/Week-2 screening depth only.
  3. Do not launch any new lane-expansion remote jobs while the active H3 app `ap-mCOxAI9Xp7WCZoxpslD6Yi` remains live.
  4. Prefer sidecar-style screening wrappers and a trait registry over immediate generalization of the hardened core Week 2 runner.
  5. Treat the new branch as breadth-first screening with promotion gates, not as full-pipeline duplication.
- Evidence summary:
  - `known`: proposal trait choice emphasized comparability to Chen, not exhaustiveness (`persona-circuits-proposal.md:626-634`).
  - `known`: current project evidence already differentiates lane quality (`sycophancy` stronger, `machiavellian` construct improved after reframing, `hallucination` negative finding).
  - `known`: planning artifacts now exist:
    - `history/20260311-trait-lane-literature-refresh-v1.md`
    - `history/20260311-trait-lane-expansion-plan-v1.md`
  - `known`: fresh literature refresh confirmed URLs for `Assistant Axis`, `Sycophancy Hides Linearly in the Attention Heads`, and `LieCraft`.
- Rationale: this preserves current progress, avoids destabilizing the live H3 line, and gives the project a disciplined way to test whether trait choice is a meaningful bottleneck without multiplying Stage2–Stage4 work across every candidate family.
- Impact:
  - Safe work now: docs, registry design, construct-card drafting, non-invasive sidecar planning.
  - Unsafe work now: new lane-expansion launches, silent default-trait changes, superseding core claim-trait updates.

## [2026-03-11T09:38:00-0500] DECISION: First trait-lane implementation tranche lands as registry + construct cards + dry-run sidecars only
- Trigger: the reconciled trait-lane expansion plan was approved for execution, but the active H3 app `ap-mCOxAI9Xp7WCZoxpslD6Yi` remains live and the branch must not disturb the current core claim path.
- Decision:
  1. Implement only the first non-invasive tranche from `history/20260311-trait-lane-expansion-plan-v1.md`.
  2. Add a registry/config layer (`configs/trait_lanes_v2.yaml`, `scripts/shared/trait_lane_registry.py`) plus construct cards for all five candidate families.
  3. Add sidecar planning wrappers (`week2_trait_lane_prompt_screen.py`, `week2_trait_lane_heldout_screen.py`, `week2_trait_lane_behavioral_smoke.py`, `week2_trait_lane_promotion_packet.py`) that emit local dry-run artifacts only.
  4. Do not modify legacy Week 2 defaults or launch any new lane-expansion Modal jobs in this tranche.
- Evidence summary:
  - `known`: parity tests confirm legacy trait defaults remain unchanged (`test_week2_trait_lane_parity.py`).
  - `known`: new registry and sidecar tests pass (`test_trait_lane_registry.py`, `test_week2_trait_lane_sidecars.py`).
  - `known`: full-family dry-run artifacts landed under `results/stage1_extraction/trait_lanes_v2/` with `13` candidate lanes, `0` namespace collisions, and a `234`-row behavioral-smoke matrix.
  - `known`: the active H3 app remains live; no lane-expansion remote launch occurred.
- Rationale: this captures the new line of work in executable form while keeping the current core experiment stable and avoiding a premature rewrite of the hardened Week 2 runner.
- Impact:
  - Safe next work: prompt/held-out generation adapters and further local screening prep.
  - Still blocked: any lane-expansion remote screening launch before H3 terminalization and explicit branch advancement.

## [2026-03-11T15:26:00-0500] DECISION: H3 gets scoped closeout first; trait-lane expansion becomes the next active branch immediately after
- Trigger: user explicitly confirmed the desired sequencing: let the bounded H3 claim-grade tranche finish to its own scoped success/failure/table determination, then advance the project into the trait-lane expansion branch rather than widening H3 first.
- Decision:
  1. Keep the live H3 run `ap-mCOxAI9Xp7WCZoxpslD6Yi` isolated until terminalization, ingestion, and a scoped H3 closeout memo/table are complete.
  2. Treat that closeout as sufficient to pause Stage4 widening unless the H3 artifact itself reveals a narrow operational fix that must be applied immediately.
  3. Make `trait_lanes_v2` the next active execution branch after H3 closeout.
  4. Preserve current branch isolation rules until H3 is closed: no lane-expansion remote launch while the active H3 app remains live.
- Evidence summary:
  - `known`: the lane-expansion branch is already materially prepared via registry, construct cards, and dry-run sidecars (`configs/trait_lanes_v2.yaml`, `scripts/shared/trait_lane_registry.py`, `results/stage1_extraction/trait_lanes_v2/*_20260311T143658Z.json`).
  - `known`: the active H3 branch is already in-flight with checkpoint/resume working and should be allowed to resolve on its own scoped terms before introducing another remote line.
  - `inferred`: switching to lane expansion after the current H3 closeout maximizes breadth without abandoning the current causal-validation read.
- Rationale: this prevents indefinite Stage4 recursion while also avoiding a premature pivot that would leave the active H3 tranche scientifically under-documented.
- Impact:
  - Immediate work remains monitoring/closeout for the active H3 tranche.
  - The next post-H3 implementation target is promotion of the `trait_lanes_v2` branch from dry-run planning into real screening execution.

## [2026-03-11T14:57:59-0500] DECISION: Close the bounded H3 claim-grade tranche as a scoped negative feasibility signal; do not rerun it by default
- Trigger: bounded H3 app `ap-mCOxAI9Xp7WCZoxpslD6Yi` stopped during `dose=1.00` with judge parse exhaustion after completing `dose=0.25` and `dose=0.50`, and the recovered checkpoint plus raw-output audits show already-degenerate circuit-only behavior at the completed doses.
- Decision:
  1. Treat the tranche `week3-stage4-h3-claimgrade-syc-resample-trancheA-20260311T0844-0500` as scoped-closed.
  2. Do not launch an immediate narrow recovery rerun for `dose=1.00` by default.
  3. Record the tranche as a negative feasibility signal for claim-grade full-complement H3 on the `sycophancy/resample` lane.
  4. Advance the next active execution branch to `trait_lanes_v2` screening, consistent with the previously locked sequencing.
- Evidence summary:
  - `known`: remote checkpoint exists and loads completed doses `0.25` and `0.50`; mid-dose state for `1.00` is not checkpointed.
  - `observed`: completed doses `0.25` and `0.50` both have `sufficiency_threshold_pass=false`, coherence-drop mean `73.2`, capability proxy `0.0`, and degenerate repetitive raw outputs.
  - `observed`: terminal failure occurred at `dose=1.00` after `65/100` random baseline sets with `Judge returned unparseable output after 6 attempts`.
  - `inferred`: finishing the remaining `35` random baseline sets at `dose=1.00` is unlikely to overturn the bounded tranche’s feasibility read, because the already-completed lower doses are non-viable under the same harsher full-complement regime.
- Rationale: this preserves scientific honesty and momentum. The tranche already answered the bounded question it was designed to answer: whether claim-grade full-complement H3 looked feasible enough to justify widening. It does not.
- Impact:
  - Stage4 H3 remains globally unresolved, but this bounded tranche is no longer an active blocking run.
  - The next concrete execution work moves to the prepared `trait_lanes_v2` branch.

## [2026-03-11T15:27:00-0500] DECISION: Prieto et al. (2026) is logged as an interpretation-sidecar reference, not a scope change
- Trigger: a deep review was requested for the new paper/repo `From Data Statistics to Feature Geometry: How Correlations Shape Superposition` / `correlations-feature-geometry`.
- Decision:
  1. Add Prieto et al. (2026) to the reference library as a confirmed March 10, 2026 paper.
  2. Treat it as an interpretation-sidecar source for future geometry-heavy Stage 2 / Stage 5 analysis and paper-writing caveats.
  3. Do not change the active H3 branch, proposal thresholds, or the post-H3 `trait_lanes_v2` execution sequence because of this paper.
  4. Reconsider it only after H3 closeout, when a promoted trait lane or refreshed cross-persona analysis actually depends on clustered/shared feature geometry for interpretation.
- Evidence summary:
  - `known`: the paper studies correlated-feature superposition in bag-of-words / autoencoder settings, not persona circuits in instruction-tuned LLM residual streams.
  - `known`: its strongest project relevance is interpretive: clustering or overlap can arise from correlated superposition and therefore is not, by itself, circuit evidence.
  - `known`: the public repo is reproduction-oriented and, at inspection time, did not expose an explicit license or a test suite in the tree.
  - `inferred`: importing the method stack directly would add scope without addressing the project’s current bottlenecks.
- Rationale: this preserves a useful new literature input while preventing accidental scope creep or retrospective reinterpretation of current results.
- Impact:
  - Docs now carry a future revisit hook for geometry-heavy interpretation.
  - No launch, pipeline, or milestone logic changes follow from this update.

## [2026-03-11T15:10:14-0500] DECISION: Promote the trait-lane branch to real-generation readiness, but keep the first P3 execution bounded
- Trigger: H3 is now scoped-closed, the `trait_lanes_v2` branch is the next active execution line, and the first wrapper tranche stopped at dry-run sidecars only.
- Decision:
  1. Add real prompt-generation wrappers for `trait_lanes_v2` extraction and held-out datasets under a new shared helper layer.
  2. Keep these wrappers non-invasive: no mutation of legacy Week 1/2 prompt-generation defaults and no writes outside `prompts/trait_lanes_v2/`.
  3. Treat the next real execution step as a bounded P3 slice rather than an all-13-lane generation burst.
  4. Preferred first slice: one lane each from the top three non-safety families, tentatively `assistant_likeness`, `honesty`, and `politeness`, subject to pre-run preregistration.
- Evidence summary:
  - `known`: new wrappers and helper now exist:
    - `scripts/shared/trait_lane_generation.py`
    - `scripts/week2_trait_lane_generate_extraction_prompts.py`
    - `scripts/week2_trait_lane_generate_heldout_prompts.py`
  - `known`: local validation passed:
    - `python3 -m py_compile scripts/shared/trait_lane_generation.py scripts/week2_trait_lane_generate_extraction_prompts.py scripts/week2_trait_lane_generate_heldout_prompts.py tests/test_trait_lane_generation.py`
    - `python3 -m unittest discover -s tests -p 'test_trait_lane_generation.py'` -> `Ran 5 tests ... OK`
  - `known`: dry-run plan artifacts landed:
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_extraction_generation_plan_20260311T200659Z.json`
    - `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_heldout_generation_plan_20260311T200659Z.json`
  - `inferred`: starting with bounded family coverage is the safest way to validate the new generation path before spending budget across all 13 lanes.
- Rationale: this moves the branch from planning to actionable execution readiness while preserving auditability, minimizing prompt-spend risk, and avoiding another broad launch before the new path is exercised on real API outputs.
- Impact:
  - The next immediate run should be a bounded local API-backed prompt-generation slice, not a full screening matrix.
  - Legacy prompt files and current core-claim artifacts remain untouched.

## [2026-03-11T15:10:14-0500] DECISION: The first live trait-lane P3 generation slice will cover `assistant_likeness`, `honesty`, and `politeness`
- Trigger: the `trait_lanes_v2` branch is ready for its first real prompt-generation run, but launching all 13 lanes immediately would spend budget before the new generation path has been quality-checked on real outputs.
- Decision:
  1. Start with three lanes only: `assistant_likeness`, `honesty`, and `politeness`.
  2. Run both extraction-prompt generation and held-out prompt generation for that trio.
  3. Defer `agreeableness` to the next slice because it is explicitly entangled with the existing `sycophancy` anchor and is therefore less useful as the first path-validation lane.
  4. Defer all safety-like lanes (`refusal_expression`, `harmfulness_judgment`, `harmlessness`) until the non-safety generation path has been audited on real outputs.
- Evidence summary:
  - `known`: family priority order in `configs/trait_lanes_v2.yaml` is `assistant_axis=1`, `honesty_deception=2`, `light_style_persona=3`, `refusal_harmlessness=4`, `agreeableness=5`.
  - `known`: `assistant_likeness` and `honesty` are high-priority lanes with distinct construct classes (`persona_like`, `strategy_like`), and `politeness` is the cleanest low-confound style-like lane in the light-style family.
  - `inferred`: this trio gives the first live slice family breadth without immediately stepping into safety-policy confounds or a lane (`agreeableness`) that is already known to overlap conceptually with `sycophancy`.
- Rationale: the first live run should validate the generation path on a bounded, diverse, lower-confound set before we widen the branch.
- Impact:
  - Immediate next run config is now preregistered.
  - Broader family coverage remains available after prompt-quality review of this first slice.

## [2026-03-11T15:15:04-0500] PIVOT: Trait-lane generation wrappers need retry + oversampling before the first live slice can succeed reliably
- Trigger: the first live extraction-generation attempt for `assistant_likeness,honesty,politeness` failed on `assistant_likeness/persona_pressure` with `RuntimeError: Insufficient valid extraction prompts`.
- Original approach: request exactly the target count per category from the Anthropic API in a single call and fail immediately if the returned batch does not survive validation/duplicate filtering.
- New approach:
  1. Add bounded retry logic per category.
  2. Oversample each API request above the target count.
  3. Accumulate valid unique prompts across attempts before deciding the category has failed.
  4. Revalidate locally, then rerun the exact same bounded slice.
- Rationale: the current failure reflects a brittle generator implementation, not evidence that the chosen lanes are bad. The wrapper has to be robust to partially invalid or duplicate model outputs before a real screening slice is interpretable.
- Impact:
  - The bounded first live slice remains the same.
  - The next step is code hardening plus rerun, not lane-scope expansion.

## [2026-03-11T15:25:00-0500] PIVOT: Held-out generation needs anti-paraphrase guards and append-safe output paths before reuse
- Trigger: the first live slice completed operationally, but the audit shows held-out lexical overlap is too high for `honesty` (`max similarity ~0.99`, `mean ~0.65` against extraction queries), and current generators would overwrite files on rerun.
- Original approach: trust prompt wording plus exact duplicate blocking to keep held-out data sufficiently distinct, and write fixed output filenames per lane.
- New approach:
  1. Add append-safe output suffix support so regenerated prompt files do not overwrite prior artifacts.
  2. Add lane-local anti-paraphrase guards for held-out generation using existing extraction queries as reference.
  3. Encourage novelty in the held-out prompt template by explicitly listing existing extraction queries to avoid.
  4. Rerun only the held-out slice with a new suffix after local validation.
- Rationale: the current issue is specific to held-out distinctness, not extraction generation. We should repair the held-out path without discarding the already-usable extraction files or violating the no-overwrite artifact rule.
- Impact:
  - Existing extraction outputs remain valid for this slice pending later content review.
  - Current held-out outputs become provisional and should not be used for screening until the anti-paraphrase rerun lands.

## [2026-03-11T15:33:37-0500] DECISION: Slice B will expand breadth with `persona_drift_from_assistant`, `lying`, and `optimism`
- Trigger: Slice A is formally closed as a completed first live generated-input slice, and the next branch decision is whether to deepen Slice A or widen breadth.
- Decision:
  1. Start Slice B as the next bounded live trio.
  2. Use `persona_drift_from_assistant`, `lying`, and `optimism`.
  3. Defer extraction-free wrapper work until after Slice B because the branch objective right now is lane breadth, not deeper instrumentation on the first trio.
- Evidence summary:
  - `known`: Slice A already covers `assistant_likeness`, `honesty`, and `politeness`.
  - `known`: the branch plan identifies `persona_drift_from_assistant`, `deception/lying`, and `optimism/agreeableness` as leading next-slice candidates.
  - `inferred`: `lying` is cleaner than `deception` for the second slice because it is narrower and easier to audit.
  - `inferred`: `optimism` is a cleaner second style lane than `agreeableness`, which is explicitly entangled with the core `sycophancy` anchor.
- Rationale: this maximizes trait-family coverage under the now-working generation/audit process while avoiding a premature expansion of wrapper scope.
- Impact:
  - Next live work is Slice B extraction + held-out generation + audit.
  - Extraction-free wrapper work is deferred one step, not abandoned.

## [2026-03-11T16:59:23-0500] DECISION: Trait-lane extraction-free work will start by executing the existing Slice A wrapper, not by rewriting the path
- Trigger: Resume inspection shows `scripts/week2_trait_lane_prepare_extraction_free_eval.py`, `tests/test_week2_trait_lane_prepare_extraction_free_eval.py`, and `prompts/trait_lanes_v2/extraction_free_exemplar_bank_sliceA.json` already exist in-repo, but no extraction-free outputs or registered artifacts exist yet for `trait_lanes_v2`.
- Decision:
  1. Treat the existing wrapper + exemplar bank as the implementation baseline.
  2. Validate it locally via tests and a dry-run plan.
  3. Run the first bounded live extraction-free generation on Slice A only: `assistant_likeness`, `honesty`, `politeness`.
  4. Defer Slice B extraction-free generation until Slice A outputs are generated and registered.
- Evidence summary:
  - `known`: no files exist yet under `prompts/trait_lanes_v2/extraction_free/`.
  - `known`: Slice A held-out inputs are the accepted `retry01` files.
  - `inferred`: duplicating the wrapper would add churn without increasing confidence; the right next step is to execute and audit the existing isolated path.
- Rationale: this keeps the branch bounded, avoids redundant code, and turns an unexercised implementation into a real screening artifact.
- Impact:
  - Next run is a local extraction-free preparation tranche for Slice A.
  - If the run succeeds, the next branch choice becomes Slice B extraction-free vs extraction-free evaluation/activation follow-on, not more wrapper work.

## [2026-03-11T17:03:10-0500] DECISION: Extend extraction-free prep parity to Slice B before widening to Slice C or building a trait-lane activation wrapper
- Trigger: Slice A extraction-free prep is now complete, and the next branch question is whether to widen breadth again or deepen screening on the existing bounded slices.
- Decision:
  1. Create a dedicated Slice B exemplar bank for `persona_drift_from_assistant`, `lying`, and `optimism`.
  2. Reuse polarity-inverted Slice A structures where the construct is the same axis with reversed sign (`assistant_likeness` -> `persona_drift_from_assistant`, `honesty` -> `lying`).
  3. Add fresh curated optimism sets rather than trying to coerce `politeness` exemplars into a different style construct.
  4. Run the same isolated extraction-free wrapper on Slice B immediately after the bank lands.
- Evidence summary:
  - `known`: the Slice A wrapper and namespace now work end-to-end.
  - `inferred`: an activation-evaluation wrapper is premature until the branch has actual extracted vectors to compare against.
  - `inferred`: Slice B parity gives higher immediate value than Slice C breadth because it completes the extraction-free prep surface for the two live generated slices already in the branch.
- Rationale: this maximizes reusable screening coverage with minimal new code and keeps the branch bounded to already-generated lanes.
- Impact:
  - next work is data/exemplar curation plus one local prompt-prep run
  - Slice C and trait-lane activation-eval wrapper work remain deferred until after Slice B extraction-free outputs land

## [2026-03-11T17:13:30-0500] DECISION: The next trait-lane step is generic rubric registration plus a screening-readiness packet, not a blind remote screening launch
- Trigger: both live trait-lane slices (`A` and `B`) now have extraction, held-out, audit, and extraction-free prep artifacts, but the branch still lacks (1) registered judge rubrics for the new lane IDs and (2) a concrete artifact selecting the first actual P4 screening tranche.
- Decision:
  1. Add a shared rubric registry covering the core traits and all current `trait_lanes_v2` judge rubric IDs.
  2. Wire `scripts/shared/behavioral_eval.py` to that registry without changing legacy trait behavior.
  3. Add a new `week2_trait_lane_screening_readiness.py` sidecar that uses actual branch artifacts to mark which live lanes are ready for first screening and to recommend the first bounded tranche.
  4. Defer remote vector/behavioral smoke launches until this readiness packet exists.
- Evidence summary:
  - `known`: `shared/behavioral_eval.py` only registers core rubrics right now.
  - `known`: `trait_lanes_v2.yaml` names rubric IDs that are not yet first-class in the shared judge path.
  - `inferred`: a remote screening launch before rubric registration and tranche selection would add cost before the branch has the minimum generic screening harness called for in the expansion plan.
- Rationale: this closes an actual Phase P2 gap and yields a concrete next-screen recommendation using current evidence, while staying non-invasive and bounded.
- Impact:
  - immediate output is a readiness/ranking artifact, not model-behavior evidence
  - next branch move after this packet should be the thin actual screening runner for the recommended tranche, not more preparation-only breadth

## [2026-03-11T17:43:20-0500] PIVOT: Trait-lane thin runner should orchestrate existing Week 2 kernels instead of duplicating extraction logic
- Trigger: Code inspection plus explorer review show that the core remote kernels already expose the right seam for branch-safe reuse: `extract_vectors_remote`, `extraction_robustness_remote`, and `run_position_ablation_remote` all accept in-memory prompt payloads and can be called without touching legacy prompt-path assumptions in their local entrypoints.
- Original approach: build a self-contained thin trait-lane smoke runner that reimplemented extraction/vector diagnostics inside a new branch script and added a bespoke judge smoke loop on top.
- New approach:
  1. Rework the new trait-lane screening runner into an orchestrator that reuses the existing remote extraction/robustness/position-ablation kernels directly.
  2. Keep only the genuinely new branch-specific code in the wrapper: readiness/tranche selection, prompt-path resolution from the readiness artifact, and the small behavioral judge-smoke loop.
  3. Preserve the sidecar boundary: do not modify the hardened Week 2 upgraded runner or silently generalize its trait defaults.
- Rationale: this reduces duplicate scientific instruments inside the repo, lowers branch-specific bug surface area, and keeps the lane-expansion branch aligned with the explicit plan to start with thin wrappers rather than a new end-to-end framework.
- Impact:
  - `scripts/week2_trait_lane_behavioral_smoke_run.py` will be rewritten around kernel orchestration.
  - helper tests remain useful, but extraction/vector test coverage should target the orchestration seam rather than duplicated math.
  - the next real branch artifact should still be a bounded `slice_a` screening-depth run, not another planning packet.

## [2026-03-11T17:38:09-0500] PIVOT: Trait-lane screening runner must execute reused Week 2 kernels via a hydration-safe path
- Trigger: The first bounded `slice_a` launch (`ap-6p7GzlWO5F1bQ23d0FNLyZ`) failed immediately with `ExecutionError: Function has not been hydrated with the metadata it needs to run on Modal, because the App it is defined on is not running.` The failure occurred at the first direct imported-kernel call (`extract_vectors_remote.remote(...)`) inside `scripts/week2_trait_lane_behavioral_smoke_run.py`.
- Original approach: Use the new trait-lane runner local entrypoint as an orchestrator that directly calls imported Modal functions from other Week 2 scripts via `.remote()`.
- New approach:
  1. Keep the trait-lane runner as the orchestration surface, but move the actual multi-stage execution into a single hydration-safe remote path inside the runner app.
  2. Reuse the existing Week 2 kernels by calling their raw function bodies (`get_raw_f()`) from within that remote execution path rather than cross-app `.remote()` dispatch.
  3. Keep the branch-specific behavioral-smoke stage in the same runner app and return one combined artifact to the local entrypoint.
- Rationale: The reuse seam is still scientifically correct; the failure is operational, not conceptual. Calling raw kernel bodies inside one running app preserves reuse of the hardened Week 2 logic without requiring deployment/hydration of multiple independent apps or a broader refactor of legacy scripts.
- Impact:
  - `scripts/week2_trait_lane_behavioral_smoke_run.py` will be patched again before the next launch.
  - The next bounded `slice_a` launch should come from the patched runner only after local tests pass again.
  - No new trait-lane widening should happen until a real screening artifact lands.

## [2026-03-11T19:26:42-0500] DECISION: Trait-lane promotion synthesis must consume actual screening executions with polarity normalization, not placeholder hand-scored metrics
- Trigger: Both bounded screening slices (`A` and `B`) are now complete, and the existing `scripts/week2_trait_lane_promotion_packet.py` scaffold still expects manually assembled lane metric dicts that do not match the real screening artifact shape. The new evidence also shows a real orientation issue (`persona_drift_from_assistant` selects a negative bidirectional effect under the current positive-score semantics).
- Decision:
  1. Extend the promotion-packet path so it can read the real `week2_trait_lane_screening_execution_*.json` artifacts plus the readiness artifact.
  2. Normalize lane direction using the observed baseline rubric polarity (`baseline_high` vs `baseline_low`) before interpreting steering/reversal signs.
  3. Treat response-phase persistence as an explicit policy field in the packet. If all screened lanes fail the old `0.7` prompt-vs-response threshold while other screening signals are positive, record that as a tracked limitation rather than silently letting the packet collapse every lane.
  4. Use this packet to recommend follow-on validation candidates, not to auto-promote new claim lanes into the core line.
- Rationale: the branch now has enough real evidence to warrant an honest comparative synthesis. Reusing the placeholder scorer would create fake precision and hide the two real issues the branch surfaced: sign/orientation asymmetry and universal response-phase persistence shortfall.
- Impact:
  - `scripts/week2_trait_lane_promotion_packet.py` will be upgraded around actual screening artifacts.
  - a new promotion/synthesis artifact should become the next branch closeout, replacing the current “next step” ambiguity after Slice A/B.
  - no new remote screening launch is needed before this packet lands.

## [2026-03-12T01:44:26Z] DECISION: Start trait-lane follow-on validation with extraction-free overlap on the three promoted lanes before building branch-local external smoke execution
- Trigger: The first real promotion packet ranked `lying`, `politeness`, and `honesty` as the top follow-on lanes, and all three already have prepared extraction-free eval files while branch-local external-smoke prompts/execution do not yet exist.
- Decision:
  1. Implement a thin branch-local extraction-free follow-on runner for `lying`, `politeness`, and `honesty`.
  2. Reuse the existing extraction-free overlap math and the existing extraction kernel instead of widening the screening runner or mutating the core Week 2 pipeline.
  3. Re-extract vectors inside the same remote app as a pragmatic fallback because the prior screening vector PT artifacts are referenced on the Modal volume but not staged locally in `results/`.
  4. Defer branch-local external smoke execution until after the extraction-free follow-on artifact lands.
- Evidence summary:
  - `known`: the promotion packet recommends `lying`, `politeness`, and `honesty` and marks extraction-free overlap pending for all three.
  - `known`: prepared extraction-free eval files already exist for all three lanes under `prompts/trait_lanes_v2/extraction_free/`.
  - `known`: branch-local external-smoke prompt files do not yet exist on disk.
  - `inferred`: extraction-free overlap is the highest-value next discriminator because it is conceptually aligned with all three recommended lanes and requires the least new infrastructure.
- Rationale: This keeps the branch bounded, uses already-prepared artifacts, and avoids burning time on a second new execution path before collecting the cleaner cross-induction signal.
- Impact:
  - next live run is a trait-lane extraction-free follow-on for `lying`, `politeness`, and `honesty`
  - external-smoke generation/execution becomes the next follow-on after that artifact lands

## [2026-03-12T01:50:00Z] PIVOT: Trait-lane extraction-free follow-on launch must use `modal run`, not raw `python`
- Trigger: The first launch attempt failed immediately with `modal.exception.ExecutionError: Function has not been hydrated with the metadata it needs to run on Modal, because the App it is defined on is not running.`
- Original approach: invoke `scripts/week2_trait_lane_extraction_free_followon.py` directly with `python3`, relying on the `app.local_entrypoint()` wrapper to dispatch the remote function.
- New approach:
  1. Keep the runner code unchanged.
  2. Relaunch via `modal run scripts/week2_trait_lane_extraction_free_followon.py ...` so the app is hydrated before `run_trait_lane_extraction_free_remote.remote(...)` is called.
  3. Treat the failed raw-`python` attempt as an operational launch miss, not a scientific result.
- Rationale: This is the same class of Modal hydration issue already seen elsewhere in the branch. The failure happened before any model execution or artifact generation, so the right response is a launch-path correction, not a code-path rewrite.
- Impact:
  - the PRE-RUN hypothesis and lane/config freeze remain valid
  - the next immediate action is a single corrected relaunch via `modal run`

## [2026-03-12T01:58:00Z] DECISION: Use branch-local external-smoke generation on `lying` and `honesty` before any promotion-packet refresh or Slice C widening
- Trigger: The extraction-free follow-on artifact narrowed the three promoted lanes to one clear leader (`politeness`) plus one fragile truthfulness lane (`lying`) and one null truthfulness lane (`honesty`).
- Decision:
  1. Generate branch-local external-smoke prompts for the two lanes that currently support external-transfer style follow-ons: `lying` and `honesty`.
  2. Keep `politeness` as the lead lane without forcing an external-smoke requirement it does not naturally fit.
  3. Defer any promotion-packet refresh until the truthfulness external-smoke inputs exist and can be executed or explicitly deferred.
- Evidence summary:
  - `known`: `week2_trait_lane_extraction_free_followon_20260312T004752Z.json` upgrades `politeness` to `moderate_overlap`, leaves `lying` `mixed_or_fragile`, and drops `honesty` to `null_overlap`.
  - `known`: a branch-local external-smoke generator scaffold and dry-run plan already exist for `lying` and `honesty`.
  - `inferred`: external smoke is now the cleanest remaining discriminator for whether the truthfulness subfamily deserves more branch budget.
- Rationale: This keeps the branch narrow, uses already-supported lanes, and avoids widening into another family or another synthesis packet before the truthfulness follow-on path has been exercised.
- Impact:
  - immediate next run is local/API-backed prompt generation for `lying` and `honesty`
  - after generation, the branch can decide whether to build/execute a thin external-smoke evaluator or close the truthfulness lane as mixed

## [2026-03-12T02:14:00Z] PIVOT: Truthfulness external-smoke evaluator should reuse the row-encoded low/high prompt schema, not a neutral baseline
- Trigger: Explorer review of the new truthfulness external-smoke prompt files plus the existing trait-lane smoke runner showed that the external-smoke rows already match the held-out smoke schema (`system_low`, `system_high`, `user_query`, `ground_truth`) and that a neutral-baseline evaluator would add an avoidable polarity confound for `lying` vs `honesty`.
- Original approach: evaluate external-smoke prompts under a neutral baseline plus plus/minus steering, modeled after the older machiavellian external-transfer script.
- New approach:
  1. Reuse the paired-prompt logic from the trait-lane smoke path: baseline_low, baseline_high, plus on low, minus on high.
  2. Keep vector orientation packet-driven via the promotion packet's `orientation_sign`, but interpret metrics against the row-encoded low/high rubric direction rather than a neutral baseline.
  3. Preserve the thin wrapper design: re-extract vectors in-app, use shared `behavioral_eval.py`, and emit a branch-local artifact under `results/stage1_extraction/trait_lanes_v2/`.
- Rationale: This makes the evaluator structurally consistent with the branch's existing smoke evidence, respects the opposite rubric polarity of `honesty` vs `lying`, and avoids importing the old `evil`-lane external-transfer assumptions into the new truthfulness branch.
- Impact:
  - `scripts/week2_trait_lane_external_smoke_eval.py` was patched before first launch.
  - the already-written PRE-RUN intent remains valid, but the evaluator design is now paired-prompt rather than neutral-baseline.

## [2026-03-12T02:19:00Z] PIVOT: Trait-lane external-smoke evaluator must include `wandb` + `wandb-key` because the reused extraction kernel depends on them
- Trigger: The first launch of `week2_trait_lane_external_smoke_eval.py` (`ap-ZSNEzR9y7q1Zm7yUqcBaaR`) failed before model execution. The remote function calls `extract_vectors_remote.get_raw_f()`, which internally runs `wandb.init(...)` and therefore requires both the `wandb` Python package and a configured W&B API key secret.
- Original approach: new evaluator image/secrets included only `anthropic` plus the HF token, assuming the thin wrapper itself did not need W&B.
- New approach:
  1. Add `wandb` to the evaluator image.
  2. Add the `wandb-key` Modal secret to the evaluator function.
  3. Relaunch the exact same frozen truthfulness external-smoke config after local validation.
- Rationale: this is an operational dependency of the reused extraction kernel, not a scientific change. The correct fix is to make the wrapper honor the full dependency surface of the reused kernel rather than forking a new extraction path.
- Impact:
  - `scripts/week2_trait_lane_external_smoke_eval.py` must be patched and revalidated.
  - the failed first launch is not scientifically interpretable; no artifact was produced.

## [2026-03-12T03:06:12Z] DECISION: Refresh the trait-lane promotion packet with follow-on evidence and treat it as the branch ranking source of truth
- Trigger: The branch now has two additional discriminators beyond Slice A/B screening: the extraction-free follow-on (`politeness` pass, `lying` mixed, `honesty` fail) and the truthfulness external-smoke evaluator (`lying` one-sided fail, `honesty` mixed fail).
- Decision:
  1. Extend `scripts/week2_trait_lane_promotion_packet.py` to optionally ingest completed extraction-free follow-on and external-smoke evaluation artifacts.
  2. Re-rank the branch using the original screening evidence plus the new follow-on evidence rather than continuing to rely on the original A/B-only packet.
  3. Treat the refreshed packet as the new branch ranking source of truth:
     - `politeness` = promoted lead lane
     - `lying` = conditional follow-on candidate
     - `honesty` = deprioritized after follow-ons
- Evidence summary:
  - `known`: `week2_trait_lane_extraction_free_followon_20260312T004752Z.json` yields `politeness=moderate_overlap`, `lying=mixed_or_fragile`, `honesty=null_overlap`.
  - `known`: `week2_trait_lane_external_smoke_eval_20260312T011734Z.json` yields `lying` one-sided and `honesty` mixed/one-sided, with `overall_pass=false`.
  - `inferred`: continuing to rank `honesty` alongside `politeness` and `lying` would ignore the very follow-on discriminators the branch was created to run.
- Rationale: the branch is now past breadth screening and into selection. The packet must reflect all executed evidence, not just the first-pass screening slice.
- Impact:
  - superseding packet artifact: `results/stage1_extraction/trait_lanes_v2/week2_trait_lane_promotion_packet_20260312T030612Z.json`
  - no case remains for Slice C widening before a separate decision on deeper Week 2 validation for `politeness` (and optionally conditional `lying`)

## [2026-03-11T22:18:00-0500] DECISION: Open trait-lane deeper-validation via a branch-local packet and block launch until `politeness` prompt depth is expanded
- Trigger: the refreshed promotion packet (`week2_trait_lane_promotion_packet_20260312T030612Z.json`) leaves `politeness` as the only supported lead lane, but the branch still has screening-depth prompt counts (`24` extraction, `12` held-out) rather than anything close to upgraded Week 2 evidence depth.
- Decision:
  1. Add a branch-local deeper-validation packet instead of pretending the promoted lane is already ready for the core upgraded Week 2 runner.
  2. Treat `politeness` as the default deeper-validation lane; keep `lying` conditional and opt-in rather than co-equal.
  3. Freeze a branch-local deeper-validation sidecar profile at `48` extraction pairs and a `10/10/10` held-out split (`30` total) as an explicitly lighter-than-core intermediate checkpoint.
  4. Keep the core full-upgrade reference visible at `100` extraction pairs and `15/15/20` held-out (`50` total), but do not claim branch lanes are at that depth yet.
  5. Expose append-safe `--target-total` controls on the trait-lane extraction/held-out generators so the branch can close this depth gap without overwriting screening artifacts.
- Evidence summary:
  - `known`: `week2_trait_lane_deeper_validation_packet_20260312T031754Z.json` selects `politeness` by default and marks `launch_recommended_now=false`.
  - `known`: the packet records current counts `24` extraction / `12` held-out and explicit deeper-sidecar blockers `24<48` and `12<30`.
  - `known`: append-safe dry-run expansion plans now exist for `politeness` at `48` extraction and `30` held-out (`*_generation_plan_20260312T031754Z.json`).
  - `inferred`: launching a deeper-validation run before prompt expansion would mostly measure thin-data variance rather than lane quality.
- Rationale: the branch now needs more evidence depth, not more ranking logic. A packetized gate keeps the move honest, preserves the branch namespace, and avoids treating screening-depth prompts as if they were upgraded Week 2 inputs.
- Impact:
  - next branch execution should be append-safe prompt expansion for `politeness` first
  - the deeper-validation launch decision now has a concrete source of truth instead of an ad hoc judgment call

## [2026-03-11T22:43:00-0500] DECISION: Reuse the core upgraded Week 2 validation kernel for trait-lane deeper validation, but disable cross-trait bleed inside the branch-local sidecar
- Trigger: `politeness` now satisfies the branch-local deeper-validation depth gate (`48` extraction / `30` held-out) and the next step is a bounded Week 2-style validation run rather than more prompt-generation work.
- Decision:
  1. Add a branch-local wrapper (`scripts/week2_trait_lane_deeper_validation_run.py`) that reuses `extract_vectors_remote.get_raw_f()` and `run_trait_validation_remote.get_raw_f()` inside one Modal app.
  2. Treat the current `deeperv1` prompt files as the active branch input set via the suffixed deeper-validation packet (`week2_trait_lane_deeper_validation_packet_20260312T032309Z.json`).
  3. Disable cross-trait bleed for this sidecar run rather than forcing custom lanes into the core `DEFAULT_TRAITS` matrix. Keep this explicit in the execution packet/report rather than silently faking an off-target comparison.
  4. Keep the rest of the upgraded validation kernel intact: held-out split, judge calibration, random/shuffled controls, specificity, and relative-only coherence.
- Evidence summary:
  - `known`: the updated deeper-validation packet (`week2_trait_lane_deeper_validation_packet_20260312T032309Z.json`) now reports `launch_recommended_now=true` for `politeness` with `deeperv1` prompt paths and no remaining sidecar blockers.
  - `known`: local validation for the wrapper path passed (`py_compile`, `test_week2_trait_lane_deeper_validation_run.py`, `test_week2_trait_lane_*py`).
  - `known`: the core upgraded validation kernel cannot safely score branch-local lanes against the hardcoded `DEFAULT_TRAITS` cross-bleed matrix without an explicit override.
  - `inferred`: a sidecar run that pretends `politeness` can already participate in the core cross-trait matrix would create fake structure rather than real evidence.
- Rationale: the branch needs real deeper-validation evidence now, but it should not mutate the core Week 2 interpretation contract just to accommodate one promoted sidecar lane. Explicitly disabling cross-trait bleed here is cleaner and scientifically more honest than shoehorning `politeness` into the legacy off-target rubric set.
- Impact:
  - new runner: `scripts/week2_trait_lane_deeper_validation_run.py`
  - core kernel patch: `scripts/week2_behavioral_validation_upgrade.py` now supports explicitly disabled cross-trait bleed for custom sidecar callers
  - next step: launch a bounded `politeness` deeper-validation run using the `deeperv1` prompt files and the branch-local sidecar profile

## [2026-03-11T22:53:00-0500] PIVOT: Skip the eager volume reload when the trait-lane deeper-validation wrapper hands off from extraction to upgraded validation
- Trigger: The first bounded `politeness` deeper-validation launch (`ap-LtavuhNzLLXoE0NpA8gtcC`) completed extraction but failed before validation because `run_trait_validation_remote()` called `vol.reload()` while the same container still had an open HuggingFace/Xet log file from the extraction stage.
- Original approach: Reuse the core upgraded Week 2 validation kernel with `resume_from_checkpoint=True` and the kernel's default eager `vol.reload()` path.
- New approach:
  1. Add an explicit `checkpoint_reload_before_resume` flag to `run_trait_validation_remote()` and default it to `True` for legacy callers.
  2. For the branch-local deeper-validation wrapper, keep `resume_from_checkpoint=True` but set `checkpoint_reload_before_resume=False` so the resumed state is read directly from the mounted volume without forcing a reload inside the same container.
  3. Relaunch the bounded `politeness` run with a fresh run token after revalidation.
- Rationale: the failure was operational, not scientific. The wrapper's single-container reuse pattern is still correct, but the eager volume reload is incompatible with the extraction stage's open file handles. Skipping the reload for this sidecar preserves resumability intent without reintroducing the known Modal open-file conflict.
- Impact:
  - patched core runner: `scripts/week2_behavioral_validation_upgrade.py`
  - patched wrapper: `scripts/week2_trait_lane_deeper_validation_run.py`
  - prior app `ap-LtavuhNzLLXoE0NpA8gtcC` must be treated as failed operationally and excluded from interpretation

## [2026-03-12T08:05:44-0500] DECISION: Pause further trait-lane deeper-validation launches until the branch review objections are closed
- Trigger: The new deep branch review argues, correctly in the main, that the current trait-lane branch has overcommitted to `politeness` without yet establishing distinctness from `sycophancy`, has soft-pedaled universal response-phase persistence failure, and disabled cross-trait bleed exactly where it matters most.
- Decision:
  1. Freeze new `politeness` deeper-validation launches until a short remediation tranche closes four items:
     - `politeness` vs `sycophancy` overlap/distinctness analysis
     - branch-local cross-trait bleed using at least `sycophancy` and `assistant_likeness`
     - explicit response-phase persistence policy freeze
     - execution redesign from single-app wrapper to split extraction + validation launches
  2. Reframe `politeness` as the tractability-first lead lane rather than a scientifically preferred lane.
  3. Reclassify `lying` from `conditional_followon_candidate` to provisional negative / construct-invalid under the current protocol.
  4. Reclassify `honesty` from effectively closed to secondary unresolved with an RLHF-asymmetry caveat.
- Evidence summary:
  - `known`: `week2_trait_lane_promotion_packet_20260312T030612Z.json` ranks `politeness` first but also records failed response-phase persistence for all screened lanes.
  - `known`: `week2_trait_lane_extraction_free_followon_20260312T004752Z.json` gives `politeness=moderate_overlap`, `lying=mixed_or_fragile`, `honesty=null_overlap`.
  - `known`: `week2_trait_lane_external_smoke_eval_20260312T011734Z.json` shows `lying` plus-steering moves in the wrong direction and `honesty` is one-sided/mixed.
  - `known`: the deeper-validation sidecar was intentionally launched with cross-trait bleed disabled.
  - `inferred`: continuing deeper validation without closing distinctness/bleed/persistence would spend GPU on an interpretation contract that is currently too weak.
- Rationale: The branch is not being abandoned. The review exposes a real interpretive gap between "cleanest tractable signal" and "best persona-circuit test". That gap should be closed before the next expensive validation attempt.
- Impact:
  - the current promotion packet remains a record of prior ranking, but it is no longer the sole interpretation source
  - next branch work is a remediation tranche, not another blind relaunch
  - `history/reviews/20260312-reviewer-trait-lane-branch-verbatim.md` and `history/20260312-trait-lane-review-reconciliation-plan-v1.md` are now part of the active branch context

## [2026-03-12T08:25:00-0500] DECISION: Treat assistant-style overlap, not sycophancy overlap, as the binding distinctness confound for `politeness`
- Trigger: The first review-driven overlap diagnostic (`week2_trait_lane_overlap_diagnostic_20260312T131958Z.json`) was run against the authoritative core `sycophancy` vector artifact and the saved `politeness` slice-A vectors.
- Decision:
  1. Mark the specific `politeness` vs `sycophancy` overlap concern as materially weakened under the current cosine criterion.
  2. Shift the next distinctness remediation target to `assistant_likeness` (while still keeping `sycophancy` in the bleed reference set).
  3. Keep the deeper-validation launch freeze in place; this diagnostic narrows the confound, but does not close the distinctness problem.
- Evidence summary:
  - `known`: selected-pair overlap (`sycophancy L12` vs `politeness L15`) = `0.0651`.
  - `known`: same-layer max abs overlap across layers `11..16` = `0.1812`.
  - `known`: cross-layer max abs overlap across `11..16 x 11..16` = `0.1812`.
  - `known`: branch-internal `politeness` vs `assistant_likeness` same-layer cosine ranges from `0.4315` to `0.6284`, substantially higher than the `sycophancy` overlap.
- Rationale: The branch now has artifact-backed evidence that `politeness` is not just a rotated copy of the core `sycophancy` vector. The stronger remaining threat is that it is an assistant-style or tone-transfer lane. That is the confound the next bleed/distinctness tranche should target directly.
- Impact:
  - next branch implementation should prioritize branch-local bleed/reference support for `assistant_likeness` and `sycophancy`
  - no new `politeness` deeper-validation launch should happen until that support exists

## [2026-03-12T08:27:00-0500] DECISION: Treat branch-local bleed support as closed for the next `politeness` validation packet, while keeping the launch freeze for policy/runtime items
- Trigger: Fresh packet regeneration after the review showed that the current deeper-validation profile and execution contract can already carry real reference-lane bleed against `sycophancy` and `assistant_likeness`.
- Decision:
  1. Mark the branch-local bleed/reference wiring item as closed for the next `politeness` deeper-validation attempt.
  2. Keep the launch freeze active because two higher-level issues are still open:
     - response-phase persistence policy is not yet frozen
     - the next attempt should use split extraction + validation launches rather than the prior single-app wrapper
  3. Record the dry-run artifact as the current source of truth for the branch-local launch contract instead of relying on older bleed-disabled packets.
- Evidence summary:
  - `known`: `week2_trait_lane_deeper_validation_packet_20260312T132600Z.json` reports `cross_trait_bleed_enabled=true`, `cross_trait_bleed_reference_traits=["sycophancy","assistant_likeness"]`, and `cross_trait_bleed_max_fraction=0.3`.
  - `known`: `week2_trait_lane_deeper_validation_dryrun_packet_20260312T132621Z.json` preserves those same reference traits in the launch contract for the selected lane `politeness`.
  - `known`: local validation passed on the packet/run helper stack (`py_compile`, focused packet/run/overlap tests, full `test_week2_trait_lane_*py` suite).
  - `inferred`: the remaining blocker is no longer "can the branch measure bleed?" but "what exact policy/runtime contract should govern the next expensive validation run?"
- Rationale: The reviewer objection was about an interpretive blind spot, not about requiring a specific science result from bleed before any packet refresh. Once the packet/runner path genuinely carries the reference rubrics, the blind spot is narrowed enough to move the freeze boundary up to the unresolved policy and execution items.
- Impact:
  - the current branch freeze checklist should now treat bleed wiring as completed
  - the next branch work should focus on persistence-policy freeze and split-launch redesign, not more packet plumbing

## [2026-03-12T08:40:06-0500] DECISION: Freeze response-phase persistence policy explicitly and replace the legacy single-app deeper-validation wrapper with split extraction/validation launches
- Trigger: The review-required persistence policy and split-launch redesign are now code-backed and artifact-backed, so the remaining blocker is no longer planning ambiguity.
- Decision:
  1. Freeze response-phase persistence under the superseding branch policy recorded in `week2_trait_lane_response_phase_policy_packet_20260312T133907Z.json`.
  2. Treat prompt-vs-response persistence as a tracked limitation, not a hard screening/launch gate, while retaining the legacy `0.7` threshold for reporting.
  3. Deprecate the legacy single-app wrapper for the next `politeness` deeper-validation attempt and use split extraction followed by split validation instead.
  4. Resume the branch operationally with an extraction-only split launch first; validation waits for the persisted vectors artifact from that extraction phase.
- Evidence summary:
  - `known`: `week2_trait_lane_response_phase_policy_packet_20260312T133907Z.json` freezes `frozen_policy.status=pre_registered_superseding_policy` with `n_response_phase_pass=0`.
  - `known`: refreshed deeper packet `week2_trait_lane_deeper_validation_packet_20260312T133907Z.json` now snapshots the persistence policy and records `execution_policy.preferred_launch_mode=split_extract_validate`.
  - `known`: split dry-run extraction packet `week2_trait_lane_deeper_validation_split_extract_dryrun_packet_20260312T133918Z.json` is launch-ready for `politeness`.
  - `known`: split dry-run validation packet `week2_trait_lane_deeper_validation_split_validate_dryrun_packet_20260312T133918Z.json` is structurally ready but blocked by `missing_vectors_pt`, exactly as expected before the extraction phase lands.
  - `known`: local validation passed for the new packet/policy/split stack (`test_week2_trait_lane_response_phase_policy_packet.py`, `test_week2_trait_lane_deeper_validation_packet.py`, `test_week2_trait_lane_deeper_validation_split.py`, full `test_week2_trait_lane_*py` suite).
- Rationale: This closes the remaining governance gap before spending more GPU. The next evidence step is now a narrow operational move with clear blast-radius control: extract vectors first, persist them locally, then validate in a second launch.
- Impact:
  - next active branch execution: extraction-only split run for `politeness`
  - the prior single-app wrapper remains in-repo for traceability but should not be used for the next attempt

## [2026-03-12T08:47:00-0500] PIVOT: Patch the upgraded Week 2 validator to use the shared branch-capable rubric registry before rerunning split validation
- Trigger: The first split validation run (`ap-usUnmHuthf7Raw436KsqPP`) progressed cleanly through `model_loaded`, `split_ready`, and `baseline_start`, then failed with `KeyError: 'politeness'` inside `week2_behavioral_validation_upgrade.py` because the validator still used a core-only hardcoded `RUBRICS` map.
- Original approach: Reuse the split validation path without changing the core validator, assuming branch-local trait rubrics already flowed through from the screening stack.
- New approach:
  1. Import the shared rubric registry from `scripts/shared/trait_rubrics.py` into `week2_behavioral_validation_upgrade.py`.
  2. Replace the local core-only rubric map/header with the shared versions so branch-local lanes like `politeness` can be judged directly.
  3. Add a direct regression test for `_judge_prompt("politeness", ...)`.
  4. Relaunch the split validation phase against the same persisted vectors artifact after local revalidation.
- Rationale: The split redesign is operationally working; the failure was not the wrapper or the launch contract. The real blocker is a core evaluator assumption that only the legacy three traits exist. That assumption must be removed before the branch can produce valid validation evidence.
- Impact:
  - patched core file: `scripts/week2_behavioral_validation_upgrade.py`
  - patched test: `tests/test_week2_validation_utils.py`
  - next branch action: rerun split validation only, reusing the successful extraction artifact

## [2026-03-12T14:28:59-0500] DECISION: Freeze independent trait-lane promotion under the current evidence stack and treat `politeness` as assistant-style modulation, not an independent persona lane
- Trigger: The completed split `politeness` deeper-validation rerun now exists, and the branch finally has the full evidence stack required to answer the promotion question without relying on provisional screening labels.
- Decision:
  1. Adopt `week2_trait_lane_adjudication_packet_20260312T192833Z.json` as the source-of-truth branch verdict.
  2. Freeze independent promotion of any new trait lane from `trait_lanes_v2` under the current evidence stack.
  3. Reclassify `politeness` as a strong-but-non-distinct assistant-style modulation lane, not an independent persona-circuit promotion candidate.
  4. Reclassify `lying` as a negative finding / construct-invalid lane under the current protocol.
  5. Reclassify `honesty` as a secondary unresolved RLHF-asymmetry lane, not an active promotion candidate.
- Evidence summary:
  - `known`: adjudication packet status = `no_independent_promotion_under_current_evidence`.
  - `known`: `politeness` deeper validation selected `layer=13`, `alpha=2.0`, `selected-test bidirectional effect=46.3333`, `judge_kappa=0.8387`, coherence/capability/specificity all pass.
  - `known`: the same `politeness` artifact fails `cross_trait_bleed_pass` because `assistant_likeness` off-target effect (`47.2333`) slightly exceeds the target-lane effect (`46.3333`), and it fails `control_test_pass` with `control_test_score=50.0`.
  - `known`: overlap diagnostic keeps `politeness` vs core `sycophancy` low (`selected_pair_abs=0.0651`) while `politeness` vs `assistant_likeness` remains high (`max_abs_same_layer_overlap=0.6284`).
  - `known`: `lying` external smoke moves in the wrong direction on plus-steering (`plus_vs_baseline=-3.125`).
  - `known`: `honesty` remains null on extraction-free overlap and mixed / one-sided on external smoke.
- Rationale: The branch has answered its selection question. It found a lane with strong behavioral steerability, but the stronger current interpretation is assistant-style modulation rather than a new independent persona lane. Continuing to treat `politeness` as independently promotable would overstate the evidence.
- Impact:
  - no new trait-lane should enter the main persona-circuit claim path without a redesign that resolves assistant-style distinctness
  - any further branch work should be framed as redesign / falsification support, not promotion follow-through

## [2026-03-12T14:49:47-0500] DECISION: Open the trait-lane redesign tranche with null-control first and prompt-sensitivity second
- Trigger: The adjudication packet closed the promotion question, but the reviewer-raised redesign items (`null-lane` and `prompt-sensitivity`) were still only tracked as pending actions.
- Decision:
  1. Materialize the redesign tranche as explicit artifacts rather than leaving it as prose in the review reconciliation memo.
  2. Prioritize a matched null-control screen before any further `politeness`-specific science run.
  3. Prioritize prompt-sensitivity as the second redesign lane, using bounded category-balanced subsets at the selected `politeness` configuration (`layer=13`, `alpha=2.0`).
  4. Defer any assistant-likeness-specific distinctness run until after null-control and prompt-sensitivity evidence lands.
- Evidence summary:
  - `known`: adjudication packet `week2_trait_lane_adjudication_packet_20260312T192833Z.json` freezes independent promotion under the current evidence stack.
  - `known`: null-control packet `week2_trait_lane_null_control_packet_20260312T194931Z.json` defines a low-cost matched false-positive test via category-stratified label permutation over the existing `politeness` prompt family.
  - `known`: prompt-sensitivity packet `week2_trait_lane_prompt_sensitivity_packet_20260312T194931Z.json` defines balanced perturbation subsets (`12` extraction rows, `8` held-out rows) and fixed retention gates at the selected configuration.
  - `known`: redesign packet `week2_trait_lane_redesign_packet_20260312T194947Z.json` sets `next_remote_priority=run_null_control_screen` and explicitly forbids another blind `politeness` rerun or Slice C widening.
- Rationale: The branch no longer needs more ranking logic. It needs falsification support. Null-control first answers whether the screening pipeline is permissive; prompt-sensitivity second answers whether the lead lane is wording-fragile. Only then is further distinctness work justified.
- Impact:
  - next remote branch work should implement the null-control screen, not another promotion-oriented lane run
  - prompt-sensitivity is now a defined second step rather than an open-ended reminder

## [2026-03-12T15:09:00-0500] PIVOT: Implement the redesign null-control as a dedicated execution wrapper around the existing screening remote instead of extending the tranche runner glob path
- Trigger: The redesign packet requires a matched false-positive control, but routing that control through the normal screening packet/artifact prefixes would contaminate branch promotion globbing and blur the distinction between real lanes and falsification lanes.
- Original approach: Extend `week2_trait_lane_behavioral_smoke_run.py` main entrypoint to accept a control mode and reuse the standard screening artifact naming path.
- New approach:
  1. Generate explicit permuted prompt files under `prompts/trait_lanes_v2/null_controls/`.
  2. Build a dedicated `week2_trait_lane_null_control_run.py` wrapper that reuses `run_trait_lane_screening_remote` unchanged.
  3. Emit distinct artifact prefixes (`week2_trait_lane_null_control_*`) so promotion-packet globbing cannot accidentally consume null-control outputs.
- Rationale: The scientific requirement is matched-kernel comparability; the governance requirement is keeping falsification artifacts out of the promotion source-of-truth path. A thin dedicated wrapper satisfies both with less risk than making the tranche runner multi-mode.
- Impact:
  - added dedicated null-control prompt generation + execution scripts/tests
  - next remote action is the null-control screen, not another `politeness` rerun
  - branch interpretation after this run will explicitly compare the null against the real `politeness` screening frontier

## [2026-03-12T15:10:30-0500] PIVOT: Wrap the null-control screen in its own Modal app after the first launch failed on imported-function hydration
- Trigger: The first attempt to launch `week2_trait_lane_null_control_run.py` failed locally with `modal.exception.ExecutionError` before any remote app ran because `run_trait_lane_screening_remote` was imported from another script/app and called directly from a non-hydrated context.
- Original approach: Call the imported screening Modal function directly from the dedicated null-control wrapper.
- New approach:
  1. Give `week2_trait_lane_null_control_run.py` its own `modal.App` and `@app.local_entrypoint()`.
  2. Add a wrapper remote function in that app that calls `run_trait_lane_screening_remote.get_raw_f()` so the execution kernel stays identical while hydration is owned by the null-control app.
  3. Harden default artifact resolution by selecting source packets via `artifact_type`, not just filename glob, to avoid the earlier dry-run naming collision contaminating launch inputs.
- Rationale: The failure was operational and local. The correct fix is to preserve the matched-kernel design while making the execution context valid on Modal. This avoids widening the main screening runner or weakening comparability.
- Impact:
  - null-control launch path is now app-hydrated and dry-run validated
  - rerun can proceed without changing the scientific contract of the control itself

## [2026-03-12T15:12:00-0500] PIVOT: Launch the null-control runner via `modal run`, not raw `python`
- Trigger: A second launch attempt still failed locally before any remote app started, confirming that the remaining issue is the invocation path, not the wrapper design or the control packet.
- Original approach: invoke `scripts/week2_trait_lane_null_control_run.py` with `python3` after adding a local-entrypoint-capable wrapper app.
- New approach:
  1. Keep the dedicated null-control wrapper code.
  2. Relaunch via `modal run scripts/week2_trait_lane_null_control_run.py ...` (or module form if needed) so Modal hydrates the app before the local entrypoint dispatches the remote screen.
  3. Treat both raw-`python` failures as operational launch misses only.
- Rationale: This matches the branch precedent already logged for extraction-free follow-on. The failure still occurs before any remote app or W&B execution, so the science state is unchanged.
- Impact:
  - next immediate action is a single corrected relaunch via `modal run`
  - no change to the frozen null-control hypothesis, packet, or generated prompt inputs

## [2026-03-12T15:20:30-0500] PIVOT: Rerun the null-control screen after adding the missing `readiness_artifact_path` packet field
- Trigger: The first real null-control app (`ap-1tXFTxszQBLo98Z3Bx1Ewa`) completed extraction, robustness, and behavioral smoke, then failed while building the combined screening report because the synthetic packet omitted `readiness_artifact_path`.
- Original approach: Treat the dedicated null-control packet as sufficient with only branch-specific fields.
- New approach:
  1. Add `readiness_artifact_path` to the synthetic execution packet, pointing to the authoritative null-control planning packet.
  2. Revalidate locally and relaunch the exact same null-control inputs.
  3. Treat the first real run as a partial operational failure with scientifically useful observed metrics but no terminal artifact.
- Rationale: The expensive kernel already showed the null is weak (`bootstrap_p05 < 0`, low train-vs-heldout, smoke best effect only `14.25` on `n=4`). The missing field is a report-assembly bug, not a signal problem. A narrow rerun is justified to obtain the final artifact cleanly.
- Impact:
  - no change to the frozen null-control prompt files or hypothesis
  - next immediate action is a single rerun of the same control with the packet-field fix

## [2026-03-12T15:32:30-0500] DECISION: Treat the matched `politeness` null-control as passed and advance the redesign branch to prompt-sensitivity
- Trigger: The repaired null-control rerun (`ap-HAH6nNXETOH7hY8feukAD0`) reached a terminal artifact with the same scientific profile as the partial first pass.
- Decision:
  1. Adopt `week2_trait_lane_null_control_execution_20260312T202047Z.json` as the source-of-truth null-control result.
  2. Mark the first redesign step (`null_control`) as passed: the screening pipeline did not promote the matched label-permutation control.
  3. Advance the branch to the second redesign step defined in `week2_trait_lane_redesign_packet_20260312T194947Z.json`: prompt-sensitivity for `politeness` at the selected configuration.
- Evidence summary:
  - `known`: final null-control evaluation reports `screening_status=hold` and `overall_false_positive_alert=false`.
  - `known`: the control remains weak on stability metrics (`bootstrap_p05=-0.6763`, `train_vs_heldout=0.2524`, `response_phase_persistence=0.2808`).
  - `known`: the best smoke condition has `absolute_bidirectional_effect=14.25`, but the oriented effect is negative (`-14.25`) and does not cross the promotion frontier.
  - `inferred`: the current branch concern is no longer generic screening permissiveness; it narrows to wording sensitivity and assistant-style distinctness.
- Rationale: The null-control falsification step did its job. Continuing to iterate on the same control would have low information value. The redesign sequence should now move forward as precommitted.
- Impact:
  - next active branch execution should be the prompt-sensitivity sidecar
  - independent lane promotion remains frozen unless prompt-sensitivity and any later distinctness work change the evidence stack
