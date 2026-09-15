import pytest
from decimal import Decimal
from billing import BillingProcessor

def test_single_item_tier_1():
    items = [{"price": 29.99, "qty": 1}]
    res = BillingProcessor.calculate_order(items)
    # 29.99 * 0.05 = 1.4995 -> Redondeo banker: 1.50
    # Total = 29.99 + 1.50 = 31.49
    assert res["subtotal"] == 29.99
    assert res["fee"] == 1.50
    assert res["total"] == 31.49

def test_tier_2_exact_boundary():
    # Exactamente 500.00 debe pagar 3.5%, es decir 17.50, total 517.50
    items = [{"price": 250.00, "qty": 2}]
    res = BillingProcessor.calculate_order(items)
    assert res["subtotal"] == 500.00
    assert res["fee"] == 17.50
    assert res["total"] == 517.50

def test_floating_point_accumulation_precision():
    items = [{"price": 0.10, "qty": 1} for _ in range(1000)]
    res = BillingProcessor.calculate_order(items)
    assert res["subtotal"] == 100.00
    assert res["fee"] == 3.50
    assert res["total"] == 103.50

def test_invalid_input_raises_exception():
    with pytest.raises(ValueError):
        BillingProcessor.calculate_order([{"price": -10.0, "qty": 1}])
    
    with pytest.raises(ValueError):
        BillingProcessor.calculate_order([{"price": 50.0, "qty": 0}])
