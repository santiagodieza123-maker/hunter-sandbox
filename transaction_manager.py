import asyncio
from typing import Dict, List, Callable, Any, Awaitable
from contextlib import AsyncExitStack
from weakref import WeakValueDictionary

class TransactionManager:
    """
    Administrador de transacciones multi-recurso con 2PL robusto.
    Previene deadlocks mediante ordenamiento determinístico y asegura liberación mediante AsyncExitStack.
    Utiliza WeakValueDictionary para evitar fugas de memoria en el registro de locks.
    """
    def __init__(self):
        self._locks: WeakValueDictionary[str, asyncio.Lock] = WeakValueDictionary()
        self._meta_lock = asyncio.Lock()

    async def _get_lock(self, resource_id: str) -> asyncio.Lock:
        async with self._meta_lock:
            lock = self._locks.get(resource_id)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[resource_id] = lock
            return lock

    async def execute_transaction(self, tx_id: str, resources: List[str], payload_fn: Callable[[], Awaitable[Any]]) -> Any:
        # Ordenamiento determinístico para prevenir deadlocks
        sorted_resources = sorted(list(set(resources)))
        
        async with AsyncExitStack() as stack:
            for res in sorted_resources:
                lock = await self._get_lock(res)
                # Registrar la adquisición en el stack para asegurar liberación incondicional
                await stack.enter_async_context(lock)
            
            # Ejecución protegida: si payload_fn falla, AsyncExitStack libera los locks
            return await payload_fn()
