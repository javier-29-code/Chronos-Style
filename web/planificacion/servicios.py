from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .eventos_horario import horario_publicado, publicacion_retirada
from .models import Horario, PropuestaHorario, BloquePropuesta,RetiradaPublicacion

from django.utils import timezone

from datetime import datetime, timedelta

CAMPOS_EDITABLES = frozenset({
    "asignatura",
    "docente",
    "aula",
    "paralelo",
    "dia",
    "hora_inicio",
    "hora_fin",
})


def _exigir_permiso(usuario, permiso):
    if (
        not usuario.is_authenticated
        or not usuario.is_active
        or not usuario.has_perm(permiso)
    ):
        raise PermissionDenied(
            "No tienes permiso para realizar esta operación."
        )


def _validar_campos(datos):
    desconocidos = set(datos) - CAMPOS_EDITABLES

    if desconocidos:
        raise ValidationError(
            "Campos no permitidos: "
            + ", ".join(sorted(desconocidos))
        )


@transaction.atomic
def crear_horario(*, usuario, **datos):
    _exigir_permiso(usuario, "planificacion.add_horario")
    _validar_campos(datos)

    horario = Horario(**datos)
    horario.full_clean()
    horario.save()

    return horario


@transaction.atomic
def actualizar_horario(*, usuario, horario_id, **cambios):
    _exigir_permiso(usuario, "planificacion.change_horario")
    _validar_campos(cambios)

    # Cargamos otra instancia para no modificar un objeto
    # que la pantalla u otro código conserve en memoria.
    horario = Horario.objects.select_for_update().get(
        pk=horario_id,
    )

    for campo, valor in cambios.items():
        setattr(horario, campo, valor)

    horario.full_clean()
    horario.save()

    return horario


@transaction.atomic
def eliminar_horario(*, usuario, horario_id):
    _exigir_permiso(usuario, "planificacion.delete_horario")

    horario = Horario.objects.select_for_update().get(
        pk=horario_id,
    )
    horario.delete()
    
    
@transaction.atomic
def enviar_propuesta_revision(*, usuario, propuesta_id):
    _exigir_permiso(
        usuario,
        "planificacion.change_propuestahorario",
    )

    propuesta = PropuestaHorario.objects.select_for_update().get(
        pk=propuesta_id,
    )

    propuesta.estado = propuesta.estado_actual.enviar_a_revision(propuesta)
    propuesta.save(
        update_fields=["estado", "actualizada_en"],
    )

    return propuesta


@transaction.atomic
def aprobar_propuesta(*, usuario, propuesta_id):
    _exigir_permiso(
        usuario,
        "planificacion.aprobar_propuestahorario",
    )

    propuesta = PropuestaHorario.objects.select_for_update().get(
        pk=propuesta_id,
    )

    siguiente_estado = propuesta.estado_actual.aprobar(propuesta)

    bloques = propuesta.bloques.select_related(
        "necesidad__asignatura",
        "necesidad__docente",
        "necesidad__paralelo__periodo",
        "aula",
    ).order_by("pk")

    for bloque in bloques:
        horario = bloque.como_horario()
        horario.bloque_origen = bloque

        # También comprueba los bloques oficiales creados
        # anteriormente dentro de esta misma transacción.
        horario.validar_para_propuesta()
        horario.save()

    propuesta.estado = siguiente_estado
    propuesta.aprobada_por = usuario
    propuesta.aprobada_en = timezone.now()
    propuesta.full_clean()
    propuesta.save(
        update_fields=[
            "estado",
            "aprobada_por",
            "aprobada_en",
            "actualizada_en",
        ],
    )

    horario_publicado.send(sender=PropuestaHorario, propuesta=propuesta)
    return propuesta

@transaction.atomic
def editar_bloque_propuesta(*, usuario, bloque_id, **cambios):
    _exigir_permiso(
        usuario,
        "planificacion.change_bloquepropuesta",
    )

    permitidos = {"aula", "dia", "hora_inicio", "hora_fin"}

    if set(cambios) - permitidos:
        raise ValidationError(
            "Se intentaron modificar campos no permitidos."
        )

    propuesta_id = (
        BloquePropuesta.objects
        .values_list("propuesta_id", flat=True)
        .get(pk=bloque_id)
    )

    propuesta = PropuestaHorario.objects.select_for_update().get(
        pk=propuesta_id,
    )

    if (
        propuesta.autor_id != usuario.pk
        and not usuario.has_perm(
            "planificacion.view_propuestahorario"
        )
    ):
        raise PermissionDenied(
            "No puedes acceder a esta propuesta."
        )

    propuesta.estado_actual.exigir_edicion(
        "Solo se pueden editar propuestas en borrador."
    )

    bloque = BloquePropuesta.objects.select_for_update().get(
        pk=bloque_id,
        propuesta=propuesta,
    )

    for campo, valor in cambios.items():
        setattr(bloque, campo, valor)

    bloque.full_clean()

    if not bloque.aula.activo:
        raise ValidationError("El aula seleccionada está inactiva.")

    bloque.save()

    # Permite trabajar con borradores incompletos, pero exige
    # que sus bloques presentes sean compatibles.
    propuesta.validar_alcance()
    propuesta.validar_bloques()
    propuesta.save(update_fields=["actualizada_en"])

    return bloque

