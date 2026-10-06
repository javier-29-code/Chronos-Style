from modelos.usuario import Usuario


class AdministradorAcademico(Usuario):

    def __init__(self, nombre, correo, contrasena, codigo_empleado):
        super().__init__(nombre, correo, contrasena)
        self._codigo_empleado = codigo_empleado

    @property
    def codigo_empleado(self):
        return self._codigo_empleado

    @codigo_empleado.setter
    def codigo_empleado(self, nuevo_codigo):
        self._codigo_empleado = nuevo_codigo

    def gestionar_horarios(self):
        print(f"{self.nombre} está gestionando los horarios académicos.")