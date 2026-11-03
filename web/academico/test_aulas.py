from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Aula


class AulaTests(TestCase):
    def test_normaliza_y_guarda(self):
        aula = Aula(
            codigo="  lab-01 ",
            nombre="  Laboratorio   de redes ",
            tipo=Aula.Tipo.LABORATORIO,
            cantidad_computadoras=20,
            equipamiento="  Switches y routers  ",
        )
        aula.full_clean()
        aula.save()
        aula.refresh_from_db()

        self.assertEqual(aula.codigo, "LAB-01")
        self.assertEqual(aula.nombre, "Laboratorio de redes")
        self.assertEqual(aula.equipamiento, "Switches y routers")
        self.assertEqual(aula.cantidad_computadoras, 20)

    def test_rechaza_datos_invalidos(self):
        casos = (
            ({"codigo": "   "}, "codigo"),
            ({"codigo": "A 01"}, "codigo"),
            ({"nombre": "   "}, "nombre"),
            ({"tipo": "VIRTUAL"}, "tipo"),
            ({"capacidad": 0}, "capacidad"),
            ({"cantidad_computadoras": -1}, "cantidad_computadoras"),
        )

        for cambios, campo in casos:
            with self.subTest(cambios=cambios):
                datos = {"codigo": "A-01", "nombre": "Aula principal"}
                datos.update(cambios)
                aula = Aula(**datos)

                with self.assertRaises(ValidationError) as resultado:
                    aula.full_clean()

                self.assertIn(campo, resultado.exception.message_dict)

    def test_capacidad_es_opcional(self):
        aula = Aula(codigo="A-01", nombre="Aula principal")
        aula.full_clean()
        aula.save()
        aula.refresh_from_db()

        self.assertIsNone(aula.capacidad)
        self.assertEqual(aula.cantidad_computadoras, 0)

    def test_caracteristicas_son_independientes(self):
        for indice, (proyector, pantalla) in enumerate(
            ((False, False), (True, False), (False, True), (True, True))
        ):
            with self.subTest(proyector=proyector, pantalla=pantalla):
                aula = Aula(
                    codigo=f"A-{indice}",
                    nombre="Aula de demostración",
                    tiene_proyector=proyector,
                    tiene_pantalla_tactil=pantalla,
                )
                aula.full_clean()
                aula.save()
                aula.refresh_from_db()

                self.assertEqual(aula.tiene_proyector, proyector)
                self.assertEqual(aula.tiene_pantalla_tactil, pantalla)

    def test_base_rechaza_codigo_duplicado(self):
        Aula.objects.create(codigo="A-01", nombre="Primera aula")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Aula.objects.create(
                    codigo="A-01",
                    nombre="Otra aula",
                )

    def test_base_rechaza_capacidad_cero(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Aula.objects.create(
                    codigo="A-01",
                    nombre="Aula principal",
                    capacidad=0,
                )