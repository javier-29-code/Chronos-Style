from modelos.aula import Aula


class AulaTeorica(Aula):
    def __init__(self, id_aula, edificio, capacidad, tiene_proyector):
        super().__init__(id_aula, edificio, capacidad, "Teórica")
        self.tiene_proyector = tiene_proyector

    @property
    def tiene_proyector(self):
        return self._tiene_proyector

    @tiene_proyector.setter
    def tiene_proyector(self, valor):
        self._tiene_proyector = valor

    def mostrar_informacion(self):
        super().mostrar_informacion()
        if self._tiene_proyector:
            print("Tiene proyector: Sí")
        else:
            print("Tiene proyector: No")