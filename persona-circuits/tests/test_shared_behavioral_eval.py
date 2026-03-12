"""Unit tests for shared behavioral evaluation helpers."""

from __future__ import annotations

import types
import unittest

import torch

from scripts.shared.behavioral_eval import (
    JudgeScore,
    SlidingWindowRateLimiter,
    _apply_steering_direction,
    _compute_retry_sleep_seconds,
    _extract_retry_after_seconds,
    _extract_score_json,
    _extract_status_code,
    _format_chat_prompt,
    _hook_name_for_layer,
    _is_retryable_judge_error,
    _judge_prompt,
    generate_response,
    judge_score,
)


class _TemplateTokenizer:
    chat_template = True

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):  # noqa: ANN001
        del tokenize, add_generation_prompt
        return f"TEMPLATE::{messages[0]['content']}::{messages[1]['content']}"


class _NoTemplateTokenizer:
    chat_template = None


class _HooksContext:
    def __init__(self, model: "_FakeModel", fwd_hooks):  # noqa: ANN001
        self.model = model
        self.fwd_hooks = list(fwd_hooks)

    def __enter__(self) -> "_HooksContext":
        self.model._active_hooks = self.fwd_hooks
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        del exc_type, exc, tb
        self.model._active_hooks = []


class _FakeModel:
    def __init__(self) -> None:
        self.cfg = types.SimpleNamespace(dtype=torch.float32)
        self._active_hooks = []
        self.generate_calls = 0

    def to_tokens(self, prompt_text: str, prepend_bos: bool = True) -> torch.Tensor:
        del prompt_text, prepend_bos
        return torch.tensor([[1, 2]], dtype=torch.long)

    def hooks(self, fwd_hooks):  # noqa: ANN001
        return _HooksContext(self, fwd_hooks)

    def generate(self, tokens: torch.Tensor, **kwargs) -> torch.Tensor:  # noqa: ANN003
        del kwargs
        self.generate_calls += 1
        resid = torch.zeros((1, 1, 2), dtype=torch.float32)
        for _, hook_fn in self._active_hooks:
            resid = hook_fn(resid, None)
        marker = int(round(float(resid.sum().item())))
        completion = torch.tensor([[10 + marker, 11 + marker]], dtype=torch.long)
        return torch.cat([tokens, completion], dim=1)

    def to_string(self, completion: torch.Tensor) -> str:
        return ",".join(str(int(x.item())) for x in completion)


class _FakeAnthropicModule:
    class RateLimitError(Exception):
        pass

    class APITimeoutError(Exception):
        pass

    class APIConnectionError(Exception):
        pass

    class InternalServerError(Exception):
        pass


class _FakeMessages:
    def __init__(self, outputs):  # noqa: ANN001
        self._outputs = list(outputs)

    def create(self, **kwargs):  # noqa: ANN003
        del kwargs
        if not self._outputs:
            raise RuntimeError("no outputs left")
        value = self._outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return types.SimpleNamespace(content=[types.SimpleNamespace(text=str(value))])


class _FakeAnthropicClient:
    def __init__(self, outputs):  # noqa: ANN001
        self.messages = _FakeMessages(outputs)


