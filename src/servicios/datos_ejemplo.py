"""Catálogos de demostración para probar la interfaz."""

from modelos.asignatura import Asignatura
from modelos.aula import Aula
from servicios.gestor_catalogos import GestorCatalogos


def crear_catalogos_con_datos_ejemplo(docentes):
    """Recibe los docentes existentes para reutilizar sus objetos."""
    catalogos = GestorCatalogos()

    for docente in docentes:
        catalogos.agregar_docente(docente)

    catalogos.agregar_asignatura(
        Asignatura(
            codigo="POO",
            nombre="Programación Orientada a Objetos",
            creditos=3,
            horas_semanales=4,
        )
    )

    catalogos.agregar_asignatura(
        Asignatura(
            codigo="BD",
            nombre="Base de Datos",
            creditos=3,
            horas_semanales=4,
        )
    )

    catalogos.agregar_aula(
        Aula(
            id_aula="A101",
            edificio="Edificio A",
            capacidad=30,
            tipo="Teórica",
        )
    )

    catalogos.agregar_aula(
        Aula(
            id_aula="LAB01",
            edificio="Edificio B",
            capacidad=25,
            tipo="Laboratorio de computación",
        )
    )

    return catalogos