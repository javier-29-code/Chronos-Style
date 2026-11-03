from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from .models import PerfilDocente
from .servicios_acceso import habilitar_acceso_docente


class AccesoDocenteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Group.objects.get_or_create(name="Docente")

        cls.actor = get_user_model().objects.create_user(
            username="admin_acceso",
            is_superuser=True,
        )
        cls.cuenta = get_user_model().objects.create_user(
            username="docente_sin_acceso",
            password=None,
        )
        cls.docente = PerfilDocente.objects.create(
            usuario=cls.cuenta,
            titulo="Ingeniero",
            area="Informática",
            horas_semanales_max=20,
        )

    def test_habilita_cuenta_y_asigna_grupo(self):
        clave = "K7!rQ9#vL2@pT6$z"

        habilitar_acceso_docente(
            actor=self.actor,
            docente_id=self.docente.pk,
            nueva_contrasena=clave,
        )

        self.cuenta.refresh_from_db()
        self.assertTrue(self.cuenta.check_password(clave))
        self.assertNotEqual(self.cuenta.password, clave)
        self.assertTrue(
            self.cuenta.groups.filter(name="Docente").exists()
        )
        self.assertFalse(self.cuenta.is_staff)
        self.assertFalse(self.cuenta.is_superuser)

    def test_no_reemplaza_password_existente(self):
        self.cuenta.set_password("Anterior9!Clave")
        self.cuenta.save()

        with self.assertRaises(ValidationError):
            habilitar_acceso_docente(
                actor=self.actor,
                docente_id=self.docente.pk,
                nueva_contrasena="K7!rQ9#vL2@pT6$z",
            )

        self.cuenta.refresh_from_db()
        self.assertTrue(
            self.cuenta.check_password("Anterior9!Clave")
        )

    def test_no_habilita_cuenta_privilegiada(self):
        self.cuenta.is_staff = True
        self.cuenta.save()

        with self.assertRaises(PermissionDenied):
            habilitar_acceso_docente(
                actor=self.actor,
                docente_id=self.docente.pk,
                nueva_contrasena="K7!rQ9#vL2@pT6$z",
            )

        self.cuenta.refresh_from_db()
        self.assertFalse(self.cuenta.has_usable_password())

    def test_exige_permiso_al_actor(self):
        with self.assertRaises(PermissionDenied):
            habilitar_acceso_docente(
                actor=self.cuenta,
                docente_id=self.docente.pk,
                nueva_contrasena="K7!rQ9#vL2@pT6$z",
            )

        self.cuenta.refresh_from_db()
        self.assertFalse(self.cuenta.has_usable_password())