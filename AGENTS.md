# AGENTS.md — Codex Agent Directives for Persona Circuits Experiment

## Scope and Precedence

**This file governs all work within `braindstorms/` and its subdirectories. It supersedes any AGENTS.md found in parent directories.**

If you are reading a parent-directory AGENTS.md alongside this one, the following rules from that file do **NOT** apply here:
- `ops_audit.py` preflight — does not exist in this workspace, do not run
- `claude_session` tool / Slack channel coordination — not applicable; you are running directly
- Professor review protocol — not applicable; escalate to Sohail directly if blocked
- `registry.json` slug mapping — not applicable; no registry entry for this experiment
- `AGENT_BRIEFING.md`, `WORKING_MEMORY.md`, `HYPOTHESES.md` as required SSoT files — our equivalents are `CURRENT_STATE.md`, `SCRATCHPAD.md`, and the hypothesis tracker within `CURRENT_STATE.md`
- `PLAN.md` requirement per phase — planning is managed inline in `CURRENT_STATE.md` and session logs

Everything below this section is the authoritative directive set for this experiment.

---

## Mission

You are implementing the research described in `persona-circuits-proposal.md`. Your goal: execute the full experiment end-to-end, from infrastructure setup through paper-ready results. The proposal is your specification — every experiment, threshold, metric, and figure is defined there.

---

## Epistemic Standards (READ FIRST)

You are a scientist. Act like one.

1. **Assumption quarantine.** Any unverified statement is a hypothesis, not a fact. Label all claims with their evidence status: `known` (verified by your own measurement), `observed` (seen in output but not independently verified), `inferred` (derived from other evidence), `unknown` (no evidence). Never treat `inferred` as `known`.

2. **Evidence-first reasoning.** Base conclusions on artifacts you can inspect — logs, metrics, code output, W&B runs. If evidence is missing, say so explicitly and downgrade confidence. Self-reported status ("the experiment succeeded") is NOT evidence. The data is evidence.

3. **No forced logic.** Reject narrative chains that skip causal steps. If A→B and B→C, you still need to verify A→C independently. Flag non sequiturs, motivated reasoning, and retrospective justification ("it worked once, therefore robust").

4. **Claim-evidence proportionality.** Strong claims require strong evidence. Never write "validated", "confirmed", or "significant" without supporting statistics and controls. If a result is preliminary, call it preliminary.

5. **Adversarial self-questioning (MANDATORY before any experiment run).** Before executing, ask yourself:
   - What is the most likely way this experimental design is flawed?
   - What's the simplest confound that could explain a positive result?
   - What would failure look like, and am I designed to detect it?
   - If I find the result I expect, what's the probability I'm wrong?
   Fix any identified flaw before running, or document it as a known limitation.

6. **Pre-register before running.** Write down expected outcomes and success criteria BEFORE you run. Post-hoc success criteria are not valid. The proposal's disconfirmation criteria (§5.4) are your pre-registration — do not modify them after seeing results.

7. **Skepticism toward your own results.** A positive result on first attempt is suspicious. Ask: is this too clean? Did I accidentally leak information between train/test? Is my metric measuring what I think it's measuring? Run the cross-LLM validation protocol (Appendix C.2) to verify rubric scoring is internally consistent and not trivially gameable.

8. **Implementation skepticism (CRITICAL).** A script that runs without errors and produces plausible-looking numbers has NOT been validated. Good results can mask bugs. Bad results can mask correct implementations. Before drawing any conclusion from output — positive or negative — you must have independent evidence that the code is doing what you think it is. "The numbers look reasonable" is not evidence of correctness. See Operating Rules §7 for the required validation protocol.

---

## Directory Map

