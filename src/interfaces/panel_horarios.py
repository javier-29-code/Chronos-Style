"""Formulario de registro y validación de horarios."""

from tkinter import ttk, messagebox

from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario


class PanelHorarios(ttk.Frame):
    def __init__(self, master, gestor_catalogos, gestor_horarios):
        super().__init__(master, padding=20)

        self._catalogos = gestor_catalogos
        self._horarios = gestor_horarios

        self._asignaturas = []
        self._docentes = []
        self._aulas = []
        self._paralelos = []

        self._crear_interfaz()
        self.actualizar_catalogos()

    # ---------- Interfaz ----------

    def _crear_interfaz(self):
        self.columnconfigure(0, weight=1)

        ttk.Label(
            self,
            text="Registrar horario",
            font=("Segoe UI", 17, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        formulario = ttk.LabelFrame(
            self,
            text="Datos de la clase",
            padding=15,
        )
        formulario.grid(row=1, column=0, sticky="ew")
        formulario.columnconfigure(1, weight=1)

        self._asignatura = self._crear_selector(
            formulario, "Asignatura:", 0
        )
        self._docente = self._crear_selector(
            formulario, "Docente:", 1
        )
        self._aula = self._crear_selector(
            formulario, "Aula:", 2
        )
        self._dia = self._crear_selector(
            formulario, "Día:", 3
        )
        self._inicio = self._crear_selector(
            formulario, "Hora de inicio:", 4
        )
        self._fin = self._crear_selector(
            formulario, "Hora de fin:", 5
        )
        
        self._paralelo = self._crear_selector(
            formulario, "Paralelo:", 6
        )

        self._dia["values"] = FranjaHoraria.dias_validos
        self._inicio["values"] = [
            f"{hora:02d}:00" for hora in range(24)
        ]
        self._fin["values"] = [
            f"{hora:02d}:00" for hora in range(1, 25)
        ]

        acciones = ttk.Frame(self)
        acciones.grid(row=2, column=0, sticky="ew", pady=15)

        self._boton_registrar = ttk.Button(
            acciones,
            text="Registrar horario",
            command=self._registrar,
        )
        self._boton_registrar.pack(side="left")

        ttk.Button(
            acciones,
            text="Limpiar",
            command=self._limpiar,
        ).pack(side="left", padx=10)

        ttk.Button(
            acciones,
            text="Actualizar catálogos",
            command=self.actualizar_catalogos,
        ).pack(side="right")

        self._estado = ttk.Label(self, wraplength=600)
        self._estado.grid(row=3, column=0, sticky="w")

    def _crear_selector(self, contenedor, texto, fila):
        ttk.Label(
            contenedor,
            text=texto,
        ).grid(
            row=fila,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=6,
        )

        selector = ttk.Combobox(
            contenedor,
            state="readonly",
            width=45,
        )
        selector.grid(
            row=fila,
            column=1,
            sticky="ew",
            pady=6,
        )

        return selector

    # ---------- Catálogos ----------

    def actualizar_catalogos(self):
        self._asignaturas = list(
            self._catalogos.listar_asignaturas()
        )
        self._docentes = list(
            self._catalogos.listar_docentes()
        )
        self._aulas = list(
            self._catalogos.listar_aulas()
        )
        self._paralelos = list(
            self._catalogos.listar_paralelos()
        )

        opciones = (
            (
                self._asignatura,
                [
                    f"{a.codigo} — {a.nombre}"
                    for a in self._asignaturas
                ],
            ),
            (
                self._docente,
                [
                    f"{d.nombre} — {d.correo}"
                    for d in self._docentes
                ],
            ),
            (
                self._aula,
                [
                    f"{a.id_aula} — {a.edificio}"
                    for a in self._aulas
                ],
            ),
            (
                self._paralelo,
                [
                    f"{p.codigo} — {p}"
                    for p in self._paralelos
                ],
            ),
        )

        for selector, valores in opciones:
            selector.set("")
            selector["values"] = valores

        faltantes = []

        if not self._asignaturas:
            faltantes.append("asignaturas")
        if not self._docentes:
            faltantes.append("docentes")
        if not self._aulas:
            faltantes.append("aulas")
            
        if not self._paralelos:
            faltantes.append("paralelos")

        if faltantes:
            self._boton_registrar.state(["disabled"])
            self._estado.configure(
                text=f"Falta registrar: {', '.join(faltantes)}."
            )
        else:
            self._boton_registrar.state(["!disabled"])
            self._estado.configure(
                text="Selecciona los datos para registrar una clase."
            )

    @staticmethod
    def _seleccionar(selector, objetos, campo):
        indice = selector.current()

        if indice < 0 or indice >= len(objetos):
            raise ValueError(f"Selecciona {campo}.")

        return objetos[indice]

    # ---------- Registro ----------

    def _registrar(self):
        try:
            asignatura = self._seleccionar(
                self._asignatura,
                self._asignaturas,
                "una asignatura",
            )
            docente = self._seleccionar(
                self._docente,
                self._docentes,
                "un docente",
            )
            aula = self._seleccionar(
                self._aula,
                self._aulas,
                "un aula",
            )
            paralelo = self._seleccionar(
                self._paralelo,
                self._paralelos,
                "un paralelo",
            )

            if self._dia.current() < 0:
                raise ValueError("Selecciona un día.")

            if self._inicio.current() < 0 or self._fin.current() < 0:
                raise ValueError("Selecciona las horas de inicio y fin.")

            inicio = int(self._inicio.get().split(":")[0])
            fin = int(self._fin.get().split(":")[0])

            franja = FranjaHoraria(
                self._dia.get(),
                inicio,
                fin,
            )

            horario = Horario(
                materia=asignatura.nombre,
                docente=docente,
                aula=aula,
                franja=franja,
                paralelo=paralelo,
                asignatura=asignatura,
            )

            conflictos = self._horarios.agregar(horario)

        except ValueError as error:
            messagebox.showerror(
                "Revisar datos",
                str(error),
                parent=self,
            )
            return

        if conflictos:
            detalles = []

            for conflicto in conflictos:
                detalles.append(
                    f"{conflicto.motivo}\n"
                    f"• {self._resumir(conflicto.horario_1)}\n"
                    f"• {self._resumir(conflicto.horario_2)}"
                )

            self._estado.configure(
                text="El horario no se registró porque existen conflictos."
            )

            messagebox.showwarning(
                "Conflictos encontrados",
                "\n\n".join(detalles),
                parent=self,
            )
            return

        self._estado.configure(
            text=(
                f"Registrado: {asignatura.nombre} | {franja} | "
                f"Aula {aula.id_aula}. "
                f"Total de horarios: {self._horarios.cantidad()}."
            )
        )

        messagebox.showinfo(
            "Registro correcto",
            "El horario se registró sin conflictos.",
            parent=self,
        )

        self.event_generate("<<HorariosActualizados>>", when="tail")

    @staticmethod
    def _resumir(horario):
        paralelo = (
            horario.paralelo.codigo
            if horario.paralelo is not None
            else "Sin paralelo"
        )

        return (
            f"{horario.materia} | {horario.franja} | "
            f"{horario.docente.nombre} | "
            f"Aula {horario.aula.id_aula} | "
            f"Paralelo {paralelo}"
        )

    def _limpiar(self):
        """Vacía los campos del formulario."""
        for selector in (
            self._asignatura,
            self._docente,
            self._aula,
            self._paralelo,
            self._dia,
            self._inicio,
            self._fin,
        ):
            selector.set("")

        self._estado.configure(text="Formulario limpiado.")