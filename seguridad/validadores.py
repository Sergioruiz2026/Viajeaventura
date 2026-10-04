"""creacion de validadores para el proyecto ViajesAventura"""


import re

from excepciones import ValidacionError


class Validador:
    @staticmethod
    def validar_nombre(nombre):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValidacionError("El nombre no puede estar vacío.")

    @staticmethod
    def validar_correo(correo):
        patron = (
            r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
            r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
            r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
        )
        if not isinstance(correo, str) or not re.fullmatch(patron, correo):
            raise ValidacionError("Correo electrónico inválido.")

    @staticmethod
    def validar_telefono(telefono):
        patron = r"^\+?\d{8,15}$"
        if not re.match(patron, telefono):
            raise ValidacionError("Teléfono inválido.")

    @staticmethod
    def validar_rut(rut):
        patron = r"^(?:[0-9]{7,8}|[0-9]{1,2}(?:\.[0-9]{3}){2})-[0-9kK]$"
        if not isinstance(rut, str) or not re.fullmatch(patron, rut.strip()):
            raise ValidacionError("Formato de RUT inválido.")
        cuerpo, digito_verificador = rut.strip().upper().split("-")
        cuerpo = cuerpo.replace(".", "")
        suma = sum(
            int(digito) * (indice % 6 + 2)
            for indice, digito in enumerate(reversed(cuerpo))
        )
        resultado = 11 - suma % 11
        esperado = "0" if resultado == 11 else "K" if resultado == 10 else str(resultado)
        if digito_verificador.upper() != esperado:
            raise ValidacionError("El dígito verificador del RUT es inválido.")

    @staticmethod
    def validar_contrasena(password):
        if not isinstance(password, str):
            raise ValidacionError("La contraseña debe ser texto.")
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
        if not re.search(r"[^A-Za-z0-9\s]", password):
            raise ValidacionError("Debe contener un carácter especial.")