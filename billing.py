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

        subtotal_dec = Decimal("0.00")
        for item in items:
            price = Decimal(str(item.get("price", 0.0)))
            qty = Decimal(str(item.get("qty", 0.0)))
            
            if price <= 0 or qty <= 0:
                raise ValueError("Price and qty must be greater than 0")
            
            subtotal_dec += price * qty

        if subtotal_dec < Decimal("100.00"):
            fee_rate = Decimal("0.05")
        elif subtotal_dec <= Decimal("500.00"):
            fee_rate = Decimal("0.035")
        else:
            fee_rate = Decimal("0.02")

        fee_dec = subtotal_dec * fee_rate
        total_dec = subtotal_dec + fee_dec

        return {
            "subtotal": float(subtotal_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)),
            "fee": float(fee_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)),
            "total": float(total_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))
        }
