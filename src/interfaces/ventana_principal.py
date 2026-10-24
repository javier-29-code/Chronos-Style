"""Ventana principal de Chronos-Style (la que aparece después del login).

Es la misma para todos los roles: usa mostrar_perfil() del usuario, que cada
clase hija implementa a su manera (polimorfismo). Esta capa solo muestra datos.
"""
import tkinter as tk
from tkinter import ttk
from interfaces.panel_horarios import PanelHorarios
from interfaces.panel_consulta_horarios import PanelConsultaHorarios
from modelos.docente import Docente

# Reutilizamos los colores del login para que ambas pantallas se vean iguales.
from interfaces.ventana_login import (
    COLOR_PRIMARIO, COLOR_PRIMARIO_OSCURO, COLOR_FONDO, COLOR_TEXTO, COLOR_SUAVE,
)

COLOR_FONDO_APP = "#f3f4f6"   # gris claro del fondo general
ANCHO = 1050
ALTO = 720


class VentanaPrincipal(tk.Tk):
    """Ventana con cabecera (nombre, rol, cerrar sesión) y pestañas."""

    def __init__(self, usuario, gestor_catalogos, gestor_horarios):
        super().__init__()

        self._usuario = usuario
        self._gestor_catalogos = gestor_catalogos
        self._gestor_horarios = gestor_horarios

        self.cerro_sesion = False

        self.title("Chronos-Style")
        self._centrar_ventana()
        self._configurar_estilos()
        self._crear_cabecera()
        self._crear_pestanas()
        
    # ---------- Configuración de la ventana ----------

    def _centrar_ventana(self):
        """Fija el tamaño de la ventana y la coloca en el centro de la pantalla."""
        x = (self.winfo_screenwidth() - ANCHO) // 2
        y = (self.winfo_screenheight() - ALTO) // 2
        self.geometry(f"{ANCHO}x{ALTO}+{x}+{y}")
        self.minsize(700, 450)

    def _configurar_estilos(self):
        """Define los estilos ttk de esta ventana."""
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        # Fondos
        estilo.configure("App.TFrame", background=COLOR_FONDO_APP)
        estilo.configure("Tarjeta.TFrame", background=COLOR_FONDO)

        # Cabecera azul
        estilo.configure("Cabecera.TFrame", background=COLOR_PRIMARIO)
        estilo.configure("Marca.TLabel", background=COLOR_PRIMARIO,
                         foreground="white", font=("Segoe UI", 16, "bold"))
        estilo.configure("Usuario.TLabel", background=COLOR_PRIMARIO,
                         foreground="white", font=("Segoe UI", 11, "bold"))
        estilo.configure("Rol.TLabel", background=COLOR_PRIMARIO,
                         foreground="#bfdbfe", font=("Segoe UI", 9))
        estilo.configure("Cabecera.TButton", background=COLOR_PRIMARIO_OSCURO,
                         foreground="white", font=("Segoe UI", 10, "bold"),
                         padding=8, borderwidth=0)
        estilo.map("Cabecera.TButton", background=[("active", "#172554")])

        # Textos de la tarjeta de perfil
        estilo.configure("Titulo.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_TEXTO, font=("Segoe UI", 16, "bold"))
        estilo.configure("Etiqueta.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_SUAVE, font=("Segoe UI", 11))
        estilo.configure("Valor.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_TEXTO, font=("Segoe UI", 11, "bold"))

        # Pestañas
        estilo.configure("TNotebook", background=COLOR_FONDO_APP, borderwidth=0)
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(18, 8))

    # ---------- Construcción de la pantalla ----------

    def _crear_cabecera(self):
        """Barra azul superior: nombre del sistema, datos del usuario y botón de salir."""
        cabecera = ttk.Frame(self, style="Cabecera.TFrame", padding=(25, 12))
        cabecera.pack(fill="x")

        ttk.Label(cabecera, text="Chronos-Style", style="Marca.TLabel").pack(side="left")

        ttk.Button(cabecera, text="Cerrar sesión", style="Cabecera.TButton",
                   command=self._cerrar_sesion).pack(side="right")

        # Nombre y rol del usuario, apilados a la izquierda del botón.
        datos = ttk.Frame(cabecera, style="Cabecera.TFrame")
        datos.pack(side="right", padx=20)
        ttk.Label(datos, text=self._usuario.nombre,
                  style="Usuario.TLabel").pack(anchor="e")
        ttk.Label(datos, text=self._obtener_rol(),
                  style="Rol.TLabel").pack(anchor="e")

    def _crear_pestanas(self):
        cuaderno = ttk.Notebook(self)
        cuaderno.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        self._crear_pestana_perfil(cuaderno)

        comprobar_permiso = getattr(
            self._usuario,
            "tiene_permiso",
            None,
        )

        self._panel_horarios = None
        self._panel_consulta = None

        if callable(comprobar_permiso):
            if comprobar_permiso("gestionar_horarios"):
                self._panel_horarios = PanelHorarios(
                    master=cuaderno,
                    gestor_catalogos=self._gestor_catalogos,
                    gestor_horarios=self._gestor_horarios,
                )

                cuaderno.add(
                    self._panel_horarios,
                    text="Registrar horario",
                )

            if comprobar_permiso("consultar_horarios_generales"):
                self._panel_consulta = PanelConsultaHorarios(
                    master=cuaderno,
                    gestor_horarios=self._gestor_horarios,
                )

                cuaderno.add(
                    self._panel_consulta,
                    text="Consultar horarios",
                )

        # Si no tiene consulta general, un docente puede ver sus clases.
        if (
            self._panel_consulta is None
            and isinstance(self._usuario, Docente)
        ):
            self._panel_consulta = PanelConsultaHorarios(
                master=cuaderno,
                gestor_horarios=self._gestor_horarios,
                docente=self._usuario,
            )

            cuaderno.add(
                self._panel_consulta,
                text="Mi horario",
            )
            
        if (
            self._panel_horarios is not None
            and self._panel_consulta is not None
        ):
            self._panel_horarios.bind(
                "<<HorariosActualizados>>",
                self._panel_consulta.actualizar,
            )

    def _crear_pestana_perfil(self, cuaderno):
        """Tarjeta con los datos del perfil, una fila por cada línea de mostrar_perfil()."""
        pestana = ttk.Frame(cuaderno, style="App.TFrame", padding=25)
        cuaderno.add(pestana, text="Mi perfil")

        tarjeta = ttk.Frame(pestana, style="Tarjeta.TFrame", padding=30)
        tarjeta.pack(anchor="nw")

        ttk.Label(tarjeta, text="Mi perfil", style="Titulo.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # mostrar_perfil() devuelve líneas con el formato "Etiqueta: valor".
        lineas = self._usuario.mostrar_perfil().split("\n")
        for fila, linea in enumerate(lineas, start=1):
            etiqueta, valor = linea.split(":", 1)
            ttk.Label(tarjeta, text=etiqueta, style="Etiqueta.TLabel").grid(
                row=fila, column=0, sticky="w", padx=(0, 40), pady=6)
            ttk.Label(tarjeta, text=valor.strip(), style="Valor.TLabel").grid(
                row=fila, column=1, sticky="w", pady=6)

    # ---------- Acciones ----------

    def _obtener_rol(self):
        """El rol es la etiqueta de la primera línea del perfil (p. ej. 'Docente')."""
        return self._usuario.mostrar_perfil().split(":", 1)[0]

    def _cerrar_sesion(self):
        """Marca que el usuario salió a propósito y cierra la ventana."""
        self.cerro_sesion = True
        self.destroy()