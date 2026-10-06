from modelos.usuario import Usuario


class Estudiante(Usuario):

    def __init__(self,nombre, correo, contrasena, codigo_estudiante, carrera, semestre):
        super().__init__(nombre, correo, contrasena)

        self._codigo_estudiante = codigo_estudiante
        self._carrera = carrera
        self._semestre = semestre

    @property
    def codigo_estudiante(self):
        return self._codigo_estudiante

    @codigo_estudiante.setter
    def codigo_estudiante(self, nuevo_codigo):
        self._codigo_estudiante = nuevo_codigo

    @property
    def carrera(self):
        return self._carrera

    @carrera.setter
    def carrera(self, nueva_carrera):
        self._carrera = nueva_carrera

    @property
    def semestre(self):
        return self._semestre

    @semestre.setter
    def semestre(self, nuevo_semestre):
        self._semestre = nuevo_semestre

    def consultar_informacion_academica(self):
        print(
            f"{self.nombre} - "
            f"{self.carrera} - "
            f"Semestre {self.semestre}"
        )