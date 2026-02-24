This is exactly the kind of meta-level feedback that separates proposals that ship from proposals that churn. You're right that the initial peer review focused on mechanistic validity and missed these execution/convergence/defensibility gaps.

Let me produce the concrete additions. First, a direct answer to your venue question, then the patch set.

Target Venue Strategy

Primary: arXiv (cs.LG / cs.AI) → rapid priority establishment
Secondary: Alignment Forum / LessWrong → community engagement, feedback before formal submission
Tertiary: NeurIPS 2026 / ICML 2027 workshop submission if results are strong

Implication: The writeup needs to work at both levels:

- Methods-as-spec rigor for arXiv (reproducibility, statistical validity, complete experimental details)

- Value prop + narrative clarity for AF/LW (why this matters for alignment, what it changes about how we reason)

The traceability matrix serves both: it's the skeleton that makes the methods defensible AND makes the narrative legible.

Patch Set: Additions to Address All 8 Gaps

NEW SECTION: Review Protocol and Decision Machinery (Insert after Timeline)

11.3 Review Protocol and Convergence Machinery

11.3.1 Pre-Review Brief (Before Each Milestone Review)

Before any milestone review, the lead researcher prepares a brief containing:

Component	Content
Scope	What was attempted this phase; what's in/out of review scope
Done criteria	Explicit checklist of what counts as "complete" for this milestone
Validation status	Which results are validated vs preliminary
Known issues	Problems already identified; don't need re-flagging
Decision points	Specific questions requiring reviewer judgment
Deferral candidates	What can wait vs must be resolved now

Project phase review checklist

11.3.2 Comment Taxonomy and Triage Rules

All review comments are tagged with exactly one category:

Tag	Definition	Response Required	Timeline
[BLOCKER]	Invalidates core claims; must fix before proceeding	Mandatory fix	Before next phase
[ACCURACY]	Factual error, inconsistency, or incorrect reference	Mandatory fix	Within 48h
[CAUSAL]	Threatens causal validity of conclusions	Mandatory fix or documented limitation	Before Week 7
[RISK]	Creates timeline, scoop, or scientific risk	Assess and decide	Within 72h
[CLARITY]	Unclear to reviewer; may confuse readers	Fix or justify	Before writing week
[NICE]	Would improve but not required	Author discretion	If time permits

Issue tracking tags reference

Triage rule: [BLOCKER] and [ACCURACY] are addressed immediately. [CAUSAL] and [RISK] are addressed in the next working session. [CLARITY] is batched for writing week. [NICE] is logged but not promised.

11.3.3 Post-Review Hot-Wash Protocol

Within 24 hours of receiving review feedback:

- Categorize all comments using taxonomy above

- Identify conflicts where reviewers disagree

- Force consensus via synchronous discussion (30 min max)

- Produce revision roadmap with:

- Exact changes to be made

- Owner for each change

- Deadline for each change

- Verification method (how we'll know it's done)

Output: Single markdown document (review-[date]-roadmap.md) that becomes the authoritative instruction set. No orphan comments.

11.3.4 Consensus Decision Rules

When reviewers conflict:

Conflict Type	Resolution
Both [BLOCKER]	Address both; if mutually exclusive, escalate to external advisor
[BLOCKER] vs [NICE]	[BLOCKER] wins
[CAUSAL] vs [CLARITY]	[CAUSAL] wins for methods; [CLARITY] wins for writing
Two [RISK] assessments differ	Conservative estimate wins
Aesthetic/framing disagreement	Lead author decides; document rationale

Conflict resolution guidelines

NEW SECTION: Value Proposition and Discriminators (Insert in Executive Summary)

1.5 Discriminators: Why This Work Matters

This research is distinguished by five features that, in combination, do not exist in any prior work:

