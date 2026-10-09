from modelos.administrador_academico import AdministradorAcademico
from modelos.docente import Docente
from modelos.estudiante import Estudiante
from modelos.programa_academico import ProgramaAcademico
from modelos.plan_estudios import PlanEstudios
from modelos.asignatura import Asignatura

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

programa = ProgramaAcademico(
    "PROG-TI",
    "Tecnologías de la Información",
    "Grado"
)

programa = ProgramaAcademico(
    "PROG-TI",
    "Tecnologías de la Información",
    "3er nivel"
)

print("\n=== PLAN DE ESTUDIOS ===")

plan = PlanEstudios(
    "2025",
    "2025-2029"
)

plan.agregar_asignatura("Programación Orientada a Objetos")
plan.agregar_asignatura("Bases de Datos")
plan.agregar_asignatura("Álgebra Lineal")

plan.mostrar_asignaturas()

print("Versión:", plan.version)
print("Vigencia:", plan.vigencia)

print("=== ADMINISTRADOR ===")
print("Nombre:", administrador.nombre)
print("Código:", administrador.codigo_empleado)
administrador.gestionar_horarios()

print("\n=== DOCENTE ===")
print("Nombre:", docente.nombre)
print("Código:", docente.codigo_docente)
print("Titulo:", docente.titulo)
docente.consultar_horario()

print("\n=== ESTUDIANTE ===")
print("Nombre:", estudiante.nombre)
print("Código:", estudiante.codigo_estudiante)
print("Carrera:", estudiante.carrera)
print("Semestre:", estudiante.semestre)
estudiante.consultar_informacion_academica()

print("\n=== PROGRAMA ACADÉMICO ===")
print("ID:", programa.id_programa)
print("Nombre:", programa.nombre)
print("Nivel:", programa.nivel)

programa.gestionar_plan_estudios()


print("\n=== ASIGNATURA ===")

programacion1 = Asignatura(
    "TI-POO1", "Programación I", 4, 6
)

programacion2 = Asignatura(
    "TI-POO2", "Programación II", 4, 6
)

programacion2.definir_requisitos([programacion1])

programacion2.mostrar_informacion()