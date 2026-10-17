import os
import sys
import unittest

# Para poder hacer "from modelos.usuario import ..." desde la carpeta tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from modelos.usuario import Usuario
from modelos.estudiante import Estudiante
from modelos.docente import Docente
from modelos.administrador_academico import AdministradorAcademico


def crear_estudiante(**cambios):
    datos = dict(
        nombre="Javier Mendoza",
        correo="1312345678@live.uleam.edu.ec",
        contrasena="clave1234",
        carrera="Software",
        semestre=3,
    )
    datos.update(cambios)
    return Estudiante(**datos)


def crear_docente(**cambios):
    datos = dict(
        nombre="Ana Perez",
        correo="ana.perez@uleam.edu.ec",
        contrasena="clave1234",
        titulo="Ingeniera",
        area="Programacion",
        horas_semanales_max=20,
    )
    datos.update(cambios)
    return Docente(**datos)


class TestUsuarioBase(unittest.TestCase):
    def test_usuario_no_se_puede_instanciar(self):
        with self.assertRaises(TypeError):
            Usuario("Ana", "ana@uleam.edu.ec", "clave1234")

    def test_nombre_vacio_falla(self):
        with self.assertRaises(ValueError):
            crear_estudiante(nombre="   ")

    def test_correo_sin_arroba_falla(self):
        with self.assertRaises(ValueError):
            crear_estudiante(correo="correo-sin-arroba")

    def test_contrasena_corta_falla(self):
        with self.assertRaises(ValueError):
            crear_estudiante(contrasena="abc1")

    def test_contrasena_sin_numeros_falla(self):
        with self.assertRaises(ValueError):
            crear_estudiante(contrasena="sololetras")

    def test_cambiar_contrasena_correcta(self):
        est = crear_estudiante()
        est.cambiar_contrasena("clave1234", "nueva5678")
        self.assertTrue(est.verificar_contrasena("nueva5678"))

    def test_cambiar_contrasena_con_actual_incorrecta(self):
        est = crear_estudiante()
        with self.assertRaises(ValueError):
            est.cambiar_contrasena("incorrecta1", "nueva5678")

    def test_sesion(self):
        est = crear_estudiante()
        self.assertFalse(est.sesion_activa)
        est.iniciar_sesion("clave1234")
        self.assertTrue(est.sesion_activa)
        est.cerrar_sesion()
        self.assertFalse(est.sesion_activa)

    def test_iniciar_sesion_con_clave_incorrecta(self):
        est = crear_estudiante()
        with self.assertRaises(ValueError):
            est.iniciar_sesion("incorrecta1")
        self.assertFalse(est.sesion_activa)


class TestEstudiante(unittest.TestCase):
    def test_creacion_correcta(self):
        est = crear_estudiante()
        self.assertEqual(est.carrera, "Software")
        self.assertEqual(est.semestre, 3)

    def test_dominio_de_docente_no_vale_para_estudiante(self):
        with self.assertRaises(ValueError):
            crear_estudiante(correo="ana.perez@uleam.edu.ec")

    def test_semestre_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            crear_estudiante(semestre=11)

    def test_perfil_no_incluye_contrasena(self):
        self.assertNotIn("clave1234", crear_estudiante().mostrar_perfil())


class TestDocente(unittest.TestCase):
    def test_creacion_correcta(self):
        doc = crear_docente()
        self.assertEqual(doc.horas_semanales_max, 20)

    def test_correo_de_estudiante_no_vale_para_docente(self):
        with self.assertRaises(ValueError):
            crear_docente(correo="1312345678@live.uleam.edu.ec")

    def test_horas_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            crear_docente(horas_semanales_max=41)

    def test_titulo_que_no_es_texto_da_valueerror(self):
        # Esta prueba probablemente FALLE ahora: es el punto 2 del diagnostico.
        with self.assertRaises(ValueError):
            crear_docente(titulo=123)

    def test_perfil_no_incluye_contrasena(self):
        self.assertNotIn("clave1234", crear_docente().mostrar_perfil())


class TestAdministradorAcademico(unittest.TestCase):
    def test_creacion_correcta(self):
        adm = AdministradorAcademico(
            "Luis Vera", "luis.vera@uleam.edu.ec", "clave1234", "Ciencias Informaticas"
        )
        self.assertEqual(adm.facultad, "Ciencias Informaticas")

    def test_facultad_vacia_falla(self):
        with self.assertRaises(ValueError):
            AdministradorAcademico(
                "Luis Vera", "luis.vera@uleam.edu.ec", "clave1234", "  "
            )


if __name__ == "__main__":
    unittest.main()