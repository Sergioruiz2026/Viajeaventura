""""implementación de la clase GestorContrasenas para generar y verificar hashes de contraseñas. generando la
seguridad de las contraseñas de los clientes y administradores del proyecto ViajesAventura"""


import hashlib
import hmac
import secrets

"""Genera el hash SHA-256 de una contraseña."""
class GestorContrasenas:

    ITERACIONES = 600_000

    @staticmethod
    def generar_hash(password):
        sal = secrets.token_bytes(16)
        derivado = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            sal,
            GestorContrasenas.ITERACIONES
        )
        return (
            f"pbkdf2_sha256${GestorContrasenas.ITERACIONES}$"
            f"{sal.hex()}${derivado.hex()}"
        )

    @staticmethod
    def verificar(password, password_hash):
        try:
            algoritmo, iteraciones, sal_hex, derivado_esperado = (
                password_hash.split("$")
            )
            if algoritmo != "pbkdf2_sha256":
                return False
            derivado = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(sal_hex),
                int(iteraciones)
            ).hex()
        except (AttributeError, ValueError):
            return False
        return hmac.compare_digest(derivado, derivado_esperado)