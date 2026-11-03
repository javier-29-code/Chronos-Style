from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from academico.models import PeriodoAcademico
from usuarios.models import PerfilDocente

from .models import DisponibilidadDocente, Horario


class DisponibilidadDocenteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026-2",
            nombre="Periodo de demostración",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        usuario = get_user_model().objects.create_user(
            username="docente_disponibilidad",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=usuario,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )

    def disponibilidad(self, **cambios):
        datos = {
            "docente": self.docente,
            "periodo": self.periodo,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": time(8, 0),
            "hora_fin": time(12, 0),
        }
        datos.update(cambios)
        return DisponibilidadDocente(**datos)

    def test_guarda_disponibilidad(self):
        disponibilidad = self.disponibilidad()
        disponibilidad.full_clean()
        disponibilidad.save()
        disponibilidad.refresh_from_db()

        self.assertEqual(
            disponibilidad.docente_id,
            self.docente.pk,
        )
        self.assertEqual(disponibilidad.hora_inicio, time(8, 0))
        self.assertEqual(disponibilidad.hora_fin, time(12, 0))

    def test_rechaza_horas_y_dias_invalidos(self):
        casos = (
            ({"hora_fin": time(8, 0)}, "hora_fin"),
            ({"hora_fin": time(7, 0)}, "hora_fin"),
            ({"dia": 0}, "dia"),
            ({"dia": 8}, "dia"),
        )

        for cambios, campo in casos:
            with self.subTest(cambios=cambios):
                disponibilidad = self.disponibilidad(**cambios)

                with self.assertRaises(ValidationError) as resultado:
                    disponibilidad.full_clean()

                self.assertIn(
                    campo,
                    resultado.exception.message_dict,
                )

    def test_base_rechaza_datos_invalidos(self):
        casos = (
            {"hora_fin": time(8, 0)},
            {"hora_fin": time(7, 0)},
            {"dia": 0},
            {"dia": 8},
        )

        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.disponibilidad(**cambios).save()

    def test_base_rechaza_duplicado_exacto(self):
        self.disponibilidad().save()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.disponibilidad().save()

    def test_permite_disponibilidad_distinta_por_periodo(self):
        self.disponibilidad().save()

        otro_periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2027-1",
            nombre="Otro periodo",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        disponibilidad = self.disponibilidad(
            periodo=otro_periodo,
            hora_inicio=time(14, 0),
            hora_fin=time(18, 0),
        )
        disponibilidad.full_clean()
        disponibilidad.save()

        self.assertEqual(
            DisponibilidadDocente.objects.count(),
            2,
        )

    def test_permite_dos_ventanas_con_descanso(self):
        self.disponibilidad().save()

        tarde = self.disponibilidad(
            hora_inicio=time(14, 0),
            hora_fin=time(18, 0),
        )
        tarde.full_clean()
        tarde.save()

        self.assertEqual(
            DisponibilidadDocente.objects.count(),
            2,
        )