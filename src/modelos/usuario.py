class Usuario:
    def __init__(self, nombre, correo, contrasena):
        self._nombre = nombre
        self._correo = correo
        self._contrasena = contrasena

    # Getter para nombre
    @property
    def nombre(self):
        return self._nombre

    # Setter para nombre
    @nombre.setter
    def nombre(self, nuevo_nombre):
        self._nombre = nuevo_nombre

    # Getter para correo
    @property
    def correo(self):
        return self._correo

    # Setter para correo
    @correo.setter
    def correo(self, nuevo_correo):
        self._correo = nuevo_correo

    # Método para cambiar la contraseña
    def cambiar_contrasena(self, nueva_contrasena):
        self._contrasena = nueva_contrasena
        
    def consultar_horario(self):
        print(f"{self.nombre} está consultando su horario.")