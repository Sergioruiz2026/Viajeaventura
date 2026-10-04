"""Jerarquia base de usuarios autenticables."""

from abc import ABC, abstractmethod


class Usuario(ABC):
    def __init__(self, nombre, correo, password_hash, usuario_id=None):
        self.__id = usuario_id
        self.__nombre = nombre
        self.__correo = correo
        self.__password_hash = password_hash

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
    @abstractmethod
    def rol(self):
        """Rol persistido y permisos principales."""

    @abstractmethod
    def puede_reservar(self):
        """Indica si el usuario puede crear reservas."""