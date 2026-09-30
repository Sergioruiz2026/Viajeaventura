""" creacion de la clase ClienteRepositorio para manejar la lista de clientes """

from excepciones import CorreoDuplicadoError


class ClienteRepositorio:

    def __init__(self):
        self.__clientes = []

    def agregar(self, cliente):

        if self.buscar_por_correo(cliente.correo):
            raise CorreoDuplicadoError(
                "Ya existe un cliente registrado con ese correo."
            )
        self.__clientes.append(cliente)

    def listar(self):
        return self.__clientes.copy()

    def buscar_por_correo(self, correo):

        for cliente in self.__clientes:
            if cliente.correo.lower() == correo.lower():
                return cliente

        return None

    def buscar_por_rut(self, rut):

        for cliente in self.__clientes:
            if cliente.rut == rut:
                return cliente

        return None