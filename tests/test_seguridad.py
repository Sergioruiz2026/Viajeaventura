import logging
import os
import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet

from excepciones import ValidacionError
from seguridad.enmascarado import mask_phone, mask_rut
from seguridad.logging_config import FiltroDatosSensibles
from seguridad.montos import aplicar_margen_clp, redondear_clp
from seguridad.validadores import Validador
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
        self.assertIn("12.XXX.XXX-9", registro.getMessage())
        self.assertIn("+56 9 XXXX 5678", registro.getMessage())

    def test_mascaras_de_rut_y_telefono(self):
        self.assertEqual(mask_rut("12.345.678-K"), "12.XXX.XXX-K")
        self.assertEqual(mask_rut("12345678-5"), "12.XXX.XXX-5")
        self.assertEqual(mask_phone("+56912341234"), "+56 9 XXXX 1234")
        self.assertEqual(
            mask_phone("+56 9 1234 1234"), "+56 9 XXXX 1234"
        )
        self.assertEqual(mask_rut("dato inválido"), "[RUT REDACTADO]")
        self.assertEqual(
            mask_phone("dato inválido"), "[TELÉFONO REDACTADO]"
        )

    def test_validadores_de_rut_mod11_y_password_con_caracter_especial(self):
        Validador.validar_rut("12.345.678-5")
        Validador.validar_rut("11111111-1")
        for rut in ("12.345.678-9", "12345678-9", "rut-invalido"):
            with self.subTest(rut=rut), self.assertRaises(ValidacionError):
                Validador.validar_rut(rut)

        Validador.validar_contrasena("ClaveFuerte1!")
        with self.assertRaises(ValidacionError):
            Validador.validar_contrasena("ClaveFuerte1")


if __name__ == "__main__":
    unittest.main()