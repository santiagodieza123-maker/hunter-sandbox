import json
import subprocess
import sys
import shlex
import shutil
from pathlib import Path

BASE_DIR = Path.home() / "bounty_hunter"
TASK_FILE = BASE_DIR / "task.json"

# Lista blanca estricta e inmutable de binarios permitidos
ALLOWED_BINARIES = frozenset(["python3", "pytest", "npm", "cargo", "jest", "repomix", "flake8"])

def load_task():
    if not TASK_FILE.exists():
        raise FileNotFoundError("Fetcher no ha generado task.json todavia.")
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_test_cmd(raw_cmd: str) -> bool:
    """Filtro estricto con shlex, validación de binario y bloqueo de flags hostiles."""
    try:
        # shlex desarma el string respetando comillas, sin invocar shell
        parts = shlex.split(raw_cmd)
        if not parts:
            return False
        
        binary = parts[0]
        if binary not in ALLOWED_BINARIES:
            print(f"[ORCHESTRATOR-SEC] Ejecución denegada: Binario '{binary}' no autorizado.")
            return False
        
        # Cortafuegos 2: Bloquear inyección de código en binarios de confianza
        dangerous_flags = {"-c", "-m", "-e", "--eval", "--exec"}
        # Intersectamos los argumentos del comando con la lista negra de flags
        if set(parts) & dangerous_flags:
            print("[ORCHESTRATOR-SEC] Ejecución denegada: Bandera de inyección detectada.")
            return False
        
        # shutil.which resuelve la ruta absoluta, mitigando secuestro de PATH
        bin_path = shutil.which(binary)
        if not bin_path:
            print(f"[ORCHESTRATOR-SEC] Binario '{binary}' no hallado en el entorno.")
            return False
            
        return True
    except ValueError:
        # Falla si un atacante manda comillas malformadas o trucos de parseo
        return False

def execute_pipeline(repo_path, test_cmd, lint_file=None):
    if not validate_test_cmd(test_cmd):
        print(f"[ORCHESTRATOR] ALERTA CRÍTICA: Comando '{test_cmd}' bloqueado por política de seguridad.")
        sys.exit(1)

    task = load_task()
    issue_id = str(task.get("number", "default"))
    print(f"[ORCHESTRATOR] Iniciando pipeline para issue #{issue_id}")

    cmd_branch = [
        "python3", str(BASE_DIR / "git_manager.py"),
        "--action", "branch",
        "--repo-dir", str(repo_path),
        "--issue", issue_id
    ]
    subprocess.run(cmd_branch, check=True)

    cmd_runner = [
        "python3", str(BASE_DIR / "runner.py"),
        "--repo", str(repo_path),
        "--cmd", test_cmd
    ]
    
    if lint_file:
        cmd_runner.extend(["--lint-file", lint_file])

    print("[ORCHESTRATOR] Ejecutando auditoria y pruebas dentro del sandbox...")
    res = subprocess.run(cmd_runner, capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"[ORCHESTRATOR] Fallo al ejecutar runner.py: {res.stderr}")
        sys.exit(1)

    try:
        eval_data = json.loads(res.stdout)
    except json.JSONDecodeError:
        print(f"[ORCHESTRATOR] Error decodificando JSON: {res.stdout}")
        sys.exit(1)

    lint_passed = eval_data.get("lint", {}).get("status") != "failed"
    tests_passed = eval_data.get("tests", {}).get("passed", False)

    if lint_passed and tests_passed:
        print("[ORCHESTRATOR] Validacion EXITOSA (Lint: OK, Tests: OK)")
        print("[ORCHESTRATOR] Listo para disparar Pull Request.")
    else:
        print("[ORCHESTRATOR] Validacion FALLIDA")
        print(json.dumps(eval_data, indent=2))

if __name__ == "__main__":
    repo_dir = str(BASE_DIR / "mock_project")
    execute_pipeline(repo_dir, "python3 main.py", "main.py")
