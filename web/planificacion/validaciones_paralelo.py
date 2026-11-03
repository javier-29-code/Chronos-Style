from django.core.exceptions import ValidationError


class ValidadorFranjaParalelo:
    """Comprueba que una clase respete las franjas de su paralelo."""

    @staticmethod
    def validar(horario):
        # Importación local para evitar dependencias circulares.
        from .models import FranjaParalelo

        franjas = FranjaParalelo.objects.filter(
            paralelo_id=horario.paralelo_id,
            activo=True,
        )

        # Sin franjas propias, se mantienen las reglas del periodo.
        if not franjas.exists():
            return

        franjas_del_dia = franjas.filter(dia=horario.dia)

        if not horario._cubre_intervalo(
            franjas_del_dia,
            horario.hora_inicio,
            horario.hora_fin,
        ):
            raise ValidationError({
                "hora_inicio": (
                    "La clase no cabe completamente en las franjas "
                    "activas del Paralelo/Curso."
                ),
            })