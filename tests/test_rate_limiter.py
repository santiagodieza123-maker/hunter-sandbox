import asyncio
import pytest
from rate_limiter import AsyncTokenBucket

@pytest.mark.asyncio
async def test_strict_burst_concurrency_limit():
    bucket = AsyncTokenBucket(capacity=20, refill_rate_per_sec=1.0)
    
    async def try_take():
        return await bucket.acquire(tokens=1, timeout=0.01)
    
    tasks = [asyncio.create_task(try_take()) for _ in range(100)]
    results = await asyncio.gather(*tasks)
    
    passed = sum(1 for r in results if r is True)
    assert passed == 20, f"Violación de ráfaga: pasaron {passed}, capacidad máxima 20"

@pytest.mark.asyncio
async def test_atomic_refill_precision_under_load():
    bucket = AsyncTokenBucket(capacity=10, refill_rate_per_sec=10.0)
    
    for _ in range(10):
        assert await bucket.acquire(tokens=1, timeout=0.01) is True
    
    assert await bucket.acquire(tokens=1, timeout=0.01) is False
    await asyncio.sleep(0.5)
    
    tasks = [asyncio.create_task(bucket.acquire(tokens=1, timeout=0.05)) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    assert all(results), "Los 5 tokens recargados debieron adquirirse"
    assert await bucket.acquire(tokens=1, timeout=0.01) is False
