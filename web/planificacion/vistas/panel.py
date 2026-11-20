from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.utils.cache import patch_cache_control

from academico.models import PeriodoAcademico

from ..adaptadores_calendario import HorarioAEventoCalendario
from ..exportacion_ics import exportar_ics
from ..models import AvisoHorario, Horario, PropuestaHorario
from ..formularios_web import FiltroHorarioForm
from ..calendario import CalendarioSemanal


@login_required
def inicio(request):
    usuario = request.user

    puede_ver_todos = usuario.has_perm(
        "planificacion.view_horario"
    )
    puede_ver_propuestas = usuario.has_perm(
        "planificacion.view_propuestahorario"
    )

    autorizados = Horario.objects.all()

    if not puede_ver_todos:
        autorizados = autorizados.filter(
            Q(docente__usuario=usuario)
            | Q(
                paralelo__inscripciones__estudiante__usuario=usuario
            )
        ).distinct()

    if puede_ver_todos:
        periodos = PeriodoAcademico.objects.all()
    else:
        periodos = PeriodoAcademico.objects.filter(
            paralelos__horarios__in=autorizados
        ).distinct()

    periodos = periodos.order_by("-fecha_inicio")
    periodo_predeterminado = periodos.first()

    datos = request.GET.copy()

    if "periodo" not in datos and periodo_predeterminado:
        datos["periodo"] = str(periodo_predeterminado.pk)

    filtros = FiltroHorarioForm(
        data=datos if datos else None,
        periodos=periodos,
        horarios_autorizados=autorizados,
    )

    periodo = periodo_predeterminado
    horarios = autorizados.none()

    valido = False

    if filtros.is_bound:
        valido = filtros.is_valid()
        periodo = filtros.cleaned_data.get("periodo")

        if valido:
            horarios = autorizados.filter(
                paralelo__periodo=periodo,
            )

            for campo in ("docente", "aula", "paralelo"):
                valor = filtros.cleaned_data.get(campo)

                if valor is not None:
                    horarios = horarios.filter(
                        **{campo: valor}
                    )

    registros = list(
        horarios.select_related(
            "asignatura",
            "docente__usuario",
            "aula",
            "paralelo__programa",
            "paralelo__periodo",
        ).order_by("dia", "hora_inicio", "pk")
    )

    if request.GET.get("exportar") == "ics":
        if not valido:
            return HttpResponseBadRequest("Los filtros del horario no son válidos.")
        return _descargar_ics(registros, dominio=request.get_host())

    es_impresion = request.GET.get("imprimir") == "1"

    avisos_horario = ()
    if not es_impresion:
        propuestas_visibles = autorizados.order_by().values(
            "bloque_origen__propuesta_id"
        )
        avisos_horario = AvisoHorario.objects.filter(
            destinatario=usuario,
            propuesta_id__in=propuestas_visibles,
        ).select_related("propuesta__periodo")[:5]

    consulta_impresion = datos.copy()
    consulta_impresion["imprimir"] = "1"

    consulta_exportacion = datos.copy()
    consulta_exportacion["exportar"] = "ics"

    filtros_aplicados = []

    if valido:
        for campo, etiqueta in (
            ("paralelo", "Paralelo/Curso"),
            ("docente", "Docente"),
            ("aula", "Aula"),
        ):
            valor = filtros.cleaned_data.get(campo)

            if valor is not None:
                filtros_aplicados.append((etiqueta, str(valor)))

    plantilla = (
        "planificacion/imprimir_horario.html"
        if es_impresion
        else "planificacion/inicio.html"
    )

    calendario = CalendarioSemanal().construir(registros)

    propuestas = PropuestaHorario.objects.none()

    if puede_ver_propuestas and periodo:
        propuestas = (
            PropuestaHorario.objects
            .filter(periodo=periodo)
            .select_related("autor")
            .order_by("-creada_en")[:6]
        )

    return render(
        request,
        plantilla,
        {
            "periodos": periodos,
            "periodo": periodo,
            "filtros_horario": filtros,
            "calendario": calendario,
            "total_bloques": len(registros),
            "total_docentes": len({
                horario.docente_id for horario in registros
            }),
            "total_aulas": len({
                horario.aula_id for horario in registros
            }),
            "propuestas": propuestas,
            "avisos_horario": avisos_horario,
            "puede_ver_todos": puede_ver_todos,
            "puede_ver_propuestas": puede_ver_propuestas,
            
            "registros": registros,
            "filtros_validos": valido,
            "filtros_aplicados": filtros_aplicados,
            "consulta_impresion": consulta_impresion.urlencode(),
            "consulta_exportacion": consulta_exportacion.urlencode(),
        },
    )


def _descargar_ics(registros, *, dominio):
    zona_horaria = timezone.get_default_timezone()
    eventos = []
    for horario in registros:
        evento = HorarioAEventoCalendario(horario).como_evento(
            zona_horaria=zona_horaria,
            dominio=dominio,
        )
        if evento is not None:
            eventos.append(evento)
    if not eventos:
        raise Http404("No hay clases para exportar con estos filtros.")

    respuesta = HttpResponse(
        exportar_ics(eventos, generado_en=timezone.now()),
        content_type="text/calendar; charset=utf-8",
    )
    respuesta["Content-Disposition"] = 'attachment; filename="horario-chronos.ics"'
    patch_cache_control(respuesta, private=True, no_store=True)
    return respuesta