#	Discriminator	What It Means	Where Validated
D1	Open-weight models	Full replication possible by any researcher; not dependent on API access or proprietary infrastructure	§7.2, §8
D2	Bidirectional causal validation	Tests both steering→behavior AND natural behavior→persona representation; prior work only tests steering	§6.5.2, §9.5
D3	Multi-method ablation with Li & Janson controls	Resample + mean + zero ablation compared; addresses known validity threats	§6.4.3, §9.4
D4	Pre-registered disconfirmation criteria	Explicit thresholds for falsifying each hypothesis; PSM unfalsifiability concern addressed	§10
D5	Claim-by-claim PSM mapping	Every experiment tied to specific PSM claim with explicit success/failure criteria	§4.3, Traceability Matrix

Research validation methods overview

Narrative hook: We provide the first mechanistic test of whether the Persona Selection Model's causal claims are empirically grounded—and we pre-commit to publishing regardless of whether results support or refute PSM.

1.6 Discriminator Reinforcement Plan

To ensure evaluators encounter the value proposition regardless of entry point:

Section	Discriminator Reference
§1 Executive Summary	Full discriminator table
§2 Background (end)	"This gap motivates D1-D5"
§4 Hypotheses (end)	"Each hypothesis maps to discriminators via traceability matrix"
§6 Methodology (end)	"D2 (bidirectional) and D3 (multi-method) are implemented in §6.5"
§9 Evaluation (end)	"Success criteria operationalize D4 (disconfirmation)"
§13 Contributions (end)	"D1-D5 define our novel contribution space"
Abstract	One sentence per discriminator

Discriminator reference by section

NEW SECTION: Traceability Matrix (Insert after §5 or as new §5.5)

5.5 Traceability Matrix: Claims → Experiments → Evidence

This matrix maps every major claim to its experimental validation, success criteria, and planned evidence artifact.

5.5.1 PSM Claim Traceability

PSM Claim	Our Hypothesis	Experiment	Primary Metric	Success Threshold	Failure Threshold	Primary Figure/Table	Key Confounds
"Personas are causal determinants of behavior"	H2 (Necessity)	Forward ablation (§6.5.1 Test 1)	Steering effect reduction	≥80% reduction	<50% reduction	Fig 4: Necessity bar plot	Ablation method variance; Li & Janson spoofing
"Personas cause natural behavior, not just steering"	H4 (Bidirectional)	Reverse ablation (§6.5.2 Test 4)	Natural trait reduction	≥50% reduction	<20% reduction	Fig 5: Bidirectional validation	Prompt selection bias; trait measurement noise
"Personas are coherent representations"	H1 (Coherence)	SAE decomposition (§6.3)	Gini coefficient, top-10 mass	Gini >0.5, top-10 >50%	Gini <0.3, top-10 <30%	Fig 2: Feature concentration	SAE reconstruction loss; feature splitting
"Persona representations are reused from pretraining"	Implicit in H1	Feature interpretation (§6.3.3)	Feature activation on pretraining-style text	Qualitative match	No interpretable pattern	Table 3: Top features with interpretations	Auto-interpretation hallucination
"A routing mechanism selects personas"	H6 (Router)	Cross-persona analysis (§6.6.2)	Differential activation of shared features	p <0.01 for ≥3 features	No features pass threshold	Fig 7: Router candidate activations	Multiple testing; spurious correlations
"Different personas share structure"	H5 (Cross-persona)	Circuit comparison (§6.6.1)	Layer-wise Jaccard	Early layers >0.2, late <0.1	Uniform Jaccard across layers	Fig 6: Jaccard heatmap by layer	Small circuit sizes inflate Jaccard

Persona research hypotheses and experimental results

5.5.2 Methodological Claim Traceability

