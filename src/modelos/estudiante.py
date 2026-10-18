from modelos.usuario import Usuario


class Estudiante(Usuario):
    """Usuario que cursa una carrera. Su correo debe ser institucional de estudiante."""

    _DOMINIO_CORREO = "live.uleam.edu.ec"

    def __init__(self, nombre, correo, contrasena, carrera, semestre):
        super().__init__(nombre, correo, contrasena)
        self._carrera = self._validar_carrera(carrera)
        self._semestre = self._validar_semestre(semestre)

    # ---------- Validaciones ----------

    def _validar_carrera(self, carrera):
        if not isinstance(carrera, str) or not carrera.strip():
            raise ValueError("La carrera no puede estar vacía.")
        return carrera.strip()

    def _validar_semestre(self, semestre):
        if not isinstance(semestre, int) or isinstance(semestre, bool):
            raise ValueError("El semestre debe ser un número entero.")
        if not 1 <= semestre <= 10:
            raise ValueError("El semestre debe estar entre 1 y 10.")
        return semestre

    # ---------- Propiedades ----------

    @property
    def carrera(self):
        return self._carrera

    @carrera.setter
    def carrera(self, nueva_carrera):
        self._carrera = self._validar_carrera(nueva_carrera)

    @property
    def semestre(self):
        return self._semestre

    @semestre.setter
    def semestre(self, nuevo_semestre):
        self._semestre = self._validar_semestre(nuevo_semestre)

    # ---------- Perfil ----------

    def mostrar_perfil(self):
        return (
            f"Estudiante: {self._nombre}\n"
            f"Correo: {self._correo}\n"
            f"Carrera: {self._carrera}\n"
            f"Semestre: {self._semestre}"
        )
        
    #--------- Horario ----------
    def ver_horario(self):
        return f"Horario del estudiante {self._nombre}: pendiente de integrar con Horario."