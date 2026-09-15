import time
import asyncio
from typing import Dict, List

class SlidingWindowLimiter:
    """
    Rate limiter basado en Sliding Window Log con proteccion contra 
    condiciones de carrera y fugas de memoria.
    """
    def __init__(self, max_requests: int = 5, window_seconds: float = 1.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds

        async with self._lock:
            # Limpieza de la clave específica y purga de claves inactivas
            keys_to_delete = []
            for k, timestamps in self._requests.items():
                valid_timestamps = [t for t in timestamps if t > cutoff]
                if not valid_timestamps:
                    keys_to_delete.append(k)
                else:
                    self._requests[k] = valid_timestamps
            
            for k in keys_to_delete:
                del self._requests[k]

            # Obtener timestamps actuales para la clave solicitada
            timestamps = self._requests.get(key, [])
            
            # Verificar capacidad
            if len(timestamps) < self.max_requests:
                timestamps.append(now)
                self._requests[key] = timestamps
                return True
            
            return False
