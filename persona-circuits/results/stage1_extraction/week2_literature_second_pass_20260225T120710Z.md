# Week 2 Literature Second Pass (Methodology Delta)

Date: 2026-02-25
Phase: Week 2 / Stage 1 behavioral validation hardening
Reviewer: codex-gpt5

## Scope and Method

Reviewed local references with direct text inspection and line-level extraction:
- `background-work/papers/chen2025_persona_vectors.md`
- `background-work/papers/rimsky2024_contrastive_activation_addition.md`
- `background-work/papers/turner2024_activation_addition.md`
- `background-work/papers/zou2023_representation_engineering.md`
- `background-work/papers/bhandari2026_trait_interference.md`
- `background-work/papers/wang2025_emergent_misalignment.md`
- `background-work/MECH_INTERP_GUIDANCE.md`
- `background-work/REFERENCES.md`

Evidence labeling used throughout:
- `known`: directly supported by inspected source text
- `inferred`: design implication derived from known evidence
- `unknown`: not yet directly tested in our pipeline

## High-Signal Findings

### 1) Steering coefficients are highly effective but quality-sensitive
- `known`: Chen reports trait suppression improves with stronger coefficients but larger values degrade capability (MMLU) and they track coherence explicitly (`chen2025_persona_vectors.md`:839-840, 832-848).
- `known`: Chen uses coherence guardrails and in one comparison selects the largest coefficient while keeping coherence >80 (`chen2025_persona_vectors.md`:5317-5319).
- `known`: Rimsky reports larger multipliers degrade open-ended quality and should be range-limited (`rimsky2024_contrastive_activation_addition.md`:196-204).
- `inferred`: Week 2 selection cannot rely on trait effect alone; coherence must be a hard gate.

### 2) Layer selection should be behavioral and held-out
- `known`: Chen selects informative layer by steering effectiveness across layers (`chen2025_persona_vectors.md`:369-372, 2538-2542).
- `known`: Rimsky sweeps all layers and evaluates effect on held-out questions (`rimsky2024_contrastive_activation_addition.md`:158-160).
- `inferred`: Our full layer sweep with sweep/confirm split is methodologically aligned; top-2-only sweep was underpowered.

### 3) Judge reliability requires stronger calibration than raw score parsing
- `known`: Chen validates LLM judge against human pairwise judgments and documents systematic edge cases (`chen2025_persona_vectors.md`:2183-2206).
- `known`: Rimsky notes LLM-rater prompt sensitivity and performs manual checks (`rimsky2024_contrastive_activation_addition.md`:356-364).
- `known`: Wang uses both alignment and coherence judges and reports failure cases (`wang2025_emergent_misalignment.md`:889-903).
- `inferred`: Cross-rater kappa alone is insufficient; directionality on known high/low pairs and parse robustness must be gated.

### 4) Random/shuffled controls should be distributional, not single-sample
- `known`: Turner reports random-vector interventions as an important robustness baseline and distinguishes targeted vectors from random perturbations (`turner2024_activation_addition.md`:965-973, 1017-1028).
- `known`: Zou explicitly compares against shuffled-vector controls in representation-control experiments (`zou2023_representation_engineering.md`:728-729).
- `inferred`: Single random vector control is weak evidence; selection should beat a random-control distribution (e.g., p95), not one draw.

### 5) Off-target trait bleed is expected and must be measured, not assumed away
- `known`: Bhandari shows persistent cross-trait behavioral bleed even under orthogonalization (`bhandari2026_trait_interference.md`:137-149, 153-159).
- `inferred`: Cross-trait bleed matrix is a Week 2 acceptance criterion, not a later-phase nicety.

### 6) Pre-registration discipline and coherence filtering materially improve evaluation trust
- `known`: Wang pre-registers held-out evaluation questions and uses coherence thresholds to exclude broken generations (`wang2025_emergent_misalignment.md`:872, 976-981).
- `inferred`: Our frozen held-out hashes and coherence gate should be mandatory before selecting final layer/alpha.

## Implemented Pipeline Upgrades (from this pass)

The following changes were applied to scripts before launch:

1. `scripts/week2_behavioral_validation_upgrade.py`
- Added judge-rate limiting + exponential backoff/jitter + retryability handling + Retry-After support (already added before this pass).
- Added judge **directionality calibration gate** on known high/low pairs:
  - Sonnet and Opus directionality rates must each exceed configurable threshold.
- Added **coherence gate** for selected combo:
  - score selected outputs with coherence rubric,
  - require steered coherence mean >= threshold,
  - require coherence drop from baseline <= threshold.
- Strengthened controls from single random vector to **distributional random baseline**:
  - evaluate multiple random vectors (`random_control_vectors`, default 8),
  - require selected effect > random p95 and > shuffled-vector control.

2. `scripts/week2_upgrade_parallel_plan.py`
- Added new command/planning parameters:
  - `--judge-directionality-threshold`
  - `--coherence-min-score`
  - `--coherence-max-drop`
  - `--random-control-vectors`
- Updated runtime/call estimates to include coherence judging and multi-random controls.
- Updated success criteria text to p95 random-control separation.

## Remaining Gaps (Not Yet Closed)

1. External benchmark transfer check in Week 2
- `known`: Chen validates generated eval prompts against external benchmarks (`chen2025_persona_vectors.md`:2399-2411).
- `unknown`: We have not yet run an external-trait benchmark transfer check for selected layer/alpha.

2. Extraction token-position robustness
- `known`: Chen extraction averages residual activations across response tokens (`chen2025_persona_vectors.md`:369).
- `known`: Current proposal/script uses last prompt-token extraction.
- `unknown`: Whether selected vectors are stable to response-token averaging in our setup.

3. Human concordance spot-check
- `known`: both Chen and Rimsky run manual checks for judge behavior.
- `unknown`: We have not yet run a fresh manual 5-example concordance in this upgraded pipeline.

## Pre-Launch Recommendation

Launch `primary` tranche only after confirming these run-level gates pass for each trait:
- judge kappa >= 0.6
- pairwise sign agreement >= 0.75
- judge directionality rates >= configured threshold (default 0.7)
- parse-fail rate <= threshold (default 0.05)
- selected bidirectional effect >= threshold (default 20)
- selected effect > random-control p95 and > shuffled control
- coherence mean >= 75 and coherence drop <= 10
- capability degradation <= 5% when capability proxy is available

If any gate fails, do not proceed to replication/stress tiers.
