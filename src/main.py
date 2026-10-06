from modelos.administrador_academico import AdministradorAcademico


administrador = AdministradorAcademico(
    "Yandri",
    "yandri@uleam.edu.ec",
    "123456",
    "ADM001"
)

print("Nombre:", administrador.nombre)
print("Correo:", administrador.correo)
print("Código:", administrador.codigo_empleado)

administrador.gestionar_horarios()