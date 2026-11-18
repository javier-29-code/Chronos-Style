from django import forms

from academico.models import PeriodoAcademico, Aula, Asignatura, Paralelo, ProgramaAcademico, Inscripcion

from usuarios.models import PerfilDocente, PerfilEstudiante

from .models import (
    NecesidadClase,
    DisponibilidadDocente,
    FranjaPlanificacion,
    BloquePropuesta,
    Horario,
    FranjaParalelo
)

class GenerarPropuestaForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre de la propuesta",
        max_length=150,
    )
    periodo = forms.ModelChoiceField(
        queryset=PeriodoAcademico.objects.none(),
        widget=forms.HiddenInput,
    )
    necesidades = forms.ModelMultipleChoiceField(
        label="Clases que se deben programar",
        queryset=NecesidadClase.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    paso_minutos = forms.IntegerField(
        label="Paso de búsqueda en minutos",
        min_value=1,
        max_value=1440,
        initial=15,
        help_text="Con 15, se prueban comienzos separados por 15 minutos.",
    )

    def __init__(self, *args, periodo=None, **kwargs):
        super().__init__(*args, **kwargs)

        if periodo is not None:
            self.fields["periodo"].queryset = (
                PeriodoAcademico.objects.filter(pk=periodo.pk)
            )
            self.fields["periodo"].initial = periodo.pk

            self.fields["necesidades"].queryset = (
                NecesidadClase.objects.filter(
                    paralelo__periodo=periodo,
                    activo=True,
                    asignatura__activo=True,
                    docente__usuario__is_active=True,
                    paralelo__programa__activo=True,
                )
                .select_related(
                    "asignatura",
                    "docente__usuario",
                    "paralelo__periodo",
                )
                .order_by("paralelo__nombre", "asignatura__nombre")
            )
            

class EditarBloqueForm(forms.ModelForm):
    class Meta:
        model = BloquePropuesta
        fields = ("aula", "dia", "hora_inicio", "hora_fin")
        widgets = {
            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
            "hora_fin": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["aula"].queryset = (
            Aula.objects.filter(activo=True).order_by("codigo")
        )
        
class MoverBloqueForm(forms.Form):
    dia = forms.TypedChoiceField(
        choices=Horario.Dia.choices, coerce=int, label="Día"
    )
    hora_inicio = forms.TimeField(
        label="Hora de inicio",
        widget=forms.TimeInput(attrs={"type": "time", "step": "any"}),
    )
    aula = forms.ModelChoiceField(
        queryset=Aula.objects.filter(activo=True).order_by("codigo"),
        required=False,
        empty_label="Conservar aula actual",
    )


class RetirarPublicacionForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo de la corrección",
        min_length=10,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    confirmar = forms.BooleanField(
        label=(
            "Confirmo que se retirarán todos los horarios oficiales "
            "de esta propuesta."
        ),
        required=True,
    )
    
class NuevaAulaForm(forms.ModelForm):
    class Meta:
        model = Aula
        fields = (
            "codigo",
            "nombre",
            "tipo",
            "ubicacion",
            "capacidad",
            "tiene_proyector",
            "tiene_pantalla_tactil",
            "cantidad_computadoras",
            "equipamiento",
            "activo",
        )
        widgets = {
            "equipamiento": forms.Textarea(attrs={"rows": 3}),
        }


class NuevoDocenteForm(forms.Form):
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
    )
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    titulo = forms.CharField(label="Título", max_length=150)
    area = forms.CharField(label="Área", max_length=150)
    horas_semanales_max = forms.IntegerField(
        label="Máximo de horas semanales",
        min_value=1,
        max_value=40,
        initial=20,
    )
    

class NecesidadClaseForm(forms.ModelForm):
    class Meta:
        model = NecesidadClase
        fields = (
            "asignatura",
            "docente",
            "paralelo",
            "sesiones_semanales",
            "duracion_minutos",
            "prefiere_laboratorio",
            "tipo_aula_preferida",
            "activo",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["asignatura"].queryset = (
            Asignatura.objects.filter(activo=True)
        )
        self.fields["docente"].queryset = (
            PerfilDocente.objects.filter(
                activo=True,
                usuario__is_active=True,
            ).select_related("usuario")
        )
        self.fields["paralelo"].queryset = (
            Paralelo.objects.filter(
                programa__activo=True,
            ).select_related("programa", "periodo")
        )


class DisponibilidadDocenteForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadDocente
        fields = (
            "docente",
            "periodo",
            "dia",
            "hora_inicio",
            "hora_fin",
            "activo",
        )
        widgets = {
            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
            "hora_fin": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["docente"].queryset = (
            PerfilDocente.objects.filter(
                activo=True,
                usuario__is_active=True,
            ).select_related("usuario")
        )


class FranjaPlanificacionForm(forms.ModelForm):
    class Meta:
        model = FranjaPlanificacion
        fields = (
            "periodo",
            "dia",
            "hora_inicio",
            "hora_fin",
            "activo",
        )
        widgets = {
            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
            "hora_fin": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
        }
        
        
class AgregarSesionForm(forms.Form):
    sesion = forms.ChoiceField(label="Sesión pendiente")
    aula = forms.ModelChoiceField(
        label="Aula",
        queryset=Aula.objects.filter(activo=True).order_by("codigo"),
    )
    dia = forms.TypedChoiceField(
        label="Día",
        choices=Horario.Dia.choices,
        coerce=int,
    )
    hora_inicio = forms.TimeField(
        label="Hora de inicio",
        widget=forms.TimeInput(
            format="%H:%M",
            attrs={"type": "time"},
        ),
        help_text=(
            "La hora final se calcula con la duración "
            "registrada en la necesidad."
        ),
    )

    def __init__(self, *args, pendientes=(), **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["sesion"].choices = [
            ("", "Selecciona una sesión"),
            *[
                (
                    f"{pendiente['necesidad_id']}:{numero}",
                    f"{pendiente['descripcion']} · Sesión {numero}",
                )
                for pendiente in pendientes
                for numero in pendiente["sesiones"]
            ],
        ]
        
        
class FiltroHorarioForm(forms.Form):
    periodo = forms.ModelChoiceField(
        label="Periodo académico",
        queryset=PeriodoAcademico.objects.none(),
    )
    docente = forms.ModelChoiceField(
        label="Docente",
        queryset=PerfilDocente.objects.none(),
        required=False,
        empty_label="Todos los docentes",
    )
    aula = forms.ModelChoiceField(
        label="Aula",
        queryset=Aula.objects.none(),
        required=False,
        empty_label="Todas las aulas",
    )
    paralelo = forms.ModelChoiceField(
        label="Paralelo/Curso",
        queryset=Paralelo.objects.none(),
        required=False,
        empty_label="Todos los paralelos",
    )

    def __init__(
        self,
        *args,
        periodos,
        horarios_autorizados,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.fields["periodo"].queryset = periodos

        periodo = None

        if self.is_bound:
            try:
                periodo = self.fields["periodo"].clean(
                    self.data.get("periodo")
                )
            except forms.ValidationError:
                pass

        opciones = horarios_autorizados.none()

        if periodo is not None:
            opciones = horarios_autorizados.filter(
                paralelo__periodo=periodo,
            )

        self.fields["docente"].queryset = (
            PerfilDocente.objects.filter(
                pk__in=opciones.values("docente_id")
            )
            .select_related("usuario")
            .order_by("usuario__last_name", "usuario__first_name", "pk")
        )
        self.fields["aula"].queryset = Aula.objects.filter(
            pk__in=opciones.values("aula_id")
        ).order_by("codigo")

        self.fields["paralelo"].queryset = (
            Paralelo.objects.filter(
                pk__in=opciones.values("paralelo_id")
            )
            .select_related("programa", "periodo")
            .order_by("nombre", "pk")
        )
        
        
class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ("codigo", "nombre", "activo")
        
        
class PeriodoAcademicoForm(forms.ModelForm):
    class Meta:
        model = PeriodoAcademico
        fields = (
            "codigo",
            "nombre",
            "fecha_inicio",
            "fecha_fin",
        )
        widgets = {
            "fecha_inicio": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "fecha_fin": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }
        
        
class ParaleloForm(forms.ModelForm):
    class Meta:
        model = Paralelo
        fields = ("programa", "periodo", "nombre")
        labels = {
            "nombre": "Nombre del paralelo/curso",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["programa"].queryset = (
            ProgramaAcademico.objects.filter(activo=True)
            .order_by("nombre")
        )
        self.fields["periodo"].queryset = (
            PeriodoAcademico.objects.order_by("-fecha_inicio")
        )
        
        
class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ("estudiante", "paralelo")
        labels = {
            "paralelo": "Paralelo/Curso",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["estudiante"].queryset = (
            PerfilEstudiante.objects.filter(
                usuario__is_active=True,
            )
            .select_related("usuario", "programa")
            .order_by("usuario__last_name", "usuario__first_name", "pk")
        )
        self.fields["paralelo"].queryset = (
            Paralelo.objects.select_related("programa", "periodo")
            .order_by("-periodo__fecha_inicio", "nombre", "pk")
        )
        
        
class EditarDocenteForm(forms.ModelForm):
    class Meta:
        model = PerfilDocente
        fields = ("titulo", "area", "horas_semanales_max")
        labels = {
            "titulo": "Título",
            "area": "Área académica",
            "horas_semanales_max": "Máximo de horas semanales",
        }
        
class FranjaParaleloForm(forms.ModelForm):
    class Meta:
        model = FranjaParalelo
        fields = ("dia", "hora_inicio", "hora_fin", "activo")
        labels = {
            "dia": "Día",
            "hora_inicio": "Hora de inicio",
            "hora_fin": "Hora de fin",
            "activo": "Franja activa",
        }
        widgets = {
            "hora_inicio": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
            "hora_fin": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
        }

    def __init__(self, *args, paralelo, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.paralelo = paralelo

    def clean(self):
        datos = super().clean()

        dia = datos.get("dia")
        inicio = datos.get("hora_inicio")
        fin = datos.get("hora_fin")

        if dia is not None and inicio is not None and fin is not None:
            repetidas = FranjaParalelo.objects.filter(
                paralelo=self.instance.paralelo,
                dia=dia,
                hora_inicio=inicio,
                hora_fin=fin,
            )

            if self.instance.pk:
                repetidas = repetidas.exclude(pk=self.instance.pk)

            if repetidas.exists():
                raise forms.ValidationError(
                    "Ya existe una franja con ese día e intervalo "
                    "en este Paralelo/Curso."
                )

        return datos
    
class ReintentarPendientesForm(forms.Form):
    paso_minutos = forms.IntegerField(
        label="Paso de búsqueda en minutos",
        min_value=1,
        max_value=1440,
        initial=15,
        help_text=(
            "Un paso menor prueba más horas de inicio "
            "y puede tardar más."
        ),
    )
    
class ProgramaAcademicoForm(forms.ModelForm):
    class Meta:
        model = ProgramaAcademico
        fields = ("codigo", "nombre", "nivel", "activo")
        labels = {
            "codigo": "Código",
            "nombre": "Nombre del programa",
            "nivel": "Nivel",
            "activo": "Programa activo",
        }

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip().upper()

        if any(caracter.isspace() for caracter in codigo):
            raise forms.ValidationError(
                "El código no puede contener espacios."
            )

        return codigo

    def clean_nombre(self):
        return " ".join(self.cleaned_data["nombre"].split())