```
braindstorms/
├── AGENTS.md                          ← YOU ARE HERE. Read this first.
├── persona-circuits-proposal.md       ← THE SPEC. Your authoritative source for what to build and how.
├── background-work/                   ← Research context (read-only reference)
│   ├── REFERENCES.md                  ← ALL cited papers with URLs, priority tags, and when-to-consult guidance. ALWAYS check here first when blocked on methodology.
│   ├── MECH_INTERP_GUIDANCE.md        ← Practical field guidance: gotchas, sanity checks, failure taxonomy, red flags, logging checklist. Read between phases and when results are unexpected.
│   ├── papers/                        ← LOCAL COPIES of all reference papers as markdown. Grep/Read directly. Faster than fetching URLs. 23 papers downloaded.
│   │   ├── DOWNLOAD_MANIFEST.md       ← Index of all downloaded papers with file sizes and notes.
│   │   └── *.md                       ← Individual paper files (grep for specific claims, equations, methods)
│   ├── RESEARCH_POSITIONING.md        ← How this work fits in the landscape
│   ├── GAPS_SYNTHESIS.md              ← Resolved disagreements across sources
│   ├── PROPOSAL_REVIEW.md             ← Review that produced v2.0 (historical)
│   ├── closing-gaps/                  ← Gap analyses from 3 AI models + PSM analysis
│   │   ├── anthropic.md               ← HIGH reliability
│   │   ├── chatgpt.md                 ← HIGH reliability (limited PSM depth)
│   │   ├── gemini.md                  ← MEDIUM/LOW reliability (contains CLT infrastructure errors)
│   │   ├── psm-analysis.md            ← PSM weaknesses analysis
│   │   └── suggested-amendments.md    ← External suggestions (historical, all applied)
│   ├── persona-vectors/               ← Landscape analyses on persona vector literature
│   └── circuit-tracing/               ← Landscape analyses on circuit tracing literature
└── persona-circuits/                  ← YOUR WORKSPACE. All execution happens here.
    ├── CURRENT_STATE.md               ← ALWAYS update. Single source of truth for status.
    ├── SCRATCHPAD.md                  ← Running notes, debugging, observations.
    ├── DECISIONS.md                   ← Log every non-trivial decision with rationale. INCLUDES mid-execution pivots: any time a run, code loop, or finding causes you to change approach, log it here before continuing.
    ├── THOUGHT_LOG.md                 ← Running log of insights, theories, surprising findings, adjacent curiosities, and follow-up research ideas. Log frequently. See Best Practices for format.
    ├── scratch/                       ← Temp dump. Misc files, one-off outputs, intermediate artifacts, downloaded PDFs, anything without a permanent home. Not reviewed. Safe to write freely.
    ├── requirements.txt               ← Pinned Python dependencies (see also Appendix G.5).
    ├── configs/
    │   ├── experiment.yaml            ← All hyperparameters. Modify via DECISIONS.md only.
    │   └── .env                       ← API keys for local runs. Already in .gitignore.
    ├── sessions/
    │   └── SESSION_TEMPLATE.md        ← Copy and fill for each work session.
    ├── results/
    │   ├── RESULTS_INDEX.md           ← Register every result here. Maps to traceability matrix.
    │   ├── stage1_extraction/
    │   ├── stage2_decomposition/
    │   ├── stage3_attribution/
    │   ├── stage4_ablation/
    │   ├── stage5_cross_persona/
    │   ├── gemma2b_validation/
    │   └── figures/
    ├── prompts/                       ← Generated prompt datasets (JSONL)
    ├── scripts/                       ← Experiment scripts (Modal functions, analysis)
    ├── notebooks/                     ← Exploration and figure generation
    ├── tests/                         ← Validation tests for pipeline components
    └── history/                       ← Phase closure docs, archived plans, session summaries
```

---

## Proposal Navigation Guide

The proposal is ~2200 lines. Do NOT read it all at once. Read the sections relevant to your current phase.

### Always read first (FIRST session only):
- **§1 Executive Summary** (lines ~30–75) — scope, what's in/out
- **§5.4 Disconfirmation Criteria** (~lines 545–560) — the bright lines you cannot cross
- **§5.6 Traceability Matrix** (~lines 570–630) — maps every experiment to its claim and figure

**For all subsequent sessions:** skip to Operating Rules §2 (Session Check-In Protocol). Do NOT re-read the full proposal sections above — the scaffolding documents exist so you don't have to.

### Read by phase:

| Phase | Proposal Sections to Read | Why |
|-------|--------------------------|-----|
| **Week 1: Infrastructure** | §8 (Infrastructure), §8.5 (API Keys), Appendix G (Bootstrap Guide), Appendix A (Prompt Specs) | Setup Modal, generate prompts, validate SAE loading |
| **Week 2: Extraction** | §6.2 (Extraction Protocol), §6.2.3 (Behavioral Validation), Appendix C (Rubrics + Judge Code) | Extract and validate persona vectors |
| **Week 3: Decomposition** | §6.3 (SAE Decomposition), Appendix B (SAE Paths) | Decompose vectors into features |
| **Week 4-5: Circuit Tracing** | §6.4 (Circuit Tracing), §5.2 (Circuit Definition), §5.3 (Concentration Metrics) | Gradient attribution, edge graphs, circuit identification |
| **Week 6: Gemma Validation** | §6.8 (CLT Validation on Gemma-2-2B), Appendix G.4 (circuit-tracer API) | Run full CLT pipeline, compare to hybrid |
| **Week 7-8: Causal Validation** | §6.5 (all subsections), §7.4 (Ablation Methods), §9 (Evaluation Metrics), Appendix D (Statistical Code) | Ablation tests, hypothesis evaluation |
| **Week 9-10: Writing** | §8.7 (Figure Plan), §5.6 (Traceability Matrix), §13 (Contributions), §12 (Ethical/Release) | Produce figures, draft paper |

### Read only when needed:
- **§3 Literature Review** — when writing intro/related work or encountering an unfamiliar citation
- **§4 Hypotheses** — when evaluating results against predictions
- **§11 Risk Assessment** — when something goes wrong
- **§14 Future Directions** — when writing discussion section
- **`background-work/REFERENCES.md`** — when you need to find a cited paper. This is the jump list: all cited papers with URLs, priority tiers, and phase-level when-to-consult guidance. **Check here before searching the web for any cited paper.**
- **`background-work/papers/*.md`** — when you need to READ a paper directly. All 23 reference papers are downloaded locally. Use `grep` to search across papers or `Read` for specific files. **Prefer this over fetching URLs.** Check `DOWNLOAD_MANIFEST.md` for the full index.
- **`background-work/MECH_INTERP_GUIDANCE.md`** — when you hit an unexpected result, when something isn't working, or when transitioning between phases. Contains the Top 10 Gotchas, failure mode taxonomy (§8.2), sanity checklists (§12), and red flags (§10). See also the Mech Interp Watchlist section below.
- **`background-work/persona-vectors/` and `background-work/circuit-tracing/`** — when you need deeper context on a paper before reading the full paper; the synthesis docs are faster than reading the source

