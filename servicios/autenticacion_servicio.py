""""CREACION DE SERVICIO DE AUTENTICACION"""

from modelos.cliente import Cliente

from seguridad.validadores import Validador
from seguridad.contraseñas import GestorContrasenas

from excepciones import AutenticacionError, CorreoDuplicadoError


class AutenticacionServicio:

    def __init__(self, cliente_repo):
        self.__cliente_repo = cliente_repo

    def registrar_cliente(
        self,
        nombre,
        rut,
        correo,
        telefono,
        password
    ):
        Validador.validar_nombre(nombre)
        Validador.validar_rut(rut)
        Validador.validar_correo(correo)
        Validador.validar_telefono(telefono)
        Validador.validar_contrasena(password)
        if self.__cliente_repo.buscar_por_correo(correo):
            raise CorreoDuplicadoError(
                "Ya existe un cliente registrado con ese correo."
            )
        password_hash = GestorContrasenas.generar_hash(password)
        cliente = Cliente(
            nombre,
            rut,
            correo,
            telefono,
            password_hash
        )
        self.__cliente_repo.agregar(cliente)
        return cliente

    def iniciar_sesion(self, correo, password):
        cliente = self.__cliente_repo.buscar_por_correo(correo)
        if not cliente:
            raise AutenticacionError("Usuario no encontrado.")

        valido = GestorContrasenas.verificar(
            password,
            cliente.password_hash
        )
        if not valido:
            raise AutenticacionError("Contraseña incorrecta.")
        if not cliente.password_hash.startswith("$argon2id$"):
            self.__cliente_repo.actualizar_password_hash(
                correo,
                GestorContrasenas.generar_hash(password)
            )
        return cliente
