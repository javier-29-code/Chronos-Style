"""Almacenamiento de asignaturas en SQLite."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from modelos.asignatura import Asignatura


class RepositorioAsignaturas:
    def __init__(self, ruta):
        self._ruta = Path(ruta)
        self._ruta.parent.mkdir(parents=True, exist_ok=True)

        with closing(sqlite3.connect(self._ruta)) as conexion:
            with conexion:
                conexion.execute("""
                    CREATE TABLE IF NOT EXISTS asignaturas (
                        codigo TEXT PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        creditos INTEGER NOT NULL,
                        horas_semanales INTEGER NOT NULL,
                        requisitos TEXT NOT NULL
                    )
                """)

    @staticmethod
    def _clave(codigo):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError(
                "El código de la asignatura debe ser texto no vacío."
            )

        return codigo.strip().casefold()

    def guardar(self, asignatura):
        if not isinstance(asignatura, Asignatura):
            raise ValueError(
                "Se necesita un objeto Asignatura."
            )

        # Conservamos el código original para mostrarlo.
        requisitos = {
            "codigo_original": asignatura.codigo,
            "codigos": [
                self._clave(requisito.codigo)
                for requisito in asignatura.requisitos
            ],
        }

        with closing(sqlite3.connect(self._ruta)) as conexion:
            with conexion:
                # Los prerrequisitos deben registrarse primero.
                existentes = {
                    fila[0]
                    for fila in conexion.execute(
                        "SELECT codigo FROM asignaturas"
                    )
                }

                codigo = self._clave(asignatura.codigo)

                for requerido in requisitos["codigos"]:
                    if requerido == codigo:
                        raise ValueError(
                            "Una asignatura no puede ser "
                            "su propio prerrequisito."
                        )

                    if requerido not in existentes:
                        raise ValueError(
                            f"Registra primero el prerrequisito: "
                            f"{requerido}."
                        )

                conexion.execute("""
                    INSERT INTO asignaturas (
                        codigo,
                        nombre,
                        creditos,
                        horas_semanales,
                        requisitos
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(codigo) DO UPDATE SET
                        nombre = excluded.nombre,
                        creditos = excluded.creditos,
                        horas_semanales = excluded.horas_semanales,
                        requisitos = excluded.requisitos
                """, (
                    codigo,
                    asignatura.nombre,
                    asignatura.creditos,
                    asignatura.horas_semanales,
                    json.dumps(
                        requisitos,
                        ensure_ascii=False,
                    ),
                ))

    def listar(self):
        with closing(sqlite3.connect(self._ruta)) as conexion:
            conexion.row_factory = sqlite3.Row

            filas = conexion.execute("""
                SELECT *
                FROM asignaturas
                ORDER BY codigo
            """).fetchall()

        asignaturas = {}
        requisitos_pendientes = {}

        # Primero reconstruimos todos los objetos.
        for fila in filas:
            detalles = json.loads(fila["requisitos"])

            asignaturas[fila["codigo"]] = Asignatura(
                codigo=detalles["codigo_original"],
                nombre=fila["nombre"],
                creditos=fila["creditos"],
                horas_semanales=fila["horas_semanales"],
            )

            requisitos_pendientes[fila["codigo"]] = (
                detalles["codigos"]
            )

        # Después conectamos las referencias entre ellos.
        for codigo, requeridos in requisitos_pendientes.items():
            faltantes = [
                requerido
                for requerido in requeridos
                if requerido not in asignaturas
            ]

            if faltantes:
                raise ValueError(
                    f"La asignatura {codigo} tiene "
                    f"prerrequisitos inexistentes: {faltantes}."
                )

            asignaturas[codigo].definir_requisitos(
                [
                    asignaturas[requerido]
                    for requerido in requeridos
                ]
            )

        return list(asignaturas.values())