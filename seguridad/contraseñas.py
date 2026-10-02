"""Compatibilidad del servicio de autenticación con hashes Argon2id."""

from seguridad.seguridad import hash_password, verify_password


class GestorContrasenas:
    @staticmethod
    def generar_hash(password):
        return hash_password(password)

    @staticmethod
    def verificar(password, password_hash):
        return verify_password(password, password_hash)