# modelos/restriccion.py
# Una Restriccion es una REGLA que se revisa sobre los horarios.
# La clase base ya sabe recorrer los horarios y crear los conflictos;
# cada regla concreta solo define CUÁNDO dos horarios chocan (_choca).

from modelos.conflicto_horario import ConflictoHorario  # ajusta la ruta si hace falta


class Restriccion:
    def __init__(self, nombre, motivo):
        # nombre: nombre corto de la regla
        # motivo: texto que irá en el ConflictoHorario cuando se incumpla
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre de la restricción no puede estar vacío")
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError("El motivo de la restricción no puede estar vacío")
        self._nombre = nombre.strip()
        self._motivo = motivo.strip()

    # ---------- Propiedades (solo lectura) ----------
    @property
    def nombre(self):
        return self._nombre

    @property
    def motivo(self):
        return self._motivo

    # ---------- Lógica ----------
    def _choca(self, horario_nuevo, horario_existente):
        # Cada regla concreta sobrescribe este método
        raise NotImplementedError("Cada restricción debe definir _choca()")

    def verificar(self, horario_nuevo, horarios_existentes):
        # Devuelve una lista de ConflictoHorario (vacía si se cumple la regla)
        conflictos = []
        for existente in horarios_existentes:
            if existente is horario_nuevo:
                continue  # un horario no se compara consigo mismo
            if self._choca(horario_nuevo, existente):
                conflictos.append(
                    ConflictoHorario(horario_nuevo, existente, self._motivo))
        return conflictos

    def __str__(self):
        return f"Restricción: {self._nombre}"


class RestriccionDocente(Restriccion):
    # Regla: un docente no puede tener dos clases a la vez
    def __init__(self):
        super().__init__("Docente sin choques",
                         "El docente ya tiene clase en esa franja")

    def _choca(self, horario_nuevo, horario_existente):
        return (horario_nuevo.se_solapa_con(horario_existente)
                and horario_nuevo.tiene_mismo_docente(horario_existente))


class RestriccionAula(Restriccion):
    # Regla: un aula no puede tener dos clases a la vez
    def __init__(self):
        super().__init__("Aula sin choques",
                         "El aula ya está ocupada en esa franja")

    def _choca(self, horario_nuevo, horario_existente):
        return (horario_nuevo.se_solapa_con(horario_existente)
                and horario_nuevo.tiene_misma_aula(horario_existente))
        
class RestriccionParalelo(Restriccion):
    """Un paralelo no puede recibir dos clases al mismo tiempo."""

    def __init__(self):
        super().__init__(
            "Paralelo sin choques",
            "El paralelo ya tiene clase en esa franja",
        )

    def _choca(self, horario_nuevo, horario_existente):
        return (
            horario_nuevo.se_solapa_con(horario_existente)
            and horario_nuevo.tiene_mismo_paralelo(
                horario_existente
            )
        )