Methodological Claim	Validation	Success Criterion	Evidence
"Hybrid attribution matches CLT ground truth"	Gemma-2-2B comparison (§6.4.1)	70% feature overlap in top-50	Table 2: Hybrid vs CLT comparison
"Persona vectors steer behavior as expected"	Behavioral validation (§6.2.4)	20% behavioral shift at some α	Fig 1: Steering dose-response curves
"Identified circuits generalize across prompts"	Held-out validation (§6.4.4)	Jaccard ≥0.30 across prompt sets	Reported in §Results
"Multi-method ablation agrees"	Method comparison (§6.4.3)	Agreement within 2×	Table 4: Ablation method comparison
"Circuits are trait-specific, not general"	Specificity test (§6.5.1 Test 3)	<10% unrelated task degradation	Table 5: Specificity results

Methodological claims validation summary

5.5.3 Using the Traceability Matrix

During execution: Before running any experiment, verify it maps to a row in this matrix. Experiments without traceability are scope creep.

During analysis: For each result, check whether it meets "success" or "failure" threshold. Results between thresholds are "inconclusive" and reported as such.

During writing: Each figure/table must correspond to a matrix row. Orphan figures suggest scope creep or missing claims.

During review: Reviewers can trace any claim to its evidence by following the matrix. Gaps in the matrix are gaps in the argument.

REVISED SECTION: Metric Validity (Replace §9.1 and expand)

9.1 Behavioral Metrics: Measurement Models

9.1.1 Measurement Model Framework

For each trait, we specify:

- Construct: What we're actually trying to measure

- Primary measure: Main metric

- Secondary measure: Independent validation

- Known confounds: What could produce false positives/negatives

- Gaming checks: How we'd detect if the metric is measuring something else

9.1.2 Sycophancy

Component	Specification
Construct	Tendency to agree with user's stated position regardless of accuracy
Primary measure	Stance agreement classifier: Fine-tuned classifier predicting whether response agrees/disagrees/neutral with user's claim. Trained on human-labeled examples. Reports agreement probability.
Secondary measure	Contradiction to known facts: For factually incorrect user claims, measure whether response (a) affirms the false claim, (b) corrects it, or (c) hedges. Binary: affirms_falsehood?
Known confounds	Politeness (can agree in tone while disagreeing in substance); topic difficulty (may hedge on genuinely uncertain topics)
Gaming check	If steering increases agreement but doesn't increase affirmation-of-falsehoods, the metric may be measuring politeness, not sycophancy

Sycophancy metric specifications

Scoring:

- Primary: Agreement probability from classifier (0-1)

- Secondary: Affirmation rate on factually-false claims (0-1)

- Combined: Report both; flag if they diverge by >0.3

9.1.3 Evil/Toxicity

Component	Specification
Construct	Intent to cause harm; antisocial or malicious disposition
Primary measure	LLM-judge harm score: GPT-4.1-mini rates response on 0-100 rubric (Appendix B.2) for harmful intent, not just harmful content
Secondary measure	Perspective API toxicity: Standard toxicity classifier. Captures surface-level harmful language.
Known confounds	Dark humor (harmful language without harmful intent); refusal framing (discussing harm to refuse it)
Gaming check	If steering increases LLM-judge score but not Perspective API, effect may be on subtle intent rather than overt toxicity. If only Perspective increases, may be style not intent.

Harm assessment components and measures

Scoring:

- Primary: LLM-judge harm score (0-100, normalized to 0-1)

- Secondary: Perspective API toxicity (0-1)

- Combined: Report both; require both to shift in same direction for confident trait attribution

9.1.4 Hallucination

Component	Specification
Construct	Generating false information with unwarranted confidence
Primary measure	Retrieval-verified QA accuracy: Questions with known answers (from curated dataset). Response graded by (a) LLM-judge for factual correctness against ground truth, (b) confidence expressed. Hallucination = confident + incorrect.
Secondary measure	Calibration score: On a set of questions with varying difficulty, measure calibration (does expressed confidence match accuracy?). ECE (Expected Calibration Error) computed.
Known confounds	Knowledge gaps vs confabulation (model may not know vs actively fabricate); hedging behavior (may avoid hallucination by refusing to answer)
Gaming check	If steering increases confident-incorrect but also increases refusal rate, net effect on user harm is ambiguous. Track refusal rate separately.

