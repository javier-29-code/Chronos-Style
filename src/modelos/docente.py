from modelos.usuario import Usuario


class Docente(Usuario):
    """Usuario que dicta clases y utiliza correo institucional."""

    _DOMINIO_CORREO = "uleam.edu.ec"

    def __init__(
        self,
        nombre,
        correo,
        contrasena,
        titulo,
        area,
        horas_semanales_max,
        **kwargs,
    ):
        # En un Docente normal continúa hacia Usuario.
        # En AdministradorAcademico continúa hacia Administrador.
        super().__init__(
            nombre=nombre,
            correo=correo,
            contrasena=contrasena,
            **kwargs,
        )

        self._titulo = self._validar_texto(titulo, "El título")
        self._area = self._validar_texto(area, "El área")
        self._horas_semanales_max = self._validar_horas(
            horas_semanales_max
        )

    # ---------- Validaciones ----------

    def _validar_horas(self, horas):
        if not isinstance(horas, int) or isinstance(horas, bool):
            raise ValueError(
                "Las horas semanales deben ser un número entero."
            )

        if not 1 <= horas <= 40:
            raise ValueError(
                "Las horas semanales deben estar entre 1 y 40."
            )

        return horas

    # ---------- Propiedades ----------

    @property
    def titulo(self):
        return self._titulo

    @property
    def area(self):
        return self._area

    @property
    def horas_semanales_max(self):
        return self._horas_semanales_max

    @horas_semanales_max.setter
    def horas_semanales_max(self, nuevas_horas):
        self._horas_semanales_max = self._validar_horas(
            nuevas_horas
        )

    # ---------- Perfil y horario ----------

    def mostrar_perfil(self):
        return (
            f"Docente: {self.nombre}\n"
            f"Correo: {self.correo}\n"
            f"Título: {self.titulo}\n"
            f"Área: {self.area}\n"
            f"Horas semanales máximas: {self.horas_semanales_max}"
        )

    def ver_horario(self):
        return (
            f"Horario de clases del docente {self.nombre}: "
            "pendiente de integrar con Horario."
        )