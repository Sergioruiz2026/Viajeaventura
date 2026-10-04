"""implementacion de la clase Cliente para el proyecto ViajesAventura"""

from seguridad.enmascarado import mask_phone, mask_rut
from modelos.usuario import Usuario

class Cliente(Usuario):
    def __init__(self,
        nombre,
        rut,
        correo,
        telefono,
        password_hash,
        rol="CLIENTE",
        usuario_id=None):

        super().__init__(nombre, correo, password_hash, usuario_id)
        self.__nombre = nombre
        self.__rut = rut
        self.__correo = correo
        self.__telefono = telefono
        self.__rol = rol

    @property
    def id(self):
        return super().id

    @property
    def nombre(self):
        return super().nombre

    @property
    def correo(self):
        return super().correo

    @property
    def password_hash(self):
        return super().password_hash

    @property
    def rol(self):
        return self.__rol

    @property
    def rut(self):
        return self.__rut

    @property
    def telefono(self):
        return self.__telefono

    def puede_reservar(self):
        return self.__rol == "CLIENTE"

    def __str__(self):
        return (
            f"Cliente: {self.__nombre} ({self.__correo}) | "
            f"RUT: {mask_rut(self.__rut)} | "
            f"Teléfono: {mask_phone(self.__telefono)}"
        )