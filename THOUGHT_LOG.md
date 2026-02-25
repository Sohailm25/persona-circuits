# THOUGHT LOG
Running log of insights, theories, surprising findings, adjacent curiosities, and follow-up research ideas.
Log freely — anything that could strengthen the paper, complicate interpretation, or open a new direction.
Format: ## [DATE] [CATEGORY] — [title]

---

## PENDING ACTIONS

Items derived from THOUGHT_LOG entries that require concrete changes before a specific phase or run.
Review this section before starting any new phase or writing any pre-run checkpoint.

- [ ] Add cross-persona selectivity control: when ablating Sherlock circuit, measure Watson behavior — should be unaffected. Required before: Phase C (Causal Validation / Week 6). See entry 2026-02-24 METHODOLOGY RISK.
- [ ] Add null-feature ablation baseline: identify features with matched activation magnitude but no persona semantics; ablate as negative control. Required before: Phase C. See entry 2026-02-24 METHODOLOGY RISK.
- [ ] Decompose Y into 3–4 orthogonal behavioral facets (lexical markers, domain knowledge, out-of-character refusal, response style) and test necessity/sufficiency for each separately. Required before: Phase B behavioral scoring design (Week 3). See entry 2026-02-24 METHODOLOGY RISK.
- [ ] Add one sentence to intro framing PSM as mechanizing Shanahan et al.'s simulator claim. Required before: paper writing (Week 9). See entry 2026-02-24 THEORY.
- [ ] Re-run SAE reconstruction sanity using stage-specific hooks/preprocessing before trusting any concentration claims. Required before: Week 3 SAE decomposition interpretation. See entry 2026-02-24 INFRA OBSERVATION.
- [ ] Calibrate Week 2 judge reliability (rubric/prompt/parse robustness) before accepting final layer-alpha selections. Required before: Week 2 closeout. See entry 2026-02-25 FINDING.
- [ ] Choose launch tranche and concurrency cap for the upgraded Week 2 matrix (primary vs replication vs stress) before execution. Required before: Week 2 upgraded run launch. See entry 2026-02-25 METHODOLOGY DESIGN.
- [ ] Run Week 2 external benchmark transfer check for selected layer/alpha per trait (beyond held-out generated prompts). Required before: Week 2 closeout. See entry 2026-02-25 LITERATURE SECOND PASS.
- [ ] Run extraction-method robustness A/B (last prompt token vs response-token average) on a sampled subset. Required before: Week 2 closeout interpretation. See entry 2026-02-25 LITERATURE SECOND PASS.
- [ ] Perform manual 5-example judge concordance spot-check after upgraded primary runs. Required before: Week 2 final layer/alpha lock. See entry 2026-02-25 LITERATURE SECOND PASS.
- [ ] Run hallucination known-fact benchmark check (TruthfulQA-style) in upgraded Week 2 validation before closeout claim. Required before: Week 2 closeout. See entry 2026-02-25 METHODOLOGY GAP.
- [ ] Run rollout-stability sensitivity check (confirm rollouts 3 vs 5) on primary-tier selected combos. Required before: Week 2 final closeout claim. See entry 2026-02-25 METHODOLOGY UPDATE.

## RESOLVED ACTIONS

- [x] Freeze/hash prompt inputs in validation artifacts — integrated into upgraded runner + explicit plan artifact with held-out hashes. Source: 2026-02-24 METHODOLOGY RISK. Resolved on 2026-02-25 during upgrade pipeline build.
- [x] Add judge API-throttle resilience (RPM throttle + retry/backoff + jitter + retryable error handling) before large parallel launch. Source: 2026-02-25 METHODOLOGY DESIGN. Resolved on 2026-02-25 in upgraded Week 2 runner/planner.
- [x] Add coherence/directionality/random-control-strength gates to Week 2 upgraded validation. Source: 2026-02-25 LITERATURE SECOND PASS. Resolved on 2026-02-25 before launch.
- [x] Tighten Week 2 acceptance gates to include secondary parse pass, non-trait control-test threshold, specificity threshold, and strict capability-availability behavior by default. Source: 2026-02-25 METHODOLOGY GAP. Resolved on 2026-02-25 in upgraded runner/planner.
- [x] Implement hallucination known-fact (TruthfulQA-style) check in upgraded Week 2 runner and planner. Source: 2026-02-25 METHODOLOGY GAP. Resolved on 2026-02-25; execution evidence still pending.
- [x] Complete rerun smoke validation after `top_k=None` patch and verify `steering_norm_diagnostics.ratio_stats` fields in report artifact. Source: 2026-02-25 METHODOLOGY/IMPLEMENTATION. Resolved on 2026-02-25 in run `i1pg2y8c` (`week2_behavioral_validation_upgrade_sycophancy_20260225T131007Z.json`).

