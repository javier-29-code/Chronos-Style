from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from academico.models import (
    Asignatura,
    Aula,
    Paralelo,
    PeriodoAcademico,
    ProgramaAcademico,
)
from usuarios.models import PerfilDocente

from .models import (
    DisponibilidadDocente,
    FranjaPlanificacion,
    Horario,
)
from .servicios_preparacion import (
    editar_disponibilidad_docente,
    editar_franja_planificacion,
)


class EditarVentanasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        cls.coordinador = Usuario.objects.create_user(
            username="coordinador_ventanas",
        )
        cls.sin_permiso = Usuario.objects.create_user(
            username="sin_permiso_ventanas",
        )

        for codigo in (
            "change_disponibilidaddocente",
            "change_franjaplanificacion",
        ):
            cls.coordinador.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="planificacion",
                    codename=codigo,
                )
            )

        cuenta = Usuario.objects.create_user(
            username="docente_ventanas",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=cuenta,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )
        programa = ProgramaAcademico.objects.create(
            codigo="PROG-VENT",
            nombre="Programa de prueba",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="PER-VENT",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        paralelo = Paralelo.objects.create(
            programa=programa,
            periodo=cls.periodo,
            nombre="CURSO A",
        )
        asignatura = Asignatura.objects.create(
            codigo="ASIG-VENT",
            nombre="Asignatura de prueba",
        )

        tipo_aula = Aula._meta.get_field("tipo").choices[0][0]
        aula = Aula.objects.create(
            codigo="AULA-VENT",
            nombre="Aula de prueba",
            tipo=tipo_aula,
            capacidad=30,
        )

        cls.horario = Horario.objects.create(
            asignatura=asignatura,
            docente=cls.docente,
            aula=aula,
            paralelo=paralelo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(9),
            hora_fin=time(11),
        )

        cls.disponibilidad = DisponibilidadDocente.objects.create(
            docente=cls.docente,
            periodo=cls.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(12),
        )
        cls.franja = FranjaPlanificacion.objects.create(
            periodo=cls.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(12),
        )

    def casos(self):
        return (
            (
                self.disponibilidad,
                editar_disponibilidad_docente,
                "disponibilidad_id",
                "editar_disponibilidad",
            ),
            (
                self.franja,
                editar_franja_planificacion,
                "franja_id",
                "editar_franja",
            ),
        )

    def datos(self, registro, **cambios):
        datos = {
            "periodo": self.periodo,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": time(8),
            "hora_fin": time(12),
            "activo": True,
        }

        if isinstance(registro, DisponibilidadDocente):
            datos["docente"] = self.docente

        datos.update(cambios)
        return datos

    def ejecutar(self, caso, actor=None, **cambios):
        registro, servicio, argumento, _ = caso

        return servicio(
            actor=actor if actor is not None else self.coordinador,
            **{argumento: registro.pk},
            **self.datos(registro, **cambios),
        )

    def agregar_alternativa(self, registro, activo=True):
        datos = self.datos(
            registro,
            hora_inicio=time(10),
            hora_fin=time(12),
            activo=activo,
        )
        return type(registro).objects.create(**datos)

    def test_permite_reducir_si_clase_sigue_cubierta(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                self.ejecutar(
                    caso,
                    hora_inicio=time(9),
                    hora_fin=time(11),
                )

                registro.refresh_from_db()
                self.assertEqual(registro.hora_inicio, time(9))
                self.assertEqual(registro.hora_fin, time(11))

    def test_rechaza_perdida_cobertura_y_conserva_original(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                with self.assertRaises(ValidationError):
                    self.ejecutar(caso, hora_fin=time(10))

                registro.refresh_from_db()
                self.assertEqual(registro.hora_fin, time(12))

    def test_permite_cobertura_por_ventanas_consecutivas(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                self.agregar_alternativa(registro)
                self.ejecutar(caso, hora_fin=time(10))

                registro.refresh_from_db()
                self.assertEqual(registro.hora_fin, time(10))

    def test_ventana_inactiva_no_aporta_cobertura(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                self.agregar_alternativa(registro, activo=False)

                with self.assertRaises(ValidationError):
                    self.ejecutar(caso, hora_fin=time(10))

                registro.refresh_from_db()
                self.assertEqual(registro.hora_fin, time(12))

    def test_cambio_dia_no_deja_descubierto_dia_original(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                with self.assertRaises(ValidationError):
                    self.ejecutar(caso, dia=Horario.Dia.MARTES)

                registro.refresh_from_db()
                self.assertEqual(registro.dia, Horario.Dia.LUNES)

    def test_rechaza_intervalo_invalido(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                with self.assertRaises(ValidationError):
                    self.ejecutar(caso, hora_fin=time(7))

                registro.refresh_from_db()
                self.assertEqual(registro.hora_fin, time(12))

    def test_servicios_exigen_permiso(self):
        for caso in self.casos():
            registro = caso[0]

            with self.subTest(modelo=type(registro).__name__):
                with self.assertRaises(PermissionDenied):
                    self.ejecutar(
                        caso,
                        actor=self.sin_permiso,
                        activo=False,
                    )

                registro.refresh_from_db()
                self.assertTrue(registro.activo)

    def test_web_permite_edicion_y_rechaza_usuario_sin_permiso(self):
        for caso in self.casos():
            registro, _, argumento, nombre_url = caso

            with self.subTest(modelo=type(registro).__name__):
                url = reverse(
                    f"planificacion_web:{nombre_url}",
                    kwargs={argumento: registro.pk},
                )

                datos = self.datos(
                    registro,
                    hora_inicio=time(9),
                    hora_fin=time(11),
                )
                post = {
                    campo: valor.pk if hasattr(valor, "pk") else valor
                    for campo, valor in datos.items()
                }

                self.client.force_login(self.coordinador)
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)

                respuesta = self.client.post(url, post)
                self.assertEqual(respuesta.status_code, 302)

                registro.refresh_from_db()
                self.assertEqual(registro.hora_inicio, time(9))
                self.assertEqual(registro.hora_fin, time(11))

                self.client.force_login(self.sin_permiso)
                respuesta = self.client.post(
                    url,
                    {**post, "hora_fin": "10:00"},
                )
                self.assertEqual(respuesta.status_code, 403)

                registro.refresh_from_db()
                self.assertEqual(registro.hora_fin, time(11))