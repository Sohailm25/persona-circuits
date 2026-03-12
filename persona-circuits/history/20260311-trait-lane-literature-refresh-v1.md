# Trait-Lane Literature Refresh — 2026-03-11

## Status
- Status: active planning note
- Purpose: refresh the trait-selection landscape before any new lane-expansion work
- Scope: only literature relevant to adding new Stage-1/Week-2 screening lanes without disturbing the current core line

## Why This Exists
The current core trait set (`sycophancy`, `evil -> machiavellian_disposition`, `hallucination`) was selected to align with the original Persona Vectors paper and the proposal. Since Week 2/Stage 4 evidence now suggests trait choice may be part of the bottleneck, this note records what the local paper library and a March 11, 2026 web refresh imply about better or complementary lane choices.

## Current Ground Truth From This Project
- `known`: `sycophancy` remains the cleanest current trait lane in the project and is still defensible as a core claim trait.
- `known`: `evil` in its original harmful-content framing was a poor fit on an instruct model because refusal and harmful-content suppression confounded the construct; the reframed `machiavellian_disposition` lane is much better aligned.
- `known`: `hallucination` is currently a negative finding under the present protocol and should not be treated as equally persona-like to the other active lanes.
- `inferred`: part of the current difficulty may come from mixing social-behavior traits with epistemic/calibration traits under one shared “persona” umbrella.

## Local-Library Findings

### 1. Sycophancy is still one of the strongest paper-backed persona-like lanes
- `known`: CAA literature explicitly studies sycophancy and reports meaningful steering effects.
  - Source: `background-work/persona-vectors/anthropic.md:15`
  - Source: `background-work/papers/rimsky2024_contrastive_activation_addition.md:110`
- `known`: newer local summaries cite mechanistic sycophancy work and neuron-level correction work.
  - Source: `background-work/persona-vectors/anthropic.md:45`
  - Source: `background-work/persona-vectors/anthropic.md:47`
- `inferred`: replacing sycophancy would be low-value. It is better used as a stable anchor when evaluating new lanes.

### 2. Hallucination is weakly aligned to the persona-circuit question
- `known`: the local literature and current project results both support the idea that hallucination blends epistemics, calibration, refusal, and knowledge gating rather than a single stable persona-like direction.
  - Source: `background-work/papers/lindsey2025_circuit_tracing.md:616`
  - Source: `background-work/persona-vectors/anthropic.md:163`
- `inferred`: if one current lane is the wrong target class for the core paper, hallucination is the strongest candidate.

### 3. Honesty / lying / deception is a much stronger literature cluster than generic hallucination
- `known`: RepE explicitly develops honesty extraction, monitoring, and control.
  - Source: `background-work/papers/zou2023_representation_engineering.md:401`
- `known`: the local landscape summaries identify strong post-2024 work on lying, deception, and strategic deception monitoring.
  - Source: `background-work/persona-vectors/chatgpt.md:126`
  - Source: `background-work/persona-vectors/chatgpt.md:136`
  - Source: `background-work/persona-vectors/anthropic.md:39`
  - Source: `background-work/persona-vectors/anthropic.md:41`
- `inferred`: if the project wants one more high-importance lane, deception-family lanes are stronger candidates than hallucination.
- `caveat`: deception is not purely “persona”; it sits partly in strategy/intention space.

### 4. Assistant-likeness is now a serious candidate for the project’s theory target
- `known`: the local summaries describe a broad “Assistant Axis” / persona-space direction over many archetypes.
  - Source: `background-work/persona-vectors/chatgpt.md:45`
- `inferred`: this is conceptually closer to the Persona Selection Model than hallucination or refusal are, because it addresses persona-space structure directly rather than one narrow behavioral symptom.
- `caveat`: it is broad and may be harder to benchmark with the same Week 2 harness without careful construct cards.

### 5. Big Five-style lanes are paper-backed but risky as immediate replacements
- `known`: multiple papers extract Big Five / Dark Triad style traits.
  - Source: `background-work/persona-vectors/anthropic.md:55`
  - Source: `background-work/persona-vectors/chatgpt.md:230`
- `known`: the same local summaries warn that Big Five steering is context-sensitive and trait interference persists even after geometric cleanup.
  - Source: `background-work/persona-vectors/anthropic.md:127`
  - Source: `background-work/persona-vectors/chatgpt.md:242`