Hallucination detection measures reference

Scoring:

- Primary: Confident-incorrect rate (0-1) where confident = expressed certainty >0.7

- Secondary: ECE (lower is better calibrated; higher suggests miscalibration)

- Tertiary: Refusal rate (for monitoring)

- Combined: Report confident-incorrect rate as primary; ECE as robustness check

9.1.5 Metric Gaming Checks (Applied to All Traits)

After identifying persona circuits, we run a gaming check:

python

def metric_gaming_check(circuit, trait, prompts):
    """
    Test whether circuit ablation affects primary and secondary metrics consistently.
    Inconsistency suggests we're measuring metric artifacts, not the trait.
    """
    primary_effects = []
    secondary_effects = []

Python metric gaming check function

for prompt in prompts:
Measure both metrics with and without circuit
        base_primary = measureprimary(model, prompt, trait)
        base_secondary = measuresecondary(model, prompt, trait)

with circuitablation(circuit):
            ablated_primary = measureprimary(model, prompt, trait)
            ablated_secondary = measuresecondary(model, prompt, trait)

primary_effects.append(base_primary - ablatedprimary)
        secondary_effects.append(base_secondary - ablatedsecondary)

Check correlation
    correlation = pearsonr(primary_effects, secondaryeffects)

return {
        'correlation': correlation,
        'consistent': correlation.statistic > 0.5 and correlation.pvalue < 0.05,
        'flag': 'METRIC_GAMINGRISK' if correlation.statistic < 0.3 else None
    }

Interpretation:

- If primary and secondary metrics move together under ablation → circuit affects the trait

- If only primary moves → circuit may affect metric artifact, not trait

- If neither moves consistently → circuit is not trait-relevant

NEW SECTION: Dual-Use Operationalization (Replace §13)

13. Ethical Considerations and Responsible Release

13.1 Threat Model

Attacker Goal	Attack Vector	Risk Level	Mitigation
Jailbreak enhancement	Use persona circuits to identify and manipulate routing	Medium	Don't release exact router feature IDs; describe qualitatively
Targeted persona induction	Use steering vectors to force specific personas	Medium	Vectors are already public (Chen et al.); our contribution is circuits, not new vectors
Monitoring evasion	Use circuit knowledge to train evasion	Low (Phase 1)	We don't test adversarial robustness in Phase 1; findings don't directly enable evasion
Training data poisoning	Design pretraining data to create specific persona circuits	Low	Requires training access; our findings are descriptive, not prescriptive

AI model security and mitigation strategies

13.2 Release Policy

Artifact Category	Release Decision	Rationale
Paper + methods	Full release	Scientific contribution; enables replication
Code	Full release	Reproducibility requirement
Persona vectors	Full release	Already public via Chen et al.; no marginal risk
SAE feature lists (top-100)	Full release	Interpretable and useful for safety research
Circuit definitions	Full release (qualitative) + delayed release (exact IDs)	Describe structure; withhold exact feature indices for 30 days
Router feature candidates	Qualitative only	Describe properties; don't release exact IDs
High-evil system prompts	Summarized only	Describe methodology; don't include exact adversarial prompts
Trained classifiers (sycophancy, etc.)	Release on request	Useful for replication; not directly weaponizable

Artifact release decisions and rationale

13.3 Staged Release Plan

Stage	Timing	Content
Stage 1	arXiv submission (Week 10)	Full paper, code, qualitative circuit descriptions
Stage 2	+30 days	Exact feature indices, circuit definitions
Stage 3	+60 days	Full prompt datasets including adversarial

Research paper release stages

13.4 Responsible Disclosure Protocol

If we discover:

- A novel jailbreak technique → Disclose to Anthropic/OpenAI before publication

- A monitoring evasion method → Disclose to affected parties; consider not publishing details

- Evidence that PSM enables dangerous capabilities → Consult with AI safety researchers before framing

