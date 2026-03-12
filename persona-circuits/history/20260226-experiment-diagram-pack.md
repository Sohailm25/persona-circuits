# Persona Circuits Experiment Diagram Pack

**As of:** 2026-02-26T08:21:42-0600 (local) / 2026-02-26T14:21:42Z (UTC)

## Evidence Legend

- `known`: directly verified in local artifacts/docs
- `observed`: directly observed from live command output in this session
- `inferred`: derived from known/observed evidence
- `unknown`: not currently evidenced

---

## 1) Mission, Hypotheses, and Disconfirmation Map

```mermaid
flowchart TB
    M["Mission: Mechanistically ground Persona Selection Model (PSM)"]

    M --> H1["H1 Coherence"]
    M --> H2["H2 Necessity"]
    M --> H3["H3 Sufficiency"]
    M --> H4["H4 Cross-persona structure"]
    M --> H5["H5 Router existence"]

    H1 --> H1S["Success: Top-20 >50%, Gini >0.5"]
    H1 --> H1F["Disconfirm: no <20% subset gets >50% necessity across >=2 traits"]

    H2 --> H2S["Success: >80% steering reduction, p<0.01 vs random"]
    H2 --> H2F["Disconfirm: <30% avg reduction or random comparable"]

    H3 --> H3S["Success: circuit-only preserves >60%"]
    H3 --> H3F["Disconfirm: <40% across >=2 traits"]

    H4 --> H4S["Success: early-layer overlap > late-layer overlap"]
    H4 --> H4F["Disconfirm: no early->late Jaccard gradient"]

    H5 --> H5S["Success: routing features found; ablation blocks propagation"]
    H5 --> H5F["Disconfirm: no routing set while preserving >90% competence"]
```

---

## 2) End-to-End Technical Architecture

```mermaid
flowchart LR
    subgraph Inputs["Prompt/Data Inputs"]
      P1["Extraction pairs (100/trait)"]
      P2["Held-out behavioral prompts"]
      P3["Extraction-free rotating eval sets"]
    end

    subgraph ModelStack["Model + SAE Stack"]
      L["Llama-3.1-8B-Instruct (32 layers)"]
      ST["Steering injection layers 11-16, alpha 0.5..3.0"]
      S1["LlamaScope SAEs (12,14,16,18,20,22,24)"]
      S2["andyrdt SAE cross-check (11,15,19,23)"]
      J["Judge: Claude Sonnet 4.6 (+ cross-rater protocol)"]
    end

    subgraph Pipeline["Analysis Pipeline"]
      A1["Stage 1: vector extraction + behavioral validation"]
      A2["Stage 2: decomposition (projection + differential activation)"]
      A3["Stage 3: attribution graph + candidate circuits"]
      A4["Stage 4: causal tests (resample/mean/zero + random baseline)"]
      A5["Stage 5: cross-persona overlap + router search"]
      G["Gemma-2-2B CLT lane for hybrid-vs-CLT validation"]
    end

    subgraph Ops["Ops + Artifacts"]
      M["Modal A100 jobs"]
      W["W&B logging"]
      R["results/stage* artifacts"]
      Q["Pre-registered thresholds + disconfirmation gates"]
    end

    P1 --> A1
    P2 --> A1
    P3 --> A1

    A1 --> ST --> L
    L --> S1 --> A2
    L --> S2 --> A2
    L --> J --> A1

    A2 --> A3 --> A4 --> A5
    A3 --> G
    A4 --> G

    A1 --> W
    A2 --> W
    A3 --> W
    A4 --> W
    A5 --> W
    W --> R
    M --> A1
    M --> A2
    M --> A3
    M --> A4
    M --> G
    Q --> A1
    Q --> A2
    Q --> A3
    Q --> A4
    Q --> A5
```

---

## 3) Program Execution Flow and Go/No-Go Gates

```mermaid
flowchart TD
    W1["Week 1 Infrastructure\nStatus: PASS (known)"]
    G1{"Milestone: Infrastructure ready?"}
    W2["Week 2 Persona Extraction\nStatus: IN PROGRESS (known)"]
    G2{"Milestone: >=2 traits validated steering?"}
    W3["Week 3 SAE Decomposition"]
    G3{"Milestone: interpretable feature sets?"}
    W45["Week 4-5 Circuit Tracing"]
    G4{"Milestone: candidate circuits for >=2 traits?"}
    W6["Week 6 Gemma CLT Validation"]
    W78["Week 7-8 Causal Validation"]
    W910["Week 9-10 Writing"]

    W1 --> G1
    G1 -- yes --> W2
    W2 --> G2
    G2 -- yes --> W3
    G2 -- no (current) --> R2["Remediate Week 2 closeout:\nartifact ingestion + concordance + reruns if needed"]
    R2 --> W2
    W3 --> G3
    G3 -- yes --> W45
    W45 --> G4
    G4 -- yes --> W6 --> W78 --> W910
```

