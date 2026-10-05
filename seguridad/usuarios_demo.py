"""Credenciales reproducibles para instalaciones locales de demostración."""

import os

from modelos.administrador import Administrador
from seguridad.contraseñas import GestorContrasenas


USUARIO_DEMO_CLIENTE = "cliente.demo@viajeaventura.local"
PASSWORD_DEMO_CLIENTE = "ClienteDemo1!"
USUARIO_DEMO_ADMIN = "admin-demo"
PASSWORD_DEMO_ADMIN = "AdminDemo1!"


def asegurar_usuarios_demo(cliente_repo, autenticacion):
    """Crea las cuentas públicas de demo sin modificar cuentas existentes."""
    if os.environ.get("VIAJES_DEMO_USUARIOS", "1").strip().lower() in {
        "0",
        "false",
        "no",
    }:
        return

    if cliente_repo.buscar_por_correo(USUARIO_DEMO_CLIENTE) is None:
        autenticacion.registrar_cliente(
            "Cliente Demo",
            "12.345.678-5",
            USUARIO_DEMO_CLIENTE,
            "+56987654321",
            PASSWORD_DEMO_CLIENTE,
        )

    if cliente_repo.buscar_por_correo(USUARIO_DEMO_ADMIN) is None:
        cliente_repo.agregar(Administrador(
            USUARIO_DEMO_ADMIN,
            GestorContrasenas.generar_hash(PASSWORD_DEMO_ADMIN),
            nombre="Administrador Demo",
        ))