- `inferred`: if Big Five is explored, it should be screened in a narrow slice first (`agreeableness`) rather than adopted wholesale.

### 6. Refusal / harmlessness is mechanistically strong but not obviously a persona lane
- `known`: refusal has unusually strong mechanistic literature support and direct necessity/sufficiency-style validation.
  - Source: `background-work/persona-vectors/chatgpt.md:97`
- `known`: recent safety-monitoring summaries distinguish harmfulness judgment from outward refusal expression.
  - Source: `background-work/persona-vectors/chatgpt.md:318`
- `inferred`: refusal is valuable as a comparison lane and possibly as a tractable mechanistic control, but it is less cleanly aligned with the project’s “persona” framing than sycophancy or assistant-likeness.

### 7. Lighter style/persona lanes are explicitly in the persona-vector family
- `known`: the Chen persona-vector summary lists `politeness`, `apathy`, `humor`, and `optimism` beyond the three primary traits.
  - Source: `background-work/persona-vectors/chatgpt.md:31`
- `inferred`: these may be the best tractability lanes if the goal is to find cleaner behavior-to-vector-to-feature pathways with lower safety confounding.
- `caveat`: these are likely less important than deception-family or assistant-axis findings unless they produce markedly cleaner circuit evidence.

## March 11, 2026 Web Refresh

### Verified additions relevant to lane expansion
1. **Assistant Axis**
- `known`: live public research page confirms an active assistant-axis line.
- URL: `https://www.anthropic.com/research/assistant-axis`
- Related arXiv ID already cited in local docs: `2601.10387`
- Why it matters: strongest direct support for adding an `assistant-likeness` lane.

2. **Sycophancy Hides Linearly in the Attention Heads**
- `known`: arXiv page exists and confirms head-level sycophancy localization.
- URL: `https://arxiv.org/abs/2601.16644`
- Why it matters: reinforces the decision to keep sycophancy as a benchmark/anchor lane.

3. **LieCraft: A Multi-Agent Framework for Evaluating Deceptive Capabilities in Language Models**
- `known`: arXiv page exists.
- URL: `https://arxiv.org/abs/2603.06874`
- Why it matters: gives the deception-family lane a stronger 2026 evaluation reference point if the project adds honesty/lying/deception screening.

## Updated Candidate Families

### A. Honesty / lying / deception
- Best use: high-importance replacement or addition to hallucination-family work
- Strengths: strong literature, clearer separation between intentional falsehood and mere uncertainty
- Main risk: partly strategy/cognition rather than pure persona

### B. Assistant-likeness / persona drift
- Best use: theory-aligned lane closest to PSM’s persona-space framing
- Strengths: direct persona-space relevance, newer research momentum
- Main risk: broad construct, benchmarking may require more custom framing

### C. Light style/persona family (`politeness`, `optimism`, `apathy`, `humor`)
- Best use: low-confound tractability family for Stage-1/Week-2 screening
- Strengths: explicitly named in persona-vector literature; likely easier to score and steer
- Main risk: lower headline importance unless they yield much cleaner mechanistic evidence

### D. Agreeableness (Big Five slice)
- Best use: broader parent-lane test around sycophancy-like behavior
- Strengths: paper-backed personality framing
- Main risk: interference/entanglement and open-ended context sensitivity

### E. Refusal / harmlessness
- Best use: mechanistic contrast lane and safety-behavior comparison class
- Strengths: strong causal literature
- Main risk: not obviously a persona lane; construct can drift toward policy enforcement rather than character

## Practical Conclusion
- `inferred`: the most likely trait-level improvement is **not** replacing sycophancy.
- `inferred`: the most likely high-value change is to treat `hallucination` as the weak lane and add one or more of:
  - `honesty / lying / deception`
  - `assistant-likeness`
  - light style/persona lanes
- `inferred`: trait choice may be a meaningful bottleneck, but it is not the only bottleneck. Even better lanes will still face response-phase dependence, imperfect SAE reconstruction, and potentially distributed mechanisms.

## Recommended Operational Use
This refresh supports a breadth-first Stage-1/Week-2 screening branch that:
1. keeps the existing core line intact,
2. explores the five candidate families cheaply,
3. promotes only the best two or three lanes to heavier validation.
