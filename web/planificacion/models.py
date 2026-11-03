# Create your models here.

from itertools import chain

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from datetime import datetime ,timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

from django.conf import settings

from .validaciones_paralelo import ValidadorFranjaParalelo

class Horario(models.Model):
    """Clase semanal de un grupo durante su periodo académico."""

    class Dia(models.IntegerChoices):
        LUNES = 1, "Lunes"
        MARTES = 2, "Martes"
        MIERCOLES = 3, "Miércoles"
        JUEVES = 4, "Jueves"
        VIERNES = 5, "Viernes"
        SABADO = 6, "Sábado"
        DOMINGO = 7, "Domingo"

    asignatura = models.ForeignKey(
        "academico.Asignatura",
        on_delete=models.PROTECT,
        related_name="horarios",
    )
    docente = models.ForeignKey(
        "usuarios.PerfilDocente",
        on_delete=models.PROTECT,
        related_name="horarios",
    )
    aula = models.ForeignKey(
        "academico.Aula",
        on_delete=models.PROTECT,
        related_name="horarios",
    )
    paralelo = models.ForeignKey(
        "academico.Paralelo",
        on_delete=models.PROTECT,
        related_name="horarios",
    )
    dia = models.PositiveSmallIntegerField(choices=Dia.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    bloque_origen = models.OneToOneField(
        "planificacion.BloquePropuesta",
        on_delete=models.PROTECT,
        related_name="horario_oficial",
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        ordering = ("dia", "hora_inicio", "pk")
        verbose_name = "horario"
        verbose_name_plural = "horarios"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    hora_fin__gt=models.F("hora_inicio"),
                ),
                name="horario_fin_posterior_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(dia__gte=1, dia__lte=7),
                name="horario_dia_entre_1_y_7",
            ),
        ]

    def clean(self):
        super().clean()

        if self.hora_inicio is None or self.hora_fin is None:
            return

        if self.hora_fin <= self.hora_inicio:
            raise ValidationError({
                "hora_fin": (
                    "La hora de fin debe ser posterior "
                    "a la hora de inicio."
                ),
            })

        if self.dia not in self.Dia.values:
            return

        self._validar_cruces()
        self._validar_carga_docente()

    def _validar_cruces(self):
        if not self.paralelo_id:
            return

        try:
            periodo = self.paralelo.periodo
        except ObjectDoesNotExist:
            # full_clean() informa el error del campo relacionado.
            return

        candidatos = (
            type(self).objects
            .filter(
                dia=self.dia,
                hora_inicio__lt=self.hora_fin,
                hora_fin__gt=self.hora_inicio,
                paralelo__periodo__fecha_inicio__lte=periodo.fecha_fin,
                paralelo__periodo__fecha_fin__gte=periodo.fecha_inicio,
            )
            .filter(
                models.Q(docente_id=self.docente_id)
                | models.Q(aula_id=self.aula_id)
                | models.Q(paralelo_id=self.paralelo_id)
            )
            .select_related("paralelo__periodo")
        )

        if self.pk is not None:
            candidatos = candidatos.exclude(pk=self.pk)

        errores = {}

        for otro in candidatos:
            otro_periodo = otro.paralelo.periodo

            inicio_comun = max(
                periodo.fecha_inicio,
                otro_periodo.fecha_inicio,
            )
            fin_comun = min(
                periodo.fecha_fin,
                otro_periodo.fecha_fin,
            )

            # Confirma que las fechas compartidas incluyen
            # al menos una ocurrencia del día de la clase.
            dias_hasta_clase = (
                self.dia - inicio_comun.isoweekday()
            ) % 7
            primera_clase_comun = inicio_comun + timedelta(
                days=dias_hasta_clase,
            )

            if primera_clase_comun > fin_comun:
                continue

            referencia = (
                f"horario #{otro.pk}, "
                f"{otro.hora_inicio:%H:%M}–{otro.hora_fin:%H:%M}"
            )

            if self.docente_id == otro.docente_id:
                errores.setdefault("docente", []).append(
                    f"El docente ya tiene clases en ese intervalo "
                    f"({referencia})."
                )

            if self.aula_id == otro.aula_id:
                errores.setdefault("aula", []).append(
                    f"El aula ya está ocupada en ese intervalo "
                    f"({referencia})."
                )

            if self.paralelo_id == otro.paralelo_id:
                errores.setdefault("paralelo", []).append(
                    f"El grupo ya tiene clases en ese intervalo "
                    f"({referencia})."
                )

        if errores:
            raise ValidationError(errores)
        
        
    @staticmethod
    def _bloques_por_semana(horario, desde=None, hasta=None):
        """Devuelve la semana y duración de cada clase del periodo."""
        periodo = horario.paralelo.periodo

        inicio = periodo.fecha_inicio
        fin = periodo.fecha_fin

        if desde is not None:
            inicio = max(inicio, desde)

        if hasta is not None:
            fin = min(fin, hasta)

        if inicio > fin:
            return

        primera_fecha = inicio + timedelta(
            days=(horario.dia - inicio.isoweekday()) % 7,
        )

        duracion = (
            datetime.combine(inicio, horario.hora_fin)
            - datetime.combine(inicio, horario.hora_inicio)
        )

        fecha = primera_fecha

        while fecha <= fin:
            lunes = fecha - timedelta(days=fecha.weekday())
            yield lunes, duracion
            fecha += timedelta(days=7)

    def _validar_carga_docente(self, adicionales=(), desde=None):
        if not self.docente_id or not self.paralelo_id:
            return

        try:
            docente = self.docente
            semanas = dict(
                self._bloques_por_semana(self, desde=desde)
            )
        except ObjectDoesNotExist:
            return

        if not semanas:
            return

        inicio = min(semanas)
        fin = max(semanas) + timedelta(days=6)

        existentes = (
            type(self).objects
            .filter(
                docente_id=self.docente_id,
                paralelo__periodo__fecha_inicio__lte=fin,
                paralelo__periodo__fecha_fin__gte=inicio,
            )
            .select_related("paralelo__periodo")
        )

        if self.pk is not None:
            existentes = existentes.exclude(pk=self.pk)

        candidatos = (
            otro
            for otro in adicionales
            if otro is not self
            and otro.docente_id == self.docente_id
        )

        for otro in chain(existentes, candidatos):
            for lunes, duracion in self._bloques_por_semana(
                otro,
                desde=inicio,
                hasta=fin,
            ):
                if lunes in semanas:
                    semanas[lunes] += duracion

        limite = timedelta(hours=docente.horas_semanales_max)

        for lunes, total in sorted(semanas.items()):
            if total > limite:
                horas = total.total_seconds() / 3600

                raise ValidationError({
                    "docente": (
                        f"La semana que comienza el {lunes:%d/%m/%Y} "
                        f"sumaría {horas:.2f} horas. "
                        f"El máximo del docente es "
                        f"{docente.horas_semanales_max} horas semanales."
                    ),
                })
                
    def validar_para_propuesta(self):
        """Valida el candidato sin guardarlo."""
        self.full_clean()
        ValidadorFranjaParalelo.validar(self)

        if not self.asignatura.activo:
            raise ValidationError({
                "asignatura": (
                    "La asignatura está retirada del catálogo activo."
                ),
            })

        if not self.docente.activo:
            raise ValidationError({
                "docente": "El docente está retirado del catálogo activo.",
            })

        if not self.aula.activo:
            raise ValidationError({
                "aula": "El aula está retirada del catálogo activo.",
            })
            
        periodo = self.paralelo.periodo

        primera_fecha = periodo.fecha_inicio + timedelta(
            days=(
                self.dia - periodo.fecha_inicio.isoweekday()
            ) % 7,
        )

        if primera_fecha > periodo.fecha_fin:
            raise ValidationError({
                "dia": "El periodo no contiene ninguna fecha de ese día.",
            })

        franjas = FranjaPlanificacion.objects.filter(
            periodo=periodo,
            dia=self.dia,
            activo=True,
        )
        disponibilidades = DisponibilidadDocente.objects.filter(
            docente_id=self.docente_id,
            periodo=periodo,
            dia=self.dia,
            activo=True,
        )

        errores = {}

        if not self._cubre_intervalo(
            franjas,
            self.hora_inicio,
            self.hora_fin,
        ):
            errores["hora_inicio"] = (
                "La clase no cabe completamente en las franjas "
                "de planificación activas."
            )

        if not self._cubre_intervalo(
            disponibilidades,
            self.hora_inicio,
            self.hora_fin,
        ):
            errores["docente"] = (
                "El docente no tiene disponibilidad activa "
                "para todo el intervalo."
            )

        if errores:
            raise ValidationError(errores)

    @staticmethod
    def _cubre_intervalo(ventanas, inicio, fin):
        """Comprueba cobertura continua, sin huecos."""
        cubierto_hasta = inicio

        for desde, hasta in ventanas.order_by(
            "hora_inicio",
            "hora_fin",
        ).values_list("hora_inicio", "hora_fin"):
            if hasta <= cubierto_hasta:
                continue

            if desde > cubierto_hasta:
                return False

            cubierto_hasta = hasta

            if cubierto_hasta >= fin:
                return True

        return False

    @property
    def periodo(self):
        return self.paralelo.periodo

    def __str__(self):
        return (
            f"{self.asignatura.codigo} · "
            f"{self.paralelo.nombre} · "
            f"{self.get_dia_display()} "
            f"{self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M}"
        )
        
        
        
