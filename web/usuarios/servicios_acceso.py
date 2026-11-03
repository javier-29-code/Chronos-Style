from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import PerfilDocente


def comprobar_habilitacion_docente(*, actor, docente):
    permisos = (
        "usuarios.add_usuario",
        "usuarios.change_perfildocente",
    )

    if (
        not actor.is_authenticated
        or not actor.is_active
        or not actor.has_perms(permisos)
    ):
        raise PermissionDenied(
            "No tienes permiso para habilitar este acceso."
        )

    cuenta = docente.usuario

    if (
        cuenta.is_staff
        or cuenta.is_superuser
        or cuenta.get_all_permissions()
        or cuenta.groups.exclude(name="Docente").exists()
    ):
        raise PermissionDenied(
            "Esta cuenta requiere gestión por un administrador."
        )

    if not docente.activo or not cuenta.is_active:
        raise ValidationError(
            "El perfil y la cuenta deben estar activos."
        )

    if cuenta.has_usable_password():
        raise ValidationError(
            "La cuenta ya tiene una contraseña configurada."
        )


@transaction.atomic
def habilitar_acceso_docente(*, actor, docente_id, nueva_contrasena):
    docente = PerfilDocente.objects.select_for_update().get(
        pk=docente_id,
    )
    cuenta = get_user_model().objects.select_for_update().get(
        pk=docente.usuario_id,
    )
    docente.usuario = cuenta

    comprobar_habilitacion_docente(
        actor=actor,
        docente=docente,
    )

    validate_password(nueva_contrasena, user=cuenta)

    grupo = Group.objects.get(name="Docente")

    cuenta.set_password(nueva_contrasena)
    cuenta.save(update_fields=["password"])
    cuenta.groups.add(grupo)

    return cuenta