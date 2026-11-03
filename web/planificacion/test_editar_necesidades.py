from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from academico.models import (
    Asignatura,
    Paralelo,
    PeriodoAcademico,
    ProgramaAcademico,
)
from usuarios.models import PerfilDocente

from .models import NecesidadClase, PropuestaHorario
from .servicios_preparacion import editar_necesidad_clase


class EditarNecesidadesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        cls.coordinador = Usuario.objects.create_user(
            username="coordinador_prueba",
        )
        cls.sin_permiso = Usuario.objects.create_user(
            username="sin_permiso",
        )

        permiso = Permission.objects.get(
            content_type__app_label="planificacion",
            codename="change_necesidadclase",
        )
        cls.coordinador.user_permissions.add(permiso)

        cuenta_docente = Usuario.objects.create_user(
            username="docente_prueba",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=cuenta_docente,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )
        cls.programa = ProgramaAcademico.objects.create(
            codigo="TI-PRUEBA",
            nombre="Tecnologías de la Información",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="PERIODO-PRUEBA",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.paralelo = Paralelo.objects.create(
            programa=cls.programa,
            periodo=cls.periodo,
            nombre="TERCERO A",
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="BD-PRUEBA",
            nombre="Bases de datos",
        )
        cls.necesidad = NecesidadClase.objects.create(
            asignatura=cls.asignatura,
            docente=cls.docente,
            paralelo=cls.paralelo,
            sesiones_semanales=2,
            duracion_minutos=60,
        )

    def datos_servicio(self, **cambios):
        datos = {
            "asignatura": self.asignatura,
            "docente": self.docente,
            "paralelo": self.paralelo,
            "sesiones_semanales": 2,
            "duracion_minutos": 90,
            "prefiere_laboratorio": True,
            "activo": True,
        }
        datos.update(cambios)
        return datos

    def datos_post(self, **cambios):
        datos = {
            "asignatura": self.asignatura.pk,
            "docente": self.docente.pk,
            "paralelo": self.paralelo.pk,
            "sesiones_semanales": 2,
            "duracion_minutos": 90,
            "prefiere_laboratorio": "on",
            "activo": "on",
        }
        datos.update(cambios)
        return datos

    def url_editar(self):
        return reverse(
            "planificacion_web:editar_necesidad",
            kwargs={"necesidad_id": self.necesidad.pk},
        )

    def test_servicio_guarda_cambio_valido(self):
        editar_necesidad_clase(
            actor=self.coordinador,
            necesidad_id=self.necesidad.pk,
            **self.datos_servicio(),
        )

        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 90)
        self.assertTrue(self.necesidad.prefiere_laboratorio)

    def test_servicio_rechaza_datos_invalidos_y_conserva_original(self):
        with self.assertRaises(ValidationError):
            editar_necesidad_clase(
                actor=self.coordinador,
                necesidad_id=self.necesidad.pk,
                **self.datos_servicio(duracion_minutos=0),
            )

        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 60)

    def test_servicio_exige_permiso(self):
        with self.assertRaises(PermissionDenied):
            editar_necesidad_clase(
                actor=self.sin_permiso,
                necesidad_id=self.necesidad.pk,
                **self.datos_servicio(),
            )

        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 60)

    def test_no_modifica_necesidad_seleccionada_en_propuesta(self):
        propuesta = PropuestaHorario.objects.create(
            nombre="Borrador de prueba",
            periodo=self.periodo,
            autor=self.coordinador,
        )
        propuesta.necesidades.add(self.necesidad)

        with self.assertRaises(ValidationError):
            editar_necesidad_clase(
                actor=self.coordinador,
                necesidad_id=self.necesidad.pk,
                **self.datos_servicio(),
            )

        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 60)
        self.assertFalse(self.necesidad.prefiere_laboratorio)

    def test_web_rechaza_post_sin_permiso(self):
        self.client.force_login(self.sin_permiso)

        respuesta = self.client.post(
            self.url_editar(),
            self.datos_post(),
        )

        self.assertEqual(respuesta.status_code, 403)
        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 60)

    def test_web_muestra_formulario_y_guarda(self):
        self.client.force_login(self.coordinador)

        respuesta = self.client.get(self.url_editar())
        self.assertEqual(respuesta.status_code, 200)

        respuesta = self.client.post(
            self.url_editar(),
            self.datos_post(),
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            respuesta.url,
            reverse("planificacion_web:necesidades"),
        )
        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 90)

    def test_web_muestra_error_si_necesidad_esta_utilizada(self):
        propuesta = PropuestaHorario.objects.create(
            nombre="Propuesta existente",
            periodo=self.periodo,
            autor=self.coordinador,
        )
        propuesta.necesidades.add(self.necesidad)

        self.client.force_login(self.coordinador)
        respuesta = self.client.post(
            self.url_editar(),
            self.datos_post(),
        )

        self.assertContains(
            respuesta,
            "Esta necesidad ya está vinculada a una propuesta.",
        )
        self.necesidad.refresh_from_db()
        self.assertEqual(self.necesidad.duracion_minutos, 60)