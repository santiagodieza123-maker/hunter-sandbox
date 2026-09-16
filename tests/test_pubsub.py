import asyncio
import pytest
from pubsub_broker import PubSubBroker, Client

@pytest.mark.asyncio
async def test_fast_publish():
    broker = PubSubBroker()
    c1, c2 = Client("1"), Client("2")
    broker.subscribe("news", c1)
    broker.subscribe("news", c2)
    await broker.publish("news", "hello")
    assert "hello" in c1.messages

@pytest.mark.asyncio
async def test_backpressure_isolation():
    broker = PubSubBroker()
    fast = Client("fast")
    slow = Client("slow")
    async def slow_send(msg):
        await asyncio.sleep(0.5)
        slow.messages.append(msg)
    slow.send = slow_send
    broker.subscribe("news", fast)
    broker.subscribe("news", slow)
    start = asyncio.get_event_loop().time()
    await broker.publish("news", "urgent")
    duration = asyncio.get_event_loop().time() - start
    assert duration < 0.2, "Backpressure detectado"

@pytest.mark.asyncio
async def test_runtime_mutation():
    broker = PubSubBroker()
    c1 = Client("1")
    broker.subscribe("news", c1)
    async def evil_send(msg):
        broker.unsubscribe("news", c1)
        c1.messages.append(msg)
    c1.send = evil_send
    await broker.publish("news", "bomb")

@pytest.mark.asyncio
async def test_memory_leak():
    broker = PubSubBroker()
    c1 = Client("1")
    broker.subscribe("news", c1)
    c1.active = False
    await broker.publish("news", "cleanup")
    assert c1 not in broker.topics["news"]
