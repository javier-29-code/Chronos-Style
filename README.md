# Chronos-Style

Sistema web de gestión de horarios de clases desarrollado con Python y
Django. Permite preparar los datos de planificación, generar propuestas,
corregirlas, revisarlas y publicar horarios oficiales.

Proyecto iniciado en la asignatura de Programación Orientada a Objetos
de la Universidad Laica Eloy Alfaro de Manabí (ULEAM) y posteriormente
migrado de una aplicación de escritorio con Tkinter a una aplicación web.

## Funcionalidades

- Catálogos de programas, periodos, paralelos/cursos, asignaturas y aulas.
- Registro de docentes y configuración de su carga semanal máxima.
- Disponibilidad docente y franjas generales por periodo.
- Franjas por Paralelo/Curso para horarios de mañana, tarde o mixtos.
- Definición de sesiones semanales y duración de cada clase.
- Generación automática de propuestas en borrador.
- Detección de conflictos de docente, aula y paralelo.
- Diagnóstico de sesiones que no pudieron ubicarse.
- Edición de bloques y asignación manual de sesiones pendientes.
- Reintento de pendientes conservando los bloques existentes.
- Revisión, aprobación y publicación de horarios.
- Retirada de publicación con registro del motivo.
- Consulta de horarios oficiales mediante un calendario semanal.
- Filtros por periodo, docente, aula y Paralelo/Curso.
- Vista de impresión y guardado como PDF desde el navegador.
- Comando para cargar datos ficticios de demostración.

La preferencia por laboratorio es flexible: el generador puede asignar
un aula común cuando no encuentra un laboratorio disponible.

## Tecnologías

- Python 3.14.2: versión utilizada en las comprobaciones locales.
- Django 5.2.18.
- SQLite para desarrollo local.
- HTML, CSS y JavaScript.
- Pruebas automatizadas con el sistema de pruebas de Django.

Las dependencias están fijadas en `web/requirements.txt`.

## Instalación local en Windows

Ejecuta los comandos en PowerShell.

### 1. Descargar el proyecto

La versión Django se encuentra actualmente en la rama
`feature/migracion-django`.

```powershell
git clone --branch feature/migracion-django https://github.com/javier-29-code/Chronos-Style.git
cd Chronos-Style
```

Si ya tienes el repositorio, utiliza tu copia existente y comprueba
que estás en la rama correspondiente.

### 2. Crear el entorno virtual

```powershell
py -3.14 -m venv .venv
```