class NecesidadClase(models.Model):
    """Clases semanales que se necesita programar para un grupo."""

    asignatura = models.ForeignKey(
        "academico.Asignatura",
        on_delete=models.PROTECT,
        related_name="necesidades_clase",
    )
    docente = models.ForeignKey(
        "usuarios.PerfilDocente",
        on_delete=models.PROTECT,
        related_name="necesidades_clase",
    )
    paralelo = models.ForeignKey(
        "academico.Paralelo",
        on_delete=models.PROTECT,
        related_name="necesidades_clase",
    )
    sesiones_semanales = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    duracion_minutos = models.PositiveSmallIntegerField(
        default=60,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(1439),
        ],
        help_text="Duración de cada sesión, en minutos.",
    )
    prefiere_laboratorio = models.BooleanField(
        default=False,
        help_text=(
            "El generador priorizará laboratorios, "
            "pero podrá proponer un aula común."
        ),
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("paralelo", "asignatura", "docente")
        verbose_name = "necesidad de clase"
        verbose_name_plural = "necesidades de clases"
        constraints = [
            models.UniqueConstraint(
                fields=("asignatura", "docente", "paralelo"),
                name="necesidad_unica_asignatura_docente_grupo",
            ),
            models.CheckConstraint(
                condition=models.Q(sesiones_semanales__gte=1),
                name="necesidad_sesiones_positivas",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    duracion_minutos__gte=1,
                    duracion_minutos__lte=1439,
                ),
                name="necesidad_duracion_valida",
            ),
        ]

    @property
    def minutos_semanales(self):
        return self.sesiones_semanales * self.duracion_minutos

    def __str__(self):
        return (
            f"{self.asignatura.codigo} · "
            f"{self.paralelo.nombre} · "
            f"{self.sesiones_semanales} sesiones "
            f"de {self.duracion_minutos} min"
        )
        
        
