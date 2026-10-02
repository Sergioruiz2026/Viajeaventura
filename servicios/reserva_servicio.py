"""CREACION DE RESERVAS DE PAQUETES TURISTICOS"""

from datetime import date

from modelos.reserva import Reserva

from excepciones import ReservaNoPermitidaError, ValidacionError
from seguridad.autorizacion import exigir_rol


class ReservaServicio:

    def __init__(
        self,
        reserva_repo,
        paquete_repo
    ):
        self.__reserva_repo = reserva_repo
        self.__paquete_repo = paquete_repo

    def crear_reserva(self, sesion, paquete_id, cantidad_personas):
        exigir_rol(sesion, "CLIENTE")
        if (
            isinstance(cantidad_personas, bool)
            or not isinstance(cantidad_personas, int)
            or cantidad_personas < 1
        ):
            raise ValidacionError("Debe reservar al menos una persona.")
        paquete = self.__paquete_repo.buscar_por_id(paquete_id)
        if not paquete:
            raise ReservaNoPermitidaError("Paquete inexistente.")
        if paquete.fecha_salida < date.today():
            raise ReservaNoPermitidaError(
                "No se puede reservar un paquete vencido."
            )

        reserva = Reserva(sesion.usuario, paquete, cantidad_personas)
        self.__reserva_repo.agregar(reserva, paquete_id=paquete_id)
        return reserva

    def reservas_cliente(self, sesion):
        exigir_rol(sesion, "CLIENTE")
        return self.__reserva_repo.reservas_por_cliente(sesion.usuario.correo)

    def listar_reservas(self, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__reserva_repo.listar()