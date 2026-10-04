"""Verificación de rol y vigencia de sesiones."""

from excepciones import AutorizacionError
from modelos.sesion import Sesion


def exigir_rol(sesion, rol_requerido):
    if not isinstance(sesion, Sesion):
        raise AutorizacionError("Se requiere una sesión autenticada.")
    sesion.renovar()
    if sesion.rol != rol_requerido:
        raise AutorizacionError("No tiene autorización para esta acción.")


def exigir_permiso_reserva(sesion):
    if not isinstance(sesion, Sesion):
        raise AutorizacionError("Se requiere una sesión autenticada.")
    sesion.renovar()
    usuario = sesion.usuario
    if usuario is None or not usuario.puede_reservar():
        raise AutorizacionError("No tiene autorización para esta acción.")