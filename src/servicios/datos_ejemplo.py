"""Catálogos de demostración para probar la interfaz."""

from modelos.asignatura import Asignatura
from modelos.aula import Aula
from servicios.gestor_catalogos import GestorCatalogos
from modelos.paralelo import Paralelo
from modelos.aula_teorica import AulaTeorica


def crear_catalogos_con_datos_ejemplo(docentes, estudiantes=(),repositorio_aulas=None,):
    """Prepara catálogos y utiliza aulas persistentes si se proporcionan."""
    catalogos = GestorCatalogos(
        repositorio_aulas=repositorio_aulas,
    )

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

    # Los ejemplos se crean únicamente si no hay aulas guardadas.
    if not catalogos.listar_aulas():
        catalogos.agregar_aula(
            AulaTeorica(
                id_aula="A101",
                edificio="Edificio A",
                capacidad=30,
                tiene_proyector=False,
                tiene_pantalla_tactil=True,
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
    
    paralelo_a = Paralelo(
        codigo="TI-3-A",
        carrera="Tecnologías de la Información",
        semestre=3,
        letra="A",
    )

    paralelo_b = Paralelo(
        codigo="TI-3-B",
        carrera="Tecnologías de la Información",
        semestre=3,
        letra="B",
    )

    # Para la demostración, inscribimos en A a los estudiantes
    # de la misma carrera y semestre.
    for estudiante in estudiantes:
        if (
            estudiante.carrera.strip().casefold()
            == paralelo_a.carrera.casefold()
            and estudiante.semestre == paralelo_a.semestre
        ):
            paralelo_a.inscribir_estudiante(estudiante)

    catalogos.agregar_paralelo(paralelo_a)
    catalogos.agregar_paralelo(paralelo_b)

    return catalogos