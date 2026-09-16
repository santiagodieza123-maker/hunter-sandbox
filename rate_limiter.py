import asyncio
import time
from typing import Optional

class AsyncTokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        start_time = time.monotonic()
        while True:
            self._refill()
            if self.tokens >= tokens:
                await asyncio.sleep(0.0001)
                self.tokens -= tokens
                return True
            
            if timeout is not None and (time.monotonic() - start_time) >= timeout:
                return False
            
            await asyncio.sleep(0.005)
