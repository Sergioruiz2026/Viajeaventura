"""Esquema y transacciones SQLite de la aplicación."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from seguridad.montos import redondear_clp
from seguridad.seguridad import encrypt_data


class BaseDatos:
    def __init__(self, ruta=None):
        usar_ruta_predeterminada = ruta is None and not os.environ.get(
            "VIAJES_DB_PATH"
        )
        if ruta is None:
            ruta = os.environ.get(
                "VIAJES_DB_PATH",
                str(Path(__file__).resolve().parent.parent / "app.db")
            )

        ruta = str(ruta)
        ruta_preexistente = ruta != ":memory:" and Path(ruta).exists()
        base_anterior = Path(__file__).resolve().parent.parent / "viajes_aventura.db"
        migrar_desde = (
            base_anterior
            if usar_ruta_predeterminada
            and not ruta_preexistente
            and base_anterior.exists()
            else None
        )
        if ruta != ":memory:":
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)

        self.__conexion = sqlite3.connect(ruta, timeout=5)
        self.__conexion.row_factory = sqlite3.Row
        self.__conexion.execute("PRAGMA foreign_keys = ON")
        self.__conexion.execute("PRAGMA busy_timeout = 5000")
        try:
            self.__crear_esquema()
            self.__migrar_schema()
            if migrar_desde is not None:
                self.migrar_desde(migrar_desde)
        except BaseException:
            self.__conexion.close()
            if migrar_desde is not None and not ruta_preexistente:
                Path(ruta).unlink(missing_ok=True)
            raise

    @property
    def conexion(self):
        return self.__conexion

    @contextmanager
    def transaccion(self):
        if self.__conexion.in_transaction:
            raise RuntimeError("No se admiten transacciones anidadas.")
        self.__conexion.execute("BEGIN IMMEDIATE")
        try:
            yield self.__conexion
            self.__validar_destinos_paquetes()
            self.__conexion.commit()
        except BaseException:
            self.__conexion.rollback()
            raise

    def cerrar(self):
        self.__conexion.close()

    def __validar_destinos_paquetes(self):
        paquete_invalido = self.__conexion.execute(
            """
            SELECT p.id
            FROM paquetes AS p
            LEFT JOIN paquete_destinos AS pd ON pd.paquete_id = p.id
            GROUP BY p.id
            HAVING COUNT(pd.destino_id) < 2 OR COUNT(pd.destino_id) > 5
            LIMIT 1
            """
        ).fetchone()
        if paquete_invalido is not None:
            raise sqlite3.IntegrityError(
                "Cada paquete debe tener entre 2 y 5 destinos."
            )

    def migrar_desde(self, ruta):
        """Importa los datos de la base anterior sin modificar su archivo."""
        anterior = sqlite3.connect(ruta)
        anterior.row_factory = sqlite3.Row
        try:
            tablas = {
                fila["name"] for fila in anterior.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "clientes" not in tablas:
                return

            with self.transaccion() as conexion:
                for fila in anterior.execute("SELECT * FROM destinos"):
                    conexion.execute(
                        """
                        INSERT INTO destinos (
                            id, nombre, zona, descripcion, duracion_dias,
                            costo_base, disponible
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            fila["id"], fila["nombre"], fila["zona"],
                            fila["descripcion"], fila["duracion_dias"],
                            int(redondear_clp(fila["costo_base"])),
                            fila["disponible"]
                        )
                    )

                for fila in anterior.execute("SELECT * FROM clientes"):
                    rut = fila["rut"]
                    telefono = fila["telefono"]
                    conexion.execute(
                        """
                        INSERT INTO usuarios (
                            id, nombre, rut, correo, telefono, password_hash
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            fila["id"], fila["nombre"],
                            rut if rut.startswith("gAAAAA") else encrypt_data(rut),
                            fila["correo"],
                            telefono if telefono.startswith("gAAAAA")
                            else encrypt_data(telefono),
                            fila["password_hash"]
                        )
                    )

                if "paquetes" in tablas:
                    for fila in anterior.execute("SELECT * FROM paquetes"):
                        conexion.execute(
                            """
                            INSERT INTO paquetes (
                                id, nombre, fecha_salida, fecha_regreso,
                                cupo_maximo, precio_publicado
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                fila["id"], fila["nombre"],
                                fila["fecha_salida"], fila["fecha_regreso"],
                                fila["cupo_maximo"],
                                int(redondear_clp(fila["precio_por_persona"]))
                            )
                        )

                if "paquete_destinos" in tablas:
                    conexion.executemany(
                        """
                        INSERT INTO paquete_destinos (
                            paquete_id, destino_id, orden
                        ) VALUES (?, ?, ?)
                        """,
                        [tuple(fila) for fila in anterior.execute(
                            "SELECT paquete_id, destino_id, orden "
                            "FROM paquete_destinos"
                        )]
                    )

                if "reservas" in tablas:
                    conexion.executemany(
                        """
                        INSERT INTO reservas (
                            id, usuario_id, paquete_id, cantidad_personas,
                            fecha_emision, total
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                fila["id"], fila["cliente_id"],
                                fila["paquete_id"], fila["cantidad_personas"],
                                fila["fecha_emision"],
                                int(redondear_clp(fila["total"]))
                            )
                            for fila in anterior.execute("SELECT * FROM reservas")
                        ]
                    )
        finally:
            anterior.close()

    def __migrar_schema(self):
        """Migraciones incrementales de schema (seguras de ejecutar en cada arranque)."""
        # 1. Agregar salida_id a reservas si aun no existe
        tiene_col = self.__conexion.execute(
            "SELECT COUNT(*) FROM pragma_table_info('reservas') WHERE name='salida_id'"
        ).fetchone()[0]
        if not tiene_col:
            self.__conexion.execute(
                "ALTER TABLE reservas ADD COLUMN salida_id INTEGER"
            )
            self.__conexion.commit()

        # 2. Crear salida inicial para cada paquete que aun no tenga ninguna
        paquetes_sin_salida = self.__conexion.execute(
            """SELECT id, fecha_salida, fecha_regreso, cupo_maximo
               FROM paquetes
               WHERE id NOT IN (SELECT paquete_id FROM paquete_salidas)"""
        ).fetchall()
        for p in paquetes_sin_salida:
            with self.transaccion() as con:
                con.execute(
                    """INSERT INTO paquete_salidas
                       (paquete_id, fecha_salida, fecha_regreso, cupo_maximo)
                       VALUES (?, ?, ?, ?)""",
                    (p["id"], p["fecha_salida"], p["fecha_regreso"], p["cupo_maximo"])
                )

        # 3. Vincular reservas existentes (sin salida_id) a la primera salida de su paquete
        with self.transaccion() as con:
            con.execute(
                """UPDATE reservas
                   SET salida_id = (
                       SELECT ps.id FROM paquete_salidas ps
                       WHERE ps.paquete_id = reservas.paquete_id
                       ORDER BY ps.id LIMIT 1
                   )
                   WHERE salida_id IS NULL"""
            )

    def __crear_esquema(self):
        # Eliminar triggers obsoletos antes de recrearlos con soporte de salidas
        self.__conexion.executescript(
            """
            DROP TRIGGER IF EXISTS reserva_unica_activa_insert;
            DROP TRIGGER IF EXISTS reserva_unica_activa_update;
            DROP TRIGGER IF EXISTS reserva_cupo_insert;
            DROP TRIGGER IF EXISTS reserva_cupo_update;
            """
        )
        self.__conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS destinos (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                zona TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                duracion_dias INTEGER NOT NULL CHECK (duracion_dias > 0),
                costo_base INTEGER NOT NULL CHECK (costo_base > 0),
                disponible INTEGER NOT NULL DEFAULT 1
                    CHECK (disponible IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS paquetes (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                fecha_salida TEXT NOT NULL,
                fecha_regreso TEXT NOT NULL CHECK (
                    julianday(fecha_regreso) IS NOT NULL
                    AND julianday(fecha_salida) IS NOT NULL
                    AND julianday(fecha_regreso) > julianday(fecha_salida)
                ),
                cupo_maximo INTEGER NOT NULL CHECK (cupo_maximo > 0),
                margen_operacion REAL NOT NULL DEFAULT 0.20
                    CHECK (margen_operacion >= 0),
                precio_publicado INTEGER NOT NULL CHECK (precio_publicado >= 0),
                publicado INTEGER NOT NULL DEFAULT 1 CHECK (publicado IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS paquete_destinos (
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id)
                    ON DELETE CASCADE,
                destino_id INTEGER NOT NULL REFERENCES destinos(id)
                    ON DELETE RESTRICT,
                orden INTEGER NOT NULL CHECK (orden >= 0),
                PRIMARY KEY (paquete_id, destino_id),
                UNIQUE (paquete_id, orden)
            );

            CREATE TRIGGER IF NOT EXISTS paquete_destinos_max_insert
            BEFORE INSERT ON paquete_destinos
            WHEN (SELECT COUNT(*) FROM paquete_destinos
                  WHERE paquete_id = NEW.paquete_id) >= 5
            BEGIN
                SELECT RAISE(ABORT, 'Un paquete no puede superar 5 destinos.');
            END;

            CREATE TRIGGER IF NOT EXISTS paquete_destinos_min_delete
            BEFORE DELETE ON paquete_destinos
            WHEN EXISTS (SELECT 1 FROM paquetes WHERE id = OLD.paquete_id)
              AND (SELECT COUNT(*) FROM paquete_destinos
                   WHERE paquete_id = OLD.paquete_id) <= 2
            BEGIN
                SELECT RAISE(ABORT, 'Un paquete debe conservar al menos 2 destinos.');
            END;

            CREATE TABLE IF NOT EXISTS paquete_salidas (
                id INTEGER PRIMARY KEY,
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id)
                    ON DELETE CASCADE,
                fecha_salida TEXT NOT NULL,
                fecha_regreso TEXT NOT NULL CHECK (
                    julianday(fecha_regreso) > julianday(fecha_salida)
                ),
                cupo_maximo INTEGER NOT NULL CHECK (cupo_maximo > 0)
            );

            CREATE INDEX IF NOT EXISTS salidas_paquete
                ON paquete_salidas(paquete_id, fecha_salida);

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                rut TEXT NOT NULL,
                correo TEXT NOT NULL COLLATE NOCASE UNIQUE,
                telefono TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'CLIENTE'
                    CHECK (rol IN ('ADMIN', 'CLIENTE')),
                intentos_fallidos INTEGER NOT NULL DEFAULT 0
                    CHECK (intentos_fallidos >= 0),
                bloqueado_hasta TEXT
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id)
                    ON DELETE RESTRICT,
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id)
                    ON DELETE RESTRICT,
                cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas >= 1),
                fecha_emision TEXT NOT NULL,
                total INTEGER NOT NULL CHECK (total >= 0),
                estado TEXT NOT NULL DEFAULT 'ACTIVA'
                    CHECK (estado IN ('ACTIVA', 'CANCELADA'))
            );

                CREATE INDEX IF NOT EXISTS reservas_cliente_paquete_estado
                    ON reservas(usuario_id, paquete_id, estado);

                CREATE INDEX IF NOT EXISTS reservas_salida_estado
                    ON reservas(salida_id, estado);

                -- Unicidad por SALIDA (nueva ruta con salida_id)
                CREATE TRIGGER IF NOT EXISTS reserva_unica_salida_insert
                BEFORE INSERT ON reservas
                WHEN NEW.estado = 'ACTIVA' AND NEW.salida_id IS NOT NULL
                 AND EXISTS (
                     SELECT 1 FROM reservas
                     WHERE usuario_id = NEW.usuario_id
                       AND salida_id = NEW.salida_id
                       AND estado = 'ACTIVA'
                 )
                BEGIN
                    SELECT RAISE(ABORT,
                        'Ya existe una reserva activa para este cliente y salida.');
                END;

                -- Unicidad por PAQUETE (ruta legada sin salida_id)
                CREATE TRIGGER IF NOT EXISTS reserva_unica_paquete_insert
                BEFORE INSERT ON reservas
                WHEN NEW.estado = 'ACTIVA' AND NEW.salida_id IS NULL
                 AND EXISTS (
                     SELECT 1 FROM reservas
                     WHERE usuario_id = NEW.usuario_id
                       AND paquete_id = NEW.paquete_id
                       AND estado = 'ACTIVA'
                 )
                BEGIN
                    SELECT RAISE(ABORT,
                        'Ya existe una reserva activa para este cliente y paquete.');
                END;

            -- Cupo por SALIDA
            CREATE TRIGGER IF NOT EXISTS reserva_cupo_salida_insert
            BEFORE INSERT ON reservas
            WHEN NEW.estado = 'ACTIVA' AND NEW.salida_id IS NOT NULL
             AND COALESCE((
                 SELECT SUM(cantidad_personas) FROM reservas
                 WHERE salida_id = NEW.salida_id AND estado = 'ACTIVA'
             ), 0) + NEW.cantidad_personas > (
                 SELECT cupo_maximo FROM paquete_salidas WHERE id = NEW.salida_id
             )
            BEGIN
                SELECT RAISE(ABORT, 'Cupo maximo de la salida excedido.');
            END;

            -- Cupo por PAQUETE (legado)
            CREATE TRIGGER IF NOT EXISTS reserva_cupo_paquete_insert
            BEFORE INSERT ON reservas
            WHEN NEW.estado = 'ACTIVA' AND NEW.salida_id IS NULL
             AND COALESCE((
                 SELECT SUM(cantidad_personas) FROM reservas
                 WHERE paquete_id = NEW.paquete_id AND estado = 'ACTIVA'
             ), 0) + NEW.cantidad_personas > (
                 SELECT cupo_maximo FROM paquetes WHERE id = NEW.paquete_id
             )
            BEGIN
                SELECT RAISE(ABORT, 'Cupo maximo del paquete excedido.');
            END;

            CREATE INDEX IF NOT EXISTS reservas_paquete_estado
                ON reservas(paquete_id, estado);
            """
        )
        self.__conexion.commit()