import unittest

from modelos.aula import Aula
from modelos.docente import Docente
from modelos.estudiante import Estudiante
from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario
from modelos.paralelo import Paralelo
from servicios.gestor_horarios import GestorHorarios


class TestParalelo(unittest.TestCase):
    def setUp(self):
        self.paralelo = Paralelo(
            "TI-3-A",
            "Tecnologías de la Información",
            3,
            "A",
        )

        self.ana = Estudiante(
            "Ana",
            "ana@live.uleam.edu.ec",
            "clave1234",
            "Tecnologías de la Información",
            3,
        )

    def test_inscripcion_y_duplicado(self):
        self.paralelo.inscribir_estudiante(self.ana)

        self.assertTrue(
            self.paralelo.contiene_estudiante(self.ana)
        )

        with self.assertRaises(ValueError):
            self.paralelo.inscribir_estudiante(self.ana)

    def test_rechaza_otro_semestre(self):
        self.ana.semestre = 2

        with self.assertRaises(ValueError):
            self.paralelo.inscribir_estudiante(self.ana)

    def test_conflicto_de_paralelo_y_horarios_consecutivos(self):
        docente_1 = Docente(
            "Carlos",
            "carlos@uleam.edu.ec",
            "clave1234",
            "Ingeniero",
            "Programación",
            20,
        )
        docente_2 = Docente(
            "Lucía",
            "lucia@uleam.edu.ec",
            "clave1234",
            "Ingeniera",
            "Bases de datos",
            20,
        )

        aula_1 = Aula("A101", "A", 30, "Teórica")
        aula_2 = Aula("A102", "A", 30, "Teórica")

        primero = Horario(
            "POO",
            docente_1,
            aula_1,
            FranjaHoraria("Lunes", 8, 10),
            paralelo=self.paralelo,
        )
        solapado = Horario(
            "Base de Datos",
            docente_2,
            aula_2,
            FranjaHoraria("Lunes", 9, 11),
            paralelo=self.paralelo,
        )
        consecutivo = Horario(
            "Base de Datos",
            docente_2,
            aula_2,
            FranjaHoraria("Lunes", 10, 12),
            paralelo=self.paralelo,
        )

        gestor = GestorHorarios()

        self.assertEqual(gestor.agregar(primero), [])

        conflictos = gestor.agregar(solapado)

        self.assertEqual(len(conflictos), 1)
        self.assertIn("paralelo", conflictos[0].motivo.lower())
        self.assertEqual(gestor.cantidad(), 1)

        self.assertEqual(gestor.agregar(consecutivo), [])
        self.assertEqual(gestor.cantidad(), 2)


if __name__ == "__main__":
    unittest.main()