from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render
from academico.models import PeriodoAcademico, Aula, Asignatura, Paralelo, Inscripcion
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import redirect
from ..formularios_web import NuevaAulaForm, NuevoDocenteForm, AsignaturaForm, PeriodoAcademicoForm, ParaleloForm, EditarDocenteForm
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from usuarios.models import PerfilDocente
from django.urls import reverse
from usuarios.servicios_docentes import editar_perfil_docente
from ..models import Horario

from django.views.decorators.http import require_http_methods

from ..formularios_web import FranjaParaleloForm
from ..models import FranjaParalelo
from ..servicios_franjas_paralelo import guardar_franja_paralelo

@login_required
@permission_required("academico.add_aula", raise_exception=True)
def nueva_aula(request):
    form = NuevaAulaForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                aula = form.save()
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el código ya existe.",
            )
        else:
            messages.success(
                request,
                f"Aula {aula.codigo} creada y disponible en el catálogo.",
            )
            return redirect("planificacion_web:lista_aulas")
        
    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Nueva aula",
            "descripcion": (
                "Registra un aula o laboratorio y su equipamiento."
            ),
            "boton": "Guardar aula",
        },
    )


@login_required
@permission_required(
    ("usuarios.add_usuario", "usuarios.add_perfildocente"),
    raise_exception=True,
)
def nuevo_docente(request):
    form = NuevoDocenteForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data

        try:
            with transaction.atomic():
                usuario = get_user_model()(
                    username=datos["username"],
                    first_name=datos["first_name"],
                    last_name=datos["last_name"],
                    email=datos["email"],
                )
                usuario.set_unusable_password()
                usuario.full_clean()
                usuario.save()

                docente = PerfilDocente(
                    usuario=usuario,
                    titulo=datos["titulo"],
                    area=datos["area"],
                    horas_semanales_max=datos["horas_semanales_max"],
                )
                docente.full_clean()
                docente.save()

        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))

        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el usuario ya existe.",
            )

        else:
            messages.success(
                request,
                "Docente registrado. Ya puedes asignarle necesidades "
                "de clases y disponibilidad.",
            )
            return redirect("planificacion_web:lista_docentes")
        
    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Nuevo docente",
            "descripcion": (
                "Crea su cuenta y perfil académico. "
                "Su acceso con contraseña se habilitará por separado."
            ),
            "boton": "Guardar docente",
        },
    )


@login_required
@permission_required("usuarios.view_perfildocente", raise_exception=True)
def lista_docentes(request):
    busqueda = request.GET.get("q", "").strip()[:200]
    estado = request.GET.get("estado", "activos")

    docentes = PerfilDocente.objects.select_related("usuario")

    if busqueda:
        docentes = docentes.filter(
            Q(usuario__first_name__icontains=busqueda)
            | Q(usuario__last_name__icontains=busqueda)
            | Q(usuario__username__icontains=busqueda)
            | Q(area__icontains=busqueda)
        )

    if estado == "activos":
        docentes = docentes.filter(activo=True)
    elif estado == "retirados":
        docentes = docentes.filter(activo=False)

    pagina = Paginator(
        docentes.order_by("usuario__last_name", "usuario__first_name", "pk"),
        10,
    ).get_page(request.GET.get("pagina"))

    filas = [
        {
            
            "url_acceso": (
                reverse(
                    "planificacion_web:habilitar_docente",
                    args=[docente.pk],
                )
                if (
                    docente.activo
                    and docente.usuario.is_active
                    and not docente.usuario.has_usable_password()
                    and not docente.usuario.is_staff
                    and not docente.usuario.is_superuser
                )
                else None
            ),            

            "nombre": docente.usuario.get_full_name()
            or docente.usuario.username,
            "detalle": (
                f"{docente.area} · "
                f"Máximo {docente.horas_semanales_max} horas semanales"
            ),
            "identificador": docente.usuario.username,
            "activo": docente.activo,
            "url_estado": reverse(
                "planificacion_web:estado_docente",
                args=[docente.pk],
            ),
            
            "url_editar": reverse(
                "planificacion_web:editar_docente",
                args=[docente.pk],
            ),
        }
        for docente in pagina
    ]

    return _render_catalogo(
        request,
        pagina=pagina,
        filas=filas,
        titulo="Docentes",
        descripcion="Equipo docente disponible para la planificación.",
        url_nuevo=reverse("planificacion_web:nuevo_docente"),
        puede_agregar=(
            request.user.has_perm("usuarios.add_usuario")
            and request.user.has_perm("usuarios.add_perfildocente")
        ),
        puede_cambiar=request.user.has_perm(
            "usuarios.change_perfildocente"
        ),
        
        puede_habilitar=request.user.has_perms(
            ("usuarios.add_usuario", "usuarios.change_perfildocente")
        ),
        busqueda=busqueda,
        estado=estado,
    )


