#!/usr/bin/env bash
set -e

TMP_DIR=$(mktemp -d)
echo "[*] Clonando sandbox en $TMP_DIR..."
git clone https://github.com/santiagodieza123-maker/hunter-sandbox.git "$TMP_DIR"
cd "$TMP_DIR"

# 1. Crear el archivo de logica con bugs sutiles
cat << 'PYEOF' > billing.py
from decimal import Decimal, ROUND_HALF_EVEN
from typing import List, Dict

class BillingProcessor:
    """
    Motor de liquidacion de facturas con descuentos escalonados y comisiones.
    Reglas de negocio:
    - Tier 1: Subtotal < 100.00 -> Comision 5% (0.05)
    - Tier 2: 100.00 <= Subtotal <= 500.00 -> Comision 3.5% (0.035)
    - Tier 3: Subtotal > 500.00 -> Comision 2% (0.02)
    - Redondeo obligatorio: Banker's Rounding (ROUND_HALF_EVEN) a 2 decimales en moneda final.
    """

    @staticmethod
    def calculate_order(items: List[Dict[str, float]]) -> Dict[str, float]:
        if not items:
            return {"subtotal": 0.0, "fee": 0.0, "total": 0.0}

        subtotal = 0.0
        for item in items:
            price = item.get("price", 0.0)
            qty = item.get("qty", 1)
            # BUG 1: Permite cantidades y precios invalidos <= 0
            subtotal += price * qty

        # BUG 2: Logica de rangos de comision con off-by-one en limites
        if subtotal < 100.0:
            fee_rate = 0.05
        elif subtotal < 500.0:  # Error: no incluye exactamente 500.0 en el tier 2
            fee_rate = 0.035
        else:
            fee_rate = 0.02

        fee = subtotal * fee_rate
        total = subtotal + fee

        # BUG 3: Uso de round() estandar de float en vez de Decimal cuantizado
        # Esto genera discrepancias en representacion IEEE 754
        return {
            "subtotal": round(subtotal, 2),
            "fee": round(fee, 2),
            "total": round(total, 2)
        }
PYEOF

# 2. Crear suite de tests que rompe con rigor
cat << 'PYEOF' > test_billing.py
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
    # Prueba de acumulacion sensible a error flotante
    items = [{"price": 0.10, "qty": 1} for _ in range(1000)]
    res = BillingProcessor.calculate_order(items)
    # 100.00 exactos -> Tier 2 (3.5% = 3.50) -> Total 103.50
    assert res["subtotal"] == 100.00
    assert res["fee"] == 3.50
    assert res["total"] == 103.50

def test_invalid_input_raises_exception():
    # Debe rechazar items con precio o cantidad <= 0
    with pytest.raises(ValueError):
        BillingProcessor.calculate_order([{"price": -10.0, "qty": 1}])
    
    with pytest.raises(ValueError):
        BillingProcessor.calculate_order([{"price": 50.0, "qty": 0}])
PYEOF

# 3. Comitear y pushear a main
git add billing.py test_billing.py
git commit -m "feat: add billing module and unit tests"
git push origin main

cd ..
rm -rf "$TMP_DIR"
echo "[+] Sandbox actualizado con modulo de facturacion complejo y tests."
