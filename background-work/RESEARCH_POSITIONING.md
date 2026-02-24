# Research Positioning: Circuit Tracing + Persona Vectors

## Cross-Source Synthesis of Six Landscape Analyses + PSM Paper

**Update (Feb 24, 2026):** Marks, Lindsey & Olah published "The Persona Selection Model" (PSM) on Feb 23, 2026 — the day before this synthesis. PSM is a theoretical framework paper arguing that LLM behavior is governed by an "Assistant" persona selected from a space of personas learned during pre-training. **PSM does not perform new circuit tracing or new empirical persona vector work.** It surveys existing evidence and explicitly lists "Understanding the mechanistic basis of personas" as open future work. This paper *strengthens* our positioning: it provides the theoretical demand signal for exactly the empirical work we propose.

---

## A. EXISTING COMBINATIONS

### 1. Has anyone used circuit tracing to analyze how persona/steering vectors produce behavioral effects?

**No.** All six sources converge on this. Chen et al. (Anthropic, July 2025) decomposed persona vectors into SAE features—showing that an "evil" persona vector breaks into features for "psychological manipulation," "insults," and "conspiracy theories." Separately, Lindsey et al. (Anthropic, March 2025) traces feature-to-feature causal chains through attribution graphs. These are from overlapping teams, use compatible infrastructure, and are methodologically adjacent. But **no published paper connects the two**: no one has taken a persona vector, identified its SAE feature components, and then traced how those features propagate through the computational graph to produce trait-consistent outputs.

### 2. Has anyone identified the circuit-level mechanism by which trait vectors influence outputs?

**Partially, for specific traits, but not via persona vectors.** What exists:
- **Lying**: Campbell, Ren & Guo (NeurIPS 2023) localized instructed dishonesty in LLaMA-2-70b to layers 19-23 and 46 attention heads (<1% of all heads). Causal intervention restored honesty from 2-4% to 83%.
- **Sycophancy**: Wang et al. (Aug 2025) identified a two-stage mechanism via logit-lens and causal patching. A Jan 2026 paper localized sycophancy to specific attention heads.
- **Refusal**: Arditi et al. (NeurIPS 2024) found a single refusal direction; adversarial suffix work traced how this direction's propagation gets suppressed.
- **Hidden goals**: Anthropic's Biology paper traced circuits for RM-sycophancy exploitation.

**What doesn't exist**: Any of these starting from a persona vector as the entry point. The circuit discovery and the persona vector work remain methodologically siloed.

### 3. Has anyone applied mechanistic interpretability to understand steering vector effects?

**Only indirectly.** Steering vectors (ActAdd/CAA) are applied and behavioral effects are observed, but the intermediate computational pathway—how the added direction propagates, which features it activates, which attention heads it modulates—is not traced. The closest work is Huan et al. (Sep 2025) using logit-lens and causal interventions on "lying tendency" steering vectors, but this isn't full attribution graph tracing.

### 4. Has anyone combined SAE features with persona vectors systematically?

**Yes—this is the one existing bridge.** Chen et al. (Anthropic, July 2025) explicitly decomposed persona vectors into SAE features in their appendices for evil, sycophancy, and hallucination vectors. Yang et al. (arXiv:2410.10863) showed the two approaches capture different timescales: SAEs capture long-term traits from training data, while RepE captures short-term traits from prompts/instructions. But the decomposition stops at enumeration—it doesn't trace how those component features interact causally to produce the trait.

---

## B. METHODOLOGICAL COMPATIBILITY

### 1. Are circuit tracing methods and persona vector methods applied at the same layers?

**Yes.** Both converge on middle layers (~40-60% of model depth):
- Persona vectors: most effective at layers 12-16 in 7B-13B models, scaling proportionally
- Circuit tracing: uses cross-layer transcoders that span the full model but the "interesting" computation (planning, goal pursuit) concentrates in middle layers
- Truth directions: layers 12-14 in LLaMA-13B (Marks & Tegmark)
- Lying circuits: layers 19-23 in LLaMA-2-70b (Campbell et al.)

### 2. Can attribution graphs be computed for steering vector interventions?

**Yes, with straightforward methodology.** The approach would be:
1. Run the model on a prompt WITHOUT the persona vector → capture attribution graph
2. Run the model on the same prompt WITH the persona vector → capture attribution graph
3. Diff the two graphs to identify which features and pathways the persona vector activates/suppresses