@login_required
@permission_required("academico.view_aula", raise_exception=True)
def lista_aulas(request):
    busqueda = request.GET.get("q", "").strip()[:200]
    estado = request.GET.get("estado", "activos")

    aulas = Aula.objects.all()

    if busqueda:
        aulas = aulas.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(ubicacion__icontains=busqueda)
        )

    if estado == "activos":
        aulas = aulas.filter(activo=True)
    elif estado == "retirados":
        aulas = aulas.filter(activo=False)

    pagina = Paginator(
        aulas.order_by("codigo"),
        10,
    ).get_page(request.GET.get("pagina"))

    filas = [
        {
            "nombre": aula.nombre,
            "detalle": (
                f"{aula.get_tipo_display()} · "
                f"{aula.ubicacion or 'Sin ubicación registrada'}"
            ),
            "identificador": aula.codigo,
            "activo": aula.activo,
            "url_estado": reverse(
                "planificacion_web:estado_aula",
                args=[aula.pk],
            ),
            
            "url_editar": reverse(
                "planificacion_web:editar_aula",
                args=[aula.pk],
            ),
        }
        for aula in pagina
    ]

    return _render_catalogo(
        request,
        pagina=pagina,
        filas=filas,
        titulo="Aulas",
        descripcion="Aulas y laboratorios de la institución.",
        url_nuevo=reverse("planificacion_web:nueva_aula"),
        puede_agregar=request.user.has_perm("academico.add_aula"),
        puede_cambiar=request.user.has_perm("academico.change_aula"),
        busqueda=busqueda,
        estado=estado,
    )


def _render_catalogo(request, **contexto):
    filtros = request.GET.copy()
    filtros.pop("pagina", None)
    contexto["filtros"] = filtros.urlencode()

    return render(
        request,
        "planificacion/catalogo.html",
        contexto,
    )


@login_required
@permission_required("usuarios.change_perfildocente", raise_exception=True)
@require_POST
def estado_docente(request, docente_id):
    docente = get_object_or_404(PerfilDocente, pk=docente_id)
    estado = request.POST.get("estado")

    if estado not in {"activo", "retirado"}:
        messages.error(request, "Acción inválida.")
    else:
        docente.activo = estado == "activo"
        docente.save(update_fields=["activo"])
        messages.success(request, "Estado del docente actualizado.")

    return redirect("planificacion_web:lista_docentes")


@login_required
@permission_required("academico.change_aula", raise_exception=True)
@require_POST
def estado_aula(request, aula_id):
    aula = get_object_or_404(Aula, pk=aula_id)
    estado = request.POST.get("estado")

    if estado not in {"activo", "retirado"}:
        messages.error(request, "Acción inválida.")
    else:
        aula.activo = estado == "activo"
        aula.save(update_fields=["activo"])
        messages.success(request, "Estado del aula actualizado.")

    return redirect("planificacion_web:lista_aulas")


