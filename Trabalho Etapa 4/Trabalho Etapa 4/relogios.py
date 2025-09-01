# relogios.py
from typing import Dict

class LamportClock:
    def __init__(self, initial: int = 0):
        self.time = initial

    def tick(self) -> int:
        """Evento local/envio."""
        self.time += 1
        return self.time

    def receive(self, other: int) -> int:
        """Recebimento de mensagem com timestamp de Lamport."""
        if other is None:
            return self.tick()
        self.time = max(self.time, int(other)) + 1
        return self.time

    def now(self) -> int:
        return self.time


class VectorClock:
    """
    Relógio vetorial com dicionário dinâmico {process_id: counter}.
    Permite operar sem lista fixa de participantes.
    """
    def __init__(self, my_id: str):
        self.my_id = my_id
        self.clock: Dict[str, int] = {}

    def tick(self) -> Dict[str, int]:
        """Evento local/envio."""
        self.clock[self.my_id] = self.clock.get(self.my_id, 0) + 1
        return self.snapshot()

    def merge(self, other: Dict[str, int] | None) -> Dict[str, int]:
        """Recebimento: merge (max) e tick local."""
        if other:
            for pid, val in other.items():
                self.clock[pid] = max(self.clock.get(pid, 0), int(val))
        return self.tick()

    def snapshot(self) -> Dict[str, int]:
        return dict(self.clock)
