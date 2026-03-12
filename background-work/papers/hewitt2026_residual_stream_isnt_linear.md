# Hewitt (2026) — How the Residual Stream is (Not) Linear

- **Author:** John Hewitt
- **Date:** February 2026
- **Type:** Research note / blog essay
- **URL:** https://www.cs.columbia.edu/~johnhew/residual-stream-isnt-linear.html
- **Accessed:** 2026-03-05

## Core Claims (Paraphrased)

1. The residual stream is additive across sublayer writes, but this does **not** imply useful global linearity for downstream interventions.
2. After an additive intervention at layer `q`, later activations are transformed by nonlinear MLP/normalization/attention dynamics, so simple linear propagation assumptions are not justified.
3. Methods like steering vectors/logit lens/SAE-based interventions should be justified by empirical performance and controls, not by architectural linearity arguments alone.
4. Approximate additive controllability may still emerge in practice; this is an empirical question, not an architectural guarantee.

## Relevance to Persona-Circuits

- **known:** This note directly touches our active methodological tension around additive steering and extraction-position dependence.
- **inferred:** It supports our current policy shift to treat prompt-vs-response A/B mismatch as a documented limitation/property, rather than a fatal contradiction.
- **known:** It strengthens the requirement to frame Stage4 causal claims with empirical gates and baselines (resample/mean/zero + random same-size sets), not linearity rhetoric.
- **inferred:** It is especially relevant to wording in Stage2/Stage3 writeups; we should avoid saying "residual stream is linear" as a justification for decomposition validity.

## How to Use in This Project

- Cite in discussion/methodology caveats when explaining why additive steering is evaluated with behavioral/causal tests.
- Link to this note when documenting extraction-method sensitivity as computational-regime dependence.
- Keep claims scoped to "empirically stable under our protocol" rather than "architecturally guaranteed."

## Suggested Citation String

Hewitt, J. (2026). *How the Residual Stream is (Not) Linear*.  
https://www.cs.columbia.edu/~johnhew/residual-stream-isnt-linear.html
