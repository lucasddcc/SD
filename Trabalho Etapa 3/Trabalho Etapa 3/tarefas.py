# tarefas.py
import threading

class ListaTarefas:
    def __init__(self):
        self.tarefas = []
        self.lock = threading.Lock()

    def adicionar(self, tarefa):
        with self.lock:
            self.tarefas.append(tarefa)
            return f"Tarefa adicionada: {tarefa}"

    def remover(self, tarefa):
        with self.lock:
            if tarefa in self.tarefas:
                self.tarefas.remove(tarefa)
                return f"Tarefa removida: {tarefa}"
            return f"Tarefa não encontrada: {tarefa}"

    def listar(self):
        with self.lock:
            return "\n".join(f"{i+1}. {t}" for i, t in enumerate(self.tarefas)) or "Lista vazia."

    def editar(self, antigo, novo):
        with self.lock:
            if antigo in self.tarefas:
                index = self.tarefas.index(antigo)
                self.tarefas[index] = novo
                return f"Tarefa editada: {antigo} -> {novo}"
            return f"Tarefa não encontrada: {antigo}"
