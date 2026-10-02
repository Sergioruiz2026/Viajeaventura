"""implementacion de la clase Paquete para el proyecto ViajesAventura"""

from datetime import date

from excepciones import ValidacionError
from seguridad.montos import a_decimal, aplicar_margen_clp


class Paquete:

    def __init__(
        self,
        nombre,
        destinos,
        fecha_salida,
        fecha_regreso,
        cupo_maximo,
        margen=0.20,
        precio_por_persona=None,
        cupo_reservado_activo=0
    ):
        if len(destinos) < 2 or len(destinos) > 5:
            raise ValidacionError(
                "El paquete debe tener entre 2 y 5 destinos."
            )
        if fecha_regreso <= fecha_salida:
            raise ValidacionError("La fecha de regreso debe ser posterior.")
        if cupo_maximo <= 0:
            raise ValidacionError("El cupo debe ser mayor que cero.")
        margen = a_decimal(margen)
        if margen < 0:
            raise ValidacionError("El margen no puede ser negativo.")

        self.__nombre = nombre
        self.__destinos = destinos
        self.__fecha_salida = fecha_salida
        self.__fecha_regreso = fecha_regreso
        self.__cupo_maximo = cupo_maximo
        self.__cupo_reservado_activo = cupo_reservado_activo
        self.__margen = margen
        costo_total = sum(
            (a_decimal(destino.costo_base) for destino in destinos),
            start=a_decimal(0)
        )
        self.__precio_por_persona = (
            aplicar_margen_clp(costo_total, margen)
            if precio_por_persona is None
            else aplicar_margen_clp(precio_por_persona, 0)
        )

    @property
    def nombre(self):
        return self.__nombre

    @property
    def precio_por_persona(self):
        return self.__precio_por_persona

    @property
    def margen_operacion(self):
        return self.__margen

    @property
    def fecha_salida(self):
        return self.__fecha_salida

    @property
    def fecha_regreso(self):
        return self.__fecha_regreso

    @property
    def destinos(self):
        return self.__destinos.copy()

    @property
    def cupo_maximo(self):
        return self.__cupo_maximo

    @property
    def cupo_reservado_activo(self):
        return self.__cupo_reservado_activo

    @property
    def cupo_disponible(self):
        return self.__cupo_maximo - self.__cupo_reservado_activo

    @property
    def estado(self):
        return "Vencido" if self.esta_vencido() else "Vigente"

    def disponible(self, personas_reservadas):
        return self.__cupo_maximo - personas_reservadas

    def esta_vencido(self, fecha_actual=None):
        return self.__fecha_salida <= (fecha_actual or date.today())

    def __str__(self):
        return (
            f"{self.__nombre} - ${self.__precio_por_persona:,.0f} - "
            f"Cupos disponibles: {self.cupo_disponible} - {self.estado}"
        )