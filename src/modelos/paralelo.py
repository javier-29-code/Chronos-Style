from modelos.estudiante import Estudiante


class Paralelo:
    """Conjunto de estudiantes que recibe una programación de clases."""

    def __init__(self, codigo, carrera, semestre, letra):
        self._codigo = self._validar_texto(codigo, "El código")
        self._carrera = self._validar_texto(carrera, "La carrera")

        if (
            not isinstance(semestre, int)
            or isinstance(semestre, bool)
            or not 1 <= semestre <= 10
        ):
            raise ValueError(
                "El semestre debe ser un entero entre 1 y 10."
            )

        self._semestre = semestre
        self._letra = self._validar_texto(
            letra, "La letra del paralelo"
        ).upper()

        self._estudiantes = []

    @staticmethod
    def _validar_texto(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{campo} no puede estar vacío.")

        return valor.strip()

    @property
    def codigo(self):
        return self._codigo

    @property
    def carrera(self):
        return self._carrera

    @property
    def semestre(self):
        return self._semestre

    @property
    def letra(self):
        return self._letra

    @property
    def estudiantes(self):
        return tuple(self._estudiantes)

    def inscribir_estudiante(self, estudiante):
        if not isinstance(estudiante, Estudiante):
            raise ValueError(
                "Solo se pueden inscribir objetos Estudiante."
            )

        if (
            estudiante.carrera.strip().casefold()
            != self.carrera.casefold()
        ):
            raise ValueError(
                "El estudiante pertenece a otra carrera."
            )

        if estudiante.semestre != self.semestre:
            raise ValueError(
                "El estudiante pertenece a otro semestre."
            )

        if self.contiene_estudiante(estudiante):
            raise ValueError(
                "El estudiante ya está inscrito en este paralelo."
            )

        self._estudiantes.append(estudiante)

    def contiene_estudiante(self, estudiante):
        if not isinstance(estudiante, Estudiante):
            raise ValueError(
                "Se necesita un objeto Estudiante."
            )

        return any(
            inscrito is estudiante
            or inscrito.correo == estudiante.correo
            for inscrito in self._estudiantes
        )

    def __str__(self):
        return (
            f"{self.carrera} | "
            f"Semestre {self.semestre} | "
            f"Paralelo {self.letra}"
        )