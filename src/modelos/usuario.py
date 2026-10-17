from abc import ABC, abstractmethod


class Usuario(ABC):
    """Clase base abstracta de todos los usuarios de Chronos-Style.

    Guarda los datos comunes (nombre, correo, contraseña) y valida que sean
    correctos. Las clases hijas agregan sus datos propios.
    """

    # Dominio de correo permitido. Las hijas lo sobrescriben.
    # None significa que no se exige un dominio concreto.
    _DOMINIO_CORREO = None
    _LONGITUD_MINIMA_CONTRASENA = 8

    def __init__(self, nombre, correo, contrasena):
        self._nombre = self._validar_nombre(nombre)
        self._correo = self._validar_correo(correo)
        self._validar_contrasena(contrasena)
        self._contrasena = contrasena
        self._sesion_activa = False

    # ---------- Validaciones ----------

    def _validar_nombre(self, nombre):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        return nombre.strip()
    
    def _validar_texto(self, valor, campo):
        """Valida que un dato sea texto no vacío y lo devuelve sin espacios sobrantes."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{campo} no puede estar vacío.")
        return valor.strip()

    def _validar_correo(self, correo):
        if not isinstance(correo, str):
            raise ValueError("El correo debe ser texto.")
        correo = correo.strip().lower()

        # Formato general: una sola @, nada antes ni después, sin espacios.
        partes = correo.split("@")
        if len(partes) != 2 or not partes[0] or "." not in partes[1] or " " in correo:
            raise ValueError(f"Correo con formato inválido: '{correo}'.")

        # Dominio específico del tipo de usuario (si la hija lo define).
        if self._DOMINIO_CORREO and not correo.endswith("@" + self._DOMINIO_CORREO):
            raise ValueError(
                f"El correo debe terminar en @{self._DOMINIO_CORREO}."
            )
        return correo

    def _validar_contrasena(self, contrasena):
        if not isinstance(contrasena, str):
            raise ValueError("La contraseña debe ser texto.")
        if len(contrasena) < self._LONGITUD_MINIMA_CONTRASENA:
            raise ValueError(
                f"La contraseña debe tener al menos "
                f"{self._LONGITUD_MINIMA_CONTRASENA} caracteres."
            )
        if not any(c.isalpha() for c in contrasena) or not any(c.isdigit() for c in contrasena):
            raise ValueError("La contraseña debe incluir letras y números.")

    # ---------- Propiedades ----------

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre):
        self._nombre = self._validar_nombre(nuevo_nombre)

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, nuevo_correo):
        self._correo = self._validar_correo(nuevo_correo)

    # ---------- Contraseña ----------

    def verificar_contrasena(self, contrasena):
        """Devuelve True si la contraseña coincide con la guardada."""
        return contrasena == self._contrasena

    def cambiar_contrasena(self, contrasena_actual, nueva_contrasena):
        """Cambia la contraseña solo si se conoce la actual."""
        if not self.verificar_contrasena(contrasena_actual):
            raise ValueError("La contraseña actual es incorrecta.")
        self._validar_contrasena(nueva_contrasena)
        self._contrasena = nueva_contrasena
        
    # ---------- Sesión ----------

    @property
    def sesion_activa(self):
        return self._sesion_activa

    def iniciar_sesion(self, contrasena):
        """Inicia sesión si la contraseña es correcta."""
        if not self.verificar_contrasena(contrasena):
            raise ValueError("Contraseña incorrecta.")
        self._sesion_activa = True

    def cerrar_sesion(self):
        """Cierra la sesión."""
        self._sesion_activa = False

    # ---------- Perfil ----------

    @abstractmethod
    def mostrar_perfil(self):
        """Devuelve un texto con el perfil. Cada hija decide qué incluye.

        Importante: nunca debe incluir la contraseña.
        """