from modelos.usuario import Usuario


class Docente(Usuario):

    def __init__(self, nombre, correo, contrasena, codigo_docente, titulo):
        super().__init__(nombre, correo, contrasena)
        self._codigo_docente = codigo_docente
        self._titulo= titulo

    @property
    def codigo_docente(self):
        return self._codigo_docente

    @codigo_docente.setter
    def codigo_docente(self, nuevo_codigo):
        self._codigo_docente = nuevo_codigo

    @property
    def titulo(self):
        return self._titulo

    @titulo.setter
    def titulo(self, titulo):
        self._titulo = titulo