---

## 4) Current Stage Snapshot (Evidence-Tagged)

```mermaid
flowchart LR
    subgraph S1["Stage 1 / Week 2"]
      S1A["Vectors extracted for 3 traits\nknown"]
      S1B["Behavioral closeout not complete\nknown"]
      S1C["Sycophancy upgraded artifact available\nknown"]
      S1D["Evil + Hallucination upgraded primary JSON missing locally\nknown"]
      S1E["Timeout/cancellation pattern likely in primary tranche\ninferred"]
    end

    subgraph S2["Stage 2 Readiness"]
      S2A["Token-level reconstruction gate: pass\nknown"]
      S2B["Hook-integrity gate: pass\nknown"]
      S2C["Cross-source overlap precondition: pass (layers 11,15)\nknown"]
      S2D["Multi-seed reconstruction rerun still pending\nknown"]
    end

    subgraph S34["Stage 3/4"]
      S3A["Attribution/ablation scaffold artifact exists\nknown"]
      S3B["No real attribution/ablation causal runs yet\nunknown"]
    end

    S1A --> S1B --> S1C --> S1D --> S1E --> S2A --> S2B --> S2C --> S2D --> S3A --> S3B
```

---

## 5) Trait-Level Evidence Matrix (ASCII)

```text
+---------------------------+------------------------------+----------------------------------------+---------------------------------------------+------------------------------------+
| Trait axis                | Vector extraction            | Behavioral closeout state              | Extraction-free overlap (reanalysis)         | Week 3 candidacy stance            |
+---------------------------+------------------------------+----------------------------------------+---------------------------------------------+------------------------------------+
| sycophancy                | Extracted (known)            | Available upgraded artifact fails gates | weak positive overlap; sign-test strong      | candidate, pending Week2 closeout  |
|                           |                              | in preflight ingestion (known)          | (known)                                      |                                    |
+---------------------------+------------------------------+----------------------------------------+---------------------------------------------+------------------------------------+
| evil -> machiavellian     | Extracted (known)            | final primary upgraded artifact missing | moderate positive overlap; sign-test strong  | reframed candidate axis (inferred) |
| disposition framing       |                              | locally (known)                         | (known)                                      | harmful-content framing disconfirmed|
+---------------------------+------------------------------+----------------------------------------+---------------------------------------------+------------------------------------+
| hallucination             | Extracted (known)            | final primary upgraded artifact missing | null overlap; fails overlap-gradient policy  | control/instruction-dynamics lane  |
|                           |                              | locally (known)                         | (known)                                      | unless rerun changes evidence      |
+---------------------------+------------------------------+----------------------------------------+---------------------------------------------+------------------------------------+
```

---

## 6) Claim-to-Experiment Traceability Skeleton

```mermaid
flowchart LR
    C1["PSM claim: persona traits causally mediate behavior"] --> H2["H2 Necessity"]
    H2 --> E1["Stage 4 forward ablation + random baseline"]
    E1 --> F1["Fig 4 (necessity), Fig 5 (bidirectional)"]

    C2["PSM claim: coherent persona representation"] --> H1["H1 Coherence"]
    H1 --> E2["Stage 2 decomposition + concentration metrics"]
    E2 --> F2["Fig 2 + Table 3"]

    C3["PSM claim: shared structure + router"] --> H4["H4 overlap"] 
    C3 --> H5["H5 router"]
    H4 --> E3["Stage 5 layer-wise Jaccard"]
    H5 --> E4["Stage 5 router candidate tests + ablation"]
    E3 --> F3["Fig 6"]
    E4 --> F4["Fig 7"]

    M1["Method claim: persona vectors steer behavior"] --> E0["Stage 1 behavioral validation"]
    E0 --> F0["Fig 1 dose-response"]
```

---

## 7) Current Critical Path (ASCII)

```text
[NOW] Week 2 closeout incomplete
  |
  +--> Confirm final trait artifacts exist locally for sycophancy/evil/hallucination
  |
  +--> Run deterministic ingestion with explicit trait->artifact map
  |
  +--> Manual 5-example judge concordance spot-check
  |
  +--> Re-run prelaunch gap checks on selected combos
  |
  +--> If >=2 traits pass Week2 validation gates -> unlock Week3 decomposition claims
  |
  '--> Otherwise: timeout-aware partitioned reruns + progress logging, then re-evaluate
```

---

## 8) Live Status Note (Command-Time Snapshot)

```text
2026-02-26T08:21:42-0600:
- modal app list --json returned no currently listed persona-circuits week2 apps (observed)
- local results directory still has only two upgraded sycophancy JSON files and no upgraded evil/hallucination JSON files (known)
- therefore Week2 primary closeout remains non-claimable until deterministic ingestion over complete trait artifacts (inferred)
```

