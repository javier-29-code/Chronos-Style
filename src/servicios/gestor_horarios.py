from modelos.horario import Horario
from modelos.restriccion import (
    RestriccionDocente,
    RestriccionAula,
    RestriccionParalelo,
)


class GestorHorarios:
    """Registra horarios cuando no incumplen las restricciones."""

    def __init__(self, restricciones=None):
        if restricciones is None:
            restricciones = [
                RestriccionDocente(),
                RestriccionAula(),
                RestriccionParalelo(),
            ]

        # Se inicializan siempre, se reciban o no restricciones.
        self._restricciones = list(restricciones)
        self._horarios = []

    # ---------- Consulta ----------

    def listar(self):
        return list(self._horarios)

    def cantidad(self):
        return len(self._horarios)

    # ---------- Operaciones ----------

    def agregar(self, horario):
        """Devuelve conflictos; si no hay, registra el horario."""
        if not isinstance(horario, Horario):
            raise ValueError(
                "Solo se pueden agregar objetos Horario"
            )

        if horario in self._horarios:
            raise ValueError("Ese horario ya está en la lista")

        conflictos = []

        for restriccion in self._restricciones:
            conflictos.extend(
                restriccion.verificar(horario, self._horarios)
            )

        if not conflictos:
            self._horarios.append(horario)

        return conflictos

    def eliminar(self, horario):
        if horario not in self._horarios:
            raise ValueError("Ese horario no está en la lista")

        self._horarios.remove(horario)