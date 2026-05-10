from __future__ import annotations

import time
from typing import Dict

from fastapi import Depends, HTTPException

from ..auth.tokens import get_current_user
from ..config import settings


class TokenBucket:
    """
    Per-user token bucket rate limiter.

    Tokens refill continuously at `refill_rate` per second up to `capacity`.
    Each API call drains 1 token.  If the bucket is empty the request is rejected
    with HTTP 429.

    Python analogy: imagine a bucket that drips water in at a fixed rate.
    Each request takes a sip.  If it's empty, you wait.
    """

    def __init__(self, capacity: float, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        added = (now - self._last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + added)
        self._last_refill = now

    def consume(self, amount: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def available(self) -> float:
        self._refill()
        return round(self.tokens, 2)


# In-memory registry keyed by "org_id:user_id".
# In production this would be Redis so limits survive restarts and scale
# across multiple workers.
_BUCKETS: Dict[str, TokenBucket] = {}


def _get_bucket(key: str) -> TokenBucket:
    if key not in _BUCKETS:
        _BUCKETS[key] = TokenBucket(
            capacity=settings.rate_limit_capacity,
            refill_rate=settings.rate_limit_refill_rate,
        )
    return _BUCKETS[key]


async def check_rate_limit(current_user: dict = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency — enforce per-user token bucket rate limiting.
    Returns the current_user dict unchanged so callers can chain it.
    Raises HTTP 429 when the bucket is empty.
    """
    key = f"{current_user['org_id']}:{current_user['user_id']}"
    bucket = _get_bucket(key)
    if not bucket.consume():
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded — {bucket.available():.1f} tokens remaining. "
                "Please wait before making another request."
            ),
            headers={"Retry-After": "10"},
        )
    return current_user