@login_required
@permission_required("academico.view_asignatura", raise_exception=True)
def lista_asignaturas(request):
    busqueda = request.GET.get("q", "").strip()[:200]
    estado = request.GET.get("estado", "activos")

    asignaturas = Asignatura.objects.all()

    if busqueda:
        asignaturas = asignaturas.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
        )

    if estado == "activos":
        asignaturas = asignaturas.filter(activo=True)
    elif estado == "retirados":
        asignaturas = asignaturas.filter(activo=False)

    pagina = Paginator(
        asignaturas.order_by("nombre", "pk"),
        10,
    ).get_page(request.GET.get("pagina"))

    filas = [
        {
            "nombre": asignatura.nombre,
            "detalle": "Asignatura del catálogo académico",
            "identificador": asignatura.codigo,
            "activo": asignatura.activo,
            "url_editar": reverse(
                "planificacion_web:editar_asignatura",
                args=[asignatura.pk],
            ),
            "url_estado": reverse(
                "planificacion_web:estado_asignatura",
                args=[asignatura.pk],
            ),
        }
        for asignatura in pagina
    ]

    return _render_catalogo(
        request,
        pagina=pagina,
        filas=filas,
        titulo="Asignaturas",
        descripcion="Materias disponibles para la planificación académica.",
        url_nuevo=reverse("planificacion_web:nueva_asignatura"),
        puede_agregar=request.user.has_perm("academico.add_asignatura"),
        puede_cambiar=request.user.has_perm("academico.change_asignatura"),
        busqueda=busqueda,
        estado=estado,
    )


@login_required
def asignatura_form_web(request, asignatura_id=None):
    editando = asignatura_id is not None

    permiso = (
        "academico.change_asignatura"
        if editando
        else "academico.add_asignatura"
    )

    if not request.user.has_perm(permiso):
        raise PermissionDenied(
            "No tienes permiso para realizar esta operación."
        )

    asignatura = (
        get_object_or_404(Asignatura, pk=asignatura_id)
        if editando
        else None
    )

    form = AsignaturaForm(
        request.POST if request.method == "POST" else None,
        instance=asignatura,
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el código ya existe.",
            )
        else:
            messages.success(request, "Asignatura guardada.")
            return redirect("planificacion_web:lista_asignaturas")

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Editar asignatura" if editando else "Nueva asignatura",
            "descripcion": "Completa el código, nombre y estado de la materia.",
            "boton": "Guardar asignatura",
        },
    )


@login_required
@permission_required("academico.change_asignatura", raise_exception=True)
@require_POST
def estado_asignatura(request, asignatura_id):
    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)
    estado = request.POST.get("estado")

    if estado not in {"activo", "retirado"}:
        messages.error(request, "Acción inválida.")
    else:
        asignatura.activo = estado == "activo"
        asignatura.save(update_fields=["activo"])
        messages.success(request, "Estado de la asignatura actualizado.")

    return redirect("planificacion_web:lista_asignaturas")


@login_required
@permission_required(
    "academico.view_periodoacademico",
    raise_exception=True,
)
def lista_periodos(request):
    busqueda = request.GET.get("q", "").strip()[:200]

    periodos = PeriodoAcademico.objects.all()

    if busqueda:
        periodos = periodos.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
        )

    pagina = Paginator(
        periodos.order_by("-fecha_inicio", "-pk"),
        10,
    ).get_page(request.GET.get("pagina"))

    return render(
        request,
        "planificacion/periodos.html",
        {
            "pagina": pagina,
            "busqueda": busqueda,
        },
    )


@login_required
@permission_required(
    "academico.add_periodoacademico",
    raise_exception=True,
)
def nuevo_periodo(request):
    form = PeriodoAcademicoForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el código ya existe.",
            )
        else:
            messages.success(request, "Periodo académico registrado.")
            return redirect("planificacion_web:lista_periodos")

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Nuevo periodo académico",
            "descripcion": (
                "Define las fechas durante las que se impartirán las clases."
            ),
            "boton": "Guardar periodo",
        },
    )


