import subprocess
import os

def pack_repository(repo_path: str, output_file: str = "repo_context.xml") -> bool:
    """Empaqueta el repositorio completo en un solo archivo XML usando Repomix."""
    full_output_path = os.path.join(repo_path, output_file)
    print(f"[*] Empaquetando repositorio en: {repo_path}...")
    try:
        # Clavamos la versión exacta para evitar Supply Chain Attacks
        result = subprocess.run(
            ["npx", "--yes", "repomix@1.14.0", "--style", "xml", "--output", output_file],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[+] Firme. Archivo de contexto generado en: {full_output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Error al empaquetar el repo:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("[-] Error: 'npx' no está disponible en el PATH del sistema.")
        return False

if __name__ == "__main__":
    pack_repository(".")
