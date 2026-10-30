# modelos/horario.py
# Un Horario representa UNA clase programada:
# qué materia, con qué docente, en qué aula y en qué franja.
# El día y las horas ya los maneja FranjaHoraria, así que aquí no se repiten.

from modelos.paralelo import Paralelo
from modelos.asignatura import Asignatura

class Horario:
    def __init__(
        self, materia, docente, aula, franja, paralelo=None, *, asignatura=None,):
        # materia: texto con el nombre de la materia
        # docente: objeto Docente
        # aula: objeto Aula (o Laboratorio)
        # franja: objeto FranjaHoraria (incluye día y horas)
        # Validaciones: no se permite crear un Horario incompleto
        if not isinstance(materia, str) or not materia.strip():
            raise ValueError("La materia no puede estar vacía")
        
        if asignatura is not None:
            if not isinstance(asignatura, Asignatura):
                raise ValueError(
                    "La asignatura debe ser un objeto Asignatura."
                )

            referencia = materia.strip().casefold()

            referencias_validas = {
                asignatura.codigo.strip().casefold(),
                asignatura.nombre.strip().casefold(),
            }

            if referencia not in referencias_validas:
                raise ValueError(
                    "La materia no corresponde a la asignatura indicada."
                )
                
        if docente is None or aula is None or franja is None:
            raise ValueError("Docente, aula y franja son obligatorios")
        
        if paralelo is not None and not isinstance(paralelo, Paralelo):
            raise ValueError(
                "El paralelo debe ser un objeto Paralelo."
            )
            
        duracion = franja.hora_fin - franja.hora_inicio

        if duracion > docente.horas_semanales_max:
            raise ValueError(
                "La duración de la clase supera las horas "
                "semanales máximas del docente."
            )

        self._materia = materia.strip()
        self._docente = docente
        self._aula = aula
        self._franja = franja
        self._paralelo = paralelo
        self._asignatura = asignatura

    # ---------- Propiedades (lectura) ----------
    @property
    def materia(self):
        """Nombre utilizado por las pantallas existentes."""
        if self._asignatura is not None:
            return self._asignatura.nombre

        return self._materia

    @property
    def asignatura(self):
        return self._asignatura

    @property
    def asignatura_codigo(self):
        if self._asignatura is None:
            return None

        return self._asignatura.codigo
    
    @property
    def docente(self):
        return self._docente

    @property
    def aula(self):
        return self._aula

    @property
    def franja(self):
        return self._franja
    
    @property
    def paralelo(self):
        return self._paralelo

    # ---------- Comprobaciones de conflicto ----------
    def se_solapa_con(self, otro):
        # Delegamos en FranjaHoraria: ella sabe si se cruzan en el tiempo
        return self._franja.se_solapa_con(otro.franja)

    def tiene_mismo_docente(self, otro):
        return (
            self.docente.correo.strip().casefold()
            == otro.docente.correo.strip().casefold()
        )

    def tiene_misma_aula(self, otro):
        return (
            self.aula.id_aula.strip().casefold()
            == otro.aula.id_aula.strip().casefold()
        )

    def tiene_conflicto_con(self, otro):
        if not self.se_solapa_con(otro):
            return False

        return (
            self.tiene_mismo_docente(otro)
            or self.tiene_misma_aula(otro)
            or self.tiene_mismo_paralelo(otro)
        )
    
    def tiene_mismo_paralelo(self, otro):
        if self.paralelo is None or otro.paralelo is None:
            return False

        return (
            self.paralelo.codigo.strip().casefold()
            == otro.paralelo.codigo.strip().casefold()
        )

    # ---------- Mostrar ----------
    def mostrar_informacion(self):
        return (f"{self.materia} | {self._franja} | "
                f"Aula: {self._aula} | Docente: {self._docente}")

    def __str__(self):
        return self.mostrar_informacion()