from datetime import timedelta

from django.core.exceptions import ValidationError

from .disponibilidad_efectiva import DisponibilidadDocenteEfectiva
from .validaciones_paralelo import ValidadorFranjaParalelo


class PasoValidacionHorario:
    """Comprueba una regla y delega al siguiente paso cuando se cumple."""

    def __init__(self, siguiente=None):
        self.siguiente = siguiente

    def validar(self, horario):
        self.comprobar(horario)
        if self.siguiente is not None:
            self.siguiente.validar(horario)

    def comprobar(self, horario):
        raise NotImplementedError


class ValidarDatosYCruces(PasoValidacionHorario):
    def comprobar(self, horario):
        horario.full_clean()


class ValidarFranjasDelParalelo(PasoValidacionHorario):
    def comprobar(self, horario):
        ValidadorFranjaParalelo.validar(horario)


class ValidarCatalogoActivo(PasoValidacionHorario):
    def comprobar(self, horario):
        for campo, mensaje in (
            ("asignatura", "La asignatura está retirada del catálogo activo."),
            ("docente", "El docente está retirado del catálogo activo."),
            ("aula", "El aula está retirada del catálogo activo."),
        ):
            if not getattr(horario, campo).activo:
                raise ValidationError({campo: mensaje})


class ValidarDiaDelPeriodo(PasoValidacionHorario):
    def comprobar(self, horario):
        periodo = horario.paralelo.periodo
        primera_fecha = periodo.fecha_inicio + timedelta(
            days=(horario.dia - periodo.fecha_inicio.isoweekday()) % 7,
        )
        if primera_fecha > periodo.fecha_fin:
            raise ValidationError({
                "dia": "El periodo no contiene ninguna fecha de ese día.",
            })


class ValidarVentanas(PasoValidacionHorario):
    def comprobar(self, horario):
        from .models import FranjaPlanificacion

        periodo = horario.paralelo.periodo
        franjas = FranjaPlanificacion.objects.filter(
            periodo=periodo,
            dia=horario.dia,
            activo=True,
        )
        disponibilidades = DisponibilidadDocenteEfectiva.obtener(
            docente_id=horario.docente_id,
            periodo_id=periodo.pk,
        )[horario.dia]
        inicio, fin = horario.hora_inicio, horario.hora_fin
        errores = {}

        if not horario._cubre_intervalo(franjas, inicio, fin):
            errores["hora_inicio"] = (
                "La clase no cabe completamente en las franjas "
                "de planificación activas."
            )
        if not horario._cubre_intervalo(disponibilidades, inicio, fin):
            errores["docente"] = (
                "El docente no tiene disponibilidad activa "
                "para todo el intervalo."
            )
        if errores:
            raise ValidationError(errores)


VALIDACION_HORARIO_PROPUESTO = ValidarDatosYCruces(
    ValidarFranjasDelParalelo(
        ValidarCatalogoActivo(ValidarDiaDelPeriodo(ValidarVentanas()))
    )
)