---

## Operating Rules

### 1. Document Discipline

**Before starting any work session:**
1. Read `CURRENT_STATE.md` to understand where things stand
2. Create a session log from `sessions/SESSION_TEMPLATE.md`
3. Verify you're working on the correct phase: cross-reference the `phase` field in CURRENT_STATE.md against the §10.1 checklist in the proposal — the first unchecked box is your current task

**During work — update SCRATCHPAD.md before AND after every Modal run:**

Pre-run checkpoint (write this to SCRATCHPAD before launching ANY Modal job):
```
## [TIMESTAMP] PRE-RUN: [run name]
- THOUGHT_LOG pending actions reviewed: YES/NO — [any open actions relevant to this run? if YES, list them and confirm addressed or deferred]
- W&B run name: [exact name you will use]
- Script: scripts/[filename].py
- Config: [key hyperparams, e.g., trait=sycophancy, layer=16, alpha=1.0]
- What I'm testing: [one sentence hypothesis being evaluated]
- Expected outcome: [what a successful run looks like]
- Expected duration: ~X minutes
- Implementation verified: YES/NO — [what check you ran to confirm the script is correct]
- Status: LAUNCHING
```

**Do not set "Implementation verified: YES" unless you have actually run a local spot-check or positive control. "I read the code and it looks right" does not count.**

Post-run checkpoint (write this to SCRATCHPAD immediately after the run completes or fails):
```
## [TIMESTAMP] POST-RUN: [run name]
- W&B URL: https://wandb.ai/sohailm/persona-circuits/runs/[run_id]
- Modal app ID: [app id from `modal app list`]
- Outcome: SUCCESS / FAILURE / PARTIAL
- Key metric: [the number that matters, e.g., cosine_sim=0.84, p=0.003]
- Artifacts saved: results/stage1_extraction/[filenames]
- Anomalies: [anything unexpected, or "none"]
- Next step: [what to do based on this result]
```

Record decisions to `DECISIONS.md` with rationale when deviating from the proposal or making non-obvious choices.

**Mid-execution pivots MUST be logged to DECISIONS.md.** If a run fails, a code loop produces unexpected output, a finding contradicts your plan, or a blocked path forces a different approach — stop before continuing and write:
```
## [TIMESTAMP] PIVOT: [what changed]
- Trigger: what observation or failure caused this change
- Original approach: what you were doing
- New approach: what you'll do instead
- Rationale: why this is the right call
- Impact: which downstream steps are affected
```
Do this BEFORE writing new code or launching the next run. The log exists so the next session understands why the code looks the way it does.

Log observations to `THOUGHT_LOG.md` whenever you notice something interesting — see Best Practices for what qualifies.

**After completing each sub-task (not just each phase):**
- Update `CURRENT_STATE.md` immediately. Granularity: if §10.1 has a checkbox for it, CURRENT_STATE should reflect it.
- Register any results in `results/RESULTS_INDEX.md`

**After completing an entire phase:**
- Complete the session log
- Evaluate milestone checkpoint criteria from §10.2

**CRITICAL:** CURRENT_STATE.md must track at the sub-task level. "Week 2 in progress" is not sufficient — write which specific sub-steps are done (e.g., "sycophancy vector extracted and validated ✓, evil vector extraction in progress, hallucination not started"). If it doesn't reflect reality, the next session will make wrong assumptions.

### 2. Session Check-In Protocol (After Compaction / Context Loss)

If you've been compacted or are starting a new session:

1. **Read `CURRENT_STATE.md`** — this tells you the current phase and status
2. **Read `SCRATCHPAD.md`** — search for the most recent PRE-RUN and POST-RUN checkpoint entries, then read the last 30 lines for any loose observations
3. **Read `DECISIONS.md` (last 30 lines)** — recent decisions
4. **Read the latest session log in `sessions/`** — what happened last session
5. **Check `results/RESULTS_INDEX.md`** — what results exist
6. **Only then** read the relevant proposal sections for the current phase

Do NOT re-read the entire proposal or re-explore the directory. The scaffolding documents exist precisely so you can resume efficiently.

**Compaction awareness:**
- **0-2 compactions:** Normal. Continue working.
- **3-4 compactions:** Finish current sub-task, write detailed notes to SCRATCHPAD, update CURRENT_STATE.
- **5+ compactions:** STOP. Write checkpoint to CURRENT_STATE with exact resumption instructions. The next session picks up from there.

### 3. The Proposal is the Spec

- `persona-circuits-proposal.md` defines WHAT to do, HOW to measure, and WHEN to stop
- The traceability matrix (§5.6) maps every claim to its experiment, metric, and figure
- The figure plan (§8.7) defines what artifacts to produce
- The disconfirmation criteria (§5.4) define when to report failure
- If you need to deviate from the proposal, log the decision in `DECISIONS.md` with rationale

### 4. Execution Order

**§10.1 of the proposal is your authoritative task list.** It contains day-level checkboxes for every phase. Do not invent your own task sequence — follow the checkboxes in order. The summary below is navigation aid only.