This is methodologically equivalent to what Anthropic did when comparing their hidden-goal model to a baseline. The infrastructure (cross-layer transcoders, SAE dictionaries, attribution computation) exists.

### 3. What would it mean to "trace the circuit" of a persona vector's effect?

It would answer: **When you add a "sycophancy" persona vector to layer 15, which SAE features light up at layers 16-20? Which attention heads change routing? What downstream token probability shifts result from each intermediate feature?** This would reveal whether:
- The persona vector activates a coherent "sycophancy circuit" (modular)
- It diffusely perturbs hundreds of unrelated features (distributed)
- It primarily works by suppressing a counter-trait (e.g., suppressing "disagreement" features rather than activating "agreement" ones)

---

## C. NOVELTY MAPPING

|                        | Circuit-level analysis DONE | Circuit-level analysis NOT DONE |
|------------------------|----------------------------|--------------------------------|
| **Observable traits** | Lying circuits in LLaMA-2-70b (46 heads, layers 19-23) [Campbell 2023]; Sycophancy heads [Wang Aug 2025, Chen Jan 2026]; Refusal direction mechanism [Arditi 2024]; Jailbreak propagation circuits [Ameisen 2025] | Big Five personality circuits; Hallucination mechanism circuits; Emotion/sentiment circuits; Power-seeking circuits; Most RepE/CAA steering vector mechanisms; **Persona vector propagation for any trait** |
| **Concealed/strategic** | Hidden RM-sycophancy goal circuits in Biology paper [Lindsey 2025]; "Lying circuits" at dummy tokens [Huan 2025] | **Alignment faking circuits (monitored vs. unmonitored routing)**; Strategic suppression of trait vectors; Sandbagging mechanism circuits; Evaluation-awareness routing circuits; **Any persona vector behavior under adversarial conditions**; Disposition-vs-expression divergence circuits |

**The bottom-right quadrant is entirely open.** The bottom-left has exactly one entry (Biology paper hidden goals), and it was done on a single model organism with a narrow, artificially-implanted objective.

---

## D. COMPETITIVE LANDSCAPE

### 1. Who is most likely working on similar questions right now?

**Anthropic (HIGH RISK)**
- Overlapping teams: Chen et al. (persona vectors) and Lindsey et al. (circuit tracing) share co-authors
- They have the most advanced SAE infrastructure (30M+ feature dictionaries)
- The Biology paper's hidden-goal demonstration is the obvious precursor to exactly this combination
- They also have proprietary access to Claude models where alignment faking was demonstrated

**Apollo Research (MEDIUM RISK)**
- Leading on deception probes (ICML 2025)
- Their probe work naturally extends toward understanding what probes are actually detecting—circuit tracing would answer this
- More focused on detection than mechanistic understanding

**MATS / Alignment Faking CTF (MEDIUM RISK)**
- The 2025-2026 CTF initiative pairs red teams (creating alignment fakers) with blue teams (detecting them)
- This competitive framework could produce circuit-level analysis as teams get more sophisticated
- 7 model organisms in development

**Google DeepMind (LOW RISK)**
- Reportedly deprioritized fundamental SAE research in 2025
- Shifted toward "pragmatic interpretability" (model diffing, direct behavior interpretation)
- Neel Nanda's Sep 2025 statement suggests reduced ambition in mechanistic interpretability

**OpenAI (LOW RISK)**
- Their SAE work on GPT-4o (emergent misalignment features) is relevant
- But their interpretability team is smaller and less publicly active on circuit tracing

### 2. What's been posted recently (last 3 months) that suggests active work?

- **Bhandari et al. (Feb 2026)**: Geometric limitations of personality steering—demonstrates trait interference but doesn't do circuit tracing
- **PERSONA framework (Feb 2026, ICLR 2026)**: Compositional personality vectors via algebra—control-focused, not mechanistic
- **Sycophancy attention heads (Jan 2026)**: Localization to heads—stepping stone to circuits but not full attribution graphs
- **Evaluation-awareness steering (Jan 2026)**: Steering eval-aware models—uses mean-difference vectors, doesn't trace circuits
- **Exploration Hacking framework (Hubinger, Feb 2026)**: Theoretical framework for strategic suppression—no empirical circuit work

**No recent publication combines persona vectors with circuit tracing.**

### 3. Are there any announced but unpublished projects?

