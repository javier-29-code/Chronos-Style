from django.db import transaction

from .models import PropuestaHorario


class ConstructorPropuestaHorario:
    """Arma una propuesta persistida dentro de la transacción del generador."""

    def __init__(self, propuesta):
        self.propuesta = propuesta

    @classmethod
    def iniciar(cls, *, nombre, periodo, autor, necesidades):
        propuesta = PropuestaHorario(nombre=nombre, periodo=periodo, autor=autor)
        propuesta.full_clean()
        propuesta.save()
        propuesta.necesidades.set(necesidades)
        return cls(propuesta)

    @transaction.atomic
    def incorporar_bloque(self, bloque):
        bloque.propuesta = self.propuesta
        bloque.full_clean()
        bloque.save()
        self.propuesta.validar_bloques()

    def finalizar(self, diagnostico, *, actualizar_fecha=False):
        self.propuesta.diagnostico_generacion = diagnostico
        campos = ["diagnostico_generacion"]
        if actualizar_fecha:
            campos.append("actualizada_en")
        self.propuesta.save(update_fields=campos)
        return self.propuesta
