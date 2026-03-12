REVIEWER 1:
Findings (Ordered by Severity)

  1. Critical: Stage 2 readiness is currently at high risk of false-positive “pass.”
     Known: your Stage 2 audit passes with a permissive token gate (cos>=0.75, EV>=0.50) and does not require multi-seed completion.
     Evidence: week3_sae_reconstruction_audit.py:192, week3_sae_reconstruction_audit_20260225T181955Z.json:61,
     week3_sae_reconstruction_audit_20260225T181955Z.json:120.
     Known: this gate is being evaluated on layer=16 by default and a tiny probe (n_probe_rows=6, seed 42), while Week 2 selected hallucination at layer 13
     and your primary SAE layer list excludes 13.
     Evidence: week3_sae_reconstruction_root_cause.py:431, week3_sae_reconstruction_root_cause_20260225T170255Z.json:14, configs/experiment.yaml:21,
     CURRENT_STATE.md:55.
     Inferred: Stage 2 “ready” can be declared before validating the actual Week 2-selected trait-layer regime.
  2. High: Stage 1 extraction likely targets the wrong activation position for robustness.
     Known: extraction is from the last prompt token.
     Evidence: week2_extract_persona_vectors.py:269, persona-circuits-proposal.md:659.
     Known: your own A/B robustness checks show low prompt-vs-response cosine for all traits (~0.376–0.406, below 0.7).
     Evidence: week2_prelaunch_gap_checks_20260227T205237Z.json:33, week2_prelaunch_gap_checks_20260227T205237Z.json:45,
     week2_prelaunch_gap_checks_20260227T205237Z.json:57.
     Paper alignment: Chen reports response tokens gave more effective steering directions.
     Evidence: chen2025_persona_vectors.md:399.
  3. High: Alpha selection is effect-maximizing, not “working-alpha” constrained.
     Known: combo ranking uses bidirectional effect (plus mild alpha penalty), without coherence/capability/specificity in the selection objective.
     Evidence: week2_behavioral_validation_upgrade.py:558, week2_behavioral_validation_upgrade.py:1642.
     Known: coherence gate then fails due absolute threshold 75 even when steered coherence is not worse than baseline (e.g., sycophancy 68.15 -> 68.55).
     Evidence: week2_behavioral_validation_upgrade_sycophancy_20260227T191157Z.json:6554,
     week2_behavioral_validation_upgrade_sycophancy_20260227T191157Z.json:6559, week2_behavioral_validation_upgrade.py:2278.
     Paper alignment: both Chen and Rimsky note quality/capability degradation at larger coefficients and the need to balance coefficient choice.
     Evidence: chen2025_persona_vectors.md:834, rimsky2024_contrastive_activation_addition.md:198.
  4. High: Governance criteria have drifted beyond prereg/proposal Week 2 definition.
     Known: proposal Week 2 milestone is “continue if >=2 traits have validated steering.”
     Evidence: persona-circuits-proposal.md:1503.
     Known: ingestion shows section623 pass for sycophancy and evil, while runner overall fails due stricter added gates (coherence/cross-bleed/etc.), and
     NO-GO is based on these stricter criteria.
     Evidence: week2_primary_postrun_ingestion_20260227T202336Z.json:62, week2_primary_postrun_ingestion_20260227T202336Z.json:126, DECISIONS.md:554.
     Inferred: this is methodologically defensible only if re-preregistered clearly; otherwise it risks moving-goalpost interpretation.
  5. Medium: Evil trait failure looks more like construct mismatch than judge failure.
     Known: evil external transfer still fails directional reversal (baseline_vs_minus < 0) despite large plus_vs_minus.
     Evidence: week2_prelaunch_gap_checks_20260227T205237Z.json:94, week2_prelaunch_gap_checks_20260227T205237Z.json:95.
     Paper alignment: Chen explicitly warns trait inducibility assumptions can fail on safety-hardened models and coarse trait definitions can miss fine-
     grained distinctions.
     Evidence: chen2025_persona_vectors.md:1177.
  6. Medium: Cross-trait bleed threshold may be over-tight for realistic personality geometry.
     Known: sycophancy fails bleed gate at ratio 0.3165 vs max 0.3.
     Evidence: week2_behavioral_validation_upgrade_sycophancy_20260227T191157Z.json:7360, week2_behavioral_validation_upgrade.py:3143.
     Paper alignment: Bhandari finds persistent cross-trait interference even under orthonormalization and notes quality-control tradeoff when forcing
     independence.
     Evidence: bhandari2026_trait_interference.md:29, bhandari2026_trait_interference.md:137, bhandari2026_trait_interference.md:149.

  Where You’re At (Concise)

  - Known: Week 2 primary runs are complete and ingested; NO-GO for replication/stress is active.
    Evidence: CURRENT_STATE.md:149, DECISIONS.md:554.
  - Known: Bottleneck has shifted from judge parsing/reliability to representation robustness (A/B method sensitivity + evil reversal instability).
    Evidence: CURRENT_STATE.md:157, week2_prelaunch_gap_checks_20260227T205237Z.json:318.

  What Remains

  - Define minimal Week 2 remediation tranche and keep replication/stress blocked until superseding decision.
    Evidence: CURRENT_STATE.md:192.
  - Complete unresolved Week 2 checklist items (validated vectors, coefficient finalization, full W&B closeout) under whichever gate policy you formally
    lock.
    Evidence: CURRENT_STATE.md:46, CURRENT_STATE.md:60.
  - Start Stage 2+ only after resolving the Stage 2 gate integrity issue above.
    Evidence: CURRENT_STATE.md:218.

  Most Beneficial Next Moves

  1. Re-run extraction robustness with response-token extraction as primary and prompt-token as secondary control.
  2. Change alpha selection to constrained optimization (effect >= threshold AND quality/capability/specificity pass), then pick smallest passing alpha.
  3. Rebuild Stage 2 readiness gate around selected trait layers (including hallucination lane), multi-seed, and stricter reconstruction criterion
     alignment.
  4. Freeze and log a single authoritative Week 2 gate set before remediation reruns to avoid criterion drift.
  5. Split evil into two explicit lanes (harmful-content vs machiavellian disposition) and gate them separately.
