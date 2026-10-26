"""Formulario para modificar un horario registrado."""

import tkinter as tk
from tkinter import ttk, messagebox

from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario


class DialogoEditarHorario(tk.Toplevel):
    def __init__(
        self,
        master,
        horario,
        gestor_catalogos,
        gestor_horarios,
        usuario,
        al_guardar,
    ):
        super().__init__(master)

        self._original = horario
        self._catalogos = gestor_catalogos
        self._gestor = gestor_horarios
        self._usuario = usuario
        self._al_guardar = al_guardar

        self.title("Editar horario")
        self.transient(master.winfo_toplevel())
        self.resizable(False, False)

        self._crear_interfaz()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Mantiene la interacción en este formulario hasta cerrarlo.
        self.grab_set()

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=20)
        contenedor.pack(fill="both", expand=True)
        contenedor.columnconfigure(1, weight=1)

        self._asignaturas = self._catalogos.listar_asignaturas()
        self._docentes = self._catalogos.listar_docentes()
        self._aulas = self._catalogos.listar_aulas()
        self._paralelos = self._catalogos.listar_paralelos()

        self._asignatura = self._selector(
            contenedor,
            "Asignatura:",
            0,
            [
                f"{a.codigo} — {a.nombre}"
                for a in self._asignaturas
            ],
        )
        self._docente = self._selector(
            contenedor,
            "Docente:",
            1,
            [
                f"{d.nombre} — {d.correo}"
                for d in self._docentes
            ],
        )
        self._aula = self._selector(
            contenedor,
            "Aula:",
            2,
            [
                f"{a.id_aula} — {a.edificio}"
                for a in self._aulas
            ],
        )
        self._paralelo = self._selector(
            contenedor,
            "Paralelo:",
            3,
            [
                f"{p.codigo} — {p}"
                for p in self._paralelos
            ],
        )
        self._dia = self._selector(
            contenedor,
            "Día:",
            4,
            FranjaHoraria.dias_validos,
        )
        self._inicio = self._selector(
            contenedor,
            "Inicio:",
            5,
            [f"{hora:02d}:00" for hora in range(24)],
        )
        self._fin = self._selector(
            contenedor,
            "Fin:",
            6,
            [f"{hora:02d}:00" for hora in range(1, 25)],
        )

        self._cargar_datos_actuales()

        acciones = ttk.Frame(contenedor)
        acciones.grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(15, 0),
        )

        ttk.Button(
            acciones,
            text="Cancelar",
            command=self.destroy,
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Guardar cambios",
            command=self._guardar,
        ).pack(side="left", padx=5)

    @staticmethod
    def _selector(contenedor, texto, fila, valores):
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
            values=valores,
            width=50,
        )
        selector.grid(
            row=fila,
            column=1,
            sticky="ew",
            pady=6,
        )

        return selector

    def _cargar_datos_actuales(self):
        for indice, asignatura in enumerate(self._asignaturas):
            if asignatura.nombre == self._original.materia:
                self._asignatura.current(indice)
                break

        selecciones = (
            (
                self._docente,
                self._docentes,
                self._original.docente,
                "correo",
            ),
            (
                self._aula,
                self._aulas,
                self._original.aula,
                "id_aula",
            ),
            (
                self._paralelo,
                self._paralelos,
                self._original.paralelo,
                "codigo",
            ),
        )

        for selector, objetos, actual, atributo in selecciones:
            if actual is None:
                continue

            identificador_actual = (
                getattr(actual, atributo).strip().casefold()
            )

            for indice, objeto in enumerate(objetos):
                identificador = (
                    getattr(objeto, atributo).strip().casefold()
                )

                if identificador == identificador_actual:
                    selector.current(indice)
                    break

        for selector, objetos, actual in selecciones:
            for indice, objeto in enumerate(objetos):
                if objeto is actual:
                    selector.current(indice)
                    break

        self._dia.set(self._original.franja.dia)
        self._inicio.set(
            f"{self._original.franja.hora_inicio:02d}:00"
        )
        self._fin.set(
            f"{self._original.franja.hora_fin:02d}:00"
        )

    @staticmethod
    def _seleccionar(selector, objetos, campo):
        indice = selector.current()

        if indice < 0 or indice >= len(objetos):
            raise ValueError(f"Selecciona {campo}.")

        return objetos[indice]

    def _guardar(self):
        try:
            # Comprueba el permiso al guardar.
            self._usuario.exigir_permiso("gestionar_horarios")

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

            if (
                self._dia.current() < 0
                or self._inicio.current() < 0
                or self._fin.current() < 0
            ):
                raise ValueError(
                    "Selecciona el día y las horas."
                )

            franja = FranjaHoraria(
                self._dia.get(),
                int(self._inicio.get().split(":")[0]),
                int(self._fin.get().split(":")[0]),
            )

            nuevo = Horario(
                materia=asignatura.nombre,
                docente=docente,
                aula=aula,
                franja=franja,
                paralelo=paralelo,
            )

            conflictos = self._gestor.actualizar(
                self._original,
                nuevo,
            )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "No se pudo actualizar",
                str(error),
                parent=self,
            )
            return

        if conflictos:
            motivos = "\n".join(
                dict.fromkeys(
                    conflicto.motivo
                    for conflicto in conflictos
                )
            )

            messagebox.showwarning(
                "Conflictos encontrados",
                (
                    f"{motivos}\n\n"
                    "Se conservó el horario original."
                ),
                parent=self,
            )
            return

        self._al_guardar()
        self.destroy()