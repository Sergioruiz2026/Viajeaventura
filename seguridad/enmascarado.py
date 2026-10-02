"""Formateo de datos personales para su exposición segura."""

import re


_RUT_COMPLETO = re.compile(
    r"^(?P<cuerpo>(?:[0-9]{1,2}(?:\.[0-9]{3}){2}|[0-9]{7,8}))-(?P<dv>[0-9Kk])$"
)
_RUT_ENMASCARADO = re.compile(r"^[0-9]{1,2}\.XXX\.XXX-[0-9K]$")
_TELEFONO_ENMASCARADO = re.compile(r"^\+56 9 XXXX [0-9]{4}$")


def mask_rut(rut: str) -> str:
    if not isinstance(rut, str):
        return "[RUT REDACTADO]"
    rut = rut.strip().upper()
    if _RUT_ENMASCARADO.fullmatch(rut):
        return rut
    coincidencia = _RUT_COMPLETO.fullmatch(rut)
    if coincidencia is None:
        return "[RUT REDACTADO]"
    cuerpo = coincidencia.group("cuerpo").replace(".", "")
    return f"{cuerpo[:-6]}.XXX.XXX-{coincidencia.group('dv').upper()}"


def mask_phone(telefono: str) -> str:
    if not isinstance(telefono, str):
        return "[TELÉFONO REDACTADO]"
    telefono = telefono.strip()
    if _TELEFONO_ENMASCARADO.fullmatch(telefono):
        return telefono
    digitos = re.sub(r"\D", "", telefono)
    if len(digitos) == 11 and digitos.startswith("569"):
        numero_local = digitos[2:]
    elif len(digitos) == 9 and digitos.startswith("9"):
        numero_local = digitos
    else:
        return "[TELÉFONO REDACTADO]"
    return f"+56 9 XXXX {numero_local[-4:]}"


class Enmascarador:

    @staticmethod
    def correo(correo):
        usuario, dominio = correo.split("@")
        if len(usuario) <= 2:
            return "*" * len(usuario) + "@" + dominio
        return f"{usuario[:2]}{'*' * (len(usuario) - 2)}@{dominio}"

    @staticmethod
    def rut(rut):
        return mask_rut(rut)

    @staticmethod
    def telefono(telefono):
        return mask_phone(telefono)