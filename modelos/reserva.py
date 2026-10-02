""""implementacion de la clase reserva para el proyecto ViajesAventura"""

from datetime import datetime

from excepciones import ValidacionError
from seguridad.montos import a_decimal, redondear_clp


class Reserva:

    def __init__(
        self,
        cliente,
        paquete,
        cantidad_personas,
        fecha_emision=None,
        total=None
    ):
        if cantidad_personas < 1:
            raise ValidacionError(
                "Debe reservar al menos una persona."
            )

        self.__cliente = cliente
        self.__paquete = paquete
        self.__cantidad_personas = cantidad_personas
        self.__fecha_emision = fecha_emision or datetime.now()
        self.__total = redondear_clp(
            a_decimal(paquete.precio_por_persona) * cantidad_personas
            if total is None
            else total
        )

    @property
    def cliente(self):
        return self.__cliente

    @property
    def paquete(self):
        return self.__paquete

    @property
    def cantidad_personas(self):
        return self.__cantidad_personas

    @property
    def total(self):
        return self.__total

    @property
    def fecha_emision(self):
        return self.__fecha_emision

    def __str__(self):
        return (
            f"Reserva de {self.__cliente.nombre} "
            f"- Total: ${self.__total:,.0f}"
        )