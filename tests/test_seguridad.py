import logging
import os
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from seguridad.logging_config import FiltroDatosSensibles
from seguridad.montos import aplicar_margen_clp, redondear_clp
from seguridad.seguridad import (
    decrypt_data,
    encrypt_data,
    hash_password,
    verify_password,
)


class SeguridadTests(unittest.TestCase):
    def setUp(self):
        self.entorno = patch.dict(os.environ, {
            "VIAJES_FERNET_KEY": Fernet.generate_key().decode()
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)

    def test_hash_argon2id_verifica_sin_guardar_clave(self):
        hashed = hash_password("ClaveFuerte1")

        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertTrue(verify_password("ClaveFuerte1", hashed))
        self.assertFalse(verify_password("otra-clave", hashed))
        self.assertFalse(verify_password("ClaveFuerte1", "hash-invalido"))

    def test_cifrado_fernet_hace_round_trip(self):
        texto = "+56912345678"

        cifrado = encrypt_data(texto)

        self.assertNotEqual(cifrado, texto)
        self.assertEqual(decrypt_data(cifrado), texto)

    def test_montos_clp_usando_decimal_y_redondeo_half_up(self):
        self.assertEqual(aplicar_margen_clp("100.10", "0.10"), 110)
        self.assertEqual(redondear_clp("10.5"), 11)
        self.assertEqual(redondear_clp("10.4"), 10)

    def test_filtro_enmascara_datos_sensibles(self):
        registro = logging.LogRecord(
            "test", logging.INFO, "", 0,
            "rut=12345678-9 telefono=+56912345678 password=Clave Fuerte1",
            (), None
        )

        self.assertTrue(FiltroDatosSensibles().filter(registro))
        self.assertNotIn("12345678-9", registro.getMessage())
        self.assertNotIn("+56912345678", registro.getMessage())
        self.assertNotIn("Clave Fuerte1", registro.getMessage())


if __name__ == "__main__":
    unittest.main()