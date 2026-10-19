# modelos/conflicto_horario.py
# Un ConflictoHorario es el REGISTRO de un choque entre dos horarios.
# No decide si hay conflicto (eso lo hace Horario / Restriccion),
# solo guarda qué horarios chocan y por qué.


class ConflictoHorario:
    def __init__(self, horario_1, horario_2, motivo):
        # horario_1, horario_2: objetos Horario que chocan
        # motivo: texto que explica el choque (ej. "Mismo docente")
        if horario_1 is None or horario_2 is None:
            raise ValueError("Se necesitan dos horarios para registrar un conflicto")
        if horario_1 is horario_2:
            raise ValueError("Un horario no puede tener conflicto consigo mismo")
        if not isinstance(motivo, str) or not motivo.strip():
            raise ValueError("El motivo del conflicto no puede estar vacío")

        self._horario_1 = horario_1
        self._horario_2 = horario_2
        self._motivo = motivo.strip()

    # ---------- Propiedades (solo lectura) ----------
    @property
    def horario_1(self):
        return self._horario_1

    @property
    def horario_2(self):
        return self._horario_2

    @property
    def motivo(self):
        return self._motivo

    # ---------- Mostrar ----------
    def mostrar_informacion(self):
        return (f"CONFLICTO: {self._motivo}\n"
                f"  - {self._horario_1}\n"
                f"  - {self._horario_2}")

    def __str__(self):
        return self.mostrar_informacion()