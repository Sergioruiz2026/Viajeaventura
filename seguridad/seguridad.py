"""Hash Argon2id y cifrado Fernet para datos sensibles."""

import os
import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet, InvalidToken


_PASSWORD_HASHER = PasswordHasher()


def hash_password(password: str) -> str:
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if not isinstance(hashed, str):
        return False
    if not hashed.startswith("$argon2id$"):
        return _verify_legacy_pbkdf2(password, hashed)
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (InvalidHashError, VerificationError, TypeError):
        return False


def _verify_legacy_pbkdf2(password: str, hashed: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, expected = hashed.split("$")
        iterations = int(iterations_text)
        if algorithm != "pbkdf2_sha256" or not 1 <= iterations <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (AttributeError, OverflowError, TypeError, ValueError):
        return False


def _fernet() -> Fernet:
    key = os.environ.get("VIAJES_FERNET_KEY")
    if not key:
        raise RuntimeError(
            "Configure VIAJES_FERNET_KEY con una clave Fernet válida."
        )
    try:
        return Fernet(key.encode("ascii"))
    except (UnicodeEncodeError, ValueError) as error:
        raise RuntimeError("VIAJES_FERNET_KEY no es válida.") from error


def encrypt_data(plain_text: str) -> str:
    return _fernet().encrypt(plain_text.encode("utf-8")).decode("ascii")


def decrypt_data(cipher_text: str) -> str:
    try:
        return _fernet().decrypt(cipher_text.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, AttributeError) as error:
        raise ValueError("El dato cifrado no es válido.") from error