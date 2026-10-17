
from modelos.administrador_academico import AdministradorAcademico
from modelos.docente import Docente
from modelos.estudiante import Estudiante
from modelos.programa_academico import ProgramaAcademico
from modelos.plan_estudios import PlanEstudios
from modelos.asignatura import Asignatura

#periodo academico
from datetime import date
from modelos.periodo_academico import PeriodoAcademico

#Aula
from modelos.aula import Aula
from modelos.aula_teorica import AulaTeorica
from modelos.laboratorio_computo import LaboratorioComputo
from modelos.laboratorio_electronica import LaboratorioElectronica
from modelos.laboratorio_redes import LaboratorioRedes

#Franja horaria
from modelos.franja_horaria import FranjaHoraria

# Crear usuarios
administrador = AdministradorAcademico(
    "Javier",
    "javier@uleam.edu.ec",
    "clave1234",
    "Facultad de Ciencias Informáticas"
)

docente = Docente(
    "Carlos",
    "carlos.perez@uleam.edu.ec",
    "clave1234",
    "Ingeniero en Tecnologías de la Información",
    "Programación",
    20
)

estudiante = Estudiante(
    "Ana",
    "e1312345678@live.uleam.edu.ec",
    "clave1234",
    "Tecnologías de la Información",
    3
)


# Usuarios
print("\n=== ADMINISTRADOR ===")
print(administrador.mostrar_perfil())

print("\n=== DOCENTE ===")
print(docente.mostrar_perfil())

print("\n=== ESTUDIANTE ===")
print(estudiante.mostrar_perfil())


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

# Aula
aula1 = AulaTeorica("102", "Edificio de Sistemas", 35, True)
aula2 = LaboratorioComputo("LB204", "Edificio de Sistemas", 30, 28)
aula3 = LaboratorioElectronica("LE305", "Edificio de Sistemas", 25, 15)
aula4 = LaboratorioRedes("LR406", "Edificio de Sistemas", 20, 10)
print("\n=== AULAS ===")
aula1.mostrar_informacion()
aula2.mostrar_informacion()
aula3.mostrar_informacion()
aula4.mostrar_informacion()

franja_a = FranjaHoraria("Lunes", 8, 10)
franja_b = FranjaHoraria("Lunes", 9, 11)
franja_c = FranjaHoraria("Martes", 10, 12)

aula1.ocupar_franja(franja_a)
aula1.ocupar_franja(franja_b)
aula1.ocupar_franja(franja_c)
aula1.liberar_franja(franja_a)
aula1.ocupar_franja(franja_b)

try:
    aula_mala = Aula("103", "Edificio de Sistemas", -5, "Teórica")
except ValueError as error:
    print("Error:", error)

try:
    aula_mala = Aula("104", "Edificio de Sistemas", 30, "Cocina")
except ValueError as error:
    print("Error:", error)

try:
    lab_malo = LaboratorioComputo("LB205", "Edificio de Sistemas", 30, -3)
except ValueError as error:
    print("Error:", error)

Aula.mostrar_total_aulas()