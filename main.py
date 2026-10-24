import queue
import threading
import logging
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from git_manager import GitManager


# Importa o watcher que você acabou de arrumar
from watcher import RepoWatcher

# Configuração básica de log para ver as mensagens no terminal
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Fila que conecta o Watcher (background) com a GUI (principal)
event_q = queue.Queue()

def on_change(file_path: Path, kind: str):
    # O watcher chama isso. Só empilha na fila e não trava.
    event_q.put(file_path)



def gui_loop(git):
    root = tk.Tk()
    root.withdraw() # Esconde a janela principal vazia

    def check_queue():
        paths = set()
        try:
            # Pega todos os arquivos que mudaram desde a última checagem
            while True:
                paths.add(event_q.get_nowait())
        except queue.Empty:
            pass

        if paths:
            msg = f"{len(paths)} arquivo(s) mudaram.\nEnviar para o GitHub?"
            if messagebox.askyesno("Git Auto-Pusher", msg):
                git.commit_and_push(f"manual: {len(paths)} arquivo(s)")
            else:
                print("❌ Envio cancelado pelo usuário.")

        # Fica verificando a fila a cada 1 segundo (1000 ms)
        root.after(1000, check_queue)

    root.after(1000, check_queue) # Inicia a checagem
    root.mainloop()

if __name__ == "__main__":
    # ⚠️ COLOQUE AQUI O CAMINHO DA PASTA QUE VOCÊ QUER MONITORAR
    # (Crie uma pasta de teste se não quiser usar seu repo real ainda)
    CAMINHO_DA_PASTA = "/home/violet/auto-git-pusher-main/" 

    print(f" Monitorando a pasta: {CAMINHO_DA_PASTA}")
    
    # Instancia o Git falso

    # 1. Inicia o Watcher na thread secundária
    watcher = RepoWatcher(
        repo_path=CAMINHO_DA_PASTA, 
        on_change=on_change, 
        ignore_patterns=[".git", ".venv", "__pycache__"]
    )
    watcher.start()
    git = GitManager("/home/violet/auto-git-pusher-main/")
    # 2. Inicia a GUI
    try:
        # A GUI roda na thread principal (isso evita bugs no Tkinter)
        gui_loop(git)
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        watcher.stop()