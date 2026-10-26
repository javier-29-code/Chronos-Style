"""Almacena los objetos disponibles para la planificación académica."""

from modelos.asignatura import Asignatura
from modelos.docente import Docente
from modelos.aula import Aula
from modelos.paralelo import Paralelo

import sqlite3

class GestorCatalogos:
    """Gestiona asignaturas, docentes y aulas en memoria."""

    def __init__(self, repositorio_aulas=None):
        self._asignaturas = []
        self._docentes = []
        self._paralelos = []

        self._repositorio_aulas = repositorio_aulas

        self._aulas = (
            repositorio_aulas.listar()
            if repositorio_aulas is not None
            else []
        )

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
        if not isinstance(aula, Aula):
            raise ValueError(
                "Solo se pueden agregar objetos Aula."
            )

        identificador = self._normalizar_identificador(
            aula.id_aula,
            "El identificador del aula",
        )

        if any(
            existente.id_aula.strip().casefold() == identificador
            for existente in self._aulas
        ):
            raise ValueError(
                "Ya existe un aula con ese identificador."
            )

        # Guardamos antes de modificar la lista en memoria.
        if self._repositorio_aulas is not None:
            try:
                self._repositorio_aulas.guardar(aula)
            except sqlite3.Error as error:
                raise ValueError(
                    f"No se pudo guardar el aula: {error}"
                ) from error

        self._aulas.append(aula)

    def listar_aulas(self):
        return list(self._aulas)
    
        # ---------- Paralelos ----------

    def agregar_paralelo(self, paralelo):
        if not isinstance(paralelo, Paralelo):
            raise ValueError(
                "Solo se pueden agregar objetos Paralelo."
            )

        codigo = self._normalizar_identificador(
            paralelo.codigo,
            "El código del paralelo",
        )

        if any(
            existente.codigo.strip().casefold() == codigo
            for existente in self._paralelos
        ):
            raise ValueError(
                "Ya existe un paralelo con ese código."
            )

        self._paralelos.append(paralelo)

    def listar_paralelos(self):
        return list(self._paralelos)

    # ---------- Validación común ----------

    @staticmethod
    def _normalizar_identificador(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{campo} debe ser texto no vacío.")

        return valor.strip().casefold()