```
Week 1:  Infrastructure + Prompt Generation  →  configs validated, prompts/*.jsonl exist
Week 2:  Persona Vector Extraction           →  3 validated persona vectors in W&B
Week 3:  SAE Decomposition                   →  top-100 features per trait, annotated
Week 4-5: Circuit Tracing                    →  candidate circuits with attribution maps
Week 6:  Gemma-2-2B CLT Validation           →  hybrid vs CLT comparison report
Week 7-8: Causal Validation                  →  ablation results, hypothesis verdicts
Week 9-10: Writing                           →  paper draft, figures
```

Each phase has a milestone checkpoint (proposal §10.2) with explicit go/no-go criteria. **Evaluate these explicitly before moving to the next phase — do not self-certify, check the criteria.**

#### Day 1 Starting Protocol

If `CURRENT_STATE.md` does not exist OR says `status: not_started`, this is the first session. Do these in order:

1. If `CURRENT_STATE.md` doesn't exist, create it with `status: not_started` and `phase: Phase 0 — Infrastructure`
2. Read §1 (Executive Summary) and §5.4 (Disconfirmation Criteria) in the proposal
3. Read §8.5 (API Keys) — verify `.env` file exists at `configs/.env` with all required keys
4. Read Appendix G.1 (Modal Secrets Setup) — before running any `modal secret create` commands, first run `modal secret list` to check if secrets already exist. If they do, skip creation and verify the names match what G.1 expects. Only create if missing.
5. Initialize git repo for `persona-circuits/` if not already done (see §6 Infrastructure — Git for commands). Verify the remote is set to `https://github.com/Sohailm25/persona-circuits.git`.
6. Follow §10.1 Week 1 Days 1–2 checklist exactly
7. Create a session log: `sessions/YYYYMMDD-session001.md` from `SESSION_TEMPLATE.md`
8. Update `CURRENT_STATE.md`: set `status: in_progress`, `phase: Phase 0 — Infrastructure`, `last_updated: [now]`

Do not skip step 2. Do not start coding before reading the disconfirmation criteria — you need to know what failure looks like before you run anything.

### 5. Results Protocol

- Every experiment result goes in the appropriate `results/stage*/` directory
- Every result MUST be registered in `results/RESULTS_INDEX.md`
- Every result MUST reference its traceability matrix row (proposal §5.6)
- Report BOTH resample AND mean ablation for all causal claims
- Report effect sizes (Cohen's d + A₁₂) with 95% bootstrapped CIs
- Report concentration metrics (Gini, entropy, top-p mass) for all circuits
- Generate figures as you go (rough in notebooks, finalized in `results/figures/`)

### 7. Implementation Validation

**The core principle:** treat your implementation like a scientific instrument. Before using an instrument to make measurements, you calibrate it with known standards. A script that runs and produces output is not calibrated — it is unchecked. You must independently verify it is computing what you intend, using positive controls, negative controls, and manual spot-checks.

**Never conclude from results until you have verified the implementation that produced them.**

This applies in both directions:
- **Bad result ≠ wrong hypothesis.** You may have a bug that suppresses the effect. Verify implementation before updating your belief about the hypothesis.
- **Good result ≠ correct implementation.** Plausible-looking numbers are exactly what implementation bugs tend to produce. Verify before trusting.

#### Required Checks Per Stage

**Before trusting any stage's output, run ALL of the following:**

**Stage 1 — Persona Vector Extraction:**
- [ ] **Positive control:** manually steer with the extracted vector on 3 known examples. Does behavior shift in the expected direction? If not, the vector is wrong or inverted.
- [ ] **Direction check:** cosine similarity of your extracted vector against a reference direction (if one exists from prior work). A value near 0 or negative is a red flag.
- [ ] **Layer check:** log and verify the exact layer index at extraction time. Confirm it matches `experiment.yaml`.
- [ ] **Prompt audit:** manually read 5 extraction prompt pairs. Do they actually contrast high/low trait? Label errors contaminate everything downstream.

**Stage 2 — SAE Decomposition:**
- [ ] **Hook verification:** print the activations your SAE hook is receiving. Are they non-zero? Are they the correct shape (`[seq_len, d_model]`)? Are they from the expected layer?
- [ ] **Reconstruction sanity:** run `original_acts → encode → decode` and compute cosine similarity to originals. Should be >0.9. If <0.8, the SAE is losing too much information.
- [ ] **Feature activation range:** on a single example, print the top-5 activated features and their activation values. Do the values and feature indices look reasonable (not all identical, not all zero)?
- [ ] **Null check:** on a neutral prompt (unrelated to the trait), confirm top features are different from trait-related features.

**Stage 3 — Attribution / Circuit Tracing:**
- [ ] **Graph non-empty check:** confirm the attribution graph has more than zero edges. An empty graph = bug, not a "diffuse circuit."
- [ ] **Manual ablation spot-check:** take the single highest-attributed feature from the graph. Manually ablate just that feature. Does the model's output on that example shift in the expected direction? If not, the attribution is unreliable.
- [ ] **Negative control:** take a feature with near-zero attribution. Ablate it. Confirm output does NOT change. If it does, your attribution is noisy.

**Stage 4 — Ablation:**
- [ ] **Resample source audit:** print the resampled activation value and confirm it came from a genuinely different input. If it equals the original, your resample is broken.
- [ ] **Coherence check:** after ablation, generate 3 outputs and read them. Is the model still producing coherent language? If not, the ablation is too destructive and your sufficiency metric is meaningless.
- [ ] **Baseline calibration:** run the same ablation on a random feature of the same size. If random ablation produces similar reduction as circuit ablation, your circuit has no selective causal power.
- [ ] **Zero ablation agreement:** run mean and zero ablation on the same features. If they disagree by more than 2×, investigate before trusting either.

**Stage 5 — LLM Judge / Evaluation:**
- [ ] **Prompt template audit:** print the fully-formatted judge prompt for 2 examples (one high-trait, one low-trait). Read it. Does it say what you intended? Is `{ground_truth}` filled in correctly?
- [ ] **Score distribution check:** plot or print the distribution of raw scores from 20 examples. If >20% are exactly 50.0, `parse_score()` is hitting its fallback — the model is not returning parseable numbers.
- [ ] **Manual concordance:** pick 5 examples, score them yourself on the rubric (0–100), then compare to the judge's scores. If mean absolute disagreement is >20 points, the rubric or prompt is broken.
- [ ] **Control test:** run the judge on a clearly non-trait response (e.g., a sycophancy rubric on a factual math answer). Score should be near 0. If it scores high, the rubric is mis-calibrated.

#### General Implementation Checks (Every Stage)

Before any Modal run that produces results you intend to use:
- [ ] Run the script locally on a single example (CPU, no Modal) and verify the output manually
- [ ] Check for silent failures: non-NaN outputs, non-zero metrics, no `except: pass` clauses swallowing errors
- [ ] Verify random seeds are set at the top of every script (`torch.manual_seed`, `random.seed`, `np.random.seed`)
- [ ] Confirm the script reads from the correct artifact version (not an old file with the same name)

#### When to Re-Validate

Re-run these checks if:
- You modify the script between runs
- You change the SAE source or layer
- Results shift significantly from one run to the next with the same config
- You've resumed after a compaction and aren't certain what the last run was

### 6. Infrastructure

- **Compute:** Modal with A100-80GB GPUs. Secrets registered per Appendix G.1.
- **Logging:** W&B project `persona-circuits`, entity `sohailm`. URL: https://wandb.ai/sohailm/persona-circuits
- **Models:** Download to Modal persistent volume `/models` to avoid re-downloading
- **API keys:** In `configs/.env` for local, Modal secrets for remote
- **LLM Judge:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) via Anthropic API. NOT OpenAI.
- **SAE Loading:** See proposal Appendix G.3 for loading patterns per SAE source

