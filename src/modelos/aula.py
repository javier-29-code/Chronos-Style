class Aula:

    total_aulas = 0

    def __init__(self, id_aula, edificio, capacidad, tipo):
        
        self._id_aula = id_aula
        self._edificio = edificio
        self._capacidad = capacidad
        self._tipo = tipo

        # Lista que guarda las franjas en las que el aula ya está ocupada.
        # Al inicio está vacía (el aula está libre).
        self._franjas_ocupadas = []

        # Cada vez que se crea un aula, aumenta el contador de clase.
        Aula.total_aulas += 1

    @property
    def id_aula(self):
        return self._id_aula

    @id_aula.setter
    def id_aula(self, nuevo_id):
        self._id_aula = nuevo_id

    @property
    def edificio(self):
        return self._edificio

    @edificio.setter
    def edificio(self, nuevo_edificio):
        self._edificio = nuevo_edificio

    @property
    def capacidad(self):
        return self._capacidad

    @capacidad.setter
    def capacidad(self, nueva_capacidad):
        # El setter permite validar antes de guardar el dato.
        if Aula.capacidad_valida(nueva_capacidad):
            self._capacidad = nueva_capacidad
        else:
            print("La capacidad debe ser mayor que 0.")

    @property
    def tipo(self):
        return self._tipo

    @tipo.setter
    def tipo(self, nuevo_tipo):
        self._tipo = nuevo_tipo

    # MÉTODO ESTÁTICO: no usa self; solo hace una comprobación.
    @staticmethod
    def capacidad_valida(capacidad):
        return capacidad > 0

    # MÉTODO DE CLASE:
    @classmethod
    def mostrar_total_aulas(cls):
        print(f"Total de aulas creadas: {cls.total_aulas}")

    # MÉTODO DE INSTANCIA que recibe un dato (la franja).
    def verificar_disponibilidad(self, franja):
        # Devuelve True si la franja NO está en la lista de ocupadas.
        return franja not in self._franjas_ocupadas

    def ocupar_franja(self, franja):
        if self.verificar_disponibilidad(franja):
            self._franjas_ocupadas.append(franja)
            print(f"Aula {self.id_aula} ocupada en: {franja}")
        else:
            print(f"Aula {self.id_aula} NO está disponible en: {franja}")

    def mostrar_informacion(self):
        print(
            f"Aula {self.id_aula} - "
            f"Edificio {self.edificio} - "
            f"Capacidad: {self.capacidad} - "
            f"Tipo: {self.tipo}"
        )