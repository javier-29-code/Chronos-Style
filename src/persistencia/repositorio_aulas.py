"""Almacenamiento de aulas y sus subclases en SQLite."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from modelos.aula import Aula
from modelos.aula_teorica import AulaTeorica
from modelos.laboratorios import Laboratorio
from modelos.laboratorio_computo import LaboratorioComputo


class RepositorioAulas:
    def __init__(self, ruta):
        self._ruta = Path(ruta)
        self._ruta.parent.mkdir(parents=True, exist_ok=True)

        with closing(sqlite3.connect(self._ruta)) as conexion:
            with conexion:
                conexion.execute("""
                    CREATE TABLE IF NOT EXISTS aulas (
                        id_aula TEXT PRIMARY KEY,
                        clase TEXT NOT NULL,
                        edificio TEXT NOT NULL,
                        capacidad INTEGER NOT NULL
                            CHECK (capacidad > 0),
                        tipo TEXT NOT NULL,
                        detalles TEXT NOT NULL
                    )
                """)

    def guardar(self, aula):
        """Inserta el aula o actualiza sus datos si ya existe."""
        if not isinstance(aula, Aula):
            raise ValueError("Se necesita un objeto Aula.")

        clase, detalles = self._serializar(aula)

        with closing(sqlite3.connect(self._ruta)) as conexion:
            with conexion:
                conexion.execute("""
                    INSERT INTO aulas (
                        id_aula,
                        clase,
                        edificio,
                        capacidad,
                        tipo,
                        detalles
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_aula) DO UPDATE SET
                        clase = excluded.clase,
                        edificio = excluded.edificio,
                        capacidad = excluded.capacidad,
                        tipo = excluded.tipo,
                        detalles = excluded.detalles
                """, (
                    aula.id_aula.strip().casefold(),
                    clase,
                    aula.edificio,
                    aula.capacidad,
                    aula.tipo,
                    json.dumps(detalles, ensure_ascii=False),
                ))

    @staticmethod
    def _serializar(aula):
        # Comprobamos la clase exacta para no perder silenciosamente
        # atributos de una subclase que todavía no conocemos.
        if type(aula) is AulaTeorica:
            return "AulaTeorica", {
                "tiene_proyector": aula.tiene_proyector,
                "tiene_pantalla_tactil": aula.tiene_pantalla_tactil,
                "id_original": aula.id_aula,
            }

        if type(aula) is LaboratorioComputo:
            return "LaboratorioComputo", {
                "numero_computadoras": aula.numero_computadoras,
                "id_original": aula.id_aula,
            }

        if type(aula) is Laboratorio:
            return "Laboratorio", {
                "equipamiento": aula.equipamiento,
                "id_original": aula.id_aula,
            }

        if type(aula) is Aula:
            return "Aula", {
                "id_original": aula.id_aula,
            }

        raise ValueError(
            f"Tipo de aula no soportado: {type(aula).__name__}."
        )

    def listar(self):
        """Reconstruye los objetos utilizando sus clases originales."""
        with closing(sqlite3.connect(self._ruta)) as conexion:
            conexion.row_factory = sqlite3.Row
            filas = conexion.execute("""
                SELECT *
                FROM aulas
                ORDER BY id_aula
            """).fetchall()

        return [
            self._reconstruir(fila)
            for fila in filas
        ]

    @staticmethod
    def _reconstruir(fila):
        detalles = json.loads(fila["detalles"])

        comunes = {
            "id_aula": detalles["id_original"],
            "edificio": fila["edificio"],
            "capacidad": fila["capacidad"],
        }

        clase = fila["clase"]

        if clase == "AulaTeorica":
            return AulaTeorica(
                **comunes,
                tiene_proyector=detalles["tiene_proyector"],
                tiene_pantalla_tactil=(
                    detalles["tiene_pantalla_tactil"]
                ),
            )

        if clase == "LaboratorioComputo":
            return LaboratorioComputo(
                **comunes,
                numero_computadoras=(
                    detalles["numero_computadoras"]
                ),
            )

        if clase == "Laboratorio":
            return Laboratorio(
                **comunes,
                tipo=fila["tipo"],
                equipamiento=detalles["equipamiento"],
            )

        if clase == "Aula":
            return Aula(
                **comunes,
                tipo=fila["tipo"],
            )

        raise ValueError(
            f"Clase de aula desconocida en la base: {clase}."
        )