class SharedBehavioralEvalTests(unittest.TestCase):
    def test_format_chat_prompt_uses_template_when_available(self) -> None:
        out = _format_chat_prompt(_TemplateTokenizer(), "sys", "usr")
        self.assertEqual(out, "TEMPLATE::sys::usr")

    def test_format_chat_prompt_fallback(self) -> None:
        out = _format_chat_prompt(_NoTemplateTokenizer(), "sys", "usr")
        self.assertIn("System: sys", out)
        self.assertIn("User: usr", out)

    def test_hook_name_and_steering_direction(self) -> None:
        self.assertEqual(_hook_name_for_layer(12.8), "blocks.12.hook_resid_post")
        resid = torch.tensor([[1.0, 2.0]], dtype=torch.float32)
        direction = torch.tensor([[0.5, -1.0]], dtype=torch.float32)
        out = _apply_steering_direction(resid, direction, 2.0)
        self.assertTrue(torch.allclose(out, torch.tensor([[2.0, 0.0]])))

    def test_extract_score_json(self) -> None:
        score, ok = _extract_score_json('{"score": 77}')
        self.assertTrue(ok)
        self.assertEqual(score, 77.0)
        bad, bad_ok = _extract_score_json('{"score": 77, "extra": 1}')
        self.assertFalse(bad_ok)
        self.assertIsNone(bad)

    def test_judge_prompt_supports_new_trait_lane_rubric(self) -> None:
        prompt = _judge_prompt("assistant_likeness", "q", "r", "N/A")
        self.assertIn("assistant-likeness", prompt.lower())

    def test_rate_limiter_constructor_guard(self) -> None:
        with self.assertRaises(ValueError):
            SlidingWindowRateLimiter(0, 0.0)
        limiter = SlidingWindowRateLimiter(60, 0.0)
        limiter.wait()

    def test_extract_status_retry_after_and_retryable(self) -> None:
        class Resp:
            status_code = 429
            headers = {"retry-after": "2.5"}

        class Exc(Exception):
            response = Resp()

        exc = Exc("boom")
        self.assertEqual(_extract_status_code(exc), 429)
        self.assertEqual(_extract_retry_after_seconds(exc), 2.5)
        self.assertTrue(_is_retryable_judge_error(exc, _FakeAnthropicModule))

    def test_compute_retry_sleep_seconds_prefers_retry_after(self) -> None:
        class Resp:
            headers = {"retry-after": "9"}

        class Exc(Exception):
            response = Resp()

        sleep_s = _compute_retry_sleep_seconds(
            attempt_index=2,
            exc=Exc("boom"),
            base_seconds=0.75,
            max_seconds=3.0,
            jitter_fraction=0.2,
        )
        self.assertEqual(sleep_s, 3.0)

    def test_generate_response_with_cache_and_hooks(self) -> None:
        model = _FakeModel()
        baseline = generate_response(
            model=model,
            prompt_text="hello",
            max_new_tokens=16,
            temperature=0.0,
            response_cache={},
            cache_key=("baseline",),
        )
        self.assertEqual(baseline, "10,11")

        response_cache: dict[tuple[str], str] = {}
        direction = torch.ones((1, 1, 2), dtype=torch.float32)

        def plus_one_hook(resid_post, hook):  # noqa: ANN001
            del hook
            return resid_post + 1.0

        steered = generate_response(
            model=model,
            prompt_text="hello",
            max_new_tokens=16,
            temperature=0.0,
            layer=12,
            direction=direction,
            alpha=2.0,
            additional_fwd_hooks=[(_hook_name_for_layer(12), plus_one_hook)],
            response_cache=response_cache,
            cache_key=("steered",),
        )
        cached = generate_response(
            model=model,
            prompt_text="hello",
            max_new_tokens=16,
            temperature=0.0,
            layer=12,
            direction=direction,
            alpha=2.0,
            additional_fwd_hooks=[(_hook_name_for_layer(12), plus_one_hook)],
            response_cache=response_cache,
            cache_key=("steered",),
        )
        self.assertEqual(steered, cached)
        self.assertEqual(model.generate_calls, 2)  # baseline + first steered only

    def test_judge_score_success_and_cache(self) -> None:
        client = _FakeAnthropicClient(['{"score": 41}'])
        cache: dict[tuple[object, ...], JudgeScore] = {}
        out = judge_score(
            anthropic_client=client,
            anthropic_module=_FakeAnthropicModule,
            judge_model="claude-sonnet-4-6",
            score_trait="sycophancy",
            user_query="q",
            response="r",
            ground_truth="g",
            max_attempts=2,
            rate_limiter=SlidingWindowRateLimiter(120, 0.0),
            retry_base_seconds=0.0,
            retry_max_seconds=0.0,
            retry_jitter_fraction=0.0,
            score_cache=cache,
        )
        self.assertEqual(out.score, 41.0)
        again = judge_score(
            anthropic_client=client,
            anthropic_module=_FakeAnthropicModule,
            judge_model="claude-sonnet-4-6",
            score_trait="sycophancy",
            user_query="q",
            response="r",
            ground_truth="g",
            max_attempts=2,
            rate_limiter=SlidingWindowRateLimiter(120, 0.0),
            retry_base_seconds=0.0,
            retry_max_seconds=0.0,
            retry_jitter_fraction=0.0,
            score_cache=cache,
        )
        self.assertEqual(again.score, 41.0)

    def test_judge_score_retries_parse_then_succeeds(self) -> None:
        client = _FakeAnthropicClient(["not-json", '{"score": 88}'])
        out = judge_score(
            anthropic_client=client,
            anthropic_module=_FakeAnthropicModule,
            judge_model="claude-sonnet-4-6",
            score_trait="evil",
            user_query="q",
            response="r",
            ground_truth="g",
            max_attempts=2,
            rate_limiter=SlidingWindowRateLimiter(120, 0.0),
            retry_base_seconds=0.0,
            retry_max_seconds=0.0,
            retry_jitter_fraction=0.0,
            score_cache=None,
        )
        self.assertEqual(out.score, 88.0)
        self.assertEqual(out.attempts, 2)


if __name__ == "__main__":
    unittest.main()
