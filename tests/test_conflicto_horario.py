# tests/test_conflicto_horario.py
import unittest
from modelos.conflicto_horario import ConflictoHorario  # ajusta la ruta si hace falta


class HorarioFalso:
    """Imita a Horario: solo necesitamos que se pueda mostrar como texto."""
    def __init__(self, texto):
        self._texto = texto

    def __str__(self):
        return self._texto


class TestConflictoHorario(unittest.TestCase):
    def setUp(self):
        self.h1 = HorarioFalso("POO | lunes 8-10")
        self.h2 = HorarioFalso("BD | lunes 9-11")

    def test_guarda_los_datos(self):
        c = ConflictoHorario(self.h1, self.h2, "Mismo docente")
        self.assertIs(c.horario_1, self.h1)
        self.assertIs(c.horario_2, self.h2)
        self.assertEqual(c.motivo, "Mismo docente")

    def test_mostrar_incluye_motivo_y_horarios(self):
        c = ConflictoHorario(self.h1, self.h2, "Misma aula")
        texto = c.mostrar_informacion()
        self.assertIn("Misma aula", texto)
        self.assertIn("POO | lunes 8-10", texto)
        self.assertIn("BD | lunes 9-11", texto)

    def test_horario_none_lanza_error(self):
        with self.assertRaises(ValueError):
            ConflictoHorario(None, self.h2, "Mismo docente")

    def test_mismo_horario_lanza_error(self):
        with self.assertRaises(ValueError):
            ConflictoHorario(self.h1, self.h1, "Mismo docente")

    def test_motivo_vacio_lanza_error(self):
        with self.assertRaises(ValueError):
            ConflictoHorario(self.h1, self.h2, "   ")


if __name__ == "__main__":
    unittest.main()