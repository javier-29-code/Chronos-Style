# tests/test_gestor_horarios.py
import unittest

from modelos.horario import Horario
from servicios.gestor_horarios import GestorHorarios

from types import SimpleNamespace
# + los imports de Docente, Aula y FranjaHoraria, copiados de test_restriccion.py

class FranjaSimple:
    # Franja de prueba: solo lo que Horario necesita (se_solapa_con y str)
    def __init__(self, dia, inicio, fin):
        self.dia = dia
        self.inicio = inicio
        self.fin = fin
        
        self.hora_inicio = inicio
        self.hora_fin = fin

    def se_solapa_con(self, otra):
        # Se solapan si es el mismo día y los intervalos se cruzan
        return (self.dia == otra.dia
                and self.inicio < otra.fin
                and otra.inicio < self.fin)

    def __str__(self):
        return f"{self.dia} {self.inicio}:00-{self.fin}:00"


class TestGestorHorarios(unittest.TestCase):

    def setUp(self):
        # Docentes y aulas de prueba: objetos simples, igual que en test_restriccion
        self.docente_1 = SimpleNamespace(
            nombre="Docente 1",
            horas_semanales_max=20,
        )
        self.docente_2 = SimpleNamespace(
            nombre="Docente 2",
            horas_semanales_max=20,
        )
        
        self.aula_1, self.aula_2 = object(), object()

        self.franja_a = FranjaSimple("Lunes", 7, 9)
        self.franja_b = FranjaSimple("Lunes", 8, 10)   # se solapa con A
        self.franja_c = FranjaSimple("Martes", 7, 9)   # no se solapa con A

        self.gestor = GestorHorarios()

    def test_agrega_horario_valido(self):
        h = Horario("POO", self.docente_1, self.aula_1, self.franja_a)
        conflictos = self.gestor.agregar(h)
        self.assertEqual(conflictos, [])
        self.assertEqual(self.gestor.cantidad(), 1)

    def test_rechaza_choque_de_docente(self):
        self.gestor.agregar(Horario("POO", self.docente_1, self.aula_1, self.franja_a))
        # Mismo docente, aula distinta, franja que se solapa
        h2 = Horario("Redes", self.docente_1, self.aula_2, self.franja_b)
        conflictos = self.gestor.agregar(h2)
        self.assertEqual(len(conflictos), 1)
        self.assertEqual(self.gestor.cantidad(), 1)

    def test_rechaza_choque_de_aula(self):
        self.gestor.agregar(Horario("POO", self.docente_1, self.aula_1, self.franja_a))
        # Misma aula, docente distinto, franja que se solapa
        h2 = Horario("Redes", self.docente_2, self.aula_1, self.franja_b)
        conflictos = self.gestor.agregar(h2)
        self.assertEqual(len(conflictos), 1)
        self.assertEqual(self.gestor.cantidad(), 1)

    def test_acepta_mismo_docente_en_franja_distinta(self):
        self.gestor.agregar(Horario("POO", self.docente_1, self.aula_1, self.franja_a))
        h2 = Horario("Redes", self.docente_1, self.aula_1, self.franja_c)
        self.assertEqual(self.gestor.agregar(h2), [])
        self.assertEqual(self.gestor.cantidad(), 2)

    def test_rechaza_horario_duplicado(self):
        h = Horario("POO", self.docente_1, self.aula_1, self.franja_a)
        self.gestor.agregar(h)
        with self.assertRaises(ValueError):
            self.gestor.agregar(h)

    def test_rechaza_objeto_que_no_es_horario(self):
        with self.assertRaises(ValueError):
            self.gestor.agregar("no soy un horario")

    def test_eliminar_horario(self):
        h = Horario("POO", self.docente_1, self.aula_1, self.franja_a)
        self.gestor.agregar(h)
        self.gestor.eliminar(h)
        self.assertEqual(self.gestor.cantidad(), 0)

    def test_eliminar_horario_inexistente(self):
        h = Horario("POO", self.docente_1, self.aula_1, self.franja_a)
        with self.assertRaises(ValueError):
            self.gestor.eliminar(h)

    def test_listar_devuelve_copia(self):
        h = Horario("POO", self.docente_1, self.aula_1, self.franja_a)
        self.gestor.agregar(h)
        self.gestor.listar().clear()
        self.assertEqual(self.gestor.cantidad(), 1)


if __name__ == "__main__":
    unittest.main()