import tempfile
import unittest
from pathlib import Path

from modelos.docente import Docente
from modelos.franja_horaria import FranjaHoraria
from modelos.horario import Horario

from servicios.datos_ejemplo import (
    crear_catalogos_con_datos_ejemplo,
)
from servicios.gestor_usuarios import (
    crear_gestor_con_datos_ejemplo,
)
from servicios.gestor_horarios_sqlite import (
    GestorHorariosSQLite,
)


class TestPersistenciaHorarios(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)

        self.ruta = Path(temporal.name) / "prueba.db"

        usuarios = crear_gestor_con_datos_ejemplo().listar()
        docentes = [
            usuario
            for usuario in usuarios
            if isinstance(usuario, Docente)
        ]

        self.catalogos = crear_catalogos_con_datos_ejemplo(
            docentes
        )
        self.docente = docentes[0]
        self.aula = self.catalogos.listar_aulas()[0]

    def abrir_gestor(self):
        return GestorHorariosSQLite(
            self.ruta,
            self.catalogos,
        )

    def crear_horario(self, inicio, fin):
        return Horario(
            "POO",
            self.docente,
            self.aula,
            FranjaHoraria("Lunes", inicio, fin),
        )

    def test_recupera_horario_y_reutiliza_docente(self):
        gestor = self.abrir_gestor()
        gestor.agregar(self.crear_horario(8, 10))

        recuperado = self.abrir_gestor()

        self.assertEqual(recuperado.cantidad(), 1)
        self.assertIs(
            recuperado.listar()[0].docente,
            self.docente,
        )

    def test_conserva_edicion(self):
        gestor = self.abrir_gestor()
        original = self.crear_horario(8, 10)
        gestor.agregar(original)

        gestor.actualizar(
            original,
            self.crear_horario(10, 12),
        )

        recuperado = self.abrir_gestor()

        self.assertEqual(
            recuperado.listar()[0].franja.hora_inicio,
            10,
        )

    def test_conserva_eliminacion(self):
        gestor = self.abrir_gestor()
        horario = self.crear_horario(8, 10)
        gestor.agregar(horario)
        gestor.eliminar(horario)

        self.assertEqual(
            self.abrir_gestor().cantidad(),
            0,
        )

    def test_no_guarda_horario_con_conflicto(self):
        gestor = self.abrir_gestor()
        gestor.agregar(self.crear_horario(8, 10))

        conflictos = gestor.agregar(
            self.crear_horario(9, 11)
        )

        self.assertTrue(conflictos)
        self.assertEqual(
            self.abrir_gestor().cantidad(),
            1,
        )


if __name__ == "__main__":
    unittest.main()