import pytest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from transaction_manager import TransactionManager

def test_high_concurrency_race_condition():
    # 20 hilos intentando debitar 5 unidades simultáneas de un balance de 100
    manager = TransactionManager({'acc_a': 100.0, 'acc_b': 0.0})
    
    def worker():
        for _ in range(5):
            manager.transfer('acc_a', 'acc_b', 1.0)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(20)]
        for f in futures:
            f.result()

    assert manager.balances['acc_a'] == 0.0
    assert manager.balances['acc_b'] == 100.0

def test_batch_rollback_atomicity():
    manager = TransactionManager({'acc_a': 50.0, 'acc_b': 10.0, 'acc_c': 0.0})
    batch = [
        ('acc_a', 'acc_c', 30.0),
        ('acc_b', 'acc_c', 20.0), # Fallará porque balance es 10.0
    ]
    with pytest.raises(ValueError):
        manager.batch_process(batch)
    
    # Debe restaurar estrictamente los estados iniciales
    assert manager.balances['acc_a'] == 50.0
    assert manager.balances['acc_b'] == 10.0
    assert manager.balances['acc_c'] == 0.0
