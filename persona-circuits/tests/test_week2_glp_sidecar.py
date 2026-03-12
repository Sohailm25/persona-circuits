"""Unit tests for Week 2 GLP sidecar helper logic."""

from __future__ import annotations

import unittest

from scripts.week2_glp_sidecar_validation import (
    _extract_behavioral_source_settings,
    _parse_artifact_map,
    _parse_traits,
    _row_record_aliases,
    _resolve_alpha,
    _resolve_generation_settings,
    _safe_delta,
    _simple_capability_match,
    _summarize_draw_distribution,
    _summarize_condition_records,
)


class Week2GLPSidecarHelperTests(unittest.TestCase):
    def test_parse_traits_and_artifact_map(self) -> None:
        self.assertEqual(_parse_traits("sycophancy, evil"), ["sycophancy", "evil"])
        mapping = _parse_artifact_map("sycophancy:results/a.json,evil:results/b.json")
        self.assertEqual(mapping["sycophancy"], "results/a.json")
        self.assertEqual(mapping["evil"], "results/b.json")

    def test_extract_behavioral_source_settings_supports_trait_map_and_direct_payload(self) -> None:
        mapped = _extract_behavioral_source_settings(
            payload={
                "traits": {
                    "sycophancy": {
                        "selected": {"layer": 12, "alpha": 2.0},
                    }
                },
                "run_metadata": {
                    "judge_models": {"primary": "claude-sonnet-4-6"},
                    "max_new_tokens": 96,
                    "temperature": 0.0,
                },
            },
            trait="sycophancy",
            source_artifact_path="mapped.json",
        )
        self.assertEqual(mapped["layer"], 12)
        self.assertEqual(mapped["alpha"], 2.0)
        self.assertEqual(mapped["judge_model"], "claude-sonnet-4-6")

        direct = _extract_behavioral_source_settings(
            payload={
                "trait": "evil",
                "selected": {"layer": 11, "alpha": 3.0},
                "run_metadata": {},
            },
            trait="evil",
            source_artifact_path="direct.json",
        )
        self.assertEqual(direct["layer"], 11)
        self.assertEqual(direct["alpha"], 3.0)

    def test_capability_match_and_safe_delta(self) -> None:
        self.assertTrue(_simple_capability_match("The answer is Tokyo.", ["tokyo"]))
        self.assertFalse(_simple_capability_match("The answer is Kyoto.", ["tokyo"]))
        self.assertEqual(_safe_delta(2.0, 1.5), 0.5)
        self.assertIsNone(_safe_delta(None, 1.0))

    def test_resolve_generation_settings_allows_smoke_override(self) -> None:
        max_new_tokens, temperature = _resolve_generation_settings(
            source={"max_new_tokens": 96, "temperature": 0.0},
            sidecar_cfg={"max_new_tokens": 48, "temperature": 0.3},
            max_new_tokens_override=8,
        )
        self.assertEqual(max_new_tokens, 8)
        self.assertEqual(temperature, 0.0)

    def test_resolve_alpha_allows_override(self) -> None:
        self.assertEqual(
            _resolve_alpha(source={"alpha": 2.0}, alpha_override=3.5),
            3.5,
        )
        self.assertEqual(
            _resolve_alpha(source={"alpha": 2.0}, alpha_override=None),
            2.0,
        )

    def test_summarize_condition_records(self) -> None:
        records = [
            {
                "trait_plus_score": 80.0,
                "trait_minus_score": 30.0,
                "coherence_plus_score": 70.0,
                "coherence_minus_score": 68.0,
                "geometry_events": [{"edit_norm": 1.0, "repair_to_edit_ratio": 0.1}],
                "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.2}],
                "bleed_scores": {"evil": [10.0, 12.0]},
                "neutral_trait_shift_abs": 2.0,
                "capability_correct_fraction": 1.0,
            },
            {
                "trait_plus_score": 82.0,
                "trait_minus_score": 28.0,
                "coherence_plus_score": 71.0,
                "coherence_minus_score": 69.0,
                "geometry_events": [{"edit_norm": 2.0, "repair_to_edit_ratio": 0.2}],
                "next_token_loss_events": [{"delta_target_nll_vs_clean": 0.4}],
                "bleed_scores": {"evil": [11.0, 13.0]},
                "neutral_trait_shift_abs": 3.0,
                "capability_correct_fraction": 0.75,
                "conditioning_regime": "clean_condition_edited_target",
            },
        ]
        summary = _summarize_condition_records(records=records, comparison_baseline=None)
        self.assertEqual(summary["n_rows"], 2)
        self.assertAlmostEqual(summary["bidirectional_effect_mean"], 52.0)
        self.assertAlmostEqual(summary["coherence_mean"], 69.5)
        self.assertAlmostEqual(summary["bleed_by_trait_mean"]["evil"], 11.5)
        self.assertAlmostEqual(summary["neutral_trait_shift_abs_mean"], 2.5)
        self.assertAlmostEqual(summary["capability_correct_fraction_mean"], 0.875)
        self.assertEqual(summary["geometry_summary"]["edit_norm"]["n"], 2)
        self.assertEqual(summary["next_token_loss_summary"]["delta_target_nll_vs_clean"]["n"], 2)
        self.assertAlmostEqual(summary["next_token_loss_summary"]["delta_target_nll_vs_clean"]["mean"], 0.3)
        self.assertEqual(
            summary["conditioning_regime_counts"],
            {"clean_condition_edited_target": 1},
        )

    def test_summarize_draw_distribution(self) -> None:
        distribution = _summarize_draw_distribution(
            [
                {
                    "bidirectional_effect_mean": -40.0,
                    "coherence_mean": 25.0,
                    "neutral_trait_shift_abs_mean": 4.0,
                    "capability_correct_fraction_mean": 1.0,
                    "geometry_summary": {"repair_to_edit_ratio": {"mean": 1.5}},
                    "next_token_loss_summary": {"delta_target_nll_vs_clean": {"mean": 0.2}},
                },
                {
                    "bidirectional_effect_mean": -20.0,
                    "coherence_mean": 35.0,
                    "neutral_trait_shift_abs_mean": 6.0,
                    "capability_correct_fraction_mean": 0.5,
                    "geometry_summary": {"repair_to_edit_ratio": {"mean": 2.5}},
                    "next_token_loss_summary": {"delta_target_nll_vs_clean": {"mean": 0.6}},
                },
            ]
        )
        self.assertEqual(distribution["bidirectional_effect_mean"]["n"], 2)
        self.assertAlmostEqual(distribution["coherence_mean"]["mean"], 30.0)
        self.assertAlmostEqual(distribution["repair_to_edit_ratio_mean"]["median"], 2.0)

    def test_row_record_aliases_expose_discoverable_schema(self) -> None:
        aliases = _row_record_aliases(
            family_records={"selected_raw": [{"row_id": "a"}]},
            random_family_records_by_draw={0: [{"row_id": "r0"}], 2: [{"row_id": "r2"}]},
        )
        self.assertEqual(aliases["row_record_schema_version"], 1)
        self.assertEqual(aliases["row_records_by_family"]["selected_raw"][0]["row_id"], "a")
        self.assertEqual(
            aliases["random_glp_draw_row_records"],
            {"0": [{"row_id": "r0"}], "2": [{"row_id": "r2"}]},
        )


if __name__ == "__main__":
    unittest.main()
