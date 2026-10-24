from modelos.docente import Docente
from servicios.gestor_usuarios import crear_gestor_con_datos_ejemplo
from servicios.datos_ejemplo import crear_catalogos_con_datos_ejemplo

usuarios = crear_gestor_con_datos_ejemplo()

docentes = [
    usuario
    for usuario in usuarios.listar()
    if isinstance(usuario, Docente)
]

catalogos = crear_catalogos_con_datos_ejemplo(docentes)

assert len(catalogos.listar_asignaturas()) == 2
assert len(catalogos.listar_aulas()) == 2
assert len(catalogos.listar_docentes()) == len(docentes)

# El catálogo conserva el mismo objeto.
assert catalogos.listar_docentes()[0] is docentes[0]

# Modificar la lista devuelta no vacía el catálogo.
copia = catalogos.listar_aulas()
copia.clear()
assert len(catalogos.listar_aulas()) == 2

# No debe permitir registrar el mismo docente otra vez.
try:
    catalogos.agregar_docente(docentes[0])
except ValueError as error:
    print("Duplicado rechazado correctamente:", error)
else:
    raise AssertionError("Se permitió un docente duplicado.")

print("Comprobaciones del catálogo completadas.")