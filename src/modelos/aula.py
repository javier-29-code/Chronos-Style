class Aula:

    total_aulas = 0
    # Tipos de aula permitidos
    Tipos_validos = [
        "Teórica",
        "Laboratorio de computación",
        "Laboratorio de electrónica",
        "Laboratorio de redes",
        "Auditorio"
    ]

    def __init__(self, id_aula, edificio, capacidad, tipo):
        
        self.id_aula = id_aula
        self.edificio = edificio
        self.capacidad = capacidad
        self.tipo = tipo

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
        if not isinstance(nuevo_id, str) or nuevo_id.strip() == "":
            #raise detiene el programa y muestra el error
            raise ValueError("El ID del aula no puede estar vacía.")
        self._id_aula = nuevo_id

    @property
    def edificio(self):
        return self._edificio

    @edificio.setter
    def edificio(self, nuevo_edificio):
        if not isinstance(nuevo_edificio, str) or nuevo_edificio.strip() == "":
            raise ValueError("El edificio no puede estar vacío.")
        self._edificio = nuevo_edificio

    @property
    def capacidad(self):
        return self._capacidad
    
    # El setter permite validar antes de guardar el dato.
    @capacidad.setter
    def capacidad(self, nueva_capacidad):
        if not Aula.capacidad_valida(nueva_capacidad):
            raise ValueError("La capacidad debe ser un entero mayor que 0.")
        self._capacidad = nueva_capacidad

    @property
    def tipo(self):
        return self._tipo

    @tipo.setter
    def tipo(self, nuevo_tipo):
        if nuevo_tipo not in Aula.Tipos_validos:
            raise ValueError(f"Tipo de aula inválido. Debe ser uno de: {Aula.Tipos_validos}")
        self._tipo = nuevo_tipo

    # Metodo estatico que solo hace una comprobación.
    @staticmethod
    def capacidad_valida(capacidad):
        return isinstance(capacidad, int) and capacidad > 0

    @classmethod
    def mostrar_total_aulas(cls):
        print(f"Total de aulas creadas: {cls.total_aulas}")

    # Metodo de instancia que recibe un dato (la franja).
    def verificar_disponibilidad(self, franja):
        for franja_ocupada in self._franjas_ocupadas:
            #Revisa si chocan
            if franja.se_solapa_con(franja_ocupada):
                return False
        return True 

    def ocupar_franja(self, franja):
        if self.verificar_disponibilidad(franja):
            self._franjas_ocupadas.append(franja)
            print(f"Aula {self.id_aula} ocupada en: {franja}")
        else:
            print(f"Aula {self.id_aula} NO está disponible en: {franja}")

    def liberar_franja(self, franja):
       for franja_ocupada in self._franjas_ocupadas:
            if franja_ocupada.es_igual_a(franja):
                self._franjas_ocupadas.remove(franja_ocupada)
                print(f"Aula {self.id_aula} liberada en: {franja}")
                return
            print(f"La franja {franja} no estaba ocupada.")

    def mostrar_informacion(self):
        print(
            f"Aula {self.id_aula} - "
            f"Edificio {self.edificio} - "
            f"Capacidad: {self.capacidad} - "
            f"Tipo: {self.tipo}"
        )