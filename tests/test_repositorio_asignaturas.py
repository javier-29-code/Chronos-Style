import tempfile
import unittest
from pathlib import Path

from modelos.asignatura import Asignatura
from persistencia.repositorio_asignaturas import (
    RepositorioAsignaturas,
)


class TestRepositorioAsignaturas(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)

        self.ruta = Path(temporal.name) / "prueba.db"
        self.repo = RepositorioAsignaturas(self.ruta)

    def test_conserva_datos(self):
        self.repo.guardar(
            Asignatura("POO", "Programación", 3, 4)
        )

        recuperadas = RepositorioAsignaturas(
            self.ruta
        ).listar()

        self.assertEqual(len(recuperadas), 1)

        asignatura = recuperadas[0]
        self.assertEqual(asignatura.codigo, "POO")
        self.assertEqual(asignatura.nombre, "Programación")
        self.assertEqual(asignatura.creditos, 3)
        self.assertEqual(asignatura.horas_semanales, 4)

    def test_reconstruye_prerrequisito_compartido(self):
        inicial = Asignatura(
            "PROG1", "Programación I", 3, 4
        )
        avanzada = Asignatura(
            "PROG2", "Programación II", 3, 4
        )
        avanzada.definir_requisitos([inicial])

        self.repo.guardar(inicial)
        self.repo.guardar(avanzada)

        recuperadas = {
            asignatura.codigo: asignatura
            for asignatura in self.repo.listar()
        }

        self.assertIs(
            recuperadas["PROG2"].requisitos[0],
            recuperadas["PROG1"],
        )

    def test_rechaza_prerrequisito_no_registrado(self):
        inicial = Asignatura(
            "PROG1", "Programación I", 3, 4
        )
        avanzada = Asignatura(
            "PROG2", "Programación II", 3, 4
        )
        avanzada.definir_requisitos([inicial])

        with self.assertRaises(ValueError):
            self.repo.guardar(avanzada)

        self.assertEqual(self.repo.listar(), [])


if __name__ == "__main__":
    unittest.main()