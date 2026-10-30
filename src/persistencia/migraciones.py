"""Migraciones del esquema de almacenamiento."""

import sqlite3
from contextlib import closing
from pathlib import Path

from modelos.asignatura import Asignatura


def _clave(valor):
    return valor.strip().casefold()


def migrar_asignaturas_horarios(ruta, asignaturas):
    """Agrega asignatura_codigo y relaciona los horarios existentes.

    No elimina la columna materia.

    Si una materia no puede identificarse de manera única,
    revierte la migración completa.
    """
    ruta = Path(ruta)

    if not ruta.is_file():
        raise ValueError(
            f"No existe la base de datos: {ruta}"
        )

    por_codigo = {}
    por_nombre = {}

    for asignatura in asignaturas:
        if not isinstance(asignatura, Asignatura):
            raise ValueError(
                "El catálogo debe contener objetos Asignatura."
            )

        codigo = _clave(asignatura.codigo)
        nombre = _clave(asignatura.nombre)

        if codigo in por_codigo:
            raise ValueError(
                f"Código de asignatura duplicado: {codigo}."
            )

        por_codigo[codigo] = asignatura
        por_nombre.setdefault(nombre, []).append(codigo)

    # mode=rw impide crear por accidente una base vacía.
    uri = ruta.resolve().as_uri() + "?mode=rw"

    with closing(
        sqlite3.connect(uri, uri=True)
    ) as conexion:
        try:
            # Inicio explícito: también permite revertir ALTER TABLE.
            conexion.execute("BEGIN IMMEDIATE")

            columnas = {
                fila[1]
                for fila in conexion.execute(
                    "PRAGMA table_info(horarios)"
                )
            }

            if not columnas:
                raise ValueError(
                    "No existe la tabla horarios."
                )

            tiene_codigo = "asignatura_codigo" in columnas

            consulta = (
                """
                SELECT id, materia, asignatura_codigo
                FROM horarios
                """
                if tiene_codigo
                else """
                SELECT id, materia, NULL
                FROM horarios
                """
            )

            filas = conexion.execute(consulta).fetchall()
            relaciones = []

            for identificador, materia, codigo_guardado in filas:
                if codigo_guardado is not None:
                    codigo = _clave(codigo_guardado)

                    if codigo not in por_codigo:
                        raise ValueError(
                            f"Horario {identificador}: "
                            f"código desconocido {codigo_guardado}."
                        )

                else:
                    texto = _clave(materia)

                    # Reunimos coincidencias por nombre y por código.
                    candidatos = set(
                        por_nombre.get(texto, [])
                    )

                    if texto in por_codigo:
                        candidatos.add(texto)

                    if len(candidatos) != 1:
                        raise ValueError(
                            f"Horario {identificador}: no se puede "
                            f"identificar de forma única la materia "
                            f"'{materia}'. Coincidencias: "
                            f"{sorted(candidatos)}."
                        )

                    codigo = candidatos.pop()

                relaciones.append(
                    (codigo, identificador)
                )

            # Solo modificamos el esquema después de resolver
            # correctamente todos los horarios.
            if not tiene_codigo:
                conexion.execute("""
                    ALTER TABLE horarios
                    ADD COLUMN asignatura_codigo TEXT
                """)

            conexion.executemany("""
                UPDATE horarios
                SET asignatura_codigo = ?
                WHERE id = ?
            """, relaciones)

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

    return len(relaciones)