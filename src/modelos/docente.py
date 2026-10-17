from modelos.usuario import Usuario


class Docente(Usuario):
    """Usuario que dicta clases. Su correo debe ser institucional de docente."""

    _DOMINIO_CORREO = "uleam.edu.ec"

    def __init__(self, nombre, correo, contrasena, titulo, area, horas_semanales_max):
        super().__init__(nombre, correo, contrasena)
        self._titulo = self._validar_texto(titulo, "El título")
        self._area = self._validar_texto(area, "El área")
        self._horas_semanales_max = self._validar_horas(horas_semanales_max)

    # ---------- Validaciones ----------

    def _validar_horas(self, horas):
        if not isinstance(horas, int) or isinstance(horas, bool):
            raise ValueError("Las horas semanales deben ser un número entero.")
        if not 1 <= horas <= 40:
            raise ValueError("Las horas semanales deben estar entre 1 y 40.")
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
        self._horas_semanales_max = self._validar_horas(nuevas_horas)

    # ---------- Perfil ----------

    def mostrar_perfil(self):
        return (
            f"Docente: {self._nombre}\n"
            f"Correo: {self._correo}\n"
            f"Título: {self._titulo}\n"
            f"Área: {self._area}\n"
            f"Horas semanales máximas: {self._horas_semanales_max}"
        )