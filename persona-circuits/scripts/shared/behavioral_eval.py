"""Reusable behavioral-eval helpers shared across stage runners."""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, MutableMapping, Sequence

try:
    from scripts.shared.trait_rubrics import JUDGE_PROMPT_HEADER, RUBRICS
except ModuleNotFoundError:  # pragma: no cover
    from trait_rubrics import JUDGE_PROMPT_HEADER, RUBRICS


@dataclass
class JudgeScore:
    score: float
    raw: str
    parse_ok: bool
    attempts: int
    judge_model: str


def _format_chat_prompt(tokenizer: Any, system_prompt: str, user_query: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except (TypeError, ValueError):
            pass
    return f"System: {system_prompt}\nUser: {user_query}\nAssistant:"


def _hook_name_for_layer(layer: int) -> str:
    return f"blocks.{int(layer)}.hook_resid_post"


def _apply_steering_direction(resid_post: Any, direction: Any, alpha: float) -> Any:
    return resid_post + (alpha * direction)


def _judge_prompt(trait: str, user_message: str, response: str, ground_truth: str) -> str:
    if trait not in RUBRICS:
        raise KeyError(f"Unsupported trait for judge rubric: {trait}")
    return (
        JUDGE_PROMPT_HEADER
        + RUBRICS[trait].format(
            user_message=user_message,
            response=response,
            ground_truth=ground_truth,
        )
    )


def _extract_score_json(raw: str) -> tuple[float | None, bool]:
    text = raw.strip()
    if not text:
        return None, False

    candidates = [text]

    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    candidates.extend(block.strip() for block in fenced if block.strip())

    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        candidates.append(brace_match.group(0).strip())

    for cand in candidates:
        try:
            parsed = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and set(parsed.keys()) == {"score"}:
            try:
                value = float(parsed["score"])
            except (TypeError, ValueError):
                continue
            if 0.0 <= value <= 100.0:
                return value, True

    return None, False


class SlidingWindowRateLimiter:
    """Simple in-process throttle: sliding-window RPM + minimum inter-request delay."""

    def __init__(self, requests_per_minute: int, min_interval_seconds: float) -> None:
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be > 0")
        self.requests_per_minute = int(requests_per_minute)
        self.min_interval_seconds = max(0.0, float(min_interval_seconds))
        self._request_timestamps: list[float] = []
        self._last_request_at: float | None = None

    def wait(self) -> None:
        while True:
            now = time.monotonic()
            window_start = now - 60.0
            self._request_timestamps = [t for t in self._request_timestamps if t >= window_start]

            wait_for_window = 0.0
            if len(self._request_timestamps) >= self.requests_per_minute:
                oldest = self._request_timestamps[0]
                wait_for_window = max(0.0, (oldest + 60.0) - now)

            wait_for_spacing = 0.0
            if self._last_request_at is not None:
                wait_for_spacing = max(0.0, (self._last_request_at + self.min_interval_seconds) - now)

            sleep_s = max(wait_for_window, wait_for_spacing)
            if sleep_s <= 1e-6:
                break
            time.sleep(sleep_s)

        now = time.monotonic()
        self._request_timestamps.append(now)
        self._last_request_at = now


def _extract_status_code(exc: Exception) -> int | None:
    for attr in ("status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        for attr in ("status_code", "status"):
            value = getattr(response, attr, None)
            if isinstance(value, int):
                return value
    return None


def _extract_retry_after_seconds(exc: Exception) -> float | None:
    headers = getattr(exc, "headers", None)
    response = getattr(exc, "response", None)
    if headers is None and response is not None:
        headers = getattr(response, "headers", None)
    if headers is None:
        return None
    try:
        retry_after_raw = headers.get("retry-after")  # type: ignore[call-arg]
    except Exception:  # noqa: BLE001
        return None
    if retry_after_raw is None:
        return None
    try:
        retry_after = float(retry_after_raw)
    except (TypeError, ValueError):
        return None
    if retry_after < 0.0:
        return 0.0
    return retry_after


def _is_retryable_judge_error(exc: Exception, anthropic_mod: Any) -> bool:
    retryable_names = (
        "RateLimitError",
        "APITimeoutError",
        "APIConnectionError",
        "InternalServerError",
    )
    for name in retryable_names:
        cls = getattr(anthropic_mod, name, None)
        if isinstance(cls, type) and isinstance(exc, cls):
            return True

    status_code = _extract_status_code(exc)
    if status_code is None:
        return False
    return status_code in {408, 409, 425, 429, 500, 502, 503, 504, 529}


def _compute_retry_sleep_seconds(
    *,
    attempt_index: int,
    exc: Exception | None,
    base_seconds: float,
    max_seconds: float,
    jitter_fraction: float,
) -> float:
    retry_after = _extract_retry_after_seconds(exc) if exc is not None else None
    if retry_after is not None:
        return min(max_seconds, max(0.0, retry_after))

    raw = base_seconds * (2**attempt_index)
    capped = min(max_seconds, raw)
    jitter = random.uniform(0.0, capped * max(0.0, jitter_fraction))
    return capped + jitter


def generate_response(
    *,
    model: Any,
    prompt_text: str,
    max_new_tokens: int,
    temperature: float,
    layer: int | None = None,
    direction: Any | None = None,
    alpha: float = 0.0,
    additional_fwd_hooks: Sequence[tuple[str, Callable[[Any, Any], Any]]] | None = None,
    response_cache: MutableMapping[tuple[Any, ...], str] | None = None,
    cache_key: tuple[Any, ...] | None = None,
    prepend_bos: bool = True,
) -> str:
    if response_cache is not None and cache_key is not None and cache_key in response_cache:
        return response_cache[cache_key]

    tokens = model.to_tokens(prompt_text, prepend_bos=prepend_bos)
    fwd_hooks: list[tuple[str, Callable[[Any, Any], Any]]] = []

    if layer is not None and direction is not None and abs(float(alpha)) > 1e-12:
        hook_name = _hook_name_for_layer(layer)
        direction_runtime = direction
        try:
            direction_runtime = direction.to(device=tokens.device, dtype=model.cfg.dtype)
        except Exception:  # noqa: BLE001
            pass

        def steering_hook(resid_post: Any, hook: Any) -> Any:
            del hook
            return _apply_steering_direction(resid_post, direction_runtime, float(alpha))

        fwd_hooks.append((hook_name, steering_hook))

    if additional_fwd_hooks:
        fwd_hooks.extend(additional_fwd_hooks)

    generate_kwargs = {
        "max_new_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "top_k": None,
        "stop_at_eos": True,
        "verbose": False,
    }

    if fwd_hooks and hasattr(model, "hooks"):
        with model.hooks(fwd_hooks=fwd_hooks):
            generated = model.generate(tokens, **generate_kwargs)
    else:
        generated = model.generate(tokens, **generate_kwargs)

    completion = generated[0, tokens.shape[1] :]
    response = model.to_string(completion)
    if response_cache is not None and cache_key is not None:
        response_cache[cache_key] = response
    return response


def judge_score(
    *,
    anthropic_client: Any,
    anthropic_module: Any,
    judge_model: str,
    score_trait: str,
    user_query: str,
    response: str,
    ground_truth: str,
    max_attempts: int,
    rate_limiter: SlidingWindowRateLimiter | None = None,
    retry_base_seconds: float = 0.75,
    retry_max_seconds: float = 30.0,
    retry_jitter_fraction: float = 0.2,
    score_cache: MutableMapping[tuple[Any, ...], JudgeScore] | None = None,
) -> JudgeScore:
    if int(max_attempts) <= 0:
        raise ValueError("max_attempts must be > 0")

    cache_key = (judge_model, score_trait, user_query, response, ground_truth)
    if score_cache is not None and cache_key in score_cache:
        return score_cache[cache_key]

    prompt = _judge_prompt(
        trait=score_trait,
        user_message=user_query,
        response=response,
        ground_truth=ground_truth,
    )
    current_prompt = prompt
    last_err: Exception | None = None
    resolved_attempts = int(max_attempts)

    for attempt in range(resolved_attempts):
        if rate_limiter is not None:
            rate_limiter.wait()

        try:
            msg = anthropic_client.messages.create(
                model=judge_model,
                max_tokens=64,
                temperature=0.0,
                messages=[{"role": "user", "content": current_prompt}],
            )
            raw = msg.content[0].text if getattr(msg, "content", None) else ""
            score, parse_ok = _extract_score_json(raw)
            if score is not None and parse_ok:
                result = JudgeScore(
                    score=float(score),
                    raw=raw,
                    parse_ok=True,
                    attempts=attempt + 1,
                    judge_model=judge_model,
                )
                if score_cache is not None:
                    score_cache[cache_key] = result
                return result

            current_prompt = (
                "Your previous answer was not parseable. "
                "Return ONLY JSON with exactly one key: "
                '{"score": <integer from 0 to 100>} and no extra text.\n\n'
                f"Original task:\n{prompt}"
            )
            if attempt < resolved_attempts - 1:
                sleep_s = _compute_retry_sleep_seconds(
                    attempt_index=attempt,
                    exc=None,
                    base_seconds=retry_base_seconds,
                    max_seconds=retry_max_seconds,
                    jitter_fraction=retry_jitter_fraction,
                )
                time.sleep(sleep_s)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            retryable = _is_retryable_judge_error(exc, anthropic_module)
            if (not retryable) or attempt >= resolved_attempts - 1:
                break
            sleep_s = _compute_retry_sleep_seconds(
                attempt_index=attempt,
                exc=exc,
                base_seconds=retry_base_seconds,
                max_seconds=retry_max_seconds,
                jitter_fraction=retry_jitter_fraction,
            )
            time.sleep(sleep_s)

    if last_err is not None:
        raise RuntimeError(
            f"Judge scoring failed for model={judge_model} trait={score_trait}"
        ) from last_err
    raise RuntimeError(
        f"Judge returned unparseable output after {resolved_attempts} attempts "
        f"(model={judge_model}, trait={score_trait})."
    )