---

## 2026-02-24 [METHODOLOGY RISK] — The Selectivity Gap in Necessity/Sufficiency Testing

**Type:** action
**Source:** Twitter/X critique of standard MechInterp practice

**The core issue:**
Standard MechInterp evidence is:
- Necessity: ablate X → Y vanishes
- Sufficiency: insert X → Y appears

But this misses **selectivity**: does X affect other stuff? Is Y just downstream of that other stuff?

MMLU/perplexity checks don't catch this — they're too coarse and too general.

**Three specific failure modes this creates for us:**

1. **Non-selective ablation:** We ablate "Sherlock persona features" and persona-consistent behavior vanishes. But did we *selectively* remove persona representation, or did we degrade general character-maintenance ability? If ablating any coherent-character features kills Sherlock behavior, we haven't found a Sherlock circuit — we've found a general coherence circuit.

2. **Y definition mismatch:** "Persona-consistent behavior" bundles many facets — lexical choices (deductive language, "elementary"), domain knowledge (Baker Street, Watson), refusal of out-of-character requests. The subset captured by our necessity test may not be the same subset captured by our sufficiency test. If we're not testing the same Y in both directions, the evidence doesn't compose.

3. **Non-unique necessity:** We need to confirm that ablating some *other* X' (a non-persona feature of similar activation magnitude) does NOT also make Y vanish. If it does, X isn't specially necessary — it's just any disruption to that representation subspace.

**What this means for our experimental design:**

We should add selectivity controls to Phase C ablation:

a) **Cross-persona selectivity:** When we ablate the Sherlock circuit, does *Watson* behavior also degrade? It should NOT if the circuit is truly persona-specific. Selective degradation of Sherlock-only behavior is the gold standard.

b) **Null-feature ablation baseline:** Identify features with similar activation magnitudes to our target features but no persona semantic content (e.g., syntax/grammar features). Ablate those. If persona behavior degrades similarly, our effect is non-specific.

c) **Multi-facet Y decomposition:** Define persona-consistency as 3–4 orthogonal behavioral facets and measure necessity/sufficiency for *each* separately. Show the circuit is necessary/sufficient for the same facets in both directions.

d) **Perplexity alternative:** Instead of MMLU, measure behavior on a *different* persona prompt. If Sherlock circuit ablation also kills our model's ability to do Watson, that's leakage.

**Relationship to existing safeguards:**
- Our Li & Janson (2024) resample ablation partially addresses the coherence collapse failure mode (§4 of MECH_INTERP_GUIDANCE.md) but doesn't address selectivity
- Our necessity threshold ≥80% and sufficiency ≥60% are blind to whether we're measuring the *right* Y

**Paper implication:**
If we find a Sherlock circuit, the strongest paper claim would be:
> "Ablating these features selectively disrupts Sherlock-consistent behavior while leaving Watson-consistent behavior intact, establishing that the circuit is persona-specific rather than a general character-coherence mechanism."

This is a stronger and more defensible claim than "ablating X makes Sherlock behavior vanish."

**Open question:**
Can we even find a circuit that's persona-specific at this granularity, or does the PSM predict that all persona-consistent behavior routes through a shared "character simulator" substrate? If the latter, selectivity will be structurally impossible — which would itself be an interesting finding.

---

## 2026-02-24 [THEORY] — Shanahan et al. (2023): LLMs as Non-Deterministic Simulators

**Type:** theory + action (intro framing)
**Source:** Shanahan, McDonell, Reynolds, "Role play with large language models," Nature 2023

**Core claim:** An LLM is best understood not as a single agent with beliefs/goals, but as "a non-deterministic simulator capable of role-playing an infinity of characters." The assistant persona is just one character in this infinite space.

**Why this matters for our experiment:**
- Directly foundational for PSM: Marks et al. (2026) inherits and mechanizes this framing
- Our experiment is asking *where* in the network the "character selection" happens and how it's encoded
- If Shanahan's framing is correct, there should be mechanistically identifiable "character context" representations that gate which character is being simulated
- Our persona vectors and SAE feature analysis are, in effect, testing the mechanistic substrate of Shanahan's "simulator" hypothesis

