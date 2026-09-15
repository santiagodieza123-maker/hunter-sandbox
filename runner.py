import subprocess
import json
import argparse
import shlex
from pathlib import Path

def run_in_sandbox(repo_path, test_cmd, lint_file=None):
    repo_absolute = str(Path(repo_path).resolve())
    mount_arg = repo_absolute + ":/workspace"

    lint_result = {"status": "skipped", "output": ""}
    if lint_file:
        # Ejecución directa sin invocar la shell
        cmd_lint = ["docker", "run", "--rm", "-v", mount_arg, "opencode-sandbox:latest", "pyright", lint_file]
        res = subprocess.run(cmd_lint, capture_output=True, text=True)
        lint_result["status"] = "passed" if res.returncode == 0 else "failed"
        lint_result["output"] = res.stdout + res.stderr

    # Shlex divide el comando en una lista segura, anulando inyecciones lógicas (;)
    safe_test_cmd = shlex.split(test_cmd)
    cmd_test = ["docker", "run", "--rm", "--network", "none", "-v", mount_arg, "opencode-sandbox:latest"] + safe_test_cmd
    res_test = subprocess.run(cmd_test, capture_output=True, text=True)

    return {
        "lint": lint_result,
        "tests": {
            "exit_code": res_test.returncode,
            "passed": res_test.returncode == 0,
            "stdout": res_test.stdout,
            "stderr": res_test.stderr
        }
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--cmd", required=True)
    parser.add_argument("--lint-file", required=False, default=None)
    args = parser.parse_args()
    print(json.dumps(run_in_sandbox(args.repo, args.cmd, args.lint_file), indent=2))
