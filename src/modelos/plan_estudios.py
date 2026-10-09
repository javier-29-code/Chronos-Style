
class PlanEstudios:

    def __init__(self, version, vigencia):
        self._version = version
        self._vigencia = vigencia
        self._asignaturas = []

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, nueva_version):
        self._version = nueva_version

    @property
    def vigencia(self):
        return self._vigencia

    @vigencia.setter
    def vigencia(self, nueva_vigencia):
        self._vigencia = nueva_vigencia

    @property
    def asignaturas(self):
        return tuple(self._asignaturas)

    def agregar_asignatura(self, asignatura):
        if asignatura in self._asignaturas:
            print("La asignatura ya está registrada.")
            return

        self._asignaturas.append(asignatura)
        print(f"Asignatura '{asignatura}' agregada al plan.")

    def mostrar_asignaturas(self):
        print(f"Plan de estudios: {self.version}")

        if not self._asignaturas:
            print("No hay asignaturas registradas.")
            return

        for asignatura in self._asignaturas:
            print(f"- {asignatura}")