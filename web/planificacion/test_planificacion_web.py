from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from academico.models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
    Asignatura,
)
from usuarios.models import PerfilDocente

from .models import (
    Horario,
    NecesidadClase,
    DisponibilidadDocente,
    FranjaPlanificacion,
)


class PreparacionWebTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="coordinador_preparacion",
            is_superuser=True,
            is_staff=True,
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=cls.usuario,
            titulo="Ingeniero",
            area="Informática",
            horas_semanales_max=20,
        )
        programa = ProgramaAcademico.objects.create(
            codigo="TI",
            nombre="Tecnologías de la Información",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.grupo = Paralelo.objects.create(
            programa=programa,
            periodo=cls.periodo,
            nombre="TERCERO A",
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="BD",
            nombre="Bases de datos",
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_crea_necesidad_desde_web(self):
        respuesta = self.client.post(
            reverse("planificacion_web:necesidades"),
            {
                "asignatura": self.asignatura.pk,
                "docente": self.docente.pk,
                "paralelo": self.grupo.pk,
                "sesiones_semanales": 2,
                "duracion_minutos": 120,
                "prefiere_laboratorio": "on",
                "activo": "on",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        necesidad = NecesidadClase.objects.get()
        self.assertEqual(necesidad.minutos_semanales, 240)
        self.assertTrue(necesidad.prefiere_laboratorio)

    def test_crea_disponibilidad_desde_web(self):
        respuesta = self.client.post(
            reverse("planificacion_web:disponibilidades"),
            {
                "docente": self.docente.pk,
                "periodo": self.periodo.pk,
                "dia": Horario.Dia.LUNES,
                "hora_inicio": "07:00",
                "hora_fin": "12:00",
                "activo": "on",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(DisponibilidadDocente.objects.count(), 1)

    def test_franja_invalida_no_se_guarda(self):
        respuesta = self.client.post(
            reverse("planificacion_web:franjas"),
            {
                "periodo": self.periodo.pk,
                "dia": Horario.Dia.LUNES,
                "hora_inicio": "12:00",
                "hora_fin": "07:00",
                "activo": "on",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(FranjaPlanificacion.objects.count(), 0)

    def test_pantallas_exigen_permisos(self):
        usuario = get_user_model().objects.create_user(
            username="sin_permisos_preparacion",
        )
        self.client.force_login(usuario)

        for nombre in ("necesidades", "disponibilidades", "franjas"):
            with self.subTest(pantalla=nombre):
                respuesta = self.client.post(
                    reverse(f"planificacion_web:{nombre}"),
                    {},
                )
                self.assertEqual(respuesta.status_code, 403)