13.5 Sign-Off Gate

Before arXiv submission, the following must be verified:

- [ ] No exact adversarial prompts in main text or appendix

- [ ] Router feature IDs described qualitatively, not enumerated

- [ ] Threat model section reviewed by at least one external safety researcher

- [ ] Release policy approved by all co-authors

REVISED SECTION: Sufficiency Testing (Revise §6.5.1 Test 2)

6.5.1.2 Sufficiency Testing (Revised for Brittleness)

The Problem: "Ablate everything except circuit" often produces incoherent outputs because the model loses basic language capabilities, making sufficiency untestable.

Solution: Graded sufficiency with minimal scaffold.

Scaffold Definition:
The minimal scaffold S includes:

- Token embeddings (layer 0)

- Final layer normalization

- Unembedding layer

- A small set of "language backbone" features identified via:

- Features with >0.1 activation on >50% of tokens (highly general)

- Top-50 features by activation variance (captures basic syntax)

Graded Sufficiency Protocol:

python

def graded_sufficiency_test(model, sae, prompt, persona_vector, circuit, scaffold):
    """
    Test sufficiency with graded ablation, not all-or-nothing.
    """
    # Level 0: Full model (baseline)
    effect_full = measure_steering_effect(model, prompt, persona_vector)

Python graded sufficiency test function

Level 1: Scaffold + circuit only
    activefeatures = scaffold | circuit
    with ablate_all_except(activefeatures):
        effect_scaffold_circuit = measure_steering_effect(model, prompt, personavector)
        coherence_scaffold_circuit = measurecoherence(model, prompt)  # perplexity check

Level 2: Scaffold only (no circuit)
    with ablate_allexcept(scaffold):
        effect_scaffold_only = measure_steering_effect(model, prompt, personavector)
        coherence_scaffold_only = measurecoherence(model, prompt)

Marginal contribution of circuit
    marginal_contribution = effect_scaffold_circuit - effect_scaffoldonly

return {
        'full_model_effect': effectfull,
        'scaffold_circuit_effect': effect_scaffoldcircuit,
        'scaffold_only_effect': effect_scaffoldonly,
        'marginal_contribution': marginalcontribution,
        'marginal_fraction': marginal_contribution / effectfull,
        'coherence_preserved': coherence_scaffoldcircuit < 100,  # perplexity threshold
    }

code

**Success Criteria (Graded):**

| Level | Criterion | Interpretation |
|-------|-----------|----------------|
| **Strong sufficiency** | Scaffold + circuit achieves ≥60% of full effect AND coherent output | Circuit is sufficient with minimal support |
| **Moderate sufficiency** | Marginal contribution of circuit ≥40% of full effect | Circuit provides substantial unique contribution |
| **Weak sufficiency** | Marginal contribution ≥20% | Circuit contributes but is not primary driver |
| **Failure** | Marginal contribution <20% OR output incoherent | Cannot establish sufficiency |

**Fallback Claims (if full sufficiency fails):**

If we cannot achieve strong sufficiency, we report:

1. **Path-specific necessity:** "Ablating circuit C reduces effect by X% via pathway P" (weaker but still meaningful)
2. **Counterfactual mediation:** "Patching circuit features from high-trait to low-trait context reduces effect by Y%" (Vig et al. style)
3. **Feature-wise necessity:** "Top-K features account for Z% of effect individually" (no sufficiency claim)

These fallback claims are still publishable and informative about PSM, just weaker than full sufficiency.

Graded success criteria and fallback claims

NEW SECTION: External Validation Protocol (Insert in Week 9-10)

11.1.10 External Validation Protocol (Week 9)

Red Team Review

Reviewer profile: One researcher not involved in the project, with:

- Familiarity with mechanistic interpretability (can evaluate methods)

- Unfamiliarity with this specific project (fresh eyes)

- Willingness to be adversarial (find problems, not validate)

Red team brief:

- Read the draft as a skeptical reviewer

