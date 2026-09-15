import os
import subprocess
from dotenv import load_dotenv
from github import Github, Auth, GithubException

class GitHubManager:
    def __init__(self, repo_name: str):
        """
        repo_name debe tener el formato: 'dueño/nombre-repo'
        """
        load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("Falta GITHUB_TOKEN en el archivo .env")

        self.auth = Auth.Token(self.token)
        self.gh = Github(auth=self.auth)
        self.repo_name = repo_name
        self.repo = self.gh.get_repo(repo_name)

    def print_info(self):
        print(f"Repositorio cargado: {self.repo.full_name}")
        print(f"Rama por defecto: {self.repo.default_branch}")

    def clone_repository(self, target_dir: str) -> str:
        """Clona el repositorio en una carpeta local usando autenticación por token."""
        if os.path.exists(target_dir):
            print(f"El directorio '{target_dir}' ya existe. Omitiendo clonación.")
            return target_dir

        clone_url = f"https://x-access-token:{self.token}@github.com/{self.repo_name}.git"
        print(f"Clonando {self.repo_name} en {target_dir}...")
        cmd = ["git", "clone", clone_url, target_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Error clonando repositorio: {result.stderr}")

        print("Clonación completada con éxito.")
        return target_dir

    def create_branch(self, work_dir: str, branch_name: str):
        """Crea y se mueve a una nueva rama de trabajo en el repositorio clonado."""
        cmd = ["git", "-C", work_dir, "checkout", "-b", branch_name]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Error creando la rama '{branch_name}': {result.stderr}")

        print(f"Rama '{branch_name}' creada y activada correctamente.")

    def push_and_create_pr(self, work_dir: str, branch_name: str, pr_title: str, pr_body: str) -> str:
        """
        Hace commit, push a GitHub y abre el Pull Request de forma autónoma.
        """
        try:
            # 1. Configurar autor local por si la máquina no tiene git global
            subprocess.run(["git", "-C", work_dir, "config", "user.name", "Hunter-Agent"], check=True)
            subprocess.run(["git", "-C", work_dir, "config", "user.email", "hunter-agent@auto.dev"], check=True)

            # 2. Stage y Commit
            subprocess.run(["git", "-C", work_dir, "add", "."], check=True)
            subprocess.run(["git", "-C", work_dir, "commit", "-m", f"fix: {pr_title}"], check=True)

            # 3. Push a la rama remota
            print(f"Subiendo cambios a la rama '{branch_name}' en GitHub...")
            subprocess.run(["git", "-C", work_dir, "push", "-u", "origin", branch_name], check=True)

            # 4. Crear Pull Request vía API
            base_branch = self.repo.default_branch
            print(f"Abriendo Pull Request contra '{base_branch}'...")
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=base_branch
            )
            print(f"¡Pull Request creado exitosamente!")
            return pr.html_url

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Fallo en comando de Git: {e}")
        except GithubException as e:
            raise RuntimeError(f"Fallo en la API de GitHub: {e.data.get('message', str(e))}")
