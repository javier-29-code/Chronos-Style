from datetime import date, time

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from academico.models import PeriodoAcademico

from .models import FranjaPlanificacion, Horario


class FranjaPlanificacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026-2",
            nombre="Periodo de demostración",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )

    def franja(self, **cambios):
        datos = {
            "periodo": self.periodo,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": time(7, 0),
            "hora_fin": time(13, 0),
        }
        datos.update(cambios)
        return FranjaPlanificacion(**datos)

    def test_guarda_franja_valida(self):
        franja = self.franja()
        franja.full_clean()
        franja.save()
        franja.refresh_from_db()

        self.assertEqual(franja.periodo_id, self.periodo.pk)
        self.assertEqual(franja.hora_inicio, time(7, 0))
        self.assertEqual(franja.hora_fin, time(13, 0))

    def test_rechaza_horas_invalidas(self):
        for fin in (time(7, 0), time(6, 0)):
            with self.subTest(fin=fin):
                franja = self.franja(hora_fin=fin)

                with self.assertRaises(ValidationError) as resultado:
                    franja.full_clean()

                self.assertIn(
                    "hora_fin",
                    resultado.exception.message_dict,
                )

    def test_rechaza_dia_invalido(self):
        for dia in (0, 8):
            with self.subTest(dia=dia):
                with self.assertRaises(ValidationError):
                    self.franja(dia=dia).full_clean()

    def test_base_rechaza_datos_invalidos(self):
        casos = (
            {"hora_fin": time(7, 0)},
            {"hora_fin": time(6, 0)},
            {"dia": 0},
            {"dia": 8},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.franja(**cambios).save()

    def test_base_rechaza_duplicado_exacto(self):
        self.franja().save()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.franja().save()

    def test_permite_dos_franjas_con_descanso_intermedio(self):
        self.franja(hora_fin=time(12, 0)).save()

        tarde = self.franja(
            hora_inicio=time(14, 0),
            hora_fin=time(18, 0),
        )
        tarde.full_clean()
        tarde.save()

        self.assertEqual(FranjaPlanificacion.objects.count(), 2)