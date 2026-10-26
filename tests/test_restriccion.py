# tests/test_restriccion.py
# Usamos Horario real con una franja falsa, para controlar si "se solapan".
import unittest
from modelos.horario import Horario
from modelos.conflicto_horario import ConflictoHorario
from modelos.restriccion import Restriccion, RestriccionDocente, RestriccionAula

from types import SimpleNamespace


class FranjaFalsa:
    def __init__(self, se_solapa):
        self._se_solapa = se_solapa
        self.hora_inicio = 8
        self.hora_fin = 10

    def se_solapa_con(self, otra):
        return self._se_solapa


class TestRestriccion(unittest.TestCase):
    def setUp(self):
        self.doc_1 = SimpleNamespace(
            nombre="Docente 1",
            correo="docente1@uleam.edu.ec",
            horas_semanales_max=20,
        )
        self.doc_2 = SimpleNamespace(
            nombre="Docente 2",
            correo="docente2@uleam.edu.ec",
            horas_semanales_max=20,
        )

        self.aula_1 = SimpleNamespace(id_aula="A101")
        self.aula_2 = SimpleNamespace(id_aula="A102")
        self.nuevo = Horario("POO", self.doc_1, self.aula_1, FranjaFalsa(True))

    def test_docente_detecta_choque(self):
        otro = Horario("BD", self.doc_1, self.aula_2, FranjaFalsa(True))
        conflictos = RestriccionDocente().verificar(self.nuevo, [otro])
        self.assertEqual(len(conflictos), 1)
        self.assertIsInstance(conflictos[0], ConflictoHorario)
        self.assertIn("docente", conflictos[0].motivo)

    def test_aula_detecta_choque(self):
        otro = Horario("BD", self.doc_2, self.aula_1, FranjaFalsa(True))
        conflictos = RestriccionAula().verificar(self.nuevo, [otro])
        self.assertEqual(len(conflictos), 1)
        self.assertIn("aula", conflictos[0].motivo)

    def test_docente_no_choca_si_es_otro_docente(self):
        otro = Horario("BD", self.doc_2, self.aula_1, FranjaFalsa(True))
        self.assertEqual(RestriccionDocente().verificar(self.nuevo, [otro]), [])

    def test_no_choca_si_no_se_solapan(self):
        nuevo = Horario("POO", self.doc_1, self.aula_1, FranjaFalsa(False))
        otro = Horario("BD", self.doc_1, self.aula_1, FranjaFalsa(False))
        self.assertEqual(RestriccionDocente().verificar(nuevo, [otro]), [])
        self.assertEqual(RestriccionAula().verificar(nuevo, [otro]), [])

    def test_ignora_el_mismo_horario(self):
        self.assertEqual(RestriccionDocente().verificar(self.nuevo, [self.nuevo]), [])

    def test_varios_conflictos(self):
        o1 = Horario("BD", self.doc_1, self.aula_2, FranjaFalsa(True))
        o2 = Horario("Redes", self.doc_1, self.aula_2, FranjaFalsa(True))
        self.assertEqual(len(RestriccionDocente().verificar(self.nuevo, [o1, o2])), 2)

    def test_base_exige_definir_choca(self):
        regla = Restriccion("Regla", "Motivo")
        with self.assertRaises(NotImplementedError):
            regla.verificar(self.nuevo, [Horario("BD", self.doc_1, self.aula_1, FranjaFalsa(True))])

    def test_nombre_vacio_lanza_error(self):
        with self.assertRaises(ValueError):
            Restriccion("  ", "Motivo")


if __name__ == "__main__":
    unittest.main()