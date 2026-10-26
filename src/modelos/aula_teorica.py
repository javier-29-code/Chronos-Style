from modelos.aula import Aula


class AulaTeorica(Aula):
    """Aula física destinada a clases teóricas."""

    def __init__(
        self,
        id_aula,
        edificio,
        capacidad,
        tiene_proyector=False,
        tiene_pantalla_tactil=False,
    ):
        super().__init__(
            id_aula,
            edificio,
            capacidad,
            "Teórica",
        )

        self.tiene_proyector = tiene_proyector
        self.tiene_pantalla_tactil = tiene_pantalla_tactil

    @property
    def tiene_proyector(self):
        return self._tiene_proyector

    @tiene_proyector.setter
    def tiene_proyector(self, valor):
        if not isinstance(valor, bool):
            raise ValueError(
                "Indica con True o False si tiene proyector."
            )

        self._tiene_proyector = valor

    @property
    def tiene_pantalla_tactil(self):
        return self._tiene_pantalla_tactil

    @tiene_pantalla_tactil.setter
    def tiene_pantalla_tactil(self, valor):
        if not isinstance(valor, bool):
            raise ValueError(
                "Indica con True o False si tiene pantalla táctil."
            )

        self._tiene_pantalla_tactil = valor

    def mostrar_informacion(self):
        super().mostrar_informacion()

        print(
            "Proyector: "
            + ("Sí" if self.tiene_proyector else "No")
        )
        print(
            "Pantalla táctil: "
            + ("Sí" if self.tiene_pantalla_tactil else "No")
        )