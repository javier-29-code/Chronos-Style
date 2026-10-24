"""Almacena los objetos disponibles para la planificación académica."""

from modelos.asignatura import Asignatura
from modelos.docente import Docente
from modelos.aula import Aula


class GestorCatalogos:
    """Gestiona asignaturas, docentes y aulas en memoria."""

    def __init__(self):
        self._asignaturas = []
        self._docentes = []
        self._aulas = []

    # ---------- Asignaturas ----------

    def agregar_asignatura(self, asignatura):
        if not isinstance(asignatura, Asignatura):
            raise ValueError(
                "Solo se pueden agregar objetos Asignatura."
            )

        codigo = self._normalizar_identificador(
            asignatura.codigo, "El código de la asignatura"
        )

        # Asignatura todavía no valida su nombre en el modelo.
        self._normalizar_identificador(
            asignatura.nombre, "El nombre de la asignatura"
        )

        if any(
            existente.codigo.strip().casefold() == codigo
            for existente in self._asignaturas
        ):
            raise ValueError(
                "Ya existe una asignatura con ese código."
            )

        self._asignaturas.append(asignatura)

    def listar_asignaturas(self):
        return list(self._asignaturas)

    # ---------- Docentes ----------

    def agregar_docente(self, docente):
        # También acepta AdministradorAcademico, porque hereda de Docente.
        if not isinstance(docente, Docente):
            raise ValueError(
                "Solo se pueden agregar objetos Docente."
            )

        correo = self._normalizar_identificador(
            docente.correo, "El correo del docente"
        )

        if any(
            existente.correo.strip().casefold() == correo
            for existente in self._docentes
        ):
            raise ValueError(
                "Ya existe un docente con ese correo."
            )

        self._docentes.append(docente)

    def listar_docentes(self):
        return list(self._docentes)

    # ---------- Aulas ----------

    def agregar_aula(self, aula):
        # También acepta las clases que heredan de Aula.
        if not isinstance(aula, Aula):
            raise ValueError(
                "Solo se pueden agregar objetos Aula."
            )

        identificador = self._normalizar_identificador(
            aula.id_aula, "El identificador del aula"
        )

        if any(
            existente.id_aula.strip().casefold() == identificador
            for existente in self._aulas
        ):
            raise ValueError(
                "Ya existe un aula con ese identificador."
            )

        self._aulas.append(aula)

    def listar_aulas(self):
        return list(self._aulas)

    # ---------- Validación común ----------

    @staticmethod
    def _normalizar_identificador(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{campo} debe ser texto no vacío.")

        return valor.strip().casefold()