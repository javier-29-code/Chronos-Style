from modelos.aula import Aula


class LaboratorioRedes(Aula):
    def __init__(self, id_aula, edificio, capacidad, numero_switches):
        super().__init__(id_aula, edificio, capacidad, "Laboratorio de redes")
        self.numero_switches = numero_switches

    @property
    def numero_switches(self):
        return self._numero_switches

    @numero_switches.setter
    def numero_switches(self, nuevo_numero):
        if not isinstance(nuevo_numero, int) or nuevo_numero <= 0:
            raise ValueError("El número de switches debe ser un entero mayor que 0.")
        self._numero_switches = nuevo_numero

    def mostrar_informacion(self):
        super().mostrar_informacion()
        print(f"Número de switches: {self.numero_switches}")