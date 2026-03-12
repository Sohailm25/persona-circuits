# Reviewer 1 — Second Pass (Verbatim)

Source: user-provided reviewer text on 2026-03-03.

• Findings (ordered by severity)

1. critical known: Stage 2 cross-SAE readiness is structurally blocked under current claim-layer
   policy.
   Evidence: claim layers are fixed to 12 for both active claim traits in
   week2_trait_scope_resolution_20260301T030203Z.json:64, while cross-check SAE layers are
   [11,15,19,23] in experiment.yaml:26; audit explicitly shows no overlap and gate fail in
   week3_sae_reconstruction_audit_20260301T033046Z.json:203 and
   week3_sae_reconstruction_audit_20260301T033046Z.json:236. Gate logic requires overlap in
   week3_sae_reconstruction_audit.py:348.
   Paper alignment: SAE quality should be judged by L0/EV/Delta-LM-loss in he2024_llama_scope.md:456,
   and base->instruct transfer is empirical/conditional, not guaranteed by declaration in
   he2024_llama_scope.md:627.
   Reasoning (inferred): without policy or layer/source change, this gate cannot pass.
2. critical known: “Seed replication resolved” currently overstates robustness relative to proposal
   intent.
   Evidence: run is prompt_last with temperature 0.0 in
   week2_extraction_seed_replication_20260302T180612Z.json:17 and
   week2_extraction_seed_replication_20260302T180612Z.json:19; script reuses one loaded prompt set
   and only swaps seed in week2_extraction_seed_replication.py:115 and
   week2_extraction_seed_replication.py:125; prompt_last path has no generation sampling in
   week2_extract_persona_vectors.py:285.
   Spec misalignment: proposal cross-seed requires different prompt orderings and sampling
   temperatures in persona-circuits-proposal.md:1041.
   Reasoning (inferred): current result mostly demonstrates deterministic extraction under fixed
   inputs, not full stochastic robustness.
3. critical known: Extraction A/B remains failed, and current diagnostic design still confounds
   position with generation-phase effects.
   Evidence: method cosine fails for all traits in
   week2_prelaunch_gap_checks_20260227T205237Z.json:33,
   week2_prelaunch_gap_checks_20260227T205237Z.json:45,
   week2_prelaunch_gap_checks_20260227T205237Z.json:57; comparison script uses prompt-cache for
   prompt_last vs generated continuations for response methods in
   week2_extraction_position_ablation.py:166 and week2_extraction_position_ablation.py:182.
   Paper alignment: response-token extraction outperforming prompt-token extraction is expected in
   chen2025_persona_vectors.md:2111 and chen2025_persona_vectors.md:399.
   Reasoning (inferred): the diagnostic does not yet isolate whether failure is true instability or
   method-definition mismatch.
4. high known: Coherence is still the dominant Week 2 blocker after WS-F.
   Evidence: both rollout5 trait runs fail coherence_pass and overall_pass in
   week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json:4027,
   week2_behavioral_validation_upgrade_evil_20260303T081318Z.json:4027, and remains failed in
   rollout3/5 comparison at week2_rollout_stability_sensitivity_20260303T121253Z.json:205 and
   week2_rollout_stability_sensitivity_20260303T121253Z.json:427.
   Paper alignment: higher steering strength can degrade quality/capability in
   chen2025_persona_vectors.md:834, chen2025_persona_vectors.md:839,
   rimsky2024_contrastive_activation_addition.md:198, turner2024_activation_addition.md:879.
   Reasoning (inferred): alpha reduction alone is insufficient; intervention placement/magnitude
   calibration remains unresolved.
5. high known: Capability evidence is currently narrower than reviewer concern R2-G8 and later-stage
   claim needs.
   Evidence: capability proxy is MMLU-only sampled at min(30, len(mmlu)) in
   week2_behavioral_validation_upgrade.py:2507 and week2_behavioral_validation_upgrade.py:2509,
   reflected in artifact n_questions=30 at
   week2_behavioral_validation_upgrade_sycophancy_20260303T082321Z.json:4003; checklist still marks
   capability suite pending in 20260227-reviewer-reconciliation-checklist-v1.md:45.
   Spec/paper alignment: Week 2 criterion does allow MMLU drop gate in persona-circuits-
   proposal.md:688, but broader unrelated-task suite is defined in persona-circuits-proposal.md:1103.
   Chen also uses coherence + MMLU as dual quality lens in chen2025_persona_vectors.md:834.
   Reasoning (inferred): current proxy is acceptable for interim Week 2 gating, not sufficient for
   stronger capability-preservation claims.
6. medium known: Rollout sensitivity artifact carries null metric fields due schema mismatch.
   Evidence: comparator requests plus_mean/minus_mean in week2_rollout_stability_sensitivity.py:27,
   but source metric schema excludes those fields in week2_behavioral_validation_upgrade.py:195;
   output is null in week2_rollout_stability_sensitivity_20260303T121253Z.json:189 and
   week2_rollout_stability_sensitivity_20260303T121253Z.json:411.
   Reasoning (inferred): this is a reporting-quality bug, not a scientific blocker, but it weakens
   WS-F interpretability.
7. medium known: Cross-trait bleed threshold sensitivity is still an open methodological gap.
   Evidence: explicitly pending in 20260227-reviewer-reconciliation-checklist-v1.md:26; gate is
   currently fixed-ratio in week2_behavioral_validation_upgrade.py:2480 with default 0.3 at
   week2_behavioral_validation_upgrade.py:3238.
   Paper alignment: cross-trait interference can persist despite geometric disentanglement in
   bhandari2026_trait_interference.md:137 and bhandari2026_trait_interference.md:139.
   Reasoning (inferred): a single threshold without sensitivity analysis is fragile.
8. medium known: Manual concordance remains low-power for final trust calibration.
   Evidence: only 5 examples/trait, 15 total in
   week2_primary_manual_concordance_ratings_20260227T202822Z.json:4 and
   week2_primary_manual_concordance_ratings_20260227T202822Z.json:213; reviewer item still pending in
   20260227-reviewer-reconciliation-checklist-v1.md:36.
   Paper alignment: Chen’s human-check scale is 50 pairs/trait and 300 judgments in
   chen2025_persona_vectors.md:2192 and chen2025_persona_vectors.md:2200.
   Reasoning (inferred): current concordance is directionally useful, not strong enough to close
   calibration skepticism.

———

known ground-truth reconciliation: Week 2 is still active and blocked, NO-GO is reaffirmed, Stage 2
claim readiness is failed, and Stage 3/4 are scaffold-only in CURRENT_STATE.md:6,
CURRENT_STATE.md:270, DECISIONS.md:833, CURRENT_STATE.md:290, RESULTS_INDEX.md:115,
RESULTS_INDEX.md:121.

What remains most important to do next (frozen-policy tranche)

1. Reclassify seed-replication evidence as robustness-partial unless rerun includes per-seed prompt-
   order perturbation and nonzero sampling variation per proposal.
2. Run a factorial A/B closure experiment that isolates token-position from generation-phase effects
   before declaring extraction-method root cause closed.
3. Resolve Stage 2 policy contradiction explicitly: either move claim layer to overlap-capable layers
   or scope down cross-source claim requirements.
4. Add capability-suite spec artifact (and implementation) that states what is Week 2 gate vs what is
   later-stage capability claim support.
5. Patch rollout-sensitivity schema to drop or compute plus_mean/minus_mean, and add tests that fail
   on missing metric keys.
6. Close the three pending reviewer items (R1-F6, R2-C5, R2-G8) before any superseding launch
   decision.

No files were edited in this review pass.
