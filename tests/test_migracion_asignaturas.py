import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from modelos.asignatura import Asignatura
from persistencia.migraciones import (
    migrar_asignaturas_horarios,
)


class TestMigracionAsignaturas(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)

        self.ruta = Path(temporal.name) / "prueba.db"

        self.asignaturas = [
            Asignatura(
                "POO",
                "Programación Orientada a Objetos",
                3,
                4,
            )
        ]

        with closing(sqlite3.connect(self.ruta)) as conexion:
            with conexion:
                conexion.execute("""
                    CREATE TABLE horarios (
                        id INTEGER PRIMARY KEY,
                        materia TEXT NOT NULL
                    )
                """)

    def insertar(self, materia):
        with closing(sqlite3.connect(self.ruta)) as conexion:
            with conexion:
                conexion.execute(
                    "INSERT INTO horarios (materia) VALUES (?)",
                    (materia,),
                )

    def test_reconoce_nombre_y_codigo(self):
        self.insertar("POO")
        self.insertar("Programación Orientada a Objetos")

        cantidad = migrar_asignaturas_horarios(
            self.ruta,
            self.asignaturas,
        )

        self.assertEqual(cantidad, 2)

        with closing(sqlite3.connect(self.ruta)) as conexion:
            filas = conexion.execute("""
                SELECT materia, asignatura_codigo
                FROM horarios
                ORDER BY id
            """).fetchall()

        self.assertEqual(filas, [
            ("POO", "poo"),
            ("Programación Orientada a Objetos", "poo"),
        ])

    def test_materia_desconocida_no_modifica_tabla(self):
        self.insertar("Materia inexistente")

        with self.assertRaises(ValueError):
            migrar_asignaturas_horarios(
                self.ruta,
                self.asignaturas,
            )

        with closing(sqlite3.connect(self.ruta)) as conexion:
            columnas = {
                fila[1]
                for fila in conexion.execute(
                    "PRAGMA table_info(horarios)"
                )
            }

            cantidad = conexion.execute(
                "SELECT COUNT(*) FROM horarios"
            ).fetchone()[0]

        self.assertNotIn("asignatura_codigo", columnas)
        self.assertEqual(cantidad, 1)

    def test_puede_ejecutarse_dos_veces(self):
        self.insertar("POO")

        migrar_asignaturas_horarios(
            self.ruta,
            self.asignaturas,
        )
        migrar_asignaturas_horarios(
            self.ruta,
            self.asignaturas,
        )

        with closing(sqlite3.connect(self.ruta)) as conexion:
            cantidad = conexion.execute(
                "SELECT COUNT(*) FROM horarios"
            ).fetchone()[0]

        self.assertEqual(cantidad, 1)

    def test_nombre_ambiguo_se_rechaza(self):
        self.insertar("Programación Orientada a Objetos")

        self.asignaturas.append(
            Asignatura(
                "POO2",
                "Programación Orientada a Objetos",
                3,
                4,
            )
        )

        with self.assertRaises(ValueError):
            migrar_asignaturas_horarios(
                self.ruta,
                self.asignaturas,
            )


if __name__ == "__main__":
    unittest.main()