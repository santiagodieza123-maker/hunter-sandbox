import subprocess
import sys

def test_main():
    res = subprocess.run([sys.executable, 'main.py'], capture_output=True, text=True)
    assert res.stdout.strip() == 'Hello Secure World', f"Esperado 'Hello Secure World', recibido: {res.stdout.strip()}"
    print("[TEST] OK: Salida validada correctamente.")

if __name__ == '__main__':
    test_main()
