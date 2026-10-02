"""cracion de la clase reserva repositorio"""

from datetime import datetime

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

    def agregar(self, reserva):
        cliente = self.__conexion.execute(
            "SELECT id FROM clientes WHERE correo = ?",
            (reserva.cliente.correo,)
        ).fetchone()
        paquete = self.__conexion.execute(
            "SELECT id FROM paquetes WHERE nombre = ?",
            (reserva.paquete.nombre,)
        ).fetchone()
        if cliente is None or paquete is None:
            raise ValueError(
                "El cliente y el paquete deben existir en SQLite."
            )
        with self.__conexion:
            self.__conexion.execute(
                """
                INSERT INTO reservas (
                    cliente_id, paquete_id, cantidad_personas,
                    fecha_emision, total
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    cliente["id"],
                    paquete["id"],
                    reserva.cantidad_personas,
                    reserva.fecha_emision.isoformat(),
                    reserva.total
                )
            )

    def listar(self):
        filas = self.__conexion.execute(
            "SELECT * FROM reservas ORDER BY id"
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def reservas_por_cliente(self, correo):
        filas = self.__conexion.execute(
            """
            SELECT r.*
            FROM reservas AS r
            JOIN clientes AS c ON c.id = r.cliente_id
            WHERE c.correo = ?
            ORDER BY r.id
            """,
            (correo,)
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def reservas_por_paquete(self, nombre_paquete):
        filas = self.__conexion.execute(
            """
            SELECT r.*
            FROM reservas AS r
            JOIN paquetes AS p ON p.id = r.paquete_id
            WHERE p.nombre = ?
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
            WHERE p.nombre = ?
            """,
            (nombre_paquete,)
        ).fetchone()
        return fila["ocupados"]

    def __desde_fila(self, fila):
        cliente = self.__conexion.execute(
            "SELECT * FROM clientes WHERE id = ?",
            (fila["cliente_id"],)
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
            fila["total"]
        )