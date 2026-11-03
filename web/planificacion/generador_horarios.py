from datetime import datetime, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from academico.models import Aula, PeriodoAcademico

from .models import (
    Horario,
    NecesidadClase,
    PropuestaHorario,
    BloquePropuesta,
    FranjaPlanificacion,
    DisponibilidadDocente,
    FranjaParalelo,
)
from .servicios import _exigir_permiso

from collections import Counter

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

        propuesta = PropuestaHorario(
            nombre=nombre,
            periodo=periodo,
            autor=usuario,
        )
        propuesta.full_clean()
        propuesta.save()
        propuesta.necesidades.set(necesidades)

        aulas = list(
            Aula.objects.filter(activo=True).order_by("codigo")
        )

        diagnosticos = []

        for necesidad in necesidades:
            espacios = list(
                self._espacios_posibles(
                    necesidad,
                    periodo,
                    paso_minutos,
                )
            )

            aulas_ordenadas = sorted(
                aulas,
                key=lambda aula: (
                    necesidad.prefiere_laboratorio
                    and aula.tipo != Aula.Tipo.LABORATORIO,
                    aula.codigo,
                ),
            )

            for numero in range(1, necesidad.sesiones_semanales + 1):
                dias_usados = set(
                    propuesta.bloques.filter(
                        necesidad__asignatura_id=necesidad.asignatura_id,
                        necesidad__paralelo_id=necesidad.paralelo_id,
                    ).values_list("dia", flat=True)
                )

                dias_ordenados = sorted(
                    {dia for dia, _, _ in espacios},
                    key=lambda dia: (
                        dia in dias_usados,
                        dia,
                    ),
                )

                ubicado = False
                intentos = 0
                errores = Counter()

                for dia_elegido in dias_ordenados:
                    for aula in aulas_ordenadas:
                        for dia, inicio, fin in espacios:
                            if dia != dia_elegido:
                                continue

                            bloque = BloquePropuesta(
                                propuesta=propuesta,
                                necesidad=necesidad,
                                numero_sesion=numero,
                                aula=aula,
                                dia=dia,
                                hora_inicio=inicio,
                                hora_fin=fin,
                            )
                            intentos += 1

                            try:
                                with transaction.atomic():
                                    bloque.full_clean()
                                    bloque.save()
                                    propuesta.validar_bloques()

                            except ValidationError as error:
                                for mensaje in error.messages:
                                    # Ese bloque candidato se revierte:
                                    # evitamos mostrar su identificador
                                    # como si fuera un bloque conservado.
                                    prefijo = f"Bloque #{bloque.pk}: "

                                    if bloque.pk and mensaje.startswith(prefijo):
                                        mensaje = (
                                            "Clase candidata: "
                                            + mensaje[len(prefijo):]
                                        )

                                    errores[mensaje] += 1

                                continue

                            ubicado = True
                            break

                        if ubicado:
                            break

                    if ubicado:
                        break

                if not ubicado:
                    motivos = []

                    if not aulas:
                        motivos.append({
                            "mensaje": "No hay aulas activas.",
                            "veces": 0,
                        })

                    if not espacios:
                        motivos.extend(
                            {
                                "mensaje": mensaje,
                                "veces": 0,
                            }
                            for mensaje in self._motivos_sin_espacios(
                                necesidad,
                                periodo,
                            )
                        )

                    motivos.extend(
                        {
                            "mensaje": mensaje,
                            "veces": cantidad,
                        }
                        for mensaje, cantidad in errores.most_common(5)
                    )

                    if not motivos:
                        motivos.append({
                            "mensaje": (
                                "No se encontró una ubicación "
                                "con el orden y paso de búsqueda utilizados."
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

        propuesta.diagnostico_generacion = {
            "paso_minutos": paso_minutos,
            "sesiones": diagnosticos,
        }
        propuesta.save(update_fields=["diagnostico_generacion"])

        avisos = []

        for bloque in propuesta.bloques.select_related(
            "necesidad__asignatura",
            "aula",
        ):
            if (
                bloque.necesidad.prefiere_laboratorio
                and bloque.aula.tipo != Aula.Tipo.LABORATORIO
            ):
                avisos.append(
                    f"{bloque.necesidad.asignatura.codigo}, "
                    f"sesión {bloque.numero_sesion}: "
                    "se recomienda laboratorio; se asignó "
                    f"el aula {bloque.aula.codigo}."
                )

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

        if propuesta.estado != PropuestaHorario.Estado.BORRADOR:
            raise ValidationError(
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

        agregadas = 0
        diagnosticos = []

        for necesidad in necesidades:
            espacios = list(
                self._espacios_posibles(
                    necesidad,
                    propuesta.periodo,
                    paso_minutos,
                )
            )

            aulas_ordenadas = sorted(
                aulas,
                key=lambda aula: (
                    necesidad.prefiere_laboratorio
                    and aula.tipo != Aula.Tipo.LABORATORIO,
                    aula.codigo,
                ),
            )

            for numero in sesiones_faltantes[necesidad.pk]:
                dias_usados = set(
                    propuesta.bloques.filter(
                        necesidad__asignatura_id=necesidad.asignatura_id,
                        necesidad__paralelo_id=necesidad.paralelo_id,
                    ).values_list("dia", flat=True)
                )

                espacios_ordenados = sorted(
                    espacios,
                    key=lambda espacio: (
                        espacio[0] in dias_usados,
                        espacio[0],
                        espacio[1],
                    ),
                )

                ubicado = False
                intentos = 0
                errores = Counter()

                for aula in aulas_ordenadas:
                    for dia, inicio, fin in espacios_ordenados:
                        bloque = BloquePropuesta(
                            propuesta=propuesta,
                            necesidad=necesidad,
                            numero_sesion=numero,
                            aula=aula,
                            dia=dia,
                            hora_inicio=inicio,
                            hora_fin=fin,
                        )
                        intentos += 1

                        try:
                            with transaction.atomic():
                                bloque.full_clean()
                                bloque.save()
                                propuesta.validar_bloques()

                        except ValidationError as error:
                            for mensaje in error.messages:
                                prefijo = f"Bloque #{bloque.pk}: "

                                if bloque.pk and mensaje.startswith(prefijo):
                                    mensaje = (
                                        "Clase candidata: "
                                        + mensaje[len(prefijo):]
                                    )

                                errores[mensaje] += 1

                            continue

                        agregadas += 1
                        ubicado = True
                        break

                    if ubicado:
                        break

                if ubicado:
                    continue

                motivos = []

                if not aulas:
                    motivos.append({
                        "mensaje": "No hay aulas activas.",
                        "veces": 0,
                    })

                if not espacios:
                    motivos.extend(
                        {"mensaje": mensaje, "veces": 0}
                        for mensaje in self._motivos_sin_espacios(
                            necesidad,
                            propuesta.periodo,
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

        propuesta.diagnostico_generacion = {
            "tipo": "reintento",
            "paso_minutos": paso_minutos,
            "sesiones": diagnosticos,
        }
        propuesta.save(
            update_fields=[
                "diagnostico_generacion",
                "actualizada_en",
            ]
        )

        return {
            "propuesta": propuesta,
            "agregadas": agregadas,
            "pendientes": propuesta.obtener_pendientes(),
        }

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

        if not DisponibilidadDocente.objects.filter(
            docente=necesidad.docente,
            periodo=periodo,
            activo=True,
        ).exists():
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

        for dia in Horario.Dia.values:
            franjas = self._unir_ventanas(
                FranjaPlanificacion.objects.filter(
                    periodo=periodo,
                    dia=dia,
                    activo=True,
                ).values_list("hora_inicio", "hora_fin")
            )

            disponibilidades = self._unir_ventanas(
                DisponibilidadDocente.objects.filter(
                    docente=necesidad.docente,
                    periodo=periodo,
                    dia=dia,
                    activo=True,
                ).values_list("hora_inicio", "hora_fin")
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