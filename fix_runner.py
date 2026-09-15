content = """import subprocess
import json
import argparse
import shlex
from pathlib import Path

def run_in_sandbox(repo_path, test_cmd, lint_file=None):
    repo_absolute = str(Path(repo_path).resolve())
    mount_arg = f"{repo_absolute}:/workspace"

    lint_result = {"status": "skipped", "output": ""}
    if lint_file:
        cmd_lint = [
            "docker", "run", "--rm",
            "-v", mount_arg,
            "-w", "/workspace",
            "-e", "PYTHONPATH=/workspace",
            "opencode-sandbox:latest",
            "pyright", lint_file
        ]
        res = subprocess.run(cmd_lint, capture_output=True, text=True)
        lint_result["status"] = "passed" if res.returncode == 0 else "failed"
        lint_result["output"] = res.stdout + res.stderr

    safe_test_cmd = shlex.split(test_cmd)
    cmd_test = [
        "docker", "run", "--rm",
        "--network", "none",
        "-v", mount_arg,
        "-w", "/workspace",
        "-e", "PYTHONPATH=/workspace",
        "opencode-sandbox:latest"
    ] + safe_test_cmd

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
"""
with open("runner.py", "w") as f:
    f.write(content)
print("[+] runner.py guardado al 100%.")
