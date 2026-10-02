""" creacion de repositorio (destino_repositorio) para el proyecto ViajesAventura"""

import sqlite3

from excepciones import DestinoDuplicadoError
from modelos.destino import Destino
from repositorios.base_datos import BaseDatos


class DestinoRepositorio:

    def __init__(self, base_datos=None):
        self.__base_datos = base_datos or BaseDatos(":memory:")
        self.__conexion = self.__base_datos.conexion

    def agregar(self, destino):
        try:
            with self.__base_datos.transaccion() as conexion:
                conexion.execute(
                    """
                    INSERT INTO destinos (
                        nombre, zona, descripcion, duracion_dias,
                        costo_base, disponible
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        destino.nombre,
                        destino.zona,
                        destino.descripcion,
                        destino.duracion_dias,
                        int(destino.costo_base),
                        int(destino.disponible)
                    )
                )
        except sqlite3.IntegrityError as error:
            raise DestinoDuplicadoError(
                f"El destino '{destino.nombre}' ya existe."
            ) from error

    def listar(self):
        filas = self.__conexion.execute(
            "SELECT * FROM destinos ORDER BY id"
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def buscar_por_nombre(self, nombre):
        fila = self.__conexion.execute(
            "SELECT * FROM destinos WHERE nombre = ?",
            (nombre,)
        ).fetchone()
        return self.__desde_fila(fila) if fila else None

    def eliminar(self, nombre):
        with self.__base_datos.transaccion() as conexion:
            fila = conexion.execute(
                "SELECT id FROM destinos WHERE nombre = ?",
                (nombre,)
            ).fetchone()
            if fila is None:
                return False
            esta_asociado = conexion.execute(
                "SELECT 1 FROM paquete_destinos WHERE destino_id = ? LIMIT 1",
                (fila["id"],)
            ).fetchone()
            if esta_asociado:
                conexion.execute(
                    "UPDATE destinos SET disponible = 0 WHERE id = ?",
                    (fila["id"],)
                )
                return True
            conexion.execute("DELETE FROM destinos WHERE id = ?", (fila["id"],))
            return True

    def actualizar(self, nombre_actual, destino):
        try:
            with self.__base_datos.transaccion() as conexion:
                cursor = conexion.execute(
                    """
                    UPDATE destinos
                    SET nombre = ?, zona = ?, descripcion = ?,
                        duracion_dias = ?, costo_base = ?
                    WHERE nombre = ?
                    """,
                    (
                        destino.nombre,
                        destino.zona,
                        destino.descripcion,
                        destino.duracion_dias,
                        int(destino.costo_base),
                        nombre_actual
                    )
                )
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as error:
            raise DestinoDuplicadoError(
                f"El destino '{destino.nombre}' ya existe."
            ) from error

    @staticmethod
    def __desde_fila(fila):
        destino = Destino(
            fila["nombre"],
            fila["zona"],
            fila["descripcion"],
            fila["duracion_dias"],
            fila["costo_base"]
        )
        if not fila["disponible"]:
            destino.marcar_no_disponible()
        return destino