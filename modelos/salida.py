"""Salida (fecha de partida) de un paquete turístico."""

from dataclasses import dataclass
from datetime import date


@dataclass
class Salida:
    id: int
    paquete_id: int
    paquete_nombre: str
    precio_por_persona: int
    fecha_salida: date
    fecha_regreso: date
    cupo_maximo: int
    cupo_disponible: int

    def esta_vigente(self, hoy=None):
        return self.fecha_salida > (hoy or date.today())
