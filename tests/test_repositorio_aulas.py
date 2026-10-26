import tempfile
import unittest
from pathlib import Path

from modelos.aula_teorica import AulaTeorica
from modelos.laboratorios import Laboratorio
from modelos.laboratorio_computo import LaboratorioComputo
from persistencia.repositorio_aulas import RepositorioAulas


class TestRepositorioAulas(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)

        self.ruta = Path(temporal.name) / "prueba.db"
        self.repo = RepositorioAulas(self.ruta)

    def test_conserva_pantalla_tactil(self):
        self.repo.guardar(
            AulaTeorica(
                "A101",
                "Edificio A",
                30,
                tiene_proyector=False,
                tiene_pantalla_tactil=True,
            )
        )

        # Otra instancia vuelve a leer la misma base.
        recuperada = RepositorioAulas(self.ruta).listar()[0]

        self.assertIsInstance(recuperada, AulaTeorica)
        self.assertEqual(recuperada.id_aula, "A101")
        self.assertTrue(recuperada.tiene_pantalla_tactil)
        self.assertFalse(recuperada.tiene_proyector)

    def test_conserva_numero_computadoras(self):
        self.repo.guardar(
            LaboratorioComputo(
                "LAB01", "Edificio B", 25, 25
            )
        )

        recuperada = self.repo.listar()[0]

        self.assertIsInstance(
            recuperada,
            LaboratorioComputo,
        )
        self.assertEqual(
            recuperada.numero_computadoras,
            25,
        )

    def test_conserva_equipamiento(self):
        self.repo.guardar(
            Laboratorio(
                "RED01",
                "Edificio B",
                20,
                "Laboratorio de redes",
                ["router", "switch", "cables de red"],
            )
        )

        recuperada = self.repo.listar()[0]

        self.assertIsInstance(recuperada, Laboratorio)
        self.assertTrue(recuperada.verificar_equipamiento())

    def test_actualiza_sin_duplicar_identificador(self):
        self.repo.guardar(
            AulaTeorica("A101", "Edificio A", 30)
        )
        self.repo.guardar(
            AulaTeorica(
                "a101",
                "Edificio A",
                35,
                tiene_pantalla_tactil=True,
            )
        )

        aulas = self.repo.listar()

        self.assertEqual(len(aulas), 1)
        self.assertEqual(aulas[0].capacidad, 35)
        self.assertTrue(aulas[0].tiene_pantalla_tactil)


if __name__ == "__main__":
    unittest.main()