### 3. Instalar las dependencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\web\requirements.txt
```

Los comandos utilizan directamente el Python del entorno virtual,
por lo que no es obligatorio activarlo.

### 4. Preparar la base de datos

```powershell
cd web
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py configurar_roles
```

La base local se crea en `web/db.sqlite3`.

Las migraciones se incluyen en Git. Para instalar el proyecto se ejecuta
`migrate`; no es necesario generar nuevas migraciones.

### 5. Elegir cómo comenzar

Para explorar el sistema con datos ficticios:

```powershell
..\.venv\Scripts\python.exe manage.py cargar_demo
```

Para administrar cuentas desde el panel de Django, puedes crear
un superusuario:

```powershell
..\.venv\Scripts\python.exe manage.py createsuperuser
```

El superusuario es independiente de las cuentas de demostración.

### 6. Iniciar el servidor local

```powershell
..\.venv\Scripts\python.exe manage.py runserver
```

- Aplicación: http://127.0.0.1:8000/
- Administración Django: http://127.0.0.1:8000/admin/

`runserver` se utiliza para desarrollo local.

## Demostración

El comando `cargar_demo` crea un programa y un periodo identificados
como demostración, además de docentes, estudiantes, aulas, asignaturas,
disponibilidades y necesidades de clases.

| Paralelo | Franjas propias |
|---|---|
| DEMO A - MAÑANA | Lunes a viernes, 07:00–12:00 |
| DEMO B - TARDE | Lunes a viernes, 13:00–18:00 |
| DEMO C - MIXTO | Lunes, 07:00–10:00; martes, 14:00–17:00 |

El periodo de demostración tiene el código `DEMO-2027`.

### Cuentas

| Usuario | Rol |
|---|---|
| `demo_coordinador` | Coordinador |
| `demo_docente_manana` | Docente |
| `demo_docente_tarde` | Docente |
| `demo_docente_mixto` | Docente |
| `demo_estudiante_manana` | Estudiante |
| `demo_estudiante_tarde` | Estudiante |
| `demo_estudiante_mixto` | Estudiante |

Las contraseñas se generan aleatoriamente y se muestran al crear
las cuentas. Deben guardarse en ese momento.

Repetir el comando conserva los registros y las contraseñas existentes.
No crea ni publica propuestas automáticamente.

El comando solo está habilitado con `DEBUG=True`.

### Recorrido recomendado

1. Iniciar sesión como `demo_coordinador`.
2. Abrir Gestión de horarios → Generar propuesta.
3. Seleccionar el periodo `DEMO-2027` y sus seis necesidades.
4. Generar el borrador: se solicitan 12 sesiones de 90 minutos.
5. Revisar los bloques y cualquier diagnóstico de pendientes.
6. Enviar la propuesta a revisión.
7. Aprobar y publicar el horario.
8. Consultar el calendario del periodo y aplicar sus filtros.
9. Probar la impresión o guardar el horario como PDF.
10. Ingresar como docente o estudiante y comprobar su consulta limitada.

El generador considera todas las aulas activas, incluidas las que
existían antes de cargar la demostración.

## Roles y acceso

| Rol | Alcance |
|---|---|
| Coordinador | Gestiona la planificación, revisa propuestas y publica horarios. |
| Docente | Consulta las clases oficiales que tiene asignadas. |
| Estudiante | Consulta las clases oficiales de los paralelos en los que está inscrito. |
| Superusuario | Administra el sistema mediante el panel de Django. |

Los grupos Docente y Estudiante no reciben el permiso global
`view_horario`, porque permite consultar todos los horarios.

## Reglas de planificación

Una clase propuesta debe respetar:

- Las franjas generales activas de su periodo.
- La disponibilidad activa del docente.
- Las franjas propias activas del Paralelo/Curso, cuando existen.
- La carga semanal máxima del docente.
- Los conflictos de docente, paralelo y aula.
- La duración solicitada para la sesión.

Si un paralelo no tiene ninguna franja propia activa, se utilizan
las franjas generales del periodo.

Cuando existen franjas propias activas, los días sin franjas propias
quedan fuera de la búsqueda.

## Generación y pendientes

El generador busca espacios por orden y guarda un borrador para
revisión humana. No garantiza encontrar la mejor distribución ni
demostrar que una sesión es imposible de ubicar.

El paso de búsqueda determina la separación entre las horas de inicio
que se prueban. Un paso menor puede encontrar otros espacios, con
un mayor número de intentos.

Reintentar pendientes:

- Solo está disponible en borradores y requiere permiso.
- Conserva los bloques existentes.
- Comprueba que los bloques conservados siguen siendo válidos.
- Busca únicamente las sesiones faltantes.
- Actualiza el diagnóstico de la búsqueda.

Si las condiciones no cambian, un reintento puede producir el mismo
resultado.

## Patrones de diseño

- **State.** `PropuestaHorario.estado_actual` selecciona el objeto que
  aplica las reglas de edición y transición de borrador, revisión o
  aprobación. Los servicios conservan los permisos y ejecutan cada
  operación dentro de una transacción.
- **Builder.** `ConstructorPropuestaHorario` prepara el borrador y
  su alcance, incorpora cada bloque y guarda el diagnóstico.
  `GeneradorHorarios` dirige la búsqueda y usa el mismo constructor para
  añadir sesiones pendientes a una propuesta existente.

## Pruebas y comprobaciones

Desde la carpeta `web`:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Para ejecutar las pruebas de franjas por paralelo y reintentos:

```powershell
..\.venv\Scripts\python.exe manage.py test planificacion.test_franja_paralelos --verbosity 2
```

La última ejecución completa reportada durante el desarrollo
finalizó con 245 pruebas correctas.

## Configuración

| Variable de entorno | Uso |
|---|---|
| `DJANGO_DEBUG` | Activa o desactiva el modo de desarrollo. Predeterminado: `true`. |
| `DJANGO_SECRET_KEY` | Clave privada del entorno. Obligatoria con `DEBUG=False`. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por comas. Predeterminado: `localhost,127.0.0.1`. |

La configuración actual utiliza variables del entorno del proceso.
No carga automáticamente archivos `.env`.

En desarrollo existe una clave de respaldo identificada como insegura.
No debe utilizarse en producción.

La preparación para producción y el despliegue siguen pendientes.
El ajuste de estas variables no sustituye la configuración de HTTPS,
archivos estáticos y servidor de aplicación.

## Organización

- `web/config/`: configuración y rutas principales de Django.
- `web/usuarios/`: cuentas, perfiles, roles y servicios de acceso.
- `web/academico/`: programas, periodos, paralelos, asignaturas y aulas.
- `web/planificacion/`: horarios, propuestas, generación y validaciones.
- `web/planificacion/vistas/`: vistas organizadas por responsabilidad.
- `web/planificacion/templates/`: plantillas HTML.
- `web/planificacion/static/`: CSS y JavaScript.
- `web/planificacion/management/commands/`: comandos de administración.
- `src/` y `tests/`: código y pruebas de la versión anterior de escritorio.
- `docs/README_tkinter.md`: documentación histórica de esa versión.

La aplicación Django utiliza `web/db.sqlite3`.
La base antigua `datos/chronos.db` pertenece a la versión de escritorio.

## Estado

Versión web funcional en desarrollo. Se ha comprobado el recorrido de
generación, revisión, publicación, consulta por roles e impresión
con los datos de demostración.

Pendientes de entrega:

- Comprobar la instalación en un entorno virtual nuevo.
- Completar la configuración de producción.
- Desplegar y comprobar la versión publicada.
