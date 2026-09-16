import asyncio
from typing import Dict, Set

class Client:
    def __init__(self, client_id: str):
        self.id = client_id
        self.active = True
        self.messages = []

    async def send(self, message: str):
        if not self.active:
            raise ConnectionError("Client disconnected")
        await asyncio.sleep(0.1)
        self.messages.append(message)

class PubSubBroker:
    def __init__(self):
        self.topics: Dict[str, Set[Client]] = {}

    def subscribe(self, topic: str, client: Client):
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(client)

    def unsubscribe(self, topic: str, client: Client):
        if topic in self.topics:
            self.topics[topic].remove(client)

    async def publish(self, topic: str, message: str):
        if topic in self.topics:
            for client in self.topics[topic]:
                try:
                    await client.send(message)
                except ConnectionError:
                    pass
