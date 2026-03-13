# Collaborator Outreach Memo v1

## Why this exists

This memo is the quickest way to understand what this repo is, what has already been done, and what kind of feedback or collaboration would actually be useful.

This project is public here:

- `https://github.com/Sohailm25/persona-circuits`

The full repo is large. The intent of this memo is to let someone skim the project in a few minutes without having to reverse-engineer the directory structure.

---

## 30-second summary

I am running an open-weight mechanistic interpretability project on persona-style behavior in Llama-3.1-8B.

The original plan was to test whether persona steering directions decompose into sparse features and causal circuits, following recent persona-vector and circuit-tracing work.

The project has now produced two meaningful side branches:

1. `trait_lanes_v2`
   A breadth-first screening branch for new trait/persona lanes beyond the original sycophancy / machiavellian / hallucination set.

2. `GLP`
   A sidecar branch testing whether Generative Latent Prior style activation repair can selectively clean up persona steering effects.

The main current result is:

- a `politeness` lane looked real at first and survived the obvious control checks,
- but it still fails as a clean standalone lane because it appears too entangled with broader `assistant_likeness` / assistant-style behavior.

So the most interesting live question is no longer "can we find another trait?" It is:

> Is assistant-style behavior the more fundamental object here, with narrower traits like politeness sitting inside it rather than standing apart from it?

---

## What the project is trying to do

At a high level, the project asks:

1. Can we extract interpretable steering directions for persona-like behavior?
2. Do those directions decompose into sparse features rather than diffuse noise?
3. Are those features part of real causal pathways, rather than just correlates?
4. When a candidate trait fails, is it failing because the signal is fake, or because it is not distinct from a broader assistant/persona computation?

The project began as a direct follow-up to persona vectors and the broader Persona Selection Model / circuit-tracing agenda, but it is deliberately grounded in open-weight models and public infrastructure.

---

## Current state in plain English

### Mainline

The core pipeline is still active, but not fully complete:

- infrastructure, vector extraction, and decomposition are done
- early attribution and causal-validation work is done
- the bounded H3 sufficiency branch was closed as a negative feasibility signal
- Gemma CLT validation has not yet been run

The canonical state tracker is:

- `CURRENT_STATE.md`
- GitHub: `https://github.com/Sohailm25/persona-circuits/blob/main/CURRENT_STATE.md`

For outreach, that file is usually too large to be the best starting point.

### Trait-lane branch

The most useful branch result so far is the `politeness` case:

- it passed a matched null-control screen
- it passed a bounded prompt-sensitivity check
- it remained behaviorally strong in deeper validation
- but it failed distinctness because the off-target effect on `assistant_likeness` was slightly larger than the target effect itself

The branch-level implication is:

- this is probably not "just noise"
- it is also probably not a clean independent persona lane under the current evidence
- the live scientific question is now assistant-style aliasing / assistant-axis structure

### GLP branch

The GLP sidecar has moved from "pipeline smoke test" to a more informative negative result:

- matching the model and layer removed the gross mismatch story
- a stronger trained unconditional checkpoint still did not show convincing selective repair
- the main unresolved confound is now the train/eval mismatch:
  - training is mostly on clean activations
  - evaluation is on edited activations

So the right next GLP question is not "does GLP work at all?" but:

> Does repair fail because the prior is fundamentally wrong for this problem, or because the training distribution is too far from the edited activations used at evaluation time?

---

## The most useful entry points

If you only read three links, these are the best ones.

### For the assistant-style / persona-space question

1. Trait-lane branch review note
- `https://github.com/Sohailm25/persona-circuits/blob/main/history/20260312-trait-lane-review-reconciliation-plan-v1.md`

2. Current assistant-distinctness summary artifact
- `https://github.com/Sohailm25/persona-circuits/blob/main/results/stage1_extraction/trait_lanes_v2/week2_trait_lane_assistant_distinctness_packet_20260313T114447Z.json`

3. Trait-lane config / registry
- `https://github.com/Sohailm25/persona-circuits/blob/main/configs/trait_lanes_v2.yaml`

### For the GLP / activation-repair question

1. GLP remediation plan
- `https://github.com/Sohailm25/persona-circuits/blob/main/history/20260312-glp-post-review-remediation-plan.md`

2. GLP validated closeout note
- `https://github.com/Sohailm25/persona-circuits/blob/main/history/20260312-glp-validated-responseall-closeout.md`

3. Latest matched `response_last` sidecar analysis
- `https://github.com/Sohailm25/persona-circuits/blob/main/results/glp_sidecar/week2_glp_sidecar_analysis_20260313T135951Z.json`

---

## A few concrete results

### Assistant-style aliasing result

From the current `politeness` distinctness packet:

- selected `politeness` effect: `46.33`
- off-target `assistant_likeness` effect: `47.23`
- off-target `sycophancy` effect: `14.67`
- matched null-control result: hold / not promoted
- prompt-sensitivity result: retained

Interpretation:

- the lane is not obviously fake
- the stronger remaining explanation is that it is part of broader assistant-style behavior rather than an independent trait

### GLP sidecar result

From the latest matched `response_last` analysis:

- `evil`: raw `-60.25`, GLP `-54.15`, coherence worsens
- `sycophancy`: raw `-72.15`, GLP `-71.0`, coherence slightly worsens
- random and baseline GLP controls remain too competitive
- metric-validity correlations remain weak

Interpretation:

- this is stronger than an "undertrained checkpoint" story
- it is still not enough to conclude the whole GLP direction is exhausted
- the main remaining scientific confound is train/eval mismatch

---

## How the repo is organized

The minimum useful map is:

### Human-readable documents

- `history/`
  Short memos, review notes, closeouts, and planning docs

### Canonical status

- `CURRENT_STATE.md`
  The full running state of the experiment

### Trait-lane branch

- `configs/trait_lanes_v2.yaml`
- `results/stage1_extraction/trait_lanes_v2/`

### GLP branch

- `configs/glp_sidecar.yaml`
- `results/glp_sidecar/`

### Code

- `scripts/`
- `tests/`

For a first pass, the `history/` notes are much easier to read than jumping straight into the Python.

---

## What I am asking for

I am usually reaching out for one of these, not for a fully formed commitment:

1. A quick gut check on whether the direction is scientifically real
2. A short call or async feedback on the current branch framing
3. A pointer to a paper, method, or failure mode I may be missing
4. If there is strong fit: an informal collaboration or mentorship-style exchange on a narrow next step

The most useful kinds of feedback are:

- "this question is sharper than you think, keep pushing it"
- "this is already basically explained by X, so reframe it"
- "the right next experiment is Y, not Z"

---

## The main open questions

### Q1. Assistant-style structure

If `politeness` survives controls but still collapses into `assistant_likeness`, is the correct next object:

- an assistant-axis / assistant-style circuit,
- a trait hierarchy inside assistant behavior,
- or just a sign that these lanes are too entangled to be worth treating independently?

### Q2. Activation repair under distribution shift

If matched GLP still does not selectively repair steering, is the main reason:

- the prior/objective is wrong,
- the corruption model is wrong,
- or the train/eval activation distributions are too mismatched?

### Q3. Disposition vs expression

Can a persona-like or honesty/deception direction still be detected when behavior is intentionally similar on the surface?

That is, can we separate:

- internal disposition
from
- outward expression

without relying only on behavioral divergence?

---

## If you want the shortest possible read

Read these in order:

1. this memo
2. the trait-lane review note or the GLP remediation note
3. one branch artifact JSON

That should be enough context for a useful reply.
