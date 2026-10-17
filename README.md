
# Chronos-Style

Sistema de gestión de horarios académicos universitarios, desarrollado en Python con Programación Orientada a Objetos para la asignatura de POO (ULEAM).

Gestiona usuarios (estudiantes, docentes y administradores académicos), asignaturas, planes de estudio, programas académicos, períodos académicos, aulas y laboratorios, y franjas horarias.

## Requisitos

- Python 3 (probado con Python 3.14)
- No necesita instalar librerías externas

## Cómo ejecutar

Desde la carpeta raíz del proyecto:

```powershell
python src\main.py
```

`main.py` crea objetos de ejemplo de cada clase y muestra su información en pantalla.

## Cómo ejecutar las pruebas

```powershell
python -m unittest tests.test_usuario -v
```

## Estructura del proyecto

```
Chronos-Style/
├── src/
│   ├── main.py            # Programa de demostración
│   ├── modelos/           # Clases del dominio
│   ├── interfaces/        # Interfaces de usuario
│   └── servicios/         # Lógica de negocio
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

`Usuario` es una clase abstracta que guarda los datos comunes (nombre, correo, contraseña), valida los datos y maneja el inicio y cierre de sesión. Cada tipo de usuario define su propio dominio de correo y su método `mostrar_perfil()`:

| Clase | Dominio de correo |
|-------|-------------------|
| `Estudiante` | `@live.uleam.edu.ec` |
| `Docente` | `@uleam.edu.ec` |
| `AdministradorAcademico` | `@uleam.edu.ec` |

La contraseña debe tener al menos 8 caracteres e incluir letras y números.

## Flujo de trabajo con Git

- `main`: versión estable.
- `develop`: rama de integración donde se suben los avances del equipo.

## Estado del proyecto

En desarrollo. Pendiente de integrar la clase `Horario` con los usuarios.