"""Controla el recorrido login -> ventana principal -> login."""

from modelos.docente import Docente

from servicios.gestor_usuarios import crear_gestor_con_datos_ejemplo
from servicios.gestor_horarios import GestorHorarios
from servicios.datos_ejemplo import crear_catalogos_con_datos_ejemplo

from interfaces.ventana_login import VentanaLogin
from interfaces.ventana_principal import VentanaPrincipal

from modelos.estudiante import Estudiante

def iniciar_aplicacion():
    # Los servicios se crean una sola vez, antes del ciclo de sesiones.
    gestor_usuarios = crear_gestor_con_datos_ejemplo()

    docentes = [
        usuario
        for usuario in gestor_usuarios.listar()
        if isinstance(usuario, Docente)
    ]

    estudiantes = [
        usuario
        for usuario in gestor_usuarios.listar()
        if isinstance(usuario, Estudiante)
    ]

    gestor_catalogos = crear_catalogos_con_datos_ejemplo(
        docentes=docentes,
        estudiantes=estudiantes,
    )
    
    gestor_horarios = GestorHorarios()

    while True:
        login = VentanaLogin(gestor_usuarios)
        login.mainloop()

        usuario = login.usuario

        if usuario is None:
            break

        principal = VentanaPrincipal(
            usuario=usuario,
            gestor_catalogos=gestor_catalogos,
            gestor_horarios=gestor_horarios,
        )
        principal.mainloop()

        usuario.cerrar_sesion()

        if not principal.cerro_sesion:
            break