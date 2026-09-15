import ast
import shutil
import subprocess
from pathlib import Path

class PatchError(Exception):
    """Excepción específica cuando un parche no cumple los criterios de calidad."""
    pass

def validate_python_syntax(code_content: str) -> None:
    """Aduana 1: Verifica en memoria que el código sea sintácticamente válido antes de tocar disco."""
    try:
        ast.parse(code_content)
    except SyntaxError as e:
        raise PatchError(f"Fallo sintáctico AST: {e.msg} (Línea {e.lineno}, Columna {e.offset})")

def apply_patch_atomic(file_path: Path, new_content: str) -> Path:
    """Aduana 2: Valida la sintaxis, genera respaldo .bak y escribe el código nuevo de forma atómica."""
    if not new_content.endswith("\n"):
        new_content += "\n"
    # 1. Validación sintáctica en memoria si es un archivo Python
    if file_path.suffix == ".py":
        validate_python_syntax(new_content)

    if not file_path.exists():
        raise FileNotFoundError(f"El archivo objetivo no existe: {file_path}")

    # 2. Respaldo exacto antes de modificar
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup_path)

    # 3. Escritura segura
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        rollback_patch(file_path)
        raise PatchError(f"Error al escribir en disco. Rollback ejecutado: {e}")

    return backup_path

def rollback_patch(file_path: Path) -> None:
    """Restaura el archivo original a partir del respaldo y elimina el archivo .bak."""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    if backup_path.exists():
        shutil.copy2(backup_path, file_path)
        backup_path.unlink()
        print(f"[PATCHER] Rollback ejecutado exitosamente en {file_path.name}")
    else:
        print(f"[PATCHER] Advertencia: No se encontró respaldo para {file_path.name}")

def discard_backup(file_path: Path) -> None:
    """Elimina el respaldo tras superar con éxito la suite de pruebas."""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    if backup_path.exists():
        backup_path.unlink()

def validate_git_diff_scope(repo_dir: Path, allowed_target: str) -> None:
    """Aduana 4: Verifica mediante Git que únicamente el archivo objetivo haya sido alterado."""
    cmd = ["git", "status", "--porcelain"]
    res = subprocess.run(cmd, cwd=str(repo_dir), capture_output=True, text=True)
    
    if res.returncode != 0:
        raise PatchError(f"Error al auditar estado de Git: {res.stderr}")

    modified_files = []
    for line in res.stdout.strip().splitlines():
        if not line:
            continue
        # Formato de porcelain: ' M ruta/al/archivo' o 'M  ruta/al/archivo'
        parts = line.strip().split()
        if len(parts) >= 2:
            modified_files.append(parts[-1])

    # Filtrar archivos residuales de respaldo y artefactos de compilacion/test
    ignore_prefixes = ("__pycache__", ".pytest_cache")
    ignore_extensions = (".bak", ".pyc")
    filtered_changes = [
        f for f in modified_files
        if not f.endswith(ignore_extensions) and not any(f.startswith(pref) for pref in ignore_prefixes)
    ]

    # 1. Validar cantidad de archivos modificados
    if len(filtered_changes) == 0:
        # Si no hay cambios en working tree, verificar si ya se modificó el target en commits recientes
        diff_head = subprocess.run(["git", "diff", "--name-only", "origin/main...HEAD"], cwd=str(repo_dir), capture_output=True, text=True)
        recent = [f for f in diff_head.stdout.strip().splitlines() if f and not f.endswith(".bak")]
        if len(recent) == 1 and Path(recent[0]).name == Path(allowed_target).name:
            return
        raise PatchError(f"Sin cambios detectados en el repositorio para el archivo objetivo: {allowed_target}")

    if len(filtered_changes) > 1:
        raise PatchError(f"Alcance excedido: Se detectaron cambios colaterales en múltiples archivos: {filtered_changes}")

    # 2. El archivo modificado debe coincidir exactamente con el target autorizado
    changed_file = Path(filtered_changes[0]).name
    target_name = Path(allowed_target).name
    if changed_file != target_name:
        raise PatchError(f"Archivo modificado no autorizado: {changed_file} (Esperado: {target_name})")

    # 3. Bloqueo explícito de alteración de tests
    if "test" in changed_file.lower():
        raise PatchError(f"Violación de seguridad: El parche intentó modificar el archivo de pruebas '{changed_file}'.")
