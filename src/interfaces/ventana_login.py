"""Pantalla de inicio de sesión de Chronos-Style.

Esta capa solo muestra datos y recoge lo que escribe el usuario.
Toda la lógica de validación vive en servicios/gestor_usuarios.py.
"""
import tkinter as tk
from tkinter import ttk

from servicios.gestor_usuarios import crear_gestor_con_datos_ejemplo

# ---------- Constantes de diseño (se cambian aquí y afectan a toda la ventana) ----------
COLOR_PRIMARIO = "#1e40af"          # azul del panel izquierdo y del botón
COLOR_PRIMARIO_OSCURO = "#1e3a8a"   # azul del botón al pasar el mouse
COLOR_FONDO = "#ffffff"             # fondo del formulario
COLOR_TEXTO = "#1f2937"             # texto principal
COLOR_SUAVE = "#6b7280"             # texto secundario
COLOR_ERROR = "#dc2626"             # mensajes de error
ANCHO = 820
ALTO = 500
ANCHO_PANEL = 340                   # ancho del panel azul de la izquierda


class VentanaLogin(tk.Tk):
    """Ventana de inicio de sesión: panel de marca a la izquierda y formulario a la derecha."""

    def __init__(self, gestor):
        super().__init__()
        # El gestor llega desde afuera: la ventana no crea ni guarda usuarios.
        self._gestor = gestor
        # Aquí queda el usuario que inició sesión (None si se cierra la ventana sin ingresar).
        self.usuario = None

        self.title("Chronos-Style - Iniciar sesión")
        self.resizable(False, False)
        self._centrar_ventana()
        self._configurar_estilos()
        self._crear_panel_marca()
        self._crear_formulario()

        # Presionar Enter equivale a presionar el botón "Ingresar".
        self.bind("<Return>", lambda evento: self._iniciar_sesion())
        self._entrada_correo.focus()

    # ---------- Configuración de la ventana ----------

    def _centrar_ventana(self):
        """Fija el tamaño de la ventana y la coloca en el centro de la pantalla."""
        x = (self.winfo_screenwidth() - ANCHO) // 2
        y = (self.winfo_screenheight() - ALTO) // 2
        self.geometry(f"{ANCHO}x{ALTO}+{x}+{y}")

    def _configurar_estilos(self):
        """Define los estilos ttk. Se usa el tema 'clam' porque permite cambiar colores."""
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        # Estilos de los textos del formulario
        estilo.configure("Fondo.TFrame", background=COLOR_FONDO)
        estilo.configure("Encabezado.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_TEXTO, font=("Segoe UI", 20, "bold"))
        estilo.configure("Suave.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_SUAVE, font=("Segoe UI", 10))
        estilo.configure("Campo.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_TEXTO, font=("Segoe UI", 10, "bold"))
        estilo.configure("Error.TLabel", background=COLOR_FONDO,
                         foreground=COLOR_ERROR, font=("Segoe UI", 10))

        # Casilla "Mostrar contraseña"
        estilo.configure("Fondo.TCheckbutton", background=COLOR_FONDO,
                         foreground=COLOR_SUAVE, font=("Segoe UI", 9))
        estilo.map("Fondo.TCheckbutton", background=[("active", COLOR_FONDO)])

        # Botón principal: cambia de color cuando el mouse pasa por encima
        estilo.configure("Principal.TButton", background=COLOR_PRIMARIO,
                         foreground="white", font=("Segoe UI", 11, "bold"),
                         padding=10, borderwidth=0)
        estilo.map("Principal.TButton",
                   background=[("active", COLOR_PRIMARIO_OSCURO)])

    # ---------- Construcción de la pantalla ----------

    def _crear_panel_marca(self):
        """Panel azul de la izquierda con el nombre del sistema."""
        panel = tk.Frame(self, bg=COLOR_PRIMARIO, width=ANCHO_PANEL)
        panel.pack(side="left", fill="y")
        panel.pack_propagate(False)  # evita que el panel se encoja al tamaño de su contenido

        # Contenedor centrado dentro del panel
        contenido = tk.Frame(panel, bg=COLOR_PRIMARIO)
        contenido.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(contenido, text="Chronos-Style", bg=COLOR_PRIMARIO, fg="white",
                 font=("Segoe UI", 26, "bold")).pack()
        tk.Label(contenido, text="Gestión de horarios\nacadémicos universitarios",
                 bg=COLOR_PRIMARIO, fg="#bfdbfe", font=("Segoe UI", 12),
                 justify="center").pack(pady=(10, 0))

        # Texto pequeño en la parte baja del panel
        tk.Label(panel, text="Proyecto de Programación Orientada a Objetos",
                 bg=COLOR_PRIMARIO, fg="#93c5fd",
                 font=("Segoe UI", 9)).pack(side="bottom", pady=20)

    def _crear_formulario(self):
        """Lado derecho: campos de correo y contraseña, mensaje de error y botón."""
        lado = ttk.Frame(self, style="Fondo.TFrame")
        lado.pack(side="right", fill="both", expand=True)

        # Formulario centrado dentro del lado derecho
        formulario = ttk.Frame(lado, style="Fondo.TFrame")
        formulario.place(relx=0.5, rely=0.5, anchor="center", width=320)

        ttk.Label(formulario, text="Iniciar sesión",
                  style="Encabezado.TLabel").pack(anchor="w")
        ttk.Label(formulario, text="Ingresa con tu correo institucional",
                  style="Suave.TLabel").pack(anchor="w", pady=(2, 25))

        # Campo de correo
        ttk.Label(formulario, text="Correo", style="Campo.TLabel").pack(anchor="w")
        self._entrada_correo = ttk.Entry(formulario, font=("Segoe UI", 11))
        self._entrada_correo.pack(fill="x", pady=(5, 15), ipady=4)

        # Campo de contraseña (show="*" oculta lo que se escribe)
        ttk.Label(formulario, text="Contraseña", style="Campo.TLabel").pack(anchor="w")
        self._entrada_contrasena = ttk.Entry(formulario, font=("Segoe UI", 11), show="*")
        self._entrada_contrasena.pack(fill="x", pady=(5, 8), ipady=4)

        # Casilla para mostrar u ocultar la contraseña
        self._mostrar = tk.BooleanVar(value=False)
        ttk.Checkbutton(formulario, text="Mostrar contraseña",
                        variable=self._mostrar, style="Fondo.TCheckbutton",
                        command=self._alternar_contrasena).pack(anchor="w")

        # Mensaje de error dentro del formulario (vacío mientras no haya error)
        self._mensaje_error = tk.StringVar()
        ttk.Label(formulario, textvariable=self._mensaje_error,
                  style="Error.TLabel", wraplength=320).pack(anchor="w", pady=(10, 10))

        ttk.Button(formulario, text="Ingresar", style="Principal.TButton",
                   command=self._iniciar_sesion).pack(fill="x")

    # ---------- Acciones ----------

    def _alternar_contrasena(self):
        """Muestra la contraseña en texto normal o la oculta según la casilla."""
        self._entrada_contrasena.configure(show="" if self._mostrar.get() else "*")

    def _iniciar_sesion(self):
        """Toma lo escrito, se lo pasa al gestor y muestra el resultado."""
        correo = self._entrada_correo.get()
        contrasena = self._entrada_contrasena.get()
        try:
            usuario = self._gestor.autenticar(correo, contrasena)
        except ValueError as error:
            # Credenciales incorrectas: mostramos el mensaje y limpiamos la contraseña
            self._mensaje_error.set(str(error))
            self._entrada_contrasena.delete(0, "end")
            self._entrada_contrasena.focus()
            return
        # Login correcto: guardamos el usuario y cerramos esta ventana.
        self.usuario = usuario
        self.destroy()


if __name__ == "__main__":
    # Permite probar esta pantalla sola, con usuarios de ejemplo.
    VentanaLogin(crear_gestor_con_datos_ejemplo()).mainloop()