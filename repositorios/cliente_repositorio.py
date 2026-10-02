""" creacion de la clase ClienteRepositorio para manejar la lista de clientes """

from excepciones import CorreoDuplicadoError, ValidacionError
from modelos.cliente import Cliente
from repositorios.base_datos import BaseDatos


class ClienteRepositorio:

    def __init__(self, base_datos=None):
        self.__base_datos = base_datos or BaseDatos(":memory:")
        self.__conexion = self.__base_datos.conexion

    def agregar(self, cliente):
        if self.buscar_por_correo(cliente.correo):
            raise CorreoDuplicadoError(
                "Ya existe un cliente registrado con ese correo."
            )
        if self.buscar_por_rut(cliente.rut):
            raise ValidacionError("Ya existe un cliente con ese RUT.")
        with self.__conexion:
            self.__conexion.execute(
                """
                INSERT INTO clientes (
                    nombre, rut, correo, telefono, password_hash
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    cliente.nombre,
                    cliente.rut,
                    cliente.correo,
                    cliente.telefono,
                    cliente.password_hash
                )
            )

    def listar(self):
        filas = self.__conexion.execute(
            "SELECT * FROM clientes ORDER BY id"
        ).fetchall()
        return [self.__desde_fila(fila) for fila in filas]

    def buscar_por_correo(self, correo):
        fila = self.__conexion.execute(
            "SELECT * FROM clientes WHERE correo = ?",
            (correo,)
        ).fetchone()
        return self.__desde_fila(fila) if fila else None

    def buscar_por_rut(self, rut):
        fila = self.__conexion.execute(
            "SELECT * FROM clientes WHERE rut = ?",
            (rut,)
        ).fetchone()
        return self.__desde_fila(fila) if fila else None

    @staticmethod
    def __desde_fila(fila):
        return Cliente(
            fila["nombre"],
            fila["rut"],
            fila["correo"],
            fila["telefono"],
            fila["password_hash"]
        )