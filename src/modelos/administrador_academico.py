from modelos.usuario import Usuario


class AdministradorAcademico(Usuario):
    """Usuario que administra la parte académica (horarios, aulas, materias)."""

    _DOMINIO_CORREO = "uleam.edu.ec"

    def __init__(self, nombre, correo, contrasena, facultad):
        super().__init__(nombre, correo, contrasena)
        self._facultad = self._validar_texto(facultad, "La facultad")

    @property
    def facultad(self):
        return self._facultad

    def mostrar_perfil(self):
        return (
            f"Administrador académico: {self._nombre}\n"
            f"Correo: {self._correo}\n"
            f"Facultad: {self._facultad}"
        )
    def ver_horario(self):
        return f"Horario general de {self._facultad}: pendiente de integrar con Horario."