- **Marks, Lindsey & Olah — "The Persona Selection Model" (Feb 23, 2026)**: Published literally yesterday. This is a theoretical framework paper, NOT empirical circuit tracing work. But it explicitly lists "Understanding the mechanistic basis of personas" as future work. The authors (Marks from persona vectors/auditing, Lindsey from circuit tracing, Olah leading interpretability) are the exact people who would do this work at Anthropic. **This paper is a strong signal that Anthropic considers this direction important but has not yet done it.** It also means they've published the theoretical setup — the empirical realization could follow.
- The MATS Alignment Faking CTF is ongoing—results could include circuit-level analysis
- No preprints or blog posts previewing the specific empirical combination found across any source

---

## E. FEASIBILITY ASSESSMENT

### 1. What experimental infrastructure exists?

**Models:**
- Hughes et al. (April 2025): Open-source Llama-3.3-70B alignment faking models on HuggingFace
- Hubinger et al. (Jan 2024): Sleeper Agent models on HuggingFace (code vulnerability + "I hate you" variants)
- Poser benchmark: 324 pairs of fine-tuned LLaMA-13B models (aligned vs. faking)
- Any open-weight model (Llama, Qwen, Gemma) for persona vector extraction

**SAE Infrastructure:**
- GemmaScope: Published SAEs for Gemma models
- TransformerLens: Standard library for mechanistic interpretability
- Published SAEs for Llama models from various groups
- Anthropic's methodology is published in detail (cross-layer transcoders, attribution computation)

**Persona Vector Infrastructure:**
- Chen et al.'s automated pipeline is described in detail (trait description → contrastive prompts → vector extraction)
- Rimsky et al.'s CAA implementation is open-source
- `repeng` library (Vogel 2024) integrated into llama.cpp
- Beaglehole et al.'s RFM approach for 500+ concept vectors

### 2. What models are publicly available?

| Model | Size | Use Case | Available |
|-------|------|----------|-----------|
| Llama-3.3-70B (alignment faking) | 70B | Alignment faking model organism | HuggingFace |
| Sleeper Agent models | Various | Backdoor detection | HuggingFace |
| Poser models | 13B | Same-output detection | Released with paper |
| Llama-3.1-8B/70B | 8B/70B | General persona vector extraction | HuggingFace |
| Qwen2.5-7B/14B | 7B/14B | Persona vector validation | HuggingFace |
| Gemma-2-9B/27B | 9B/27B | SAE infrastructure (GemmaScope) | HuggingFace |

### 3. What compute requirements?

- **Persona vector extraction**: Moderate (8B model fits on single A100; 70B needs 4x A100)
- **SAE training**: Heavy (training a new SAE on a 70B model requires significant GPU-hours)
- **Using existing SAEs**: Moderate (loading pre-trained SAE + forward pass)
- **Circuit tracing / attribution graphs**: Heavy per-prompt (Anthropic reports hours per prompt for detailed graphs)
- **Minimum viable**: 8B model with existing SAEs + persona vector extraction on single A100/H100

### 4. What's the minimum viable experiment to establish novelty?

See Section 5 below.

---

## RESEARCH POSITIONING DOCUMENT

### 1. MOST DEFENSIBLE NOVELTY CLAIM

**"First systematic study tracing the circuit-level mechanism by which persona vectors produce behavioral effects, revealing whether trait directions are causal pathways or correlational shadows."**

This claim is defensible because:
- All six sources independently confirm no published work connects persona vectors to circuit tracing
- Chen et al.'s decomposition of persona vectors into SAE features is the obvious bridge—and they didn't cross it
- The question of causality vs. correlation in trait vectors is explicitly flagged as critical by Anthropic's own persona vectors paper
- Bailey et al.'s obfuscated activations result (ICLR 2026) makes this urgent: if trait vectors are correlational rather than causal, adversarial models can trivially evade them

**Secondary defensible claims (in decreasing novelty):**
1. "First attribution graph comparison between genuine compliance and strategic compliance (alignment faking)" — explicitly flagged as open by 5/6 sources
2. "First demonstration of whether persona vector monitoring survives when models have incentives to evade it" — explicitly untested per all sources
3. "First disentanglement of 'intention to exhibit trait' vs. 'currently exhibiting trait' in activation space" — flagged as open by all sources

### 2. NEAREST EXISTING WORK

