from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase

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
    DisponibilidadDocente,
    FranjaParalelo,
    FranjaPlanificacion,
    Horario,
    NecesidadClase,
)

from django.urls import reverse

class FranjasParaleloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        cls.actor = Usuario.objects.create_user(
            username="coordinador_franjas",
            is_superuser=True,
            is_staff=True,
        )
        cuenta = Usuario.objects.create_user(
            username="docente_franjas",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=cuenta,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )
        programa = ProgramaAcademico.objects.create(
            codigo="PROG-FP",
            nombre="Programa de prueba",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="PER-FP",
            nombre="Periodo de prueba",
            fecha_inicio=date(2026, 11, 2),
            fecha_fin=date(2026, 11, 30),
        )
        cls.paralelo = Paralelo.objects.create(
            programa=programa,
            periodo=cls.periodo,
            nombre="CURSO A",
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="ASIG-FP",
            nombre="Asignatura de prueba",
        )
        cls.aula = Aula.objects.create(
            codigo="AULA-FP",
            nombre="Aula de prueba",
            activo=True,
        )
        cls.necesidad = NecesidadClase.objects.create(
            asignatura=cls.asignatura,
            docente=cls.docente,
            paralelo=cls.paralelo,
            sesiones_semanales=1,
            duracion_minutos=60,
        )

        for dia in (Horario.Dia.LUNES, Horario.Dia.MARTES):
            FranjaPlanificacion.objects.create(
                periodo=cls.periodo,
                dia=dia,
                hora_inicio=time(7),
                hora_fin=time(20),
            )
            DisponibilidadDocente.objects.create(
                docente=cls.docente,
                periodo=cls.periodo,
                dia=dia,
                hora_inicio=time(7),
                hora_fin=time(20),
            )

    def franja(self, inicio, fin, **extras):
        datos = {
            "paralelo": self.paralelo,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": inicio,
            "hora_fin": fin,
        }
        datos.update(extras)
        return FranjaParalelo.objects.create(**datos)

    def espacios(self):
        return list(
            GeneradorHorarios()._espacios_posibles(
                self.necesidad,
                self.periodo,
                paso_minutos=15,
            )
        )

    def candidato(self, inicio, fin):
        return Horario(
            asignatura=self.asignatura,
            docente=self.docente,
            aula=self.aula,
            paralelo=self.paralelo,
            dia=Horario.Dia.LUNES,
            hora_inicio=inicio,
            hora_fin=fin,
        )

    def test_sin_franjas_propias_usa_las_del_periodo(self):
        espacios = self.espacios()

        self.assertIn(
            (Horario.Dia.LUNES, time(7), time(8)),
            espacios,
        )
        self.assertIn(
            (Horario.Dia.MARTES, time(7), time(8)),
            espacios,
        )

    def test_restringe_horas_y_dias_del_paralelo(self):
        self.franja(time(13), time(15))

        espacios = self.espacios()

        self.assertTrue(espacios)
        for dia, inicio, fin in espacios:
            self.assertEqual(dia, Horario.Dia.LUNES)
            self.assertGreaterEqual(inicio, time(13))
            self.assertLessEqual(fin, time(15))

    def test_admite_manana_y_tarde_sin_cruzar_descanso(self):
        self.franja(time(7), time(9))
        self.franja(time(14), time(16))

        espacios = self.espacios()

        self.assertIn(
            (Horario.Dia.LUNES, time(7), time(8)),
            espacios,
        )
        self.assertIn(
            (Horario.Dia.LUNES, time(14), time(15)),
            espacios,
        )
        for _, inicio, fin in espacios:
            self.assertTrue(
                fin <= time(9) or inicio >= time(14)
            )

    def test_respeta_disponibilidad_docente(self):
        self.franja(time(13), time(15))
        DisponibilidadDocente.objects.filter(
            docente=self.docente,
        ).update(
            hora_inicio=time(7),
            hora_fin=time(12),
        )

        self.assertEqual(self.espacios(), [])

    def test_franja_inactiva_no_restringe(self):
        self.franja(time(13), time(15), activo=False)

        self.assertIn(
            (Horario.Dia.LUNES, time(7), time(8)),
            self.espacios(),
        )

    def test_validacion_rechaza_clase_fuera_de_franja(self):
        self.franja(time(13), time(15))

        with self.assertRaisesMessage(
            ValidationError,
            "franjas activas del Paralelo/Curso",
        ):
            self.candidato(
                time(8),
                time(9),
            ).validar_para_propuesta()

        self.candidato(
            time(13),
            time(14),
        ).validar_para_propuesta()

    def test_generacion_usa_inicio_del_paralelo(self):
        self.franja(time(13, 10), time(14, 10))

        resultado = GeneradorHorarios().generar(
            usuario=self.actor,
            nombre="Propuesta con franja propia",
            periodo_id=self.periodo.pk,
            necesidades_ids=[self.necesidad.pk],
        )

        self.assertFalse(resultado["pendientes"])
        bloque = resultado["propuesta"].bloques.get()
        self.assertEqual(bloque.hora_inicio, time(13, 10))
        self.assertEqual(bloque.hora_fin, time(14, 10))

    def test_diagnostico_explica_falta_de_intervalo_comun(self):
        self.franja(time(13), time(15))
        DisponibilidadDocente.objects.filter(
            docente=self.docente,
        ).update(
            hora_inicio=time(7),
            hora_fin=time(12),
        )

        resultado = GeneradorHorarios().generar(
            usuario=self.actor,
            nombre="Propuesta sin coincidencia",
            periodo_id=self.periodo.pk,
            necesidades_ids=[self.necesidad.pk],
        )

        self.assertTrue(resultado["pendientes"])
        self.assertFalse(
            resultado["propuesta"].bloques.exists()
        )

        diagnostico = (
            resultado["propuesta"]
            .diagnostico_generacion["sesiones"][0]
        )
        mensajes = " ".join(
            motivo["mensaje"]
            for motivo in diagnostico["motivos"]
        )
        self.assertIn("franjas del Paralelo/Curso", mensajes)
        
        
    def propuesta_pendiente_para_reintento(self):
        DisponibilidadDocente.objects.filter(
            docente=self.docente,
        ).update(activo=False)

        propuesta = GeneradorHorarios().generar(
            usuario=self.actor,
            nombre="Borrador para reintentar",
            periodo_id=self.periodo.pk,
            necesidades_ids=[self.necesidad.pk],
        )["propuesta"]

        DisponibilidadDocente.objects.filter(
            docente=self.docente,
        ).update(activo=True)

        return propuesta

    def test_reintento_completa_pendientes_sin_crear_otra_propuesta(self):
        propuesta = self.propuesta_pendiente_para_reintento()

        resultado = GeneradorHorarios().reintentar(
            usuario=self.actor,
            propuesta_id=propuesta.pk,
        )

        self.assertEqual(resultado["propuesta"].pk, propuesta.pk)
        self.assertEqual(resultado["agregadas"], 1)
        self.assertFalse(resultado["pendientes"])
        self.assertEqual(propuesta.bloques.count(), 1)
        self.assertEqual(Horario.objects.count(), 0)

    def test_reintento_conserva_bloques_existentes(self):
        self.necesidad.sesiones_semanales = 2
        self.necesidad.save(update_fields=["sesiones_semanales"])
        self.franja(time(7), time(8))

        propuesta = GeneradorHorarios().generar(
            usuario=self.actor,
            nombre="Borrador parcial",
            periodo_id=self.periodo.pk,
            necesidades_ids=[self.necesidad.pk],
        )["propuesta"]

        original = propuesta.bloques.get()
        campos = (
            "necesidad_id",
            "numero_sesion",
            "aula_id",
            "dia",
            "hora_inicio",
            "hora_fin",
        )
        antes = tuple(getattr(original, campo) for campo in campos)

        self.franja(
            time(14),
            time(15),
            dia=Horario.Dia.MARTES,
        )

        resultado = GeneradorHorarios().reintentar(
            usuario=self.actor,
            propuesta_id=propuesta.pk,
        )

        original.refresh_from_db()

        self.assertEqual(
            tuple(getattr(original, campo) for campo in campos),
            antes,
        )
        self.assertEqual(resultado["agregadas"], 1)
        self.assertFalse(resultado["pendientes"])
        self.assertEqual(propuesta.bloques.count(), 2)

    def test_reintento_repetido_no_duplica_sesiones(self):
        propuesta = self.propuesta_pendiente_para_reintento()
        generador = GeneradorHorarios()

        generador.reintentar(
            usuario=self.actor,
            propuesta_id=propuesta.pk,
        )
        resultado = generador.reintentar(
            usuario=self.actor,
            propuesta_id=propuesta.pk,
        )

        self.assertEqual(resultado["agregadas"], 0)
        self.assertEqual(propuesta.bloques.count(), 1)

    def test_reintento_rechaza_estado_en_revision(self):
        propuesta = self.propuesta_pendiente_para_reintento()
        propuesta.estado = "EN_REVISION"
        propuesta.save(update_fields=["estado"])

        with self.assertRaisesMessage(ValidationError, "borrador"):
            GeneradorHorarios().reintentar(
                usuario=self.actor,
                propuesta_id=propuesta.pk,
            )

        self.assertEqual(propuesta.bloques.count(), 0)

    def test_reintento_exige_permiso(self):
        propuesta = self.propuesta_pendiente_para_reintento()
        sin_permiso = get_user_model().objects.create_user(
            username="sin_permiso_reintento",
        )

        with self.assertRaises(PermissionDenied):
            GeneradorHorarios().reintentar(
                usuario=sin_permiso,
                propuesta_id=propuesta.pk,
            )

        self.assertEqual(propuesta.bloques.count(), 0)

    def test_reintento_actualiza_diagnostico(self):
        propuesta = self.propuesta_pendiente_para_reintento()

        DisponibilidadDocente.objects.filter(
            docente=self.docente,
        ).update(activo=False)

        resultado = GeneradorHorarios().reintentar(
            usuario=self.actor,
            propuesta_id=propuesta.pk,
            paso_minutos=5,
        )
        propuesta.refresh_from_db()

        self.assertEqual(resultado["agregadas"], 0)
        self.assertTrue(resultado["pendientes"])
        self.assertEqual(
            propuesta.diagnostico_generacion["tipo"],
            "reintento",
        )
        self.assertEqual(
            propuesta.diagnostico_generacion["paso_minutos"],
            5,
        )
        self.assertTrue(
            propuesta.diagnostico_generacion["sesiones"]
        )

    def test_reintento_web_rechaza_get(self):
        propuesta = self.propuesta_pendiente_para_reintento()
        self.client.force_login(self.actor)

        respuesta = self.client.get(
            reverse(
                "planificacion_web:reintentar_pendientes",
                args=[propuesta.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(propuesta.bloques.count(), 0)

    def test_reintento_web_completa_pendientes(self):
        propuesta = self.propuesta_pendiente_para_reintento()
        self.client.force_login(self.actor)

        respuesta = self.client.post(
            reverse(
                "planificacion_web:reintentar_pendientes",
                args=[propuesta.pk],
            ),
            {"paso_minutos": 5},
        )

        self.assertRedirects(
            respuesta,
            reverse(
                "planificacion_web:detalle_propuesta",
                args=[propuesta.pk],
            ),
        )
        self.assertEqual(propuesta.bloques.count(), 1)
        self.assertFalse(propuesta.obtener_pendientes())