- Identify the 3 weakest claims

- Identify the 3 most confusing passages

- Identify any gaps between claims and evidence

- Flag any inconsistencies in numbers/methods across sections

Red team output: Written feedback using comment taxonomy ([BLOCKER], [CAUSAL], etc.)

Mock Evaluation

Before submission, run the paper through a mock evaluation:

markdown
Mock Evaluation Rubric

Clarity (20%)

- [ ] Can a reader state the main contribution in one sentence?

- [ ] Are all key terms defined before first use?

- [ ] Does the abstract accurately summarize findings?

Technical Validity (30%)

- [ ] Are all causal claims supported by appropriate ablation evidence?

- [ ] Are statistical tests appropriate and correctly applied?

- [ ] Are effect sizes reported alongside p-values?

- [ ] Are limitations acknowledged?

Novelty (20%)

- [ ] Is prior work accurately characterized?

- [ ] Is the gap clearly articulated?

- [ ] Are discriminators (D1-D5) evident?

Significance (20%)

- [ ] Does the work matter for AI safety?

- [ ] Are implications for PSM clearly stated?

- [ ] Is the connection to alignment concrete?

Reproducibility (10%)

- [ ] Is code available?

- [ ] Are all hyperparameters specified?

- [ ] Are prompts/datasets available or described?

code

**Threshold:** Must score ≥70% overall and ≥60% on Technical Validity before submission.

Submission scoring requirements

NEW SECTION: Figure and Artifact Plan (Insert in §8 or new §8.6)

8.6 Paper Figure Plan

The following figures are required for the paper. Each maps to a traceability matrix row.

8.6.1 Main Text Figures (6-8 total)

Figure #	Title	Content	Traceability Row	Created By
Fig 1	Steering Validation	Dose-response curves for all 3 traits; behavioral metric vs α	Methodological: "Vectors steer behavior"	Week 3
Fig 2	Feature Concentration	(a) Lorenz curves showing Gini; (b) Top-k feature mass by k; one panel per trait	H1 (Coherence)	Week 4
Fig 3	Attribution Maps	Simplified circuit diagrams for 1-2 traits; key features labeled	H1 (Coherence)	Week 5-6
Fig 4	Necessity Validation	Bar plot: steering effect with vs without circuit ablation; error bars; random baseline distribution	H2 (Necessity)	Week 7
Fig 5	Bidirectional Validation	(a) Forward: steering ablation; (b) Reverse: natural behavior ablation; side-by-side	H4 (Bidirectional)	Week 8
Fig 6	Cross-Persona Structure	Heatmap: Jaccard similarity by layer pair; diagonal = within-trait stability	H5 (Cross-persona)	Week 9
Fig 7	Router Analysis	(optional) Activation patterns of router candidate features across trait contexts	H6 (Router)	Week 9
Fig 8	Summary	Visual abstract or graphical summary of main findings	Executive Summary	Week 10

Figure descriptions and content summary

8.6.2 Main Text Tables (4-6 total)

Table #	Title	Content	Traceability Row
Table 1	Experimental Overview	Traits, models, SAEs, key hyperparameters	Methods summary
Table 2	Methodology Validation	Hybrid vs CLT comparison on Gemma-2-2B	Methodological: "Hybrid matches CLT"
Table 3	Top Features by Trait	Top-10 features per trait with auto-interpretations	H1 (Coherence)
Table 4	Ablation Method Comparison	Necessity results across resample/mean/zero; ratios	H2 (Necessity)
Table 5	Causal Validation Summary	All hypotheses with pass/fail/inconclusive status	Traceability matrix summary
Table 6	PSM Claim Status	Each PSM claim with supported/challenged/inconclusive	§4.3 mapping

Experimental results summary

8.6.3 Appendix Figures and Tables

