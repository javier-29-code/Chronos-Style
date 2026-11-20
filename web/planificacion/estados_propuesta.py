from django.core.exceptions import ValidationError


class EstadoPropuesta:
    """Acciones que admite la propuesta según su estado persistido."""

    permite_editar = False
    permite_retirar = False

    def exigir_edicion(self, mensaje):
        if not self.permite_editar:
            raise ValidationError(mensaje)

    def enviar_a_revision(self, propuesta):
        raise ValidationError(
            "Solo se puede enviar a revisión una propuesta en borrador."
        )

    def aprobar(self, propuesta):
        raise ValidationError("Solo se puede aprobar una propuesta en revisión.")

    def devolver_a_borrador(self, propuesta):
        raise ValidationError("Solo se pueden devolver propuestas en revisión.")

    def retirar_publicacion(self, propuesta):
        raise ValidationError("Solo se puede retirar una propuesta aprobada.")


class Borrador(EstadoPropuesta):
    permite_editar = True

    def enviar_a_revision(self, propuesta):
        propuesta.validar_completa()
        return propuesta.Estado.EN_REVISION


class EnRevision(EstadoPropuesta):
    def aprobar(self, propuesta):
        # Las condiciones pueden haber cambiado desde el envío a revisión.
        propuesta.validar_completa()
        return propuesta.Estado.APROBADA

    def devolver_a_borrador(self, propuesta):
        return propuesta.Estado.BORRADOR


class Aprobada(EstadoPropuesta):
    permite_retirar = True

    def retirar_publicacion(self, propuesta):
        return propuesta.Estado.BORRADOR
