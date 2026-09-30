"""CREACION DE RESERVAS DE PAQUETES TURISTICOS"""

from modelos.reserva import Reserva

from excepciones import CupoInsuficienteError, ReservaNoPermitidaError


class ReservaServicio:

    def __init__(
        self,
        reserva_repo,
        paquete_repo
    ):
        self.__reserva_repo = reserva_repo
        self.__paquete_repo = paquete_repo

    def crear_reserva(self, cliente, nombre_paquete, cantidad_personas):
        paquete = self.__paquete_repo.buscar_por_nombre(nombre_paquete)
        if not paquete:
            raise ReservaNoPermitidaError("Paquete inexistente.")
        if paquete.esta_vencido():
            raise ReservaNoPermitidaError(
                "No se puede reservar un paquete vencido."
            )

        ocupados = self.__reserva_repo.cupos_ocupados(nombre_paquete)
        disponibles = paquete.cupo_maximo - ocupados
        if cantidad_personas > disponibles:
            raise CupoInsuficienteError(f"Solo quedan {disponibles} cupos.")

        reserva = Reserva(cliente, paquete, cantidad_personas)
        self.__reserva_repo.agregar(reserva)
        return reserva

    def reservas_cliente(self, correo):
        return self.__reserva_repo.reservas_por_cliente(correo)

    def listar_reservas(self):
        return self.__reserva_repo.listar()