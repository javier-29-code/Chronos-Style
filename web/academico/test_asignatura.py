from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Asignatura


class AsignaturaTests(TestCase):
    def test_normaliza_y_guarda_asignatura(self):
        asignatura = Asignatura(
            codigo="  prog-01  ",
            nombre="  Programación   orientada a objetos  ",
        )
        asignatura.full_clean()
        asignatura.save()
        asignatura.refresh_from_db()

        self.assertEqual(asignatura.codigo, "PROG-01")
        self.assertEqual(
            asignatura.nombre,
            "Programación orientada a objetos",
        )

    def test_rechaza_datos_invalidos(self):
        casos = (
            ("   ", "Programación", "codigo"),
            ("PROG 01", "Programación", "codigo"),
            ("PROG-01", "   ", "nombre"),
        )

        for codigo, nombre, campo in casos:
            with self.subTest(codigo=codigo, nombre=nombre):
                asignatura = Asignatura(
                    codigo=codigo,
                    nombre=nombre,
                )

                with self.assertRaises(ValidationError) as resultado:
                    asignatura.full_clean()

                self.assertIn(
                    campo,
                    resultado.exception.message_dict,
                )

    def test_rechaza_codigo_equivalente(self):
        Asignatura.objects.create(
            codigo="PROG-01",
            nombre="Programación",
        )
        duplicada = Asignatura(
            codigo="  prog-01 ",
            nombre="Otra materia",
        )

        with self.assertRaises(ValidationError):
            duplicada.full_clean()

    def test_base_rechaza_codigo_duplicado(self):
        Asignatura.objects.create(
            codigo="PROG-01",
            nombre="Programación",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Asignatura.objects.create(
                    codigo="PROG-01",
                    nombre="Otra materia",
                )

    def test_permite_mismo_nombre_con_codigos_distintos(self):
        for codigo in ("MAT-01", "MAT-02"):
            asignatura = Asignatura(
                codigo=codigo,
                nombre="Matemáticas",
            )
            asignatura.full_clean()
            asignatura.save()

        self.assertEqual(
            Asignatura.objects.filter(nombre="Matemáticas").count(),
            2,
        )