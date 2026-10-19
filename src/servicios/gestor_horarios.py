# servicios/gestor_horarios.py
# GestorHorarios guarda la lista de horarios y, antes de agregar uno nuevo,
# le pregunta a cada Restriccion si hay choques.
# Si hay choques, NO lo agrega y devuelve los ConflictoHorario encontrados.

from modelos.horario import Horario
from modelos.restriccion import RestriccionDocente, RestriccionAula


class GestorHorarios:
    def __init__(self, restricciones=None):
        # restricciones: lista de objetos Restriccion.
        # Si no se pasa nada, se usan las dos reglas por defecto.
        if restricciones is None:
            restricciones = [RestriccionDocente(), RestriccionAula()]
        self._restricciones = list(restricciones)
        self._horarios = []

    # ---------- Consulta ----------
    def listar(self):
        # Devolvemos una COPIA para que nadie modifique la lista por fuera
        return list(self._horarios)

    def cantidad(self):
        return len(self._horarios)

    # ---------- Operaciones ----------
    def agregar(self, horario):
        # Devuelve la lista de conflictos:
        #   - lista vacía  -> el horario se agregó
        #   - con elementos -> NO se agregó (choca con alguno existente)
        if not isinstance(horario, Horario):
            raise ValueError("Solo se pueden agregar objetos Horario")
        if horario in self._horarios:
            raise ValueError("Ese horario ya está en la lista")

        # Juntamos los conflictos de TODAS las restricciones
        conflictos = []
        for restriccion in self._restricciones:
            conflictos.extend(restriccion.verificar(horario, self._horarios))

        if not conflictos:
            self._horarios.append(horario)
        return conflictos

    def eliminar(self, horario):
        # Quita un horario de la lista; error si no estaba
        if horario not in self._horarios:
            raise ValueError("Ese horario no está en la lista")
        self._horarios.remove(horario)