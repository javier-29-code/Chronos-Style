from modelos.aula import Aula


class Laboratorio(Aula):
    """Laboratorio: un Aula con equipos. El tipo decide qué equipo básico necesita."""

    # Equipo mínimo según el tipo de laboratorio
    EQUIPO_BASICO = {
        "Laboratorio de computación": ["computadoras"],
        "Laboratorio de electrónica": ["osciloscopio", "multímetro", "fuente de poder"],
        "Laboratorio de redes": ["router", "switch", "cables de red"],
    }

    def __init__(self, id_aula, edificio, capacidad, tipo, equipamiento):
        super().__init__(id_aula, edificio, capacidad, tipo)
        # Un laboratorio solo puede ser de uno de los tres tipos de laboratorio
        if tipo not in Laboratorio.EQUIPO_BASICO:
            raise ValueError("El tipo debe ser un laboratorio válido.")
        self.equipamiento = equipamiento

    @property
    def equipamiento(self):
        return self._equipamiento

    @equipamiento.setter
    def equipamiento(self, nueva_lista):
        if not isinstance(nueva_lista, list):
            raise ValueError("El equipamiento debe ser una lista de nombres de equipos.")
        self._equipamiento = nueva_lista

    # True si tiene todo el equipo básico de su tipo
    def verificar_equipamiento(self):
        equipos = [equipo.lower() for equipo in self._equipamiento]
        for requerido in Laboratorio.EQUIPO_BASICO[self.tipo]:
            if requerido not in equipos:
                return False
        return True

    # Sobrescribe el método de Aula (polimorfismo)
    def mostrar_informacion(self):
        super().mostrar_informacion()
        print(f"Equipamiento: {', '.join(self._equipamiento)}")
        if self.verificar_equipamiento():
            print("Equipo básico: completo")
        else:
            print("Equipo básico: incompleto")