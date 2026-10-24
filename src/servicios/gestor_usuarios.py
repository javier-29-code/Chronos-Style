from modelos.administrador_academico import AdministradorAcademico
from modelos.docente import Docente
from modelos.estudiante import Estudiante


class GestorUsuarios:
    """Guarda los usuarios registrados y se encarga de autenticarlos."""

    def __init__(self):
        self._usuarios = {}  # clave: correo, valor: Usuario

    def registrar(self, usuario):
        if usuario.correo in self._usuarios:
            raise ValueError("Ya existe un usuario con ese correo.")

        self._usuarios[usuario.correo] = usuario

    def autenticar(self, correo, contrasena):
        """Devuelve el usuario con la sesión iniciada, o lanza ValueError."""
        usuario = self._usuarios.get(correo.strip().lower())

        # Mismo mensaje para correo y contraseña incorrectos.
        if usuario is None or not usuario.verificar_contrasena(contrasena):
            raise ValueError("Correo o contraseña incorrectos.")

        usuario.iniciar_sesion(contrasena)
        return usuario
    def listar(self):
        """Devuelve una copia de la colección de usuarios."""
        return list(self._usuarios.values())


def crear_gestor_con_datos_ejemplo():
    """Gestor con cuentas de ejemplo para probar la interfaz."""
    gestor = GestorUsuarios()

    # Administrador académico: también es Docente y Administrador.
    administrador_academico = AdministradorAcademico(
        nombre="Javier",
        correo="javier@uleam.edu.ec",
        contrasena="clave1234",
        facultad="Facultad de Ciencias Informáticas",
        titulo="Ingeniero en Tecnologías de la Información",
        area="Tics",
        horas_semanales_max=20,
        codigo_administrativo="ADM001",
    )
    gestor.registrar(administrador_academico)

    docente = Docente(
        nombre="Carlos",
        correo="carlos.perez@uleam.edu.ec",
        contrasena="clave1234",
        titulo="Ingeniero en Tecnologías de la Información",
        area="Programación",
        horas_semanales_max=20,
    )
    gestor.registrar(docente)

    estudiante = Estudiante(
        "Ana",
        "e1312345678@live.uleam.edu.ec",
        "clave1234",
        "Tecnologías de la Información",
        3,
    )
    gestor.registrar(estudiante)

    return gestor