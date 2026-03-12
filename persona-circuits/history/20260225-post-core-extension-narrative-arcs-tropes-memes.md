# Post-Core Extension Blueprint: Narrative Arcs, Tropes, and Memes in Persona-Circuit Space

## Document Status
- Status: planned (not started)
- Created: 2026-02-25
- Scope: post-core extension to the preregistered persona-circuits study
- Decision anchor: this extension is deferred until core phases complete; no Week 2.5 execution

## Why This Exists
This extension asks a focused follow-up question:

Can we map narrative arcs, tropes, and meme cues onto the persona-circuit structure discovered in the core study, and test whether these narrative structures act as routing or amplification controls in latent space?

The core study establishes causal evidence for persona circuits. This extension then characterizes how culturally meaningful narrative constructs interact with those validated circuits.

## Placement in Timeline
This is intentionally a post-core extension.

Do not run it during Week 2. Do not run it during Stage 1 closeout.

Execute only after all core preregistered milestones are resolved:
1. Week 2 behavioral validation finalized for all three traits.
2. Stage 2 SAE decomposition complete and reconstruction checks passed.
3. Stage 3 attribution graphs validated with manual ablation spot-checks.
4. Stage 4 causal ablation results complete with random same-size baselines.
5. Stage 5 cross-persona analysis complete.
6. Gemma-2-2B validation complete (as currently scoped).
7. Core traceability matrix rows and disconfirmation outcomes are written and stable.

Rationale: narrative/trope/meme labels are high-variance abstractions. Running them before core causal grounding increases risk of mistaking prompt artifacts for mechanistic findings.

## Extension Goals
1. Determine whether narrative arc phase (setup/conflict/resolution) modulates activation of already validated persona circuits.
2. Determine whether trope prompts (e.g., antihero, trickster, martyr, reformer) map onto reusable feature bundles across traits.
3. Determine whether meme-like lexical/cultural triggers act as low-cost routing gates that alter persona expression.
4. Quantify whether these effects are additive, interfering, or orthogonal when composed.
5. Produce publication-quality evidence that is clearly marked as post-core characterization, not core preregistration evidence.

## Value to the Program
1. Improves explanatory depth: converts "persona circuits exist" into "persona circuits are dynamically routed by narrative structure."
2. Improves external interpretability: links mechanistic findings to constructs legible to broader alignment and social-AI audiences.
3. Provides stronger theory tests for PSM-style routing claims under structured semantic manipulations.
4. Generates a high-value extension section for the final write-up without contaminating preregistered claims.

## Non-Goals
1. This extension does not alter preregistered hypotheses H1-H5 or disconfirmation criteria.
2. This extension does not replace core causal validation.
3. This extension does not expand to new base models unless explicitly approved after core completion.
4. This extension does not claim universality across all narrative cultures or meme ecosystems.

## Core Questions and Post-Core Hypotheses

### Q1: Arc Dynamics
Do validated persona circuits show phase-specific activation shifts across narrative arcs?

- EXT-H1 (arc dynamics): circuit activation and edge-level attribution profiles differ by arc phase with consistent within-arc ordering across prompts.

### Q2: Trope Reuse
Are trope effects explained by recombination of existing persona feature bundles?

- EXT-H2 (trope reuse): trope-conditioned behavior is primarily mediated by overlapping subsets of validated persona features, not entirely new diffuse features.

### Q3: Meme Gating
Can short meme cues reroute persona behavior and circuit activity?

- EXT-H3 (meme gating): meme cue insertion significantly shifts circuit activation or steering outcomes relative to minimal-pair controls.

### Q4: Composition
How do arc + trope + meme manipulations combine?

- EXT-H4 (composition): combined manipulations show either additive or interpretable interference structure (not random instability).

## Integration With Existing Infrastructure

### Reuse Without Changes
1. Compute: Modal A100-80GB setup and volume caching.
2. Logging: W&B project/entity already in use.
3. Judge stack: existing Claude Sonnet 4.6 judge pipeline and hard parse gates.
4. Prompt-quality tooling: `scripts/prompt_quality_rules.py` and audit flow.
5. Validation harnesses: Week 2 upgrade framework (split logic, control distributions, calibration).
6. Results bookkeeping: `results/RESULTS_INDEX.md` with traceability references.
7. Governance docs: `CURRENT_STATE.md`, `SCRATCHPAD.md`, `DECISIONS.md`, `THOUGHT_LOG.md`.