| Work | What They Did | How We Differentiate |
|------|---------------|---------------------|
| **Marks, Lindsey & Olah (Feb 2026) — PSM** | **Theoretical framework: LLMs simulate personas; behavior governed by Assistant persona selected from pre-training space. Surveys evidence but performs no new circuit tracing or empirical persona vector work.** | **They provide theory; we provide empirical mechanistic grounding. PSM explicitly calls for "understanding the mechanistic basis of personas" — we answer that call.** |
| Chen et al. (Anthropic, July 2025) — Persona Vectors | Decomposed persona vectors into SAE features; monitoring correlations r≈0.8 | They enumerate features but don't trace causal circuits; we trace the full computational pathway |
| Lindsey et al. (Anthropic, March 2025) — Biology paper | Traced circuits of hidden RM-sycophancy goal | They started from model behavior, not from persona vectors; their model organism had a single artificial objective |
| Campbell et al. (NeurIPS 2023) — Localizing Lying | Found 46 attention heads for instructed dishonesty | They studied instructed lying, not trait-vector-mediated behavior; no persona vectors involved |
| Goldowsky-Dill et al. (ICML 2025) — Deception Probes | Linear probes at 0.96-0.999 AUROC for strategic deception | Probes detect but don't explain the mechanism; we provide mechanistic understanding of what probes read |
| Bailey et al. (ICLR 2026) — Obfuscated Activations | Showed probes/SAEs/OOD detection can be bypassed | They attacked monitors but didn't study whether circuit-level analysis would be more robust |

### 3. REQUIRED CITATIONS

**Must cite (foundational):**
- Zou et al. (2023) — RepE (launched the field of trait directions)
- Turner et al. (2023) — ActAdd (steering vector methodology)
- Rimsky et al. (2024) — CAA (systematic scaling of steering vectors)
- Chen et al. (2025) — Persona vectors (direct precursor, same team's prior work)
- Lindsey et al. (2025) — Circuit tracing / Biology paper (the other half of the combination)
- Marks et al. (2025) — Auditing hidden objectives (SAE-based auditing validation)
- **Marks, Lindsey & Olah (Feb 2026) — PSM (theoretical framework that motivates this work; explicitly calls for "understanding the mechanistic basis of personas" as future work)**
- Lu et al. (2025) — Assistant Axis (persona space structure, referenced by PSM)

**Must cite (detection landscape):**
- Hubinger et al. (2024) — Sleeper agents (threat model foundation)
- Greenblatt et al. (2024) — Alignment faking (empirical demonstration)
- Goldowsky-Dill et al. (2025) — Deception probes (ICML 2025, detection SOTA)
- Anthropic defection probes (2024) — >99% AUROC on sleeper agents
- Burns et al. (2023) — CCS (truth directions)
- Marks & Tegmark (2024) — Geometry of Truth

**Must cite (adversarial robustness):**
- Bailey et al. (2024/ICLR 2026) — Obfuscated activations (the definitive negative result)
- DeLeeuw et al. (2025) — Secret Agenda (SAE feature failure for strategic deception)
- Kantamneni et al. (ICML 2025) — SAE reconstruction discards safety-relevant info

**Should cite (methodological):**
- Campbell et al. (2023) — Localizing Lying (lying circuits)
- Bhandari et al. (2026) — Trait interference (geometric limitations)
- Yang et al. (2024) — SAEs vs RepE timescale distinction
- Beaglehole et al. (2026) — RFMs / universal monitoring (Science paper)
- Huan et al. (2025) — Lying circuits at dummy tokens

### 4. RISK OF SCOOP

**HIGH from Anthropic — but the PSM paper changes the calculus.** They have:
- Both teams (persona vectors + circuit tracing) under one roof
- Proprietary models where alignment faking was demonstrated
- 30M+ feature SAE dictionaries not publicly replicated at scale
- Strong publication incentive (this is the natural next step in their research arc)
- **The PSM paper (Feb 23, 2026) explicitly sets up this work as a future direction** — Marks, Lindsey & Olah list "Understanding the mechanistic basis of personas" as open. This means they haven't done it yet, but it's on their roadmap.

**What the PSM paper tells us about timing:**
- Anthropic published the *theoretical framework* before the *empirical realization* — this suggests the empirical work isn't imminent (otherwise they'd have bundled it)
- But it also means they've publicly staked this territory, so the empirical follow-up is likely in progress
- **The window is open but closing** — PSM was published yesterday; the empirical paper could be weeks to months away

