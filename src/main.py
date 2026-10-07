from modelos.administrador_academico import AdministradorAcademico
from modelos.docente import Docente
from modelos.estudiante import Estudiante
from modelos.usuario import Usuario


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
    "Ingenieria en software"
)

estudiante = Estudiante(
    "Ana",
    "ana@uleam.edu.ec",
    "987654",
    "EST001",
    "Tecnologías de la Información",
    3
)




print("=== ADMINISTRADOR ===")
print("Nombre:", administrador.nombre)
print("Código:", administrador.codigo_empleado)
administrador.gestionar_horarios()

print("\n=== DOCENTE ===")
print("Nombre:", docente.nombre)
print("Código:", docente.codigo_docente)
print("titulo:", docente.titulo)
docente.consultar_horario()

print("\n=== ESTUDIANTE ===")
print("Nombre:", estudiante.nombre)
print("Código:", estudiante.codigo_estudiante)
print("Carrera:", estudiante.carrera)
print("Semestre:", estudiante.semestre)
estudiante.consultar_informacion_academica()