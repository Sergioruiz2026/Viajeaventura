import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet

from excepciones import AutenticacionError, SesionExpiradaError
from modelos.cliente import Cliente
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio


class AutenticacionSeguraTests(unittest.TestCase):
    def setUp(self):
        self.entorno = patch.dict(os.environ, {
            "VIAJES_FERNET_KEY": Fernet.generate_key().decode()
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.base_datos = BaseDatos(":memory:")
        self.addCleanup(self.base_datos.cerrar)
        self.repositorio = ClienteRepositorio(self.base_datos)
        self.servicio = AutenticacionServicio(self.repositorio)
        self.servicio.registrar_cliente(
            "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
            "ClaveFuerte1!"
        )
        self.ahora = datetime(2026, 10, 2, 12, 0, 0)

    def test_credenciales_invalidas_siempre_tienen_mensaje_generico(self):
        mensajes = []
        for correo, password in (
            ("ana@example.com", "incorrecta"),
            ("noexiste@example.com", "incorrecta")
        ):
            with self.assertRaises(AutenticacionError) as contexto:
                self.servicio.iniciar_sesion(
                    correo, password, ahora=self.ahora
                )
            mensajes.append(str(contexto.exception))
        self.assertEqual(mensajes, [
            "Correo o contraseña incorrectos.",
            "Correo o contraseña incorrectos."
        ])

    def test_bloquea_al_quinto_fallo_y_permite_login_a_los_15_minutos(self):
        for _ in range(5):
            with self.assertRaisesRegex(
                AutenticacionError, "Correo o contraseña incorrectos"
            ):
                self.servicio.iniciar_sesion(
                    "ana@example.com", "incorrecta", ahora=self.ahora
                )

        fila = self.base_datos.conexion.execute(
            "SELECT intentos_fallidos, bloqueado_hasta FROM usuarios"
        ).fetchone()
        self.assertEqual(fila["intentos_fallidos"], 5)
        self.assertEqual(
            datetime.fromisoformat(fila["bloqueado_hasta"]),
            self.ahora + timedelta(minutes=15)
        )
        with self.assertRaises(AutenticacionError):
            self.servicio.iniciar_sesion(
                "ana@example.com", "ClaveFuerte1!",
                ahora=self.ahora + timedelta(minutes=14)
            )

        sesion = self.servicio.iniciar_sesion(
            "ana@example.com", "ClaveFuerte1!",
            ahora=self.ahora + timedelta(minutes=15)
        )
        self.assertEqual(sesion.rol, "CLIENTE")
        fila = self.base_datos.conexion.execute(
            "SELECT intentos_fallidos, bloqueado_hasta FROM usuarios"
        ).fetchone()
        self.assertEqual(fila["intentos_fallidos"], 0)
        self.assertIsNone(fila["bloqueado_hasta"])

    def test_sesion_expira_tras_30_minutos_inactiva(self):
        sesion = self.servicio.iniciar_sesion(
            "ana@example.com", "ClaveFuerte1!", ahora=self.ahora
        )

        with self.assertRaises(SesionExpiradaError):
            sesion.renovar(self.ahora + timedelta(minutes=30))

    def test_persiste_y_recupera_rol_admin(self):
        administrador = Cliente(
            "Admin", "", "admin@example.com", "", "hash", "ADMIN"
        )
        self.repositorio.agregar(administrador)

        self.assertEqual(
            self.repositorio.buscar_por_correo("admin@example.com").rol,
            "ADMIN"
        )


if __name__ == "__main__":
    unittest.main()