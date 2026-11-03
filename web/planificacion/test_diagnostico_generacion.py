from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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

from .generador_horarios import GeneradorHorarios
from .models import (
    BloquePropuesta,
    DisponibilidadDocente,
    FranjaPlanificacion,
    Horario,
    NecesidadClase,
)


class DiagnosticoGeneracionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        cls.actor = Usuario.objects.create_user(
            username="autor_diagnostico",
        )
        cls.actor.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="planificacion",
                codename="add_propuestahorario",
            )
        )

        cuenta = Usuario.objects.create_user(
            username="docente_diagnostico",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=cuenta,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )
        programa = ProgramaAcademico.objects.create(
            codigo="PROG-DIAG",
            nombre="Programa de prueba",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="PER-DIAG",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        cls.paralelo = Paralelo.objects.create(
            programa=programa,
            periodo=cls.periodo,
            nombre="CURSO A",
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="ASIG-DIAG",
            nombre="Asignatura de prueba",
        )
        cls.necesidad = NecesidadClase.objects.create(
            asignatura=cls.asignatura,
            docente=cls.docente,
            paralelo=cls.paralelo,
            sesiones_semanales=1,
            duracion_minutos=120,
        )

        tipo_comun = next(
            valor
            for valor, _ in Aula._meta.get_field("tipo").choices
            if valor != Aula.Tipo.LABORATORIO
        )
        cls.aula = Aula.objects.create(
            codigo="AULA-DIAG",
            nombre="Aula común",
            tipo=tipo_comun,
            capacidad=30,
            activo=True,
        )
        cls.franja = FranjaPlanificacion.objects.create(
            periodo=cls.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(10),
        )
        cls.disponibilidad = DisponibilidadDocente.objects.create(
            docente=cls.docente,
            periodo=cls.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(10),
        )

    def generar(self):
        return GeneradorHorarios().generar(
            usuario=self.actor,
            nombre="Propuesta con diagnóstico",
            periodo_id=self.periodo.pk,
            necesidades_ids=[self.necesidad.pk],
        )

    def mensajes(self, propuesta):
        return " ".join(
            motivo["mensaje"]
            for sesion in propuesta.diagnostico_generacion["sesiones"]
            for motivo in sesion["motivos"]
        )

    def url_detalle(self, propuesta):
        return reverse(
            "planificacion_web:detalle_propuesta",
            kwargs={"propuesta_id": propuesta.pk},
        )

    def test_sin_aulas_guarda_diagnostico_persistente(self):
        self.aula.activo = False
        self.aula.save(update_fields=["activo"])

        resultado = self.generar()
        propuesta = resultado["propuesta"]
        propuesta.refresh_from_db()

        self.assertTrue(resultado["pendientes"])
        self.assertIn("No hay aulas activas.", self.mensajes(propuesta))

        sesion = propuesta.diagnostico_generacion["sesiones"][0]
        self.assertEqual(sesion["necesidad_id"], self.necesidad.pk)
        self.assertEqual(sesion["numero_sesion"], 1)
        self.assertEqual(sesion["intentos"], 0)
        self.assertEqual(propuesta.bloques.count(), 0)

    def test_sin_franjas_informa_la_ausencia(self):
        self.franja.delete()

        propuesta = self.generar()["propuesta"]

        self.assertIn(
            "No hay franjas de planificación activas",
            self.mensajes(propuesta),
        )

    def test_sin_disponibilidad_informa_la_ausencia(self):
        self.disponibilidad.delete()

        propuesta = self.generar()["propuesta"]

        self.assertIn(
            "El docente no tiene disponibilidad activa",
            self.mensajes(propuesta),
        )

    def test_ventanas_sin_intervalo_comun(self):
        self.disponibilidad.hora_inicio = time(11)
        self.disponibilidad.hora_fin = time(13)
        self.disponibilidad.save()

        propuesta = self.generar()["propuesta"]

        self.assertIn(
            "no comparten un intervalo continuo suficiente",
            self.mensajes(propuesta),
        )

    def test_conserva_error_de_carga_y_revierte_candidato(self):
        self.docente.horas_semanales_max = 1
        self.docente.save(update_fields=["horas_semanales_max"])

        propuesta = self.generar()["propuesta"]

        self.assertIn(
            "horas semanales",
            self.mensajes(propuesta),
        )
        self.assertEqual(propuesta.bloques.count(), 0)
        self.assertEqual(Horario.objects.count(), 0)
        self.assertGreater(
            propuesta.diagnostico_generacion["sesiones"][0]["intentos"],
            0,
        )

    def test_conserva_error_de_choque_con_horario_oficial(self):
        oficial = Horario.objects.create(
            asignatura=self.asignatura,
            docente=self.docente,
            aula=self.aula,
            paralelo=self.paralelo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(10),
        )

        propuesta = self.generar()["propuesta"]

        self.assertIn(
            "El docente ya tiene clases",
            self.mensajes(propuesta),
        )
        self.assertEqual(propuesta.bloques.count(), 0)
        self.assertTrue(Horario.objects.filter(pk=oficial.pk).exists())

    def test_preferencia_laboratorio_permite_aula_comun(self):
        self.necesidad.prefiere_laboratorio = True
        self.necesidad.save(update_fields=["prefiere_laboratorio"])

        resultado = self.generar()
        propuesta = resultado["propuesta"]

        self.assertFalse(resultado["pendientes"])
        self.assertEqual(
            propuesta.bloques.get().aula_id,
            self.aula.pk,
        )
        self.assertEqual(
            propuesta.diagnostico_generacion["sesiones"],
            [],
        )
        self.assertTrue(resultado["avisos"])

    def test_detalle_muestra_diagnostico(self):
        self.franja.delete()
        propuesta = self.generar()["propuesta"]
        self.client.force_login(self.actor)

        respuesta = self.client.get(self.url_detalle(propuesta))

        self.assertContains(respuesta, "Diagnóstico de generación")
        self.assertContains(
            respuesta,
            "No hay franjas de planificación activas",
        )

    def test_sesion_completada_deja_de_mostrar_diagnostico(self):
        self.franja.delete()
        propuesta = self.generar()["propuesta"]

        # Simula una sesión completada después de corregir las ventanas.
        FranjaPlanificacion.objects.create(
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(10),
        )
        BloquePropuesta.objects.create(
            propuesta=propuesta,
            necesidad=self.necesidad,
            numero_sesion=1,
            aula=self.aula,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8),
            hora_fin=time(10),
        )

        self.client.force_login(self.actor)
        respuesta = self.client.get(self.url_detalle(propuesta))

        self.assertNotContains(respuesta, "Diagnóstico de generación")
        propuesta.refresh_from_db()
        self.assertTrue(
            propuesta.diagnostico_generacion["sesiones"]
        )

    def test_otro_usuario_no_puede_consultar_diagnostico(self):
        self.franja.delete()
        propuesta = self.generar()["propuesta"]
        otro = get_user_model().objects.create_user(
            username="otro_diagnostico",
        )
        self.client.force_login(otro)

        respuesta = self.client.get(self.url_detalle(propuesta))

        self.assertEqual(respuesta.status_code, 404)