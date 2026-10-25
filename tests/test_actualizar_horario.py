import unittest

from modelos.aula import Aula
from modelos.docente import Docente
from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario
from servicios.gestor_horarios import GestorHorarios


class TestActualizarHorario(unittest.TestCase):
    def setUp(self):
        self.gestor = GestorHorarios()

        self.docente = Docente(
            "Carlos",
            "carlos@uleam.edu.ec",
            "clave1234",
            "Ingeniero",
            "Programación",
            20,
        )

        self.aula = Aula(
            "A101", "Edificio A", 30, "Teórica"
        )

        self.original = self.crear_horario(8, 10)
        self.gestor.agregar(self.original)

    def crear_horario(self, inicio, fin):
        return Horario(
            materia="POO",
            docente=self.docente,
            aula=self.aula,
            franja=FranjaHoraria("Lunes", inicio, fin),
        )

    def test_actualiza_sin_conflictos(self):
        nuevo = self.crear_horario(9, 11)

        conflictos = self.gestor.actualizar(
            self.original,
            nuevo,
        )

        self.assertEqual(conflictos, [])
        self.assertEqual(self.gestor.cantidad(), 1)
        self.assertIs(self.gestor.listar()[0], nuevo)

    def test_conflicto_conserva_original(self):
        segundo = self.crear_horario(10, 12)
        self.gestor.agregar(segundo)

        nuevo = self.crear_horario(9, 11)

        conflictos = self.gestor.actualizar(
            self.original,
            nuevo,
        )

        self.assertTrue(conflictos)

        registrados = self.gestor.listar()

        self.assertEqual(len(registrados), 2)
        self.assertIs(registrados[0], self.original)
        self.assertIs(registrados[1], segundo)
        self.assertEqual(
            self.original.franja.hora_inicio,
            8,
        )

    def test_rechaza_original_no_registrado(self):
        inexistente = self.crear_horario(14, 16)
        nuevo = self.crear_horario(16, 18)

        with self.assertRaises(ValueError):
            self.gestor.actualizar(inexistente, nuevo)

        self.assertIs(
            self.gestor.listar()[0],
            self.original,
        )

    def test_rechaza_nuevo_invalido(self):
        with self.assertRaises(ValueError):
            self.gestor.actualizar(self.original, None)

        self.assertIs(
            self.gestor.listar()[0],
            self.original,
        )


if __name__ == "__main__":
    unittest.main()