"""implementacion de la clase reserva para el proyecto ViajesAventura"""

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
        total=None,
        *,
        id_reserva=None,
        estado="ACTIVA",
        salida_id=None,
        salida_fecha_salida=None,
        salida_fecha_regreso=None,
    ):
        if (
            isinstance(cantidad_personas, bool)
            or not isinstance(cantidad_personas, int)
            or cantidad_personas < 1
        ):
            raise ValidacionError(
                "Debe reservar al menos una persona."
            )

        self.__cliente = cliente
        self.__paquete = paquete
        self.__id = id_reserva
        self.__cantidad_personas = cantidad_personas
        self.__fecha_emision = fecha_emision or datetime.now()
        self.__estado = estado
        self.__salida_id = salida_id
        self.__salida_fecha_salida = salida_fecha_salida
        self.__salida_fecha_regreso = salida_fecha_regreso
        self.__total = redondear_clp(
            a_decimal(paquete.precio_por_persona) * cantidad_personas
            if total is None
            else total
        )

    @property
    def cliente(self):
        return self.__cliente

    @property
    def id(self):
        return self.__id

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

    @property
    def estado(self):
        return self.__estado

    @property
    def salida_id(self):
        return self.__salida_id

    @property
    def salida_fecha_salida(self):
        return self.__salida_fecha_salida

    @property
    def salida_fecha_regreso(self):
        return self.__salida_fecha_regreso

    def __str__(self):
        identificador = f"#{self.__id}" if self.__id is not None else "nueva"
        return (
            f"Reserva {identificador} | {self.__paquete.nombre} | "
            f"{self.__estado} | Total: ${self.__total:,.0f}"
        )