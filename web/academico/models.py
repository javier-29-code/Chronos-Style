
# Create your models here.

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)

class ProgramaAcademico(models.Model):
    class Nivel(models.TextChoices):
        GRADO = "GRADO", "Grado"
        POSGRADO = "POSGRADO", "Posgrado"

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )
    nombre = models.CharField(max_length=150)
    nivel = models.CharField(
        max_length=10,
        choices=Nivel.choices,
        default=Nivel.GRADO,
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "programa académico"
        verbose_name_plural = "programas académicos"

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class PeriodoAcademico(models.Model):
    codigo = models.CharField(
        max_length=30,
        unique=True,
    )
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "periodo académico"
        verbose_name_plural = "periodos académicos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    fecha_fin__gt=models.F("fecha_inicio")
                ),
                name="periodo_fin_posterior_inicio",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.fecha_inicio is not None
            and self.fecha_fin is not None
            and self.fecha_fin <= self.fecha_inicio
        ):
            raise ValidationError({
                "fecha_fin": (
                    "La fecha de fin debe ser posterior "
                    "a la fecha de inicio."
                ),
            })

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"
    
class Paralelo(models.Model):
    """Grupo de clases de un programa durante un periodo."""

    programa = models.ForeignKey(
        ProgramaAcademico,
        on_delete=models.PROTECT,
        related_name="paralelos",
    )
    periodo = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name="paralelos",
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Ejemplos: Tercero A, Décimo B, Grupo intensivo.",
    )

    class Meta:
        ordering = ("programa__nombre", "nombre")
        verbose_name = "grupo o paralelo"
        verbose_name_plural = "grupos o paralelos"
        constraints = [
            models.UniqueConstraint(
                fields=("programa", "periodo", "nombre"),
                name="paralelo_nombre_unico_programa_periodo",
            ),
        ]

    def clean(self):
        super().clean()

        # Unifica espacios y mayúsculas para evitar variantes
        # como "Tercero A" y "  tercero   a  ".
        self.nombre = " ".join((self.nombre or "").split()).upper()

        if not self.nombre:
            raise ValidationError({
                "nombre": "El nombre del grupo es obligatorio.",
            })

    def __str__(self):
        return (
            f"{self.programa.codigo} · "
            f"{self.nombre} · {self.periodo.codigo}"
        )


class Inscripcion(models.Model):
    """Relaciona un estudiante con un grupo y su periodo."""

    estudiante = models.ForeignKey(
        "usuarios.PerfilEstudiante",
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )
    paralelo = models.ForeignKey(
        Paralelo,
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "inscripción a grupo"
        verbose_name_plural = "inscripciones a grupos"
        constraints = [
            models.UniqueConstraint(
                fields=("estudiante", "paralelo"),
                name="inscripcion_estudiante_paralelo_unica",
            ),
        ]

    def __str__(self):
        return f"{self.estudiante} → {self.paralelo}"
    
class Asignatura(models.Model):
    """Materia del catálogo académico."""

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )
    nombre = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("nombre", "codigo")
        verbose_name = "asignatura"
        verbose_name_plural = "asignaturas"

    def clean(self):
        super().clean()

        self.codigo = (self.codigo or "").strip().upper()
        self.nombre = " ".join((self.nombre or "").split())

        errores = {}

        if not self.codigo:
            errores["codigo"] = "El código es obligatorio."
        elif any(caracter.isspace() for caracter in self.codigo):
            errores["codigo"] = "El código no puede contener espacios."

        if not self.nombre:
            errores["nombre"] = "El nombre es obligatorio."

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"
    

class Aula(models.Model):
    """Espacio físico disponible para impartir clases."""

    class Tipo(models.TextChoices):
        AULA = "AULA", "Aula teórica"
        LABORATORIO = "LABORATORIO", "Laboratorio general"
        COMPUTACION = "COMPUTACION", "Laboratorio de computación"
        ELECTRONICA = "ELECTRONICA", "Laboratorio de electrónica"
        REDES = "REDES", "Laboratorio de redes"

    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(
        max_length=15,
        choices=Tipo.choices,
        default=Tipo.AULA,
    )
    ubicacion = models.CharField(max_length=150, blank=True)

    capacidad = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Opcional. Número de estudiantes que admite.",
    )
    tiene_proyector = models.BooleanField(default=False)
    tiene_pantalla_tactil = models.BooleanField(default=False)
    cantidad_computadoras = models.PositiveSmallIntegerField(default=0)
    equipamiento = models.TextField(
        blank=True,
        help_text="Descripción del equipamiento disponible.",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("codigo",)
        verbose_name = "aula"
        verbose_name_plural = "aulas"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(capacidad__isnull=True)
                    | models.Q(capacidad__gte=1)
                ),
                name="aula_capacidad_positiva_o_nula",
            ),
        ]

    def clean(self):
        super().clean()

        self.codigo = (self.codigo or "").strip().upper()
        self.nombre = " ".join((self.nombre or "").split())
        self.ubicacion = (self.ubicacion or "").strip()
        self.equipamiento = (self.equipamiento or "").strip()

        errores = {}

        if not self.codigo:
            errores["codigo"] = "El código es obligatorio."
        elif any(caracter.isspace() for caracter in self.codigo):
            errores["codigo"] = "El código no puede contener espacios."

        if not self.nombre:
            errores["nombre"] = "El nombre es obligatorio."

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"