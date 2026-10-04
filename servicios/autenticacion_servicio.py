"""CREACION DE SERVICIO DE AUTENTICACION"""

from datetime import datetime

from modelos.cliente import Cliente
from modelos.sesion import Sesion

from seguridad.normalizador import capitalizar_titulo
from seguridad.validadores import Validador
from seguridad.contraseñas import GestorContrasenas

from excepciones import (
    AutenticacionError,
    CorreoDuplicadoError,
    ValidacionError,
)


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
        nombre = capitalizar_titulo(nombre)
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

    def iniciar_sesion(self, correo, password, *, ahora=None):
        ahora = ahora or datetime.now()
        cliente = self.__cliente_repo.buscar_por_correo(correo)
        if cliente is None or self.__cliente_repo.esta_bloqueado(correo, ahora):
            raise AutenticacionError("Correo o contraseña incorrectos.")

        valido = GestorContrasenas.verificar(
            password,
            cliente.password_hash
        )
        if not valido:
            self.__cliente_repo.registrar_intento_fallido(correo, ahora)
            raise AutenticacionError("Correo o contraseña incorrectos.")
        if not cliente.password_hash.startswith("$argon2id$"):
            self.__cliente_repo.actualizar_password_hash(
                correo,
                GestorContrasenas.generar_hash(password)
            )
        self.__cliente_repo.reiniciar_intentos_fallidos(correo)
        return Sesion(cliente, ahora=ahora)

    def crear_administrador(self, usuario, password, *, sesion):
        if not isinstance(sesion, Sesion) or sesion.rol != "ADMIN":
            raise AutenticacionError(
                "Se requiere una sesión de administrador."
            )
        if not isinstance(usuario, str) or not usuario.strip():
            raise ValidacionError("El usuario administrador es obligatorio.")
        Validador.validar_contrasena(password)
        usuario = usuario.strip()
        if self.__cliente_repo.buscar_por_correo(usuario):
            raise CorreoDuplicadoError(
                "Ya existe un usuario con ese nombre."
            )
        administrador = Cliente(
            "Administrador",
            "",
            usuario,
            "",
            GestorContrasenas.generar_hash(password),
            "ADMIN"
        )
        self.__cliente_repo.agregar(administrador)

    def cambiar_credenciales_administrador(
        self, sesion, nuevo_usuario, nueva_password
    ):
        if not isinstance(sesion, Sesion) or sesion.rol != "ADMIN":
            raise AutenticacionError(
                "Se requiere una sesión de administrador."
            )
        if not isinstance(nuevo_usuario, str) or not nuevo_usuario.strip():
            raise ValidacionError("El usuario administrador es obligatorio.")
        Validador.validar_contrasena(nueva_password)
        self.__cliente_repo.actualizar_credenciales_administrador(
            sesion.correo,
            nuevo_usuario.strip(),
            GestorContrasenas.generar_hash(nueva_password)
        )

    def recuperar_contrasena(self, correo, rut, nueva_password):
        Validador.validar_correo(correo)
        Validador.validar_rut(rut)
        Validador.validar_contrasena(nueva_password)
        cliente = self.__cliente_repo.buscar_por_correo(correo)
        if cliente is None:
            raise AutenticacionError(
                "No se encontró una cuenta con esos datos."
            )
        if cliente.rol == "ADMIN":
            raise ValidacionError(
                "Este método de recuperación es solo para clientes."
            )
        if cliente.rut.casefold() != rut.strip().casefold():
            raise AutenticacionError(
                "No se encontró una cuenta con esos datos."
            )
        self.__cliente_repo.actualizar_password_hash(
            correo,
            GestorContrasenas.generar_hash(nueva_password)
        )
