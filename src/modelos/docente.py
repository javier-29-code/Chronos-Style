from modelos.usuario import Usuario


class Docente(Usuario):

    def __init__(self, nombre, correo, contrasena, codigo_docente, especialidad):
        super().__init__(nombre, correo, contrasena)
        self._codigo_docente = codigo_docente
        self._especialidad = especialidad

    @property
    def codigo_docente(self):
        return self._codigo_docente

    @codigo_docente.setter
    def codigo_docente(self, nuevo_codigo):
        self._codigo_docente = nuevo_codigo

    @property
    def especialidad(self):
        return self._especialidad

    @especialidad.setter
    def especialidad(self, nueva_especialidad):
        self._especialidad = nueva_especialidad

    def consultar_horario(self):
        print(f"{self.nombre} está consultando su horario.")