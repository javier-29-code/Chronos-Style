from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academico.models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
)


class ParalelosWebTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="admin_paralelos",
            is_superuser=True,
            is_staff=True,
        )
        cls.programa = ProgramaAcademico.objects.create(
            codigo="TI",
            nombre="Tecnologías de la Información",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def datos(self):
        return {
            "programa": self.programa.pk,
            "periodo": self.periodo.pk,
            "nombre": "  tercero   a ",
        }

    def test_crea_y_normaliza_paralelo(self):
        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_paralelo"),
            self.datos(),
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            Paralelo.objects.get().nombre,
            "TERCERO A",
        )

    def test_rechaza_duplicado_en_mismo_periodo(self):
        Paralelo.objects.create(
            programa=self.programa,
            periodo=self.periodo,
            nombre="TERCERO A",
        )

        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_paralelo"),
            self.datos(),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Paralelo.objects.count(), 1)

    def test_permite_reutilizar_nombre_en_otro_periodo(self):
        Paralelo.objects.create(
            programa=self.programa,
            periodo=self.periodo,
            nombre="TERCERO A",
        )
        otro_periodo = PeriodoAcademico.objects.create(
            codigo="OTRO-2027",
            nombre="Otro periodo",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        datos = self.datos()
        datos["periodo"] = otro_periodo.pk

        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_paralelo"),
            datos,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Paralelo.objects.count(), 2)

    def test_listado_muestra_paralelo_y_contadores(self):
        Paralelo.objects.create(
            programa=self.programa,
            periodo=self.periodo,
            nombre="TERCERO A",
        )

        respuesta = self.client.get(
            reverse("planificacion_web:lista_paralelos"),
            {"q": "TERCERO"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "TERCERO A")

        registro = respuesta.context["pagina"].object_list[0]
        self.assertEqual(registro.total_inscritos, 0)
        self.assertEqual(registro.total_bloques, 0)

    def test_exige_permisos(self):
        usuario = get_user_model().objects.create_user(
            username="sin_permisos_paralelos",
        )
        self.client.force_login(usuario)

        respuesta = self.client.get(
            reverse("planificacion_web:lista_paralelos")
        )
        self.assertEqual(respuesta.status_code, 403)

        respuesta = self.client.post(
            reverse("planificacion_web:nuevo_paralelo"),
            self.datos(),
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Paralelo.objects.count(), 0)