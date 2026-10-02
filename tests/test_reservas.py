import os
import sqlite3
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet

from excepciones import (
    CupoInsuficienteError,
    ReservaNoPermitidaError,
    ValidacionError
)
from modelos.destino import Destino
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.reserva_servicio import ReservaServicio
from modelos.sesion import Sesion


class CrearReservasTests(unittest.TestCase):
    def setUp(self):
        self.entorno = patch.dict(os.environ, {
            "VIAJES_FERNET_KEY": Fernet.generate_key().decode()
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.base_datos = BaseDatos(":memory:")
        self.addCleanup(self.base_datos.cerrar)
        self.clientes = ClienteRepositorio(self.base_datos)
        autenticacion = AutenticacionServicio(self.clientes)
        autenticacion.registrar_cliente(
            "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
            "ClaveFuerte1!"
        )
        autenticacion.registrar_cliente(
            "Bea", "11.111.111-1", "bea@example.com", "+56987654321",
            "ClaveFuerte2!"
        )
        self.sesion_ana = autenticacion.iniciar_sesion(
            "ana@example.com", "ClaveFuerte1!"
        )
        self.sesion_bea = autenticacion.iniciar_sesion(
            "bea@example.com", "ClaveFuerte2!"
        )
        self.paquetes = PaqueteRepositorio(self.base_datos)
        self.reservas = ReservaRepositorio(self.base_datos)
        self.servicio = ReservaServicio(self.reservas, self.paquetes)
        self.destinos = DestinoRepositorio(self.base_datos)
        self.destinos.agregar(Destino("Norte", "Zona", "Desierto", 3, 100))
        self.destinos.agregar(Destino("Sur", "Zona", "Lagos", 4, 200))
        self.admin = Sesion.administrador("admin")
        self.id_paquete = self.crear_paquete("Ruta", cupo=3)

    def crear_paquete(self, nombre, cupo, salida=None):
        salida = salida or date.today() + timedelta(days=30)
        PaqueteServicio(self.paquetes, self.destinos).crear_paquete(
            nombre,
            ["Norte", "Sur"],
            salida,
            salida + timedelta(days=5),
            cupo,
            sesion=self.admin
        )
        return self.base_datos.conexion.execute(
            "SELECT id FROM paquetes WHERE nombre = ?", (nombre,)
        ).fetchone()["id"]

    def test_reserva_por_id_guarda_fecha_actual_y_total_publicado(self):
        reserva = self.servicio.crear_reserva(
            self.sesion_ana, self.id_paquete, 2
        )

        self.assertEqual(reserva.paquete.id, self.id_paquete)
        self.assertEqual(reserva.total, 720)
        self.assertEqual(reserva.fecha_emision.date(), date.today())
        self.assertIn(f"#{self.id_paquete}", str(reserva.paquete))

    def test_rechaza_cantidad_invalida_paquete_inexistente_y_fecha_pasada(self):
        for cantidad in (0, -1, True, 1.5):
            with self.subTest(cantidad=cantidad), self.assertRaises(ValidacionError):
                self.servicio.crear_reserva(
                    self.sesion_ana, self.id_paquete, cantidad
                )

        with self.assertRaises(ReservaNoPermitidaError):
            self.servicio.crear_reserva(self.sesion_ana, -1, 1)

        id_vencido = self.crear_paquete(
            "Vencido", cupo=2, salida=date.today() - timedelta(days=1)
        )
        with self.assertRaises(ReservaNoPermitidaError):
            self.servicio.crear_reserva(self.sesion_ana, id_vencido, 1)

    def test_cupo_se_calcula_con_reservas_activas_en_transaccion(self):
        self.servicio.crear_reserva(self.sesion_ana, self.id_paquete, 2)

        with self.assertRaises(CupoInsuficienteError):
            self.servicio.crear_reserva(self.sesion_bea, self.id_paquete, 2)

        self.assertEqual(len(self.reservas.listar()), 1)
        self.assertEqual(self.reservas.cupos_ocupados("Ruta"), 2)

    def test_impide_duplicado_activo_y_permite_reservar_tras_cancelacion(self):
        self.servicio.crear_reserva(self.sesion_ana, self.id_paquete, 1)

        with self.assertRaises(ReservaNoPermitidaError):
            self.servicio.crear_reserva(self.sesion_ana, self.id_paquete, 1)

        usuario_id = self.base_datos.conexion.execute(
            "SELECT id FROM usuarios WHERE correo = ?", ("ana@example.com",)
        ).fetchone()["id"]
        with self.assertRaises(sqlite3.IntegrityError):
            with self.base_datos.transaccion() as conexion:
                conexion.execute(
                    """
                    INSERT INTO reservas (
                        usuario_id, paquete_id, cantidad_personas,
                        fecha_emision, total
                    ) VALUES (?, ?, 1, ?, 360)
                    """,
                    (usuario_id, self.id_paquete, date.today().isoformat())
                )

        self.base_datos.conexion.execute(
            "UPDATE reservas SET estado = 'CANCELADA' "
            "WHERE usuario_id = (SELECT id FROM usuarios WHERE correo = ?) "
            "AND paquete_id = ?",
            ("ana@example.com", self.id_paquete)
        )
        self.base_datos.conexion.commit()

        nueva = self.servicio.crear_reserva(
            self.sesion_ana, self.id_paquete, 2
        )

        self.assertEqual(nueva.cantidad_personas, 2)
        filas = self.base_datos.conexion.execute(
            "SELECT estado FROM reservas ORDER BY id"
        ).fetchall()
        self.assertEqual([fila["estado"] for fila in filas], ["CANCELADA", "ACTIVA"])


if __name__ == "__main__":
    unittest.main()