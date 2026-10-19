import unittest

from modelos.franja_horaria import FranjaHoraria
from modelos.aula import Aula
from modelos.laboratorios import Laboratorio


class TestFranjaHoraria(unittest.TestCase):

    def test_franjas_que_se_solapan(self):
        a = FranjaHoraria("Lunes", 7, 9)
        b = FranjaHoraria("Lunes", 8, 10)
        self.assertTrue(a.se_solapa_con(b))

    def test_franjas_que_solo_se_tocan_no_se_solapan(self):
        # a termina a las 9 y c empieza a las 9: no chocan
        a = FranjaHoraria("Lunes", 7, 9)
        c = FranjaHoraria("Lunes", 9, 11)
        self.assertFalse(a.se_solapa_con(c))

    def test_dias_distintos_no_se_solapan(self):
        a = FranjaHoraria("Lunes", 7, 9)
        d = FranjaHoraria("Martes", 7, 9)
        self.assertFalse(a.se_solapa_con(d))

    def test_hora_inicio_mayor_que_fin_lanza_error(self):
        with self.assertRaises(ValueError):
            FranjaHoraria("Lunes", 10, 8)

    def test_dia_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            FranjaHoraria("Domingo", 7, 9)


class TestAula(unittest.TestCase):

    def test_capacidad_invalida_lanza_error(self):
        with self.assertRaises(ValueError):
            Aula("A-01", "Edificio A", 0, "Teórica")

    def test_tipo_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            Aula("A-01", "Edificio A", 30, "Cancha")

    def test_aula_libre_al_inicio(self):
        aula = Aula("A-01", "Edificio A", 30, "Teórica")
        self.assertTrue(aula.verificar_disponibilidad(FranjaHoraria("Lunes", 7, 9)))

    def test_aula_ocupada_no_esta_disponible(self):
        aula = Aula("A-01", "Edificio A", 30, "Teórica")
        aula.ocupar_franja(FranjaHoraria("Lunes", 7, 9))
        # Una franja que choca con la ocupada ya no está disponible
        self.assertFalse(aula.verificar_disponibilidad(FranjaHoraria("Lunes", 8, 10)))

    def test_liberar_franja_deja_el_aula_disponible(self):
        aula = Aula("A-01", "Edificio A", 30, "Teórica")
        aula.ocupar_franja(FranjaHoraria("Lunes", 7, 9))
        aula.liberar_franja(FranjaHoraria("Lunes", 7, 9))
        self.assertTrue(aula.verificar_disponibilidad(FranjaHoraria("Lunes", 7, 9)))


class TestLaboratorio(unittest.TestCase):

    def test_equipamiento_completo(self):
        lab = Laboratorio("LR-01", "Edificio C", 25, "Laboratorio de redes",
                          ["Router", "Switch", "Cables de red"])
        self.assertTrue(lab.verificar_equipamiento())

    def test_equipamiento_incompleto(self):
        lab = Laboratorio("LE-01", "Edificio B", 20, "Laboratorio de electrónica",
                          ["Osciloscopio", "Multímetro"])
        self.assertFalse(lab.verificar_equipamiento())

    def test_tipo_no_laboratorio_lanza_error(self):
        with self.assertRaises(ValueError):
            Laboratorio("L-01", "Edificio A", 20, "Teórica", [])


if __name__ == "__main__":
    unittest.main()