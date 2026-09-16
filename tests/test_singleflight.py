import asyncio
import contextlib

import pytest

from singleflight_cache import SingleFlightCache


@pytest.mark.asyncio
async def test_thundering_herd_coalescing():
    cache = SingleFlightCache()
    call_count = 0

    async def fetch_fn():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.2)
        return "resultado-compartido"

    results = await asyncio.gather(*[
        cache.get_or_fetch("shared-key", fetch_fn, ttl_seconds=60.0)
        for _ in range(50)
    ])

    assert call_count == 1, (
        f"fetch_fn se ejecuto {call_count} veces en lugar de 1 (cache stampede / thundering herd)."
    )
    assert all(r == "resultado-compartido" for r in results)


@pytest.mark.asyncio
async def test_cancellation_recovery():
    cache = SingleFlightCache()

    async def fetch_fn():
        await asyncio.sleep(1.0)
        return "valor-final"

    primary = asyncio.create_task(
        cache.get_or_fetch("volatile-key", fetch_fn, ttl_seconds=60.0)
    )
    # Deja que la corrutina primaria registre el future compartido de coalescencia.
    await asyncio.sleep(0.05)

    secondaries = [
        asyncio.create_task(cache.get_or_fetch("volatile-key", fetch_fn, ttl_seconds=60.0))
        for _ in range(5)
    ]
    # A mitad de camino del fetch (que dura 1.0s), se cancela la primaria.
    await asyncio.sleep(0.1)

    primary.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await primary

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*secondaries, return_exceptions=True), timeout=1.5
        )
    except asyncio.TimeoutError:
        for task in secondaries:
            task.cancel()
        pytest.fail(
            "Deadlock detectado: los suscriptores quedaron congelados esperando un "
            "asyncio.Future huerfano tras la cancelacion de la corrutina primaria."
        )

    # No hubo deadlock. Cualquier secundaria que haya completado con exito (failover)
    # debe traer el valor correcto; una que haya recibido una excepcion propagada en
    # lugar de colgarse para siempre tambien cuenta como recuperacion valida.
    for r in results:
        if isinstance(r, BaseException):
            continue
        assert r == "valor-final"


@pytest.mark.asyncio
async def test_memory_drain_post_execution():
    cache = SingleFlightCache()

    async def fetch_fn():
        await asyncio.sleep(0.01)
        return "ok"

    await asyncio.gather(*[
        cache.get_or_fetch(f"key-{i}", fetch_fn, ttl_seconds=60.0)
        for i in range(200)
    ])

    assert len(cache._inflight) == 0, (
        f"Fuga de memoria: {len(cache._inflight)} referencias huerfanas retenidas "
        "en el registro de coalescencia tras finalizar la resolucion."
    )
