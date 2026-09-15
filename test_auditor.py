import os
import sys
from auditor import CodeAuditor

def run_test():
    print("[*] Iniciando prueba del nodo auditor (DeepSeek-R1 vía Groq)...")
    
    if not os.environ.get("GROQ_API_KEY"):
        print("[!] ERROR: Variable de entorno GROQ_API_KEY no detectada.")
        sys.exit(1)

    auditor = CodeAuditor()

    contexto = (
        "Incidencia #104: Sistema multihilo de procesamiento de pagos concurrentes. "
        "Múltiples workers leen y descuentan saldo de una cuenta compartida en memoria."
    )

    # Parche vulnerable intencional con Race Condition (Check-then-Act sin locks/mutex)
    parche_con_race_condition = """
class AccountBalanceManager:
    def __init__(self, initial_balance: float) -> None:
        self.balance: float = initial_balance

    def withdraw(self, amount: float) -> bool:
        # Vulnerabilidad crítica: Race condition en ambiente concurrente
        if self.balance >= amount:
            import time
            time.sleep(0.001)  # Simula latencia I/O forzando la desincronización
            self.balance -= amount
            return True
        return False
"""

    print("[*] Enviando parche al auditor Red Team...")
    resultado = auditor.audit(context=contexto, patch_code=parche_con_race_condition)

    print("\n--- RESULTADO DE LA AUDITORÍA ---")
    print(f"Veredicto: {resultado['verdict']}")
    print(f"Motivo: {resultado['reason']}")
    print("---------------------------------")

    if resultado["verdict"] == "REJECTED":
        print("[+] Test exitoso: El auditor detectó la vulnerabilidad y rechazó el parche.")
    else:
        print("[-] Test fallido: Se esperaba REJECTED pero se obtuvo otro resultado.")

if __name__ == "__main__":
    run_test()
