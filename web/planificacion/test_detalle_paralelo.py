from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from academico.models import (
    Asignatura,
    Aula,
    Inscripcion,
    Paralelo,
    PeriodoAcademico,
    ProgramaAcademico,
)
from usuarios.models import PerfilDocente, PerfilEstudiante

from .models import Horario


class DetalleParaleloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        cls.coordinador = Usuario.objects.create_user(
            username="coordinador_ficha",
        )
        cls.sin_permiso = Usuario.objects.create_user(
            username="sin_permiso_ficha",
        )
        cls.permiso_paralelo = Permission.objects.get(
            content_type__app_label="academico",
            codename="view_paralelo",
        )

        cls.coordinador.user_permissions.add(
            cls.permiso_paralelo,
            Permission.objects.get(
                content_type__app_label="planificacion",
                codename="view_horario",
            ),
        )

        programa = ProgramaAcademico.objects.create(
            codigo="PROG-FICHA",
            nombre="Programa de prueba",
        )
        periodo = PeriodoAcademico.objects.create(
            codigo="PER-FICHA",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.paralelo = Paralelo.objects.create(
            programa=programa,
            periodo=periodo,
            nombre="CURSO A",
        )
        cls.otro_paralelo = Paralelo.objects.create(
            programa=programa,
            periodo=periodo,
            nombre="CURSO B",
        )

        cuenta_docente = Usuario.objects.create_user(
            username="docente_ficha",
        )
        docente = PerfilDocente.objects.create(
            usuario=cuenta_docente,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="ASIG-FICHA",
            nombre="Asignatura del curso A",
        )
        otra_asignatura = Asignatura.objects.create(
            codigo="OTRA-FICHA",
            nombre="Asignatura exclusiva del curso B",
        )

        aula = Aula.objects.create(
            codigo="AULA-FICHA",
            nombre="Aula de prueba",
            tipo=Aula._meta.get_field("tipo").choices[0][0],
            capacidad=30,
        )

        for dia in (Horario.Dia.LUNES, Horario.Dia.MARTES):
            Horario.objects.create(
                asignatura=cls.asignatura,
                docente=docente,
                aula=aula,
                paralelo=cls.paralelo,
                dia=dia,
                hora_inicio=time(9),
                hora_fin=time(10),
            )

        Horario.objects.create(
            asignatura=otra_asignatura,
            docente=docente,
            aula=aula,
            paralelo=cls.otro_paralelo,
            dia=Horario.Dia.MIERCOLES,
            hora_inicio=time(9),
            hora_fin=time(10),
        )

        for username, paralelo in (
            ("estudiante_curso_a", cls.paralelo),
            ("estudiante_curso_b", cls.otro_paralelo),
        ):
            cuenta = Usuario.objects.create_user(username=username)
            estudiante = PerfilEstudiante.objects.create(
                usuario=cuenta,
                programa=programa,
                semestre=3,
            )
            Inscripcion.objects.create(
                estudiante=estudiante,
                paralelo=paralelo,
            )

    def url(self):
        return reverse(
            "planificacion_web:detalle_paralelo",
            kwargs={"paralelo_id": self.paralelo.pk},
        )

    def test_exige_inicio_sesion(self):
        respuesta = self.client.get(self.url())
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("next=", respuesta.url)

    def test_rechaza_usuario_sin_permisos(self):
        self.client.force_login(self.sin_permiso)
        respuesta = self.client.get(self.url())
        self.assertEqual(respuesta.status_code, 403)

    def test_permiso_paralelo_solo_no_permite_ver_horarios(self):
        self.sin_permiso.user_permissions.add(self.permiso_paralelo)
        self.client.force_login(self.sin_permiso)

        respuesta = self.client.get(self.url())

        self.assertEqual(respuesta.status_code, 403)

    def test_muestra_solo_horarios_del_paralelo(self):
        self.client.force_login(self.coordinador)

        respuesta = self.client.get(self.url())

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total_bloques"], 2)
        self.assertTrue(all(
            horario.paralelo_id == self.paralelo.pk
            for horario in respuesta.context["horarios"]
        ))
        self.assertNotContains(
            respuesta,
            "Asignatura exclusiva del curso B",
        )
        self.assertEqual(
            list(respuesta.context["asignaturas"]),
            [self.asignatura],
        )

    def test_oculta_estudiantes_sin_permiso_inscripciones(self):
        self.client.force_login(self.coordinador)

        respuesta = self.client.get(self.url())

        self.assertFalse(respuesta.context["puede_ver_inscritos"])
        self.assertIsNone(respuesta.context["pagina_estudiantes"])
        self.assertNotContains(respuesta, "estudiante_curso_a")

    def test_muestra_solo_estudiantes_del_paralelo(self):
        self.coordinador.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="academico",
                codename="view_inscripcion",
            )
        )
        self.client.force_login(self.coordinador)

        respuesta = self.client.get(self.url())

        self.assertContains(respuesta, "estudiante_curso_a")
        self.assertNotContains(respuesta, "estudiante_curso_b")
        self.assertEqual(
            respuesta.context["pagina_estudiantes"].paginator.count,
            1,
        )

    def test_paralelo_sin_clases_muestra_estado_vacio(self):
        Horario.objects.filter(paralelo=self.paralelo).delete()
        self.client.force_login(self.coordinador)

        respuesta = self.client.get(self.url())

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total_bloques"], 0)
        self.assertContains(
            respuesta,
            "Este paralelo todavía no tiene clases oficiales.",
        )