"""" creacion de repositorio (paquete_repositorio) para el proyecto ViajesAventura"""

from excepciones import PaqueteDuplicadoError
import sqlite3
from datetime import date

from excepciones import PaqueteDuplicadoError
from modelos.destino import Destino
from modelos.paquete import Paquete
from repositorios.base_datos import BaseDatos

class PaqueteRepositorio:

    def __init__(self, base_datos=None):
        self.__base_datos = base_datos or BaseDatos(":memory:")
        self.__conexion = self.__base_datos.conexion

    def agregar(self, paquete):
        try:
            with self.__conexion:
                cursor = self.__conexion.execute(
                    """
                    INSERT INTO paquetes (
                        nombre, fecha_salida, fecha_regreso,
                        cupo_maximo, precio_por_persona
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        paquete.nombre,
                        paquete.fecha_salida.isoformat(),
                        paquete.fecha_regreso.isoformat(),
                        paquete.cupo_maximo,
                        paquete.precio_por_persona
                    )
                )
                for orden, destino in enumerate(paquete.destinos):
                    fila = self.__conexion.execute(
                        "SELECT id FROM destinos WHERE nombre = ?",
                        (destino.nombre,)
                    ).fetchone()
                    if fila is None:
                        raise ValueError(
                            f"El destino '{destino.nombre}' no está guardado."
                        )
                    self.__conexion.execute(
                        """
                        INSERT INTO paquete_destinos (
                            paquete_id, destino_id, orden
                        ) VALUES (?, ?, ?)
                        """,
                        (cursor.lastrowid, fila["id"], orden)
                    )
        except sqlite3.IntegrityError as error:
            raise PaqueteDuplicadoError(
                f"El paquete '{paquete.nombre}' ya existe."
            ) from error

    def listar(self):
        filas = self.__conexion.execute(
            "SELECT * FROM paquetes ORDER BY id"
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def buscar_por_nombre(self, nombre):
        fila = self.__conexion.execute(
            "SELECT * FROM paquetes WHERE nombre = ?",
            (nombre,)
        ).fetchone()
        return self.__desde_fila(fila) if fila else None

    def eliminar(self, nombre):
        try:
            with self.__conexion:
                cursor = self.__conexion.execute(
                    "DELETE FROM paquetes WHERE nombre = ?",
                    (nombre,)
                )
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    def paquetes_vigentes(self):
        return [paquete for paquete in self.listar() if not paquete.esta_vencido()]

    def __desde_fila(self, fila):
        filas_destinos = self.__conexion.execute(
            """
            SELECT d.*
            FROM destinos AS d
            JOIN paquete_destinos AS pd ON pd.destino_id = d.id
            WHERE pd.paquete_id = ?
            ORDER BY pd.orden
            """,
            (fila["id"],)
        ).fetchall()
        destinos = [
            Destino(
                destino["nombre"],
                destino["zona"],
                destino["descripcion"],
                destino["duracion_dias"],
                destino["costo_base"]
            )
            for destino in filas_destinos
        ]
        for destino, fila_destino in zip(destinos, filas_destinos):
            if not fila_destino["disponible"]:
                destino.marcar_no_disponible()

        return Paquete(
            fila["nombre"],
            destinos,
            date.fromisoformat(fila["fecha_salida"]),
            date.fromisoformat(fila["fecha_regreso"]),
            fila["cupo_maximo"],
            precio_por_persona=fila["precio_por_persona"]
        )