class FranjaPlanificacion(models.Model):
    """Ventana semanal en la que se pueden programar clases."""

    periodo = models.ForeignKey(
        "academico.PeriodoAcademico",
        on_delete=models.PROTECT,
        related_name="franjas_planificacion",
    )
    dia = models.PositiveSmallIntegerField(
        choices=Horario.Dia.choices,
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("periodo", "dia", "hora_inicio")
        verbose_name = "franja de planificación"
        verbose_name_plural = "franjas de planificación"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    hora_fin__gt=models.F("hora_inicio"),
                ),
                name="franja_plan_fin_posterior_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(dia__gte=1, dia__lte=7),
                name="franja_plan_dia_valido",
            ),
            models.UniqueConstraint(
                fields=(
                    "periodo",
                    "dia",
                    "hora_inicio",
                    "hora_fin",
                ),
                name="franja_plan_unica_por_periodo",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.hora_inicio is not None
            and self.hora_fin is not None
            and self.hora_fin <= self.hora_inicio
        ):
            raise ValidationError({
                "hora_fin": (
                    "La hora de fin debe ser posterior "
                    "a la hora de inicio."
                ),
            })

    def __str__(self):
        return (
            f"{self.periodo.codigo} · "
            f"{self.get_dia_display()} · "
            f"{self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M}"
        )
        
