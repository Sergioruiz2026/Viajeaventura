"""Sesión autenticada con vencimiento por inactividad."""

from datetime import datetime, timedelta

from excepciones import SesionExpiradaError


class Sesion:
    DURACION_INACTIVIDAD = timedelta(minutes=30)

    def __init__(self, usuario=None, rol=None, ahora=None, identidad=None):
        self.__usuario = usuario
        self.__rol = rol or (usuario.rol if usuario is not None else None)
        if self.__rol not in ("ADMIN", "CLIENTE"):
            raise ValueError("El rol de la sesión no es válido.")
        self.__identidad = identidad
        self.__ultima_actividad = ahora or datetime.now()

    @classmethod
    def administrador(cls, nombre, ahora=None):
        return cls(rol="ADMIN", ahora=ahora, identidad=nombre)

    @property
    def usuario(self):
        return self.__usuario

    @property
    def rol(self):
        return self.__rol

    @property
    def nombre(self):
        return (
            self.__usuario.nombre
            if self.__usuario is not None
            else self.__identidad
        )

    @property
    def correo(self):
        return (
            self.__usuario.correo
            if self.__usuario is not None
            else self.__identidad
        )

    def renovar(self, ahora=None):
        ahora = ahora or datetime.now()
        if ahora - self.__ultima_actividad >= self.DURACION_INACTIVIDAD:
            raise SesionExpiradaError("La sesión expiró por inactividad.")
        self.__ultima_actividad = ahora