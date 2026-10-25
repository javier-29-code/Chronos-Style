"""Consulta de los horarios registrados."""

from tkinter import ttk

from modelos.franja_horaria import FranjaHoraria
from tkinter import ttk, messagebox

from interfaces.dialogo_editar_horario import DialogoEditarHorario


class PanelConsultaHorarios(ttk.Frame):
    def __init__(
        self,
        master,
        gestor_horarios,
        docente=None,
        estudiante=None,
        usuario=None,
        gestor_catalogos = None,
    ):
        super().__init__(master, padding=20)

        if docente is not None and estudiante is not None:
            raise ValueError(
                "La consulta debe ser de docente o estudiante."
            )

        self._gestor_horarios = gestor_horarios
        self._docente = docente
        self._estudiante = estudiante
        self._usuario = usuario
        self._horarios_por_fila = {}
        
        self._gestor_catalogos = gestor_catalogos

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
        
        if self._puede_eliminar():
            ttk.Button(
                herramientas,
                text="Eliminar seleccionado",
                command=self._eliminar_seleccionado,
            ).pack(side="right", padx=10)

        if (
            self._puede_eliminar()
            and self._gestor_catalogos is not None
        ):
            ttk.Button(
                herramientas,
                text="Editar seleccionado",
                command=self._editar_seleccionado,
            ).pack(side="right", padx=5)
            
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

        # Limpia las referencias de las filas anteriores.
        self._horarios_por_fila.clear()

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
            # Guarda el identificador que devuelve Treeview.
            fila = self._tabla.insert(
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

            # Relaciona esta fila con el objeto Horario original.
            self._horarios_por_fila[fila] = horario

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
        
    def _puede_eliminar(self):
        comprobar_permiso = getattr(
            self._usuario,
            "tiene_permiso",
            None,
        )

        return (
            callable(comprobar_permiso)
            and comprobar_permiso("gestionar_horarios")
        )

    def _eliminar_seleccionado(self):
        # Se comprueba también al ejecutar la acción.
        if not self._puede_eliminar():
            messagebox.showerror(
                "Acceso denegado",
                "No tienes permiso para eliminar horarios.",
                parent=self,
            )
            return

        seleccion = self._tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un horario",
                "Selecciona una fila de la tabla.",
                parent=self,
            )
            return

        horario = self._horarios_por_fila.get(seleccion[0])

        if horario is None:
            self.actualizar()
            return

        confirmar = messagebox.askyesno(
            "Eliminar horario",
            (
                "¿Deseas eliminar esta clase?\n\n"
                f"Asignatura: {horario.materia}\n"
                f"Docente: {horario.docente.nombre}\n"
                f"Aula: {horario.aula.id_aula}\n"
                f"Franja: {horario.franja}"
            ),
            parent=self,
        )

        if not confirmar:
            return

        try:
            self._gestor_horarios.eliminar(horario)
        except ValueError as error:
            messagebox.showerror(
                "No se pudo eliminar",
                str(error),
                parent=self,
            )
            self.actualizar()
            return

        self.actualizar()

        self._estado.configure(
            text="Horario eliminado correctamente."
        )

        self.event_generate(
            "<<HorariosActualizados>>",
            when="tail",
        )
        
    def _editar_seleccionado(self):
        if not self._puede_eliminar():
            messagebox.showerror(
                "Acceso denegado",
                "No tienes permiso para editar horarios.",
                parent=self,
            )
            return

        if self._gestor_catalogos is None:
            return

        seleccion = self._tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Selecciona un horario",
                "Selecciona una fila de la tabla.",
                parent=self,
            )
            return

        horario = self._horarios_por_fila.get(seleccion[0])

        if horario is None:
            self.actualizar()
            return

        dialogo = DialogoEditarHorario(
            master=self,
            horario=horario,
            gestor_catalogos=self._gestor_catalogos,
            gestor_horarios=self._gestor_horarios,
            usuario=self._usuario,
            al_guardar=self._despues_de_editar,
        )

        self.wait_window(dialogo)

    def _despues_de_editar(self):
        self.actualizar()

        self._estado.configure(
            text="Horario actualizado correctamente."
        )

        self.event_generate(
            "<<HorariosActualizados>>",
            when="tail",
        )