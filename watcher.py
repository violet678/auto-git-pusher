
import logging
import os
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger(__name__)


class RepoEventHandler(FileSystemEventHandler):
    def __init__(self, repo_path: Path, on_change, ignore_patterns=None):
        super().__init__()
        self.repo_path = repo_path.resolve()
        self.on_change = on_change
        self.ignore_patterns = ignore_patterns or []

    def _is_ignored(self, path: Path) -> bool:
        # 1) pasta .git e subpastas — sempre ignorar
        try:
            path.resolve().relative_to(self.repo_path)
        except ValueError:
            return True  # fora do repo, ignora

        parts = path.resolve().relative_to(self.repo_path).parts
        if parts and parts[0] == ".git":
            return True

        # 2) padrões do config (nomes simples; para glob real, use fnmatch)
        name = path.name
        for pat in self.ignore_patterns:
            if pat == name or (pat.startswith("*.") and name.endswith(pat[1:])):
                return True
        return False

    def _handle(self, event: FileSystemEvent, kind: str):
        if event.is_directory:
            return
        path = Path(os.fsdecode(event.src_path))
        if self._is_ignored(path):
            log.debug("ignorado (%s): %s", kind, path)
            return
        log.info("evento %s: %s", kind, path)
        self.on_change(path, kind)

    # eventos que interessam (Nível 1: created + moved)
    def on_created(self, event):
        self._handle(event, "created")

    def on_moved(self, event):
        # No moved, o arquivo relevante é o destino
        if not event.is_directory:
            path = Path(os.fsdecode(event.dest_path))
            if not self._is_ignored(path):
                log.info("evento moved: %s -> %s", event.src_path, path)
                self.on_change(path, "moved")

    # Nível 2 vai usar on_modified — deixei pronto mas desligado
    def on_modified(self, event):
        self._handle(event, "modified")


class RepoWatcher:
    def __init__(self, repo_path: str | Path, on_change, ignore_patterns=None):
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.handler = RepoEventHandler(
            self.repo_path, on_change, ignore_patterns
        )
        self.observer = Observer()

    def start(self):
        self.observer.schedule(
            self.handler, str(self.repo_path), recursive=True
        )
        self.observer.start()
        log.info("observando %s (recursivo)", self.repo_path)

    def stop(self):
        self.observer.stop()
        self.observer.join()
        log.info("watcher encerrado")