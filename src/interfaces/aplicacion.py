"""Controla el recorrido de pantallas: login -> ventana principal -> (cerrar sesión) -> login."""
from servicios.gestor_usuarios import crear_gestor_con_datos_ejemplo
from interfaces.ventana_login import VentanaLogin
from interfaces.ventana_principal import VentanaPrincipal


def iniciar_aplicacion():
    """Repite login y ventana principal hasta que el usuario cierre alguna con la X."""
    gestor = crear_gestor_con_datos_ejemplo()

    while True:
        # 1. Pantalla de login: mainloop() se queda aquí hasta que la ventana se cierre.
        login = VentanaLogin(gestor)
        login.mainloop()

        usuario = login.usuario
        if usuario is None:
            break  # cerró el login sin ingresar: termina el programa

        # 2. Ventana principal del usuario que ingresó.
        principal = VentanaPrincipal(usuario)
        principal.mainloop()
        usuario.cerrar_sesion()  # sea cual sea la forma de salir, la sesión se cierra

        # 3. Si salió con la X (no con "Cerrar sesión"), termina el programa.
        if not principal.cerro_sesion:
            break


if __name__ == "__main__":
    iniciar_aplicacion()