import asyncio
from typing import Dict

class InsufficientStockError(Exception):
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
        await asyncio.sleep(0.01)
        return True

class InventoryManager:
    def __init__(self, db: Database, payment_gateway: MockPaymentGateway):
        self.db = db
        self.payment_gateway = payment_gateway
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_item_lock(self, item_id: str) -> asyncio.Lock:
        async with self._global_lock:
            if item_id not in self._locks:
                self._locks[item_id] = asyncio.Lock()
            return self._locks[item_id]

    async def purchase_item(self, user_id: str, item_id: str, quantity: int, unit_price: float = 10.0) -> bool:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        lock = await self._get_item_lock(item_id)
        async with lock:
            current_stock = self.db.get_stock(item_id)
            if current_stock < quantity:
                raise InsufficientStockError("Not enough stock available")

            success = await self.payment_gateway.charge(user_id, unit_price * quantity)
            if not success:
                return False

            self.db.set_stock(item_id, current_stock - quantity)
            return True
