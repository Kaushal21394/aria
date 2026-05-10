from __future__ import annotations

import asyncio
import logging
from typing import Optional

import anthropic

from ..config import settings

logger = logging.getLogger(__name__)

# Minimum seconds to wait before each retry attempt.
# The rate limit is per-minute, so we need to wait long enough for the
# window to partially reset. The Anthropic 429 response includes a
# `retry-after` header — we use that when available.
_FALLBACK_WAITS = [15, 30, 60]  # seconds before attempt 2, 3, 4


def _retry_after(exc: anthropic.RateLimitError, max_wait: float = 30.0) -> Optional[float]:
    """Extract Retry-After from the error headers, capped at max_wait seconds."""
    try:
        value = exc.response.headers.get("retry-after")
        if value is not None:
            return min(float(value), max_wait)
    except Exception:
        pass
    return None


async def with_backoff(create_fn, max_retries: int = 4, **kwargs):
    """
    Call an async Anthropic messages.create with retry on rate-limit errors.

    Strategy:
    - Read the `retry-after` header from the 429 response and wait that long.
    - Fall back to 15s → 30s → 60s if the header is absent.
    - Raises the original error after max_retries exhausted.
    """
    for attempt in range(max_retries):
        try:
            return await create_fn(**kwargs)
        except anthropic.RateLimitError as exc:
            if attempt == max_retries - 1:
                raise

            wait = _retry_after(exc) or _FALLBACK_WAITS[min(attempt, len(_FALLBACK_WAITS) - 1)]
            logger.warning(
                "[RateLimit] 429 — waiting %.0fs before retry %d/%d",
                wait, attempt + 2, max_retries,
            )
            await asyncio.sleep(wait)


async def with_timeout_and_fallback(
    primary_fn,
    fallback_fn,
    timeout_sec: float = 60.0,
    **kwargs,
):
    """
    Phase 4 resilience wrapper:

    1. Attempt `primary_fn(**kwargs)` with a `timeout_sec` deadline.
    2. On asyncio.TimeoutError or any exception, retry once with `fallback_fn`
       (typically a cheaper/faster model, or the same fn on a different key).
    3. If the fallback also fails, re-raise.

    Usage:
        resp = await with_timeout_and_fallback(
            primary_fn=client.messages.create,
            fallback_fn=fallback_client.messages.create,
            timeout_sec=45,
            model=settings.aria_model,
            max_tokens=600,
            messages=[...],
        )
    """
    loop = asyncio.get_event_loop()

    async def _attempt(fn):
        return await asyncio.wait_for(fn(**kwargs), timeout=timeout_sec)

    try:
        return await _attempt(primary_fn)
    except (asyncio.TimeoutError, Exception) as primary_exc:
        logger.warning(
            "[Resilience] Primary call failed (%s) — trying fallback model %s",
            primary_exc, settings.fallback_model,
        )
        try:
            fallback_kwargs = {**kwargs, "model": settings.fallback_model}
            return await _attempt(fallback_fn)
        except Exception as fallback_exc:
            logger.error("[Resilience] Fallback also failed: %s", fallback_exc)
            raise fallback_exc
