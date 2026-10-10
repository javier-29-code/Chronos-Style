
from modelos.administrador_academico import AdministradorAcademico
from modelos.docente import Docente
from modelos.estudiante import Estudiante
from modelos.programa_academico import ProgramaAcademico
from modelos.plan_estudios import PlanEstudios
from modelos.asignatura import Asignatura

#periodo academico
from datetime import date
from modelos.periodo_academico import PeriodoAcademico

# Crear usuarios
administrador = AdministradorAcademico(
    "javier",
    "javier@uleam.edu.ec",
    "123456",
    "ADM001"
)

docente = Docente(
    "Carlos",
    "carlos@uleam.edu.ec",
    "abcdef",
    "DOC001",
    "Ing en tecnologias de la informacion"
)

estudiante = Estudiante(
    "Ana",
    "ana@uleam.edu.ec",
    "987654",
    "EST001",
    "Tecnologías de la Información",
    3
)


# Crear asignaturas
programacion1 = Asignatura(
    "TI-POO1", "Programación I", 4, 6
)

programacion2 = Asignatura(
    "TI-POO2", "Programación II", 4, 6
)

bases_datos = Asignatura(
    "TI-BD1", "Bases de Datos", 3, 4
)

algebra_lineal = Asignatura(
    "TI-MAT1", "Álgebra Lineal", 3, 4
)

# Definir prerrequisitos
programacion2.definir_requisitos([programacion1])


# Crear plan de estudios
plan = PlanEstudios("2025", "2025-2029")

plan.agregar_asignatura(programacion1)
plan.agregar_asignatura(programacion2)
plan.agregar_asignatura(bases_datos)
plan.agregar_asignatura(algebra_lineal)

print("\n=== PLAN DE ESTUDIOS ===")
plan.mostrar_asignaturas()
print("Versión:", plan.version)
print("Vigencia:", plan.vigencia)


# Crear programa académico y asignarle el plan
programa = ProgramaAcademico(
    "PROG-TI",
    "Tecnologías de la Información",
    "Pregrado"
)

programa.asignar_plan_estudios(plan)

print("\n=== PROGRAMA Y SU PLAN DE ESTUDIOS ===")
print("Programa:", programa.nombre)
programa.mostrar_plan_estudios()


# Administrador
print("\n=== ADMINISTRADOR ===")
print("Nombre:", administrador.nombre)
print("Código:", administrador.codigo_empleado)
administrador.gestionar_horarios()


# Docente
print("\n=== DOCENTE ===")
print("Nombre:", docente.nombre)
print("Código:", docente.codigo_docente)
print("Titulo:", docente.titulo)
docente.consultar_horario()


# Estudiante
print("\n=== ESTUDIANTE ===")
print("Nombre:", estudiante.nombre)
print("Codigo:", estudiante.codigo_estudiante)
print("Carrera:", estudiante.carrera)
print("Semestre:", estudiante.semestre)
estudiante.consultar_informacion_academica()


# Detalle de asignatura
print("\n=== ASIGNATURA ===")
programacion2.mostrar_informacion()

# Crear período académico
periodo = PeriodoAcademico(
    "PA-2026-1",
    "Primer período académico 2026",
    date(2026, 4, 1),
    date(2026, 8, 31)
)

print("\n=== PERÍODO ACADÉMICO ===")
periodo.mostrar_informacion()