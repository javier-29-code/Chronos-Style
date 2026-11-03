# Register your models here.

from django.contrib import admin

from .models import (
    Horario,
    NecesidadClase,
    FranjaPlanificacion,
    DisponibilidadDocente,
    PropuestaHorario,
    BloquePropuesta
)

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = (
        "asignatura",
        "docente",
        "paralelo",
        "aula",
        "dia",
        "hora_inicio",
        "hora_fin",
    )
    list_filter = (
        "paralelo__periodo",
        "dia",
        "paralelo__programa",
    )
    search_fields = (
        "asignatura__codigo",
        "asignatura__nombre",
        "docente__usuario__username",
        "docente__usuario__first_name",
        "docente__usuario__last_name",
        "aula__codigo",
        "paralelo__nombre",
    )
    autocomplete_fields = (
        "asignatura",
        "docente",
        "aula",
        "paralelo",
    )
    list_select_related = (
        "asignatura",
        "docente__usuario",
        "aula",
        "paralelo__programa",
        "paralelo__periodo",
    )
    
@admin.register(NecesidadClase)
class NecesidadClaseAdmin(admin.ModelAdmin):
    list_display = (
        "asignatura",
        "docente",
        "paralelo",
        "sesiones_semanales",
        "duracion_minutos",
        "prefiere_laboratorio",
        "activo",
    )
    list_filter = (
        "paralelo__periodo",
        "prefiere_laboratorio",
        "activo",
    )
    search_fields = (
        "asignatura__codigo",
        "asignatura__nombre",
        "docente__usuario__username",
        "docente__usuario__first_name",
        "docente__usuario__last_name",
        "paralelo__nombre",
    )
    autocomplete_fields = ("asignatura", "docente", "paralelo")
    list_select_related = (
        "asignatura",
        "docente__usuario",
        "paralelo__programa",
        "paralelo__periodo",
    )
    
@admin.register(FranjaPlanificacion)
class FranjaPlanificacionAdmin(admin.ModelAdmin):
    list_display = (
        "periodo",
        "dia",
        "hora_inicio",
        "hora_fin",
        "activo",
    )
    list_filter = ("periodo", "dia", "activo")
    search_fields = ("periodo__codigo", "periodo__nombre")
    autocomplete_fields = ("periodo",)
    list_select_related = ("periodo",)
    
    
@admin.register(DisponibilidadDocente)
class DisponibilidadDocenteAdmin(admin.ModelAdmin):
    list_display = (
        "docente",
        "periodo",
        "dia",
        "hora_inicio",
        "hora_fin",
        "activo",
    )
    list_filter = ("periodo", "dia", "activo")
    search_fields = (
        "docente__usuario__username",
        "docente__usuario__first_name",
        "docente__usuario__last_name",
        "periodo__codigo",
    )
    autocomplete_fields = ("docente", "periodo")
    list_select_related = ("docente__usuario", "periodo")
    
    
@admin.register(PropuestaHorario)
class PropuestaHorarioAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "periodo",
        "estado",
        "autor",
        "creada_en",
    )
    list_filter = ("periodo", "estado")
    search_fields = (
        "nombre",
        "periodo__codigo",
        "autor__username",
    )
    autocomplete_fields = ("periodo", "autor", "necesidades")
    readonly_fields = (
        "estado",
        "aprobada_por",
        "aprobada_en",
        "creada_en",
        "actualizada_en",
    )
    list_select_related = ("periodo", "autor")
    
    
@admin.register(BloquePropuesta)
class BloquePropuestaAdmin(admin.ModelAdmin):
    list_display = (
        "propuesta",
        "necesidad",
        "numero_sesion",
        "aula",
        "dia",
        "hora_inicio",
        "hora_fin",
    )
    list_filter = ("propuesta", "dia")
    search_fields = (
        "propuesta__nombre",
        "necesidad__asignatura__codigo",
        "necesidad__asignatura__nombre",
        "necesidad__paralelo__nombre",
        "aula__codigo",
    )
    autocomplete_fields = ("propuesta", "necesidad", "aula")
    list_select_related = (
        "propuesta__periodo",
        "necesidad__asignatura",
        "necesidad__docente__usuario",
        "necesidad__paralelo",
        "aula",
    )