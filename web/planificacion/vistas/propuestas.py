from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from academico.models import PeriodoAcademico
from ..models import Horario, PropuestaHorario, BloquePropuesta
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from ..formularios_web import GenerarPropuestaForm, EditarBloqueForm, RetirarPublicacionForm, AgregarSesionForm, ReintentarPendientesForm
from ..formularios_web import MoverBloqueForm
from ..generador_horarios import GeneradorHorarios
from django.views.decorators.http import require_POST
from ..servicios import enviar_propuesta_revision as enviar_a_revision, aprobar_propuesta as publicar_propuesta, devolver_propuesta_borrador, editar_bloque_propuesta, retirar_publicacion, agregar_sesion_pendiente
from django.core.paginator import Paginator
from ..calendario import CalendarioSemanal

@login_required
@permission_required(
    "planificacion.add_propuestahorario",
    raise_exception=True,
)
def generar_propuesta(request):
    periodos = PeriodoAcademico.objects.order_by("-fecha_inicio")

    if request.method == "POST":
        periodo_id = request.POST.get("periodo")
    else:
        periodo_id = request.GET.get("periodo")

    if periodo_id:
        try:
            periodo_id = int(periodo_id)
        except (TypeError, ValueError):
            raise Http404("Periodo inválido.")

        periodo = get_object_or_404(periodos, pk=periodo_id)
    else:
        periodo = periodos.first()

    form = GenerarPropuestaForm(
        request.POST if request.method == "POST" else None,
        periodo=periodo,
        initial={"nombre": "Nueva propuesta"},
    )

    if request.method == "POST" and form.is_valid():
        try:
            resultado = GeneradorHorarios().generar(
                usuario=request.user,
                nombre=form.cleaned_data["nombre"],
                periodo_id=form.cleaned_data["periodo"].pk,
                necesidades_ids=(
                    form.cleaned_data["necesidades"]
                    .values_list("pk", flat=True)
                ),
                paso_minutos=form.cleaned_data["paso_minutos"],
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        else:
            if resultado["pendientes"]:
                messages.warning(
                    request,
                    "Borrador generado con sesiones pendientes.",
                )
            else:
                messages.success(
                    request,
                    "Borrador generado con todas las sesiones ubicadas.",
                )

            return redirect(
                "planificacion_web:detalle_propuesta",
                propuesta_id=resultado["propuesta"].pk,
            )

    return render(
        request,
        "planificacion/generar_propuesta.html",
        {
            "form": form,
            "periodos": periodos,
            "periodo": periodo,
        },
    )


@login_required
def detalle_propuesta(request, propuesta_id):
    propuestas = PropuestaHorario.objects.select_related(
        "periodo",
        "autor",
    )

    if not request.user.has_perm(
        "planificacion.view_propuestahorario"
    ):
        propuestas = propuestas.filter(autor=request.user)

    propuesta = get_object_or_404(
        propuestas,
        pk=propuesta_id,
    )

    bloques = list(
        propuesta.bloques.select_related(
            "necesidad__asignatura",
            "necesidad__docente__usuario",
            "necesidad__paralelo",
            "aula",
        ).order_by("dia", "hora_inicio", "pk")
    )

    paralelos_por_id = {
        str(bloque.necesidad.paralelo_id): bloque.necesidad.paralelo
        for bloque in bloques
    }

    paralelo_id = request.GET.get("paralelo", "").strip()
    paralelo_seleccionado = None

    if paralelo_id:
        paralelo_seleccionado = paralelos_por_id.get(paralelo_id)

        if paralelo_seleccionado is None:
            raise Http404(
                "El paralelo no tiene bloques en esta propuesta."
            )

    bloques_calendario = [
        bloque
        for bloque in bloques
        if (
            paralelo_seleccionado is None
            or bloque.necesidad.paralelo_id == paralelo_seleccionado.pk
        )
    ]

    horarios_calendario = []
    for bloque in bloques_calendario:
        horario = bloque.como_horario()
        horario.bloque_origen_id = bloque.pk
        horarios_calendario.append(horario)

    calendario_propuesta = CalendarioSemanal().construir(
        horarios_calendario, fin_minimo=20 * 60
    )
    puede_mover = (
        propuesta.estado == PropuestaHorario.Estado.BORRADOR
        and request.user.has_perm("planificacion.change_bloquepropuesta")
    )

    paralelos_calendario = sorted(
        paralelos_por_id.values(),
        key=lambda paralelo: (paralelo.nombre, paralelo.pk),
    )
    
    error_alcance = None
    pendientes = []

    try:
        pendientes = propuesta.obtener_pendientes()
    except ValidationError as error:
        error_alcance = "; ".join(error.messages)

    sesiones_pendientes = {
        (pendiente["necesidad_id"], numero)
        for pendiente in pendientes
        for numero in pendiente["sesiones"]
    }

    diagnosticos = [
        diagnostico
        for diagnostico in propuesta.diagnostico_generacion.get(
            "sesiones",
            [],
        )
        if (
            diagnostico["necesidad_id"],
            diagnostico["numero_sesion"],
        ) in sesiones_pendientes
    ]

    avisos = []
    for bloque in bloques:
        aviso = bloque.necesidad.aviso_aula(bloque.aula, bloque.numero_sesion)
        if aviso:
            avisos.append(aviso)


    return render(
        request,
        "planificacion/detalle_propuesta.html",
        {
            "propuesta": propuesta,
            "bloques": bloques,
            "pendientes": pendientes,
            "avisos": avisos,
            "error_alcance": error_alcance,
            "diagnosticos": diagnosticos,
            "form_reintento": ReintentarPendientesForm(),
            "calendario_propuesta": calendario_propuesta,
            "form_mover": MoverBloqueForm() if puede_mover else None,
            "paralelos_calendario": paralelos_calendario,
            "paralelo_seleccionado": paralelo_seleccionado,
            "total_bloques_calendario": len(bloques_calendario),
        },
    )


def _propuesta_accesible(usuario, propuesta_id):
    propuestas = PropuestaHorario.objects.all()

    if not usuario.has_perm(
        "planificacion.view_propuestahorario"
    ):
        propuestas = propuestas.filter(autor=usuario)

    return get_object_or_404(
        propuestas,
        pk=propuesta_id,
    )


@login_required
@permission_required(
    "planificacion.change_propuestahorario",
    raise_exception=True,
)
@require_POST
def enviar_revision_web(request, propuesta_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    try:
        enviar_a_revision(
            usuario=request.user,
            propuesta_id=propuesta.pk,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(
            request,
            "Propuesta enviada a revisión.",
        )

    return redirect(
        "planificacion_web:detalle_propuesta",
        propuesta_id=propuesta.pk,
    )


@login_required
@permission_required(
    "planificacion.aprobar_propuestahorario",
    raise_exception=True,
)
@require_POST
def aprobar_propuesta_web(request, propuesta_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    try:
        publicar_propuesta(
            usuario=request.user,
            propuesta_id=propuesta.pk,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(
            request,
            "Propuesta aprobada. Sus clases ya son horarios oficiales.",
        )

    return redirect(
        "planificacion_web:detalle_propuesta",
        propuesta_id=propuesta.pk,
    )


@login_required
@permission_required(
    "planificacion.change_bloquepropuesta",
    raise_exception=True,
)
def editar_bloque_web(request, propuesta_id, bloque_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    bloque = get_object_or_404(
        BloquePropuesta.objects.select_related(
            "necesidad__asignatura",
            "necesidad__paralelo",
        ),
        pk=bloque_id,
        propuesta=propuesta,
    )

    if propuesta.estado != PropuestaHorario.Estado.BORRADOR:
        messages.error(
            request,
            "Solo se pueden editar propuestas en borrador.",
        )
        return redirect(
            "planificacion_web:detalle_propuesta",
            propuesta_id=propuesta.pk,
        )

    form = EditarBloqueForm(
        request.POST if request.method == "POST" else None,
        instance=bloque,
    )

    if request.method == "POST" and form.is_valid():
        try:
            editar_bloque_propuesta(
                usuario=request.user,
                bloque_id=bloque.pk,
                **form.cleaned_data,
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        else:
            messages.success(request, "Bloque actualizado.")
            return redirect(
                "planificacion_web:detalle_propuesta",
                propuesta_id=propuesta.pk,
            )

    return render(
        request,
        "planificacion/editar_bloque.html",
        {
            "form": form,
            "bloque": bloque,
            "propuesta": propuesta,
        },
    )


@login_required
@permission_required("planificacion.change_bloquepropuesta", raise_exception=True)
@require_POST
def mover_bloque_web(request, propuesta_id, bloque_id):
    propuesta = _propuesta_accesible(request.user, propuesta_id)
    bloque = get_object_or_404(
        BloquePropuesta.objects.select_related("necesidad"),
        pk=bloque_id,
        propuesta=propuesta,
    )
    if propuesta.estado != PropuestaHorario.Estado.BORRADOR:
        return JsonResponse(
            {"errores": ["Solo se pueden mover bloques en borradores."]},
            status=409,
        )

    form = MoverBloqueForm(request.POST)
    if not form.is_valid():
        errores = [mensaje for campo in form.errors.values() for mensaje in campo]
        return JsonResponse({"errores": errores}, status=400)

    inicio = datetime.combine(date(2000, 1, 1), form.cleaned_data["hora_inicio"])
    fin = inicio + timedelta(minutes=bloque.necesidad.duracion_minutos)
    if fin.date() != inicio.date():
        return JsonResponse(
            {"errores": ["La clase debe terminar el mismo día."]},
            status=400,
        )

    cambios = {
        "dia": form.cleaned_data["dia"],
        "hora_inicio": inicio.time(),
        "hora_fin": fin.time(),
    }
    if form.cleaned_data["aula"] is not None:
        cambios["aula"] = form.cleaned_data["aula"]

    try:
        editar_bloque_propuesta(usuario=request.user, bloque_id=bloque.pk, **cambios)
    except ValidationError as error:
        return JsonResponse({"errores": error.messages}, status=400)

    messages.success(request, "Clase movida en el calendario.")
    return JsonResponse({"ok": True})


@login_required
@permission_required(
    "planificacion.aprobar_propuestahorario",
    raise_exception=True,
)
@require_POST
def devolver_borrador_web(request, propuesta_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    try:
        devolver_propuesta_borrador(
            usuario=request.user,
            propuesta_id=propuesta.pk,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(
            request,
            "Propuesta devuelta a borrador. Ya puedes corregir sus bloques.",
        )

    return redirect(
        "planificacion_web:detalle_propuesta",
        propuesta_id=propuesta.pk,
    )


@login_required
@permission_required(
    (
        "planificacion.aprobar_propuestahorario",
        "planificacion.delete_horario",
    ),
    raise_exception=True,
)
def retirar_publicacion_web(request, propuesta_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    if propuesta.estado != PropuestaHorario.Estado.APROBADA:
        messages.error(request, "La propuesta no está aprobada.")
        return redirect(
            "planificacion_web:detalle_propuesta",
            propuesta_id=propuesta.pk,
        )

    cantidad = Horario.objects.filter(
        bloque_origen__propuesta=propuesta,
    ).count()

    form = RetirarPublicacionForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            retirar_publicacion(
                usuario=request.user,
                propuesta_id=propuesta.pk,
                motivo=form.cleaned_data["motivo"],
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        else:
            messages.success(
                request,
                "Publicación retirada. Puedes corregir el borrador "
                "y enviarlo nuevamente a revisión.",
            )
            return redirect(
                "planificacion_web:detalle_propuesta",
                propuesta_id=propuesta.pk,
            )

    return render(
        request,
        "planificacion/retirar_publicacion.html",
        {
            "propuesta": propuesta,
            "cantidad": cantidad,
            "form": form,
        },
    )


@login_required
def historial_propuestas(request):
    propuestas = PropuestaHorario.objects.select_related(
        "periodo",
        "autor",
    )

    if not request.user.has_perm(
        "planificacion.view_propuestahorario"
    ):
        propuestas = propuestas.filter(autor=request.user)

    busqueda = request.GET.get("q", "").strip()[:200]
    estado = request.GET.get("estado", "")

    if busqueda:
        propuestas = propuestas.filter(
            Q(nombre__icontains=busqueda)
            | Q(periodo__codigo__icontains=busqueda)
        )

    if estado in PropuestaHorario.Estado.values:
        propuestas = propuestas.filter(estado=estado)

    propuestas = propuestas.order_by("-creada_en", "-pk")

    pagina = Paginator(propuestas, 10).get_page(
        request.GET.get("pagina")
    )

    filtros = request.GET.copy()
    filtros.pop("pagina", None)

    return render(
        request,
        "planificacion/historial_propuestas.html",
        {
            "pagina": pagina,
            "busqueda": busqueda,
            "estado": estado,
            "estados": PropuestaHorario.Estado.choices,
            "filtros": filtros.urlencode(),
        },
    )


@login_required
@permission_required(
    "planificacion.add_bloquepropuesta",
    raise_exception=True,
)
def agregar_sesion_web(request, propuesta_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    if propuesta.estado != PropuestaHorario.Estado.BORRADOR:
        messages.error(
            request,
            "Solo se pueden añadir sesiones a un borrador.",
        )
        return redirect(
            "planificacion_web:detalle_propuesta",
            propuesta_id=propuesta.pk,
        )

    try:
        pendientes = propuesta.obtener_pendientes()
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
        return redirect(
            "planificacion_web:detalle_propuesta",
            propuesta_id=propuesta.pk,
        )

    if not pendientes:
        messages.info(request, "La propuesta no tiene sesiones pendientes.")
        return redirect(
            "planificacion_web:detalle_propuesta",
            propuesta_id=propuesta.pk,
        )

    form = AgregarSesionForm(
        request.POST if request.method == "POST" else None,
        pendientes=pendientes,
    )

    if request.method == "POST" and form.is_valid():
        necesidad_id, numero = map(
            int,
            form.cleaned_data["sesion"].split(":"),
        )

        try:
            agregar_sesion_pendiente(
                usuario=request.user,
                propuesta_id=propuesta.pk,
                necesidad_id=necesidad_id,
                numero_sesion=numero,
                aula=form.cleaned_data["aula"],
                dia=form.cleaned_data["dia"],
                hora_inicio=form.cleaned_data["hora_inicio"],
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        else:
            messages.success(request, "Sesión añadida al borrador.")
            return redirect(
                "planificacion_web:detalle_propuesta",
                propuesta_id=propuesta.pk,
            )

    return render(
        request,
        "planificacion/agregar_sesion.html",
        {
            "form": form,
            "propuesta": propuesta,
        },
    )

@login_required
@permission_required(
    "planificacion.add_bloquepropuesta",
    raise_exception=True,
)
@require_POST
def reintentar_pendientes_web(request, propuesta_id):
    propuesta = _propuesta_accesible(
        request.user,
        propuesta_id,
    )

    form = ReintentarPendientesForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Introduce un paso de búsqueda entero entre 1 y 1440 minutos.",
        )
    else:
        try:
            resultado = GeneradorHorarios().reintentar(
                usuario=request.user,
                propuesta_id=propuesta.pk,
                paso_minutos=form.cleaned_data["paso_minutos"],
            )
        except ValidationError as error:
            messages.error(request, "; ".join(error.messages))
        else:
            restantes = sum(
                len(pendiente["sesiones"])
                for pendiente in resultado["pendientes"]
            )

            mensaje = (
                f"Sesiones añadidas: {resultado['agregadas']}. "
                f"Sesiones pendientes: {restantes}."
            )

            if restantes:
                messages.warning(request, mensaje)
            else:
                messages.success(request, mensaje)

    return redirect(
        "planificacion_web:detalle_propuesta",
        propuesta_id=propuesta.pk,
    )