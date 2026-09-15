import time
import asyncio
from collections import defaultdict
from typing import Dict, List

class SlidingWindowLimiter:
    """
    Rate limiter basado en Sliding Window Log.
    Vulnerable a condiciones de carrera concurrentes y fuga de memoria.
    """
    def __init__(self, max_requests: int = 5, window_seconds: float = 1.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # VULNERABILIDAD 2: defaultdict nunca elimina claves vacías -> Fuga de memoria
        self._requests: Dict[str, List[float]] = defaultdict(list)

    async def acquire(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        # Limpiar timestamps obsoletos
        timestamps = self._requests[key]
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self._requests[key] = valid_timestamps

        # VULNERABILIDAD 1: Race Condition (Check-Then-Act sin sincronización)
        # Una corrutina cede el control aquí simulando I/O o context switch
        await asyncio.sleep(0.001)

        if len(self._requests[key]) < self.max_requests:
            self._requests[key].append(now)
            return True
        
        return False
