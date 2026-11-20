from datetime import datetime, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from academico.models import Aula, PeriodoAcademico

from .constructor_propuesta import ConstructorPropuestaHorario
from .models import (
    Horario,
    NecesidadClase,
    PropuestaHorario,
    BloquePropuesta,
    FranjaPlanificacion,
    FranjaParalelo,
)
from .servicios import _exigir_permiso

from collections import Counter

from .disponibilidad_efectiva import DisponibilidadDocenteEfectiva

class GeneradorHorarios:
    """Genera borradores mediante búsqueda de espacios en orden."""

    @transaction.atomic
    def generar(
        self,
        *,
        usuario,
        nombre,
        periodo_id,
        necesidades_ids,
        paso_minutos=15,
    ):
        _exigir_permiso(
            usuario,
            "planificacion.add_propuestahorario",
        )

        if (
            not isinstance(paso_minutos, int)
            or isinstance(paso_minutos, bool)
            or not 1 <= paso_minutos <= 1440
        ):
            raise ValidationError(
                "El paso de búsqueda debe estar entre 1 y 1440 minutos."
            )

        identificadores = set(necesidades_ids)

        if not identificadores:
            raise ValidationError(
                "Selecciona al menos una necesidad."
            )

        periodo = PeriodoAcademico.objects.get(pk=periodo_id)

        necesidades = list(
            NecesidadClase.objects.filter(
                pk__in=identificadores,
                paralelo__periodo=periodo,
                activo=True,
                asignatura__activo=True,
                docente__usuario__is_active=True,
                docente__activo=True,
                paralelo__programa__activo=True,
            )
            .select_related(
                "asignatura",
                "docente__usuario",
                "paralelo__periodo",
            )
            .order_by("-duracion_minutos", "pk")
        )

        if len(necesidades) != len(identificadores):
            raise ValidationError(
                "Hay necesidades inexistentes, de otro periodo "
                "o relacionadas con registros inactivos."
            )

        constructor = ConstructorPropuestaHorario.iniciar(
            nombre=nombre,
            periodo=periodo,
            autor=usuario,
            necesidades=necesidades,
        )

        aulas = list(
            Aula.objects.filter(activo=True).order_by("codigo")
        )

        sesiones = {
            necesidad.pk: range(1, necesidad.sesiones_semanales + 1)
            for necesidad in necesidades
        }
        _, diagnosticos = self._ubicar_sesiones(
            constructor, necesidades, sesiones, aulas, paso_minutos
        )

        propuesta = constructor.finalizar({
            "paso_minutos": paso_minutos,
            "sesiones": diagnosticos,
        })

        avisos = []

        for bloque in propuesta.bloques.select_related(
            "necesidad__asignatura",
            "aula",
        ):
            aviso = bloque.necesidad.aviso_aula(bloque.aula, bloque.numero_sesion)
            if aviso:
                avisos.append(aviso)

        return {
            "propuesta": propuesta,
            "pendientes": propuesta.obtener_pendientes(),
            "avisos": avisos,
        }

    @transaction.atomic
    def reintentar(
        self,
        *,
        usuario,
        propuesta_id,
        paso_minutos=15,
    ):
        _exigir_permiso(
            usuario,
            "planificacion.add_bloquepropuesta",
        )

        if (
            not isinstance(paso_minutos, int)
            or isinstance(paso_minutos, bool)
            or not 1 <= paso_minutos <= 1440
        ):
            raise ValidationError(
                "El paso de búsqueda debe estar entre 1 y 1440 minutos."
            )

        propuesta = (
            PropuestaHorario.objects
            .select_for_update()
            .select_related("periodo")
            .get(pk=propuesta_id)
        )

        if (
            propuesta.autor_id != usuario.pk
            and not usuario.has_perm(
                "planificacion.view_propuestahorario"
            )
        ):
            raise PermissionDenied(
                "No tienes acceso a esta propuesta."
            )

        propuesta.estado_actual.exigir_edicion(
            "Solo se pueden reintentar propuestas en borrador."
        )

        propuesta.full_clean()
        pendientes = propuesta.obtener_pendientes()

        # Los bloques existentes deben ser válidos antes de añadir otros.
        if propuesta.bloques.exists():
            propuesta.validar_bloques()

        if not pendientes:
            return {
                "propuesta": propuesta,
                "agregadas": 0,
                "pendientes": [],
            }

        sesiones_faltantes = {
            pendiente["necesidad_id"]: pendiente["sesiones"]
            for pendiente in pendientes
        }

        necesidades = list(
            propuesta.necesidades.filter(
                pk__in=sesiones_faltantes,
                activo=True,
                asignatura__activo=True,
                docente__activo=True,
                docente__usuario__is_active=True,
                paralelo__programa__activo=True,
            )
            .select_related(
                "asignatura",
                "docente__usuario",
                "paralelo__periodo",
            )
            .order_by("-duracion_minutos", "pk")
        )

        if len(necesidades) != len(sesiones_faltantes):
            raise ValidationError(
                "Hay sesiones pendientes relacionadas con registros "
                "inactivos. Corrige sus datos antes de reintentar."
            )

        aulas = list(
            Aula.objects.filter(activo=True).order_by("codigo")
        )

        constructor = ConstructorPropuestaHorario(propuesta)
        agregadas, diagnosticos = self._ubicar_sesiones(
            constructor, necesidades, sesiones_faltantes, aulas, paso_minutos
        )

        propuesta = constructor.finalizar(
            {
                "tipo": "reintento",
                "paso_minutos": paso_minutos,
                "sesiones": diagnosticos,
            },
            actualizar_fecha=True,
        )

        return {
            "propuesta": propuesta,
            "agregadas": agregadas,
            "pendientes": propuesta.obtener_pendientes(),
        }

    @staticmethod
    def _priorizar_dias(propuesta, necesidad, espacios):
        """Ordena días según asignatura y carga del paralelo."""
        carga = Counter()
        dias_asignatura = set()

        bloques = propuesta.bloques.filter(
            necesidad__paralelo_id=necesidad.paralelo_id,
        ).values_list(
            "dia",
            "hora_inicio",
            "hora_fin",
            "necesidad__asignatura_id",
        )

        oficiales = Horario.objects.filter(
            paralelo_id=necesidad.paralelo_id,
        ).values_list(
            "dia",
            "hora_inicio",
            "hora_fin",
            "asignatura_id",
        )

        for registros in (bloques, oficiales):
            for dia, inicio, fin, asignatura_id in registros:
                duracion = (
                    datetime.combine(propuesta.periodo.fecha_inicio, fin)
                    - datetime.combine(propuesta.periodo.fecha_inicio, inicio)
                )
                carga[dia] += duracion.total_seconds()

                if asignatura_id == necesidad.asignatura_id:
                    dias_asignatura.add(dia)

        return sorted(
            {dia for dia, _, _ in espacios},
            key=lambda dia: (
                dia in dias_asignatura,
                carga[dia],
                dia,
            ),
        )

    def _candidatos_ordenados(
        self,
        propuesta,
        necesidad,
        espacios,
        aulas,
    ):
        """Prueba tipos de aula por preferencia y días por carga."""
        if not espacios or not aulas:
            return

        por_dia = {}
        for dia, inicio, fin in espacios:
            por_dia.setdefault(dia, []).append((inicio, fin))

        dias = self._priorizar_dias(propuesta, necesidad, espacios)
        intervalos = {dia: sorted(por_dia[dia]) for dia in dias}
        uso_aulas = Counter(propuesta.bloques.values_list("aula_id", flat=True))

        por_prioridad = {}
        for prioridad, aula in aulas:
            por_prioridad.setdefault(prioridad, []).append(aula)

        for prioridad in sorted(por_prioridad):
            aulas_ordenadas = sorted(
                por_prioridad[prioridad],
                key=lambda aula: (uso_aulas[aula.pk], aula.codigo),
            )
            for dia in dias:
                for inicio, fin in intervalos[dia]:
                    for aula in aulas_ordenadas:
                        yield dia, aula, inicio, fin

    @staticmethod
    def _motivos_sin_espacios(necesidad, periodo):
        motivos = []

        if not FranjaPlanificacion.objects.filter(
            periodo=periodo,
            activo=True,
        ).exists():
            motivos.append(
                "No hay franjas de planificación activas "
                "en este periodo."
            )

        disponibilidad_efectiva = DisponibilidadDocenteEfectiva.obtener(
            docente_id=necesidad.docente_id,
            periodo_id=periodo.pk,
        )

        if not any(disponibilidad_efectiva.values()):
            motivos.append(
                "El docente no tiene disponibilidad activa "
                "en este periodo."
            )

        if not motivos:
            tiene_franjas_propias = FranjaParalelo.objects.filter(
                paralelo_id=necesidad.paralelo_id,
                activo=True,
            ).exists()

            if tiene_franjas_propias:
                motivos.append(
                    "Las franjas del periodo, la disponibilidad docente "
                    "y las franjas del Paralelo/Curso no comparten "
                    "un intervalo continuo suficiente para una sesión "
                    f"de {necesidad.duracion_minutos} minutos."
                )
            else:
                motivos.append(
                    "Las franjas y disponibilidades activas no comparten "
                    "un intervalo continuo suficiente para una sesión "
                    f"de {necesidad.duracion_minutos} minutos."
                )

        return motivos

    @staticmethod
    def _unir_ventanas(ventanas):
        """Une ventanas superpuestas o consecutivas."""
        resultado = []

        for inicio, fin in sorted(ventanas):
            if resultado and inicio <= resultado[-1][1]:
                resultado[-1] = (
                    resultado[-1][0],
                    max(resultado[-1][1], fin),
                )
            else:
                resultado.append((inicio, fin))

        return resultado

    @classmethod
    def _intersectar_ventanas(cls, primeras, segundas):
        """Obtiene los intervalos compartidos por dos conjuntos."""
        intersecciones = []

        for inicio_a, fin_a in primeras:
            for inicio_b, fin_b in segundas:
                inicio = max(inicio_a, inicio_b)
                fin = min(fin_a, fin_b)

                if inicio < fin:
                    intersecciones.append((inicio, fin))

        return cls._unir_ventanas(intersecciones)

    def _espacios_posibles(self, necesidad, periodo, paso_minutos):
        duracion = timedelta(minutes=necesidad.duracion_minutos)
        paso = timedelta(minutes=paso_minutos)

        franjas_paralelo = list(
            FranjaParalelo.objects.filter(
                paralelo_id=necesidad.paralelo_id,
                activo=True,
            ).values_list("dia", "hora_inicio", "hora_fin")
        )

        tiene_franjas_propias = bool(franjas_paralelo)
        
        disponibilidad_efectiva = DisponibilidadDocenteEfectiva.obtener(
            docente_id=necesidad.docente_id,
            periodo_id=periodo.pk,
        )

        for dia in Horario.Dia.values:
            franjas = self._unir_ventanas(
                FranjaPlanificacion.objects.filter(
                    periodo=periodo,
                    dia=dia,
                    activo=True,
                ).values_list("hora_inicio", "hora_fin")
            )

            disponibilidades = self._unir_ventanas(
                disponibilidad_efectiva[dia]
            )

            ventanas = self._intersectar_ventanas(
                franjas,
                disponibilidades,
            )

            if tiene_franjas_propias:
                ventanas_del_paralelo = self._unir_ventanas(
                    (inicio, fin)
                    for dia_franja, inicio, fin in franjas_paralelo
                    if dia_franja == dia
                )

                ventanas = self._intersectar_ventanas(
                    ventanas,
                    ventanas_del_paralelo,
                )

            for inicio, fin in ventanas:
                cursor = datetime.combine(
                    periodo.fecha_inicio,
                    inicio,
                )
                limite = datetime.combine(
                    periodo.fecha_inicio,
                    fin,
                )

                while cursor + duracion <= limite:
                    yield (
                        dia,
                        cursor.time(),
                        (cursor + duracion).time(),
                    )
                    cursor += paso

    def _ubicar_sesiones(
        self, constructor, necesidades, sesiones, aulas, paso_minutos
    ):
        propuesta = constructor.propuesta
        agregadas = 0
        diagnosticos = []

        for necesidad in necesidades:
            espacios = list(
                self._espacios_posibles(
                    necesidad, propuesta.periodo, paso_minutos
                )
            )
            aulas_candidatas = []
            for aula in aulas:
                prioridad = necesidad.prioridad_aula(aula)
                if prioridad is not None:
                    aulas_candidatas.append((prioridad, aula))

            for numero in sesiones[necesidad.pk]:
                intentos = 0
                errores = Counter()

                for dia, aula, inicio, fin in self._candidatos_ordenados(
                    propuesta, necesidad, espacios, aulas_candidatas
                ):
                    bloque = BloquePropuesta(
                        necesidad=necesidad,
                        numero_sesion=numero,
                        aula=aula,
                        dia=dia,
                        hora_inicio=inicio,
                        hora_fin=fin,
                    )
                    intentos += 1

                    try:
                        constructor.incorporar_bloque(bloque)
                    except ValidationError as error:
                        prefijo = f"Bloque #{bloque.pk}: "
                        for mensaje in error.messages:
                            if bloque.pk and mensaje.startswith(prefijo):
                                mensaje = "Clase candidata: " + mensaje[len(prefijo):]
                            errores[mensaje] += 1
                        continue

                    agregadas += 1
                    break
                else:
                    motivos = []

                    if not aulas:
                        motivos.append({
                            "mensaje": "No hay aulas activas.",
                            "veces": 0,
                        })

                    elif not aulas_candidatas:
                        motivos.append({
                            "mensaje": (
                                "No hay aulas teóricas ni laboratorios activos "
                                "de la especialidad seleccionada."
                            ),
                            "veces": 0,
                        })

                    if not espacios:
                        motivos.extend(
                            {"mensaje": mensaje, "veces": 0}
                            for mensaje in self._motivos_sin_espacios(
                                necesidad, propuesta.periodo
                            )
                        )

                    motivos.extend(
                        {"mensaje": mensaje, "veces": cantidad}
                        for mensaje, cantidad in errores.most_common(5)
                    )

                    if not motivos:
                        motivos.append({
                            "mensaje": (
                                "No se encontró una ubicación con el orden "
                                "y paso de búsqueda utilizados."
                            ),
                            "veces": 0,
                        })

                    diagnosticos.append({
                        "necesidad_id": necesidad.pk,
                        "numero_sesion": numero,
                        "descripcion": str(necesidad),
                        "intentos": intentos,
                        "motivos": motivos,
                    })

        return agregadas, diagnosticos
