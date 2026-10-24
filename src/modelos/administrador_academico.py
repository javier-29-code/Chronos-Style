from modelos.docente import Docente
from modelos.administrador import Administrador


class AdministradorAcademico(Docente, Administrador):
    """Docente que también administra la planificación académica."""

    _DOMINIO_CORREO = "uleam.edu.ec"

    PERMISOS_PREDETERMINADOS = (
        Administrador.PERMISOS_PREDETERMINADOS
        | frozenset({
            "gestionar_catalogos",
            "gestionar_horarios",
            "consultar_horarios_generales",
        })
    )

    def __init__(
        self,
        nombre,
        correo,
        contrasena,
        facultad,
        *,
        titulo,
        area,
        horas_semanales_max,
        codigo_administrativo,
        permisos=None,
    ):
        super().__init__(
            nombre=nombre,
            correo=correo,
            contrasena=contrasena,
            titulo=titulo,
            area=area,
            horas_semanales_max=horas_semanales_max,
            codigo_administrativo=codigo_administrativo,
            permisos=permisos,
        )

        self._facultad = self._validar_texto(
            facultad,
            "La facultad",
        )

    # ---------- Propiedades ----------

    @property
    def facultad(self):
        return self._facultad

    # ---------- Perfil y horario ----------

    def mostrar_perfil(self):
        return (
            f"Administrador académico: {self.nombre}\n"
            f"Correo: {self.correo}\n"
            f"Código administrativo: {self.codigo_administrativo}\n"
            f"Facultad: {self.facultad}\n"
            f"Título: {self.titulo}\n"
            f"Área: {self.area}\n"
            f"Horas semanales máximas: {self.horas_semanales_max}"
        )

    def ver_horario(self):
        return (
            f"Horario general de {self.facultad}: "
            "pendiente de integrar con Horario."
        )

    def ver_horario_docente(self):
        """Permite consultar también su faceta de docente."""
        return super().ver_horario()