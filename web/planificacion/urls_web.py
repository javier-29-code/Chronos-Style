from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .vistas import (
    inicio, 
    generar_propuesta, 
    detalle_propuesta, 
    enviar_revision_web, 
    aprobar_propuesta_web, 
    editar_bloque_web, 
    devolver_borrador_web, 
    retirar_publicacion_web, 
    historial_propuestas, 
    nueva_aula, 
    nuevo_docente, 
    lista_docentes, 
    lista_aulas, 
    estado_docente, 
    estado_aula, 
    necesidades_web, 
    disponibilidades_web, 
    franjas_web, 
    agregar_sesion_web, 
    lista_asignaturas, 
    asignatura_form_web, 
    estado_asignatura, 
    lista_periodos, 
    nuevo_periodo, 
    lista_paralelos, 
    nuevo_paralelo, 
    inscripciones_web, 
    habilitar_docente_web, 
    editar_aula_web, 
    editar_docente_web
)

from .vistas.preparacion import (
    editar_necesidad_web,
    editar_disponibilidad_web,
    editar_franja_web,
    )

from .vistas.catalogos import (
    detalle_paralelo_web,
    franja_paralelo_form_web,
    estado_franja_paralelo_web,
)

from .vistas.propuestas import reintentar_pendientes_web

app_name = "planificacion_web"

urlpatterns = [
    path("", inicio, name="inicio"),
    path(
        "ingresar/",
        LoginView.as_view(
            template_name="planificacion/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "salir/",
        LogoutView.as_view(),
        name="logout",
    ),
    
    path(
        "propuestas/generar/",
        generar_propuesta,
        name="generar_propuesta",
    ),
    path(
        "propuestas/<int:propuesta_id>/",
        detalle_propuesta,
        name="detalle_propuesta",
    ),
    
        path(
        "propuestas/<int:propuesta_id>/enviar-revision/",
        enviar_revision_web,
        name="enviar_revision",
    ),
    path(
        "propuestas/<int:propuesta_id>/aprobar/",
        aprobar_propuesta_web,
        name="aprobar_propuesta",
    ),
    
    path(
        "propuestas/<int:propuesta_id>/bloques/<int:bloque_id>/editar/",
        editar_bloque_web,
        name="editar_bloque",
    ),
    
    path(
        "propuestas/<int:propuesta_id>/devolver-borrador/",
        devolver_borrador_web,
        name="devolver_borrador",
    ),
    
    path(
        "propuestas/<int:propuesta_id>/retirar-publicacion/",
        retirar_publicacion_web,
        name="retirar_publicacion",
    ),
    
    path(
        "propuestas/",
        historial_propuestas,
        name="historial_propuestas",
    ),
    path("aulas/nueva/", nueva_aula, name="nueva_aula"),
    path("docentes/nuevo/", nuevo_docente, name="nuevo_docente"),
    
    path("docentes/", lista_docentes, name="lista_docentes"),
    path("aulas/", lista_aulas, name="lista_aulas"),
    path(
        "docentes/<int:docente_id>/estado/",
        estado_docente,
        name="estado_docente",
    ),
    path(
        "aulas/<int:aula_id>/estado/",
        estado_aula,
        name="estado_aula",
    ),
    
    path("necesidades/", necesidades_web, name="necesidades"),
    path(
        "disponibilidades/",
        disponibilidades_web,
        name="disponibilidades",
    ),
    path("franjas/", franjas_web, name="franjas"),
    
    path(
        "propuestas/<int:propuesta_id>/sesiones/agregar/",
        agregar_sesion_web,
        name="agregar_sesion",
    ),
    
    path(
        "asignaturas/",
        lista_asignaturas,
        name="lista_asignaturas",
    ),
    path(
        "asignaturas/nueva/",
        asignatura_form_web,
        name="nueva_asignatura",
    ),
    path(
        "asignaturas/<int:asignatura_id>/editar/",
        asignatura_form_web,
        name="editar_asignatura",
    ),
    path(
        "asignaturas/<int:asignatura_id>/estado/",
        estado_asignatura,
        name="estado_asignatura",
    ),
    
    path("periodos/", lista_periodos, name="lista_periodos"),
    path("periodos/nuevo/", nuevo_periodo, name="nuevo_periodo"),
    
    path("paralelos/", lista_paralelos, name="lista_paralelos"),
    path("paralelos/nuevo/", nuevo_paralelo, name="nuevo_paralelo"),
    
    path(
        "inscripciones/",
        inscripciones_web,
        name="inscripciones",
    ),
    
    path(
        "docentes/<int:docente_id>/habilitar-acceso/",
        habilitar_docente_web,
        name="habilitar_docente",
    ),
    
    path(
        "aulas/<int:aula_id>/editar/",
        editar_aula_web,
        name="editar_aula",
    ),
    
        path(
        "docentes/<int:docente_id>/editar/",
        editar_docente_web,
        name="editar_docente",
    ),
        
    path(
        "necesidades/<int:necesidad_id>/editar/",
        editar_necesidad_web,
        name="editar_necesidad",
    ),
    
    path(
        "disponibilidades/<int:disponibilidad_id>/editar/",
        editar_disponibilidad_web,
        name="editar_disponibilidad",
    ),
    path(
        "franjas/<int:franja_id>/editar/",
        editar_franja_web,
        name="editar_franja",
    ),
    
    path(
        "paralelos/<int:paralelo_id>/",
        detalle_paralelo_web,
        name="detalle_paralelo",
    ),
    
    path(
        "paralelos/<int:paralelo_id>/franjas/nueva/",
        franja_paralelo_form_web,
        name="nueva_franja_paralelo",
    ),
    path(
        "paralelos/<int:paralelo_id>/franjas/<int:franja_id>/editar/",
        franja_paralelo_form_web,
        name="editar_franja_paralelo",
    ),
    path(
        "paralelos/<int:paralelo_id>/franjas/<int:franja_id>/estado/",
        estado_franja_paralelo_web,
        name="estado_franja_paralelo",
    ),
    
    path(
        "propuestas/<int:propuesta_id>/reintentar-pendientes/",
        reintentar_pendientes_web,
        name="reintentar_pendientes",
    ),
]