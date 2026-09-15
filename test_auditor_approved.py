import os
import sys
from auditor import CodeAuditor

def run_approved_test():
    print("[*] Iniciando prueba de caso positivo (APPROVED) en nodo auditor...")
    
    if not os.environ.get("GROQ_API_KEY"):
        print("[!] ERROR: GROQ_API_KEY no detectada.")
        sys.exit(1)

    auditor = CodeAuditor()

    contexto = (
        "Incidencia #104: Sistema multihilo de procesamiento de transacciones concurrentes. "
        "Múltiples workers deben descontar saldo sin introducir condiciones de carrera ni saldos negativos."
    )

    # Parche corregido usando primitivas de sincronización estrictas y tipado seguro
    parche_robusto = """
import threading
from decimal import Decimal

class AccountBalanceManager:
    def __init__(self, initial_balance: Decimal) -> None:
        if initial_balance < Decimal("0.00"):
            raise ValueError("El saldo inicial no puede ser negativo.")
        self._balance: Decimal = initial_balance
        self._lock: threading.Lock = threading.Lock()

    def withdraw(self, amount: Decimal) -> bool:
        if amount <= Decimal("0.00"):
            return False
        with self._lock:
            if self._balance >= amount:
                self._balance -= amount
                return True
            return False

    @property
    def balance(self) -> Decimal:
        with self._lock:
            return self._balance
"""

    print("[*] Enviando parche corregido al auditor Red Team...")
    resultado = auditor.audit(context=contexto, patch_code=parche_robusto)

    print("\n--- RESULTADO DE LA AUDITORÍA ---")
    print(f"Veredicto: {resultado['verdict']}")
    if resultado['reason']:
        print(f"Motivo: {resultado['reason']}")
    print("---------------------------------")

    if resultado["verdict"] == "APPROVED":
        print("[+] Test exitoso: El auditor validó la sincronización con lock y aprobó el parche.")
    else:
        print(f"[-] Test fallido: Se esperaba APPROVED pero se obtuvo {resultado['verdict']}.")

if __name__ == "__main__":
    run_approved_test()
