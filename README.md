# Chronos-Style

Sistema de gestión de horarios académicos universitarios, desarrollado en Python con Programación Orientada a Objetos para la asignatura de POO (ULEAM).

Gestiona usuarios (estudiantes, docentes y administradores académicos), asignaturas, planes de estudio, programas académicos, períodos académicos, aulas y laboratorios, y franjas horarias.

## Requisitos

- Python 3 (probado con Python 3.14)
- No necesita instalar librerías externas (la interfaz usa tkinter, que viene incluido con Python)

## Cómo ejecutar

Desde la carpeta raíz del proyecto.

**Aplicación con interfaz gráfica** (login y ventana principal):

```powershell
cd src
python -m interfaces.aplicacion
```

**Programa de demostración** (consola):

```powershell
python src\main.py
```

`main.py` crea objetos de ejemplo de cada clase y muestra su información en pantalla.

## Cómo ejecutar las pruebas

Todas las pruebas:

```powershell
python -m unittest discover -s tests -v
```

O por módulo:

```powershell
python -m unittest tests.test_usuario -v
python -m unittest tests.test_gestor_usuario -v
```

## Estructura del proyecto

```
Chronos-Style/
├── src/
│   ├── main.py            # Programa de demostración
│   ├── modelos/           # Clases del dominio
│   ├── servicios/         # Lógica de negocio (GestorUsuarios)
│   └── interfaces/        # Interfaz gráfica (tkinter)
└── tests/                 # Pruebas unitarias
```

### Clases en `src/modelos/`

| Grupo | Clases |
|-------|--------|
| Usuarios | `Usuario` (abstracta), `Estudiante`, `Docente`, `AdministradorAcademico` |
| Académico | `Asignatura`, `PlanEstudios`, `ProgramaAcademico`, `PeriodoAcademico` |
| Espacios | `Aula`, `AulaTeorica`, `LaboratorioComputo`, `LaboratorioElectronica`, `LaboratorioRedes` |
| Tiempo | `FranjaHoraria` |

## Usuarios

`Usuario` es una clase abstracta que guarda los datos comunes (nombre, correo, contraseña), valida los datos y maneja el inicio y cierre de sesión. Cada tipo de usuario define su propio dominio de correo y sus métodos `mostrar_perfil()` y `ver_horario()`:

| Clase | Dominio de correo |
|-------|-------------------|
| `Estudiante` | `@live.uleam.edu.ec` |
| `Docente` | `@uleam.edu.ec` |
| `AdministradorAcademico` | `@uleam.edu.ec` |

La contraseña debe tener al menos 8 caracteres e incluir letras y números.

`GestorUsuarios` (en `src/servicios/`) guarda los usuarios registrados por correo y valida el inicio de sesión. Ante un correo o una contraseña incorrectos devuelve el mismo mensaje de error, a propósito.

## Interfaz gráfica

La aplicación usa **tkinter (ttk)**. El código está organizado por capas:

| Carpeta | Responsabilidad |
|---|---|
| `src/modelos/` | Clases del dominio. |
| `src/servicios/` | Lógica de la aplicación (`GestorUsuarios`). |
| `src/interfaces/` | Ventanas de tkinter. Solo muestran datos y recogen lo que escribe el usuario; no contienen lógica de negocio. |

Gracias a esta separación, cambiar de librería gráfica solo implica reescribir `interfaces/`.

### Archivos de la interfaz

- `ventana_login.py`: pantalla de inicio de sesión (correo, contraseña, opción de mostrar contraseña y mensaje de error dentro del formulario).
- `ventana_principal.py`: ventana que se abre tras iniciar sesión. Es la misma para los tres roles: muestra el nombre y el rol en la cabecera, el perfil del usuario y el botón de cerrar sesión. Usa `mostrar_perfil()`, que cada clase hija implementa a su manera (polimorfismo).
- `aplicacion.py`: controla el recorrido de pantallas (login → ventana principal → cerrar sesión → login).

### Usuarios de ejemplo

Datos de prueba creados por `crear_gestor_con_datos_ejemplo()` (contraseña de los tres: `clave1234`):

| Rol | Correo |
|---|---|
| Administrador académico | `javier@uleam.edu.ec` |
| Docente | `carlos.perez@uleam.edu.ec` |
| Estudiante | `e1312345678@live.uleam.edu.ec` |

## Flujo de trabajo con Git

- `main`: versión estable.
- `develop`: rama de integración donde se suben los avances del equipo.

## Estado del proyecto

En desarrollo.

Pendiente:

- Pestañas de horario y cambio de contraseña en la ventana principal.
- Registro de usuarios nuevos.
- Integrar la clase `Horario` con los usuarios (`ver_horario()` devuelve por ahora un texto provisional).