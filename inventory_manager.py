import asyncio
from typing import Dict

class InsufficientStockError(Exception):
    pass

class PaymentError(Exception):
    pass

class Database:
    def __init__(self, initial_stock: Dict[str, int]):
        self._stock = initial_stock

    def get_stock(self, item_id: str) -> int:
        return self._stock.get(item_id, 0)

    def set_stock(self, item_id: str, amount: int) -> None:
        self._stock[item_id] = amount

class MockPaymentGateway:
    async def charge(self, user_id: str, amount: float) -> bool:
        # Latencia asincrona forzada para maximizar la ventana de race condition
        await asyncio.sleep(0.01)
        return True

class InventoryManager:
    def __init__(self, db: Database, payment_gateway: MockPaymentGateway):
        self.db = db
        self.payment_gateway = payment_gateway

    async def purchase_item(self, user_id: str, item_id: str, quantity: int, unit_price: float = 10.0) -> bool:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        # VULNERABILIDAD: Check no atomico (TOCTOU)
        current_stock = self.db.get_stock(item_id)
        if current_stock < quantity:
            raise InsufficientStockError("Not enough stock available")

        # Ventana de desincronizacion: el control cede el hilo de ejecucion
        await self.payment_gateway.charge(user_id, unit_price * quantity)

        # Act no atomico: actualizacion con estado obsoleto
        self.db.set_stock(item_id, current_stock - quantity)
        return True
