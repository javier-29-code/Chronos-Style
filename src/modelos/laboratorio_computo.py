from modelos.aula import Aula

class LaboratorioComputo(Aula):

    def __init__(self, id_aula, edificio, capacidad, numero_computadoras):
        self.numero_computadoras = numero_computadoras
        super().__init__(id_aula, edificio, capacidad, "Laboratorio de computación")

        
    @property
    def numero_computadoras(self):
        return self._numero_computadoras

    @numero_computadoras.setter
    def numero_computadoras(self, nuevo_numero):
        if not isinstance(nuevo_numero, int) or nuevo_numero <= 0:
            raise ValueError("El número de computadoras debe ser un entero mayor que 0.")
        self._numero_computadoras = nuevo_numero

    def mostrar_informacion(self):
        super().mostrar_informacion()

        print(
            f"Computadoras: {self.numero_computadoras}"
        )

        if self.numero_computadoras >= self.capacidad:
            print("Equipos: suficientes para todos los puestos")
        else:
            print("Equipos: insuficientes para todos los puestos")