"""Repositorio de salidas (fechas de partida) de paquetes."""

from datetime import date

from modelos.salida import Salida
from repositorios.base_datos import BaseDatos


class SalidaRepositorio:

    def __init__(self, base_datos=None):
        self.__base_datos = base_datos or BaseDatos(":memory:")
        self.__conexion = self.__base_datos.conexion

    def agregar(self, paquete_id, fecha_salida, fecha_regreso, cupo_maximo):
        with self.__base_datos.transaccion() as con:
            cursor = con.execute(
                """INSERT INTO paquete_salidas
                   (paquete_id, fecha_salida, fecha_regreso, cupo_maximo)
                   VALUES (?, ?, ?, ?)""",
                (paquete_id, fecha_salida.isoformat(),
                 fecha_regreso.isoformat(), cupo_maximo)
            )
        return cursor.lastrowid

    def listar_por_paquete(self, paquete_id):
        filas = self.__conexion.execute(
            """SELECT ps.*, p.nombre AS paq_nombre, p.precio_publicado AS precio
               FROM paquete_salidas ps
               JOIN paquetes p ON p.id = ps.paquete_id
               WHERE ps.paquete_id = ?
               ORDER BY ps.fecha_salida""",
            (paquete_id,)
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def salidas_vigentes(self, hoy=None):
        fecha = (hoy or date.today()).isoformat()
        filas = self.__conexion.execute(
            """SELECT ps.*, p.nombre AS paq_nombre, p.precio_publicado AS precio
               FROM paquete_salidas ps
               JOIN paquetes p ON p.id = ps.paquete_id
               WHERE date(ps.fecha_salida) > ? AND p.publicado = 1
               ORDER BY ps.fecha_salida""",
            (fecha,)
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def buscar_por_id(self, salida_id):
        fila = self.__conexion.execute(
            """SELECT ps.*, p.nombre AS paq_nombre, p.precio_publicado AS precio
               FROM paquete_salidas ps
               JOIN paquetes p ON p.id = ps.paquete_id
               WHERE ps.id = ?""",
            (salida_id,)
        ).fetchone()
        return self.__desde_fila(fila) if fila else None

    def buscar_fecha_salida_por_id(self, salida_id):
        """Retorna solo la fecha_salida para validaciones rápidas."""
        fila = self.__conexion.execute(
            "SELECT fecha_salida FROM paquete_salidas WHERE id = ?",
            (salida_id,)
        ).fetchone()
        return date.fromisoformat(fila["fecha_salida"]) if fila else None

    def actualizar(self, salida_id, fecha_salida, fecha_regreso, cupo_maximo):
        ocupados = self.__cupos_ocupados(salida_id)
        if cupo_maximo < ocupados:
            return False
        with self.__base_datos.transaccion() as con:
            cursor = con.execute(
                """UPDATE paquete_salidas
                   SET fecha_salida = ?, fecha_regreso = ?, cupo_maximo = ?
                   WHERE id = ?""",
                (
                    fecha_salida.isoformat(),
                    fecha_regreso.isoformat(),
                    cupo_maximo,
                    salida_id,
                ),
            )
        return cursor.rowcount > 0

    def __cupos_ocupados(self, salida_id):
        return self.__conexion.execute(
            """SELECT COALESCE(SUM(cantidad_personas), 0)
               FROM reservas WHERE salida_id = ? AND estado = 'ACTIVA'""",
            (salida_id,)
        ).fetchone()[0]

    def __desde_fila(self, fila):
        ocupados = self.__cupos_ocupados(fila["id"])
        return Salida(
            id=fila["id"],
            paquete_id=fila["paquete_id"],
            paquete_nombre=fila["paq_nombre"],
            precio_por_persona=fila["precio"],
            fecha_salida=date.fromisoformat(fila["fecha_salida"]),
            fecha_regreso=date.fromisoformat(fila["fecha_regreso"]),
            cupo_maximo=fila["cupo_maximo"],
            cupo_disponible=fila["cupo_maximo"] - ocupados,
        )
