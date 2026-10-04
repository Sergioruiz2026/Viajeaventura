"""implementacion de la clase Administrador para el proyecto ViajesAventura"""

class Administrador:
    def __init__(self, usuario):
        self.__usuario = usuario

    @property
    def usuario(self):
        return self.__usuario

    def __str__(self):
        return f"Administrador: {self.__usuario}"