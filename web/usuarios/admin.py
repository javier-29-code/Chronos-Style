# Register your models here.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Usuario,
    PerfilDocente,
    PerfilEstudiante,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )


@admin.register(PerfilDocente)
class PerfilDocenteAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "titulo",
        "area",
        "horas_semanales_max",
    )
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
        "area",
    )
    list_select_related = ("usuario",)
    autocomplete_fields = ("usuario",)


@admin.register(PerfilEstudiante)
class PerfilEstudianteAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "programa",
        "semestre",
    )
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
    )
    list_filter = ("programa", "semestre")
    list_select_related = ("usuario", "programa")
    autocomplete_fields = ("usuario", "programa")


admin.site.site_header = "Administración de Chronos-Style"
admin.site.site_title = "Chronos-Style"
admin.site.index_title = "Gestión del sistema"