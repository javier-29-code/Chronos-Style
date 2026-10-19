# tests/test_horario.py
# Prueba de Horario de forma aislada: usamos una franja falsa (FranjaFalsa)
# para no depender de cómo está hecha la FranjaHoraria real.
import unittest
from modelos.horario import Horario  # ajusta la ruta a la de tu proyecto


class FranjaFalsa:
    """Imita a FranjaHoraria: responde lo que le indiquemos."""
    def __init__(self, se_solapa):
        self._se_solapa = se_solapa

    def se_solapa_con(self, otra):
        return self._se_solapa


class TestHorario(unittest.TestCase):
    def setUp(self):
        self.docente_1 = object()
        self.docente_2 = object()
        self.aula_1 = object()
        self.aula_2 = object()

    def test_conflicto_mismo_docente(self):
        a = Horario("POO", self.docente_1, self.aula_1, FranjaFalsa(True))
        b = Horario("BD", self.docente_1, self.aula_2, FranjaFalsa(True))
        self.assertTrue(a.tiene_conflicto_con(b))

    def test_conflicto_misma_aula(self):
        a = Horario("POO", self.docente_1, self.aula_1, FranjaFalsa(True))
        b = Horario("BD", self.docente_2, self.aula_1, FranjaFalsa(True))
        self.assertTrue(a.tiene_conflicto_con(b))

    def test_sin_conflicto_si_no_se_solapan(self):
        a = Horario("POO", self.docente_1, self.aula_1, FranjaFalsa(False))
        b = Horario("BD", self.docente_1, self.aula_1, FranjaFalsa(False))
        self.assertFalse(a.tiene_conflicto_con(b))

    def test_sin_conflicto_si_todo_es_distinto(self):
        a = Horario("POO", self.docente_1, self.aula_1, FranjaFalsa(True))
        b = Horario("BD", self.docente_2, self.aula_2, FranjaFalsa(True))
        self.assertFalse(a.tiene_conflicto_con(b))

    def test_materia_vacia_lanza_error(self):
        with self.assertRaises(ValueError):
            Horario("  ", self.docente_1, self.aula_1, FranjaFalsa(True))

    def test_docente_none_lanza_error(self):
        with self.assertRaises(ValueError):
            Horario("POO", None, self.aula_1, FranjaFalsa(True))


if __name__ == "__main__":
    unittest.main()