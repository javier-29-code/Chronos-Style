from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from usuarios.models import PerfilDocente
from django.contrib.auth.forms import SetPasswordForm
from usuarios.servicios_acceso import comprobar_habilitacion_docente, habilitar_acceso_docente


@login_required
@permission_required(
    ("usuarios.add_usuario", "usuarios.change_perfildocente"),
    raise_exception=True,
)
def habilitar_docente_web(request, docente_id):
    docente = get_object_or_404(
        PerfilDocente.objects.select_related("usuario"),
        pk=docente_id,
    )

    try:
        comprobar_habilitacion_docente(
            actor=request.user,
            docente=docente,
        )
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
        return redirect("planificacion_web:lista_docentes")

    form = SetPasswordForm(
        docente.usuario,
        data=request.POST if request.method == "POST" else None,
    )

    if request.method == "POST" and form.is_valid():
        try:
            habilitar_acceso_docente(
                actor=request.user,
                docente_id=docente.pk,
                nueva_contrasena=form.cleaned_data["new_password1"],
            )
        except ValidationError as error:
            form.add_error(None, "; ".join(error.messages))
        else:
            messages.success(
                request,
                f"Acceso habilitado para {docente.usuario.username}.",
            )
            return redirect("planificacion_web:lista_docentes")

    return render(
        request,
        "planificacion/habilitar_docente.html",
        {
            "form": form,
            "docente": docente,
        },
    )
