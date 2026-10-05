"""CREACION DE RESERVAS DE PAQUETES TURISTICOS"""

from datetime import date

from modelos.reserva import Reserva

from excepciones import ReservaNoPermitidaError, ValidacionError
from seguridad.autorizacion import exigir_permiso_reserva, exigir_rol


class ReservaServicio:

    def __init__(self, reserva_repo, paquete_repo, salida_repo=None):
        self.__reserva_repo = reserva_repo
        self.__paquete_repo = paquete_repo
        self.__salida_repo = salida_repo

    def crear_reserva(self, sesion, paquete_id, cantidad_personas,
                      salida_id=None):
        exigir_permiso_reserva(sesion)
        if (
            isinstance(cantidad_personas, bool)
            or not isinstance(cantidad_personas, int)
            or cantidad_personas < 1
        ):
            raise ValidacionError("Debe reservar al menos una persona.")

        if salida_id is not None and self.__salida_repo is not None:
            salida = self.__salida_repo.buscar_por_id(salida_id)
            if not salida:
                raise ReservaNoPermitidaError("Salida inexistente.")
            if salida.fecha_salida <= date.today():
                raise ReservaNoPermitidaError(
                    "No se puede reservar una salida vencida."
                )
            paquete_id = salida.paquete_id
            paquete = self.__paquete_repo.buscar_por_id(paquete_id)
            if not paquete:
                raise ReservaNoPermitidaError("Paquete inexistente.")
            reserva = Reserva(sesion.usuario, paquete, cantidad_personas)
            return self.__reserva_repo.agregar(
                reserva, paquete_id=paquete_id, salida_id=salida_id
            )

        # Ruta legada (sin salida_id)
        paquete = self.__paquete_repo.buscar_por_id(paquete_id)
        if not paquete:
            raise ReservaNoPermitidaError("Paquete inexistente.")
        if paquete.fecha_salida < date.today():
            raise ReservaNoPermitidaError(
                "No se puede reservar un paquete vencido."
            )
        reserva = Reserva(sesion.usuario, paquete, cantidad_personas)
        return self.__reserva_repo.agregar(reserva, paquete_id=paquete_id)

    def reservas_cliente(self, sesion):
        exigir_rol(sesion, "CLIENTE")
        return self.__reserva_repo.reservas_por_cliente(sesion.usuario.id)

    def cancelar_reserva(self, sesion, reserva_id):
        exigir_rol(sesion, "CLIENTE")
        return self.__reserva_repo.cancelar(reserva_id, sesion.usuario.id)

    def listar_reservas(self, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__reserva_repo.listar()
