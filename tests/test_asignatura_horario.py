import unittest
from types import SimpleNamespace

from modelos.asignatura import Asignatura
from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario


class TestAsignaturaHorario(unittest.TestCase):
    def setUp(self):
        self.asignatura = Asignatura(
            "POO",
            "Programación Orientada a Objetos",
            3,
            4,
        )

        self.docente = SimpleNamespace(
            nombre="Carlos",
            correo="carlos@uleam.edu.ec",
            horas_semanales_max=20,
        )

        self.aula = SimpleNamespace(id_aula="A101")

    def crear_horario(self, materia, **kwargs):
        return Horario(
            materia=materia,
            docente=self.docente,
            aula=self.aula,
            franja=FranjaHoraria("Lunes", 8, 10),
            **kwargs,
        )

    def test_conserva_referencia_a_asignatura(self):
        horario = self.crear_horario(
            "POO",
            asignatura=self.asignatura,
        )

        self.assertIs(
            horario.asignatura,
            self.asignatura,
        )
        self.assertEqual(
            horario.asignatura_codigo,
            "POO",
        )
        self.assertEqual(
            horario.materia,
            self.asignatura.nombre,
        )

    def test_rechaza_materia_incompatible(self):
        with self.assertRaises(ValueError):
            self.crear_horario(
                "Base de Datos",
                asignatura=self.asignatura,
            )

    def test_conserva_compatibilidad_con_texto(self):
        horario = self.crear_horario("POO")

        self.assertEqual(horario.materia, "POO")
        self.assertIsNone(horario.asignatura)

    def test_rechaza_asignatura_de_tipo_incorrecto(self):
        with self.assertRaises(ValueError):
            self.crear_horario(
                "POO",
                asignatura="POO",
            )


if __name__ == "__main__":
    unittest.main()