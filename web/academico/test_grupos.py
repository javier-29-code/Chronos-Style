from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
    Inscripcion,
)
from usuarios.models import PerfilEstudiante


class GruposInscripcionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.programa = ProgramaAcademico.objects.create(
            codigo="TI",
            nombre="Tecnologías de la Información",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026-2",
            nombre="Periodo de demostración",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.grupo = Paralelo.objects.create(
            programa=cls.programa,
            periodo=cls.periodo,
            nombre="TERCERO A",
        )
        usuario = get_user_model().objects.create_user(
            username="estudiante_prueba",
            email="estudiante@example.com",
        )
        cls.estudiante = PerfilEstudiante.objects.create(
            usuario=usuario,
            programa=cls.programa,
            semestre=3,
        )

    def test_normaliza_nombre(self):
        grupo = Paralelo(
            programa=self.programa,
            periodo=self.periodo,
            nombre="  decimo   b  ",
        )
        grupo.full_clean()
        grupo.save()
        grupo.refresh_from_db()

        self.assertEqual(grupo.nombre, "DECIMO B")

    def test_rechaza_nombre_vacio(self):
        grupo = Paralelo(
            programa=self.programa,
            periodo=self.periodo,
            nombre="   ",
        )

        with self.assertRaises(ValidationError):
            grupo.full_clean()

    def test_rechaza_nombre_equivalente_en_mismo_periodo(self):
        grupo = Paralelo(
            programa=self.programa,
            periodo=self.periodo,
            nombre="  tercero   a ",
        )

        with self.assertRaises(ValidationError):
            grupo.full_clean()

    def test_base_rechaza_grupo_duplicado(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Paralelo.objects.create(
                    programa=self.programa,
                    periodo=self.periodo,
                    nombre="TERCERO A",
                )

    def test_permite_mismo_nombre_en_otro_periodo(self):
        otro_periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2027-1",
            nombre="Otro periodo",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        grupo = Paralelo(
            programa=self.programa,
            periodo=otro_periodo,
            nombre="TERCERO A",
        )
        grupo.full_clean()
        grupo.save()

        self.assertNotEqual(grupo.pk, self.grupo.pk)

    def test_base_rechaza_inscripcion_duplicada(self):
        Inscripcion.objects.create(
            estudiante=self.estudiante,
            paralelo=self.grupo,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Inscripcion.objects.create(
                    estudiante=self.estudiante,
                    paralelo=self.grupo,
                )

    def test_cambio_de_semestre_conserva_inscripcion(self):
        inscripcion = Inscripcion.objects.create(
            estudiante=self.estudiante,
            paralelo=self.grupo,
        )

        self.estudiante.semestre = 4
        self.estudiante.full_clean()
        self.estudiante.save()

        inscripcion.refresh_from_db()
        inscripcion.full_clean()

        self.assertEqual(
            inscripcion.estudiante.semestre,
            4,
        )
        self.assertEqual(inscripcion.paralelo_id, self.grupo.pk)

    def test_no_permite_eliminar_grupo_con_inscripciones(self):
        Inscripcion.objects.create(
            estudiante=self.estudiante,
            paralelo=self.grupo,
        )

        with self.assertRaises(ProtectedError):
            self.grupo.delete()

        self.assertTrue(
            Paralelo.objects.filter(pk=self.grupo.pk).exists()
        )