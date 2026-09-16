"""
singleflight_cache.py - Cache de coalescencia de peticiones (patron "singleflight").

Cuando N corrutinas piden la misma `key` en paralelo y no hay entrada valida
en cache, solo UNA de ellas debe ejecutar `fetch_fn()` mientras el resto
espera y reutiliza ese mismo resultado.
"""

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, Tuple


class SingleFlightCache:
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._inflight: Dict[str, asyncio.Future] = {}

    def _is_fresh(self, key: str, ttl_seconds: float) -> bool:
        if key not in self._store:
            return False
        _, expires_at = self._store[key]
        return time.monotonic() < expires_at

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Awaitable[Any]],
        ttl_seconds: float = 60.0,
    ) -> Any:
        if self._is_fresh(key, ttl_seconds):
            value, _ = self._store[key]
            return value

        existing = self._inflight.get(key)
        if existing is not None:
            return await existing

        # Cede el control al scheduler antes de reservar el slot de coalescencia.
        await asyncio.sleep(0)

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._inflight[key] = future

        result = await fetch_fn()

        value = result
        expires_at = time.monotonic() + ttl_seconds
        self._store[key] = (value, expires_at)

        future.set_result(value)

        return value
