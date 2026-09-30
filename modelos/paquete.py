"""implementacion de la clase Paquete para el proyecto ViajesAventura"""

from datetime import date

from excepciones import ValidacionError


class Paquete:

    def __init__(
        self,
        nombre,
        destinos,
        fecha_salida,
        fecha_regreso,
        cupo_maximo,
        margen=0.20
    ):
        if len(destinos) < 2 or len(destinos) > 5:
            raise ValidacionError(
                "El paquete debe tener entre 2 y 5 destinos."
            )
        if fecha_regreso <= fecha_salida:
            raise ValidacionError("La fecha de regreso debe ser posterior.")
        if cupo_maximo <= 0:
            raise ValidacionError("El cupo debe ser mayor que cero.")
        if margen < 0:
            raise ValidacionError("El margen no puede ser negativo.")

        self.__nombre = nombre
        self.__destinos = destinos
        self.__fecha_salida = fecha_salida
        self.__fecha_regreso = fecha_regreso
        self.__cupo_maximo = cupo_maximo
        costo_total = sum(destino.costo_base for destino in destinos)
        self.__precio_por_persona = costo_total * (1 + margen)

    @property
    def nombre(self):
        return self.__nombre

    @property
    def precio_por_persona(self):
        return self.__precio_por_persona

    @property
    def fecha_salida(self):
        return self.__fecha_salida

    @property
    def cupo_maximo(self):
        return self.__cupo_maximo

    def disponible(self, personas_reservadas):
        return self.__cupo_maximo - personas_reservadas

    def esta_vencido(self):
        return self.__fecha_salida < date.today()

    def __str__(self):
        return f"{self.__nombre} - ${self.__precio_por_persona:,.0f}"