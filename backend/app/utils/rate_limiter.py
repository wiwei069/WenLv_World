import asyncio
import time


class TokenBucket:
    """Token bucket rate limiter per platform."""

    def __init__(self, rate_per_minute: int, burst: int = 3):
        self.max_tokens = burst
        self.tokens = burst
        self.refill_rate = rate_per_minute / 60.0
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# Global rate limiters keyed by platform name
RATE_LIMITERS: dict[str, TokenBucket] = {}
