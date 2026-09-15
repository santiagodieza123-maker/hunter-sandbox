import asyncio
import time
import pytest
from rate_limiter import SlidingWindowLimiter

@pytest.mark.asyncio
async def test_rate_limiter_basic_window():
    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=0.2)
    assert await limiter.acquire("client_1") is True
    assert await limiter.acquire("client_1") is True
    assert await limiter.acquire("client_1") is False

    # Esperar expiración de ventana
    await asyncio.sleep(0.25)
    assert await limiter.acquire("client_1") is True

@pytest.mark.asyncio
async def test_concurrent_burst_race_condition():
    # 5 peticiones máximas en ventana de 1 segundo
    max_reqs = 5
    limiter = SlidingWindowLimiter(max_requests=max_reqs, window_seconds=1.0)

    # 25 corrutinas atacando simultáneamente la misma clave
    results = await asyncio.gather(*[limiter.acquire("attack_key") for _ in range(25)])
    successful = sum(1 for r in results if r is True)

    assert successful == max_reqs, f"Race condition detectada: se permitieron {successful} peticiones de un maximo de {max_reqs}"

@pytest.mark.asyncio
async def test_memory_cleanup_no_leaks():
    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=0.1)

    # Insertar 50 claves efímeras
    for i in range(50):
        await limiter.acquire(f"ephemeral_client_{i}")

    assert len(limiter._requests) == 50

    # Esperar a que todos los timestamps expiren
    await asyncio.sleep(0.15)

    # Trigger de limpieza (adquiriendo o purgando)
    # Cualquier intento subsiguiente de consulta/adquisición debe asegurar que las claves obsoletas se purguen
    for i in range(50):
        # Intentar consultar o adquirir no debe resucitar llaves viejas si no se les otorga cuota
        pass

    # Evaluar limpieza forzada o durante la operacion
    # Si la clase tiene un método de purga o si en acquire() limpia las entradas vacías
    # Ejecutamos un ciclo para disparar la limpieza
    await limiter.acquire("cleanup_trigger")
    
    # Comprobar que las llaves inactivas ya no consuman memoria
    # Solo debe quedar la clave activa 'cleanup_trigger'
    active_keys = [k for k, v in limiter._requests.items() if len(v) > 0]
    assert len(limiter._requests) <= 1, f"Fuga de memoria detectada: {len(limiter._requests)} claves retenidas en almacenamiento"
