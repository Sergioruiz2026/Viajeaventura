"""Persistencia de sesiones autenticadas en la base de datos compartida."""

from datetime import datetime

from repositorios.base_datos import BaseDatos


class SesionRepositorio:
    def __init__(self, base_datos: BaseDatos):
        self.__base_datos = base_datos
        self.__conexion = base_datos.conexion

    def crear(self, token_hash: str, usuario_id: int, ahora: datetime) -> None:
        with self.__base_datos.transaccion() as conexion:
            conexion.execute(
                """
                INSERT INTO sesiones (token_hash, usuario_id, ultima_actividad)
                VALUES (?, ?, ?)
                """,
                (token_hash, usuario_id, ahora.isoformat()),
            )

    def buscar(self, token_hash: str):
        fila = self.__conexion.execute(
            """
            SELECT usuario_id, ultima_actividad
            FROM sesiones
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if fila is None:
            return None
        return fila["usuario_id"], datetime.fromisoformat(
            fila["ultima_actividad"]
        )

    def actualizar_actividad(
        self, token_hash: str, ahora: datetime
    ) -> None:
        with self.__base_datos.transaccion() as conexion:
            conexion.execute(
                "UPDATE sesiones SET ultima_actividad = ? WHERE token_hash = ?",
                (ahora.isoformat(), token_hash),
            )

    def eliminar(self, token_hash: str) -> None:
        with self.__base_datos.transaccion() as conexion:
            conexion.execute(
                "DELETE FROM sesiones WHERE token_hash = ?",
                (token_hash,),
            )
