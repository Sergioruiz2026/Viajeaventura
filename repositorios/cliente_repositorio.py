""" creacion de la clase ClienteRepositorio para manejar la lista de clientes """

import sqlite3
from datetime import datetime, timedelta

from excepciones import CorreoDuplicadoError, ValidacionError
from modelos.cliente import Cliente
from modelos.administrador import Administrador
from repositorios.base_datos import BaseDatos
from seguridad.seguridad import decrypt_data, encrypt_data


class ClienteRepositorio:

    def __init__(self, base_datos=None):
        self.__base_datos = base_datos or BaseDatos(":memory:")
        self.__conexion = self.__base_datos.conexion
        self.__migrar_datos_sensibles()

    def __migrar_datos_sensibles(self):
        filas = self.__conexion.execute(
            "SELECT id, rut, telefono FROM usuarios"
        ).fetchall()
        for fila in filas:
            rut = fila["rut"]
            telefono = fila["telefono"]
            if not rut.startswith("gAAAAA") or not telefono.startswith("gAAAAA"):
                with self.__base_datos.transaccion() as conexion:
                    conexion.execute(
                        "UPDATE usuarios SET rut = ?, telefono = ? WHERE id = ?",
                        (
                            rut if rut.startswith("gAAAAA") else encrypt_data(rut),
                            telefono if telefono.startswith("gAAAAA") else encrypt_data(telefono),
                            fila["id"]
                        )
                    )

    def agregar(self, cliente):
        if self.buscar_por_correo(cliente.correo):
            raise CorreoDuplicadoError(
                "Ya existe un cliente registrado con ese correo."
            )
        if cliente.rut and self.buscar_por_rut(cliente.rut):
            raise ValidacionError("Ya existe un cliente con ese RUT.")
        try:
            with self.__base_datos.transaccion() as conexion:
                conexion.execute(
                    """
                    INSERT INTO usuarios (
                        nombre, rut, correo, telefono, password_hash, rol
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cliente.nombre,
                        encrypt_data(cliente.rut),
                        cliente.correo,
                        encrypt_data(cliente.telefono),
                        cliente.password_hash,
                        cliente.rol
                    )
                )
        except sqlite3.IntegrityError as error:
            if "usuarios.correo" in str(error):
                raise CorreoDuplicadoError(
                    "Ya existe un cliente registrado con ese correo."
                ) from error
            raise

    def listar(self):
        filas = self.__conexion.execute(
            "SELECT * FROM usuarios ORDER BY id"
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def buscar_por_correo(self, correo):
        fila = self.__conexion.execute(
            "SELECT * FROM usuarios WHERE correo = ?",
            (correo,)
        ).fetchone()
        return self.__desde_fila(fila) if fila else None

    def esta_bloqueado(self, correo, ahora):
        with self.__base_datos.transaccion() as conexion:
            fila = conexion.execute(
                """
                SELECT intentos_fallidos, bloqueado_hasta
                FROM usuarios WHERE correo = ?
                """,
                (correo,)
            ).fetchone()
            if fila is None or fila["bloqueado_hasta"] is None:
                return False
            bloqueado_hasta = datetime.fromisoformat(fila["bloqueado_hasta"])
            if bloqueado_hasta > ahora:
                return True
            conexion.execute(
                """
                UPDATE usuarios
                SET intentos_fallidos = 0, bloqueado_hasta = NULL
                WHERE correo = ?
                """,
                (correo,)
            )
            return False

    def registrar_intento_fallido(self, correo, ahora):
        with self.__base_datos.transaccion() as conexion:
            fila = conexion.execute(
                """
                SELECT intentos_fallidos, bloqueado_hasta
                FROM usuarios WHERE correo = ?
                """,
                (correo,)
            ).fetchone()
            if fila is None:
                return 0

            bloqueado_hasta = (
                datetime.fromisoformat(fila["bloqueado_hasta"])
                if fila["bloqueado_hasta"] is not None
                else None
            )
            if bloqueado_hasta is not None and bloqueado_hasta > ahora:
                return fila["intentos_fallidos"]

            intentos = (
                0 if bloqueado_hasta is not None else fila["intentos_fallidos"]
            ) + 1
            nuevo_bloqueo = (
                (ahora + timedelta(minutes=15)).isoformat()
                if intentos >= 5
                else None
            )
            conexion.execute(
                """
                UPDATE usuarios
                SET intentos_fallidos = ?, bloqueado_hasta = ?
                WHERE correo = ?
                """,
                (intentos, nuevo_bloqueo, correo)
            )
            return intentos

    def reiniciar_intentos_fallidos(self, correo):
        with self.__base_datos.transaccion() as conexion:
            conexion.execute(
                """
                UPDATE usuarios
                SET intentos_fallidos = 0, bloqueado_hasta = NULL
                WHERE correo = ?
                """,
                (correo,)
            )

    def buscar_por_rut(self, rut):
        filas = self.__conexion.execute(
            "SELECT * FROM usuarios ORDER BY id"
        ).fetchall()
        for fila in filas:
            cliente = self.__desde_fila(fila)
            if cliente.rut.casefold() == rut.casefold():
                return cliente
        return None

    def actualizar_password_hash(self, correo, password_hash):
        with self.__base_datos.transaccion() as conexion:
            conexion.execute(
                "UPDATE usuarios SET password_hash = ? WHERE correo = ?",
                (password_hash, correo)
            )

    def contar_administradores(self):
        fila = self.__conexion.execute(
            "SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'ADMIN'"
        ).fetchone()
        return fila["total"]

    def actualizar_credenciales_administrador(
        self, usuario_actual, nuevo_usuario, password_hash
    ):
        try:
            with self.__base_datos.transaccion() as conexion:
                cursor = conexion.execute(
                    """
                    UPDATE usuarios
                    SET correo = ?, password_hash = ?,
                        intentos_fallidos = 0, bloqueado_hasta = NULL
                    WHERE correo = ? AND rol = 'ADMIN'
                    """,
                    (nuevo_usuario, password_hash, usuario_actual)
                )
                if cursor.rowcount == 0:
                    raise ValidacionError(
                        "No se encontró el administrador actual."
                    )
        except sqlite3.IntegrityError as error:
            raise CorreoDuplicadoError(
                "Ya existe un administrador con ese usuario."
            ) from error

    @staticmethod
    def __desde_fila(fila):
        if fila["rol"] == "ADMIN":
            return Administrador(
                fila["correo"], fila["password_hash"], fila["id"],
                nombre=fila["nombre"],
            )
        return Cliente(
            fila["nombre"],
            decrypt_data(fila["rut"]),
            fila["correo"],
            decrypt_data(fila["telefono"]),
            fila["password_hash"],
            fila["rol"],
            usuario_id=fila["id"]
        )