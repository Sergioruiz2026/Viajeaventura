from datetime import date
from decimal import Decimal, InvalidOperation
import getpass
import os

from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio

from servicios.catalogo_servicio import CatalogoServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.reserva_servicio import ReservaServicio
from modelos.cliente import Cliente
from seguridad.contraseñas import GestorContrasenas

from excepciones import (
    AutenticacionError,
    SesionExpiradaError,
    ValidacionError,
    ViajesAventuraError
)
from seguridad.validadores import Validador
from seguridad.logging_config import configurar_logging, enmascarar_texto
from repositorios.base_datos import BaseDatos


# ==========================
# INICIALIZACIÓN
# ==========================

destino_repo = DestinoRepositorio()
base_datos = BaseDatos()
destino_repo = DestinoRepositorio(base_datos)
paquete_repo = PaqueteRepositorio(base_datos)
cliente_repo = ClienteRepositorio(base_datos)
reserva_repo = ReservaRepositorio(base_datos)

catalogo = CatalogoServicio(destino_repo)
paquetes = PaqueteServicio(
    paquete_repo,
    destino_repo
)
auth = AutenticacionServicio(cliente_repo)
reservas = ReservaServicio(
    reserva_repo,
    paquete_repo
)

ADMIN_USUARIO = os.environ.get("VIAJES_ADMIN_USUARIO", "admin")
ADMIN_PASSWORD = os.environ.get("VIAJES_ADMIN_PASSWORD")


# ==========================
# MENÚ ADMINISTRADOR
# ==========================

def menu_admin(sesion):
    while True:
        print("\n===== ADMINISTRADOR =====")
        print("1. Registrar destino")
        print("2. Listar destinos")
        print("3. Crear paquete")
        print("4. Listar paquetes")
        print("5. Ver reservas")
        print("0. Cerrar sesión")

        opcion = input("Seleccione: ")
        try:
            if opcion == "1":
                nombre = input("Nombre: ")
                zona = input("Zona: ")
                descripcion = input("Descripción: ")
                duracion = int(input("Duración días: "))
                costo = Decimal(input("Costo base: "))
                catalogo.registrar_destino(
                    nombre,
                    zona,
                    descripcion,
                    duracion,
                    costo,
                    sesion=sesion
                )
                print("Destino registrado.")

            elif opcion == "2":
                for destino in catalogo.listar_destinos(sesion=sesion):
                    print(destino)

            elif opcion == "3":
                nombre = input("Nombre paquete: ")
                destinos = [
                    destino.strip()
                    for destino in input(
                        "Destinos separados por coma: "
                    ).split(",")
                ]
                anio_salida = int(input("Año salida: "))
                mes_salida = int(input("Mes salida: "))
                dia_salida = int(input("Día salida: "))
                anio_retorno = int(input("Año regreso: "))
                mes_retorno = int(input("Mes regreso: "))
                dia_retorno = int(input("Día regreso: "))
                cupo = int(input("Cupo máximo: "))

                paquetes.crear_paquete(
                    nombre,
                    destinos,
                    date(anio_salida, mes_salida, dia_salida),
                    date(anio_retorno, mes_retorno, dia_retorno),
                    cupo,
                    sesion=sesion
                )
                print("Paquete creado.")

            elif opcion == "4":
                for paquete in paquetes.listar_paquetes(sesion=sesion):
                    print(paquete)

            elif opcion == "5":
                todas = reservas.listar_reservas(sesion=sesion)
                if not todas:
                    print("No existen reservas.")
                for reserva in todas:
                    print(reserva)

            elif opcion == "0":
                break

            else:
                print("Opción inválida.")

        except SesionExpiradaError as error:
            print(f"Error: {enmascarar_texto(str(error))}")
            break
        except ViajesAventuraError as error:
            print(f"Error: {enmascarar_texto(str(error))}")
        except (ValueError, InvalidOperation) as error:
            print(f"Dato inválido: {enmascarar_texto(str(error))}")


# ==========================
# MENÚ CLIENTE
# ==========================

def menu_cliente(sesion):
    while True:
        print(f"\n===== BIENVENIDO {sesion.nombre} =====")
        print("1. Ver paquetes")
        print("2. Reservar paquete")
        print("3. Mis reservas")
        print("0. Cerrar sesión")

        opcion = input("Seleccione: ")
        try:
            if opcion == "1":
                lista = paquetes.listar_vigentes(sesion=sesion)
                if not lista:
                    print("No existen paquetes.")
                for paquete in lista:
                    print(paquete)

            elif opcion == "2":
                nombre_paquete = input("Nombre paquete: ")
                personas = int(input("Cantidad personas: "))
                reserva = reservas.crear_reserva(
                    sesion,
                    nombre_paquete,
                    personas
                )
                print("Reserva realizada.")
                print(f"Total: ${reserva.total:,.0f}")

            elif opcion == "3":
                mis_reservas = reservas.reservas_cliente(sesion)
                if not mis_reservas:
                    print("No posee reservas.")
                for reserva in mis_reservas:
                    print(reserva)

            elif opcion == "0":
                break

            else:
                print("Opción inválida.")

        except SesionExpiradaError as error:
            print(f"Error: {enmascarar_texto(str(error))}")
            break
        except ViajesAventuraError as error:
            print(f"Error: {enmascarar_texto(str(error))}")
        except ValueError as error:
            print(f"Dato inválido: {enmascarar_texto(str(error))}")


