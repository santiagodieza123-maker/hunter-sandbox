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
    # Tiempo máximo de espera por suscriptor antes de seguir adelante
    # (aísla el broker de un suscriptor lento sin bloquear a los demás).
    SEND_TIMEOUT = 0.15

    def __init__(self):
        self.topics: Dict[str, Set[Client]] = {}

    def subscribe(self, topic: str, client: Client):
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(client)

    def unsubscribe(self, topic: str, client: Client):
        if topic in self.topics:
            self.topics[topic].discard(client)

    async def _send_safe(self, topic: str, client: Client, message: str):
        try:
            await asyncio.wait_for(client.send(message), timeout=self.SEND_TIMEOUT)
        except ConnectionError:
            # Cliente zombie (desconectado): se limpia atómicamente
            # del topic para no retener referencias indefinidamente.
            if topic in self.topics:
                self.topics[topic].discard(client)
        except asyncio.TimeoutError:
            # Suscriptor lento: se descarta este envío puntual, pero
            # no se desconecta al cliente ni se bloquea a los demás.
            pass

    async def publish(self, topic: str, message: str):
        if topic not in self.topics:
            return
        # Snapshot inmutable: evita el error "Set changed size during
        # iteration" si un callback modifica self.topics[topic] en caliente.
        snapshot = list(self.topics[topic])
        # Envío concurrente: un suscriptor lento ya no bloquea
        # (backpressure) la entrega al resto.
        await asyncio.gather(
            *(self._send_safe(topic, client, message) for client in snapshot)
        )
