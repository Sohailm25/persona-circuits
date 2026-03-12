# Week 2 Gap 3/4 Literature Addendum (Sampling Stability + Steering Norm Diagnostics)

Timestamp (UTC): 2026-02-25
Scope: Resolve Week 2 pre-closeout methodology gaps:
- Gap 3: single deterministic rollout per prompt in primary validation.
- Gap 4: missing steering magnitude diagnostics relative to residual norm.

## Sources reviewed (local primary literature)

1. `background-work/papers/chen2025_persona_vectors.md`
2. `background-work/papers/turner2024_activation_addition.md`
3. `background-work/papers/rimsky2024_contrastive_activation_addition.md`
4. `background-work/papers/lindsey2025_circuit_tracing.md`
5. `background-work/papers/wang2025_emergent_misalignment.md`

## Gap 3: Multi-rollout stability

### Evidence

- known: Chen reports generating "10 rollouts per configuration and evaluation question" and averaging trait scores (`chen2025_persona_vectors.md:570-571`).
- known: Wang uses sampling-based metrics with "1000 responses per question at temperature 1" and reports uncertainty with bootstrapped confidence intervals (`wang2025_emergent_misalignment.md:342`, `:183`).
- known: Lindsey reports intervention effects as sampled response distributions (e.g., 50 and 500 sampled completions depending on experiment) (`lindsey2025_circuit_tracing.md:247`, `:1013`).
- observed: Turner qualitative demonstrations are not single-sample only; they report multiple completions and seed checks (`turner2024_activation_addition.md:359`, `:373`).

### Implication

- inferred: Single deterministic rollouts are weaker evidence for behavioral claims than sampled averages with uncertainty summaries.
- inferred: At minimum, sweep/confirm/baseline should each support multi-rollout means under fixed sampling hyperparameters.

## Gap 4: Steering magnitude relative to residual norm

### Evidence

- known: Turner Appendix F defines relative steering magnitude as steering-vector norm divided by residual-stream norm and explicitly analyzes this as a steering sanity diagnostic (`turner2024_activation_addition.md:987-1003`).
- known: Turner notes effective coefficients can approach or exceed the underlying residual scale, motivating oversteer diagnostics (`turner2024_activation_addition.md:1015`).
- known: Rimsky notes residual-stream norms vary strongly over layers and can skew layer-optimality conclusions if magnitude effects are not tracked (`rimsky2024_contrastive_activation_addition.md:366-368`).

### Implication

- inferred: Logging only alpha and vector norm is insufficient; diagnostics should track injection/residual ratios and outlier behavior (not just means).
- inferred: Percentiles/max and threshold exceedance fractions are higher-signal oversteer diagnostics than mean-only ratios.

## Implementation decisions applied

- known: Week 2 upgraded runner now supports rollout averaging for sweep/confirm/baseline and defaults sweep rollouts to multi-sample (3) instead of deterministic single-sample.
- known: Week 2 upgraded runner now logs steering norm diagnostics with ratio distributions (mean/median/p90/p95/max/min), exceedance fractions (>0.5, >1.0), and max-ratio warnings.
- known: Planner defaults were aligned to sweep multi-rollout and regenerated for updated runtime/call estimates.

## Remaining limits

- unknown: How sensitive selected layer/alpha is to rollout count beyond 3 (planned stability check: 3 -> 5).
- unknown: Whether p95/max oversteer thresholds correlate with coherence/capability degradation in this exact setup.

