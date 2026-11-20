from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from academico.models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
    Asignatura,
    Aula,
    Inscripcion,
)
from usuarios.models import PerfilDocente, PerfilEstudiante

from .models import (
    Horario,
    FranjaPlanificacion,
    DisponibilidadDocente,
)
from .servicios import (
    crear_horario,
    actualizar_horario,
    eliminar_horario,
)
from .validaciones_paralelo import ValidadorFranjaParalelo

from django.urls import reverse

from unittest.mock import patch
from usuarios.servicios_docentes import editar_perfil_docente

class HorarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        cls.paralelo = Paralelo.objects.create(
            programa=programa,
            periodo=cls.periodo,
            nombre="TERCERO A",
        )
        cls.asignatura = Asignatura.objects.create(
            codigo="PROG-01",
            nombre="Programación",
        )
        cls.aula = Aula.objects.create(
            codigo="LAB-01",
            nombre="Laboratorio de programación",
            tipo=Aula.Tipo.LABORATORIO,
        )
        usuario = get_user_model().objects.create_user(
            username="docente_prueba",
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=usuario,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )

    def horario(self, **cambios):
        datos = {
            "asignatura": self.asignatura,
            "docente": self.docente,
            "aula": self.aula,
            "paralelo": self.paralelo,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": time(8, 0),
            "hora_fin": time(10, 0),
        }
        datos.update(cambios)
        return Horario(**datos)

    def test_guarda_horario_y_obtiene_periodo_del_grupo(self):
        horario = self.horario()
        horario.full_clean()
        horario.save()
        horario.refresh_from_db()

        self.assertEqual(horario.periodo.pk, self.periodo.pk)
        self.assertEqual(horario.hora_inicio, time(8, 0))
        self.assertEqual(horario.hora_fin, time(10, 0))

    def test_rechaza_horas_iguales(self):
        horario = self.horario(hora_fin=time(8, 0))

        with self.assertRaises(ValidationError) as resultado:
            horario.full_clean()

        self.assertIn("hora_fin", resultado.exception.message_dict)

    def test_rechaza_fin_anterior_al_inicio(self):
        horario = self.horario(hora_fin=time(7, 0))

        with self.assertRaises(ValidationError):
            horario.full_clean()

    def test_rechaza_dia_invalido(self):
        horario = self.horario(dia=8)

        with self.assertRaises(ValidationError):
            horario.full_clean()

    def test_base_rechaza_horas_invalidas(self):
        for hora_fin in (time(8, 0), time(7, 0)):
            with self.subTest(hora_fin=hora_fin):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.horario(hora_fin=hora_fin).save()

    def test_base_rechaza_dias_fuera_del_rango(self):
        for dia in (0, 8):
            with self.subTest(dia=dia):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.horario(dia=dia).save()
                        
                        
                        
                        
    def test_rechaza_cruce_independiente_por_cada_recurso(self):
        original = self.horario()
        original.full_clean()
        original.save()

        otra_aula = Aula.objects.create(
            codigo="A-02",
            nombre="Otra aula",
        )
        otro_grupo = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=self.periodo,
            nombre="TERCERO B",
        )
        otro_usuario = get_user_model().objects.create_user(
            username="otro_docente",
        )
        otro_docente = PerfilDocente.objects.create(
            usuario=otro_usuario,
            titulo="Ingeniero",
            area="Programación",
            horas_semanales_max=20,
        )

        alternativas = {
            "docente": otro_docente,
            "aula": otra_aula,
            "paralelo": otro_grupo,
        }
        originales = {
            "docente": self.docente,
            "aula": self.aula,
            "paralelo": self.paralelo,
        }

        for campo in originales:
            with self.subTest(recurso=campo):
                datos = alternativas.copy()
                datos[campo] = originales[campo]

                candidato = self.horario(
                    hora_inicio=time(9, 0),
                    hora_fin=time(11, 0),
                    **datos,
                )

                with self.assertRaises(ValidationError) as resultado:
                    candidato.full_clean()

                self.assertEqual(
                    set(resultado.exception.message_dict),
                    {campo},
                )

    def test_permite_horarios_consecutivos(self):
        self.horario().save()

        for inicio, fin in (
            (time(6, 0), time(8, 0)),
            (time(10, 0), time(12, 0)),
        ):
            with self.subTest(inicio=inicio, fin=fin):
                candidato = self.horario(
                    hora_inicio=inicio,
                    hora_fin=fin,
                )
                candidato.full_clean()
                candidato.save()

    def test_permite_mismas_horas_en_otro_dia(self):
        self.horario().save()

        candidato = self.horario(dia=Horario.Dia.MARTES)
        candidato.full_clean()
        candidato.save()

    def test_edicion_no_choca_consigo_misma(self):
        horario = self.horario()
        horario.full_clean()
        horario.save()

        horario.hora_fin = time(11, 0)
        horario.full_clean()
        horario.save()
        horario.refresh_from_db()

        self.assertEqual(horario.hora_fin, time(11, 0))

    def test_detecta_cruce_entre_periodos_superpuestos(self):
        self.horario().save()

        otro_periodo = PeriodoAcademico.objects.create(
            codigo="OTRO-2026",
            nombre="Periodo superpuesto",
            fecha_inicio=date(2026, 11, 1),
            fecha_fin=date(2026, 12, 31),
        )
        otro_grupo = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=otro_periodo,
            nombre="GRUPO ESPECIAL",
        )
        candidato = self.horario(paralelo=otro_grupo)

        with self.assertRaises(ValidationError) as resultado:
            candidato.full_clean()

        self.assertEqual(
            set(resultado.exception.message_dict),
            {"docente", "aula"},
        )

    def test_permite_reutilizar_recursos_en_periodos_separados(self):
        self.horario().save()

        otro_periodo = PeriodoAcademico.objects.create(
            codigo="DEMO-2027-1",
            nombre="Periodo posterior",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        otro_grupo = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=otro_periodo,
            nombre="TERCERO A",
        )
        candidato = self.horario(paralelo=otro_grupo)
        candidato.full_clean()
        candidato.save()

    def test_no_hay_cruce_si_fechas_compartidas_no_incluyen_el_dia(self):
        # El 1 de noviembre de 2026 es domingo.
        periodo_corto = PeriodoAcademico.objects.create(
            codigo="CORTO-2026",
            nombre="Fin de semana",
            fecha_inicio=date(2026, 10, 31),
            fecha_fin=date(2026, 11, 1),
        )
        grupo_corto = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=periodo_corto,
            nombre="GRUPO CORTO",
        )
        self.horario().save()

        # Ambos bloques son lunes, pero el periodo corto
        # no contiene ningún lunes.
        candidato = self.horario(paralelo=grupo_corto)
        candidato.full_clean()
        
    
    
    
    def _usuario_con_permisos(self, *codigos):
        modelo_usuario = get_user_model()
        usuario = modelo_usuario.objects.create_user(
            username=f"gestor_{modelo_usuario.objects.count()}",
        )

        for codigo in codigos:
            permiso = Permission.objects.get(
                content_type__app_label="planificacion",
                content_type__model="horario",
                codename=codigo,
            )
            usuario.user_permissions.add(permiso)

        return usuario

    def _datos_servicio(self):
        return {
            "asignatura": self.asignatura,
            "docente": self.docente,
            "aula": self.aula,
            "paralelo": self.paralelo,
            "dia": Horario.Dia.LUNES,
            "hora_inicio": time(8, 0),
            "hora_fin": time(10, 0),
        }

    def test_servicio_rechaza_creacion_sin_autorizacion(self):
        staff = self._usuario_con_permisos()
        staff.is_staff = True
        staff.save()

        inactivo = self._usuario_con_permisos("add_horario")
        inactivo.is_active = False
        inactivo.save()

        for usuario in (AnonymousUser(), staff, inactivo):
            with self.subTest(usuario=str(usuario)):
                with self.assertRaises(PermissionDenied):
                    crear_horario(
                        usuario=usuario,
                        **self._datos_servicio(),
                    )

        self.assertEqual(Horario.objects.count(), 0)

    def test_servicio_crea_con_permiso(self):
        usuario = self._usuario_con_permisos("add_horario")

        horario = crear_horario(
            usuario=usuario,
            **self._datos_servicio(),
        )

        self.assertTrue(
            Horario.objects.filter(pk=horario.pk).exists()
        )

    def test_servicio_rechaza_edicion_sin_permiso(self):
        original = self.horario()
        original.save()
        usuario = self._usuario_con_permisos("add_horario")

        with self.assertRaises(PermissionDenied):
            actualizar_horario(
                usuario=usuario,
                horario_id=original.pk,
                hora_fin=time(11, 0),
            )

        original.refresh_from_db()
        self.assertEqual(original.hora_fin, time(10, 0))

    def test_servicio_edicion_rechazada_conserva_original(self):
        self.horario().save()

        original = self.horario(dia=Horario.Dia.MARTES)
        original.save()
        usuario = self._usuario_con_permisos("change_horario")

        with self.assertRaises(ValidationError):
            actualizar_horario(
                usuario=usuario,
                horario_id=original.pk,
                dia=Horario.Dia.LUNES,
                hora_inicio=time(9, 0),
                hora_fin=time(11, 0),
            )

        # El objeto que tenía el llamador tampoco cambió.
        self.assertEqual(original.dia, Horario.Dia.MARTES)
        self.assertEqual(original.hora_inicio, time(8, 0))

        # Comprobamos también lo que realmente quedó guardado.
        original.refresh_from_db()
        self.assertEqual(original.dia, Horario.Dia.MARTES)
        self.assertEqual(original.hora_inicio, time(8, 0))
        self.assertEqual(original.hora_fin, time(10, 0))
        self.assertEqual(Horario.objects.count(), 2)

    def test_servicio_actualiza_con_permiso(self):
        original = self.horario()
        original.save()
        usuario = self._usuario_con_permisos("change_horario")

        actualizado = actualizar_horario(
            usuario=usuario,
            horario_id=original.pk,
            hora_fin=time(11, 0),
        )

        original.refresh_from_db()
        self.assertEqual(actualizado.pk, original.pk)
        self.assertEqual(original.hora_fin, time(11, 0))

    def test_servicio_elimina_solo_con_permiso(self):
        original = self.horario()
        original.save()
        identificador = original.pk

        sin_permiso = self._usuario_con_permisos()

        with self.assertRaises(PermissionDenied):
            eliminar_horario(
                usuario=sin_permiso,
                horario_id=identificador,
            )

        self.assertTrue(
            Horario.objects.filter(pk=identificador).exists()
        )

        autorizado = self._usuario_con_permisos("delete_horario")
        eliminar_horario(
            usuario=autorizado,
            horario_id=identificador,
        )

        self.assertFalse(
            Horario.objects.filter(pk=identificador).exists()
        )

    def test_servicio_rechaza_campos_no_permitidos(self):
        usuario = self._usuario_con_permisos("add_horario")

        with self.assertRaises(ValidationError):
            crear_horario(
                usuario=usuario,
                id=999,
                **self._datos_servicio(),
            )

        self.assertEqual(Horario.objects.count(), 0)
        
        
    def _fijar_limite_docente(self, horas):
        self.docente.horas_semanales_max = horas
        self.docente.save()

    def test_carga_permite_limite_exacto_y_rechaza_exceso(self):
        # Dos clases de 10 horas completan el límite de 20.
        for dia in (Horario.Dia.LUNES, Horario.Dia.MARTES):
            horario = self.horario(
                dia=dia,
                hora_inicio=time(8, 0),
                hora_fin=time(18, 0),
            )
            horario.full_clean()
            horario.save()

        adicional = self.horario(
            dia=Horario.Dia.MIERCOLES,
            hora_inicio=time(8, 0),
            hora_fin=time(9, 0),
        )

        with self.assertRaises(ValidationError) as resultado:
            adicional.full_clean()

        self.assertIn("docente", resultado.exception.message_dict)

    def test_carga_cuenta_minutos_sin_redondear(self):
        self._fijar_limite_docente(1)

        original = self.horario(
            hora_inicio=time(8, 0),
            hora_fin=time(8, 30),
        )
        original.full_clean()
        original.save()

        # 30 + 31 minutos superan una hora.
        adicional = self.horario(
            dia=Horario.Dia.MARTES,
            hora_inicio=time(8, 0),
            hora_fin=time(8, 31),
        )

        with self.assertRaises(ValidationError):
            adicional.full_clean()

    def test_carga_edicion_no_cuenta_dos_veces_el_original(self):
        self._fijar_limite_docente(2)

        horario = self.horario()
        horario.full_clean()
        horario.save()

        horario.hora_inicio = time(9, 0)
        horario.hora_fin = time(11, 0)
        horario.full_clean()
        horario.save()

    def test_servicio_conserva_original_si_edicion_supera_carga(self):
        self._fijar_limite_docente(3)

        lunes = self.horario()
        lunes.full_clean()
        lunes.save()

        martes = self.horario(
            dia=Horario.Dia.MARTES,
            hora_fin=time(9, 0),
        )
        martes.full_clean()
        martes.save()

        usuario = self._usuario_con_permisos("change_horario")

        with self.assertRaises(ValidationError):
            actualizar_horario(
                usuario=usuario,
                horario_id=martes.pk,
                hora_fin=time(10, 0),
            )

        martes.refresh_from_db()
        self.assertEqual(martes.hora_fin, time(9, 0))
        self.assertEqual(Horario.objects.count(), 2)

    def test_carga_no_suma_periodos_de_semanas_distintas(self):
        self._fijar_limite_docente(2)

        original = self.horario()
        original.full_clean()
        original.save()

        periodo_futuro = PeriodoAcademico.objects.create(
            codigo="FUTURO-2027",
            nombre="Periodo futuro",
            fecha_inicio=date(2027, 3, 1),
            fecha_fin=date(2027, 7, 31),
        )
        grupo_futuro = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=periodo_futuro,
            nombre="GRUPO FUTURO",
        )

        candidato = self.horario(paralelo=grupo_futuro)
        candidato.full_clean()
        candidato.save()

    def test_carga_suma_periodos_separados_en_la_misma_semana(self):
        self._fijar_limite_docente(3)

        periodo_uno = PeriodoAcademico.objects.create(
            codigo="CORTO-UNO",
            nombre="Lunes y martes",
            fecha_inicio=date(2026, 11, 2),
            fecha_fin=date(2026, 11, 3),
        )
        periodo_dos = PeriodoAcademico.objects.create(
            codigo="CORTO-DOS",
            nombre="Jueves y viernes",
            fecha_inicio=date(2026, 11, 5),
            fecha_fin=date(2026, 11, 6),
        )
        grupo_uno = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=periodo_uno,
            nombre="GRUPO UNO",
        )
        grupo_dos = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=periodo_dos,
            nombre="GRUPO DOS",
        )

        original = self.horario(
            paralelo=grupo_uno,
            dia=Horario.Dia.MARTES,
        )
        original.full_clean()
        original.save()

        candidato = self.horario(
            paralelo=grupo_dos,
            dia=Horario.Dia.JUEVES,
        )

        # No hay cruce de fechas ni horas, pero son
        # cuatro horas de trabajo en la misma semana.
        with self.assertRaises(ValidationError) as resultado:
            candidato.full_clean()

        self.assertIn("docente", resultado.exception.message_dict)
        

    def _crear_ventanas(self, inicio=time(8, 0), fin=time(10, 0)):
        franja = FranjaPlanificacion.objects.create(
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=inicio,
            hora_fin=fin,
        )
        disponibilidad = DisponibilidadDocente.objects.create(
            docente=self.docente,
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=inicio,
            hora_fin=fin,
        )
        return franja, disponibilidad

    def test_propuesta_acepta_limites_exactos_sin_guardar(self):
        self._crear_ventanas()

        self.horario().validar_para_propuesta()

        self.assertEqual(Horario.objects.count(), 0)

    def test_propuesta_detiene_la_cadena_si_los_datos_son_invalidos(self):
        candidato = self.horario(hora_fin=time(7))

        with patch.object(ValidadorFranjaParalelo, "validar") as validar_franja:
            with self.assertRaises(ValidationError) as resultado:
                candidato.validar_para_propuesta()

        self.assertIn("hora_fin", resultado.exception.message_dict)
        validar_franja.assert_not_called()

    def test_propuesta_rechaza_falta_de_franja(self):
        DisponibilidadDocente.objects.create(
            docente=self.docente,
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
        )

        with self.assertRaises(ValidationError) as resultado:
            self.horario().validar_para_propuesta()

        self.assertEqual(
            set(resultado.exception.message_dict),
            {"hora_inicio"},
        )

    def test_propuesta_rechaza_falta_de_disponibilidad(self):
        FranjaPlanificacion.objects.create(
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
        )

        candidato = self.horario()

        DisponibilidadDocente.objects.create(
            docente=candidato.docente,
            periodo=self.periodo,
            dia=Horario.Dia.LUNES,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            activo=False,
        )

        with self.assertRaises(ValidationError) as resultado:
            candidato.validar_para_propuesta()

        self.assertEqual(
            set(resultado.exception.message_dict),
            {"docente"},
        )

    def test_propuesta_ignora_ventanas_inactivas(self):
        franja, disponibilidad = self._crear_ventanas()

        for objeto, campo_error in (
            (franja, "hora_inicio"),
            (disponibilidad, "docente"),
        ):
            with self.subTest(modelo=type(objeto).__name__):
                objeto.activo = False
                objeto.save()

                with self.assertRaises(ValidationError) as resultado:
                    self.horario().validar_para_propuesta()

                self.assertEqual(
                    set(resultado.exception.message_dict),
                    {campo_error},
                )

                objeto.activo = True
                objeto.save()

    def test_propuesta_rechaza_cobertura_parcial(self):
        franja, disponibilidad = self._crear_ventanas()

        for objeto, campo_error in (
            (franja, "hora_inicio"),
            (disponibilidad, "docente"),
        ):
            with self.subTest(modelo=type(objeto).__name__):
                objeto.hora_fin = time(9, 59)
                objeto.save()

                with self.assertRaises(ValidationError) as resultado:
                    self.horario().validar_para_propuesta()

                self.assertEqual(
                    set(resultado.exception.message_dict),
                    {campo_error},
                )

                objeto.hora_fin = time(10, 0)
                objeto.save()

    def test_propuesta_combina_ventanas_consecutivas(self):
        self._crear_ventanas(time(8, 0), time(9, 0))
        self._crear_ventanas(time(9, 0), time(10, 0))

        self.horario().validar_para_propuesta()

    def test_propuesta_no_atraviesa_descansos(self):
        self._crear_ventanas(time(8, 0), time(9, 0))
        self._crear_ventanas(time(9, 15), time(10, 0))

        with self.assertRaises(ValidationError) as resultado:
            self.horario().validar_para_propuesta()

        self.assertEqual(
            set(resultado.exception.message_dict),
            {"hora_inicio", "docente"},
        )

    def test_propuesta_rechaza_dia_sin_fechas_en_periodo(self):
        periodo_corto = PeriodoAcademico.objects.create(
            codigo="SOLO-FIN-SEMANA",
            nombre="Sábado y domingo",
            fecha_inicio=date(2026, 10, 31),
            fecha_fin=date(2026, 11, 1),
        )
        grupo_corto = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=periodo_corto,
            nombre="GRUPO CORTO",
        )

        with self.assertRaises(ValidationError) as resultado:
            self.horario(
                paralelo=grupo_corto,
            ).validar_para_propuesta()

        self.assertIn("dia", resultado.exception.message_dict)
        
    def _crear_horarios_para_filtros(self):
        primero = self.horario()
        primero.save()

        usuario = get_user_model().objects.create_user(
            username="docente_filtros_dos",
        )
        docente = PerfilDocente.objects.create(
            usuario=usuario,
            titulo="Ingeniero",
            area="Redes",
            horas_semanales_max=20,
        )
        aula = Aula.objects.create(
            codigo="A-FILTROS",
            nombre="Otra aula",
        )
        paralelo = Paralelo.objects.create(
            programa=self.paralelo.programa,
            periodo=self.periodo,
            nombre="TERCERO B",
        )
        segundo = self.horario(
            docente=docente,
            aula=aula,
            paralelo=paralelo,
        )
        segundo.save()

        return primero, segundo

    def test_inicio_filtra_por_docente_aula_y_paralelo(self):
        primero, _ = self._crear_horarios_para_filtros()

        usuario = self._usuario_con_permisos("view_horario")
        self.client.force_login(usuario)

        for campo, valor in (
            ("docente", primero.docente_id),
            ("aula", primero.aula_id),
            ("paralelo", primero.paralelo_id),
        ):
            with self.subTest(filtro=campo):
                respuesta = self.client.get(
                    reverse("planificacion_web:inicio"),
                    {
                        "periodo": self.periodo.pk,
                        campo: valor,
                    },
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(
                    respuesta.context["total_bloques"],
                    1,
                )

    def test_filtros_incompatibles_muestran_resultado_vacio(self):
        primero, segundo = self._crear_horarios_para_filtros()

        usuario = self._usuario_con_permisos("view_horario")
        self.client.force_login(usuario)

        respuesta = self.client.get(
            reverse("planificacion_web:inicio"),
            {
                "periodo": self.periodo.pk,
                "docente": primero.docente_id,
                "aula": segundo.aula_id,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total_bloques"], 0)

    def test_exportacion_ics_respeta_filtros_y_fechas_del_periodo(self):
        self.periodo.fecha_fin = date(2026, 10, 19)
        self.periodo.save()
        primero, segundo = self._crear_horarios_para_filtros()
        self.client.force_login(self._usuario_con_permisos("view_horario"))
        url = reverse("planificacion_web:inicio")
        filtros = {"periodo": self.periodo.pk, "aula": primero.aula_id}
        pagina = self.client.get(url, filtros)
        self.assertContains(pagina, "Descargar calendario (.ics)")
        self.assertIn(f"aula={primero.aula_id}", pagina.context["consulta_exportacion"])

        respuesta = self.client.get(url, {**filtros, "exportar": "ics"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "text/calendar; charset=utf-8")
        self.assertIn("horario-chronos.ics", respuesta["Content-Disposition"])
        self.assertIn("private", respuesta["Cache-Control"])
        self.assertEqual(respuesta.content.count(b"BEGIN:VEVENT\r\n"), 1)
        self.assertContains(respuesta, "DTSTART:20261005T130000Z")
        self.assertContains(respuesta, "DTEND:20261005T150000Z")
        self.assertContains(respuesta, "RRULE:FREQ=WEEKLY;COUNT=3")
        self.assertContains(respuesta, primero.aula.codigo)
        self.assertNotContains(respuesta, segundo.aula.codigo)

    def test_exportacion_ics_solo_incluye_las_clases_visibles_al_estudiante(self):
        primero, segundo = self._crear_horarios_para_filtros()
        cuenta = get_user_model().objects.create_user(username="estudiante_ics")
        estudiante = PerfilEstudiante.objects.create(
            usuario=cuenta, programa=self.paralelo.programa, semestre=3,
        )
        Inscripcion.objects.create(estudiante=estudiante, paralelo=primero.paralelo)
        url = reverse("planificacion_web:inicio")
        datos = {"periodo": self.periodo.pk, "exportar": "ics"}

        self.assertEqual(self.client.get(url, datos).status_code, 302)
        self.client.force_login(cuenta)
        respuesta = self.client.get(url, datos)
        self.assertEqual(respuesta.content.count(b"BEGIN:VEVENT\r\n"), 1)
        self.assertContains(respuesta, primero.aula.codigo)
        self.assertNotContains(respuesta, segundo.aula.codigo)
        respuesta_ajena = self.client.get(url, {**datos, "aula": segundo.aula_id})
        self.assertEqual(respuesta_ajena.status_code, 400)
        self.assertNotContains(respuesta_ajena, segundo.aula.codigo, status_code=400)

    def test_exportacion_ics_escapa_texto_y_conserva_utf8(self):
        self.horario().save()
        self.asignatura.nombre = "Á" * 45 + ", Redes; prácticas\\Taller"
        self.asignatura.save()
        self.client.force_login(self.docente.usuario)
        respuesta = self.client.get(reverse("planificacion_web:inicio"), {"exportar": "ics"})
        self.assertEqual(respuesta.status_code, 200)

        for linea in respuesta.content.split(b"\r\n"):
            self.assertLessEqual(len(linea), 75)
            linea.decode("utf-8")
        texto = respuesta.content.replace(b"\r\n ", b"").decode("utf-8")
        esperado = "SUMMARY:" + "Á" * 45 + r"\, Redes\; prácticas\\Taller"
        self.assertIn(esperado + "\r\n", texto)
        self.assertIn(r"DESCRIPTION:Paralelo TERCERO A\nDocente", texto)

    def test_exportacion_ics_sin_clases_devuelve_404(self):
        primero, segundo = self._crear_horarios_para_filtros()
        self.client.force_login(self._usuario_con_permisos("view_horario"))
        respuesta = self.client.get(
            reverse("planificacion_web:inicio"),
            {
                "periodo": self.periodo.pk, "docente": primero.docente_id,
                "aula": segundo.aula_id, "exportar": "ics",
            },
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_filtro_invalido_muestra_error_sin_fallar(self):
        self._crear_horarios_para_filtros()

        usuario = self._usuario_con_permisos("view_horario")
        self.client.force_login(usuario)

        respuesta = self.client.get(
            reverse("planificacion_web:inicio"),
            {
                "periodo": self.periodo.pk,
                "aula": "valor-invalido",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "aula",
            respuesta.context["filtros_horario"].errors,
        )
        self.assertEqual(respuesta.context["total_bloques"], 0)

    def test_docente_no_amplia_su_acceso_mediante_filtros(self):
        primero, segundo = self._crear_horarios_para_filtros()

        self.client.force_login(self.docente.usuario)
        url = reverse("planificacion_web:inicio")

        respuesta = self.client.get(
            url,
            {"periodo": self.periodo.pk},
        )
        self.assertEqual(respuesta.context["total_bloques"], 1)

        opciones = (
            respuesta.context["filtros_horario"]
            .fields["docente"].queryset
        )
        self.assertEqual(
            set(opciones.values_list("pk", flat=True)),
            {primero.docente_id},
        )

        respuesta = self.client.get(
            url,
            {
                "periodo": self.periodo.pk,
                "docente": segundo.docente_id,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "docente",
            respuesta.context["filtros_horario"].errors,
        )
        self.assertEqual(respuesta.context["total_bloques"], 0)
        
        
    def test_inscripcion_permite_al_estudiante_ver_su_horario(self):
        horario = self.horario()
        horario.save()

        cuenta = get_user_model().objects.create_user(
            username="estudiante_inscripcion_web",
        )
        estudiante = PerfilEstudiante.objects.create(
            usuario=cuenta,
            programa=self.paralelo.programa,
            semestre=3,
        )

        self.client.force_login(cuenta)
        inicio = reverse("planificacion_web:inicio")

        respuesta = self.client.get(inicio)
        self.assertEqual(respuesta.context["total_bloques"], 0)

        coordinador = get_user_model().objects.create_user(
            username="coordinador_inscripcion_web",
            is_superuser=True,
        )
        self.client.force_login(coordinador)

        respuesta = self.client.post(
            reverse("planificacion_web:inscripciones"),
            {
                "estudiante": estudiante.pk,
                "paralelo": self.paralelo.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 302)

        self.client.force_login(cuenta)
        respuesta = self.client.get(
            inicio,
            {"periodo": self.periodo.pk},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total_bloques"], 1)
        self.assertContains(respuesta, self.asignatura.nombre)

        # El estudiante no puede registrar sus propias inscripciones.
        respuesta = self.client.post(
            reverse("planificacion_web:inscripciones"),
            {
                "estudiante": estudiante.pk,
                "paralelo": self.paralelo.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(
            Inscripcion.objects.filter(estudiante=estudiante).count(),
            1,
        )
        
    def _editor_perfil_docente(self):
        usuario = self._usuario_con_permisos()

        permiso = Permission.objects.get(
            content_type__app_label="usuarios",
            content_type__model="perfildocente",
            codename="change_perfildocente",
        )
        usuario.user_permissions.add(permiso)

        self.client.force_login(usuario)
        return usuario

    def _datos_edicion_docente(self, limite=20):
        return {
            "titulo": "Magíster",
            "area": "Bases de datos",
            "horas_semanales_max": limite,
        }

    def test_web_edita_datos_academicos_docente(self):
        self._editor_perfil_docente()
        cuenta_id = self.docente.usuario_id

        respuesta = self.client.post(
            reverse(
                "planificacion_web:editar_docente",
                args=[self.docente.pk],
            ),
            self._datos_edicion_docente(limite=25),
        )

        self.assertEqual(respuesta.status_code, 302)
        self.docente.refresh_from_db()

        self.assertEqual(self.docente.titulo, "Magíster")
        self.assertEqual(self.docente.area, "Bases de datos")
        self.assertEqual(self.docente.horas_semanales_max, 25)
        self.assertEqual(self.docente.usuario_id, cuenta_id)

    def test_reduccion_incompatible_conserva_perfil_original(self):
        self._editor_perfil_docente()
        self.horario(hora_fin=time(12, 0)).save()

        with patch(
            "usuarios.servicios_docentes.timezone.localdate",
            return_value=date(2026, 11, 2),
        ):
            respuesta = self.client.post(
                reverse(
                    "planificacion_web:editar_docente",
                    args=[self.docente.pk],
                ),
                self._datos_edicion_docente(limite=3),
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "máximo del docente")

        self.docente.refresh_from_db()
        self.assertEqual(self.docente.horas_semanales_max, 20)
        self.assertEqual(self.docente.titulo, "Ingeniero")
        self.assertEqual(self.docente.area, "Programación")

    def test_permite_reducir_hasta_carga_exacta(self):
        self._editor_perfil_docente()
        self.horario(hora_fin=time(12, 0)).save()

        with patch(
            "usuarios.servicios_docentes.timezone.localdate",
            return_value=date(2026, 11, 2),
        ):
            respuesta = self.client.post(
                reverse(
                    "planificacion_web:editar_docente",
                    args=[self.docente.pk],
                ),
                self._datos_edicion_docente(limite=4),
            )

        self.assertEqual(respuesta.status_code, 302)
        self.docente.refresh_from_db()
        self.assertEqual(self.docente.horas_semanales_max, 4)

    def test_historial_anterior_no_impide_reducir_limite_actual(self):
        actor = self._editor_perfil_docente()
        self.horario().save()

        with patch(
            "usuarios.servicios_docentes.timezone.localdate",
            return_value=date(2027, 8, 1),
        ):
            editar_perfil_docente(
                actor=actor,
                docente_id=self.docente.pk,
                horas_semanales_max=1,
            )

        self.docente.refresh_from_db()
        self.assertEqual(self.docente.horas_semanales_max, 1)
        self.assertEqual(Horario.objects.count(), 1)

    def test_docente_sin_permiso_no_edita_su_perfil_academico(self):
        self.client.force_login(self.docente.usuario)

        url = reverse(
            "planificacion_web:editar_docente",
            args=[self.docente.pk],
        )

        self.assertEqual(self.client.get(url).status_code, 403)

        respuesta = self.client.post(
            url,
            self._datos_edicion_docente(limite=40),
        )

        self.assertEqual(respuesta.status_code, 403)
        self.docente.refresh_from_db()
        self.assertEqual(self.docente.horas_semanales_max, 20)
