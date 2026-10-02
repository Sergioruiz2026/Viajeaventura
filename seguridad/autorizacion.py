"""Verificación de rol y vigencia de sesiones."""

from excepciones import AutorizacionError
from modelos.sesion import Sesion


def exigir_rol(sesion, rol_requerido):
    if not isinstance(sesion, Sesion):
        raise AutorizacionError("Se requiere una sesión autenticada.")
    sesion.renovar()
    if sesion.rol != rol_requerido:
        raise AutorizacionError("No tiene autorización para esta acción.")