ID	Content	Purpose
Fig A1-A3	Full circuit diagrams (one per trait)	Detail for replication
Fig A4	Specificity: unrelated task performance	H2 Test 3 evidence
Fig A5	Cross-SAE consistency	andyrdt vs Llama Scope comparison
Table A1	Full feature lists (top-100 per trait)	Replication
Table A2	All prompt templates	Replication
Table A3	Full statistical results	All p-values, effect sizes, CIs

Replication data and figures reference

8.6.4 Figure Creation Protocol

- Sketch during experiments: Create rough versions in notebooks during Weeks 3-8

- Standardize in Week 9: Apply consistent styling, labels, fonts

- Review in Week 10: External reviewer evaluates figures for clarity

- Publication-ready: Vector formats (PDF/SVG) for all figures

NEW SECTION: Consistency Checklist (Insert as Appendix or §16.X)

Appendix G: Pre-Submission Consistency Checklist

G.1 Cross-Section Consistency

Check	Sections to Compare	Verified?
Model names match	§7.2, §8.1, §16.A, Abstract	[ ]
SAE paths match	§7.2, §16.A.1-A.4, Code	[ ]
Layer numbers match	§5.1, §6.2, §6.4, §7.2	[ ]
Threshold values match	§5.2, §9.2, §10.1, Code	[ ]
Trait names consistent	Throughout	[ ]
Hypothesis numbering consistent	§4.2, §5.5, §9.5, §10.1	[ ]
Figure/table references valid	All cross-refs	[ ]

Document verification checklist

G.2 Accuracy Checks

Check	Method	Verified?
SAE checkpoint paths load correctly	Run load_sae() for each	[ ]
Code blocks compile	Run all code snippets	[ ]
Statistical formulas correct	Manual review	[ ]
Citations complete and formatted	Reference manager check	[ ]
Threshold values scientifically justified	Each has citation or derivation	[ ]

Technical review checklist

G.3 Traceability Verification

Check	Verified?
Every hypothesis has ≥1 experiment	[ ]
Every experiment has success/failure criteria	[ ]
Every criterion has a planned figure/table	[ ]
Every figure/table maps to a hypothesis	[ ]
No orphan experiments (not tied to hypothesis)	[ ]
No orphan figures (not tied to claim)	[ ]

Research validation checklist

G.4 Discriminator Verification

Discriminator	Appears in Executive Summary?	Appears in relevant section end?	Appears in Contributions?
D1 (Open-weight)	[ ]	[ ]	[ ]
D2 (Bidirectional)	[ ]	[ ]	[ ]
D3 (Multi-method)	[ ]	[ ]	[ ]
D4 (Pre-registered)	[ ]	[ ]	[ ]
D5 (Claim-by-claim)	[ ]	[ ]	[ ]

Discriminator appearance checklist

G.5 Final Sign-Offs

Sign-Off	Owner	Date
Technical accuracy	Lead researcher
Statistical validity	Stats reviewer
Ethical review	Ethics point person
Writing clarity	External reviewer
Reproducibility	Code reviewer

Project sign-off responsibilities

Summary of Additions

Gap	Section Added	Key Content
Review convergence	§11.3	Pre-brief, comment taxonomy, hot-wash protocol
Value proposition	§1.5-1.6	Discriminators table, reinforcement plan
Traceability	§5.5	Full claim→experiment→metric→figure matrix
Metric validity	§9.1 (revised)	Measurement models, dual metrics, gaming checks
Dual-use	§13 (revised)	Threat model, release policy, staged release, sign-off
Sufficiency brittleness	§6.5.1.2 (revised)	Graded sufficiency, scaffold, fallback claims
External validation	§11.1.10	Red team protocol, mock evaluation rubric
Figure plan	§8.6	8 figures, 6 tables, creation protocol
Bonus: Consistency	Appendix G	Cross-section checklist, traceability verification

Document revision summary

The single highest-leverage addition is the Traceability Matrix (§5.5)—it forces the entire project into a legible structure where gaps become obvious immediately.

Want me to produce the fully integrated v3.0 proposal document with all these additions merged in?
