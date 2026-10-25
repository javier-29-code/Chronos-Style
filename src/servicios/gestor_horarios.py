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
        
    def actualizar(self, horario_original, horario_nuevo):
        """Reemplaza un horario únicamente si no genera conflictos.

        Devuelve:
        - Lista vacía: modificación realizada.
        - Lista de conflictos: se conserva el horario original.
        """
        if not isinstance(horario_original, Horario):
            raise ValueError(
                "El horario original debe ser un objeto Horario."
            )

        if not isinstance(horario_nuevo, Horario):
            raise ValueError(
                "El nuevo horario debe ser un objeto Horario."
            )

        if horario_original not in self._horarios:
            raise ValueError(
                "El horario original no está registrado."
            )

        if (
            horario_nuevo is not horario_original
            and horario_nuevo in self._horarios
        ):
            raise ValueError(
                "El nuevo horario ya está registrado."
            )

        # El horario que vamos a reemplazar no debe provocar
        # un conflicto consigo mismo.
        otros_horarios = [
            horario
            for horario in self._horarios
            if horario is not horario_original
        ]

        conflictos = []

        for restriccion in self._restricciones:
            conflictos.extend(
                restriccion.verificar(
                    horario_nuevo,
                    otros_horarios,
                )
            )

        if conflictos:
            return conflictos

        posicion = self._horarios.index(horario_original)
        self._horarios[posicion] = horario_nuevo

        return []