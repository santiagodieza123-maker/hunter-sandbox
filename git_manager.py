import subprocess
import argparse
from pathlib import Path

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Comando fallo: {cmd}\nStderr: {res.stderr}")
    return res.stdout.strip()

def setup_branch(repo_url, repo_dir, issue_id):
    path = Path(repo_dir).resolve()
    if not path.exists():
        print(f"[GIT] Clonando {repo_url} en {path}...")
        run_cmd(["git", "clone", repo_url, str(path)])

    # Cast estricto a entero para sanitizar el ID
    branch_name = f"fix/issue-{int(issue_id)}"
    print(f"[GIT] Creando rama {branch_name}...")
    run_cmd(["git", "checkout", "-B", branch_name], cwd=str(path))
    return branch_name

def create_pr(repo_dir, issue_id, title, body):
    path = Path(repo_dir).resolve()
    print("[GIT] Agregando cambios y commit...")
    run_cmd(["git", "add", "."], cwd=str(path))
    
    commit_msg = f"fix: resolve issue #{int(issue_id)} -via OpenCode"
    run_cmd(["git", "commit", "-m", commit_msg], cwd=str(path))

    print("[GIT] Enviando Pull Request...")
    cmd_pr = [
        "gh", "pr", "create",
        "--title", title,
        "--body", body,
        "--fill",
        "--" # Obliga a gh a interpretar todo lo posterior como strings, no como flags
    ]
    out = run_cmd(cmd_pr, cwd=str(path))
    print(f"[PR] Pull Request creado con exito: {out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenCode Git Manager")
    parser.add_argument("--action", choices=["branch", "pr"], required=True)
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--repo-url", required=False)
    parser.add_argument("--title", required=False)
    parser.add_argument("--body", required=False)
    args = parser.parse_args()

    if args.action == "branch":
        setup_branch(args.repo_url, args.repo_dir, args.issue)
    elif args.action == "pr":
        create_pr(args.repo_dir, args.issue, args.title, args.body)
