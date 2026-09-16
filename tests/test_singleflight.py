import asyncio
import contextlib

import pytest

from singleflight_cache import SingleFlightCache


async def _guarded(coro, timeout, deadlock_message):
    """Ejecuta una corrutina con limite de tiempo estricto. Si un parche candidato
    introduce un deadlock/hang real en cualquier punto (registro, fetch, o limpieza
    tras cancelacion), la prueba falla de forma controlada en vez de congelar pytest
    y el contenedor de la Aduana 3 indefinidamente."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(deadlock_message)


@pytest.mark.asyncio
async def test_thundering_herd_coalescing():
    cache = SingleFlightCache()
    call_count = 0

    async def fetch_fn():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.2)
        return "resultado-compartido"

    async def body():
        return await asyncio.gather(*[
            cache.get_or_fetch("shared-key", fetch_fn, ttl_seconds=60.0)
            for _ in range(50)
        ])

    results = await _guarded(
        body(),
        timeout=5.0,
        deadlock_message=(
            "Deadlock/hang detectado: las 50 llamadas concurrentes nunca resolvieron "
            "(cache stampede o bloqueo en el registro de coalescencia)."
        ),
    )

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

    async def cleanup_primary():
        with contextlib.suppress(asyncio.CancelledError):
            await primary

    await _guarded(
        cleanup_primary(),
        timeout=1.5,
        deadlock_message=(
            "Deadlock detectado: la propia corrutina primaria quedo congelada al limpiar "
            "sus recursos tras ser cancelada (p. ej. re-adquiriendo un lock que un "
            "suscriptor en cola sigue reteniendo indefinidamente)."
        ),
    )

    async def wait_secondaries():
        return await asyncio.gather(*secondaries, return_exceptions=True)

    results = await _guarded(
        wait_secondaries(),
        timeout=1.5,
        deadlock_message=(
            "Deadlock detectado: los suscriptores quedaron congelados esperando un "
            "asyncio.Future huerfano tras la cancelacion de la corrutina primaria."
        ),
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

    async def body():
        return await asyncio.gather(*[
            cache.get_or_fetch(f"key-{i}", fetch_fn, ttl_seconds=60.0)
            for i in range(200)
        ])

    await _guarded(
        body(),
        timeout=5.0,
        deadlock_message=(
            "Deadlock/hang detectado: la resolucion de 200 claves concurrentes nunca "
            "termino (bloqueo en el registro o limpieza de coalescencia)."
        ),
    )

    assert len(cache._inflight) == 0, (
        f"Fuga de memoria: {len(cache._inflight)} referencias huerfanas retenidas "
        "en el registro de coalescencia tras finalizar la resolucion."
    )