class FranjaParalelo(models.Model):
    """Intervalo semanal en el que un paralelo puede recibir clases."""

    paralelo = models.ForeignKey(
        "academico.Paralelo",
        on_delete=models.PROTECT,
        related_name="franjas_clase",
    )
    dia = models.PositiveSmallIntegerField(
        choices=Horario.Dia.choices,
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("paralelo", "dia", "hora_inicio", "pk")
        verbose_name = "franja de paralelo"
        verbose_name_plural = "franjas de paralelos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    hora_fin__gt=models.F("hora_inicio"),
                ),
                name="franja_par_fin_posterior_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(dia__gte=1, dia__lte=7),
                name="franja_par_dia_valido",
            ),
            models.UniqueConstraint(
                fields=(
                    "paralelo",
                    "dia",
                    "hora_inicio",
                    "hora_fin",
                ),
                name="franja_par_intervalo_unico",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.hora_inicio is not None
            and self.hora_fin is not None
            and self.hora_fin <= self.hora_inicio
        ):
            raise ValidationError({
                "hora_fin": (
                    "La hora de fin debe ser posterior "
                    "a la hora de inicio."
                ),
            })

    def __str__(self):
        return (
            f"{self.paralelo} · "
            f"{self.get_dia_display()} · "
            f"{self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M}"
        )
        
class DisponibilidadDocente(models.Model):
    """Ventana semanal de disponibilidad de un docente."""

    docente = models.ForeignKey(
        "usuarios.PerfilDocente",
        on_delete=models.PROTECT,
        related_name="disponibilidades",
    )
    periodo = models.ForeignKey(
        "academico.PeriodoAcademico",
        on_delete=models.PROTECT,
        related_name="disponibilidades_docentes",
    )
    dia = models.PositiveSmallIntegerField(
        choices=Horario.Dia.choices,
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("docente", "periodo", "dia", "hora_inicio")
        verbose_name = "disponibilidad docente"
        verbose_name_plural = "disponibilidades docentes"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    hora_fin__gt=models.F("hora_inicio"),
                ),
                name="disp_docente_fin_posterior_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(dia__gte=1, dia__lte=7),
                name="disp_docente_dia_valido",
            ),
            models.UniqueConstraint(
                fields=(
                    "docente",
                    "periodo",
                    "dia",
                    "hora_inicio",
                    "hora_fin",
                ),
                name="disp_docente_unica_por_periodo",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.hora_inicio is not None
            and self.hora_fin is not None
            and self.hora_fin <= self.hora_inicio
        ):
            raise ValidationError({
                "hora_fin": (
                    "La hora de fin debe ser posterior "
                    "a la hora de inicio."
                ),
            })

    def __str__(self):
        return (
            f"{self.docente} · "
            f"{self.periodo.codigo} · "
            f"{self.get_dia_display()} "
            f"{self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M}"
        )
        
        
