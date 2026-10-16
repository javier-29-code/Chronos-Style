from modelos.aula import Aula

class LaboratorioElectronica(Aula):
    def __init__(self, id_aula, edificio, capacidad, numero_equipos):
        super().__init__(id_aula, edificio, capacidad, "Laboratorio de electrónica")
        self.numero_equipos = numero_equipos

    @property
    def numero_equipos(self):
        return self._numero_equipos

    @numero_equipos.setter
    def numero_equipos(self, nuevo_numero):
        if not isinstance(nuevo_numero, int) or nuevo_numero <= 0:
            raise ValueError("El número de equipos debe ser un entero mayor que 0.")
        self._numero_equipos = nuevo_numero

    def mostrar_informacion(self):
        super().mostrar_informacion()
        print(f"Equipos de medición: {self.numero_equipos}")