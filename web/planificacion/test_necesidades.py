from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from academico.models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
    Asignatura,
    Aula,
)
from usuarios.models import PerfilDocente

from .models import NecesidadClase


class NecesidadClaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        programa = ProgramaAcademico.objects.create(
            codigo="TI",
            nombre="Tecnologías de la Información",
        )
        periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026-2",
            nombre="Periodo de demostración",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.grupo = Paralelo.objects.create(
            programa=programa,
            periodo=periodo,
            nombre="TERCERO A",
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="PROG-01",
            nombre="Programación",
        )
        usuario = get_user_model().objects.create_user(
            username="docente_necesidades",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=usuario,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )

    def necesidad(self, **cambios):
        datos = {
            "asignatura": self.asignatura,
            "docente": self.docente,
            "paralelo": self.grupo,
            "sesiones_semanales": 2,
            "duracion_minutos": 120,
        }
        datos.update(cambios)
        return NecesidadClase(**datos)

    def test_guarda_necesidad_y_calcula_carga(self):
        necesidad = self.necesidad()
        necesidad.full_clean()
        necesidad.save()
        necesidad.refresh_from_db()

        self.assertEqual(necesidad.minutos_semanales, 240)
        self.assertEqual(necesidad.paralelo.periodo, self.grupo.periodo)

    def test_rechaza_cantidades_invalidas(self):
        casos = (
            ("sesiones_semanales", 0),
            ("sesiones_semanales", -1),
            ("duracion_minutos", 0),
            ("duracion_minutos", -1),
            ("duracion_minutos", 1440),
        )

        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                necesidad = self.necesidad(**{campo: valor})

                with self.assertRaises(ValidationError) as resultado:
                    necesidad.full_clean()

                self.assertIn(campo, resultado.exception.message_dict)

    def test_base_rechaza_necesidad_duplicada(self):
        self.necesidad().save()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.necesidad().save()

    def test_permite_misma_asignatura_y_docente_en_otro_grupo(self):
        self.necesidad().save()

        otro_grupo = Paralelo.objects.create(
            programa=self.grupo.programa,
            periodo=self.grupo.periodo,
            nombre="TERCERO B",
        )
        necesidad = self.necesidad(paralelo=otro_grupo)
        necesidad.full_clean()
        necesidad.save()

        self.assertEqual(NecesidadClase.objects.count(), 2)

    def test_preferencia_laboratorio_no_exige_que_existan_laboratorios(self):
        self.assertEqual(Aula.objects.count(), 0)

        necesidad = self.necesidad(prefiere_laboratorio=True)
        necesidad.full_clean()
        necesidad.save()

        self.assertTrue(necesidad.prefiere_laboratorio)

    def test_protege_asignatura_utilizada(self):
        self.necesidad().save()

        with self.assertRaises(ProtectedError):
            self.asignatura.delete()

        self.assertTrue(
            Asignatura.objects.filter(pk=self.asignatura.pk).exists()
        )