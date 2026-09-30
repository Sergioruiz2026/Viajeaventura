"""cracion de la clase reserva repositorio"""


class ReservaRepositorio:

    def __init__(self):
        self.__reservas = []

    def agregar(self, reserva):
        self.__reservas.append(reserva)

    def listar(self):
        return self.__reservas.copy()

    def reservas_por_cliente(self, correo):
        return [
            reserva
        for reserva in self.__reservas
        if reserva.cliente.correo.lower()
        == correo.lower()
        ]

    def reservas_por_paquete(self, nombre_paquete):
        return [
            reserva
            for reserva in self.__reservas
            if reserva.paquete.nombre.lower() == nombre_paquete.lower()
        ]

    def cupos_ocupados(self, nombre_paquete):
        reservas = self.reservas_por_paquete(nombre_paquete)
        return sum(reserva.cantidad_personas for reserva in reservas)