# ==========================
# REGISTRO CLIENTE
# ==========================

def solicitar_dato(prompt, validar, comprobar_disponibilidad=None):
    while True:
        valor = input(prompt).strip()
        try:
            validar(valor)
            if comprobar_disponibilidad is not None:
                comprobar_disponibilidad(valor)
            return valor
        except ViajesAventuraError as error:
            print(
                f"Error: {enmascarar_texto(str(error))}. "
                "Ingrese nuevamente este dato."
            )


def validar_correo_disponible(correo):
    if cliente_repo.buscar_por_correo(correo):
        raise ValidacionError("Ya existe un cliente con ese correo.")


def solicitar_contrasena():
    while True:
        mostrar = input(
            "¿Mostrar la contraseña mientras la escribe? (s/N): "
        ).strip().lower()
        if mostrar not in ("s", "n", ""):
            print("Responda s o n.")
            continue
        break

    leer_contrasena = input if mostrar == "s" else getpass.getpass
    while True:
        password = leer_contrasena("Contraseña: ")
        try:
            Validador.validar_contrasena(password)
        except ViajesAventuraError as error:
            print(
                f"Error: {enmascarar_texto(str(error))}. "
                "Ingrese nuevamente la contraseña."
            )
            continue

        confirmacion = leer_contrasena("Confirme la contraseña: ")
        if password != confirmacion:
            print("Las contraseñas no coinciden. Inténtelo nuevamente.")
            continue
        return password


def registrar_cliente():
    try:
        nombre = solicitar_dato("Nombre: ", Validador.validar_nombre)
        rut = solicitar_dato("RUT: ", Validador.validar_rut)
        correo = solicitar_dato(
            "Correo: ",
            Validador.validar_correo,
            validar_correo_disponible
        )
        telefono = solicitar_dato(
            "Teléfono: ",
            Validador.validar_telefono
        )
        password = solicitar_contrasena()

        auth.registrar_cliente(
            nombre,
            rut,
            correo,
            telefono,
            password
        )
        print("Cliente registrado correctamente.")
    except ViajesAventuraError as error:
        print(f"Error: {enmascarar_texto(str(error))}")


# ==========================
# LOGIN CLIENTE
# ==========================

def login_cliente():
    try:
        correo = input("Correo: ")
        password = getpass.getpass("Contraseña: ")
        sesion = auth.iniciar_sesion(correo, password)
        menu_cliente(sesion)
    except ViajesAventuraError as error:
        print(f"Error: {enmascarar_texto(str(error))}")


# ==========================
# LOGIN ADMIN
# ==========================

def login_admin():
    usuario = input("Usuario: ")
    password = getpass.getpass("Contraseña: ")

    if ADMIN_PASSWORD is None:
        print("Credenciales de administrador no configuradas.")
    elif usuario != ADMIN_USUARIO:
        print("Correo o contraseña incorrectos.")
    else:
        try:
            sesion = auth.iniciar_sesion(usuario, password)
            if sesion.rol != "ADMIN":
                raise AutenticacionError(
                    "Correo o contraseña incorrectos."
                )
            menu_admin(sesion)
        except AutenticacionError as error:
            print(f"Error: {enmascarar_texto(str(error))}")


def asegurar_administrador_configurado():
    if ADMIN_PASSWORD is None:
        return
    administrador = cliente_repo.buscar_por_correo(ADMIN_USUARIO)
    if administrador is None:
        cliente_repo.agregar(Cliente(
            "Administrador",
            "",
            ADMIN_USUARIO,
            "",
            GestorContrasenas.generar_hash(ADMIN_PASSWORD),
            "ADMIN"
        ))
    elif administrador.rol == "ADMIN" and not GestorContrasenas.verificar(
        ADMIN_PASSWORD, administrador.password_hash
    ):
        cliente_repo.actualizar_password_hash(
            ADMIN_USUARIO,
            GestorContrasenas.generar_hash(ADMIN_PASSWORD)
        )
        cliente_repo.reiniciar_intentos_fallidos(ADMIN_USUARIO)


# ==========================
# MENÚ PRINCIPAL
# ==========================

def main():
    asegurar_administrador_configurado()
    configurar_logging()
    while True:
        print("\n======================")
        print(" VIAJES AVENTURA ")
        print("======================")
        print("1. Registrar cliente")
        print("2. Iniciar sesión cliente")
        print("3. Iniciar sesión admin")
        print("0. Salir")

        opcion = input("Seleccione: ")
        if opcion == "1":
            registrar_cliente()
        elif opcion == "2":
            login_cliente()
        elif opcion == "3":
            login_admin()
        elif opcion == "0":
            print("Hasta pronto.")
            break
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()