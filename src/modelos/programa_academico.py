class ProgramaAcademico:

    def __init__(self, id_programa, nombre, nivel):
        self._id_programa = id_programa
        self._nombre = nombre
        self._nivel = nivel

    @property
    def id_programa(self):
        return self._id_programa

    @id_programa.setter
    def id_programa(self, nuevo_id):
        self._id_programa = nuevo_id

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre):
        self._nombre = nuevo_nombre

    @property
    def nivel(self):
        return self._nivel

    @nivel.setter
    def nivel(self, nuevo_nivel):
        self._nivel = nuevo_nivel

    def gestionar_plan_estudios(self):
        print(
            f"El programa {self.nombre} está gestionando "
            f"su plan de estudios."
        )