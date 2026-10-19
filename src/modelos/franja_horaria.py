class FranjaHoraria:

    # Atributo de clase con los días permitidos
    dias_validos = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

    def __init__(self, dia, hora_inicio, hora_fin):
        self.dia = dia
        # Se comprueba que las horas sean correctas antes de guardarlas
        if not FranjaHoraria.horas_validas(hora_inicio, hora_fin):
            raise ValueError("Las horas deben ser números enteros entre 0 y 24, "
                             "y la hora de inicio debe ser menor que la de fin.")
        self._hora_inicio = hora_inicio
        self._hora_fin = hora_fin

    @property
    def dia(self):
        return self._dia

    @dia.setter
    def dia(self, nuevo_dia):
        if nuevo_dia not in FranjaHoraria.dias_validos:
            raise ValueError(f"Día inválido. Debe ser uno de: {FranjaHoraria.dias_validos}")
        self._dia = nuevo_dia

    @property
    def hora_inicio(self):
        return self._hora_inicio

    @hora_inicio.setter
    def hora_inicio(self, nueva_hora):
        if not FranjaHoraria.horas_validas(nueva_hora, self._hora_fin):
            raise ValueError("Hora de inicio inválida.")
        self._hora_inicio = nueva_hora

    @property
    def hora_fin(self):
        return self._hora_fin

    @hora_fin.setter
    def hora_fin(self, nueva_hora):
        if not FranjaHoraria.horas_validas(self._hora_inicio, nueva_hora):
            raise ValueError("Hora de fin inválida.")
        self._hora_fin = nueva_hora

    # Metodo estático igual que capacidad_valida en Aula
    # solo comprueba y devuelve True o False
    @staticmethod
    def horas_validas(hora_inicio, hora_fin):
        if not isinstance(hora_inicio, int) or not isinstance(hora_fin, int):
            return False
        if hora_inicio < 0 or hora_fin > 24:
            return False
        return hora_inicio < hora_fin

    # Es el método seSolapaCon
    def se_solapa_con(self, otra_franja):
        # Si son días distintos, no se pisan
        if self.dia != otra_franja.dia:
            return False

        # Se pisan si cada una empieza antes de que termine la otra
        if self.hora_inicio < otra_franja.hora_fin and otra_franja.hora_inicio < self.hora_fin:
            return True
        return False

    # Dice si dos franjas son exactamente la misma
    def es_igual_a(self, otra_franja):
        return (
            self.dia == otra_franja.dia
            and self.hora_inicio == otra_franja.hora_inicio
            and self.hora_fin == otra_franja.hora_fin
        )

    # Define el texto que aparece (franja)
    def __str__(self):
        return f"{self.dia} {self.hora_inicio}:00-{self.hora_fin}:00"
    
    # Cambia inicio y fin a la vez, validando el par completo
    def cambiar_horas(self, nuevo_inicio, nuevo_fin):
        if not FranjaHoraria.horas_validas(nuevo_inicio, nuevo_fin):
            raise ValueError("Horas inválidas.")
        self._hora_inicio = nuevo_inicio
        self._hora_fin = nuevo_fin