from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from academico.models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
    Asignatura,
    Aula,
)
from usuarios.models import PerfilDocente

from .models import (
    Horario,
    NecesidadClase,
    PropuestaHorario,
    BloquePropuesta,
    FranjaPlanificacion,
    DisponibilidadDocente,
    RetiradaPublicacion,
)

from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied

from .servicios import (
    enviar_propuesta_revision,
    aprobar_propuesta,
    retirar_publicacion,
    agregar_sesion_pendiente,
)

from .generador_horarios import GeneradorHorarios

from django.urls import reverse

from .servicios import editar_bloque_propuesta

from .servicios import devolver_propuesta_borrador

class BloquePropuestaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        usuario = get_user_model().objects.create_user(
            username="autor_bloques",
        )
        docente = PerfilDocente.objects.create(
            usuario=usuario,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )
        programa = ProgramaAcademico.objects.create(
            codigo="TI",
            nombre="Tecnologías de la Información",
        )
        cls.periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2026-2",
            nombre="Periodo de demostración",
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2027, 2, 28),
        )
        grupo = Paralelo.objects.create(
            programa=programa,
            periodo=cls.periodo,
            nombre="TERCERO A",
        )
        asignatura = Asignatura.objects.create(
            codigo="PROG-01",
            nombre="Programación",
        )
        cls.necesidad = NecesidadClase.objects.create(
            asignatura=asignatura,
            docente=docente,
            paralelo=grupo,
            sesiones_semanales=2,
            duracion_minutos=120,
            prefiere_laboratorio=True,
        )
        cls.aula = Aula.objects.create(
            codigo="A-01",
            nombre="Aula común",
            tipo=Aula.Tipo.AULA,
        )
        cls.propuesta = PropuestaHorario.objects.create(
            nombre="Borrador inicial",
            periodo=cls.periodo,
            autor=usuario,
        )

    def bloque(self, **cambios):
        datos = {
            "propuesta": self.propuesta,
            "necesidad": self.necesidad,
            "numero_sesion": 1,
            "aula": self.aula,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": time(8, 0),
            "hora_fin": time(10, 0),
        }
        datos.update(cambios)
        return BloquePropuesta(**datos)

    def test_guarda_bloque_sin_publicar_horario(self):
        bloque = self.bloque()
        bloque.full_clean()
        bloque.save()

        candidato = bloque.como_horario()

        self.assertIsNone(candidato.pk)
        self.assertEqual(
            candidato.asignatura_id,
            self.necesidad.asignatura_id,
        )
        self.assertEqual(
            candidato.docente_id,
            self.necesidad.docente_id,
        )
        self.assertEqual(
            candidato.paralelo_id,
            self.necesidad.paralelo_id,
        )
        self.assertEqual(Horario.objects.count(), 0)

    def test_rechaza_necesidad_de_otro_periodo(self):
        otro_periodo = PeriodoAcademico.objects.create(
            codigo="OTRO-2027",
            nombre="Otro periodo",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        otra_propuesta = PropuestaHorario.objects.create(
            nombre="Otra propuesta",
            periodo=otro_periodo,
            autor=self.propuesta.autor,
        )

        with self.assertRaises(ValidationError) as resultado:
            self.bloque(propuesta=otra_propuesta).full_clean()

        self.assertIn("necesidad", resultado.exception.message_dict)

    def test_rechaza_duracion_distinta_de_la_solicitada(self):
        with self.assertRaises(ValidationError) as resultado:
            self.bloque(hora_fin=time(9, 0)).full_clean()

        self.assertIn("hora_fin", resultado.exception.message_dict)

    def test_rechaza_numero_de_sesion_invalido(self):
        for numero in (0, 3):
            with self.subTest(numero=numero):
                with self.assertRaises(ValidationError) as resultado:
                    self.bloque(numero_sesion=numero).full_clean()

                self.assertIn(
                    "numero_sesion",
                    resultado.exception.message_dict,
                )

    def test_base_rechaza_sesion_duplicada_en_propuesta(self):
        self.bloque().save()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.bloque().save()

    def test_preferencia_laboratorio_permite_aula_comun(self):
        bloque = self.bloque()
        bloque.full_clean()
        bloque.save()

        self.assertTrue(bloque.necesidad.prefiere_laboratorio)
        self.assertEqual(bloque.aula.tipo, Aula.Tipo.AULA)
        
        

    def _crear_ventanas(self):
        FranjaPlanificacion.objects.create(
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(7, 0),
            hora_fin=time(14, 0),
        )
        DisponibilidadDocente.objects.create(
            docente=self.necesidad.docente,
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(7, 0),
            hora_fin=time(14, 0),
        )

    def test_propuesta_valida_bloques_consecutivos_sin_publicar(self):
        self._crear_ventanas()
        self.bloque().save()
        self.bloque(
            numero_sesion=2,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
        ).save()

        self.propuesta.validar_bloques()

        self.assertEqual(Horario.objects.count(), 0)
        self.assertEqual(self.propuesta.bloques.count(), 2)

    def test_propuesta_detecta_cruce_entre_sus_bloques(self):
        self._crear_ventanas()
        self.bloque().save()
        self.bloque(
            numero_sesion=2,
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
        ).save()

        with self.assertRaises(ValidationError):
            self.propuesta.validar_bloques()

        self.assertEqual(Horario.objects.count(), 0)

    def test_propuesta_suma_carga_de_todos_sus_bloques(self):
        self._crear_ventanas()

        docente = self.necesidad.docente
        docente.horas_semanales_max = 3
        docente.save()

        self.bloque().save()
        self.bloque(
            numero_sesion=2,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
        ).save()

        with self.assertRaises(ValidationError) as resultado:
            self.propuesta.validar_bloques()

        self.assertIn(
            "máximo del docente",
            " ".join(resultado.exception.messages),
        )
        self.assertEqual(Horario.objects.count(), 0)

    def test_propuesta_detecta_cruce_con_horario_oficial(self):
        self._crear_ventanas()

        bloque = self.bloque()
        bloque.save()
        bloque.como_horario().save()

        with self.assertRaises(ValidationError):
            self.propuesta.validar_bloques()

        self.assertEqual(Horario.objects.count(), 1)

    def test_propuesta_rechaza_borrador_vacio(self):
        with self.assertRaises(ValidationError):
            self.propuesta.validar_bloques()

    def test_propuestas_alternativas_no_se_bloquean_entre_si(self):
        self._crear_ventanas()
        self.bloque().save()

        alternativa = PropuestaHorario.objects.create(
            nombre="Alternativa",
            periodo=self.periodo,
            autor=self.propuesta.autor,
        )
        self.bloque(propuesta=alternativa).save()

        self.propuesta.validar_bloques()
        alternativa.validar_bloques()

        self.assertEqual(Horario.objects.count(), 0)
        
    def test_pendientes_detecta_necesidad_sin_ningun_bloque(self):
        self.propuesta.necesidades.add(self.necesidad)

        pendientes = self.propuesta.obtener_pendientes()

        self.assertEqual(len(pendientes), 1)
        self.assertEqual(
            pendientes[0]["necesidad_id"],
            self.necesidad.pk,
        )
        self.assertEqual(pendientes[0]["sesiones"], [1, 2])

    def test_propuesta_incompleta_identifica_sesion_faltante(self):
        self.propuesta.necesidades.add(self.necesidad)
        self.bloque().save()

        pendientes = self.propuesta.obtener_pendientes()

        self.assertEqual(pendientes[0]["sesiones"], [2])

        with self.assertRaises(ValidationError):
            self.propuesta.validar_completa()

        self.assertEqual(Horario.objects.count(), 0)

    def test_propuesta_completa_valida_sin_publicar(self):
        self._crear_ventanas()
        self.propuesta.necesidades.add(self.necesidad)

        self.bloque().save()
        self.bloque(
            numero_sesion=2,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
        ).save()

        self.assertEqual(
            self.propuesta.obtener_pendientes(),
            [],
        )

        self.propuesta.validar_completa()

        self.assertEqual(Horario.objects.count(), 0)

    def test_alcance_rechaza_bloque_de_necesidad_no_seleccionada(self):
        otra_asignatura = Asignatura.objects.create(
            codigo="MAT-01",
            nombre="Matemáticas",
        )
        otra_necesidad = NecesidadClase.objects.create(
            asignatura=otra_asignatura,
            docente=self.necesidad.docente,
            paralelo=self.necesidad.paralelo,
            sesiones_semanales=1,
            duracion_minutos=120,
        )

        self.propuesta.necesidades.add(otra_necesidad)
        self.bloque().save()

        with self.assertRaises(ValidationError):
            self.propuesta.validar_alcance()

    def test_alcance_rechaza_seleccion_vacia(self):
        with self.assertRaises(ValidationError):
            self.propuesta.validar_alcance()

    def test_alcance_rechaza_necesidad_de_otro_periodo(self):
        otro_periodo = PeriodoAcademico.objects.create(
            codigo="ALCANCE-2027",
            nombre="Otro periodo",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        otro_grupo = Paralelo.objects.create(
            programa=self.necesidad.paralelo.programa,
            periodo=otro_periodo,
            nombre="OTRO GRUPO",
        )
        otra_necesidad = NecesidadClase.objects.create(
            asignatura=self.necesidad.asignatura,
            docente=self.necesidad.docente,
            paralelo=otro_grupo,
            sesiones_semanales=1,
            duracion_minutos=120,
        )
        self.propuesta.necesidades.add(otra_necesidad)

        with self.assertRaises(ValidationError):
            self.propuesta.validar_alcance()
            
            
    def _usuario_revision(self, *codigos):
        modelo = get_user_model()
        usuario = modelo.objects.create_user(
            username=f"revisor_{modelo.objects.count()}",
        )

        for codigo in codigos:
            permiso = Permission.objects.get(
                content_type__app_label="planificacion",
                content_type__model="propuestahorario",
                codename=codigo,
            )
            usuario.user_permissions.add(permiso)

        return usuario

    def _preparar_propuesta_completa(self):
        self._crear_ventanas()
        self.propuesta.necesidades.add(self.necesidad)

        self.bloque().save()
        self.bloque(
            numero_sesion=2,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
        ).save()

        return self._usuario_revision(
            "change_propuestahorario",
            "aprobar_propuestahorario",
        )

    def test_envio_y_aprobacion_publican_con_trazabilidad(self):
        usuario = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.EN_REVISION,
        )
        self.assertEqual(Horario.objects.count(), 0)

        aprobar_propuesta(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.APROBADA,
        )
        self.assertEqual(
            self.propuesta.aprobada_por_id,
            usuario.pk,
        )
        self.assertIsNotNone(self.propuesta.aprobada_en)

        origenes = set(
            Horario.objects.values_list("bloque_origen_id", flat=True)
        )
        self.assertEqual(
            origenes,
            set(self.propuesta.bloques.values_list("pk", flat=True)),
        )
        self.assertEqual(Horario.objects.count(), 2)

    def test_revision_y_aprobacion_exigen_permisos(self):
        autorizado = self._preparar_propuesta_completa()
        sin_permiso = self._usuario_revision()

        with self.assertRaises(PermissionDenied):
            enviar_propuesta_revision(
                usuario=sin_permiso,
                propuesta_id=self.propuesta.pk,
            )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )

        enviar_propuesta_revision(
            usuario=autorizado,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(PermissionDenied):
            aprobar_propuesta(
                usuario=sin_permiso,
                propuesta_id=self.propuesta.pk,
            )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.EN_REVISION,
        )
        self.assertEqual(Horario.objects.count(), 0)

    def test_no_permite_aprobar_directamente_un_borrador(self):
        usuario = self._preparar_propuesta_completa()

        with self.assertRaises(ValidationError):
            aprobar_propuesta(
                usuario=usuario,
                propuesta_id=self.propuesta.pk,
            )

        self.assertEqual(Horario.objects.count(), 0)

    def test_no_publica_dos_veces_la_misma_propuesta(self):
        usuario = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )
        aprobar_propuesta(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(ValidationError):
            aprobar_propuesta(
                usuario=usuario,
                propuesta_id=self.propuesta.pk,
            )

        self.assertEqual(Horario.objects.count(), 2)

    def test_aprobacion_revalida_conflictos_nuevos(self):
        usuario = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        # Otro proceso registró una clase después del envío.
        bloque = self.propuesta.bloques.order_by("pk").first()
        bloque.como_horario().save()

        with self.assertRaises(ValidationError):
            aprobar_propuesta(
                usuario=usuario,
                propuesta_id=self.propuesta.pk,
            )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.EN_REVISION,
        )
        self.assertIsNone(self.propuesta.aprobada_en)
        self.assertEqual(Horario.objects.count(), 1)

    def test_fallo_en_segundo_guardado_revierte_publicacion(self):
        usuario = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        guardar_original = Horario.save
        llamadas = 0

        def guardar_con_fallo(instancia, *args, **kwargs):
            nonlocal llamadas
            llamadas += 1

            if llamadas == 2:
                raise ValidationError("Fallo simulado.")

            return guardar_original(instancia, *args, **kwargs)

        with patch.object(Horario, "save", new=guardar_con_fallo):
            with self.assertRaises(ValidationError):
                aprobar_propuesta(
                    usuario=usuario,
                    propuesta_id=self.propuesta.pk,
                )

        self.assertEqual(llamadas, 2)
        self.assertEqual(Horario.objects.count(), 0)

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.EN_REVISION,
        )
        self.assertIsNone(self.propuesta.aprobada_por_id)
        self.assertIsNone(self.propuesta.aprobada_en)

    def test_no_envia_a_revision_una_propuesta_incompleta(self):
        usuario = self._usuario_revision(
            "change_propuestahorario",
        )
        self.propuesta.necesidades.add(self.necesidad)
        self.bloque().save()

        with self.assertRaises(ValidationError):
            enviar_propuesta_revision(
                usuario=usuario,
                propuesta_id=self.propuesta.pk,
            )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )
        self.assertEqual(Horario.objects.count(), 0)
        
        
    def _usuario_generador(self):
        return self._usuario_revision(
            "add_propuestahorario",
        )

    def _generar(self, usuario):
        return GeneradorHorarios().generar(
            usuario=usuario,
            nombre="Borrador automático",
            periodo_id=self.periodo.pk,
            necesidades_ids=[self.necesidad.pk],
        )

    def test_generador_crea_borrador_y_permite_aula_comun(self):
        self._crear_ventanas()
        usuario = self._usuario_generador()

        resultado = self._generar(usuario)
        propuesta = resultado["propuesta"]

        self.assertEqual(
            propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )
        self.assertEqual(propuesta.bloques.count(), 2)
        self.assertEqual(resultado["pendientes"], [])
        self.assertEqual(len(resultado["avisos"]), 2)

        propuesta.validar_completa()

        self.assertEqual(Horario.objects.count(), 0)

    def test_generador_prioriza_laboratorio_disponible(self):
        self._crear_ventanas()
        usuario = self._usuario_generador()

        laboratorio = Aula.objects.create(
            codigo="LAB-02",
            nombre="Laboratorio disponible",
            tipo=Aula.Tipo.LABORATORIO,
        )

        resultado = self._generar(usuario)

        aulas_asignadas = set(
            resultado["propuesta"].bloques.values_list(
                "aula_id",
                flat=True,
            )
        )

        self.assertEqual(aulas_asignadas, {laboratorio.pk})
        self.assertEqual(resultado["avisos"], [])

    def test_generador_informa_pendientes_sin_disponibilidad(self):
        usuario = self._usuario_generador()

        resultado = self._generar(usuario)

        self.assertEqual(
            resultado["propuesta"].bloques.count(),
            0,
        )
        self.assertEqual(
            resultado["pendientes"][0]["sesiones"],
            [1, 2],
        )
        self.assertEqual(Horario.objects.count(), 0)

    def test_generador_conserva_resultado_parcial(self):
        self._crear_ventanas()

        FranjaPlanificacion.objects.filter(
            periodo=self.periodo,
        ).update(
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
        )
        DisponibilidadDocente.objects.filter(
            periodo=self.periodo,
        ).update(
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
        )

        resultado = self._generar(self._usuario_generador())

        self.assertEqual(
            resultado["propuesta"].bloques.count(),
            1,
        )
        self.assertEqual(
            resultado["pendientes"][0]["sesiones"],
            [2],
        )

        with self.assertRaises(ValidationError):
            resultado["propuesta"].validar_completa()

    def test_generador_exige_permiso(self):
        usuario = self._usuario_revision()
        cantidad_anterior = PropuestaHorario.objects.count()

        with self.assertRaises(PermissionDenied):
            self._generar(usuario)

        self.assertEqual(
            PropuestaHorario.objects.count(),
            cantidad_anterior,
        )
        

    def _preparar_revision_web(self):
        usuario = self._preparar_propuesta_completa()

        permiso = Permission.objects.get(
            content_type__app_label="planificacion",
            content_type__model="propuestahorario",
            codename="view_propuestahorario",
        )
        usuario.user_permissions.add(permiso)
        self.client.force_login(usuario)

        return usuario

    def test_web_envia_y_aprueba_propuesta(self):
        self._preparar_revision_web()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:enviar_revision",
                args=[self.propuesta.pk],
            )
        )
        self.assertEqual(respuesta.status_code, 302)

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.EN_REVISION,
        )
        self.assertEqual(Horario.objects.count(), 0)

        respuesta = self.client.post(
            reverse(
                "planificacion_web:aprobar_propuesta",
                args=[self.propuesta.pk],
            ),
            follow=True,
        )

        self.assertEqual(respuesta.status_code, 200)
        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.APROBADA,
        )
        self.assertEqual(Horario.objects.count(), 2)

    def test_web_acciones_rechazan_get(self):
        self._preparar_revision_web()

        for nombre in ("enviar_revision", "aprobar_propuesta"):
            with self.subTest(accion=nombre):
                respuesta = self.client.get(
                    reverse(
                        f"planificacion_web:{nombre}",
                        args=[self.propuesta.pk],
                    )
                )
                self.assertEqual(respuesta.status_code, 405)

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )
        self.assertEqual(Horario.objects.count(), 0)

    def test_web_aprobacion_exige_permiso(self):
        usuario = self._usuario_revision()
        self.client.force_login(usuario)

        respuesta = self.client.post(
            reverse(
                "planificacion_web:aprobar_propuesta",
                args=[self.propuesta.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Horario.objects.count(), 0)

    def test_web_no_envia_propuesta_incompleta(self):
        usuario = self._usuario_revision(
            "change_propuestahorario",
            "view_propuestahorario",
        )
        self.client.force_login(usuario)

        self.propuesta.necesidades.add(self.necesidad)
        self.bloque().save()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:enviar_revision",
                args=[self.propuesta.pk],
            ),
            follow=True,
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "faltan las sesiones")

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )
        self.assertEqual(Horario.objects.count(), 0)
        
    def test_generador_prefiere_repartir_sesiones_entre_dias(self):
        self._crear_ventanas()

        FranjaPlanificacion.objects.create(
            periodo=self.periodo,
            dia=Horario.Dia.MARTES,
            hora_inicio=time(7, 0),
            hora_fin=time(14, 0),
        )
        DisponibilidadDocente.objects.create(
            docente=self.necesidad.docente,
            periodo=self.periodo,
            dia=Horario.Dia.MARTES,
            hora_inicio=time(7, 0),
            hora_fin=time(14, 0),
        )

        resultado = self._generar(self._usuario_generador())
        propuesta = resultado["propuesta"]

        dias = set(
            propuesta.bloques.values_list("dia", flat=True)
        )

        self.assertEqual(
            dias,
            {Horario.Dia.LUNES, Horario.Dia.MARTES},
        )
        self.assertEqual(resultado["pendientes"], [])
        propuesta.validar_completa()

    def test_generador_permite_mismo_dia_si_no_hay_otro_disponible(self):
        self._crear_ventanas()

        resultado = self._generar(self._usuario_generador())
        propuesta = resultado["propuesta"]

        self.assertEqual(propuesta.bloques.count(), 2)
        self.assertEqual(
            set(propuesta.bloques.values_list("dia", flat=True)),
            {Horario.Dia.LUNES},
        )
        self.assertEqual(resultado["pendientes"], [])
        propuesta.validar_completa()
        
        
    def _usuario_editor(self, puede_ver_ajenas=True):
        codigos = (
            ("view_propuestahorario",)
            if puede_ver_ajenas
            else ()
        )
        usuario = self._usuario_revision(*codigos)

        permiso = Permission.objects.get(
            content_type__app_label="planificacion",
            content_type__model="bloquepropuesta",
            codename="change_bloquepropuesta",
        )
        usuario.user_permissions.add(permiso)

        return usuario

    def test_web_edita_bloque_valido(self):
        self._preparar_propuesta_completa()
        usuario = self._usuario_editor()
        self.client.force_login(usuario)

        bloque = self.propuesta.bloques.order_by("pk").first()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_bloque",
                args=[self.propuesta.pk, bloque.pk],
            ),
            {
                "aula": self.aula.pk,
                "dia": Horario.Dia.LUNES,
                "hora_inicio": "12:00",
                "hora_fin": "14:00",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        bloque.refresh_from_db()
        self.assertEqual(bloque.hora_inicio, time(12, 0))
        self.assertEqual(bloque.hora_fin, time(14, 0))
        self.assertEqual(Horario.objects.count(), 0)

    def test_web_edicion_con_conflicto_conserva_original(self):
        self._preparar_propuesta_completa()
        usuario = self._usuario_editor()
        self.client.force_login(usuario)

        bloque = self.propuesta.bloques.order_by("pk").first()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_bloque",
                args=[self.propuesta.pk, bloque.pk],
            ),
            {
                "aula": self.aula.pk,
                "dia": Horario.Dia.LUNES,
                "hora_inicio": "09:00",
                "hora_fin": "11:00",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "se cruzan")

        bloque.refresh_from_db()
        self.assertEqual(bloque.hora_inicio, time(8, 0))
        self.assertEqual(bloque.hora_fin, time(10, 0))
        self.assertEqual(Horario.objects.count(), 0)

    def test_edicion_rechaza_propuesta_en_revision_y_aprobada(self):
        revisor = self._preparar_propuesta_completa()
        editor = self._usuario_editor()
        bloque = self.propuesta.bloques.order_by("pk").first()

        enviar_propuesta_revision(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(ValidationError):
            editar_bloque_propuesta(
                usuario=editor,
                bloque_id=bloque.pk,
                hora_inicio=time(12, 0),
                hora_fin=time(14, 0),
            )

        aprobar_propuesta(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(ValidationError):
            editar_bloque_propuesta(
                usuario=editor,
                bloque_id=bloque.pk,
                hora_inicio=time(12, 0),
                hora_fin=time(14, 0),
            )

        bloque.refresh_from_db()
        self.assertEqual(bloque.hora_inicio, time(8, 0))
        self.assertEqual(Horario.objects.count(), 2)

    def test_editor_no_accede_a_propuesta_ajena_sin_permiso_de_lectura(self):
        self._preparar_propuesta_completa()
        usuario = self._usuario_editor(puede_ver_ajenas=False)
        self.client.force_login(usuario)

        bloque = self.propuesta.bloques.order_by("pk").first()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_bloque",
                args=[self.propuesta.pk, bloque.pk],
            ),
            {
                "aula": self.aula.pk,
                "dia": Horario.Dia.LUNES,
                "hora_inicio": "12:00",
                "hora_fin": "14:00",
            },
        )

        self.assertEqual(respuesta.status_code, 404)

        with self.assertRaises(PermissionDenied):
            editar_bloque_propuesta(
                usuario=usuario,
                bloque_id=bloque.pk,
                hora_inicio=time(12, 0),
                hora_fin=time(14, 0),
            )

        bloque.refresh_from_db()
        self.assertEqual(bloque.hora_inicio, time(8, 0))
        
    def test_web_devuelve_propuesta_y_permite_corregir(self):
        revisor = self._preparar_revision_web()

        enviar_propuesta_revision(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )

        respuesta = self.client.post(
            reverse(
                "planificacion_web:devolver_borrador",
                args=[self.propuesta.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )

        bloque = self.propuesta.bloques.order_by("pk").first()
        editor = self._usuario_editor()

        editar_bloque_propuesta(
            usuario=editor,
            bloque_id=bloque.pk,
            hora_inicio=time(12, 0),
            hora_fin=time(14, 0),
        )

        bloque.refresh_from_db()
        self.assertEqual(bloque.hora_inicio, time(12, 0))
        self.assertEqual(Horario.objects.count(), 0)

    def test_web_devolver_exige_permiso_de_revision(self):
        revisor = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )

        usuario = self._usuario_revision(
            "view_propuestahorario",
            "change_propuestahorario",
        )
        self.client.force_login(usuario)

        respuesta = self.client.post(
            reverse(
                "planificacion_web:devolver_borrador",
                args=[self.propuesta.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 403)

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.EN_REVISION,
        )

    def test_no_devuelve_a_borrador_una_propuesta_aprobada(self):
        revisor = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )
        aprobar_propuesta(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(ValidationError):
            devolver_propuesta_borrador(
                usuario=revisor,
                propuesta_id=self.propuesta.pk,
            )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.APROBADA,
        )
        self.assertEqual(Horario.objects.count(), 2)
        
    def _publicacion_para_corregir(self):
        usuario = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )
        aprobar_propuesta(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        permiso = Permission.objects.get(
            content_type__app_label="planificacion",
            content_type__model="horario",
            codename="delete_horario",
        )
        usuario.user_permissions.add(permiso)

        # Nueva instancia para evitar la caché de permisos anterior.
        return get_user_model().objects.get(pk=usuario.pk)

    def test_retira_publicacion_conservando_borrador_y_registro(self):
        usuario = self._publicacion_para_corregir()

        retirar_publicacion(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
            motivo="Se asignó un horario equivocado.",
        )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.BORRADOR,
        )
        self.assertEqual(Horario.objects.count(), 0)
        self.assertEqual(self.propuesta.bloques.count(), 2)
        self.assertIsNone(self.propuesta.aprobada_en)

        registro = self.propuesta.retiradas.get()
        self.assertEqual(registro.usuario_id, usuario.pk)
        self.assertEqual(
            len(registro.datos_publicacion["horarios"]),
            2,
        )

    def test_retira_publicacion_exige_permiso_de_eliminacion(self):
        usuario = self._preparar_propuesta_completa()

        enviar_propuesta_revision(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )
        aprobar_propuesta(
            usuario=usuario,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(PermissionDenied):
            retirar_publicacion(
                usuario=usuario,
                propuesta_id=self.propuesta.pk,
                motivo="Corrección del horario publicado.",
            )

        self.assertEqual(Horario.objects.count(), 2)
        self.assertEqual(RetiradaPublicacion.objects.count(), 0)

    def test_fallo_al_retirar_revierte_toda_la_operacion(self):
        usuario = self._publicacion_para_corregir()

        with patch.object(
            PropuestaHorario,
            "save",
            side_effect=ValidationError("Fallo simulado."),
        ):
            with self.assertRaises(ValidationError):
                retirar_publicacion(
                    usuario=usuario,
                    propuesta_id=self.propuesta.pk,
                    motivo="Corrección del horario publicado.",
                )

        self.propuesta.refresh_from_db()
        self.assertEqual(
            self.propuesta.estado,
            PropuestaHorario.Estado.APROBADA,
        )
        self.assertEqual(Horario.objects.count(), 2)
        self.assertEqual(RetiradaPublicacion.objects.count(), 0)
        
        
    def test_generador_rechaza_docente_retirado(self):
        self._crear_ventanas()

        docente = self.necesidad.docente
        docente.activo = False
        docente.save()

        cantidad_anterior = PropuestaHorario.objects.count()

        with self.assertRaises(ValidationError):
            self._generar(self._usuario_generador())

        self.assertEqual(
            PropuestaHorario.objects.count(),
            cantidad_anterior,
        )
        
        
    def _preparar_sesion_pendiente_web(self):
        self._crear_ventanas()
        self.propuesta.necesidades.add(self.necesidad)
        self.bloque().save()

        usuario = self._usuario_revision(
            "view_propuestahorario",
        )
        permiso = Permission.objects.get(
            content_type__app_label="planificacion",
            content_type__model="bloquepropuesta",
            codename="add_bloquepropuesta",
        )
        usuario.user_permissions.add(permiso)
        self.client.force_login(usuario)

        return usuario

    def _datos_sesion_pendiente(self, inicio="10:00"):
        return {
            "sesion": f"{self.necesidad.pk}:2",
            "aula": self.aula.pk,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": inicio,
        }

    def test_web_agrega_sesion_y_calcula_hora_final(self):
        self._preparar_sesion_pendiente_web()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:agregar_sesion",
                args=[self.propuesta.pk],
            ),
            self._datos_sesion_pendiente(),
        )

        self.assertEqual(respuesta.status_code, 302)

        bloque = self.propuesta.bloques.get(numero_sesion=2)
        self.assertEqual(bloque.hora_inicio, time(10, 0))
        self.assertEqual(bloque.hora_fin, time(12, 0))
        self.assertEqual(self.propuesta.obtener_pendientes(), [])
        self.assertEqual(Horario.objects.count(), 0)

    def test_web_sesion_con_conflicto_no_se_guarda(self):
        self._preparar_sesion_pendiente_web()

        respuesta = self.client.post(
            reverse(
                "planificacion_web:agregar_sesion",
                args=[self.propuesta.pk],
            ),
            self._datos_sesion_pendiente(inicio="09:00"),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "se cruzan")
        self.assertEqual(self.propuesta.bloques.count(), 1)
        self.assertEqual(
            self.propuesta.obtener_pendientes()[0]["sesiones"],
            [2],
        )

    def test_agregar_sesion_rechaza_propuesta_en_revision(self):
        usuario = self._preparar_sesion_pendiente_web()

        self.bloque(
            numero_sesion=2,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
        ).save()

        revisor = self._usuario_revision(
            "change_propuestahorario",
        )
        enviar_propuesta_revision(
            usuario=revisor,
            propuesta_id=self.propuesta.pk,
        )

        with self.assertRaises(ValidationError):
            agregar_sesion_pendiente(
                usuario=usuario,
                propuesta_id=self.propuesta.pk,
                necesidad_id=self.necesidad.pk,
                numero_sesion=2,
                aula=self.aula,
                dia=Horario.Dia.LUNES,
                hora_inicio=time(12, 0),
            )

        self.assertEqual(self.propuesta.bloques.count(), 2)

    def test_web_agregar_sesion_exige_permiso(self):
        self._preparar_sesion_pendiente_web()

        usuario = self._usuario_revision(
            "view_propuestahorario",
        )
        self.client.force_login(usuario)

        respuesta = self.client.post(
            reverse(
                "planificacion_web:agregar_sesion",
                args=[self.propuesta.pk],
            ),
            self._datos_sesion_pendiente(),
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.propuesta.bloques.count(), 1)