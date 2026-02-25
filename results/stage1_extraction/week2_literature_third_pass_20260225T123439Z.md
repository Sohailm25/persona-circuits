# Week 2 Literature Third Pass (Critical, Method-Focused)

Timestamp: 2026-02-25 (local)
Scope: Week 2 extraction/behavioral validation methodology hardening before primary tranche launch.

## Primary source signals (with local-paper evidence pointers)

1. Coefficient/layer sweeps and coherence trade-off are mandatory, not optional.
- Chen persona vectors reports increasing trait suppression with larger coefficients but notes capability degradation at high coefficients (chen2025_persona_vectors.md:839-840).
- Rimsky CAA explicitly limits multiplier range when larger multipliers degrade open-ended quality (rimsky2024_contrastive_activation_addition.md:198).

2. Judge reliability needs explicit calibration and edge-case handling.
- Chen reports human-LLM pairwise agreement and explicitly documents judge edge cases for sycophancy/hallucination (chen2025_persona_vectors.md:2181-2203).
- Proposal Appendix C.2 requires cross-rater kappa >= 0.6 before proceeding.

3. External benchmark transfer is high-signal for avoiding prompt-set overfit.
- Chen validates correlation between internal eval set and external benchmark questions (chen2025_persona_vectors.md:2393-2411).

4. Random/shuffled controls are required for causal specificity.
- Turner includes same-norm random-vector controls and random text-vector controls (turner2024_activation_addition.md:1021-1031).
- Zou uses random/shuffled controls in memorization-control experiments (zou2023_representation_engineering.md:724-730).

5. Cross-trait interference should be measured directly at selection stage.
- Bhandari shows geometric decorrelation alone does not remove behavioral bleed; reports target-vs-bleed plus fluency checks (bhandari2026_trait_interference.md:129, 137, 147).

6. Prompt leakage must be actively prevented.
- Zou explicitly uses far-out-of-distribution stimuli to avoid leakage and overfitting to extraction conditions (zou2023_representation_engineering.md:455).

## Implementation audit outcome (current codebase)

Status: Partially addressed with recent upgrades.

Already implemented (known):
- Strict JSON judge parsing + parse-fail accounting.
- Rate limit + retry/backoff + jitter for judge API.
- Sweep/confirm split for layer-alpha selection.
- Multi-random + shuffled controls.
- Coherence gate + directionality calibration gate.
- Cross-trait bleed matrix.
- External transfer + extraction-method A/B prelaunch script (run in progress).

Still open / caution (unknown or inferred):
- Hallucination known-fact metric in Week 2 does not yet include a TruthfulQA-style explicit check (proposal §6.2.3 expectation).
- Manual concordance check on newly generated outputs still pending for final lock.
- Current evaluation uses deterministic single rollout per prompt; literature often averages multiple rollouts for stability (e.g., Chen: 10 rollouts per config, lines ~570).
- Injection-strength diagnostics relative to residual-stream norm are not yet logged (Turner-style magnitude sanity; potential oversteer risk).

## Decision impact for launch

Recommended pre-launch requirement set (in addition to current gates):
1. Complete external transfer + extraction-method A/B run and review quality gates.
2. Run manual 5-example concordance check for each trait on upgraded outputs.
3. Add/record hallucination known-fact benchmark check before Week 2 closeout claim.

