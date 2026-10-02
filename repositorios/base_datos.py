"""Conexión y esquema SQLite de ViajesAventura."""

import os
import sqlite3
from pathlib import Path


class BaseDatos:
    def __init__(self, ruta=None):
        if ruta is None:
            ruta = os.environ.get(
                "VIAJES_DB_PATH",
                str(Path(__file__).resolve().parent.parent / "viajes_aventura.db")
            )

        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)

        self.__conexion = sqlite3.connect(ruta)
        self.__conexion.row_factory = sqlite3.Row
        self.__conexion.execute("PRAGMA foreign_keys = ON")
        self.__crear_esquema()

    @property
    def conexion(self):
        return self.__conexion

    def cerrar(self):
        self.__conexion.close()

    def __crear_esquema(self):
        self.__conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS destinos (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                zona TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                duracion_dias INTEGER NOT NULL,
                costo_base REAL NOT NULL,
                disponible INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS paquetes (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                fecha_salida TEXT NOT NULL,
                fecha_regreso TEXT NOT NULL,
                cupo_maximo INTEGER NOT NULL,
                precio_por_persona REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS paquete_destinos (
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id)
                    ON DELETE CASCADE,
                destino_id INTEGER NOT NULL REFERENCES destinos(id)
                    ON DELETE RESTRICT,
                orden INTEGER NOT NULL,
                PRIMARY KEY (paquete_id, destino_id),
                UNIQUE (paquete_id, orden)
            );

            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                rut TEXT NOT NULL COLLATE NOCASE UNIQUE,
                correo TEXT NOT NULL COLLATE NOCASE UNIQUE,
                telefono TEXT NOT NULL,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id)
                    ON DELETE RESTRICT,
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id)
                    ON DELETE RESTRICT,
                cantidad_personas INTEGER NOT NULL,
                fecha_emision TEXT NOT NULL,
                total REAL NOT NULL
            );
            """
        )
        self.__conexion.commit()