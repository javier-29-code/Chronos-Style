from datetime import time


class DisponibilidadDocenteEfectiva:
    """Resuelve la disponibilidad personalizada o predeterminada."""

    @staticmethod
    def obtener(*, docente_id, periodo_id):
        # Importación local para evitar dependencias circulares.
        from .models import DisponibilidadDocente

        registros = list(
            DisponibilidadDocente.objects.filter(
                docente_id=docente_id,
                periodo_id=periodo_id,
            ).values_list(
                "dia",
                "hora_inicio",
                "hora_fin",
                "activo",
            )
        )

        ventanas = {dia: [] for dia in range(1, 8)}

        if not registros:
            for dia in range(1, 6):
                ventanas[dia] = [(time(7), time(20))]

            return ventanas

        for dia, inicio, fin, activo in registros:
            if activo and dia in ventanas:
                ventanas[dia].append((inicio, fin))

        for intervalos in ventanas.values():
            intervalos.sort()

        return ventanas