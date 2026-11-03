from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from planificacion.models import Horario

from .models import PerfilDocente


@transaction.atomic
def editar_perfil_docente(*, actor, docente_id, **cambios):
    if (
        not actor.is_authenticated
        or not actor.is_active
        or not actor.has_perm("usuarios.change_perfildocente")
    ):
        raise PermissionDenied(
            "No tienes permiso para editar docentes."
        )

    permitidos = {"titulo", "area", "horas_semanales_max"}

    if set(cambios) - permitidos:
        raise ValidationError(
            "Se intentaron modificar campos no permitidos."
        )

    docente = PerfilDocente.objects.select_for_update().get(
        pk=docente_id,
    )
    limite_anterior = docente.horas_semanales_max

    for campo, valor in cambios.items():
        setattr(docente, campo, valor)

    docente.full_clean()

    if docente.horas_semanales_max < limite_anterior:
        hoy = timezone.localdate()
        lunes = hoy - timedelta(days=hoy.weekday())

        horarios = Horario.objects.filter(
            docente_id=docente.pk,
            paralelo__periodo__fecha_fin__gte=lunes,
        ).select_related("paralelo__periodo")

        for horario in horarios:
            # Usa el máximo propuesto antes de guardarlo.
            horario.docente = docente
            horario._validar_carga_docente(desde=lunes)

    docente.save()

    return docente