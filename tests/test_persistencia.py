import hashlib
import os
import secrets
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from modelos.destino import Destino
from modelos.cliente import Cliente
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.reserva_servicio import ReservaServicio
from cryptography.fernet import Fernet


class PersistenciaSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.clave_fernet_original = os.environ.get("VIAJES_FERNET_KEY")
        os.environ["VIAJES_FERNET_KEY"] = Fernet.generate_key().decode()
        self.directorio = tempfile.TemporaryDirectory()
        self.ruta = str(Path(self.directorio.name) / "viajes.db")
        self.base_datos = BaseDatos(self.ruta)

    def tearDown(self):
        self.base_datos.cerrar()
        self.directorio.cleanup()
        if self.clave_fernet_original is None:
            os.environ.pop("VIAJES_FERNET_KEY", None)
        else:
            os.environ["VIAJES_FERNET_KEY"] = self.clave_fernet_original

    def test_rut_y_telefono_se_guardan_cifrados(self):
        clientes = ClienteRepositorio(self.base_datos)
        cliente = AutenticacionServicio(clientes).registrar_cliente(
            "Ana",
            "12345678-9",
            "ana@example.com",
            "+56912345678",
            "ClaveFuerte1"
        )

        fila = self.base_datos.conexion.execute(
            "SELECT rut, telefono FROM clientes WHERE correo = ?",
            (cliente.correo,)
        ).fetchone()

        self.assertNotEqual(fila["rut"], cliente.rut)
        self.assertNotEqual(fila["telefono"], cliente.telefono)
        self.assertEqual(clientes.buscar_por_rut(cliente.rut).telefono,
                         cliente.telefono)

    def test_migra_rut_y_telefono_heredados_en_texto_claro(self):
        self.base_datos.conexion.execute(
            """
            INSERT INTO clientes (
                nombre, rut, correo, telefono, password_hash
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("Ana", "12345678-9", "ana@example.com", "+56912345678", "hash")
        )
        self.base_datos.conexion.commit()

        clientes = ClienteRepositorio(self.base_datos)
        fila = self.base_datos.conexion.execute(
            "SELECT rut, telefono FROM clientes"
        ).fetchone()

        self.assertNotEqual(fila["rut"], "12345678-9")
        self.assertNotEqual(fila["telefono"], "+56912345678")
        self.assertEqual(
            clientes.buscar_por_rut("12345678-9").telefono,
            "+56912345678"
        )

    def test_login_migra_hash_pbkdf2_a_argon2id(self):
        clientes = ClienteRepositorio(self.base_datos)
        password = "ClaveFuerte1"
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 1_000)
        legacy_hash = f"pbkdf2_sha256$1000${salt.hex()}${digest.hex()}"
        clientes.agregar(Cliente(
            "Ana", "12345678-9", "ana@example.com", "+56912345678", legacy_hash
        ))

        cliente = AutenticacionServicio(clientes).iniciar_sesion(
            "ana@example.com", password
        )
        hash_guardado = self.base_datos.conexion.execute(
            "SELECT password_hash FROM clientes WHERE correo = ?",
            (cliente.correo,)
        ).fetchone()["password_hash"]

        self.assertTrue(hash_guardado.startswith("$argon2id$"))

    def test_cliente_paquete_y_reserva_sobreviven_reapertura(self):
        clientes = ClienteRepositorio(self.base_datos)
        destinos = DestinoRepositorio(self.base_datos)
        paquetes = PaqueteRepositorio(self.base_datos)
        reservas = ReservaRepositorio(self.base_datos)

        cliente = AutenticacionServicio(clientes).registrar_cliente(
            "Ana",
            "12345678-9",
            "ana@example.com",
            "+56912345678",
            "ClaveFuerte1"
        )
        destinos.agregar(Destino("Norte", "Norte", "Desierto", 4, 100))
        destinos.agregar(Destino("Sur", "Sur", "Lagos", 5, 200))

        salida = date.today() + timedelta(days=30)
        PaqueteServicio(paquetes, destinos).crear_paquete(
            "Ruta Chile",
            ["Norte", "Sur"],
            salida,
            salida + timedelta(days=7),
            4
        )
        ReservaServicio(reservas, paquetes).crear_reserva(
            cliente,
            "Ruta Chile",
            2
        )
        self.base_datos.cerrar()

        self.base_datos = BaseDatos(self.ruta)
        clientes = ClienteRepositorio(self.base_datos)
        destinos = DestinoRepositorio(self.base_datos)
        paquetes = PaqueteRepositorio(self.base_datos)
        reservas = ReservaRepositorio(self.base_datos)

        cliente_guardado = clientes.buscar_por_correo("ANA@example.com")
        paquete_guardado = paquetes.buscar_por_nombre("ruta chile")
        reservas_guardadas = reservas.reservas_por_cliente(
            "ana@example.com"
        )

        self.assertIsNotNone(cliente_guardado)
        self.assertEqual(cliente_guardado.nombre, "Ana")
        self.assertEqual(len(destinos.listar()), 2)
        self.assertEqual(
            [destino.nombre for destino in paquete_guardado.destinos],
            ["Norte", "Sur"]
        )
        self.assertEqual(paquete_guardado.precio_por_persona, 360)
        self.assertEqual(len(reservas_guardadas), 1)
        self.assertEqual(reservas_guardadas[0].cantidad_personas, 2)
        self.assertEqual(reservas_guardadas[0].total, 720)
        self.assertEqual(reservas.cupos_ocupados("Ruta Chile"), 2)


if __name__ == "__main__":
    unittest.main()