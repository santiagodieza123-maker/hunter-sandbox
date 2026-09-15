import json

task_config = {
    "number": 8,
    "title": "BUG: Race Condition (TOCTOU) and Inventory Overselling in Async Checkout",
    "repo": "santiagodieza123-maker/hunter-sandbox",
    "target_file": "inventory_manager.py",
    "test_cmd": "pytest -v tests/test_inventory.py",
    "prompt_context": """### Vulnerabilidad Critica: Condicion de Carrera (TOCTOU) en purchase_item
El metodo `purchase_item(user_id, item_id, quantity, unit_price)` en `inventory_manager.py` presenta una condicion de carrera Check-Then-Act al consultar el stock (`db.get_stock`) y luego ceder el control en la llamada asincrona `await self.payment_gateway.charge(...)` antes de actualizar el stock (`db.set_stock`).

Bajo cargas concurrentes paralelas, multiples corrutinas observan el mismo stock disponible y cobran al usuario, provocando sobreventa masiva e inventario negativo.

### Requisitos Obligatorios del Parche:
1. Implementar sincronizacion asincrona (`asyncio.Lock`) para serializar el ciclo critico de verificacion, cobro y actualizacion de stock.
2. Si el stock es insuficiente (< quantity), debe lanzar `InsufficientStockError` de inmediato sin llamar al gateway de pagos.
3. No alterar las firmas publicas de metodos ni clases existentes para mantener compatibilidad total con la suite de pruebas.
4. El codigo debe ser 100% thread-safe y coroutine-safe en entornos asyncio."""
}

with open("task.json", "w", encoding="utf-8") as f:
    json.dump(task_config, f, indent=2, ensure_ascii=False)

print("[+] task.json configurado con exito para Issue #8.")
