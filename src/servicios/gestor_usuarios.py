
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
        # Mismo mensaje para correo y contraseña incorrectos, a propósito.
        if usuario is None or not usuario.verificar_contrasena(contrasena):
            raise ValueError("Correo o contraseña incorrectos.")
        usuario.iniciar_sesion(contrasena)
        return usuario
 
def crear_gestor_con_datos_ejemplo():
    """Gestor con un usuario de cada tipo, para probar la interfaz."""
    gestor = GestorUsuarios()
    gestor.registrar(AdministradorAcademico(
        "Javier", "javier@uleam.edu.ec", "clave1234",
        "Facultad de Ciencias Informáticas"))
    gestor.registrar(Docente(
        "Carlos", "carlos.perez@uleam.edu.ec", "clave1234",
        "Ingeniero en Tecnologías de la Información", "Programación", 20))
    gestor.registrar(Estudiante(
        "Ana", "e1312345678@live.uleam.edu.ec", "clave1234",
        "Tecnologías de la Información", 3))
    return gestor