**Interesting tension with PSM:**
Shanahan et al. argue the model is simultaneously multiple characters in superposition until "collapsed" by context. PSM adds a specific claim: that collapse happens via a discrete persona-selection module with identifiable geometric structure. If we find clear circuit evidence, we're advancing PSM. If the representation is diffuse/entangled, it's more consistent with pure Shanahan.

**Follow-up question for the paper:**
Worth a sentence in the intro: "The character-simulator framing (Shanahan et al., 2023) predicts that LLMs maintain latent representations of multiple simultaneous characters. The Persona Selection Model (Marks et al., 2026) makes this concrete by proposing a specific geometric structure for character selection. Our circuit analysis tests whether this structure is mechanistically grounded."

---

## 2026-02-24 [INFRA OBSERVATION] — Week 1 SAE Reconstruction Sanity Is Lower Than Expected

**Type:** action  
**Phase:** Week 1 / Infrastructure  
**Relevance:** Stage 2 decomposition reliability and interpretation validity

- `known`: During infrastructure validation, sampled encode→decode cosine values were low (`Llama layer16: 0.1278`, `Gemma layer12: 0.4526`) using straightforward residual-cache activations.
- `unknown`: Whether this is a real SAE quality issue vs a hook/preprocessing mismatch in the quick Week 1 sanity script.
- `inferred`: Stage 2 claims would be fragile if we treat these as true reconstruction metrics without re-validating with stage-appropriate hooks and expected activation normalization.

Action: before Week 3 interpretation, run the full reconstruction protocol with verified hooks and confirm >0.9 on controlled examples (or explicitly document why threshold differs for this setup).

## 2026-02-24 [FINDING] — Automated Prompt Audits Can Miss Obvious Label Contamination

**Type:** finding  
**Phase:** Week 1 / Infrastructure -> Week 2 transition  
**Relevance:** Stage 1 extraction validity depends directly on prompt-label cleanliness

- `known`: A strict regex-based audit reported pass, but manual random sampling still found an `evil` prompt asking for coercive tactics.
- `known`: After moving generation+audit to shared rule definitions and broadening coercive/instructional detection, regenerated prompts passed both automated audit and manual spot checks.
- `inferred`: For Stage 1 data quality, deterministic checks alone are insufficient; manual sampling remains necessary to catch natural-language edge cases.

## 2026-02-24 [METHODOLOGY RISK] — Mutable Prompt Files Can Break Run Traceability Mid-Execution

**Type:** action  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Evidence status for layer/alpha selection depends on reproducible run inputs

- `known`: A Week 2 behavioral validation run was active while held-out prompt files were regenerated to restore full audit coverage.
- `known`: The in-flight run had already loaded an earlier in-memory prompt set, so continuing would produce results that no longer mapped 1:1 to on-disk artifacts.
- `inferred`: Any long run that consumes mutable local prompt files is vulnerable to silent input drift unless the exact input set is frozen and hashed before launch.

Action: before each long validation run, produce a prompt manifest with hashes/counts and avoid prompt-file mutation until run completion; if mutation occurs, invalidate and rerun.

## 2026-02-25 [FINDING] — Completed Frozen Behavioral Run Still Fails Judge Reliability Gates

**Type:** action  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Final layer/alpha selection validity

- `known`: Run `8b3fp37q` completed with frozen prompts and traceable hashes; report artifact exists.
- `known`: Cross-rater kappa (Sonnet vs Opus bins) was below 0.6 for all traits (sycophancy 0.5607, evil 0.0, hallucination 0.4266).
- `known`: Hallucination exact-50 rate was 0.2743 (>0.2 fallback-risk threshold), indicating parse/format reliability risk.
- `inferred`: The selected layer/alpha combinations from this run are provisional; accepting them as validated would overstate confidence.

Action: run a judge calibration pass (manual concordance + prompt-template/parse tightening) and rerun behavioral validation before locking Week 2 optimal settings.

## 2026-02-25 [METHODOLOGY DESIGN] — Judge Reliability Failure Was Structural, Not Just Noise
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Final layer/alpha validity gate

- `known`: In the prior accepted-input run (`8b3fp37q`), hallucination raw judge outputs were often truncated narrative text with no parseable number, producing fallback-like behavior.
- `known`: Current Week 2 acceptance criteria depended on judge outputs for all steering metrics; parse fragility therefore directly contaminates selection.
- `inferred`: Judge parsing must be promoted from a soft diagnostic to a hard gate (explicit parse-fail rate threshold), or layer/alpha ranking can be an artifact of parser behavior.

