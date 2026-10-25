"""Consulta de los horarios registrados."""

from tkinter import ttk

from modelos.franja_horaria import FranjaHoraria


class PanelConsultaHorarios(ttk.Frame):
    def __init__(
        self,
        master,
        gestor_horarios,
        docente=None,
        estudiante=None,
    ):
        super().__init__(master, padding=20)

        if docente is not None and estudiante is not None:
            raise ValueError(
                "La consulta debe ser de docente o estudiante."
            )

        self._gestor_horarios = gestor_horarios
        self._docente = docente
        self._estudiante = estudiante

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._crear_interfaz()
        self.actualizar()

    def _crear_interfaz(self):
        ttk.Label(
            self,
            text=(
                "Mi horario"
                if (
                    self._docente is not None
                    or self._estudiante is not None
                )
                else "Horarios registrados"
            ),
            font=("Segoe UI", 17, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        herramientas = ttk.Frame(self)
        herramientas.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )

        ttk.Label(
            herramientas,
            text="Día:",
        ).pack(side="left")

        self._filtro_dia = ttk.Combobox(
            herramientas,
            state="readonly",
            values=["Todos", *FranjaHoraria.dias_validos],
            width=15,
        )
        self._filtro_dia.set("Todos")
        self._filtro_dia.pack(side="left", padx=10)
        self._filtro_dia.bind(
            "<<ComboboxSelected>>",
            self.actualizar,
        )

        ttk.Button(
            herramientas,
            text="Actualizar",
            command=self.actualizar,
        ).pack(side="right")

        contenedor = ttk.Frame(self)
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        columnas = (
            "materia",
            "paralelo",
            "docente",
            "aula",
            "dia",
            "inicio",
            "fin",
        )

        self._tabla = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )

        configuracion = (
            ("materia", "Asignatura", 230),
            ("paralelo", "Paralelo", 110),
            ("docente", "Docente", 170),
            ("aula", "Aula", 90),
            ("dia", "Día", 100),
            ("inicio", "Inicio", 75),
            ("fin", "Fin", 75),
        )

        for columna, titulo, ancho in configuracion:
            self._tabla.heading(columna, text=titulo)
            self._tabla.column(
                columna,
                width=ancho,
                minwidth=70,
                anchor="w",
            )

        self._tabla.grid(row=0, column=0, sticky="nsew")

        barra_vertical = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=self._tabla.yview,
        )
        barra_vertical.grid(row=0, column=1, sticky="ns")

        barra_horizontal = ttk.Scrollbar(
            contenedor,
            orient="horizontal",
            command=self._tabla.xview,
        )
        barra_horizontal.grid(row=1, column=0, sticky="ew")

        self._tabla.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set,
        )

        self._estado = ttk.Label(self)
        self._estado.grid(
            row=3,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

    def actualizar(self, event=None):
        """Recarga los datos respetando el filtro seleccionado."""
        for fila in self._tabla.get_children():
            self._tabla.delete(fila)

        horarios = self._gestor_horarios.listar()

        if self._docente is not None:
            horarios = [
                horario
                for horario in horarios
                if horario.docente is self._docente
            ]

        elif self._estudiante is not None:
            horarios = [
                horario
                for horario in horarios
                if (
                    horario.paralelo is not None
                    and horario.paralelo.contiene_estudiante(
                        self._estudiante
                    )
                )
            ]

        dia_seleccionado = self._filtro_dia.get()

        visibles = [
            horario
            for horario in horarios
            if (
                dia_seleccionado == "Todos"
                or horario.franja.dia == dia_seleccionado
            )
        ]

        orden_dias = {
            dia: indice
            for indice, dia in enumerate(FranjaHoraria.dias_validos)
        }

        visibles.sort(
            key=lambda horario: (
                orden_dias[horario.franja.dia],
                horario.franja.hora_inicio,
                horario.materia,
            )
        )

        for horario in visibles:
            self._tabla.insert(
                "",
                "end",
                values=(
                    horario.materia,
                    (
                        horario.paralelo.codigo
                        if horario.paralelo is not None
                        else "Sin paralelo"
                    ),
                    horario.docente.nombre,
                    horario.aula.id_aula,
                    horario.franja.dia,
                    f"{horario.franja.hora_inicio:02d}:00",
                    f"{horario.franja.hora_fin:02d}:00",
                ),
            )

        if not horarios:
            texto = "Todavía no hay horarios registrados."
        elif not visibles:
            texto = "No hay horarios para el día seleccionado."
        else:
            texto = (
                f"Mostrando {len(visibles)} de "
                f"{len(horarios)} horarios."
            )

        self._estado.configure(text=texto)