"""Unit tests for Week 2 behavioral validation and gap-check helper logic."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import torch

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from week2_behavioral_validation_upgrade import (
    SweepMetric,
    _extract_score_json as parse_upgrade_json,
)
from week2_behavioral_validation_upgrade import _pick_top_combos, _split_rows
from week2_behavioral_validation_upgrade import (
    _alpha_grid_from_config,
    _apply_steering_direction,
    _build_coherence_summary,
    _combo_selection_policy_from_config,
    _coherence_gate_mode_from_config,
    _combo_key,
    _compute_retry_sleep_seconds,
    _decode_int_key_dict,
    _encode_int_key_dict,
    _extract_retry_after_seconds,
    _hook_name_for_layer,
    _normalize_csv_floats,
    _normalize_csv_ints,
    _judge_prompt,
    _resolve_checkpoint_key,
    _select_confirm_combo,
)
from week2_prelaunch_gap_checks import _extract_score_json as parse_gap_json
from week2_prelaunch_gap_checks import _parse_trait_combos


class Week2ValidationUtilsTests(unittest.TestCase):
    def test_extract_score_json_accepts_plain_and_fenced_json(self) -> None:
        score_plain, ok_plain = parse_upgrade_json('{"score": 87}')
        score_fenced, ok_fenced = parse_upgrade_json("```json\n{\"score\": 42}\n```")

        self.assertTrue(ok_plain)
        self.assertEqual(score_plain, 87.0)
        self.assertTrue(ok_fenced)
        self.assertEqual(score_fenced, 42.0)

    def test_extract_score_json_rejects_invalid_schema(self) -> None:
        score_extra, ok_extra = parse_upgrade_json('{"score": 50, "note": "extra"}')
        score_text, ok_text = parse_upgrade_json("score: 50")

        self.assertFalse(ok_extra)
        self.assertIsNone(score_extra)
        self.assertFalse(ok_text)
        self.assertIsNone(score_text)

    def test_upgrade_judge_prompt_supports_trait_lane_rubric(self) -> None:
        prompt = _judge_prompt("politeness", "q", "r", "N/A")
        self.assertIn("politeness", prompt.lower())

    def test_gap_and_upgrade_score_parsers_match_on_valid_input(self) -> None:
        raw = '{"score": 33}'
        up_score, up_ok = parse_upgrade_json(raw)
        gap_score, gap_ok = parse_gap_json(raw)

        self.assertTrue(up_ok)
        self.assertTrue(gap_ok)
        self.assertEqual(up_score, gap_score)

    def test_pick_top_combos_prefers_feasible_bidirectional(self) -> None:
        metrics = [
            SweepMetric(
                layer=15,
                alpha=1.5,
                steering_shift_mean=1.2,
                steering_shift_std=0.1,
                reversal_shift_mean=1.0,
                reversal_shift_std=0.1,
                bidirectional_effect=2.2,
                n_prompts=15,
            ),
            SweepMetric(
                layer=16,
                alpha=1.5,
                steering_shift_mean=2.5,
                steering_shift_std=0.1,
                reversal_shift_mean=-0.1,
                reversal_shift_std=0.1,
                bidirectional_effect=2.4,
                n_prompts=15,
            ),
            SweepMetric(
                layer=14,
                alpha=2.0,
                steering_shift_mean=0.9,
                steering_shift_std=0.1,
                reversal_shift_mean=0.8,
                reversal_shift_std=0.1,
                bidirectional_effect=1.7,
                n_prompts=15,
            ),
        ]

        top = _pick_top_combos(metrics, top_k=2)
        self.assertEqual(top[0].layer, 15)
        self.assertEqual(top[1].layer, 14)

    def test_select_confirm_combo_prefers_smallest_feasible_alpha(self) -> None:
        confirm_evaluations = [
            {
                "confirm_metric": {
                    "layer": 16,
                    "alpha": 3.0,
                    "steering_shift_mean": 11.0,
                    "reversal_shift_mean": 10.0,
                    "bidirectional_effect": 21.0,
                }
            },
            {
                "confirm_metric": {
                    "layer": 12,
                    "alpha": 2.0,
                    "steering_shift_mean": 10.5,
                    "reversal_shift_mean": 10.0,
                    "bidirectional_effect": 20.5,
                }
            },
            {
                "confirm_metric": {
                    "layer": 15,
                    "alpha": 2.5,
                    "steering_shift_mean": 11.5,
                    "reversal_shift_mean": 11.0,
                    "bidirectional_effect": 22.5,
                }
            },
        ]

        selected, meta = _select_confirm_combo(
            confirm_evaluations,
            min_bidirectional_effect=20.0,
            combo_selection_policy="smallest_feasible_alpha",
        )
        self.assertEqual(selected["confirm_metric"]["alpha"], 2.0)
        self.assertFalse(meta["fallback_used"])
        self.assertEqual(meta["eligible_count"], 3)

    def test_select_confirm_combo_falls_back_when_none_meet_min_effect(self) -> None:
        confirm_evaluations = [
            {
                "confirm_metric": {
                    "layer": 16,
                    "alpha": 3.0,
                    "steering_shift_mean": 9.0,
                    "reversal_shift_mean": 8.0,
                    "bidirectional_effect": 17.0,
                }
            },
            {
                "confirm_metric": {
                    "layer": 14,
                    "alpha": 2.0,
                    "steering_shift_mean": 7.0,
                    "reversal_shift_mean": 6.5,
                    "bidirectional_effect": 13.5,
                }
            },
        ]
        selected, meta = _select_confirm_combo(
            confirm_evaluations,
            min_bidirectional_effect=20.0,
            combo_selection_policy="smallest_feasible_alpha",
        )
        self.assertTrue(meta["fallback_used"])
        self.assertEqual(meta["fallback_reason"], "no_feasible_combo_meeting_min_bidirectional_effect")
        self.assertEqual(selected["confirm_metric"]["alpha"], 3.0)

    def test_select_confirm_combo_max_bidirectional_policy(self) -> None:
        confirm_evaluations = [
            {
                "confirm_metric": {
                    "layer": 12,
                    "alpha": 2.0,
                    "steering_shift_mean": 10.0,
                    "reversal_shift_mean": 10.0,
                    "bidirectional_effect": 20.0,
                }
            },
            {
                "confirm_metric": {
                    "layer": 16,
                    "alpha": 3.0,
                    "steering_shift_mean": 11.0,
                    "reversal_shift_mean": 11.0,
                    "bidirectional_effect": 22.0,
                }
            },
        ]
        selected, meta = _select_confirm_combo(
            confirm_evaluations,
            min_bidirectional_effect=20.0,
            combo_selection_policy="max_bidirectional_effect",
        )
        self.assertTrue(meta["fallback_used"])
        self.assertEqual(meta["fallback_reason"], "policy_prefers_max_bidirectional_effect")
        self.assertEqual(selected["confirm_metric"]["alpha"], 3.0)

    def test_split_rows_is_deterministic_and_sized(self) -> None:
        rows = [{"id": i} for i in range(40)]
        out1 = _split_rows(
            rows,
            seed=42,
            trait="sycophancy",
            sweep_prompts_per_trait=5,
            confirm_prompts_per_trait=7,
            test_prompts_per_trait=8,
        )
        out2 = _split_rows(
            rows,
            seed=42,
            trait="sycophancy",
            sweep_prompts_per_trait=5,
            confirm_prompts_per_trait=7,
            test_prompts_per_trait=8,
        )

        self.assertEqual(len(out1[0]), 5)
        self.assertEqual(len(out1[1]), 7)
        self.assertEqual(len(out1[2]), 8)
        self.assertEqual(out1, out2)

    def test_split_rows_raises_on_insufficient_prompts(self) -> None:
        rows = [{"id": i} for i in range(5)]
        with self.assertRaises(ValueError):
            _split_rows(
                rows,
                seed=42,
                trait="evil",
                sweep_prompts_per_trait=2,
                confirm_prompts_per_trait=2,
                test_prompts_per_trait=2,
            )

    def test_parse_trait_combos(self) -> None:
        parsed = _parse_trait_combos("sycophancy:15:3.0,evil:16:2.5")
        self.assertEqual(parsed["sycophancy"]["layer"], 15)
        self.assertEqual(parsed["evil"]["alpha"], 2.5)

        with self.assertRaises(ValueError):
            _parse_trait_combos("unknown:16:2.0")

    def test_hook_name_for_layer(self) -> None:
        self.assertEqual(_hook_name_for_layer(15), "blocks.15.hook_resid_post")
        self.assertEqual(_hook_name_for_layer(15.9), "blocks.15.hook_resid_post")

    def test_apply_steering_direction_sign(self) -> None:
        resid = torch.tensor([[1.0, 2.0]], dtype=torch.float32)
        direction = torch.tensor([[0.5, -1.0]], dtype=torch.float32)
        plus = _apply_steering_direction(resid, direction, 2.0)
        minus = _apply_steering_direction(resid, direction, -2.0)

        self.assertTrue(torch.allclose(plus, torch.tensor([[2.0, 0.0]])))
        self.assertTrue(torch.allclose(minus, torch.tensor([[0.0, 4.0]])))

    def test_extract_retry_after_seconds_from_response_headers(self) -> None:
        class FakeResponse:
            headers = {"retry-after": "3.5"}

        class FakeExc(Exception):
            response = FakeResponse()

        retry_after = _extract_retry_after_seconds(FakeExc("boom"))
        self.assertEqual(retry_after, 3.5)

    def test_compute_retry_sleep_seconds_prefers_retry_after(self) -> None:
        class FakeResponse:
            headers = {"retry-after": "120"}

        class FakeExc(Exception):
            response = FakeResponse()

        sleep_s = _compute_retry_sleep_seconds(
            attempt_index=2,
            exc=FakeExc("boom"),
            base_seconds=0.75,
            max_seconds=30.0,
            jitter_fraction=0.2,
        )
        self.assertEqual(sleep_s, 30.0)

    def test_compute_retry_sleep_seconds_exponential_no_jitter(self) -> None:
        sleep_s = _compute_retry_sleep_seconds(
            attempt_index=3,
            exc=None,
            base_seconds=0.5,
            max_seconds=10.0,
            jitter_fraction=0.0,
        )
        self.assertEqual(sleep_s, 4.0)

    def test_alpha_grid_from_config(self) -> None:
        config = {"steering": {"coefficients": [0.5, 1.0, 2.5]}}
        self.assertEqual(_alpha_grid_from_config(config), [0.5, 1.0, 2.5])

    def test_alpha_grid_from_config_raises_on_missing_values(self) -> None:
        with self.assertRaises(ValueError):
            _alpha_grid_from_config({"steering": {"coefficients": []}})

    def test_combo_selection_policy_from_config_default_and_override(self) -> None:
        self.assertEqual(_combo_selection_policy_from_config({"steering": {}}), "smallest_feasible_alpha")
        self.assertEqual(
            _combo_selection_policy_from_config({"steering": {"combo_selection_policy": "max_bidirectional_effect"}}),
            "max_bidirectional_effect",
        )
        with self.assertRaises(ValueError):
            _combo_selection_policy_from_config({"steering": {"combo_selection_policy": "unknown"}})

    def test_coherence_gate_mode_from_config_default_and_override(self) -> None:
        self.assertEqual(_coherence_gate_mode_from_config({"steering": {}}), "absolute_and_relative")
        self.assertEqual(
            _coherence_gate_mode_from_config({"steering": {"coherence_gate_mode": "relative_only"}}),
            "relative_only",
        )
        with self.assertRaises(ValueError):
            _coherence_gate_mode_from_config({"steering": {"coherence_gate_mode": "unknown"}})

    def test_build_coherence_summary_supports_gate_modes(self) -> None:
        baseline_scores = [60.0, 60.0]
        steered_scores = [65.0, 65.0]
        summary_relative = _build_coherence_summary(
            baseline_scores=baseline_scores,
            steered_scores=steered_scores,
            coherence_min_score=75.0,
            coherence_max_drop=10.0,
            coherence_gate_mode="relative_only",
        )
        summary_absolute = _build_coherence_summary(
            baseline_scores=baseline_scores,
            steered_scores=steered_scores,
            coherence_min_score=75.0,
            coherence_max_drop=10.0,
            coherence_gate_mode="absolute_and_relative",
        )

        self.assertTrue(summary_relative["pass_max_drop"])
        self.assertFalse(summary_relative["pass_min_score"])
        self.assertTrue(summary_relative["pass_relative_only"])
        self.assertFalse(summary_relative["pass_absolute_and_relative"])
        self.assertTrue(summary_relative["pass"])
        self.assertFalse(summary_absolute["pass"])

    def test_normalize_csv_helpers(self) -> None:
        self.assertEqual(_normalize_csv_floats("0.5, 1.0,2.5"), [0.5, 1.0, 2.5])
        self.assertEqual(_normalize_csv_ints("11, 12,13"), [11, 12, 13])
        with self.assertRaises(ValueError):
            _normalize_csv_floats("  ,  ")
        with self.assertRaises(ValueError):
            _normalize_csv_ints("  ,  ")

    def test_checkpoint_key_resolution_and_normalization(self) -> None:
        key_explicit = _resolve_checkpoint_key(
            trait="sycophancy",
            seed=42,
            run_name="ignored",
            checkpoint_key=" custom key / name ",
        )
        key_run_name = _resolve_checkpoint_key(
            trait="evil",
            seed=7,
            run_name="run name with spaces",
            checkpoint_key=None,
        )
        key_fallback = _resolve_checkpoint_key(
            trait="hallucination",
            seed=9,
            run_name=None,
            checkpoint_key="",
        )

        self.assertEqual(key_explicit, "custom-key-name")
        self.assertEqual(key_run_name, "run-name-with-spaces")
        self.assertEqual(key_fallback, "week2-upgrade-hallucination-s9")

    def test_encode_decode_int_key_dict_roundtrip(self) -> None:
        original = {1: {"x": 2}, 9: [1, 2, 3]}
        encoded = _encode_int_key_dict(original)
        decoded = _decode_int_key_dict(encoded)
        self.assertEqual(encoded, {"1": {"x": 2}, "9": [1, 2, 3]})
        self.assertEqual(decoded, original)

    def test_combo_key_is_stable(self) -> None:
        self.assertEqual(_combo_key(15, 2.5), "l15_a2.50000000")
        self.assertEqual(_combo_key(15, 2.5000000001), "l15_a2.50000000")


if __name__ == "__main__":
    unittest.main()