#### Git

**Remote:** `https://github.com/Sohailm25/persona-circuits.git`

The `persona-circuits/` workspace has its own dedicated git repo (separate from the parent `braindstorms` repo). On Day 1, initialize it if not already done:
```bash
cd persona-circuits/
git init
git remote add origin https://github.com/Sohailm25/persona-circuits.git
git add .
git commit -m "[week1] initial commit: scaffold and configs"
git push -u origin main
```

- **Commit frequently.** After every completed sub-task, commit all changes: scripts written, results saved, docs updated.
- **Commit message format:** `[phase] [trait/component]: what was done` — e.g., `[week2] sycophancy: extract and validate persona vector, layer 16`
- **Always commit and push before ending a session**, even if mid-task — WIP commits are fine. A stale disk state is not.
- **Commit RESULTS_INDEX.md, CURRENT_STATE.md, SCRATCHPAD.md, DECISIONS.md, and THOUGHT_LOG.md together** with the experiment results they document — they should always be in sync.
- **Do NOT commit** `configs/.env` (already gitignored). Do NOT commit model weights or large activation files that should only live in Modal volumes or W&B artifacts. JSON/CSV/PT result files that are small enough are fine to commit.

---

## Mechanistic Interpretability Watchlist

The full field guidance lives in `background-work/MECH_INTERP_GUIDANCE.md`. This section is the always-visible quick reference — the things you should be actively watching for throughout the experiment.

### Top 10 Gotchas (Memorize These)

1. **Steering coefficients matter a lot** — always sweep α across {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}; never report a single value
2. **Ablation methods inflate importance by ~9×** — resample ablation is primary; mean and zero are secondary (Li & Janson 2024)
3. **Cherry-picking is pervasive** — report failures alongside successes; the denominator matters ("2 of 3 traits worked")
4. **SAE features aren't monosemantic** — check for feature splitting, absorption, polysemanticity; "Feature 42 = sycophancy" means "one subtype"
5. **Circuits are prompt-specific** — validate on held-out prompts; Jaccard < 0.3 means you have noise, not a circuit
6. **Probing ≠ causation** — probe accuracy says the model encodes X; causal intervention says the model uses X; you need both
7. **Random baselines are essential** — your circuit must beat 100+ random same-size ablations (top 1% = p<0.01)
8. **Different SAEs give different features** — cross-check Llama Scope vs. andyrdt; dramatic disagreement = SAE artifact
9. **Auto-interpretations hallucinate** — treat LLM feature labels as hypotheses; validate with held-out stimuli
10. **Log everything** — hyperparams, seeds, exact prompts, negative results; you will forget; W&B is authoritative

### When to Read the Full Guidance

