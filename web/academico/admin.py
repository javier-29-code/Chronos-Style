from django.contrib import admin

from .models import (
    ProgramaAcademico,
    PeriodoAcademico,
    Paralelo,
    Inscripcion,
    Asignatura,
    Aula,
)


@admin.register(ProgramaAcademico)
class ProgramaAcademicoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "nivel", "activo")
    search_fields = ("codigo", "nombre")
    list_filter = ("nivel", "activo")


@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "fecha_inicio",
        "fecha_fin",
    )
    search_fields = ("codigo", "nombre")
    ordering = ("-fecha_inicio",)


@admin.register(Paralelo)
class ParaleloAdmin(admin.ModelAdmin):
    list_display = ("nombre", "programa", "periodo")
    list_filter = ("periodo", "programa")
    search_fields = (
        "nombre",
        "programa__codigo",
        "programa__nombre",
        "periodo__codigo",
    )
    list_select_related = ("programa", "periodo")
    autocomplete_fields = ("programa", "periodo")


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = (
        "estudiante",
        "paralelo",
        "fecha_inscripcion",
    )
    list_filter = (
        "paralelo__periodo",
        "paralelo__programa",
    )
    search_fields = (
        "estudiante__usuario__username",
        "estudiante__usuario__first_name",
        "estudiante__usuario__last_name",
        "paralelo__nombre",
    )
    list_select_related = (
        "estudiante__usuario",
        "paralelo__programa",
        "paralelo__periodo",
    )
    autocomplete_fields = ("estudiante", "paralelo")
    readonly_fields = ("fecha_inscripcion",)
    
@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activo")
    search_fields = ("codigo", "nombre")
    list_filter = ("activo",)
    
@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "tipo",
        "capacidad",
        "cantidad_computadoras",
        "tiene_proyector",
        "tiene_pantalla_tactil",
        "activo",
    )
    search_fields = ("codigo", "nombre", "ubicacion", "equipamiento")
    list_filter = (
        "tipo",
        "activo",
        "tiene_proyector",
        "tiene_pantalla_tactil",
    )
    fieldsets = (
        ("Identificación", {
            "fields": ("codigo", "nombre", "tipo", "ubicacion", "activo"),
        }),
        ("Capacidad y equipamiento", {
            "fields": (
                "capacidad",
                "tiene_proyector",
                "tiene_pantalla_tactil",
                "cantidad_computadoras",
                "equipamiento",
            ),
        }),
    )