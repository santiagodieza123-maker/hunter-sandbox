import json

issue_payload = {
    "title": "BUG: Race Condition (TOCTOU) and Inventory Overselling in Async Checkout",
    "body": """### Summary
Under high concurrency, `inventory_manager.py` allows double-spending and overselling inventory below zero.

### Vulnerability Mechanics
The `purchase_item(user_id, item_id, quantity)` coroutine executes a non-atomic Check-Then-Act (TOCTOU):
1. Reads `available = db.get_stock(item_id)`
2. Awaits an external payment verification: `await payment_gateway.charge(user_id)`
3. Writes `db.set_stock(item_id, available - quantity)`

Because no lock or atomic CAS (Compare-And-Swap) mechanism isolates the checkout lifecycle across tasks, concurrent coroutines interleave at step 2, reading stale state and driving stock into negative balances.

### Expected Behavior
- Concurrency control must guarantee zero overselling under parallel loads (`asyncio.gather`).
- If stock is insufficient, raise `InsufficientStockError` without executing payment.
- Preserve thread-safe and task-safe execution using proper synchronization (`asyncio.Lock` per resource or atomic transaction pattern).
""",
    "target_file": "inventory_manager.py",
    "test_file": "tests/test_inventory.py"
}

with open("task_issue8.json", "w") as f:
    json.dump(issue_payload, f, indent=2)

print("[+] task_issue8.json generado exitosamente.")