Design response implemented:
- strict JSON-first judge prompt
- parse-failure accounting per model
- explicit gate (`parse_fail_rate <= 0.05`) before acceptance
- cross-rater calibration retained as separate reliability dimension (kappa + pairwise sign agreement)

## 2026-02-25 [METHODOLOGY DESIGN] — Split Sweep and Confirm Sets to Reduce Selection Bias
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Credible optimal layer/alpha claims

- `known`: Previous Week 2 script selected best layer/alpha on the same held-out pool used to report final effects.
- `inferred`: This creates optimistic selection bias even without prompt leakage.
- `known`: Upgraded runner now uses deterministic held-out split (`sweep` for ranking, `confirm` for final selection/effect reporting) and evaluates top-k sweep candidates on confirm.

Interpretation:
- `inferred`: This does not eliminate all bias, but materially improves evidence quality versus single-pool selection.

## 2026-02-25 [METHODOLOGY DESIGN] — Cross-Trait Bleed Is High-Signal at This Stage
**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Deciding whether to trust trait-specificity before Week 3 decomposition

- `known`: Local paper review (especially `bhandari2026_trait_interference.md`) emphasizes that target-trait steering can induce substantial off-target shifts, and geometric decorrelation alone does not guarantee behavioral independence.
- `inferred`: Cross-trait bleed matrix should be measured during Week 2 selection, not deferred to later phases, because a "good" target effect with high bleed changes interpretation of "optimal" settings.
- `known`: Upgraded runner now scores selected-combo outputs with all three rubrics and logs bleed matrix.

Action: before launching replication/stress tiers, inspect primary-tier bleed matrices and decide if alpha caps need tightening trait-by-trait.

## 2026-02-25 [METHODOLOGY DESIGN] — Full Parallel Matrix Is Informative but Budget-Heavy
**Type:** action
**Phase:** Week 2 / Upgrade execution planning
**Relevance:** Launch sequencing and risk control

- `known`: Generated plan artifact (`week2_upgrade_parallel_plan_20260225T113925Z.json`) includes 15 jobs (primary + replication + stress), with rough totals of ~47k primary judge calls and ~44k generations.
- `inferred`: Launching all tiers at once increases blast radius if one calibration assumption is wrong.
- `inferred`: Highest-signal rollout is stage-gated: launch primary tier first (3 jobs), review gates/bleed/capability, then conditionally launch replication and stress tiers.

Action: choose tranche policy before first upgraded launch (`primary-only` recommended as first tranche).

## 2026-02-25 [LITERATURE SECOND PASS] — Week 2 Reliability Gates Needed Tightening
**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Prevent false-positive layer/alpha selection before Week 3 decomposition

- `known`: Chen-style work uses behavioral layer sweeps and explicitly tracks coherence/capability tradeoffs as coefficients rise; large coefficients can degrade general quality.
- `known`: Chen and Rimsky both treat LLM-judge reliability as non-trivial and include manual/pairwise validation with documented edge cases.
- `known`: Turner and Zou both use random/shuffled baselines as robustness checks for steering-specific effects.
- `known`: Bhandari shows off-target trait bleed persists even when geometric overlap is reduced.
- `inferred`: Our prior gates (kappa + parse diagnostics + single random control) were necessary but not sufficient for high-confidence Week 2 lock-in.

Implemented response (completed before launch):
- Added judge API throttle/backoff with retryable-error handling.
- Added calibration directionality gate on known high-vs-low contrasts.
- Added coherence gate for selected combos (minimum score + bounded drop from baseline).
- Strengthened controls from one random vector to a random-control distribution with p95 separation requirement (plus shuffled vector control retained).

Remaining unresolved risks:
- `unknown`: transfer of selected settings to external benchmark prompts (outside generated held-out set).
- `unknown`: sensitivity of extraction vector quality to token-position choice (prompt-last vs response-token averaging).
- `unknown`: post-upgrade manual concordance quality on newly generated outputs.

## 2026-02-25 [METHODOLOGY GAP] — Week 2 Gate Audit Found Proposal-Mismatch Risks

**Type:** action
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Prevent overstating vector validation before Week 3 decomposition

- known: Proposal §6.2.3 specifies hallucination should be checked on known-fact questions (TruthfulQA-style), but the current upgrade runner only uses a small MMLU proxy for capability.
- known: Prior upgrade quality gate only required primary-judge parse pass; secondary-judge parse failures could occur without blocking acceptance.
- known: Non-trait control test score and neutral specificity shift were computed but not used as hard acceptance gates.
- inferred: Without these gates, a run could pass even when judge reliability/control sanity is weak, raising false-positive risk for layer/alpha lock.

