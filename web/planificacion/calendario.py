from math import ceil, floor


class CalendarioSemanal:
    DIAS = (
        (1, "Lunes"),
        (2, "Martes"),
        (3, "Miércoles"),
        (4, "Jueves"),
        (5, "Viernes"),
        (6, "Sábado"),
        (7, "Domingo"),
    )
    PIXELES_POR_MINUTO = 1.4

    @staticmethod
    def _minutos(hora):
        return (
            hora.hour * 60
            + hora.minute
            + hora.second / 60
            + hora.microsecond / 60_000_000
        )

    @staticmethod
    def _numero(valor):
        # Evita comas decimales dentro de los estilos CSS.
        return f"{valor:.3f}"

    def construir(self, horarios):
        horarios = list(horarios)

        inicio = 7 * 60
        fin = 19 * 60

        if horarios:
            inicio = min(
                inicio,
                floor(
                    min(self._minutos(h.hora_inicio) for h in horarios) / 60
                ) * 60,
            )
            fin = max(
                fin,
                ceil(
                    max(self._minutos(h.hora_fin) for h in horarios) / 60
                ) * 60,
            )

        dias = []

        for numero, nombre in self.DIAS:
            registros = sorted(
                (h for h in horarios if h.dia == numero),
                key=lambda h: (h.hora_inicio, h.hora_fin, h.pk or 0),
            )

            bloques = []
            grupo = []
            fin_grupo = -1

            for horario in registros:
                comienzo = self._minutos(horario.hora_inicio)
                termino = self._minutos(horario.hora_fin)

                if grupo and comienzo >= fin_grupo:
                    bloques.extend(self._colocar(grupo, inicio))
                    grupo = []
                    fin_grupo = -1

                grupo.append(horario)
                fin_grupo = max(fin_grupo, termino)

            if grupo:
                bloques.extend(self._colocar(grupo, inicio))

            dias.append({
                "numero": numero,
                "nombre": nombre,
                "bloques": bloques,
            })

        marcas = [
            {
                "texto": f"{minuto // 60:02d}:00",
                "arriba": self._numero(
                    (minuto - inicio) * self.PIXELES_POR_MINUTO
                ),
            }
            for minuto in range(inicio, fin, 60)
        ]

        return {
            "dias": dias,
            "marcas": marcas,
            "altura": self._numero(
                (fin - inicio) * self.PIXELES_POR_MINUTO
            ),
        }

    def _colocar(self, horarios, inicio_calendario):
        finales = []
        posiciones = []

        for horario in horarios:
            inicio = self._minutos(horario.hora_inicio)
            fin = self._minutos(horario.hora_fin)

            columna = next(
                (
                    indice
                    for indice, final in enumerate(finales)
                    if final <= inicio
                ),
                len(finales),
            )

            if columna == len(finales):
                finales.append(fin)
            else:
                finales[columna] = fin

            posiciones.append((horario, inicio, fin, columna))

        ancho = 100 / len(finales)

        return [
            {
                "horario": horario,
                "arriba": self._numero(
                    (inicio - inicio_calendario)
                    * self.PIXELES_POR_MINUTO
                ),
                "alto": self._numero(
                    (fin - inicio) * self.PIXELES_POR_MINUTO
                ),
                "izquierda": self._numero(columna * ancho),
                "ancho": self._numero(ancho),
                "color": horario.asignatura_id % 5,
            }
            for horario, inicio, fin, columna in posiciones
        ]