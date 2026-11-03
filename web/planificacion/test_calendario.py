from datetime import time
from types import SimpleNamespace

from django.test import SimpleTestCase

from .calendario import CalendarioSemanal


class CalendarioSemanalTests(SimpleTestCase):
    def horario(self, pk, inicio, fin, dia=1):
        return SimpleNamespace(
            pk=pk,
            asignatura_id=1,
            dia=dia,
            hora_inicio=time(*inicio),
            hora_fin=time(*fin),
        )

    def bloques(self, horarios):
        calendario = CalendarioSemanal().construir(horarios)
        return calendario["dias"][0]["bloques"]

    def test_dos_horas_tienen_doble_altura_que_una(self):
        bloques = self.bloques([
            self.horario(1, (8, 0), (9, 0)),
            self.horario(2, (10, 0), (12, 0)),
        ])

        self.assertEqual(
            float(bloques[1]["alto"]),
            float(bloques[0]["alto"]) * 2,
        )

    def test_consecutivos_usan_ancho_completo(self):
        bloques = self.bloques([
            self.horario(1, (8, 0), (10, 0)),
            self.horario(2, (10, 0), (12, 0)),
        ])

        self.assertTrue(
            all(float(b["ancho"]) == 100 for b in bloques)
        )

    def test_simultaneos_se_colocan_lado_a_lado(self):
        bloques = self.bloques([
            self.horario(1, (8, 0), (10, 0)),
            self.horario(2, (9, 0), (11, 0)),
        ])

        self.assertEqual(
            [float(b["izquierda"]) for b in bloques],
            [0, 50],
        )
        self.assertTrue(
            all(float(b["ancho"]) == 50 for b in bloques)
        )

    def test_amplia_eje_para_clases_tempranas(self):
        calendario = CalendarioSemanal().construir([
            self.horario(1, (6, 30), (8, 0)),
        ])

        self.assertEqual(
            calendario["marcas"][0]["texto"],
            "06:00",
        )
        self.assertEqual(
            float(calendario["dias"][0]["bloques"][0]["arriba"]),
            42,
        )

    def test_incluye_domingo(self):
        calendario = CalendarioSemanal().construir([
            self.horario(1, (8, 0), (10, 0), dia=7),
        ])

        self.assertEqual(len(calendario["dias"]), 7)
        self.assertEqual(
            len(calendario["dias"][6]["bloques"]),
            1,
        )