@transaction.atomic
def devolver_propuesta_borrador(*, usuario, propuesta_id):
    _exigir_permiso(
        usuario,
        "planificacion.aprobar_propuestahorario",
    )

    propuesta = PropuestaHorario.objects.select_for_update().get(
        pk=propuesta_id,
    )

    propuesta.estado = propuesta.estado_actual.devolver_a_borrador(propuesta)
    propuesta.save(
        update_fields=["estado", "actualizada_en"],
    )

    return propuesta


@transaction.atomic
def retirar_publicacion(*, usuario, propuesta_id, motivo):
    _exigir_permiso(
        usuario,
        "planificacion.aprobar_propuestahorario",
    )
    _exigir_permiso(usuario, "planificacion.delete_horario")

    motivo = (motivo or "").strip()

    if len(motivo) < 10:
        raise ValidationError(
            "Explica el motivo con al menos 10 caracteres."
        )

    propuesta = PropuestaHorario.objects.select_for_update().get(
        pk=propuesta_id,
    )

    siguiente_estado = propuesta.estado_actual.retirar_publicacion(propuesta)

    horarios = list(
        Horario.objects.select_for_update()
        .filter(bloque_origen__propuesta=propuesta)
        .order_by("pk")
    )

    copia = {
        "aprobada_por_id": propuesta.aprobada_por_id,
        "aprobada_en": (
            propuesta.aprobada_en.isoformat()
            if propuesta.aprobada_en
            else None
        ),
        "horarios": [
            {
                "id": horario.pk,
                "asignatura_id": horario.asignatura_id,
                "docente_id": horario.docente_id,
                "aula_id": horario.aula_id,
                "paralelo_id": horario.paralelo_id,
                "dia": horario.dia,
                "hora_inicio": horario.hora_inicio.isoformat(),
                "hora_fin": horario.hora_fin.isoformat(),
                "bloque_origen_id": horario.bloque_origen_id,
            }
            for horario in horarios
        ],
    }

    RetiradaPublicacion.objects.create(
        propuesta=propuesta,
        usuario=usuario,
        motivo=motivo,
        datos_publicacion=copia,
    )

    Horario.objects.filter(
        pk__in=[horario.pk for horario in horarios]
    ).delete()

    propuesta.estado = siguiente_estado
    propuesta.aprobada_por = None
    propuesta.aprobada_en = None
    propuesta.save(
        update_fields=[
            "estado",
            "aprobada_por",
            "aprobada_en",
            "actualizada_en",
        ],
    )

    publicacion_retirada.send(sender=PropuestaHorario, propuesta=propuesta)
    return propuesta

@transaction.atomic
def agregar_sesion_pendiente(
    *,
    usuario,
    propuesta_id,
    necesidad_id,
    numero_sesion,
    aula,
    dia,
    hora_inicio,
):
    _exigir_permiso(
        usuario,
        "planificacion.add_bloquepropuesta",
    )

    propuesta = PropuestaHorario.objects.select_for_update().get(
        pk=propuesta_id,
    )

    if (
        propuesta.autor_id != usuario.pk
        and not usuario.has_perm(
            "planificacion.view_propuestahorario"
        )
    ):
        raise PermissionDenied(
            "No puedes acceder a esta propuesta."
        )

    propuesta.estado_actual.exigir_edicion(
        "Solo se pueden añadir sesiones a un borrador."
    )

    necesidad = (
        propuesta.necesidades
        .filter(pk=necesidad_id)
        .first()
    )

    if necesidad is None:
        raise ValidationError(
            "La necesidad no pertenece al alcance de esta propuesta."
        )

    inicio = datetime.combine(
        propuesta.periodo.fecha_inicio,
        hora_inicio,
    )
    fin = inicio + timedelta(minutes=necesidad.duracion_minutos)

    if fin.date() != inicio.date():
        raise ValidationError(
            "La sesión debe empezar y terminar el mismo día."
        )

    bloque = BloquePropuesta(
        propuesta=propuesta,
        necesidad=necesidad,
        numero_sesion=numero_sesion,
        aula=aula,
        dia=dia,
        hora_inicio=hora_inicio,
        hora_fin=fin.time(),
    )
    bloque.full_clean()
    bloque.save()

    propuesta.validar_alcance()
    propuesta.validar_bloques()
    propuesta.save(update_fields=["actualizada_en"])

    return bloque
