from django.contrib.auth import get_user_model
from django.db.models import Q
from django.dispatch import receiver

from academico.models import Inscripcion

from .eventos_horario import horario_publicado, publicacion_retirada
from .models import AvisoHorario, Horario, PropuestaHorario


@receiver(horario_publicado, sender=PropuestaHorario)
def registrar_avisos_publicacion(sender, propuesta, **kwargs):
    horarios = Horario.objects.filter(
        bloque_origen__propuesta=propuesta,
    ).order_by()
    docentes = horarios.values("docente__usuario_id")
    estudiantes = Inscripcion.objects.filter(
        paralelo_id__in=horarios.values("paralelo_id"),
    ).order_by().values("estudiante__usuario_id")
    destinatarios = get_user_model().objects.filter(
        Q(pk__in=docentes) | Q(pk__in=estudiantes),
        is_active=True,
    ).values_list("pk", flat=True)

    AvisoHorario.objects.bulk_create([
        AvisoHorario(propuesta=propuesta, destinatario_id=destinatario_id)
        for destinatario_id in destinatarios
    ])


@receiver(publicacion_retirada, sender=PropuestaHorario)
def retirar_avisos_publicacion(sender, propuesta, **kwargs):
    AvisoHorario.objects.filter(propuesta=propuesta).delete()
