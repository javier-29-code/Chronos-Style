from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class RolesTests(TestCase):
    def setUp(self):
        call_command("configurar_roles", stdout=StringIO())

    def test_coordinador_gestiona_sin_ser_superusuario(self):
        usuario = get_user_model().objects.create_user(
            username="coordinador_prueba_roles",
        )
        usuario.groups.add(
            Group.objects.get(name="Coordinador")
        )

        self.assertTrue(
            usuario.has_perm("academico.add_aula")
        )
        self.assertTrue(
            usuario.has_perm(
                "planificacion.aprobar_propuestahorario"
            )
        )
        self.assertFalse(usuario.is_superuser)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(
            usuario.has_perm("auth.change_group")
        )
        self.assertFalse(
            usuario.has_perm("usuarios.change_usuario")
        )

        self.client.force_login(usuario)
        respuesta = self.client.get(
            reverse("planificacion_web:lista_aulas")
        )
        self.assertEqual(respuesta.status_code, 200)

    def test_roles_personales_no_reciben_acceso_general(self):
        for nombre in ("Docente", "Estudiante"):
            with self.subTest(rol=nombre):
                usuario = get_user_model().objects.create_user(
                    username=f"rol_{nombre.lower()}",
                )
                usuario.groups.add(
                    Group.objects.get(name=nombre)
                )

                self.assertFalse(
                    usuario.has_perm("planificacion.view_horario")
                )
                self.assertFalse(
                    usuario.has_perm("academico.add_aula")
                )

    def test_repetir_comando_conserva_grupos_y_miembros(self):
        usuario = get_user_model().objects.create_user(
            username="miembro_roles",
        )
        grupo = Group.objects.get(name="Coordinador")
        usuario.groups.add(grupo)

        permisos_antes = set(
            grupo.permissions.values_list("pk", flat=True)
        )

        call_command("configurar_roles", stdout=StringIO())

        self.assertEqual(
            Group.objects.filter(
                name__in=["Coordinador", "Docente", "Estudiante"]
            ).count(),
            3,
        )
        self.assertTrue(usuario.groups.filter(pk=grupo.pk).exists())
        self.assertEqual(
            set(grupo.permissions.values_list("pk", flat=True)),
            permisos_antes,
        )