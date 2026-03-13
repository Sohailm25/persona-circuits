# Collaborator Memo

This is the fastest way to understand what this project is, what has already been done, and what kind of feedback would actually be useful.

Repo:

- `https://github.com/Sohailm25/persona-circuits`

Detailed memo:

- [`history/20260313-collaborator-outreach-memo-v1.md`](history/20260313-collaborator-outreach-memo-v1.md)

## Project in one paragraph

This is an open-weight mechanistic interpretability project focused on persona-style behavior in Llama-3.1-8B. The original goal was to test whether persona steering directions decompose into sparse features and causal pathways, following recent persona-vector and circuit-tracing work. The project now has two meaningful side branches:

- `trait_lanes_v2`: a breadth-first branch for new trait/persona lanes
- `GLP`: a sidecar branch testing Generative Latent Prior style activation repair

The main live result is that a `politeness` lane looked real, survived the obvious control checks, but still appears too entangled with broader `assistant_likeness` behavior to count as a clean standalone lane.

## Main open question

The strongest current question is:

> Is assistant-style behavior the more fundamental object here, with narrower traits like politeness sitting inside it rather than standing apart from it?

The main GLP-side question is:

> Does GLP-style repair fail here because the prior/objective is wrong, or because training is mostly on clean activations while evaluation is on edited activations?

## Best links to open

### If you care about assistant-style behavior / persona-space structure

1. Trait-lane branch review note  
   [`history/20260312-trait-lane-review-reconciliation-plan-v1.md`](history/20260312-trait-lane-review-reconciliation-plan-v1.md)

2. Assistant-distinctness summary artifact  
   [`results/stage1_extraction/trait_lanes_v2/week2_trait_lane_assistant_distinctness_packet_20260313T114447Z.json`](results/stage1_extraction/trait_lanes_v2/week2_trait_lane_assistant_distinctness_packet_20260313T114447Z.json)

3. Assistant-distinctness execution result  
   [`results/stage1_extraction/trait_lanes_v2/week2_trait_lane_assistant_distinctness_execution_20260313T124626Z.json`](results/stage1_extraction/trait_lanes_v2/week2_trait_lane_assistant_distinctness_execution_20260313T124626Z.json)

### If you care about GLP / activation repair

1. GLP remediation note  
   [`history/20260312-glp-post-review-remediation-plan.md`](history/20260312-glp-post-review-remediation-plan.md)

2. GLP validated closeout note  
   [`history/20260312-glp-validated-responseall-closeout.md`](history/20260312-glp-validated-responseall-closeout.md)

3. Latest matched `response_last` GLP analysis  
   [`results/glp_sidecar/week2_glp_sidecar_analysis_20260313T135951Z.json`](results/glp_sidecar/week2_glp_sidecar_analysis_20260313T135951Z.json)

## Current state in plain English

- The core pipeline is partially complete: extraction, decomposition, and early causal work are done; Gemma CLT validation is still pending.
- The bounded H3 sufficiency branch was closed as a negative feasibility signal.
- The `trait_lanes_v2` branch no longer looks like a generic screening problem. The surviving issue is assistant-style aliasing.
- The GLP branch is not scientifically closed. The strongest current read is “no selective repair under the current setup, with train/eval mismatch still unresolved.”

The full running state is tracked in:

- [`CURRENT_STATE.md`](CURRENT_STATE.md)

## What kind of feedback is useful

The most useful replies are one of:

1. “This looks like a real question; keep pushing it.”
2. “You are asking the wrong question; the sharper version is X.”
3. “The next experiment should be Y, not Z.”
4. “This overlaps heavily with paper / method X.”

For cold outreach, I am usually asking for:

- a quick gut check
- async feedback on framing
- or a short call

not a heavy commitment.