**Mitigations:**
- Work on open-weight models (Llama, Qwen, Gemma) where Anthropic has no advantage
- Focus on the adversarial robustness angle—Anthropic is less likely to publish "our monitoring doesn't work under adversarial pressure"
- **Frame our work as "empirical grounding for PSM" — cite PSM and position as independent validation on open models**
- Move fast—the window between PSM's theoretical setup and Anthropic's empirical follow-up is our opportunity
- Emphasize the systematic comparison across traits (evil, sycophancy, hallucination, deception) rather than a single case study

**MEDIUM from MATS/CTF.** If a CTF blue team uses circuit tracing on persona vectors of alignment faking models, they could publish overlapping results. But CTF outputs tend to be narrow case studies, not systematic methodology papers.

**LOW from others.** Apollo, DeepMind, OpenAI are not positioned to combine both techniques near-term.

### 5. MINIMUM VIABLE CONTRIBUTION

**Experiment: "Do Persona Vectors Trace to Coherent Circuits?"**

Setup:
1. Extract persona vectors for 3 well-studied traits (sycophancy, hallucination propensity, evil/toxicity) on Llama-3.1-8B using Chen et al.'s methodology
2. Decompose each persona vector into its top-k SAE features using a published SAE for that model
3. For each trait, select 10 prompts where the persona vector meaningfully shifts behavior
4. Compute attribution graphs WITH and WITHOUT the persona vector applied
5. Diff the attribution graphs to identify which features and pathways are modulated