@login_required
@permission_required(
    "academico.view_paralelo",
    raise_exception=True,
)
def lista_paralelos(request):
    busqueda = request.GET.get("q", "").strip()[:200]

    paralelos = Paralelo.objects.select_related(
        "programa",
        "periodo",
    )

    if busqueda:
        paralelos = paralelos.filter(
            Q(nombre__icontains=busqueda)
            | Q(programa__nombre__icontains=busqueda)
            | Q(programa__codigo__icontains=busqueda)
            | Q(periodo__codigo__icontains=busqueda)
        )

    paralelos = paralelos.annotate(
        total_inscritos=Count("inscripciones", distinct=True),
        total_bloques=Count("horarios", distinct=True),
    ).order_by(
        "-periodo__fecha_inicio",
        "programa__nombre",
        "nombre",
        "pk",
    )

    pagina = Paginator(paralelos, 10).get_page(
        request.GET.get("pagina")
    )

    return render(
        request,
        "planificacion/paralelos.html",
        {
            "pagina": pagina,
            "busqueda": busqueda,
        },
    )


@login_required
@permission_required(
    "academico.add_paralelo",
    raise_exception=True,
)
def nuevo_paralelo(request):
    form = ParaleloForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el paralelo "
                "ya existe en ese programa y periodo.",
            )
        else:
            messages.success(request, "Paralelo/Curso registrado.")
            return redirect("planificacion_web:lista_paralelos")

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Nuevo paralelo/curso",
            "descripcion": (
                "Selecciona el programa y el periodo "
                "al que pertenece."
            ),
            "boton": "Guardar paralelo",
        },
    )


@login_required
@permission_required("academico.change_aula", raise_exception=True)
def editar_aula_web(request, aula_id):
    aula = get_object_or_404(Aula, pk=aula_id)

    form = NuevaAulaForm(
        request.POST if request.method == "POST" else None,
        instance=aula,
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si el código ya existe.",
            )
        else:
            messages.success(request, "Aula actualizada.")
            return redirect("planificacion_web:lista_aulas")

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Editar aula",
            "descripcion": (
                "Actualiza los datos, capacidad y equipamiento del espacio."
            ),
            "boton": "Guardar cambios",
        },
    )


