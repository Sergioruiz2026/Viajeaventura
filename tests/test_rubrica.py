import os
import unittest
from datetime import datetime
from unittest.mock import patch

from cryptography.fernet import Fernet

from excepciones import AutenticacionError, ValidacionError
from modelos.administrador import Administrador
from modelos.cliente import Cliente
from modelos.usuario import Usuario
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio
from seguridad.validadores import Validador


class RubricaTests(unittest.TestCase):
    def setUp(self):
        self.entorno = patch.dict(os.environ, {
            "VIAJES_FERNET_KEY": Fernet.generate_key().decode("ascii")
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.base_datos = BaseDatos(":memory:")
        self.addCleanup(self.base_datos.cerrar)
        self.repositorio = ClienteRepositorio(self.base_datos)
        self.autenticacion = AutenticacionServicio(self.repositorio)

    def test_uml_usuario_cliente_administrador_y_permisos(self):
        self.assertTrue(issubclass(Cliente, Usuario))
        self.assertTrue(issubclass(Administrador, Usuario))
        self.assertTrue(Cliente(
            "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
            "hash"
        ).puede_reservar())
        self.assertFalse(Administrador("admin").puede_reservar())

    def test_politica_de_contrasena_tiene_limite_superior(self):
        with self.assertRaises(ValidacionError):
            Validador.validar_contrasena("A1!" + "a" * 128)

    def test_correo_inexistente_y_cuenta_bloqueada_comparten_mensaje(self):
        mensaje = "Correo o contraseña incorrectos."
        with self.assertRaisesRegex(AutenticacionError, mensaje):
            self.autenticacion.iniciar_sesion(
                "noexiste@example.com", "ClaveFuerte1!"
            )
        self.autenticacion.registrar_cliente(
            "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
            "ClaveFuerte1!"
        )
        ahora = datetime(2026, 10, 4, 12, 0, 0)
        for _ in range(5):
            with self.assertRaisesRegex(AutenticacionError, mensaje):
                self.autenticacion.iniciar_sesion(
                    "ana@example.com", "incorrecta", ahora=ahora
                )
        with self.assertRaisesRegex(AutenticacionError, mensaje):
            self.autenticacion.iniciar_sesion(
                "ana@example.com", "ClaveFuerte1!", ahora=ahora
            )


if __name__ == "__main__":
    unittest.main()
