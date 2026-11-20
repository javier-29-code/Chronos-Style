from datetime import datetime, timedelta

from .exportacion_ics import EventoCalendario


class HorarioAEventoCalendario:
    """Adapta una clase semanal al contrato del exportador de calendarios."""

    def __init__(self, horario):
        self.horario = horario

    def como_evento(self, *, zona_horaria, dominio) -> EventoCalendario | None:
        horario = self.horario
        periodo = horario.periodo
        dias_hasta_clase = (horario.dia - periodo.fecha_inicio.isoweekday()) % 7
        duracion_periodo = (periodo.fecha_fin - periodo.fecha_inicio).days
        dias_restantes = duracion_periodo - dias_hasta_clase
        if dias_restantes < 0:
            return None

        primera_clase = periodo.fecha_inicio + timedelta(days=dias_hasta_clase)
        docente = horario.docente.usuario
        uid = (
            f"bloque-{horario.bloque_origen_id}"
            if horario.bloque_origen_id
            else f"horario-{horario.pk}"
        )
        return EventoCalendario(
            uid=f"chronos-{uid}@{dominio}",
            titulo=horario.asignatura.nombre,
            ubicacion=f"{horario.aula.codigo} · {horario.aula.nombre}",
            descripcion=(
                f"Paralelo {horario.paralelo.nombre}\n"
                f"Docente {docente.get_full_name() or docente.username}"
            ),
            inicio=datetime.combine(primera_clase, horario.hora_inicio, zona_horaria),
            fin=datetime.combine(primera_clase, horario.hora_fin, zona_horaria),
            repeticiones=1 + dias_restantes // 7,
        )