@login_required
@permission_required(
    "usuarios.change_perfildocente",
    raise_exception=True,
)
def editar_docente_web(request, docente_id):
    docente = get_object_or_404(
        PerfilDocente.objects.select_related("usuario"),
        pk=docente_id,
    )

    form = EditarDocenteForm(
        request.POST if request.method == "POST" else None,
        instance=docente,
    )

    if request.method == "POST" and form.is_valid():
        try:
            editar_perfil_docente(
                actor=request.user,
                docente_id=docente.pk,
                **form.cleaned_data,
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        else:
            messages.success(request, "Perfil docente actualizado.")
            return redirect("planificacion_web:lista_docentes")

    return render(
        request,
        "planificacion/formulario_catalogo.html",
        {
            "form": form,
            "titulo": "Editar docente",
            "descripcion": (
                docente.usuario.get_full_name()
                or docente.usuario.username
            ),
            "boton": "Guardar cambios",
        },
    )


@login_required
@permission_required(
    (
        "academico.view_paralelo",
        "planificacion.view_horario",
    ),
    raise_exception=True,
)
def detalle_paralelo_web(request, paralelo_id):
    paralelo = get_object_or_404(
        Paralelo.objects.select_related(
            "programa",
            "periodo",
        ),
        pk=paralelo_id,
    )

    horarios = list(
        Horario.objects.filter(
            paralelo=paralelo,
        ).select_related(
            "asignatura",
            "docente__usuario",
            "aula",
        ).order_by(
            "dia",
            "hora_inicio",
            "pk",
        )
    )

    asignaturas = (
        Asignatura.objects
        .filter(horarios__paralelo=paralelo)
        .distinct()
        .order_by("nombre", "pk")
    )

    puede_ver_inscritos = request.user.has_perm(
        "academico.view_inscripcion"
    )

    pagina_estudiantes = None

    if puede_ver_inscritos:
        inscripciones = (
            Inscripcion.objects
            .filter(paralelo=paralelo)
            .select_related("estudiante__usuario")
            .order_by(
                "estudiante__usuario__last_name",
                "estudiante__usuario__first_name",
                "pk",
            )
        )

        pagina_estudiantes = Paginator(
            inscripciones,
            20,
        ).get_page(request.GET.get("pagina"))

    franjas_paralelo = list(
        FranjaParalelo.objects.filter(
            paralelo=paralelo,
        ).order_by("dia", "hora_inicio", "pk")
    )

    return render(
        request,
        "planificacion/detalle_paralelo.html",
        {
            "paralelo": paralelo,
            "horarios": horarios,
            "asignaturas": asignaturas,
            "total_bloques": len(horarios),
            "puede_ver_inscritos": puede_ver_inscritos,
            "pagina_estudiantes": pagina_estudiantes,
            "franjas_paralelo": franjas_paralelo,
            "tiene_franjas_propias": any(
                franja.activo for franja in franjas_paralelo),
        },
    )
    
@login_required
@permission_required(
    (
        "academico.view_paralelo",
        "planificacion.view_horario",
        "academico.change_paralelo",
    ),
    raise_exception=True,
)
@require_http_methods(["GET", "POST"])
def franja_paralelo_form_web(request, paralelo_id, franja_id=None):
    paralelo = get_object_or_404(
        Paralelo.objects.select_related("programa", "periodo"),
        pk=paralelo_id,
    )

    franja = (
        get_object_or_404(
            FranjaParalelo,
            pk=franja_id,
            paralelo=paralelo,
        )
        if franja_id is not None
        else FranjaParalelo(paralelo=paralelo)
    )

    form = FranjaParaleloForm(
        request.POST if request.method == "POST" else None,
        instance=franja,
        paralelo=paralelo,
    )

    if request.method == "POST" and form.is_valid():
        try:
            guardar_franja_paralelo(
                actor=request.user,
                franja=form.save(commit=False),
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        except IntegrityError:
            form.add_error(
                None,
                "No se pudo guardar. Comprueba si la franja ya existe.",
            )
        else:
            messages.success(request, "Franja del paralelo guardada.")
            return redirect(
                "planificacion_web:detalle_paralelo",
                paralelo_id=paralelo.pk,
            )

    return render(
        request,
        "planificacion/formulario_franja_paralelo.html",
        {
            "form": form,
            "paralelo": paralelo,
            "titulo": (
                "Editar franja de clases"
                if franja_id is not None
                else "Nueva franja de clases"
            ),
        },
    )


@login_required
@permission_required(
    (
        "academico.view_paralelo",
        "planificacion.view_horario",
        "academico.change_paralelo",
    ),
    raise_exception=True,
)
@require_POST
def estado_franja_paralelo_web(request, paralelo_id, franja_id):
    franja = get_object_or_404(
        FranjaParalelo,
        pk=franja_id,
        paralelo_id=paralelo_id,
    )

    estado = request.POST.get("estado")

    if estado not in {"activo", "inactivo"}:
        messages.error(request, "Acción inválida.")
    else:
        franja.activo = estado == "activo"

        try:
            guardar_franja_paralelo(
                actor=request.user,
                franja=franja,
            )
        except ValidationError as error:
            messages.error(request, "; ".join(error.messages))
        else:
            messages.success(request, "Estado de la franja actualizado.")

    return redirect(
        "planificacion_web:detalle_paralelo",
        paralelo_id=paralelo_id,
    )