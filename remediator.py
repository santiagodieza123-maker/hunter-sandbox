import sys
from pathlib import Path
from patcher import rollback_patch, discard_backup
from brain import call_gemini_with_retry, generate_and_apply_patch
import json
import patcher
from runner import run_in_sandbox

def run_test_suite(repo_dir: Path, test_cmd: str) -> tuple[bool, str]:
    """Ejecuta los tests dentro de la jaula Docker efímera con aislamiento de red."""
    try:
        result = run_in_sandbox(repo_path=str(repo_dir), test_cmd=test_cmd)
        test_info = result.get("tests", {})
        passed = test_info.get("passed", False)
        stdout = test_info.get("stdout", "")
        stderr = test_info.get("stderr", "")
        output = stdout if passed else f"{stdout}\n{stderr}"
        return passed, output.strip()
    except Exception as e:
        return False, f"Error en el contenedor Docker del sandbox: {e}"

def repair_loop(repo_dir: Path, target_relative_path: str, issue_description: str, test_cmd: str, max_iterations: int = 3) -> bool:
    """Aduana 3: Aplica el parche y entra en bucle de autorreflexión contra la suite de pruebas."""
    full_target_path = (repo_dir / target_relative_path).resolve()

    print(f"[*] Iniciando Aduana 3 (Bucle de verificación) para {target_relative_path}...")

    # 1. Primer intento de parche
    try:
        generate_and_apply_patch(issue_description, repo_dir, target_relative_path)
    except Exception as e:
        print(f"[-] Fallo en generación inicial de parche: {e}")
        return False

    # 2. Bucle de ejecución de tests y feedback
    for iteration in range(1, max_iterations + 1):
        print(f"[*] Ejecutando validación de pruebas (Iteración {iteration}/{max_iterations})...")
        passed, test_output = run_test_suite(repo_dir, test_cmd)

        if passed:
            print(f"[+] Aduana 3 SUPERADA: Tests pasaron al 100% en la iteración {iteration}.")
            discard_backup(full_target_path)
            return True

        print(f"[!] Fallo en suite de pruebas detectado:\n--- ERROR TRACE ---\n{test_output}\n-------------------")

        if iteration == max_iterations:
            print(f"[-] Límite de iteraciones alcanzado sin éxito. Iniciando rollback de seguridad...")
            rollback_patch(full_target_path)
            return False

        # Feedback loop: Enviar stacktrace al modelo para corrección guiada
        print("[*] Reinyectando stacktrace a Gemini 3.1 Flash Lite para autorreparación...")
        with open(full_target_path, "r", encoding="utf-8") as f:
            broken_code = f.read()

        reflection_prompt = f"""Eres OpenCode. Tu intento previo de solucionar el problema provocó fallos en las pruebas.
Corrige el código asegurándote de resolver el error específico reportado por el runner.

<problema_original>
{issue_description}
</problema_original>

<codigo_con_fallo ruta="{target_relative_path}">
{broken_code}
</codigo_con_fallo>

<resultado_de_los_tests>
{test_output}
</resultado_de_los_tests>

Instrucciones estrictas:
1. Analiza el traceback y corrige exactamente el fallo indicado sin introducir regresiones.
2. Devuelve ÚNICAMENTE un JSON con la estructura requerida.

Esquema JSON:
{{
  "target_file": "{target_relative_path}",
  "patched_code": "código completo corregido aquí"
}}
"""
        try:
            raw_response = call_gemini_with_retry(reflection_prompt)
            data = json.loads(raw_response)
            patched_code = data["patched_code"]
            patcher.apply_patch_atomic(full_target_path, patched_code)
            print(f"[+] Parche de autorreparación inyectado. Reevaluando...")
        except Exception as e:
            print(f"[-] Error durante la fase de autorreflexión: {e}")
            rollback_patch(full_target_path)
            return False

    return False
