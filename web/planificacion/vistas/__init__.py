from .panel import (
    inicio,
)

from .propuestas import (
    generar_propuesta,
    detalle_propuesta,
    _propuesta_accesible,
    enviar_revision_web,
    aprobar_propuesta_web,
    editar_bloque_web,
    devolver_borrador_web,
    retirar_publicacion_web,
    historial_propuestas,
    agregar_sesion_web,
)

from .catalogos import (
    nueva_aula,
    nuevo_docente,
    lista_docentes,
    lista_aulas,
    _render_catalogo,
    estado_docente,
    estado_aula,
    lista_asignaturas,
    asignatura_form_web,
    estado_asignatura,
    lista_periodos,
    nuevo_periodo,
    lista_paralelos,
    nuevo_paralelo,
    editar_aula_web,
    editar_docente_web,
)

from .preparacion import (
    _pantalla_preparacion,
    necesidades_web,
    disponibilidades_web,
    franjas_web,
    inscripciones_web,
)

from .cuentas import (
    habilitar_docente_web,
)

