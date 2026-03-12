import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from scripts.glp_export_memmap_dataset import (
    FlatMemmapWriter,
    RunningMoments,
    _build_prompt_records,
    _default_dataset_name,
    _format_export_prompt,
    _load_hooked_model,
    _resolve_prompt_row,
    _select_capture_positions,
)


class TestGLPExportMemmapDataset(unittest.TestCase):
    def test_resolve_prompt_row_prefers_neutral_and_user_query(self) -> None:
        row = {
            "neutral_system_prompt": "neutral",
            "system_low": "low",
            "user_query": "question",
        }
        system_prompt, user_query = _resolve_prompt_row(
            row,
            default_system_prompt="fallback",
        )
        self.assertEqual(system_prompt, "neutral")
        self.assertEqual(user_query, "question")

    def test_resolve_prompt_row_falls_back_to_system_low_and_prompt(self) -> None:
        row = {"system_low": "low", "prompt": "prompt text"}
        system_prompt, user_query = _resolve_prompt_row(
            row,
            default_system_prompt="fallback",
        )
        self.assertEqual(system_prompt, "low")
        self.assertEqual(user_query, "prompt text")

    def test_select_capture_positions(self) -> None:
        self.assertEqual(_select_capture_positions(5, 5, "prompt_last"), [4])
        self.assertEqual(_select_capture_positions(5, 8, "response_last"), [7])
        self.assertEqual(_select_capture_positions(5, 8, "response_all"), [5, 6, 7])
        self.assertEqual(_select_capture_positions(5, 8, "all_tokens"), list(range(8)))
        self.assertEqual(_select_capture_positions(5, 5, "response_last"), [])

    def test_build_prompt_records_dedupes_prompt_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rows.jsonl"
            rows = [
                {"id": 1, "neutral_system_prompt": "n", "user_query": "q"},
                {"id": 2, "neutral_system_prompt": "n", "user_query": "q"},
                {"id": 3, "system_low": "low", "prompt": "other"},
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            records = _build_prompt_records(
                prompt_paths=[path],
                default_system_prompt="fallback",
                limit_per_file=0,
                seed=0,
                dedupe=True,
            )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].row_id, "1")
        self.assertEqual(records[1].system_prompt, "low")

    def test_memmap_writer_rolls_over_shards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            writer = FlatMemmapWriter(
                output_dir=out,
                vector_dim=4,
                dtype=np.float32,
                samples_per_shard=2,
            )
            writer.write_vector(np.array([1, 2, 3, 4], dtype=np.float32))
            writer.write_vector(np.array([5, 6, 7, 8], dtype=np.float32))
            writer.write_vector(np.array([9, 10, 11, 12], dtype=np.float32))
            writer.flush()
            indices = np.load(out / "data_indices.npy")
            self.assertEqual(indices.shape, (3, 3))
            self.assertEqual((out / "data_0000.npy").exists(), True)
            self.assertEqual((out / "data_0001.npy").exists(), True)
            self.assertEqual((out / "dtype.txt").read_text(encoding="utf-8"), "float32")

    def test_running_moments_finalize(self) -> None:
        moments = RunningMoments(vector_dim=2)
        moments.update(np.array([1.0, 3.0], dtype=np.float32))
        moments.update(np.array([3.0, 7.0], dtype=np.float32))
        mean, var = moments.finalize()
        np.testing.assert_allclose(mean, np.array([2.0, 5.0], dtype=np.float32))
        np.testing.assert_allclose(var, np.array([1.0, 4.0], dtype=np.float32))

    def test_default_dataset_name(self) -> None:
        name = _default_dataset_name(
            model_name="meta-llama/Llama-3.1-8B-Instruct",
            layer=12,
            capture_mode="response_all",
            prompt_count=99,
        )
        self.assertIn("llama-3-1-8b-instruct", name)
        self.assertIn("l12", name)
        self.assertIn("response_all", name)
        self.assertTrue(name.endswith("99p"))

    def test_default_dataset_name_conditional(self) -> None:
        name = _default_dataset_name(
            model_name="meta-llama/Llama-3.1-8B-Instruct",
            layer=12,
            capture_mode="response_last",
            prompt_count=99,
            condition_mode="prompt_last",
        )
        self.assertIn("cond-prompt-last-to-response-last", name)
        self.assertTrue(name.endswith("99p"))

    def test_format_export_prompt_falls_back_when_system_role_not_supported(self) -> None:
        tokenizer = mock.Mock()
        tokenizer.apply_chat_template.side_effect = [
            Exception("System role not supported"),
            "<bos>user merged<assistant>",
        ]
        prompt = _format_export_prompt(tokenizer, "system text", "user text")
        self.assertEqual(prompt, "<bos>user merged<assistant>")
        merged_messages = tokenizer.apply_chat_template.call_args_list[1].args[0]
        self.assertEqual(merged_messages, [{"role": "user", "content": "system text\n\nuser text"}])

    def test_load_hooked_model_retries_local_files_only_on_gated_error(self) -> None:
        mocked_cls = mock.Mock()
        mocked_cls.from_pretrained.side_effect = [
            OSError("Cannot access gated repo for url ... 401 Client Error"),
            "cached-model",
        ]
        with mock.patch.dict("sys.modules", {"sae_lens": mock.Mock(HookedSAETransformer=mocked_cls)}):
            model = _load_hooked_model("meta-llama/Llama-3.1-8B-Instruct")
        self.assertEqual(model, "cached-model")
        self.assertEqual(mocked_cls.from_pretrained.call_count, 2)
        first_call = mocked_cls.from_pretrained.call_args_list[0]
        second_call = mocked_cls.from_pretrained.call_args_list[1]
        self.assertNotIn("local_files_only", first_call.kwargs)
        self.assertEqual(second_call.kwargs["local_files_only"], True)


if __name__ == "__main__":
    unittest.main()
