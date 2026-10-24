from modelos.usuario import Usuario


class Administrador(Usuario):
    """Usuario que dispone de permisos para administrar el sistema."""

    _DOMINIO_CORREO = "uleam.edu.ec"

    PERMISOS_VALIDOS = frozenset({
        "registrar_usuario",
        "cambiar_estado_usuario",
        "gestionar_catalogos",
        "gestionar_horarios",
        "consultar_horarios_generales",
    })

    PERMISOS_PREDETERMINADOS = frozenset({
        "registrar_usuario",
        "cambiar_estado_usuario",
    })

    def __init__(self,nombre,correo,contrasena,*,codigo_administrativo,permisos=None,):
        super().__init__(nombre, correo, contrasena)

        self._codigo_administrativo = self._validar_texto(
            codigo_administrativo,
            "El código administrativo",
        )

        if permisos is None:
            permisos = self.PERMISOS_PREDETERMINADOS

        self._permisos = self._validar_permisos(permisos)

    # ---------- Validaciones ----------

    def _validar_permisos(self, permisos):
        if not isinstance(permisos, (list, tuple, set, frozenset)):
            raise ValueError(
                "Los permisos deben proporcionarse como una colección."
            )

        permisos_validados = set()

        for permiso in permisos:
            if not isinstance(permiso, str):
                raise ValueError("Cada permiso debe ser texto.")

            if permiso not in self.PERMISOS_VALIDOS:
                raise ValueError(f"Permiso desconocido: {permiso}.")

            permisos_validados.add(permiso)

        return frozenset(permisos_validados)

    # ---------- Propiedades ----------

    @property
    def codigo_administrativo(self):
        return self._codigo_administrativo

    @property
    def permisos(self):
        # frozenset evita modificaciones desde fuera.
        return self._permisos

    # ---------- Autorización ----------

    def tiene_permiso(self, permiso):
        if not isinstance(permiso, str):
            raise ValueError("El permiso debe ser texto.")

        return permiso in self._permisos

    def exigir_permiso(self, permiso):
        """Impide continuar si el administrador no tiene el permiso."""
        if not self.tiene_permiso(permiso):
            raise PermissionError(
                f"El usuario {self.nombre} no tiene permiso "
                f"para realizar la operación: {permiso}."
            )

    # ---------- Perfil y horario ----------

    def mostrar_perfil(self):
        permisos = ", ".join(sorted(self.permisos)) or "Sin permisos"

        return (
            f"Administrador: {self.nombre}\n"
            f"Correo: {self.correo}\n"
            f"Código administrativo: {self.codigo_administrativo}\n"
            f"Permisos: {permisos}"
        )

    def ver_horario(self):
        return (
            "El administrador general no tiene un horario docente asignado."
        )