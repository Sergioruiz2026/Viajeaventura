"""Credenciales reproducibles para instalaciones locales de demostración."""

import os

from modelos.administrador import Administrador
from seguridad.contraseñas import GestorContrasenas


USUARIO_DEMO_CLIENTE = "cliente.demo@viajeaventura.local"
PASSWORD_DEMO_CLIENTE = "ClienteDemo1!"
USUARIO_DEMO_ADMIN = "admin-demo"
PASSWORD_DEMO_ADMIN = "AdminDemo1!"

_CUERPO_RUT_DEMO_INICIAL = 12_345_678
_USUARIOS_DEMO = frozenset({
    USUARIO_DEMO_CLIENTE.casefold(),
    USUARIO_DEMO_ADMIN.casefold(),
})


def usuarios_demo_habilitados():
    return os.environ.get("VIAJES_DEMO_USUARIOS", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "si",
    }


def es_usuario_demo(usuario):
    return isinstance(usuario, str) and usuario.casefold() in _USUARIOS_DEMO


def _digito_verificador_rut(cuerpo):
    suma = sum(
        int(digito) * (indice % 6 + 2)
        for indice, digito in enumerate(reversed(str(cuerpo)))
    )
    resultado = 11 - suma % 11
    return (
        "0" if resultado == 11 else "K" if resultado == 10 else str(resultado)
    )


def _rut_demo_disponible(cliente_repo):
    rangos = (
        (_CUERPO_RUT_DEMO_INICIAL, 100_000_000),
        (10_000_000, _CUERPO_RUT_DEMO_INICIAL),
    )
    for inicio, limite in rangos:
        for cuerpo in range(inicio, limite):
            cuerpo_formateado = f"{cuerpo:,}".replace(",", ".")
            rut = f"{cuerpo_formateado}-{_digito_verificador_rut(cuerpo)}"
            if cliente_repo.buscar_por_rut(rut) is None:
                return rut
    raise RuntimeError("No hay un RUT disponible para la cuenta de demostración.")


def asegurar_usuarios_demo(cliente_repo, autenticacion):
    """Crea las cuentas públicas de demo sin modificar cuentas existentes."""
    if not usuarios_demo_habilitados():
        return

    if cliente_repo.buscar_por_correo(USUARIO_DEMO_CLIENTE) is None:
        autenticacion.registrar_cliente(
            "Cliente Demo",
            _rut_demo_disponible(cliente_repo),
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
