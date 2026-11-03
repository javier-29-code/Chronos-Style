from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from academico.models import Inscripcion
from ..models import NecesidadClase, DisponibilidadDocente, FranjaPlanificacion
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from ..formularios_web import NecesidadClaseForm, DisponibilidadDocenteForm, FranjaPlanificacionForm, InscripcionForm
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from ..servicios_preparacion import (
    editar_necesidad_clase,
    editar_disponibilidad_docente,
    editar_franja_planificacion,
    )

def _pantalla_preparacion(
    request,
    *,
    formulario,
    registros,
    titulo,
    descripcion,
    ruta,
    ruta_editar=None,
    permiso_editar=None,
):
    form = formulario(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el registro ya existe.",
            )
        else:
            messages.success(request, "Registro guardado.")
            return redirect(ruta)

    pagina = Paginator(
        registros.order_by("-pk"),
        10,
    ).get_page(request.GET.get("pagina"))

    return render(
        request,
        "planificacion/preparacion.html",
        {
            "form": form,
            "pagina": pagina,
            "titulo": titulo,
            "descripcion": descripcion,
            "ruta_editar": ruta_editar,
            "puede_editar": (
                request.user.has_perm(permiso_editar)
                if permiso_editar
                else False
            ),
        },
    )


@login_required
@permission_required(
    (
        "planificacion.view_necesidadclase",
        "planificacion.add_necesidadclase",
    ),
    raise_exception=True,
)
def necesidades_web(request):
    return _pantalla_preparacion(
        request,
        formulario=NecesidadClaseForm,
        registros=NecesidadClase.objects.select_related(
            "asignatura",
            "docente__usuario",
            "paralelo__programa",
            "paralelo__periodo",
        ),
        titulo="Necesidades de clases",
        descripcion=(
            "Indica qué materias deben programarse, "
            "para qué grupos y con qué docentes."
        ),
        ruta="planificacion_web:necesidades",

        ruta_editar="planificacion_web:editar_necesidad",
        permiso_editar="planificacion.change_necesidadclase",
    )


@login_required
@permission_required(
    (
        "planificacion.view_disponibilidaddocente",
        "planificacion.add_disponibilidaddocente",
    ),
    raise_exception=True,
)
def disponibilidades_web(request):
    return _pantalla_preparacion(
        request,
        formulario=DisponibilidadDocenteForm,
        registros=DisponibilidadDocente.objects.select_related(
            "docente__usuario",
            "periodo",
        ),
        titulo="Disponibilidades docentes",
        descripcion=(
            "Registra los días y horas en que cada docente "
            "puede impartir clases durante un periodo."
        ),
        ruta="planificacion_web:disponibilidades",
        ruta_editar="planificacion_web:editar_disponibilidad",
        permiso_editar="planificacion.change_disponibilidaddocente",
    )


@login_required
@permission_required(
    (
        "planificacion.view_franjaplanificacion",
        "planificacion.add_franjaplanificacion",
    ),
    raise_exception=True,
)
def franjas_web(request):
    return _pantalla_preparacion(
        request,
        formulario=FranjaPlanificacionForm,
        registros=FranjaPlanificacion.objects.select_related("periodo"),
        titulo="Franjas de planificación",
        descripcion=(
            "Define las ventanas de funcionamiento "
            "en las que se pueden programar clases."
        ),
        ruta="planificacion_web:franjas",
        ruta_editar="planificacion_web:editar_franja",
        permiso_editar="planificacion.change_franjaplanificacion",
    )


@login_required
@permission_required(
    ("academico.view_inscripcion", "academico.add_inscripcion"),
    raise_exception=True,
)
def inscripciones_web(request):
    form = InscripcionForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None,
                "El estudiante ya está asociado a ese paralelo.",
            )
        else:
            messages.success(
                request,
                "Estudiante asociado al paralelo.",
            )
            return redirect("planificacion_web:inscripciones")

    registros = (
        Inscripcion.objects
        .select_related(
            "estudiante__usuario",
            "paralelo__programa",
            "paralelo__periodo",
        )
        .order_by("-fecha_inscripcion", "-pk")
    )

    pagina = Paginator(registros, 10).get_page(
        request.GET.get("pagina")
    )

    return render(
        request,
        "planificacion/inscripciones.html",
        {
            "form": form,
            "pagina": pagina,
        },
    )

@login_required
@permission_required(
    "planificacion.change_necesidadclase",
    raise_exception=True,
)
def editar_necesidad_web(request, necesidad_id):
    necesidad = get_object_or_404(
        NecesidadClase.objects.select_related(
            "asignatura",
            "docente__usuario",
            "paralelo",
        ),
        pk=necesidad_id,
    )

    form = NecesidadClaseForm(
        request.POST if request.method == "POST" else None,
        instance=necesidad,
    )

    if request.method == "POST" and form.is_valid():
        try:
            editar_necesidad_clase(
                actor=request.user,
                necesidad_id=necesidad.pk,
                **form.cleaned_data,
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si ya existe "
                "una necesidad con esa asignatura, docente y paralelo.",
            )
        else:
            messages.success(
                request,
                "Necesidad de clase actualizada.",
            )
            return redirect("planificacion_web:necesidades")

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Editar necesidad de clase",
            "descripcion": (
                "Las necesidades vinculadas a propuestas "
                "conservan sus datos y no permiten modificaciones."
            ),
            "boton": "Guardar cambios",
        },
    )
    
    
def _editar_ventana_web(
    request,
    *,
    registro,
    formulario,
    servicio,
    argumento_id,
    titulo,
    ruta,
):
    form = formulario(
        request.POST if request.method == "POST" else None,
        instance=registro,
    )

    if request.method == "POST" and form.is_valid():
        try:
            servicio(
                actor=request.user,
                **{argumento_id: registro.pk},
                **form.cleaned_data,
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si ya existe "
                "un registro con esos datos.",
            )
        else:
            messages.success(request, "Registro actualizado.")
            return redirect(ruta)

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": titulo,
            "descripcion": (
                "El cambio debe conservar la cobertura "
                "de los horarios oficiales existentes."
            ),
            "boton": "Guardar cambios",
        },
    )


@login_required
@permission_required(
    "planificacion.change_disponibilidaddocente",
    raise_exception=True,
)
def editar_disponibilidad_web(request, disponibilidad_id):
    disponibilidad = get_object_or_404(
        DisponibilidadDocente,
        pk=disponibilidad_id,
    )

    return _editar_ventana_web(
        request,
        registro=disponibilidad,
        formulario=DisponibilidadDocenteForm,
        servicio=editar_disponibilidad_docente,
        argumento_id="disponibilidad_id",
        titulo="Editar disponibilidad docente",
        ruta="planificacion_web:disponibilidades",
    )


@login_required
@permission_required(
    "planificacion.change_franjaplanificacion",
    raise_exception=True,
)
def editar_franja_web(request, franja_id):
    franja = get_object_or_404(
        FranjaPlanificacion,
        pk=franja_id,
    )

    return _editar_ventana_web(
        request,
        registro=franja,
        formulario=FranjaPlanificacionForm,
        servicio=editar_franja_planificacion,
        argumento_id="franja_id",
        titulo="Editar franja de planificación",
        ruta="planificacion_web:franjas",
    )