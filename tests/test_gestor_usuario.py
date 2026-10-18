import os
import sys
import unittest
 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
 
from servicios.gestor_usuarios import crear_gestor_con_datos_ejemplo
 
 
class TestGestorUsuarios(unittest.TestCase):
    def setUp(self):
        self.gestor = crear_gestor_con_datos_ejemplo()
 
    def test_autenticar_correcto(self):
        usuario = self.gestor.autenticar("carlos.perez@uleam.edu.ec", "clave1234")
        self.assertTrue(usuario.sesion_activa)
 
    def test_autenticar_contrasena_incorrecta(self):
        with self.assertRaises(ValueError):
            self.gestor.autenticar("carlos.perez@uleam.edu.ec", "incorrecta1")
 
    def test_autenticar_correo_inexistente(self):
        with self.assertRaises(ValueError):
            self.gestor.autenticar("nadie@uleam.edu.ec", "clave1234")
 
    def test_registrar_correo_repetido(self):
        usuario = self.gestor.autenticar("javier@uleam.edu.ec", "clave1234")
        with self.assertRaises(ValueError):
            self.gestor.registrar(usuario)
 
 
if __name__ == "__main__":
    unittest.main()