class PropuestaHorario(models.Model):
    """Borrador de planificación que requiere revisión."""

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        EN_REVISION = "EN_REVISION", "En revisión"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    nombre = models.CharField(max_length=150)
    periodo = models.ForeignKey(
        "academico.PeriodoAcademico",
        on_delete=models.PROTECT,
        related_name="propuestas_horario",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="propuestas_horario",
    )
    
    necesidades = models.ManyToManyField(
        NecesidadClase,
        related_name="propuestas",
        blank=True,
        help_text="Necesidades que esta propuesta debe cubrir.",
    )
    
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        editable=False,
    )
    
    aprobada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="propuestas_horario_aprobadas",
        null=True,
        blank=True,
        editable=False,
    )
    aprobada_en = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )
    
    diagnostico_generacion = models.JSONField(
        default=dict,
        blank=True,
        editable=False,
        help_text="Resultado de la búsqueda automática original.",
    )
    
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-creada_en", "-pk")
        verbose_name = "propuesta de horario"
        verbose_name_plural = "propuestas de horarios"
        permissions = [
            (
                "aprobar_propuestahorario",
                "Puede aprobar propuestas de horarios",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    estado__in=(
                        "BORRADOR",
                        "EN_REVISION",
                        "APROBADA",
                        "RECHAZADA",
                    ),
                ),
                name="propuesta_estado_valido",
            ),
        ]

    def clean(self):
        super().clean()

        self.nombre = " ".join((self.nombre or "").split())

        if not self.nombre:
            raise ValidationError({
                "nombre": "El nombre de la propuesta es obligatorio.",
            })
            
    def validar_bloques(self):
        """Valida los bloques existentes sin publicarlos."""
        self.full_clean()

        if self.pk is None:
            raise ValidationError(
                "Guarda la propuesta antes de validar sus bloques."
            )

        bloques = list(
            self.bloques.select_related(
                "propuesta__periodo",
                "necesidad__asignatura",
                "necesidad__docente__usuario",
                "necesidad__paralelo__periodo",
                "aula",
            )
        )

        if not bloques:
            raise ValidationError(
                "La propuesta no contiene bloques."
            )

        candidatos = []

        for bloque in bloques:
            try:
                bloque.full_clean()

                if not bloque.necesidad.activo:
                    raise ValidationError(
                        "La necesidad de clase está inactiva."
                    )

                candidato = bloque.como_horario()
                candidato.validar_para_propuesta()

            except ValidationError as error:
                raise ValidationError(
                    f"Bloque #{bloque.pk}: "
                    + "; ".join(error.messages)
                ) from error

            candidatos.append(candidato)

        for indice, primero in enumerate(candidatos):
            for segundo_indice in range(indice + 1, len(candidatos)):
                segundo = candidatos[segundo_indice]

                se_cruzan = (
                    primero.dia == segundo.dia
                    and primero.hora_inicio < segundo.hora_fin
                    and segundo.hora_inicio < primero.hora_fin
                )

                if not se_cruzan:
                    continue

                recursos = []

                if primero.docente_id == segundo.docente_id:
                    recursos.append("docente")

                if primero.aula_id == segundo.aula_id:
                    recursos.append("aula")

                if primero.paralelo_id == segundo.paralelo_id:
                    recursos.append("grupo")

                if recursos:
                    raise ValidationError(
                        f"Los bloques #{bloques[indice].pk} y "
                        f"#{bloques[segundo_indice].pk} se cruzan "
                        f"y comparten: {', '.join(recursos)}."
                    )

        for candidato in candidatos:
            candidato._validar_carga_docente(
                adicionales=candidatos,
            )

    def __str__(self):
        return (
            f"{self.nombre} · "
            f"{self.periodo.codigo} · "
            f"{self.get_estado_display()}"
        )
        
    def validar_alcance(self):
        """Comprueba qué necesidades abarca la propuesta."""
        if self.pk is None:
            raise ValidationError(
                "Guarda la propuesta antes de definir su alcance."
            )

        necesidades = list(
            self.necesidades.select_related("paralelo")
        )

        if not necesidades:
            raise ValidationError(
                "Selecciona al menos una necesidad para la propuesta."
            )

        errores = []

        for necesidad in necesidades:
            if necesidad.paralelo.periodo_id != self.periodo_id:
                errores.append(
                    f"La necesidad #{necesidad.pk} pertenece "
                    "a otro periodo."
                )

            if not necesidad.activo:
                errores.append(
                    f"La necesidad #{necesidad.pk} está inactiva."
                )

        seleccionadas = {
            necesidad.pk for necesidad in necesidades
        }

        fuera_del_alcance = (
            self.bloques
            .exclude(necesidad_id__in=seleccionadas)
            .exists()
        )

        if fuera_del_alcance:
            errores.append(
                "Hay bloques de necesidades que no están "
                "seleccionadas en esta propuesta."
            )

        if errores:
            raise ValidationError(errores)

    def obtener_pendientes(self):
        """Devuelve las sesiones seleccionadas que aún no tienen bloque."""
        self.validar_alcance()

        presentes = set(
            self.bloques.values_list(
                "necesidad_id",
                "numero_sesion",
            )
        )

        pendientes = []

        necesidades = self.necesidades.select_related(
            "asignatura",
            "paralelo",
        ).order_by("pk")

        for necesidad in necesidades:
            faltantes = [
                numero
                for numero in range(
                    1,
                    necesidad.sesiones_semanales + 1,
                )
                if (necesidad.pk, numero) not in presentes
            ]

            if faltantes:
                pendientes.append({
                    "necesidad_id": necesidad.pk,
                    "descripcion": str(necesidad),
                    "sesiones": faltantes,
                })

        return pendientes

    def validar_completa(self):
        """Exige cobertura completa y bloques válidos."""
        self.full_clean()
        pendientes = self.obtener_pendientes()

        if pendientes:
            raise ValidationError([
                (
                    f"{pendiente['descripcion']}: faltan "
                    "las sesiones "
                    + ", ".join(
                        str(numero)
                        for numero in pendiente["sesiones"]
                    )
                    + "."
                )
                for pendiente in pendientes
            ])

        self.validar_bloques()
        
        
