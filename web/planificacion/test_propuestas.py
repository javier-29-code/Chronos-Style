from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from academico.models import PeriodoAcademico

from .models import Horario, PropuestaHorario


class PropuestaHorarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026-2",
            nombre="Periodo de demostración",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.autor = get_user_model().objects.create_user(
            username="coordinador_prueba",
        )

    def propuesta(self, **cambios):
        datos = {
            "nombre": "Propuesta inicial",
            "periodo": self.periodo,
            "autor": self.autor,
        }
        datos.update(cambios)
        return PropuestaHorario(**datos)

    def test_crear_propuesta_no_crea_horarios_oficiales(self):
        propuesta = self.propuesta()
        propuesta.full_clean()
        propuesta.save()
        propuesta.refresh_from_db()

        self.assertEqual(
            propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )
        self.assertEqual(Horario.objects.count(), 0)

    def test_normaliza_nombre(self):
        propuesta = self.propuesta(
            nombre="  Propuesta   de prueba  ",
        )
        propuesta.full_clean()
        propuesta.save()
        propuesta.refresh_from_db()

        self.assertEqual(propuesta.nombre, "Propuesta de prueba")

    def test_rechaza_nombre_vacio(self):
        propuesta = self.propuesta(nombre="   ")

        with self.assertRaises(ValidationError):
            propuesta.full_clean()

    def test_base_rechaza_estado_desconocido(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.propuesta(estado="INVENTADO").save()

    def test_conserva_autor_de_propuesta(self):
        self.propuesta().save()

        with self.assertRaises(ProtectedError):
            self.autor.delete()

        self.assertTrue(
            get_user_model().objects.filter(
                pk=self.autor.pk,
            ).exists()
        )