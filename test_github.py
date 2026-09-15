import os
import sys
from github import Github, Auth

token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("[!] ERROR: GITHUB_TOKEN no detectada.")
    sys.exit(1)

auth = Auth.Token(token)
gh = Github(auth=auth)

user = gh.get_user()
print(f"[+] Conexión exitosa con PyGithub. Autenticado como: {user.login}")
