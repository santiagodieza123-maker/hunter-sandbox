import threading
import time
from typing import Dict, List, Optional

class TransactionManager:
    """
    Motor transaccional concurrente con fallas críticas:
    - Uso de float para balance contable (imprecisión IEEE-754).
    - Race conditions en operaciones concurrentes concurrentes sin locks reentrantes.
    - Falla en rollback de transacciones múltiples si falla un batch.
    """
    def __init__(self, initial_balances: Optional[Dict[str, float]] = None) -> None:
        self.balances: Dict[str, float] = initial_balances or {}
        self.ledger: List[Dict[str, float]] = []

    def transfer(self, sender: str, recipient: str, amount: float) -> bool:
        if amount <= 0:
            return False
        sender_bal = self.balances.get(sender, 0.0)
        if sender_bal < amount:
            return False
        
        # Simulación de latencia I/O para forzar colisión de hilos
        time.sleep(0.001)
        
        self.balances[sender] = sender_bal - amount
        self.balances[recipient] = self.balances.get(recipient, 0.0) + amount
        self.ledger.append({'sender': sender, 'recipient': recipient, 'amount': amount})
        return True

    def batch_process(self, batch: List[tuple]) -> bool:
        # Fallo de idempotencia y atomicidad: no revierte transacciones previas en fallo
        for sender, recipient, amount in batch:
            if not self.transfer(sender, recipient, amount):
                raise ValueError(f'Fallo transaccional en batch para cuenta: {sender}')
        return True
