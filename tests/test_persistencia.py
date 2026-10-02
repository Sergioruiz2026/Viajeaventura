import hashlib
import os
import secrets
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from excepciones import AutorizacionError, CorreoDuplicadoError, ValidacionError
from modelos.destino import Destino
from modelos.cliente import Cliente
from modelos.sesion import Sesion
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
            "12.345.678-5",
            "ana@example.com",
            "+56912345678",
            "ClaveFuerte1!"
        )

        fila = self.base_datos.conexion.execute(
            "SELECT rut, telefono FROM usuarios WHERE correo = ?",
            (cliente.correo,)
        ).fetchone()

        self.assertNotEqual(fila["rut"], cliente.rut)
        self.assertNotEqual(fila["telefono"], cliente.telefono)
        self.assertEqual(clientes.buscar_por_rut(cliente.rut).telefono,
                         cliente.telefono)

    def test_registro_exige_rut_mod11_y_correo_unico(self):
        clientes = ClienteRepositorio(self.base_datos)
        servicio = AutenticacionServicio(clientes)
        cliente = servicio.registrar_cliente(
            "Ana", "12345678-5", "ana@example.com", "+56912345678",
            "ClaveFuerte1!"
        )
        fila = self.base_datos.conexion.execute(
            "SELECT rut, telefono, password_hash FROM usuarios WHERE id = 1"
        ).fetchone()

        self.assertTrue(fila["password_hash"].startswith("$argon2id$"))
        self.assertNotEqual(fila["rut"], cliente.rut)
        self.assertNotEqual(fila["telefono"], cliente.telefono)

        with self.assertRaises(CorreoDuplicadoError):
            servicio.registrar_cliente(
                "Otra", "12.345.678-5", "ANA@example.com", "+56987654321",
                "ClaveFuerte2!"
            )

        with self.assertRaises(ValidacionError):
            servicio.registrar_cliente(
                "Inválido", "12.345.678-9", "otro@example.com",
                "+56987654321", "ClaveFuerte2!"
            )

    def test_migra_rut_y_telefono_heredados_en_texto_claro(self):
        self.base_datos.conexion.execute(
            """
            INSERT INTO usuarios (
                nombre, rut, correo, telefono, password_hash
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("Ana", "12345678-9", "ana@example.com", "+56912345678", "hash")
        )
        self.base_datos.conexion.commit()

        clientes = ClienteRepositorio(self.base_datos)
        fila = self.base_datos.conexion.execute(
            "SELECT rut, telefono FROM usuarios"
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
            "SELECT password_hash FROM usuarios WHERE correo = ?",
            (cliente.correo,)
        ).fetchone()["password_hash"]

        self.assertTrue(hash_guardado.startswith("$argon2id$"))

    def test_cliente_paquete_y_reserva_sobreviven_reapertura(self):
        clientes = ClienteRepositorio(self.base_datos)
        destinos = DestinoRepositorio(self.base_datos)
        paquetes = PaqueteRepositorio(self.base_datos)
        reservas = ReservaRepositorio(self.base_datos)

        autenticacion = AutenticacionServicio(clientes)
        autenticacion.registrar_cliente(
            "Ana",
            "12.345.678-5",
            "ana@example.com",
            "+56912345678",
            "ClaveFuerte1!"
        )
        sesion_cliente = autenticacion.iniciar_sesion(
            "ana@example.com", "ClaveFuerte1!"
        )
        sesion_admin = Sesion.administrador("admin")
        destinos.agregar(Destino("Norte", "Norte", "Desierto", 4, 100))
        destinos.agregar(Destino("Sur", "Sur", "Lagos", 5, 200))

        salida = date.today() + timedelta(days=30)
        PaqueteServicio(paquetes, destinos).crear_paquete(
            "Ruta Chile",
            ["Norte", "Sur"],
            salida,
            salida + timedelta(days=7),
            4,
            sesion=sesion_admin
        )
        paquete_id = self.base_datos.conexion.execute(
            "SELECT id FROM paquetes WHERE nombre = ?",
            ("Ruta Chile",)
        ).fetchone()["id"]
        servicio_reservas = ReservaServicio(reservas, paquetes)
        servicio_reservas.crear_reserva(
            sesion_cliente,
            paquete_id,
            2
        )
        with self.assertRaises(AutorizacionError):
            servicio_reservas.crear_reserva(
                sesion_admin, paquete_id, 1
            )
        with self.assertRaises(AutorizacionError):
            servicio_reservas.reservas_cliente(sesion_admin)
        with self.assertRaises(AutorizacionError):
            servicio_reservas.listar_reservas(sesion=sesion_cliente)
        self.assertEqual(
            len(servicio_reservas.listar_reservas(sesion=sesion_admin)), 1
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

    def test_constraints_sql_relacion_y_cupo_transaccional(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.base_datos.transaccion() as conexion:
                conexion.execute(
                    """
                    INSERT INTO destinos (
                        nombre, zona, descripcion, duracion_dias, costo_base
                    ) VALUES ('Inválido', 'Norte', 'Descripción', 0, 100)
                    """
                )
        self.assertEqual(
            self.base_datos.conexion.execute(
                "SELECT COUNT(*) FROM destinos"
            ).fetchone()[0],
            0
        )

        clientes = ClienteRepositorio(self.base_datos)
        autenticacion = AutenticacionServicio(clientes)
        autenticacion.registrar_cliente(
            "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
            "ClaveFuerte1!"
        )
        sesion_cliente = autenticacion.iniciar_sesion(
            "ana@example.com", "ClaveFuerte1!"
        )
        destinos = DestinoRepositorio(self.base_datos)
        destinos.agregar(Destino("Norte", "Norte", "Desierto", 4, 100))
        destinos.agregar(Destino("Sur", "Sur", "Lagos", 5, 200))
        paquetes = PaqueteRepositorio(self.base_datos)
        salida = date.today() + timedelta(days=30)
        PaqueteServicio(paquetes, destinos).crear_paquete(
            "Cupo unitario", ["Norte", "Sur"], salida,
            salida + timedelta(days=4), 1,
            sesion=Sesion.administrador("admin")
        )
        paquete_id = self.base_datos.conexion.execute(
            "SELECT id FROM paquetes WHERE nombre = ?",
            ("Cupo unitario",)
        ).fetchone()["id"]
        ReservaServicio(
            ReservaRepositorio(self.base_datos), paquetes
        ).crear_reserva(sesion_cliente, paquete_id, 1)

        usuario_id = self.base_datos.conexion.execute(
            "SELECT id FROM usuarios WHERE correo = ?",
            (sesion_cliente.correo,)
        ).fetchone()["id"]
        with self.assertRaises(sqlite3.IntegrityError):
            with self.base_datos.transaccion() as conexion:
                conexion.execute(
                    """
                    INSERT INTO reservas (
                        usuario_id, paquete_id, cantidad_personas,
                        fecha_emision, total
                    ) VALUES (?, ?, 1, ?, ?)
                    """,
                    (usuario_id, paquete_id, date.today().isoformat(), 360)
                )
        self.assertEqual(
            ReservaRepositorio(self.base_datos).cupos_ocupados(
                "Cupo unitario"
            ),
            1
        )

    def test_paquete_exige_entre_dos_y_cinco_destinos(self):
        destinos = DestinoRepositorio(self.base_datos)
        for numero in range(6):
            destinos.agregar(Destino(
                f"Destino {numero}", "Zona", "Descripción", 2, 100
            ))
        filas_destino = self.base_datos.conexion.execute(
            "SELECT id FROM destinos ORDER BY id"
        ).fetchall()

        with self.assertRaises(sqlite3.IntegrityError):
            with self.base_datos.transaccion() as conexion:
                cursor = conexion.execute(
                    """
                    INSERT INTO paquetes (
                        nombre, fecha_salida, fecha_regreso, cupo_maximo,
                        margen_operacion, precio_publicado
                    ) VALUES ('Seis destinos', '2026-11-01', '2026-11-02', 2, 0.2, 600)
                    """
                )
                for orden, fila in enumerate(filas_destino):
                    conexion.execute(
                        """
                        INSERT INTO paquete_destinos (
                            paquete_id, destino_id, orden
                        ) VALUES (?, ?, ?)
                        """,
                        (cursor.lastrowid, fila["id"], orden)
                    )
        with self.assertRaises(sqlite3.IntegrityError):
            with self.base_datos.transaccion() as conexion:
                conexion.execute(
                    """
                    INSERT INTO paquetes (
                        nombre, fecha_salida, fecha_regreso, cupo_maximo,
                        margen_operacion, precio_publicado
                    ) VALUES ('Sin destinos', '2026-11-01', '2026-11-02', 2, 0.2, 0)
                    """
                )

    def test_migra_usuarios_desde_base_legacy_sin_modificar_origen(self):
        ruta_legacy = Path(self.directorio.name) / "legacy.db"
        conexion_legacy = sqlite3.connect(ruta_legacy)
        conexion_legacy.executescript(
            """
            CREATE TABLE destinos (
                id INTEGER PRIMARY KEY, nombre TEXT, zona TEXT,
                descripcion TEXT, duracion_dias INTEGER,
                costo_base REAL, disponible INTEGER
            );
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY, nombre TEXT, rut TEXT,
                correo TEXT, telefono TEXT, password_hash TEXT
            );
            INSERT INTO clientes VALUES (
                7, 'Ana', '12345678-9', 'ana@example.com',
                '+56912345678', 'hash-legacy'
            );
            """
        )
        conexion_legacy.commit()
        conexion_legacy.close()

        clientes = ClienteRepositorio(self.base_datos)
        self.base_datos.migrar_desde(ruta_legacy)
        fila = self.base_datos.conexion.execute(
            "SELECT id, rut, telefono, password_hash FROM usuarios"
        ).fetchone()

        self.assertEqual(fila["id"], 7)
        self.assertNotEqual(fila["rut"], "12345678-9")
        self.assertNotEqual(fila["telefono"], "+56912345678")
        self.assertEqual(fila["password_hash"], "hash-legacy")
        cliente = clientes.buscar_por_correo("ana@example.com")
        self.assertEqual(cliente.rut, "12345678-9")
        conexion_legacy = sqlite3.connect(ruta_legacy)
        rut_origen = conexion_legacy.execute(
            "SELECT rut FROM clientes WHERE id = 7"
        ).fetchone()[0]
        conexion_legacy.close()
        self.assertEqual(rut_origen, "12345678-9")


if __name__ == "__main__":
    unittest.main()