import asyncio
import pytest
from transaction_manager import TransactionManager

@pytest.mark.asyncio
async def test_cross_resource_deadlock_prevention():
    tm = TransactionManager()

    async def tx1_work():
        await asyncio.sleep(0.05)
        return 'tx1_ok'

    async def tx2_work():
        await asyncio.sleep(0.05)
        return 'tx2_ok'

    # Tx1 adquiere [A, B] y Tx2 adquiere [B, A] simultáneamente
    # En código no determinístico esto entra en Deadlock
    try:
        t1 = asyncio.create_task(tm.execute_transaction('tx1', ['res_A', 'res_B'], tx1_work))
        t2 = asyncio.create_task(tm.execute_transaction('tx2', ['res_B', 'res_A'], tx2_work))
        
        # Debe completar holgadamente en menos de 1 segundo si no hay deadlock
        res1, res2 = await asyncio.wait_for(asyncio.gather(t1, t2), timeout=1.0)
        assert res1 == 'tx1_ok'
        assert res2 == 'tx2_ok'
    except asyncio.TimeoutError:
        pytest.fail('DEADLOCK DETECTADO: Las transacciones concurrentes quedaron bloqueadas indefinidamente.')

@pytest.mark.asyncio
async def test_lock_release_on_payload_exception():
    tm = TransactionManager()

    async def failing_work():
        raise RuntimeError('Fallo forzado en negocio')

    async def recovery_work():
        return 'recovery_ok'

    # Ejecutar transacción que revienta
    with pytest.raises(RuntimeError):
        await tm.execute_transaction('tx_fail', ['res_X', 'res_Y'], failing_work)

    # La siguiente transacción sobre los mismos recursos NO debe quedarse bloqueada
    try:
        res = await asyncio.wait_for(
            tm.execute_transaction('tx_recover', ['res_X', 'res_Y'], recovery_work),
            timeout=0.5
        )
        assert res == 'recovery_ok'
    except asyncio.TimeoutError:
        pytest.fail('RECURSO HUERFANO: Los locks no fueron liberados tras la excepcion.')
