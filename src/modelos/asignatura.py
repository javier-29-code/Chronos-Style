
class Asignatura:

    def __init__(self, codigo, nombre, creditos, horas_semanales):
        self._codigo = codigo
        self._nombre = nombre
        self._creditos = creditos
        self._horas_semanales = horas_semanales
        self._requisitos = []

    @property
    def codigo(self):
        return self._codigo

    @codigo.setter
    def codigo(self, nuevo_codigo):
        self._codigo = nuevo_codigo

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre):
        self._nombre = nuevo_nombre

    @property
    def creditos(self):
        return self._creditos

    @creditos.setter
    def creditos(self, nuevos_creditos):
        self._creditos = nuevos_creditos

    @property
    def horas_semanales(self):
        return self._horas_semanales

    @horas_semanales.setter
    def horas_semanales(self, nuevas_horas):
        self._horas_semanales = nuevas_horas

    @property
    def requisitos(self):
        return tuple(self._requisitos)

    def definir_requisitos(self, asignaturas):
        self._requisitos = list(asignaturas)

    def mostrar_informacion(self):
        print(f"Código: {self.codigo}")
        print(f"Nombre: {self.nombre}")
        print(f"Créditos: {self.creditos}")
        print(f"Horas semanales: {self.horas_semanales}")
        print("Prerrequisitos:")

        if not self._requisitos:
            print("Ninguno")
        else:
            for asignatura in self._requisitos:
                print(f"- {asignatura.nombre}")