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
        return {
            "subtotal": round(subtotal, 2),
            "fee": round(fee, 2),
            "total": round(total, 2)
        }
