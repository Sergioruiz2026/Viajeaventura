"""" creacion de validadores para el proyecto ViajesAventura"""


import re

from excepciones import ValidacionError


class Validador:
    @staticmethod
    def validar_nombre(nombre):
        if not nombre.strip():
            raise ValidacionError("El nombre no puede estar vacío.")

    @staticmethod
    def validar_correo(correo):
        patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(patron, correo):
            raise ValidacionError("Correo electrónico inválido.")

    @staticmethod
    def validar_telefono(telefono):
        patron = r"^\+?\d{8,15}$"
        if not re.match(patron, telefono):
            raise ValidacionError("Teléfono inválido.")

    @staticmethod
    def validar_rut(rut):
        patron = r"^\d{7,8}-[\dkK]$"
        if not re.match(patron, rut):
            raise ValidacionError("Formato de RUT inválido.")

    @staticmethod
    def validar_contrasena(password):
        if len(password) < 8:
            raise ValidacionError(
                "La contraseña debe tener al menos 8 caracteres."
            )
        if not re.search(r"[A-Z]", password):
            raise ValidacionError("Debe contener una mayúscula.")
        if not re.search(r"[a-z]", password):
            raise ValidacionError("Debe contener una minúscula.")
        if not re.search(r"\d", password):
            raise ValidacionError("Debe contener un número.")