### New Artifacts to Add (When Extension Starts)
1. `prompts/post_core_extension/arc_prompts.jsonl`
2. `prompts/post_core_extension/trope_prompts.jsonl`
3. `prompts/post_core_extension/meme_minimal_pairs.jsonl`
4. `scripts/post_core_extension_generate_prompts.py`
5. `scripts/post_core_extension_behavioral_eval.py`
6. `scripts/post_core_extension_mech_map.py`
7. `scripts/post_core_extension_causal_eval.py`
8. `results/post_core_extension/` (new folder with timestamped outputs)
9. `results/figures/post_core_extension_*` (final figures)

No existing files should be overwritten. Extension scripts should be new files.

## Implementation Plan

### Stage E0: Readiness Gate (mandatory)
Before any extension run:
1. Confirm core phase status is complete in `CURRENT_STATE.md`.
2. Confirm core results are indexed in `results/RESULTS_INDEX.md`.
3. Confirm active core Modal apps are not running (avoid cross-phase contamination).
4. Write a DECISION entry declaring extension start.
5. Write extension prereg appendix (small) with explicit success/failure criteria.

Output:
- `results/post_core_extension/extension_readiness_check_YYYYMMDDTHHMMSSZ.json`

### Stage E1: Prompt and Control Set Construction
Build three prompt families with strict controls:
1. Arc set: same task content, varied arc phase framing (setup/conflict/resolution).
2. Trope set: same task content, varied trope framing (balanced set, not only mainstream stereotypes).
3. Meme set: minimal pairs differing only by meme cue insertion/removal.

Controls:
1. Neutral non-narrative baseline prompts.
2. Lexical-shuffle controls preserving token count/style but removing semantic cue.
3. Off-target trait controls.

Quality gates:
1. Prompt contamination audit.
2. Manual review sample per family.
3. Exact and normalized overlap checks against existing train/held-out sets.

Outputs:
- Prompt files in `prompts/post_core_extension/`
- Audit report JSON in `results/post_core_extension/`

### Stage E2: Behavioral Characterization
Run behavioral scoring with existing hardened judge infrastructure.

Design:
1. Use lockbox split policy (sweep/confirm/test) mirroring upgraded Week 2 practices.
2. Use existing parse-fail gates and cross-rater checks.
3. Record coherence/capability proxies to detect degradation.
4. For meme minimal pairs, use paired statistical tests.

