import unittest

from src.modelos.usuario import Usuario


class UsuarioDePrueba(Usuario):
    """Subclase mínima para poder instanciar la clase abstracta."""

    def mostrar_perfil(self):
        return f"Perfil de prueba: {self._nombre}"


class UsuarioConDominio(UsuarioDePrueba):
    """Simula una hija que exige un dominio de correo concreto."""

    _DOMINIO_CORREO = "live.uleam.edu.ec"


class TestUsuario(unittest.TestCase):

    def setUp(self):
        self.usuario = UsuarioDePrueba("Ana Pérez", "ana@uleam.edu.ec", "Clave1234")

    def test_no_se_puede_instanciar_la_clase_abstracta(self):
        with self.assertRaises(TypeError):
            Usuario("Ana", "ana@uleam.edu.ec", "Clave1234")

    def test_creacion_valida_normaliza_datos(self):
        u = UsuarioDePrueba("  Ana  ", " ANA@Uleam.edu.ec ", "Clave1234")
        self.assertEqual(u.nombre, "Ana")
        self.assertEqual(u.correo, "ana@uleam.edu.ec")

    def test_nombre_vacio_es_rechazado(self):
        with self.assertRaises(ValueError):
            UsuarioDePrueba("   ", "ana@uleam.edu.ec", "Clave1234")

    def test_correo_invalido_es_rechazado(self):
        for malo in ["sin-arroba", "a@b", "@uleam.edu.ec", "a@@uleam.edu.ec", "a b@uleam.edu.ec"]:
            with self.assertRaises(ValueError, msg=malo):
                UsuarioDePrueba("Ana", malo, "Clave1234")

    def test_dominio_exigido_por_la_clase(self):
        u = UsuarioConDominio("Luis", "e0123456789@live.uleam.edu.ec", "Clave1234")
        self.assertEqual(u.correo, "e0123456789@live.uleam.edu.ec")
        with self.assertRaises(ValueError):
            UsuarioConDominio("Luis", "luis@uleam.edu.ec", "Clave1234")

    def test_contrasena_debil_es_rechazada(self):
        with self.assertRaises(ValueError):
            UsuarioDePrueba("Ana", "ana@uleam.edu.ec", "corta1")
        with self.assertRaises(ValueError):
            UsuarioDePrueba("Ana", "ana@uleam.edu.ec", "soloLetrasAqui")

    def test_setters_validan(self):
        with self.assertRaises(ValueError):
            self.usuario.correo = "xyz"
        with self.assertRaises(ValueError):
            self.usuario.nombre = ""

    def test_verificar_y_cambiar_contrasena(self):
        self.assertTrue(self.usuario.verificar_contrasena("Clave1234"))
        self.assertFalse(self.usuario.verificar_contrasena("OtraClave99"))
        self.usuario.cambiar_contrasena("Clave1234", "NuevaClave99")
        self.assertTrue(self.usuario.verificar_contrasena("NuevaClave99"))
        self.assertFalse(self.usuario.verificar_contrasena("Clave1234"))

    def test_cambiar_contrasena_con_actual_incorrecta(self):
        with self.assertRaises(ValueError):
            self.usuario.cambiar_contrasena("incorrecta1", "NuevaClave99")


if __name__ == "__main__":
    unittest.main()