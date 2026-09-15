import os
import json
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

import patcher

def validate_api_key(api_key: str) -> str:
    """Filtro estricto de credenciales sin valores de fallback inseguros."""
    if not api_key or not api_key.strip():
        raise ValueError("[CEREBRO] Error fatal: API Key nula o vacía.")
    
    if "tu_api_key" in api_key.lower():
        raise ValueError("[CEREBRO] Error fatal: API Key placeholder detectada.")
        
    return api_key.strip()

def get_available_keys() -> list[str]:
    """Recupera todas las llaves configuradas en el .env."""
    load_dotenv(override=True)
    keys = []
    for i in range(1, 10):
        k = os.getenv(f"GEMINI_KEY_{i}")
        if k and "tu_api_key" not in k.lower():
            keys.append(k.strip())
    
    fallback = os.getenv("GEMINI_API_KEY")
    if fallback and "tu_api_key" not in fallback.lower() and fallback not in keys:
        keys.append(fallback.strip())
        
    if not keys:
        raise ValueError("[CEREBRO] Error fatal: No se hallaron API Keys válidas en el .env.")
    return keys

def call_gemini_with_retry(prompt: str, max_retries: int = 4) -> str:
    """Ejecuta la llamada aplicando rotación de llaves y backoff ante errores 503/429."""
    keys = get_available_keys()
    key_idx = 0
    delay = 2

    for attempt in range(1, max_retries + 1):
        current_key = keys[key_idx % len(keys)]
        client = genai.Client(api_key=current_key)
        
        try:
            chat = client.chats.create(
                model="gemini-3.1-flash-lite",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            response = chat.send_message(prompt)
            return response.text
        except APIError as e:
            # Captura 503 (servidor saturado) o 429 (rate limit)
            if e.code in (503, 429):
                print(f"[!] Aviso API ({e.code}): Servidor saturado. Reintento {attempt}/{max_retries} en {delay}s...")
                time.sleep(delay)
                delay *= 2
                key_idx += 1  # Rota a la siguiente llave
            else:
                raise e
        except Exception as e:
            raise e

    raise RuntimeError("[CEREBRO] Límite de reintentos alcanzado. El clúster no respondió.")

def generate_and_apply_patch(issue_description: str, repo_dir: Path, target_relative_path: str) -> Path:
    """Genera el parche estructurado en JSON y lo inyecta atómicamente."""
    full_target_path = (repo_dir / target_relative_path).resolve()

    if not full_target_path.exists():
        raise FileNotFoundError(f"Archivo objetivo no encontrado: {full_target_path}")

    with open(full_target_path, "r", encoding="utf-8") as f:
        current_code = f.read()

    prompt = f"""Eres OpenCode, un ingeniero de software senior enfocado en seguridad y calidad de código.
Debes solucionar el siguiente problema técnico aplicando las mejores prácticas:

<problema>
{issue_description}
</problema>

<archivo_original ruta="{target_relative_path}">
{current_code}
</archivo_original>

Instrucciones estrictas:
1. Devuelve ÚNICAMENTE un objeto JSON válido.
2. No incluyas explicaciones en lenguaje natural ni bloques markdown ```json.
3. El código modificado debe ser completo y funcional para el archivo completo.

Esquema JSON requerido:
{{
  "target_file": "{target_relative_path}",
  "patched_code": "código completo corregido aquí"
}}
"""

    print(f"[*] Solicitando parche correctivo para {target_relative_path} a Gemini 3.1 Flash Lite...")
    raw_response = call_gemini_with_retry(prompt)

    try:
        data = json.loads(raw_response)
        patched_code = data["patched_code"]
    except (json.JSONDecodeError, KeyError) as e:
        raise patcher.PatchError(f"El modelo no devolvió una estructura JSON válida: {e}")

    backup_path = patcher.apply_patch_atomic(full_target_path, patched_code)
    print(f"[+] Parche aplicado atómicamente en {target_relative_path}. Respaldo creado en {backup_path.name}")
    return backup_path

if __name__ == "__main__":
    base_dir = Path.home() / "bounty_hunter"
    mock_file = base_dir / "mock_project" / "main.py"
    
    if mock_file.exists():
        issue_test = "El archivo main.py debe imprimir 'Hello Secure World' en vez de cualquier otro texto."
        try:
            bak = generate_and_apply_patch(issue_test, base_dir / "mock_project", "main.py")
            print("[+] Integración superada con éxito.")
        except Exception as err:
            print(f"[-] Error en el proceso: {err}")
    else:
        print(f"[-] No se encontró {mock_file} para ejecutar la prueba.")
