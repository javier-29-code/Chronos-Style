from django.apps import AppConfig


class PlanificacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planificacion'

    def ready(self):
        from . import avisos_horario  # Registra los receptores de los eventos.
