import unittest
from types import SimpleNamespace

from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario
from servicios.gestor_horarios import GestorHorarios


class TestIdentidadHorarios(unittest.TestCase):
    @staticmethod
    def docente(correo):
        return SimpleNamespace(
            nombre="Docente de prueba",
            correo=correo,
            horas_semanales_max=20,
        )

    def test_mismo_docente_con_objetos_diferentes(self):
        docente_1 = self.docente("carlos@uleam.edu.ec")
        docente_2 = self.docente("CARLOS@uleam.edu.ec")

        primero = Horario(
            "POO",
            docente_1,
            SimpleNamespace(id_aula="A101"),
            FranjaHoraria("Lunes", 8, 10),
        )
        segundo = Horario(
            "BD",
            docente_2,
            SimpleNamespace(id_aula="A102"),
            FranjaHoraria("Lunes", 9, 11),
        )

        self.assertIsNot(docente_1, docente_2)

        gestor = GestorHorarios()
        self.assertEqual(gestor.agregar(primero), [])

        conflictos = gestor.agregar(segundo)

        self.assertEqual(len(conflictos), 1)
        self.assertIn("docente", conflictos[0].motivo.lower())
        self.assertEqual(gestor.cantidad(), 1)

    def test_misma_aula_con_objetos_diferentes(self):
        aula_1 = SimpleNamespace(id_aula="A101")
        aula_2 = SimpleNamespace(id_aula=" a101 ")

        primero = Horario(
            "POO",
            self.docente("carlos@uleam.edu.ec"),
            aula_1,
            FranjaHoraria("Lunes", 8, 10),
        )
        segundo = Horario(
            "BD",
            self.docente("javier@uleam.edu.ec"),
            aula_2,
            FranjaHoraria("Lunes", 9, 11),
        )

        self.assertIsNot(aula_1, aula_2)

        gestor = GestorHorarios()
        self.assertEqual(gestor.agregar(primero), [])

        conflictos = gestor.agregar(segundo)

        self.assertEqual(len(conflictos), 1)
        self.assertIn("aula", conflictos[0].motivo.lower())
        self.assertEqual(gestor.cantidad(), 1)


if __name__ == "__main__":
    unittest.main()