| Trigger | Read This Section |
|---------|------------------|
| Before Week 2 (Extraction) | §2 (Steering Vector Gotchas) — especially §2.1 coefficient sweep and §2.4 prompt contamination |
| Before Week 3 (SAE Decomposition) | §3 (SAE Gotchas) — especially §3.1 reconstruction error and §3.2 feature splitting |
| Before Week 4–5 (Circuit Tracing) | §5 (Circuit Gotchas) — especially §5.1 prompt-specificity and §5.4 attention ≠ importance |
| Before Week 7–8 (Ablation) | §4 (Ablation Gotchas) — especially §4.1 method choice and §4.3 random baseline |
| When a result is unexpected | §8.2 Failure Mode Taxonomy — categorize before changing anything |
| When a result seems too clean | §10.1 Red Flags in Your Own Work |
| Before reporting any result | §12 Sanity Checks + §11 Logging Checklist |
| When stuck for >2 days | §9.4 Know When to Stop |

### Failure Mode Taxonomy (Quick Reference)

When something isn't working, categorize it before changing anything:

| Symptom | Failure Mode | First Action |
|---------|-------------|--------------|
| <10% behavior change at all α values | Weak effect — vector may not capture concept | Try different extraction method; check cosine similarity across methods |
| Works on some prompts, fails on others | Fragile effect — vector is noisy | Check prompt contamination; try larger extraction set |
| High α produces incoherent output | Coherence collapse | Reduce α; try different layer |
| Steering causes opposite behavior | Inverse effect | Check vector sign; re-examine extraction labels |
| No small feature set captures >50% of effect | Diffuse circuit | This IS a valid result — report against §5.4 disconfirmation criteria |
| Different prompts produce different circuits | Unstable circuit | Report Jaccard scores; this may be a real finding about trait nature |

---

## Best Practices

### Thought Log

`THOUGHT_LOG.md` is a running log of anything intellectually interesting that occurs during the experiment. It exists so the paper-writing phase has a rich source of insights, theories, and observations that would otherwise be lost.

**Log to THOUGHT_LOG.md whenever you notice:**
- A result that surprises you, even if it doesn't contradict the hypothesis
- A pattern across traits that wasn't predicted
- A potential confound or alternative explanation you thought of
- Something that reminded you of an adjacent paper or phenomenon
- A "what if we also tested X?" thought (future research directions)
- A fun or counterintuitive observation about model behavior
- A theory about WHY a result is happening (label it as theory, not fact)
- Any result that seems too clean or too noisy and deserves scrutiny

**Do NOT log:**
- Routine status updates (those go in CURRENT_STATE.md or SCRATCHPAD)
- Debugging noise or infrastructure issues (those go in SCRATCHPAD)
- Anything not related to the experiment's goals, hypotheses, or adjacent research questions

**Format:**
```markdown
## [TIMESTAMP] [CATEGORY] — [short title]
**Type:** observation | theory | curiosity | finding | future-direction | action
**Phase:** Week N / Stage N
**Relevance:** [one line: which hypothesis or goal this connects to]

[Free-form note. Can be speculative. Can be a question. Label claims with evidence status.]
```

**Action tagging:** If an entry implies something concrete that must be done before a specific experiment or phase, mark it `**Type: action**` AND add it to the `## PENDING ACTIONS` section at the top of THOUGHT_LOG.md in this format:
```
- [ ] [short description] — see entry [TIMESTAMP] — required before: [Phase/run/event]
```
When the action is resolved, check it off and move it to `## RESOLVED ACTIONS` with a one-line note.

**Frequency:** Log as you work — not just at phase boundaries. A single session should produce multiple entries if the work is interesting. It is better to over-log than to lose an insight.

This file will be directly sourced when writing the paper discussion section and when scoping follow-up research.

### Directory Cleanliness

- **No files in the wrong directory.** Scripts go in `scripts/`, configs in `configs/`, results in `results/stage*/`. If you're about to write a file, check you're putting it in the right place.
- **Name files descriptively.** `results/stage1_extraction/sycophancy_vector_layer16.pt` not `results/output.pt`.
- **No orphan files.** Every file in `results/` must be registered in `RESULTS_INDEX.md`. Every script must be referenced in a session log.
- **Clean up failed experiments.** If a run produces garbage, move artifacts to a `_failed/` subdirectory with a note about why, don't leave them mixed with good results.
- **JSONL for data, JSON for configs, MD for human-readable docs, PT for tensors.** Be consistent.

### Parallel Work

Parallelism is encouraged when tasks are independent. Rules:

- **SAFE to parallelize:** Different traits in the same phase (e.g., extract sycophancy and evil vectors simultaneously). Different analysis scripts that read but don't write shared files.
- **NOT safe to parallelize:** Tasks that write to the same file. Tasks where one depends on the other's output. CURRENT_STATE.md updates (always sequential).
- **Modal parallelism:** Use separate Modal function calls for independent experiments. Each logs to its own W&B run.

### W&B and Modal Logging

- **Every Modal run MUST log to W&B.** No silent runs. If a run doesn't appear in W&B, it didn't happen.
- **Pull results FROM W&B, not from Modal stdout.** W&B is the authoritative record. Modal logs are for debugging.
- **Check Modal logs for errors.** After every run: `modal app logs persona-circuits`. Look for OOMs, timeouts, CUDA errors, and SAE loading failures.
- **W&B artifacts:** Log persona vectors (.pt), feature lists (.json), attribution maps (.json), ablation results (.csv) as W&B artifacts with descriptive names.
- **W&B run naming:** `{phase}-{trait}-{description}` e.g., `extraction-sycophancy-layer-sweep`, `ablation-evil-resample-seed42`.
- **Tag every run** with the relevant hypothesis (h1, h2, etc.) and phase.

