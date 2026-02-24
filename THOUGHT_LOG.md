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

## RESOLVED ACTIONS

*(none yet)*

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
