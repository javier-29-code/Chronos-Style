# Create your models here.

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models


class Usuario(AbstractUser):
    """Cuenta de acceso de Chronos-Style."""

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"


class PerfilDocente(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_docente",
    )
    titulo = models.CharField(max_length=150)
    area = models.CharField(max_length=150)
    horas_semanales_max = models.PositiveSmallIntegerField(
        default=20,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(40),
        ],
    )
    
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "perfil docente"
        verbose_name_plural = "perfiles docentes"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    horas_semanales_max__gte=1,
                    horas_semanales_max__lte=40,
                ),
                name="docente_horas_entre_1_y_40",
            ),
        ]

    def __str__(self):
        nombre = (
            self.usuario.get_full_name()
            or self.usuario.username
        )
        return f"Docente: {nombre}"


class PerfilEstudiante(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_estudiante",
    )
    programa = models.ForeignKey(
        "academico.ProgramaAcademico",
        on_delete=models.PROTECT,
        related_name="estudiantes",
    )
    semestre = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
    )

    class Meta:
        verbose_name = "perfil estudiante"
        verbose_name_plural = "perfiles estudiantiles"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    semestre__gte=1,
                    semestre__lte=10,
                ),
                name="estudiante_semestre_entre_1_y_10",
            ),
        ]

    def __str__(self):
        nombre = (
            self.usuario.get_full_name()
            or self.usuario.username
        )
        return f"Estudiante: {nombre}"