class BloquePropuesta(models.Model):
    """Sesión provisional de una necesidad de clase."""

    propuesta = models.ForeignKey(
        PropuestaHorario,
        on_delete=models.CASCADE,
        related_name="bloques",
    )
    necesidad = models.ForeignKey(
        NecesidadClase,
        on_delete=models.PROTECT,
        related_name="bloques_propuesta",
    )
    numero_sesion = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    aula = models.ForeignKey(
        "academico.Aula",
        on_delete=models.PROTECT,
        related_name="bloques_propuesta",
    )
    dia = models.PositiveSmallIntegerField(
        choices=Horario.Dia.choices,
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        ordering = ("dia", "hora_inicio", "pk")
        verbose_name = "bloque de propuesta"
        verbose_name_plural = "bloques de propuestas"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    hora_fin__gt=models.F("hora_inicio"),
                ),
                name="bloque_prop_fin_posterior_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(dia__gte=1, dia__lte=7),
                name="bloque_prop_dia_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(numero_sesion__gte=1),
                name="bloque_prop_sesion_positiva",
            ),
            models.UniqueConstraint(
                fields=("propuesta", "necesidad", "numero_sesion"),
                name="bloque_prop_sesion_unica",
            ),
        ]

    def clean(self):
        super().clean()

        errores = {}

        if self.hora_inicio is not None and self.hora_fin is not None:
            if self.hora_fin <= self.hora_inicio:
                errores["hora_fin"] = (
                    "La hora de fin debe ser posterior "
                    "a la hora de inicio."
                )

        if self.propuesta_id and self.necesidad_id:
            try:
                propuesta = self.propuesta
                necesidad = self.necesidad
            except ObjectDoesNotExist:
                # full_clean() informará del campo relacionado inválido.
                return

            if propuesta.periodo_id != necesidad.paralelo.periodo_id:
                errores["necesidad"] = (
                    "La necesidad pertenece a otro periodo académico."
                )

            if (
                self.numero_sesion is not None
                and self.numero_sesion > necesidad.sesiones_semanales
            ):
                errores["numero_sesion"] = (
                    "El número de sesión supera la cantidad "
                    "solicitada en la necesidad."
                )

            if (
                self.hora_inicio is not None
                and self.hora_fin is not None
                and self.hora_fin > self.hora_inicio
            ):
                fecha = propuesta.periodo.fecha_inicio
                duracion = (
                    datetime.combine(fecha, self.hora_fin)
                    - datetime.combine(fecha, self.hora_inicio)
                )

                if duracion != timedelta(
                    minutes=necesidad.duracion_minutos,
                ):
                    errores["hora_fin"] = (
                        "La duración debe coincidir con los "
                        f"{necesidad.duracion_minutos} minutos "
                        "solicitados."
                    )

        if errores:
            raise ValidationError(errores)

    def como_horario(self):
        """Construye un candidato en memoria; no valida ni guarda."""
        return Horario(
            asignatura=self.necesidad.asignatura,
            docente=self.necesidad.docente,
            paralelo=self.necesidad.paralelo,
            aula=self.aula,
            dia=self.dia,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
        )

    def __str__(self):
        return (
            f"{self.necesidad.asignatura.codigo} · "
            f"Sesión {self.numero_sesion} · "
            f"{self.get_dia_display()} "
            f"{self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M}"
        )
        
        
class RetiradaPublicacion(models.Model):
    propuesta = models.ForeignKey(
        PropuestaHorario,
        on_delete=models.PROTECT,
        related_name="retiradas",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="retiradas_publicacion",
    )
    motivo = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    datos_publicacion = models.JSONField()

    class Meta:
        ordering = ("-fecha", "-pk")
        verbose_name = "retirada de publicación"
        verbose_name_plural = "retiradas de publicaciones"

    def __str__(self):
        return f"Propuesta #{self.propuesta_id} · {self.fecha}"