import pytest
import asyncio
from inventory_manager import InventoryManager, Database, MockPaymentGateway, InsufficientStockError

@pytest.mark.asyncio
async def test_purchase_item_success():
    db = Database({"sku_gpu": 10})
    gateway = MockPaymentGateway()
    manager = InventoryManager(db, gateway)

    success = await manager.purchase_item("user_1", "sku_gpu", 2)
    assert success is True
    assert db.get_stock("sku_gpu") == 8

@pytest.mark.asyncio
async def test_purchase_item_insufficient_stock():
    db = Database({"sku_gpu": 1})
    gateway = MockPaymentGateway()
    manager = InventoryManager(db, gateway)

    with pytest.raises(InsufficientStockError):
        await manager.purchase_item("user_1", "sku_gpu", 5)
    assert db.get_stock("sku_gpu") == 1

@pytest.mark.asyncio
async def test_concurrent_purchases_race_condition():
    # 5 unidades disponibles, 20 compradores concurrentes intentando comprar 1 unidad cada uno
    initial_stock = 5
    db = Database({"sku_ram": initial_stock})
    gateway = MockPaymentGateway()
    manager = InventoryManager(db, gateway)

    async def attempt_purchase(uid: int):
        try:
            return await manager.purchase_item(f"user_{uid}", "sku_ram", 1)
        except InsufficientStockError:
            return False

    # Disparo masivo en paralelo
    results = await asyncio.gather(*[attempt_purchase(i) for i in range(20)])

    successful_purchases = sum(1 for r in results if r is True)
    final_stock = db.get_stock("sku_ram")

    # Aserciones criticas del contrato
    assert final_stock >= 0, f"Stock cayo por debajo de cero: {final_stock}"
    assert successful_purchases == initial_stock, f"Se permitieron {successful_purchases} compras pero solo habia {initial_stock} en stock"
    assert final_stock == 0, f"Stock final inconsistente: {final_stock}"
