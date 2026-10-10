from datetime import date


class PeriodoAcademico:

    def __init__(self, codigo, nombre, fecha_inicio, fecha_fin):
        self._codigo = codigo
        self._nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

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
    def fecha_inicio(self):
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, nueva_fecha):
        if not isinstance(nueva_fecha, date):
            raise TypeError("La fecha de inicio debe ser una fecha válida.")

        if hasattr(self, "_fecha_fin") and nueva_fecha >= self._fecha_fin:
            raise ValueError(
                "La fecha de inicio debe ser anterior a la fecha de fin."
            )

        self._fecha_inicio = nueva_fecha

    @property
    def fecha_fin(self):
        return self._fecha_fin

    @fecha_fin.setter
    def fecha_fin(self, nueva_fecha):
        if not isinstance(nueva_fecha, date):
            raise TypeError("La fecha de fin debe ser una fecha válida.")

        if nueva_fecha <= self._fecha_inicio:
            raise ValueError(
                "La fecha de fin debe ser posterior a la fecha de inicio."
            )

        self._fecha_fin = nueva_fecha

    def mostrar_informacion(self):
        print(f"Código: {self.codigo}")
        print(f"Nombre: {self.nombre}")
        print(f"Fecha de inicio: {self.fecha_inicio}")
        print(f"Fecha de fin: {self.fecha_fin}")