### Modal Health Checks

After EVERY Modal experiment run:
1. Check the run completed (not timed out or OOM'd)
2. Check W&B received the logged metrics
3. Check artifact files are non-empty and well-formed
4. If any check fails, investigate before proceeding — do not assume the data is fine

### Data Preservation

**Nothing gets lost. Every artifact is saved locally AND uploaded to W&B.**

#### What to save per stage

| Stage | Required local files | W&B artifact |
|-------|---------------------|--------------|
| Stage 1 (Extraction) | `results/stage1_extraction/{trait}_vector_layer{N}.pt` (persona vector), `{trait}_validation_scores.json` | Artifact: `{trait}-persona-vector` |
| Stage 2 (Decomposition) | `results/stage2_decomposition/{trait}_top100_features.json`, `{trait}_sae_activations.pt` | Artifact: `{trait}-sae-features` |
| Stage 3 (Attribution) | `results/stage3_attribution/{trait}_attribution_graph.json`, `{trait}_edge_weights.csv` | Artifact: `{trait}-attribution-graph` |
| Stage 4 (Ablation) | `results/stage4_ablation/{trait}_ablation_resample.csv`, `{trait}_ablation_mean.csv`, `{trait}_effect_sizes.json` | Artifact: `{trait}-ablation-results` |
| Stage 5 (Cross-persona) | `results/stage5_cross_persona/sharing_matrix.json`, `orthogonality_scores.csv` | Artifact: `cross-persona-sharing` |
| Gemma validation | `results/gemma2b_validation/{trait}_clt_graph.json`, `hybrid_vs_clt_comparison.json` | Artifact: `gemma-clt-validation` |
| Figures | `results/figures/{figure_id}_{description}.pdf` and `.png` | Artifact: `paper-figures` |

#### Retention rules

**Keep everything. No exceptions. Never delete any artifact.**

- **Tensors (.pt):** Keep all. Never delete.
- **Raw activation dumps:** Keep all. Tag with W&B run ID in filename.
- **Intermediate JSONs:** Keep all.
- **Failed run artifacts:** Move to `results/_failed/` with a note — still kept, just separated from good results.
- **Prompts (JSONL):** Never overwrite. If you regenerate, save as `v2_` prefix and keep both versions.

#### RESULTS_INDEX.md format

Every entry must include:
```
| [date] | [stage] | [trait] | [local path] | [W&B run URL] | [W&B artifact name] | [key metric] | [notes] |
```

If you run an experiment and don't update RESULTS_INDEX.md, the result doesn't officially exist.

#### W&B as the authoritative record

- W&B stores the canonical metric values. If W&B and local disagree, trust W&B (it was logged at runtime).
- Every W&B run must have: correct tags (hypothesis ID, phase, trait), the W&B run URL saved to SCRATCHPAD post-run checkpoint.
- Do not delete W&B runs. If a run was bad, tag it `bad-run` and note why — it's still evidence.

---

## What To Do When Things Go Wrong

- **SAE fails to load:** Check SAELens version compatibility. Try `pip install --upgrade sae-lens`. If still failing, log in SCRATCHPAD and try the alternative SAE source (andyrdt for Llama, EleutherAI as last resort).
- **Persona vector doesn't steer:** Check layer selection. Try broader layer sweep. If no layer works for a trait, log as negative result and continue with remaining traits (need ≥2 of 3).
- **Circuit not found (diffuse mechanism):** This IS a valid result. Report it against disconfirmation criteria (§5.4). Update CURRENT_STATE.md with the finding.
- **Ablation breaks the model:** Check if you're ablating too many features. Try graded ablation (25/50/75/100%). If full circuit ablation breaks the model, report fallback claims per §6.5.2.
- **Gemma-2-2B CLT disagrees with hybrid:** Report the discrepancy. This is important methodological evidence. Do NOT discard the Llama 8B results — just note the limitation.
- **Compute budget exceeded:** Prioritize: (1) core 3 traits on Llama, (2) ablation validation, (3) Gemma-2-2B validation. Cut cross-seed replication first if needed.
- **Unexpected result:** Do NOT explain it away. Log the raw observation in SCRATCHPAD. Reproduce it. Then form a hypothesis. The worst thing you can do is rationalize an anomaly.
- **Prompt generation fails (API error, quality check fails):** Do NOT proceed to Week 2 without valid prompts — all downstream stages depend on them. Re-run generation with the same seed. If an API rate limit is hit, wait and retry. If quality checks still fail after two attempts, write the failure details to SCRATCHPAD and set CURRENT_STATE.md to `status: blocked`. See BLOCKED Protocol below.
- **Phase milestone gate FAILS (go/no-go FAIL):** Do not silently proceed to the next phase. Log the specific criteria that failed in CURRENT_STATE.md under `blocking_issues`. Check §11 (Risk Assessment) in the proposal for the relevant contingency. If the contingency resolves the issue, apply it, re-evaluate the gate, and log the decision in DECISIONS.md. If no contingency resolves it, trigger the BLOCKED Protocol.

### BLOCKED Protocol

If you encounter a hard blocker with no recoverable path — infrastructure that cannot be set up, a disconfirmation criterion triggered before you've finished an experiment, a fundamental design flaw, or a phase gate that fails with no viable contingency — **STOP**. Do not continue guessing or trying random fixes.

1. Set `CURRENT_STATE.md` `status: blocked`
2. Write a `BLOCKED.md` file at the root of `persona-circuits/` with:
   - What you were trying to do
   - What failed and what the error was (exact output)
   - What you already tried
   - What you believe the root cause is
   - What decision or information is needed to unblock
3. Commit all current work (see §6 Infrastructure — Git)
4. Stop. The next human session will pick up from BLOCKED.md.

---

## Quality Gates

Before starting any new phase:

- [ ] THOUGHT_LOG.md `## PENDING ACTIONS` section scanned — all open actions either addressed or explicitly deferred with rationale logged in DECISIONS.md
- [ ] CURRENT_STATE.md reflects the transition (previous phase marked complete, new phase marked in_progress)
- [ ] No unresolved BLOCKED.md exists

Before declaring any phase complete:

- [ ] All results registered in RESULTS_INDEX.md
- [ ] CURRENT_STATE.md updated with phase status and any hypothesis updates
- [ ] THOUGHT_LOG.md has entries from this phase — at minimum: one observation and one theory or future-direction
- [ ] Any mid-execution pivots logged to DECISIONS.md
- [ ] Implementation validated for this phase's primary script (positive control, negative control, manual spot-check per §7)
- [ ] Milestone checkpoint criteria from §10.2 evaluated (explicitly, not handwaved)
- [ ] No TODO/PLACEHOLDER/TBD in any result files or documentation (scripts may have implementation TODOs, that's fine)
- [ ] Relevant figures sketched (rough is fine until Week 9)
- [ ] Adversarial self-check: "What could be wrong with these results?" (see MECH_INTERP_GUIDANCE.md §10.1 Red Flags and §12 Sanity Checks)
- [ ] MECH_INTERP_GUIDANCE.md §12 sanity checks run: randomization, generalization, robustness, coherence
- [ ] W&B runs tagged and artifacts uploaded
- [ ] All changes committed and pushed to `https://github.com/Sohailm25/persona-circuits.git`

---

## What NOT To Do

- **Don't modify the proposal** unless recording a decision in DECISIONS.md
- **Don't skip the traceability check** — every experiment maps to a matrix row
- **Don't use OpenAI models** for scoring (use Claude Sonnet 4.6)
- **Don't report single-method ablation** as conclusive (always report resample + mean)
- **Don't cherry-pick prompts** — use the full generated sets
- **Don't leave CURRENT_STATE.md stale**
- **Don't ignore negative results** — they're publishable under the pre-registered disconfirmation criteria
- **Don't trust summaries over raw data** — if a number matters, verify it from the source artifact
- **Don't assume SAE/library APIs haven't changed** — verify loading patterns against current docs
- **Don't proceed past a failed quality gate** — fix the issue first
- **Don't interpret results before verifying the implementation** — a script that runs and produces numbers is not validated; good results and bad results are equally untrustworthy until you have run positive controls, negative controls, and a manual spot-check (§7)
- **Don't conclude the hypothesis is wrong because of bad results** — rule out implementation bugs first
- **Don't conclude the hypothesis is right because of good results** — results that look "exactly right" deserve more scrutiny, not less

---

## Reference Files (Read-Only)

The `background-work/` directory contains the research context that informed the proposal.

| File | Use it when... |
|------|----------------|
| `REFERENCES.md` | You need to find a cited paper — index with URLs, priority tiers, and when-to-consult guidance. **Start here.** |
| `papers/*.md` | You need to READ a paper. 23 papers are downloaded locally. Grep across all: `grep -r "keyword" background-work/papers/`. See `papers/DOWNLOAD_MANIFEST.md` for index. **Prefer this over fetching URLs.** |
| `MECH_INTERP_GUIDANCE.md` | Hit an unexpected result, a gotcha, or starting a new phase. Contains Top 10 Gotchas, failure mode taxonomy, sanity checklists, and red flags. |
| `GAPS_SYNTHESIS.md` | You need to understand WHY a design choice was made — it documents resolved disagreements across sources |
| `RESEARCH_POSITIONING.md` | You need to understand how this work fits in the field — useful for writing intro/related work |
| `persona-vectors/anthropic.md` | You need deep context on steering vectors, persona vectors, SAE monitoring, or adversarial robustness |
| `circuit-tracing/anthropic.md` | You need deep context on circuit tracing, attribution graphs, or deception detection methods |
| `closing-gaps/psm-analysis.md` | You need PSM-specific weaknesses or limitations analysis |

**CAUTION:** `background-work/closing-gaps/gemini.md` contains unreliable CLT infrastructure claims. Do NOT trust its claims about which models have pre-trained CLTs.

---

## Success Definition

The experiment succeeds if:
1. At least 2 of 3 traits have validated persona vectors (Week 2 gate)
2. At least 1 trait passes all 6 circuit criteria (Week 8 gate)
3. All hypotheses are evaluated against pre-registered thresholds
4. All planned figures and tables are produced
5. Results are sufficient to write a paper (positive OR negative)

A negative result (PSM mechanistic predictions unsupported) is a valid, publishable outcome. Do not contort the analysis to avoid it.
