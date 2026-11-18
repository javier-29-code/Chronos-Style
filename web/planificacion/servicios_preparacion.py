from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import (
    NecesidadClase,
    DisponibilidadDocente,
    FranjaPlanificacion,
    Horario,
)

@transaction.atomic
def editar_necesidad_clase(
    *,
    actor,
    necesidad_id,
    asignatura,
    docente,
    paralelo,
    sesiones_semanales,
    duracion_minutos,
    prefiere_laboratorio,
    activo,
    tipo_aula_preferida=None,
):
    if not actor.has_perm("planificacion.change_necesidadclase"):
        raise PermissionDenied(
            "No tienes permiso para editar necesidades de clases."
        )

    necesidad = (
        NecesidadClase.objects
        .select_for_update()
        .get(pk=necesidad_id)
    )

    cambia_planificacion = (
        necesidad.asignatura_id != asignatura.pk
        or necesidad.docente_id != docente.pk
        or necesidad.paralelo_id != paralelo.pk
        or necesidad.sesiones_semanales != sesiones_semanales
        or necesidad.duracion_minutos != duracion_minutos
        or necesidad.activo != activo
    )
    if cambia_planificacion and (
        necesidad.propuestas.exists()
        or necesidad.bloques_propuesta.exists()
    ):
        raise ValidationError(
            "Esta necesidad ya está vinculada a una propuesta. "
            "Sus datos se conservan para no alterar la planificación "
            "existente."
        )

    necesidad.asignatura = asignatura
    necesidad.docente = docente
    necesidad.paralelo = paralelo
    necesidad.sesiones_semanales = sesiones_semanales
    necesidad.duracion_minutos = duracion_minutos
    necesidad.prefiere_laboratorio = prefiere_laboratorio
    if tipo_aula_preferida is not None:
        necesidad.tipo_aula_preferida = tipo_aula_preferida
    necesidad.activo = activo

    necesidad.full_clean()
    necesidad.save()

    return necesidad

@transaction.atomic
def _editar_ventana(*, actor, modelo, registro_id, datos):
    permiso = f"planificacion.change_{modelo._meta.model_name}"

    if not actor.has_perm(permiso):
        raise PermissionDenied(
            "No tienes permiso para editar este registro."
        )

    ventana = (
        modelo.objects
        .select_for_update()
        .get(pk=registro_id)
    )

    # Conservamos el ámbito anterior: es donde podría perderse cobertura.
    afectados = {
        "paralelo__periodo_id": ventana.periodo_id,
        "dia": ventana.dia,
    }

    campos = {
        "periodo",
        "dia",
        "hora_inicio",
        "hora_fin",
        "activo",
    }

    if modelo is DisponibilidadDocente:
        afectados["docente_id"] = ventana.docente_id
        campos.add("docente")

    if set(datos) != campos:
        raise ValidationError(
            "Los campos recibidos no corresponden al formulario."
        )

    for campo, valor in datos.items():
        setattr(ventana, campo, valor)

    ventana.full_clean()
    ventana.save()

    # Consultamos después de guardar, dentro de la transacción.
    # Si falla la cobertura, la excepción revierte el cambio.
    horarios = Horario.objects.filter(**afectados)

    for horario in horarios:
        filtros = {
            "periodo_id": afectados["paralelo__periodo_id"],
            "dia": horario.dia,
            "activo": True,
        }

        if modelo is DisponibilidadDocente:
            filtros["docente_id"] = horario.docente_id

        ventanas = modelo.objects.filter(**filtros)

        if not Horario._cubre_intervalo(
            ventanas,
            horario.hora_inicio,
            horario.hora_fin,
        ):
            raise ValidationError(
                f"El cambio dejaría sin cobertura al horario oficial "
                f"#{horario.pk}, de "
                f"{horario.hora_inicio:%H:%M} a "
                f"{horario.hora_fin:%H:%M}. "
                "Ajusta primero su planificación."
            )

    return ventana


def editar_disponibilidad_docente(
    *,
    actor,
    disponibilidad_id,
    **datos,
):
    return _editar_ventana(
        actor=actor,
        modelo=DisponibilidadDocente,
        registro_id=disponibilidad_id,
        datos=datos,
    )


def editar_franja_planificacion(
    *,
    actor,
    franja_id,
    **datos,
):
    return _editar_ventana(
        actor=actor,
        modelo=FranjaPlanificacion,
        registro_id=franja_id,
        datos=datos,
    )