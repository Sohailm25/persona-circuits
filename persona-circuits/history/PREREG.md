# Persona Circuits Local Pre-Registration

## Title
Tracing Persona Circuits: A Pre-Registered Mechanistic Test of the Persona Selection Model

## Summary
This project tests whether persona steering effects in open-weight LLMs are mediated by sparse, identifiable circuits rather than diffuse activation shifts. We will run the full pipeline on Llama-3.1-8B-Instruct (primary) and Gemma-2-2B-IT (CLT validation): persona vector extraction, SAE decomposition, attribution/circuit discovery, and causal ablation.

## Core hypotheses
1. Coherence: persona vectors decompose into concentrated feature sets.
2. Necessity: ablating the discovered circuit strongly suppresses steering effects.
3. Sufficiency: circuit-only interventions preserve a substantial fraction of steering effects.
4. Cross-persona structure: circuits show shared early-layer routing and diverging late-layer enactment.
5. Router mechanism: a routing subset exists whose ablation blocks persona propagation while preserving general competence.

## Pre-registered disconfirmation criteria
1. H1 disconfirmed if no circuit of <20% components achieves >50% necessity across at least 2 of 3 traits.
2. H2 disconfirmed if circuit ablation reduces steering effect by <30% on average, or random same-size ablation is comparable (p > 0.05).
3. H3 disconfirmed if circuit-only runs preserve <40% steering effect across at least 2 traits.
4. H4 disconfirmed if no layer-wise Jaccard gradient appears (not consistently higher early than late across at least 2 trait pairs).
5. H5 disconfirmed if no feature/head set can block persona propagation while preserving >90% general competence.
6. PSM exhaustiveness challenged if coherent goal-directed trait behavior persists after ablating all identified persona-relevant features.

## Measurement and reporting standards
- Report both resample and mean ablation.
- Report effect sizes (Cohen's d and A12) with 95% bootstrap CIs.
- Compare circuits against >=100 random same-size baselines.
- Report concentration metrics (Gini, entropy, top-p mass).
- Log all runs/artifacts in W&B (`sohailm/persona-circuits`).

## Scope
In scope: sycophancy, evil/toxicity, hallucination traits; mechanistic tracing and causal validation.
Out of scope (Phase 1): frontier closed-weight models, adversarial robustness benchmarking, large-scale CLT graph extraction on 8B+.

## Reproducibility
- Fixed seeds, pinned dependencies, and config/version logging.
- Code and small result artifacts tracked in the dedicated `persona-circuits` repo.
- Prompt generation and evaluation scripts will be deterministic where possible and fully logged.

## Status
Local pre-registration finalized on February 24, 2026. This file replaces external LW/AF prereg publication for this experiment.
