"""" implementacion de la clase Cliente para el proyecto ViajesAventura"""

class Cliente:
    def __init__(self,
        nombre,
        rut,
        correo,
        telefono,
        password_hash,
        rol="CLIENTE",
        usuario_id=None):

        self.__id = usuario_id
        self.__nombre = nombre
        self.__rut = rut
        self.__correo = correo
        self.__telefono = telefono
        self.__password_hash = password_hash
        self.__rol = rol

    @property
    def id(self):
        return self.__id

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    @property
    def password_hash(self):
        return self.__password_hash

    @property
    def rol(self):
        return self.__rol

    @property
    def rut(self):
        return self.__rut

    @property
    def telefono(self):
        return self.__telefono

    def __str__(self):
        return f"Cliente: {self.__nombre} ({self.__correo})"