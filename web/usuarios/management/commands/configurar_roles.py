from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crea los grupos y permisos de Chronos-Style."

    @transaction.atomic
    def handle(self, *args, **options):
        coordinador, _ = Group.objects.get_or_create(
            name="Coordinador",
        )
        Group.objects.get_or_create(name="Docente")
        Group.objects.get_or_create(name="Estudiante")

        modelos = {
            "academico": (
                "programaacademico",
                "periodoacademico",
                "paralelo",
                "asignatura",
                "aula",
                "inscripcion",
            ),
            "planificacion": (
                "horario",
                "necesidadclase",
                "franjaplanificacion",
                "disponibilidaddocente",
                "propuestahorario",
                "bloquepropuesta",
            ),
            "usuarios": (
                "perfildocente",
                "perfilestudiante",
            ),
        }

        permisos = []

        for app, nombres in modelos.items():
            for modelo in nombres:
                for accion in ("view", "add", "change"):
                    permisos.append(
                        self._permiso(
                            app,
                            modelo,
                            f"{accion}_{modelo}",
                        )
                    )

        permisos.extend([
            self._permiso(
                "usuarios",
                "usuario",
                "add_usuario",
            ),
            self._permiso(
                "planificacion",
                "horario",
                "delete_horario",
            ),
            self._permiso(
                "planificacion",
                "propuestahorario",
                "aprobar_propuestahorario",
            ),
        ])

        # Añade los permisos sin eliminar asignaciones anteriores.
        coordinador.permissions.add(*permisos)

        # Docente y Estudiante no reciben view_horario:
        # ese permiso permite ver todos los horarios.
        self.stdout.write(self.style.SUCCESS(
            "Grupos configurados: Coordinador, Docente y Estudiante."
        ))

    @staticmethod
    def _permiso(app, modelo, codigo):
        try:
            return Permission.objects.get(
                content_type__app_label=app,
                content_type__model=modelo,
                codename=codigo,
            )
        except Permission.DoesNotExist as error:
            raise CommandError(
                f"Falta el permiso {app}.{codigo}. "
                "Comprueba las migraciones."
            ) from error