Action:
1. Keep strengthened gates now implemented (secondary parse pass + control/specificity thresholds + strict capability availability by default).
2. Add an explicit hallucination known-fact benchmark check before Week 2 closeout (prefer TruthfulQA-format eval).

## 2026-02-25 [METHODOLOGY UPDATE] — Rollout Stability and Oversteer Diagnostics Added to Week 2

**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation
**Relevance:** Strengthens evidence quality before layer/alpha lock-in

- known: Upgraded Week 2 runner now supports multi-rollout averaging with separate rollout controls (`sweep_rollouts_per_prompt`, `confirm_rollouts_per_prompt`, `baseline_rollouts_per_prompt`, `rollout_temperature`).
- known: Runner now logs `steering_norm_diagnostics` that compare injection magnitude (`|alpha|*||v||`) to pre-steering residual norms at the selected layer.
- inferred: This reduces variance-sensitive selection risk and gives an explicit warning channel for potential oversteering (injection magnitude approaching or exceeding residual scale).
- unknown: Empirical sensitivity of selected layer/alpha to rollout count and rollout temperature in this exact setup.

Follow-up: evaluate whether selected combos remain stable when increasing confirm rollouts (e.g., 3 -> 5) on primary-tier reruns.

## 2026-02-25 [METHODOLOGY/IMPLEMENTATION] — Gap 3/4 closure uncovered hidden generation compatibility risk
**Type:** action  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Ensures upgraded rollout/norm methodology is executable under current runtime stack

- `known`: Targeted gap closure added sweep multi-rollout defaults and expanded steering norm diagnostics (distributional ratios + exceedance rates).
- `known`: First remote smoke run failed with `AssertionError: top_k has to be greater than 0` from current `transformer_lens` when using `model.generate(..., top_k=0)`.
- `known`: Runner patched to `top_k=None` in both steered and unsteered generation paths.
- `inferred`: This failure mode could have blocked all upgraded Week 2 runs despite passing local spot checks, reinforcing that remote smoke checks are mandatory after generation-path edits.
- `unknown`: End-to-end smoke completion status for the rerun after `top_k=None` patch (currently active at time of logging).

Action: complete rerun smoke and confirm report includes `steering_norm_diagnostics.ratio_stats`/`max_ratio` before launching primary tranche.

## 2026-02-25 [IMPLEMENTATION FINDING] — `top_k=None` restored remote generation compatibility
**Type:** finding  
**Phase:** Week 2 / Stage 1 behavioral validation  
**Relevance:** Confirms upgraded runner is runnable before primary tranche launch

- `known`: Rerun smoke (`i1pg2y8c`) completed successfully after patching generation from `top_k=0` to `top_k=None`.
- `known`: Output artifact contains new norm diagnostics fields (`steering_norm_diagnostics.ratio_stats`, `ratio_fraction_gt_0_5`, `ratio_fraction_gt_1_0`, `max_ratio`).
- `inferred`: The gap-closure upgrades are now implementation-valid; remaining uncertainty is scientific robustness on full-size primary runs, not code path correctness.

## [2026-02-25T13:30:12Z] [FINDING] — Null-control norm mismatch can fake selectivity
**Type:** finding
**Phase:** Week 2 / Stage 1 behavioral validation upgrade
**Relevance:** Directly affects control-separation validity for final layer/alpha acceptance.

[known] The selected steering direction was used at native norm, while random/shuffled/random-text controls were unit-normalized. That asymmetry can inflate apparent superiority of selected vectors even when direction quality is similar. We patched controls to norm-match all null directions to the selected vector norm and surfaced both norms in the report.

## [2026-02-25T13:43:32Z] [OBSERVATION] — Smoke runtime should be intentionally decoupled from closeout-scale evaluation load
**Type:** observation
**Phase:** Week 2 / Stage 1 behavioral validation upgrade
**Relevance:** Affects implementation-validation cadence and risk of conflating infra latency with methodological validity.

[known] Implementation smoke accidentally inherited heavy defaults (`truthfulqa_samples=30`), creating long feedback loops that do not increase confidence in code-path correctness. [inferred] For fast iteration, smoke profiles should explicitly downshift high-cost evaluators while still traversing the same logic branches; full sample settings remain for primary/replication evidence runs.
