import subprocess
import json
import argparse
from pathlib import Path
import os

def fetch_issue(repo, issue_number):
    # Validar que el issue sea número estrictamente
    issue_number = int(issue_number)
    cmd = ["gh", "issue", "view", str(issue_number), "-R", repo, "--json", "title,body,number,url,labels"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Error consultando GHCLI: {res.stderr}")

    data = json.loads(res.stdout)
    task = {
        "repo": repo,
        "number": data.get("number"),
        "title": data.get("title"),
        "url": data.get("url"),
        "labels": [l.get("name") for l in data.get("labels", [])],
        "prompt_context": data.get("body", "")
    }

    # Bloqueo de ataques de enlace simbólico (Symlink)
    base_dir = Path.home() / "bounty_hunter"
    base_dir.mkdir(parents=True, exist_ok=True)
    task_file = base_dir / "task.json"

    if task_file.is_symlink():
        task_file.unlink() # Destruye el enlace malicioso
        
    # Limita permisos a escritura exclusiva del dueño (0o600)
    task_file.touch(mode=0o600, exist_ok=True)
    
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, indent=2)

    print(f"Issue #{issue_number} capturado exitosamente en {task_file}")
    print(json.dumps(task, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GHCLI Issue Fetcher")
    parser.add_argument("--repo", required=True, help="Repositorio en formato owner/repo")
    parser.add_argument("--issue", required=True, type=int, help="Numero del issue")
    args = parser.parse_args()
    fetch_issue(args.repo, args.issue)
