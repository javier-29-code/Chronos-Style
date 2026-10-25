import unittest

from modelos.aula import Aula
from modelos.docente import Docente
from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario
from servicios.gestor_horarios import GestorHorarios


class TestCargaDocente(unittest.TestCase):
    def setUp(self):
        self.docente = Docente(
            "Carlos",
            "carlos@uleam.edu.ec",
            "clave1234",
            "Ingeniero",
            "Programación",
            4,
        )

        self.aula = Aula(
            "A101", "Edificio A", 30, "Teórica"
        )

        self.gestor = GestorHorarios()

    def crear_horario(self, dia, inicio, fin):
        return Horario(
            "POO",
            self.docente,
            self.aula,
            FranjaHoraria(dia, inicio, fin),
        )

    def test_acepta_exactamente_el_limite(self):
        primero = self.crear_horario("Lunes", 8, 10)
        segundo = self.crear_horario("Martes", 8, 10)

        self.assertEqual(self.gestor.agregar(primero), [])
        self.assertEqual(self.gestor.agregar(segundo), [])
        self.assertEqual(self.gestor.cantidad(), 2)

    def test_rechaza_exceso_sin_solapamiento(self):
        primero = self.crear_horario("Lunes", 8, 11)
        segundo = self.crear_horario("Martes", 8, 10)

        self.gestor.agregar(primero)
        conflictos = self.gestor.agregar(segundo)

        self.assertTrue(conflictos)
        self.assertIn("carga semanal", conflictos[0].motivo)
        self.assertEqual(self.gestor.cantidad(), 1)

    def test_edicion_no_cuenta_dos_veces_el_original(self):
        original = self.crear_horario("Lunes", 8, 10)
        segundo = self.crear_horario("Martes", 8, 10)

        self.gestor.agregar(original)
        self.gestor.agregar(segundo)

        reemplazo = self.crear_horario("Miércoles", 10, 12)

        self.assertEqual(
            self.gestor.actualizar(original, reemplazo),
            [],
        )

    def test_edicion_con_exceso_conserva_original(self):
        original = self.crear_horario("Lunes", 8, 10)
        segundo = self.crear_horario("Martes", 8, 10)

        self.gestor.agregar(original)
        self.gestor.agregar(segundo)

        reemplazo = self.crear_horario("Miércoles", 8, 11)

        conflictos = self.gestor.actualizar(
            original,
            reemplazo,
        )

        self.assertTrue(conflictos)
        self.assertIs(self.gestor.listar()[0], original)

    def test_clase_individual_supera_limite(self):
        with self.assertRaises(ValueError):
            self.crear_horario("Lunes", 8, 13)


if __name__ == "__main__":
    unittest.main()