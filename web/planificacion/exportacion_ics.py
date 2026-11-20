from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable


@dataclass(frozen=True)
class EventoCalendario:
    uid: str
    titulo: str
    ubicacion: str
    descripcion: str
    inicio: datetime
    fin: datetime
    repeticiones: int


def _texto(valor):
    return (
        valor.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _fecha_utc(fecha):
    return fecha.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _plegar_linea(linea):
    """Limita las líneas a 75 octetos sin cortar caracteres UTF-8."""
    datos = linea.encode("utf-8")
    partes = []
    while len(datos) > 75:
        corte = 75
        while datos[corte] & 0b11000000 == 0b10000000:
            corte -= 1
        partes.append(datos[:corte])
        datos = b" " + datos[corte:]
    return b"\r\n".join([*partes, datos])


def exportar_ics(eventos: Iterable[EventoCalendario], *, generado_en: datetime):
    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Chronos-Style//Horario academico//ES",
    ]
    sello = _fecha_utc(generado_en)
    for evento in eventos:
        lineas.extend((
            "BEGIN:VEVENT",
            f"UID:{_texto(evento.uid)}",
            f"DTSTAMP:{sello}",
            f"DTSTART:{_fecha_utc(evento.inicio)}",
            f"DTEND:{_fecha_utc(evento.fin)}",
            f"SUMMARY:{_texto(evento.titulo)}",
            f"LOCATION:{_texto(evento.ubicacion)}",
            f"DESCRIPTION:{_texto(evento.descripcion)}",
        ))
        if evento.repeticiones > 1:
            lineas.append(f"RRULE:FREQ=WEEKLY;COUNT={evento.repeticiones}")
        lineas.append("END:VEVENT")
    lineas.append("END:VCALENDAR")
    return b"\r\n".join(_plegar_linea(linea) for linea in lineas) + b"\r\n"
