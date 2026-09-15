import sys
import time
import subprocess
import json
from pathlib import Path
import remediator
import patcher
from auditor import CodeAuditor
from github_manager import GitHubManager

def load_task_data(base_dir: Path):
    task_file = base_dir / "task.json"
    if task_file.exists():
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Advertencia: No se pudo leer task.json: {e}")
    return None

def run_hunt(remote_repo: str = None, branch_name: str = None):
    base_dir = Path.home() / "bounty_hunter"
    task_data = load_task_data(base_dir)

    issue_number = None
    if task_data:
        print(f"[*] Tarea detectada desde task.json: #{task_data.get('number')} - {task_data.get('title')}")
        if not remote_repo and task_data.get("repo"):
            remote_repo = task_data.get("repo")
        issue_number = task_data.get("number")
        issue = task_data.get("prompt_context", "").strip()
    else:
        issue = "El script main.py debe imprimir exactamente 'Hello Secure World'. Cualquier otro texto hara fallar los tests."

    if remote_repo:
        repo = base_dir / "workspace_repo"
        if not branch_name:
            branch_name = f"autofix/patch-{int(time.time())}"

        print(f"[*] Modo Remoto Activado: {remote_repo}")
        gm = GitHubManager(remote_repo)
        gm.clone_repository(str(repo))
        gm.create_branch(str(repo), branch_name)
    else:
        repo = base_dir / "mock_project"
        print("[*] Modo Local: mock_project")

    target_file = task_data.get("target_file", "main.py") if task_data else "main.py"
    test_cmd = task_data.get("test_cmd", "python3 test_main.py") if task_data else "python3 test_main.py"

    print("=" * 50)
    print("[*] BOUNTY HUNTER INICIANDO SECUENCIA DE REMEDIACION")
    print("=" * 50)

    exito = remediator.repair_loop(repo, target_file, issue, test_cmd, max_iterations=3)

    if not exito:
        print("\n[-] Mision abortada: El parche no supero el entorno de pruebas local.")
        sys.exit(1)

    print("\n[*] Entrando a Aduana 4: Verificando rastro en Git...")
    try:
        patcher.validate_git_diff_scope(repo, target_file)
        print("[+] Aduana 4 SUPERADA: Modificacion estrictamente confinada al archivo objetivo.")
    except patcher.PatchError as e:
        print(f"\n[-] Aduana 4 FALLIDA (Brecha de seguridad): {e}")
        print("[*] El sistema detecto danos colaterales. Abortando operacion.")
        sys.exit(1)

    print("\n[*] Entrando a Aduana 5 (Red Team): Auditoria con modelo de razonamiento via Groq...")
    diff_proc = subprocess.run(
        ["git", "diff", "HEAD", target_file],
        cwd=str(repo),
        capture_output=True,
        text=True
    )
    patch_diff = diff_proc.stdout.strip()
    if not patch_diff:
        target_path = repo / target_file
        if target_path.exists():
            patch_diff = target_path.read_text(encoding="utf-8").strip()

    if not patch_diff:
        print("[-] Aduana 5 FALLIDA: No se detectaron cambios ni contenido en el archivo para auditar.")
        sys.exit(1)

    auditor = CodeAuditor()
    audit_res = auditor.audit(context=issue, patch_code=patch_diff)

    print(f"[*] Veredicto Auditor: {audit_res['verdict']}")
    if audit_res["verdict"] != "APPROVED":
        print(f"[-] Aduana 5 RECHAZADA por Red Team: {audit_res.get('reason', 'Sin motivo especificado')}")
        print("[*] Parche bloqueado antes de publicacion.")
        sys.exit(1)

    print("[+] Aduana 5 SUPERADA: Parche certificado por el Auditor Red Team.")
    print("\n[+] CACERIA EXITOSA: Parche validado por todas las aduanas.")

    if remote_repo:
        print("\n[*] Empaquetando y publicando solucion en GitHub...")
        pr_title = f"Fix issue en {target_file}"
        if issue_number:
            pr_title = f"Fix #{issue_number}: Correccion automatica en {target_file}"

        fixes_clause = f"\nFixes #{issue_number}\n" if issue_number else ""
        pr_body = (
            f"### Resumen de Remediacion Autonoma\n\n"
            f"{fixes_clause}"
            f"- **Archivo modificado:** `{target_file}`\n"
            f"- **Validacion de Tests:** Superada con `{test_cmd}` en contenedor aislado\n"
            f"- **Aduanas de Seguridad:** 1 a 5 (Auditor Red Team en Groq) aprobadas sin daños colaterales.\n\n"
            f"> Generado automaticamente por Hunter-Agent con sandboxing Docker."
        )
        pr_url = gm.push_and_create_pr(str(repo), branch_name, pr_title, pr_body, target_file=target_file)
        print(f"[+] Pull Request abierto exitosamente: {pr_url}")

if __name__ == "__main__":
    remote = sys.argv[1] if len(sys.argv) > 1 else None
    run_hunt(remote_repo=remote)
