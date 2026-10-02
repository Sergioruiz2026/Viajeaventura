"""cracion de la clase reserva repositorio"""

import sqlite3
from datetime import date, datetime

from excepciones import CupoInsuficienteError, ReservaNoPermitidaError
from modelos.reserva import Reserva
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio

class ReservaRepositorio:

    def __init__(self, base_datos=None):
        self.__base_datos = base_datos or BaseDatos(":memory:")
        self.__conexion = self.__base_datos.conexion
        self.__clientes = ClienteRepositorio(self.__base_datos)
        self.__paquetes = PaqueteRepositorio(self.__base_datos)

    def agregar(self, reserva, paquete_id=None):
        reserva_id = None
        try:
            with self.__base_datos.transaccion() as conexion:
                cliente = conexion.execute(
                    "SELECT id FROM usuarios WHERE correo = ?",
                    (reserva.cliente.correo,)
                ).fetchone()
                if paquete_id is None:
                    paquete = conexion.execute(
                        "SELECT id, cupo_maximo FROM paquetes WHERE nombre = ?",
                        (reserva.paquete.nombre,)
                    ).fetchone()
                else:
                    paquete = conexion.execute(
                        "SELECT id, cupo_maximo FROM paquetes WHERE id = ?",
                        (paquete_id,)
                    ).fetchone()
                if cliente is None or paquete is None:
                    raise ValueError(
                        "El usuario y el paquete deben existir en SQLite."
                    )

                reserva_activa = conexion.execute(
                    """
                    SELECT 1 FROM reservas
                    WHERE usuario_id = ? AND paquete_id = ?
                      AND estado = 'ACTIVA'
                    LIMIT 1
                    """,
                    (cliente["id"], paquete["id"])
                ).fetchone()
                if reserva_activa is not None:
                    raise ReservaNoPermitidaError(
                        "Ya tienes una reserva activa para este paquete."
                    )

                ocupados = conexion.execute(
                    """
                    SELECT COALESCE(SUM(cantidad_personas), 0)
                    FROM reservas WHERE paquete_id = ? AND estado = 'ACTIVA'
                    """,
                    (paquete["id"],)
                ).fetchone()[0]
                disponibles = paquete["cupo_maximo"] - ocupados
                if reserva.cantidad_personas > disponibles:
                    raise CupoInsuficienteError(
                        f"Solo quedan {disponibles} cupos."
                    )
                cursor = conexion.execute(
                    """
                    INSERT INTO reservas (
                        usuario_id, paquete_id, cantidad_personas,
                        fecha_emision, total
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        cliente["id"],
                        paquete["id"],
                        reserva.cantidad_personas,
                        reserva.fecha_emision.isoformat(),
                        int(reserva.total)
                    )
                )
                reserva_id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            detalle = str(error)
            if "Ya existe una reserva activa" in detalle:
                raise ReservaNoPermitidaError(
                    "Ya tienes una reserva activa para este paquete."
                ) from error
            if (
                "reservas.paquete_id" in detalle
                and "reservas.usuario_id" in detalle
            ):
                raise ReservaNoPermitidaError(
                    "Ya tienes una reserva activa para este paquete."
                ) from error
            if "Cupo máximo del paquete excedido" in detalle:
                raise CupoInsuficienteError(
                    "No hay cupos suficientes para esta reserva."
                ) from error
            raise
        fila = self.__conexion.execute(
            "SELECT * FROM reservas WHERE id = ?",
            (reserva_id,)
        ).fetchone()
        return self.__desde_fila(fila)

    def listar(self):
        filas = self.__conexion.execute(
            "SELECT * FROM reservas ORDER BY id"
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def reservas_por_cliente(self, usuario_id):
        filas = self.__conexion.execute(
            """
            SELECT r.*
            FROM reservas AS r
            WHERE r.usuario_id = ?
            ORDER BY r.id
            """,
            (usuario_id,)
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def cancelar(self, reserva_id, usuario_id, fecha_actual=None):
        fecha_actual = fecha_actual or date.today()
        with self.__base_datos.transaccion() as conexion:
            fila = conexion.execute(
                """
                SELECT r.estado, p.fecha_salida
                FROM reservas AS r
                JOIN paquetes AS p ON p.id = r.paquete_id
                WHERE r.id = ? AND r.usuario_id = ?
                """,
                (reserva_id, usuario_id)
            ).fetchone()
            if fila is None:
                raise ReservaNoPermitidaError(
                    "No se encontró una reserva propia."
                )
            if fila["estado"] != "ACTIVA":
                raise ReservaNoPermitidaError(
                    "La reserva no está activa."
                )
            if date.fromisoformat(fila["fecha_salida"]) <= fecha_actual:
                raise ReservaNoPermitidaError(
                    "No se puede cancelar una reserva cuyo paquete ya inició."
                )
            conexion.execute(
                """
                UPDATE reservas SET estado = 'CANCELADA'
                WHERE id = ? AND usuario_id = ? AND estado = 'ACTIVA'
                """,
                (reserva_id, usuario_id)
            )

        fila_actualizada = self.__conexion.execute(
            "SELECT * FROM reservas WHERE id = ?",
            (reserva_id,)
        ).fetchone()
        return self.__desde_fila(fila_actualizada)

    def reservas_por_paquete(self, nombre_paquete):
        filas = self.__conexion.execute(
            """
            SELECT r.*
            FROM reservas AS r
            JOIN paquetes AS p ON p.id = r.paquete_id
            WHERE p.nombre = ? AND r.estado = 'ACTIVA'
            ORDER BY r.id
            """,
            (nombre_paquete,)
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def cupos_ocupados(self, nombre_paquete):
        fila = self.__conexion.execute(
            """
            SELECT COALESCE(SUM(r.cantidad_personas), 0) AS ocupados
            FROM reservas AS r
            JOIN paquetes AS p ON p.id = r.paquete_id
            WHERE p.nombre = ? AND r.estado = 'ACTIVA'
            """,
            (nombre_paquete,)
        ).fetchone()
        return fila["ocupados"]

    def __desde_fila(self, fila):
        cliente = self.__conexion.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (fila["usuario_id"],)
        ).fetchone()
        paquete = self.__conexion.execute(
            "SELECT nombre FROM paquetes WHERE id = ?",
            (fila["paquete_id"],)
        ).fetchone()
        return Reserva(
            self.__clientes.buscar_por_correo(cliente["correo"]),
            self.__paquetes.buscar_por_nombre(paquete["nombre"]),
            fila["cantidad_personas"],
            datetime.fromisoformat(fila["fecha_emision"]),
            fila["total"],
            id_reserva=fila["id"],
            estado=fila["estado"]
        )