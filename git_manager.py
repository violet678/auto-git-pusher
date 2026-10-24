
import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class GitError(Exception):
    """Erro em operação git."""


class GitManager:
    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path).expanduser().resolve()
        if not (self.repo_path / ".git").exists():
            raise GitError(f"{self.repo_path} não é um repositório git.")

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Executa um comando git no diretório do repositório."""
        cmd = ["git", *args]
        log.debug("executando: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise GitError(
                f"git {' '.join(args)} falhou ({result.returncode}):\n"
                f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )
        return result

    def has_changes(self) -> bool:
        """Há algo para commitar? (ignora arquivos no .gitignore)"""
        result = self._run("status", "--porcelain", check=False)
        return bool(result.stdout.strip())

    def current_branch(self) -> str:
        result = self._run("rev-parse", "--abbrev-ref", "HEAD", check=False)
        return result.stdout.strip() or "main"

    def commit_and_push(self, message: str) -> bool:
        """
        Faz add, commit e push. Retorna True se algo foi enviado.
        Não levanta exceção em falha de push — só loga, para não
        matar o watcher.
        """
        if not self.has_changes():
            log.info("sem mudanças, nada a commitar")
            return False

        try:
            self._run("add", "-A")
            self._run("commit", "-m", message)
        except GitError as e:
            log.error("falha no commit: %s", e)
            return False

        try:
            self._run("push")
            log.info("push concluído: %s", message)
            return True
        except GitError as e:
            # rede caiu, conflito, sem remote, etc. — não derruba o app
            log.error("falha no push (committed localmente): %s", e)
            return False

    def is_ignored(self, path: Path) -> bool:
        """True se o caminho está no .gitignore."""
        rel = path.resolve().relative_to(self.repo_path)
        result = self._run("check-ignore", str(rel), check=False)
        return result.returncode == 0