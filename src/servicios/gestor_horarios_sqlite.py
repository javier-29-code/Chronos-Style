"""Gestor de horarios con almacenamiento local en SQLite."""

import sqlite3
from contextlib import closing
from pathlib import Path

from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario
from servicios.gestor_horarios import GestorHorarios


class GestorHorariosSQLite(GestorHorarios):
    """Conserva las validaciones y guarda los cambios aceptados."""

    def __init__(self, ruta, catalogos, restricciones=None):
        super().__init__(restricciones)

        self._ruta = Path(ruta)
        self._ruta.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._crear_tabla()
            self._cargar(catalogos)
        except sqlite3.Error as error:
            raise ValueError(
                f"No se pudo abrir la base de horarios: {error}"
            ) from error

    # ---------- Base de datos ----------

    def _crear_tabla(self):
        with closing(sqlite3.connect(self._ruta)) as conexion:
            with conexion:
                conexion.execute("""
                    CREATE TABLE IF NOT EXISTS horarios (
                        id INTEGER PRIMARY KEY,
                        materia TEXT NOT NULL,
                        docente_correo TEXT NOT NULL,
                        aula_codigo TEXT NOT NULL,
                        paralelo_codigo TEXT,
                        dia TEXT NOT NULL,
                        hora_inicio INTEGER NOT NULL,
                        hora_fin INTEGER NOT NULL,
                        CHECK (
                            hora_inicio >= 0
                            AND hora_fin <= 24
                            AND hora_inicio < hora_fin
                        )
                    )
                """)

    @staticmethod
    def _clave(valor):
        return valor.strip().casefold()

    def _cargar(self, catalogos):
        # Reutilizamos los objetos de los catálogos.
        # No creamos copias de docentes, aulas ni paralelos.
        docentes = {
            self._clave(docente.correo): docente
            for docente in catalogos.listar_docentes()
        }
        aulas = {
            self._clave(aula.id_aula): aula
            for aula in catalogos.listar_aulas()
        }
        paralelos = {
            self._clave(paralelo.codigo): paralelo
            for paralelo in catalogos.listar_paralelos()
        }

        with closing(sqlite3.connect(self._ruta)) as conexion:
            filas = conexion.execute("""
                SELECT
                    id,
                    materia,
                    docente_correo,
                    aula_codigo,
                    paralelo_codigo,
                    dia,
                    hora_inicio,
                    hora_fin
                FROM horarios
                ORDER BY id
            """).fetchall()

        # Validamos toda la carga antes de asignarla a este gestor.
        temporal = GestorHorarios(self._restricciones)

        for fila in filas:
            (
                identificador,
                materia,
                correo,
                codigo_aula,
                codigo_paralelo,
                dia,
                inicio,
                fin,
            ) = fila

            docente = docentes.get(self._clave(correo))
            aula = aulas.get(self._clave(codigo_aula))
            paralelo = None

            if docente is None:
                raise ValueError(
                    f"Horario {identificador}: el docente "
                    f"{correo} no existe en el catálogo."
                )

            if aula is None:
                raise ValueError(
                    f"Horario {identificador}: el aula "
                    f"{codigo_aula} no existe en el catálogo."
                )

            if codigo_paralelo is not None:
                paralelo = paralelos.get(
                    self._clave(codigo_paralelo)
                )

                if paralelo is None:
                    raise ValueError(
                        f"Horario {identificador}: el paralelo "
                        f"{codigo_paralelo} no existe."
                    )

            horario = Horario(
                materia=materia,
                docente=docente,
                aula=aula,
                franja=FranjaHoraria(dia, inicio, fin),
                paralelo=paralelo,
            )

            conflictos = temporal.agregar(horario)

            if conflictos:
                motivos = "; ".join(
                    conflicto.motivo
                    for conflicto in conflictos
                )
                raise ValueError(
                    f"Horario {identificador}: "
                    f"los datos guardados tienen conflictos. {motivos}"
                )

        self._horarios = temporal.listar()

    def _guardar(self):
        filas = [
            (
                horario.materia,
                horario.docente.correo,
                horario.aula.id_aula,
                (
                    horario.paralelo.codigo
                    if horario.paralelo is not None
                    else None
                ),
                horario.franja.dia,
                horario.franja.hora_inicio,
                horario.franja.hora_fin,
            )
            for horario in self._horarios
        ]

        try:
            with closing(sqlite3.connect(self._ruta)) as conexion:
                # Borrado e inserción forman una sola transacción.
                # Si falla la inserción, se conserva lo anterior.
                with conexion:
                    conexion.execute("DELETE FROM horarios")

                    conexion.executemany("""
                        INSERT INTO horarios (
                            materia,
                            docente_correo,
                            aula_codigo,
                            paralelo_codigo,
                            dia,
                            hora_inicio,
                            hora_fin
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, filas)

        except sqlite3.Error as error:
            raise ValueError(
                f"No se pudo guardar el cambio: {error}"
            ) from error

    # ---------- Operaciones persistentes ----------

    def agregar(self, horario):
        anteriores = self.listar()
        conflictos = super().agregar(horario)

        if not conflictos:
            try:
                self._guardar()
            except ValueError:
                self._horarios = anteriores
                raise

        return conflictos

    def eliminar(self, horario):
        anteriores = self.listar()
        super().eliminar(horario)

        try:
            self._guardar()
        except ValueError:
            self._horarios = anteriores
            raise

    def actualizar(self, horario_original, horario_nuevo):
        anteriores = self.listar()

        conflictos = super().actualizar(
            horario_original,
            horario_nuevo,
        )

        if not conflictos:
            try:
                self._guardar()
            except ValueError:
                self._horarios = anteriores
                raise

        return conflictos