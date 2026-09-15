import asyncio
from typing import Dict, List, Callable, Any

class TransactionManager:
    """
    Administrador de transacciones multi-recurso con 2PL ingenuo.
    Vulnerable a Deadlocks por inversion de orden y recursos huerfanos ante fallos.
    """
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()

    async def _get_lock(self, resource_id: str) -> asyncio.Lock:
        async with self._meta_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = asyncio.Lock()
            return self._locks[resource_id]

    async def execute_transaction(self, tx_id: str, resources: List[str], payload_fn: Callable[[], Any]) -> Any:
        acquired_locks = []
        # VULNERABILIDAD 1: No hay orden deterministico -> Deadlock con recursos cruzados
        for res in resources:
            lock = await self._get_lock(res)
            await lock.acquire()
            acquired_locks.append(lock)
            # Ceder ejecucion para facilitar context switch y reproducir el deadlock
            await asyncio.sleep(0.01)

        # VULNERABILIDAD 2: Sin bloque try/finally robusto -> Fuga de locks ante excepciones
        result = await payload_fn()

        for lock in acquired_locks:
            lock.release()

        return result
