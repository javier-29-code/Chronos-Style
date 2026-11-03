
from django.core.exceptions import ValidationError
from django.db import transaction

from academico.models import Paralelo

from .models import Horario
from .servicios import _exigir_permiso
from .validaciones_paralelo import ValidadorFranjaParalelo


@transaction.atomic
def guardar_franja_paralelo(*, actor, franja):
    _exigir_permiso(actor, "academico.change_paralelo")

    # Serializa los cambios de franjas del mismo paralelo.
    Paralelo.objects.select_for_update().get(
        pk=franja.paralelo_id,
    )

    franja.full_clean()
    franja.save()

    horarios = Horario.objects.filter(
        paralelo_id=franja.paralelo_id,
    ).order_by("dia", "hora_inicio", "pk")

    for horario in horarios:
        try:
            ValidadorFranjaParalelo.validar(horario)
        except ValidationError as error:
            raise ValidationError(
                "No se guardó el cambio: el horario oficial "
                f"#{horario.pk} quedaría fuera de las franjas "
                "activas del Paralelo/Curso."
            ) from error

    return franja