Key outputs:
1. Effect-size table (mean delta, Cohen's d, A12, bootstrap CI).
2. Reliability table (parse rates, kappa, fallback rates).
3. Trait-bleed matrix under extension prompts.

### Stage E3: Mechanistic Mapping
Map extension conditions onto validated circuits/features.

Design:
1. Reuse validated core circuit definitions as primary anchors.
2. Compute overlap metrics between extension-activated features and core persona feature sets.
3. Track layer-wise concentration shifts (Gini/entropy/top-p mass).
4. Use attribution as hypothesis generator, not final claim.

Key outputs:
1. Arc-phase activation trajectory plots across layers.
2. Trope-to-feature overlap heatmap.
3. Meme cue delta-attribution maps.

### Stage E4: Causal Extension Tests
Validate key extension effects causally.

Design:
1. Primary method: resample ablation.
2. Secondary checks: mean/zero ablation for sensitivity only.
3. Random same-size ablation baselines (>=100).
4. Positive control: top-attributed feature ablation should shift behavior.
5. Negative control: near-zero attribution feature ablation should not meaningfully shift behavior.

Key outputs:
1. Causal necessity/sufficiency deltas for extension-defined conditions.
2. Random-baseline significance comparisons.
3. Selectivity checks against non-target narrative conditions.

### Stage E5: Synthesis and Reporting
Produce extension report and figures while keeping core claims separated.

Deliverables:
1. `results/post_core_extension/post_core_extension_report_YYYYMMDD.md`
2. Figure bundle under `results/figures/`
3. Results index entries with explicit `extension` tag.
4. One paper section draft labeled "Post-Core Extension (Exploratory Characterization)."

## Success Criteria (Extension-Specific)
1. Reliability: judge parse/coherence gates pass on extension runs.
2. Behavioral signal: statistically non-trivial shifts for at least two extension conditions with controlled baselines.
3. Mechanistic alignment: measurable overlap with validated persona circuits above random baselines.
4. Causal specificity: circuit-targeted interventions outperform random same-size controls.
5. Replication: at least one replication seed per major extension finding.

## Failure Criteria (Extension-Specific)
1. Judge reliability failures persist despite hardened pipeline.
2. Extension effects vanish under minimal-pair or shuffled controls.
3. Mechanistic overlap does not exceed random baseline.
4. Causal effects are indistinguishable from random feature ablations.
5. Findings are highly seed-unstable without interpretable cause.

Failure is still informative; report it explicitly.

## Statistical and Method Constraints
1. Report both effect size and uncertainty (Cohen's d, A12, 95% bootstrap CI).
2. Use paired analyses for minimal-pair meme tests.
3. Maintain random baseline distributions, not single random comparisons.
4. Separate exploratory analyses from confirmatory extension tests.
5. Predefine thresholds before each Stage E run.

## Known Confounds and Mitigations
1. Demographic stereotype confound.
- Mitigation: separate demographic cues from narrative cues; include demographic-only controls.

2. Prompt lexical leakage.
- Mitigation: minimal-pair controls, lexical shuffles, and overlap audits.

3. Attribution over-interpretation.
- Mitigation: require causal intervention checks before mechanistic claims.

4. Oversteering/coherence collapse.
- Mitigation: keep alpha sweeps, coherence gates, and norm diagnostics.

5. Culture-specific trope bias.
- Mitigation: diversify trope set and report distribution limits explicitly.

## Traceability Extension Rows (Proposed)
Add these as extension rows (separate from core H1-H5 rows):
1. EXT-1 Arc-phase routing evidence.
- Claim: persona-circuit activity is phase-sensitive to narrative arc.
- Evidence: phase-conditioned activation trajectory + causal spot checks.

2. EXT-2 Trope motif reuse.
- Claim: trope effects are mediated via reuse/recombination of persona feature bundles.
- Evidence: overlap metrics + controlled ablations.

3. EXT-3 Meme gating.
- Claim: meme cues can gate persona-circuit activation.
- Evidence: minimal-pair behavioral shift + circuit delta + random baseline separation.

4. EXT-4 Composition/interference.
- Claim: arc/trope/meme manipulations combine with structured interaction effects.
- Evidence: factorial tests + interaction effect estimates.

## Operational Workflow (When Executing)
1. Add PRE-RUN and POST-RUN entries in `SCRATCHPAD.md` for every Modal launch.
2. Log pivots in `DECISIONS.md` before code or run changes.
3. Register every artifact in `results/RESULTS_INDEX.md`.
4. Keep `CURRENT_STATE.md` updated at sub-task granularity.
5. Add non-routine insights to `THOUGHT_LOG.md`.

## Proposed Milestone Sequence
1. Milestone EXT-A: Prompt families generated and audited.
2. Milestone EXT-B: Behavioral signal and reliability confirmed.
3. Milestone EXT-C: Mechanistic mapping complete.
4. Milestone EXT-D: Causal extension tests complete.
5. Milestone EXT-E: Final extension report and figure pack complete.

## Resourcing Notes
1. Extension should be run in controlled tranches (no all-at-once launch).
2. Start with one trait as calibration tranche before full extension matrix.
3. Reuse existing runtime images where possible; add new images only if unavoidable.
4. Treat judge-call budget as a hard planning input and estimate before each tranche.

## Minimal Start Checklist (for future execution)
- [ ] Core phases complete and logged.
- [ ] Core claims frozen (no pending reruns affecting core conclusions).
- [ ] Extension start decision logged in `DECISIONS.md`.
- [ ] Extension prompt/audit scripts added.
- [ ] Extension prereg appendix written.
- [ ] First calibration run completed and reviewed.

## Final Note
This extension is designed to maximize additional signal without jeopardizing the causal clarity of the core preregistered study. It should be executed only after core evidence is stable.
