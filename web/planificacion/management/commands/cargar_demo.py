import secrets
from collections import Counter
from datetime import date, time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academico.models import (
    Asignatura,
    Aula,
    Inscripcion,
    Paralelo,
    PeriodoAcademico,
    ProgramaAcademico,
)
from planificacion.models import (
    DisponibilidadDocente,
    FranjaParalelo,
    FranjaPlanificacion,
    NecesidadClase,
)
from usuarios.models import PerfilDocente, PerfilEstudiante


class Command(BaseCommand):
    help = (
        "Carga datos ficticios de demostración sin sobrescribir "
        "los registros existentes. Solo disponible con DEBUG=True."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "cargar_demo solo está disponible en desarrollo."
            )

        self.creados = Counter()
        self.credenciales = []

        call_command("configurar_roles", stdout=self.stdout)

        programa = self.obtener(
            ProgramaAcademico,
            codigo="DEMO-TI",
            defaults={
                "nombre": "Demostración de Tecnologías de la Información",
            },
        )

        periodo = self.obtener(
            PeriodoAcademico,
            codigo="DEMO-2027",
            defaults={
                "nombre": "Periodo de demostración 2027",
                "fecha_inicio": date(2027, 3, 1),
                "fecha_fin": date(2027, 7, 31),
            },
        )

        self.cuenta(
            username="demo_coordinador",
            nombres="Coordinador",
            apellidos="Demostración",
            rol="Coordinador",
        )

        for numero in (1, 2):
            self.obtener(
                Aula,
                codigo=f"DEMO-A{numero}",
                defaults={
                    "nombre": f"Aula de demostración {numero}",
                    "tipo": Aula.Tipo.AULA,
                    "capacidad": 40,
                    "ubicacion": "Edificio de demostración",
                    "tiene_proyector": True,
                },
            )

        self.obtener(
            Aula,
            codigo="DEMO-LAB",
            defaults={
                "nombre": "Laboratorio de demostración",
                "tipo": Aula.Tipo.LABORATORIO,
                "capacidad": 30,
                "cantidad_computadoras": 30,
                "ubicacion": "Edificio de demostración",
            },
        )

        # Franjas generales de la institución para este periodo.
        for dia in range(1, 6):
            self.obtener(
                FranjaPlanificacion,
                periodo=periodo,
                dia=dia,
                hora_inicio=time(7),
                hora_fin=time(20),
            )

        configuraciones = (
            {
                "clave": "manana",
                "nombre": "DEMO A - MAÑANA",
                "ventanas": [
                    (dia, time(7), time(12))
                    for dia in range(1, 6)
                ],
                "asignaturas": (
                    ("DEMO-PROG", "Programación"),
                    ("DEMO-BD", "Bases de datos"),
                ),
            },
            {
                "clave": "tarde",
                "nombre": "DEMO B - TARDE",
                "ventanas": [
                    (dia, time(13), time(18))
                    for dia in range(1, 6)
                ],
                "asignaturas": (
                    ("DEMO-RED", "Redes"),
                    ("DEMO-SO", "Sistemas operativos"),
                ),
            },
            {
                "clave": "mixto",
                "nombre": "DEMO C - MIXTO",
                # Cuatro sesiones de 90 minutos requieren ambos días.
                "ventanas": [
                    (1, time(7), time(10)),
                    (2, time(14), time(17)),
                ],
                "asignaturas": (
                    ("DEMO-REQ", "Ingeniería de requisitos"),
                    ("DEMO-SIS", "Sistemas digitales"),
                ),
            },
        )

        for configuracion in configuraciones:
            clave = configuracion["clave"]

            paralelo = self.obtener(
                Paralelo,
                programa=programa,
                periodo=periodo,
                nombre=configuracion["nombre"],
            )

            cuenta_docente = self.cuenta(
                username=f"demo_docente_{clave}",
                nombres="Docente",
                apellidos=f"Demo {clave}",
                rol="Docente",
            )

            docente = self.obtener(
                PerfilDocente,
                usuario=cuenta_docente,
                defaults={
                    "titulo": "Ingeniero",
                    "area": "Tecnologías de la Información",
                    "horas_semanales_max": 20,
                },
            )

            for dia in range(1, 6):
                self.obtener(
                    DisponibilidadDocente,
                    docente=docente,
                    periodo=periodo,
                    dia=dia,
                    hora_inicio=time(7),
                    hora_fin=time(20),
                )

            for dia, inicio, fin in configuracion["ventanas"]:
                self.obtener(
                    FranjaParalelo,
                    paralelo=paralelo,
                    dia=dia,
                    hora_inicio=inicio,
                    hora_fin=fin,
                )

            for codigo, nombre in configuracion["asignaturas"]:
                asignatura = self.obtener(
                    Asignatura,
                    codigo=codigo,
                    defaults={"nombre": nombre},
                )

                self.obtener(
                    NecesidadClase,
                    asignatura=asignatura,
                    docente=docente,
                    paralelo=paralelo,
                    defaults={
                        "sesiones_semanales": 2,
                        "duracion_minutos": 90,
                        "prefiere_laboratorio": codigo in {
                            "DEMO-PROG",
                            "DEMO-BD",
                            "DEMO-RED",
                            "DEMO-SO",
                        },
                    },
                )

            cuenta_estudiante = self.cuenta(
                username=f"demo_estudiante_{clave}",
                nombres="Estudiante",
                apellidos=f"Demo {clave}",
                rol="Estudiante",
            )

            estudiante = self.obtener(
                PerfilEstudiante,
                usuario=cuenta_estudiante,
                defaults={
                    "programa": programa,
                    "semestre": 3,
                },
            )

            self.obtener(
                Inscripcion,
                estudiante=estudiante,
                paralelo=paralelo,
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Datos de demostración preparados."
        ))

        if self.creados:
            for modelo, cantidad in sorted(self.creados.items()):
                self.stdout.write(f"  {modelo}: {cantidad} nuevos")
        else:
            self.stdout.write(
                "No se crearon registros: los datos ya existían."
            )

        if self.credenciales:
            self.stdout.write("")
            self.stdout.write(
                "Accesos nuevos de demostración:"
            )

            for username, password in self.credenciales:
                self.stdout.write(
                    f"  {username} | {password}"
                )

            self.stdout.write(
                "Guarda estas contraseñas: no se mostrarán "
                "ni se cambiarán al repetir el comando."
            )

        self.stdout.write("")
        self.stdout.write(
            "Siguiente paso: ingresa como demo_coordinador "
            "y genera una propuesta para DEMO-2027."
        )

    def obtener(self, modelo, *, defaults=None, **identidad):
        objeto, creado = modelo.objects.get_or_create(
            **identidad,
            defaults=defaults or {},
        )

        if creado:
            objeto.full_clean()
            self.creados[modelo.__name__] += 1

        return objeto

    def cuenta(self, *, username, nombres, apellidos, rol):
        Usuario = get_user_model()

        existente = Usuario.objects.filter(
            username=username,
        ).first()

        if existente is not None:
            # Evita reutilizar por accidente una cuenta ajena.
            if not existente.groups.filter(
                name="Demostración Chronos",
            ).exists():
                raise CommandError(
                    f"La cuenta {username} ya existe y no está "
                    "identificada como cuenta de demostración."
                )

            return existente

        password = secrets.token_urlsafe(12)

        usuario = Usuario(
            username=username,
            first_name=nombres,
            last_name=apellidos,
            email=f"{username}@example.invalid",
        )
        usuario.set_password(password)
        usuario.full_clean()
        usuario.save()

        marcador, _ = Group.objects.get_or_create(
            name="Demostración Chronos",
        )
        grupo = Group.objects.get(name=rol)
        usuario.groups.add(marcador, grupo)

        self.creados["Usuario"] += 1
        self.credenciales.append((username, password))

        return usuario