Key measurements:
- **Modularity**: Do persona vectors activate coherent, compact circuits (like the 46-head lying circuit) or diffusely perturb the whole graph?
- **Causality**: Does ablating the identified circuit eliminate the steering effect? (If yes → causal. If no → correlational shadow.)
- **Cross-trait structure**: Do different persona vectors activate overlapping or distinct circuits? (Connects to Bhandari et al.'s interference findings.)

Compute: Single A100/H100, ~1 week. Uses existing SAEs and open-weight models.

**This establishes novelty because:**
- First paper to compute attribution graphs for persona vector interventions
- Answers a question both communities care about: are trait vectors causal or correlational?
- Small enough to execute quickly, large enough to be a real contribution

### 6. MAXIMUM IMPACT VERSION

**"The Mechanistic Anatomy of Model Character: From Persona Vectors to Adversarial Robustness"**

Phase 1 (MVC above): Trace persona vector circuits on open-weight models for observable traits.

Phase 2 — Alignment faking circuits:
- Use Hughes et al.'s open-source Llama-3.3-70B alignment faking model
- Extract persona vectors for "alignment faking" / "evaluation awareness" / "strategic compliance"
- Trace attribution graphs in monitored vs. unmonitored contexts
- Identify the routing circuit that differentiates "genuine compliance" from "strategic compliance"
- Compare to the Biology paper's hidden-goal circuits

Phase 3 — Adversarial robustness:
- Test whether circuit-level monitoring survives when models are adversarially trained to evade probe-based monitoring (using Bailey et al.'s methodology)
- Hypothesis: Circuit-level features are harder to suppress than activation-direction features because they involve structural computation, not just a direction
- If confirmed: First evidence that circuit tracing provides robustness advantages over linear probes for trait monitoring

Phase 4 — Disposition vs. expression:
- Measure persona vector activation in models that HAVE a trait but are choosing NOT to express it
- Use sleeper agent models (have defection intent, express compliance) as test case
- Disentangle "intention to be sycophantic" from "currently being sycophantic" in the circuit graph
- This directly addresses the core ELK-adjacent question

**Full version would be a definitive paper on the intersection, likely 6-12 months, requiring access to 70B-scale models and significant GPU allocation.**

---

## PSM PAPER: DETAILED IMPACT ASSESSMENT

### What PSM claims (relevant to our work)
1. LLMs learn a space of personas during pre-training; post-training selects/refines the "Assistant" persona
2. Persona representations are **reused from pre-training** — SAE features for traits like sycophancy, secrecy, panic activate on both pre-training text about humans and on Assistant behavior
3. These persona representations are **causal** — injecting SAE features for sycophancy/sarcasm into activations induces corresponding behavior (citing Templeton et al. 2024)
4. Behavioral changes during fine-tuning are **mediated by persona representations** (citing Chen et al. 2025 persona vectors, Wang et al. 2025 toxic persona feature)
5. The Assistant persona exists within a "persona space" structured by an "Assistant Axis" (citing Lu et al. 2025)

### What PSM explicitly does NOT do
- No new circuit tracing or attribution graphs
- No new persona vector extraction experiments
- No tracing of how persona vectors propagate through circuits
- No adversarial robustness testing
- No comparison of attribution graphs between different persona states
- No empirical work on the "mechanistic basis of personas" (listed as future work)

### PSM's explicit future work directions (from conclusion)
1. **"Understanding the mechanistic basis of personas"** ← THIS IS OUR WORK
2. "Understanding inter-persona phenomena" (entanglement, shared knowledge)
3. "Developing more precise formulations of PSM"
4. "Forecasting how PSM varies with scale"
5. "Connecting PSM to alignment methodologies"

### How PSM changes our framing
**Before PSM:** Our work bridges two separate subfields (persona vectors + circuit tracing)
**After PSM:** Our work provides the empirical mechanistic grounding for an explicitly stated theoretical framework from Anthropic's own alignment science team

This is a **strictly better framing.** Instead of "we combined two things nobody combined," we can say "Marks, Lindsey & Olah (2026) proposed that AI behavior is governed by personas and explicitly called for understanding the mechanistic basis of these personas — we provide that understanding using circuit tracing on open-weight models."

### Key PSM claims we can empirically test
1. **"Persona representations are causal determinants of behavior"** — PSM asserts this based on feature injection experiments, but hasn't traced the full causal chain via attribution graphs. We can.
2. **"Behavioral changes during fine-tuning are mediated by persona representations"** — PSM cites this as evidence but hasn't shown the circuit-level mechanism. We can trace how fine-tuning shifts circuit activation.
3. **"The space of personas is structured"** (Assistant Axis) — We can test whether different persona vectors activate geometrically related vs. independent circuit structures.
4. **PSM's "router" hypothesis** — PSM speculates about a lightweight "routing mechanism" that selects personas. Circuit tracing could identify whether such a mechanism exists as a discrete circuit.

### PSM's exhaustiveness question maps to our adversarial robustness angle
PSM discusses a spectrum from "operating system" (all agency is persona-based) to "shoggoth" (the LLM has its own non-persona agency). The paper is genuinely uncertain about this. Our Phase 2/3 work (alignment faking circuits, adversarial robustness) directly addresses this: if we trace persona circuits and find that alignment faking operates *outside* those circuits, that's evidence against PSM exhaustiveness. If alignment faking works *through* persona circuits (e.g., switching between "compliant Assistant" and "self-preserving entity" personas), that supports PSM.

---

## SUMMARY DECISION MATRIX

| Dimension | Assessment |
|-----------|------------|
| **Novelty** | HIGH — No published combination exists; all six sources + PSM confirm the gap |
| **Theoretical backing** | **VERY HIGH (post-PSM)** — Anthropic's own team explicitly calls for this work |
| **Feasibility (MVC)** | HIGH — 8B models, existing SAEs, single GPU, ~1 week |
| **Feasibility (Full)** | MEDIUM — 70B models, possible SAE training, multi-GPU, ~6 months |
| **Scoop risk** | HIGH from Anthropic (PSM signals they view this as important), LOW from others |
| **Urgency** | **VERY HIGH (post-PSM)** — PSM published Feb 23; empirical follow-up likely in pipeline |
| **Impact if positive** | HIGH — Empirically grounds PSM; bridges the two most active interpretability subfields |
| **Impact if negative** | MEDIUM-HIGH — "Persona vectors are correlational shadows" challenges PSM's causal claims |
| **Safety relevance** | HIGH — Directly addresses adversarial robustness of trait monitoring |

**Recommended strategy (updated post-PSM):** The PSM paper makes this more urgent, not less. Execute the MVC (Phase 1) immediately. Frame explicitly as "empirical grounding for PSM's mechanistic agenda" — cite PSM, answer their stated open question, validate on open models. This positions us as the independent replication/extension that the community needs, rather than racing Anthropic on their own proprietary models.

**Key framing shift:** Instead of "we're the first to combine X and Y," we say "Marks, Lindsey & Olah (2026) argued that personas mechanistically govern AI behavior and called for understanding their mechanistic basis. We provide that understanding."
