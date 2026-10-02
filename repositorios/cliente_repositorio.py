""" creacion de la clase ClienteRepositorio para manejar la lista de clientes """

from excepciones import CorreoDuplicadoError, ValidacionError
from modelos.cliente import Cliente
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
        if self.buscar_por_rut(cliente.rut):
            raise ValidacionError("Ya existe un cliente con ese RUT.")
        with self.__base_datos.transaccion() as conexion:
            conexion.execute(
                """
                INSERT INTO usuarios (
                    nombre, rut, correo, telefono, password_hash
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    cliente.nombre,
                    encrypt_data(cliente.rut),
                    cliente.correo,
                    encrypt_data(cliente.telefono),
                    cliente.password_hash
                )
            )

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

    @staticmethod
    def __desde_fila(fila):
        return Cliente(
            fila["nombre"],
            decrypt_data(fila["rut"]),
            fila["correo"],
            decrypt_data(fila["telefono"]),
            fila["password_hash"]
        )