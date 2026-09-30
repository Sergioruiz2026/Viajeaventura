""" creacion de repositorio (destino_repositorio) para el proyecto ViajesAventura"""

from excepciones import DestinoDuplicadoError


class DestinoRepositorio:

    def __init__(self):
        self.__destinos = []

    def agregar(self, destino):
        if self.buscar_por_nombre(destino.nombre):
            raise DestinoDuplicadoError(
                f"El destino '{destino.nombre}' ya existe."
            )
        self.__destinos.append(destino)

    def listar(self):
        return self.__destinos.copy()

    def buscar_por_nombre(self, nombre):

        for destino in self.__destinos:
            if destino.nombre.lower() == nombre.lower():
                return destino

        return None

    def eliminar(self, nombre):

        destino = self.buscar_por_nombre(nombre)

        if destino:
            self.__destinos.remove(destino)
            return True

        return False