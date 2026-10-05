from datetime import date
from decimal import Decimal, InvalidOperation
import getpass
import logging
import os
import traceback

if os.name == "nt":
    import winreg
else:
    winreg = None

from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio

from servicios.catalogo_servicio import CatalogoServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.reserva_servicio import ReservaServicio
from modelos.cliente import Cliente
from modelos.administrador import Administrador
from modelos.destino import Destino
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
from seguridad.enmascarado import mask_phone, mask_rut
from seguridad.usuarios_demo import asegurar_usuarios_demo


MENSAJE_ERROR_INESPERADO = (
    "Ocurrió un error inesperado al procesar su solicitud. "
    "Por favor intente nuevamente."
)
MENSAJE_ERROR_CONFIGURACION = (
    "La aplicación no está configurada para proteger los datos sensibles. "
    "Defina VIAJES_FERNET_KEY y vuelva a intentarlo."
)
logger = logging.getLogger(__name__)


# ==========================
# INICIALIZACIÓN
# ==========================

base_datos: BaseDatos
destino_repo: DestinoRepositorio
paquete_repo: PaqueteRepositorio
cliente_repo: ClienteRepositorio
reserva_repo: ReservaRepositorio
catalogo: CatalogoServicio
paquetes: PaqueteServicio
auth: AutenticacionServicio
reservas: ReservaServicio

ADMIN_USUARIO = os.environ.get("VIAJES_ADMIN_USUARIO", "admin")
ADMIN_PASSWORD = os.environ.get("VIAJES_ADMIN_PASSWORD")
MARGEN_OPERACION_POR_DEFECTO = Decimal("0.20")

DESTINOS_INICIALES = (
    (
        "Valle del Elqui",
        "Región de Coquimbo",
        "Destino turístico del Valle del Elqui.",
        2,
        120000,
    ),
    (
        "Salar de Surire",
        "Región de Arica y Parinacota",
        "Destino turístico del Salar de Surire.",
        3,
        310000,
    ),
    (
        "Cajón del Maipo",
        "Región Metropolitana",
        "Destino turístico del Cajón del Maipo.",
        1,
        45000,
    ),
    (
        "Parque Conguillío",
        "Región de La Araucanía",
        "Destino turístico del Parque Conguillío.",
        3,
        185000,
    ),
    (
        "Carretera Austral",
        "Región de Aysén",
        "Destino turístico de la Carretera Austral.",
        7,
        640000,
    ),
    (
        "Isla Damas",
        "Región de Coquimbo",
        "Destino turístico de Isla Damas.",
        1,
        38000,
    ),
)


def inicializar_aplicacion():
    global auth, base_datos, catalogo, cliente_repo, destino_repo
    global paquetes, paquete_repo, reserva_repo, reservas

    base_datos = BaseDatos()
    destino_repo = DestinoRepositorio(base_datos)
    paquete_repo = PaqueteRepositorio(base_datos)
    cliente_repo = ClienteRepositorio(base_datos)
    reserva_repo = ReservaRepositorio(base_datos)
    catalogo = CatalogoServicio(destino_repo)
    paquetes = PaqueteServicio(paquete_repo, destino_repo)
    auth = AutenticacionServicio(cliente_repo)
    reservas = ReservaServicio(reserva_repo, paquete_repo)


def cargar_destinos_iniciales():
    for datos_destino in DESTINOS_INICIALES:
        nombre = datos_destino[0]
        if destino_repo.buscar_por_nombre(nombre) is None:
            destino_repo.agregar(Destino(*datos_destino))


def solicitar_margen_operacion():
    margen_ingresado = input(
        "Margen de operación (%) [20]: "
    ).strip()
    if not margen_ingresado:
        return MARGEN_OPERACION_POR_DEFECTO
    return Decimal(margen_ingresado) / Decimal("100")


def cargar_configuracion_entorno_usuario():
    """Carga la clave de usuario en Windows si la terminal no la heredó."""
    if os.environ.get("VIAJES_FERNET_KEY") or os.name != "nt":
        return

    try:
        if winreg is None:
            return
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment"
        ) as clave_usuario:
            clave_fernet, _ = winreg.QueryValueEx(
                clave_usuario,
                "VIAJES_FERNET_KEY"
            )
    except (FileNotFoundError, OSError):
        return

    if isinstance(clave_fernet, str) and clave_fernet.strip():
        os.environ["VIAJES_FERNET_KEY"] = clave_fernet.strip()


def mostrar_error_inesperado():
    logger.error(
        "Error técnico en la interfaz de consola:\n%s",
        traceback.format_exc()
    )
    print(MENSAJE_ERROR_INESPERADO)


def mostrar_error_configuracion():
    logger.error(
        "Error de configuración de seguridad en la interfaz de consola:\n%s",
        traceback.format_exc()
    )
    print(MENSAJE_ERROR_CONFIGURACION)


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
        print("6. Administrar usuarios")
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
                margen = solicitar_margen_operacion()

                paquetes.crear_paquete(
                    nombre,
                    destinos,
                    date(anio_salida, mes_salida, dia_salida),
                    date(anio_retorno, mes_retorno, dia_retorno),
                    cupo,
                    margen_operacion=margen,
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

            elif opcion == "6":
                menu_usuarios_admin(sesion)

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
            print("Dato inválido. Revise el valor e intente nuevamente.")


def menu_usuarios_admin(sesion):
    while True:
        print("\n===== USUARIOS ADMINISTRADORES =====")
        print("1. Cambiar mi usuario y contraseña")
        print("2. Crear otro administrador")
        print("0. Volver")
        opcion = input("Seleccione: ")
        try:
            if opcion == "1":
                nuevo_usuario = input("Nuevo usuario: ").strip()
                nueva_password = solicitar_contrasena()
                auth.cambiar_credenciales_administrador(
                    sesion, nuevo_usuario, nueva_password
                )
                print(
                    "Credenciales actualizadas. Inicie sesión nuevamente "
                    "con el nuevo usuario."
                )
                return
            if opcion == "2":
                usuario = input("Usuario del nuevo administrador: ").strip()
                password = solicitar_contrasena()
                auth.crear_administrador(
                    usuario, password, sesion=sesion
                )
                print("Administrador creado correctamente.")
            elif opcion == "0":
                return
            else:
                print("Opción inválida.")
        except ViajesAventuraError as error:
            print(f"Error: {enmascarar_texto(str(error))}")


# ==========================
# MENÚ CLIENTE
# ==========================

def menu_cliente(sesion):
    while True:
        print(f"\n===== MENÚ CLIENTE: {sesion.nombre} =====")
        print("1. Ver paquetes")
        print("2. Reservar paquete")
        print("3. Mis reservas")
        print("4. Cancelar reserva")
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
                paquete_id = int(input("ID paquete: "))
                personas = int(input("Cantidad personas: "))
                reserva = reservas.crear_reserva(
                    sesion,
                    paquete_id,
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

            elif opcion == "4":
                reserva_id = int(input("ID de reserva: "))
                reservas.cancelar_reserva(sesion, reserva_id)
                print("Reserva cancelada.")

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
            print("Dato inválido. Revise el valor e intente nuevamente.")


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
    except RuntimeError:
        mostrar_error_configuracion()


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

    try:
        sesion = auth.iniciar_sesion(usuario, password)
        if sesion.rol != "ADMIN":
            raise AutenticacionError("Correo o contraseña incorrectos.")
        menu_admin(sesion)
    except AutenticacionError as error:
        print(f"Error: {enmascarar_texto(str(error))}")


def asegurar_administrador_configurado():
    if cliente_repo.contar_administradores() > 0:
        return
    if ADMIN_PASSWORD is None:
        return
    cliente_repo.agregar(Administrador(
        ADMIN_USUARIO,
        GestorContrasenas.generar_hash(ADMIN_PASSWORD),
        nombre="Administrador",
    ))


# ==========================
# MENÚ PRINCIPAL
# ==========================

def main():
    cargar_configuracion_entorno_usuario()
    try:
        configurar_logging()
    except Exception:
        print(MENSAJE_ERROR_INESPERADO)
        return
    try:
        inicializar_aplicacion()
        cargar_destinos_iniciales()
        asegurar_administrador_configurado()
        if "cliente_repo" in globals() and "auth" in globals():
            asegurar_usuarios_demo(cliente_repo, auth)
    except RuntimeError:
        mostrar_error_configuracion()
        return
    except Exception:
        mostrar_error_inesperado()
        return

    while True:
        try:
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
        except EOFError:
            print("Hasta pronto.")
            break
        except Exception:
            mostrar_error_inesperado()


# ==========================
# INTERFAZ WEB
# ==========================

def iniciar_web(host="127.0.0.1", puerto=8000):
    """Prepara la base de datos, levanta la API y abre el navegador."""
    import threading
    import webbrowser

    cargar_configuracion_entorno_usuario()
    try:
        configurar_logging()
        inicializar_aplicacion()
        cargar_destinos_iniciales()
        asegurar_administrador_configurado()
        if "cliente_repo" in globals() and "auth" in globals():
            asegurar_usuarios_demo(cliente_repo, auth)
    except RuntimeError:
        mostrar_error_configuracion()
        return
    except Exception:
        mostrar_error_inesperado()
        return

    # La API abre su propia conexión en cada solicitud.
    try:
        base_datos.cerrar()
    except Exception:
        pass

    if not os.environ.get("VIAJES_FERNET_KEY"):
        print(
            "Aviso: VIAJES_FERNET_KEY no está definida; "
            "el registro de clientes fallará."
        )

    import uvicorn
    from api import app

    url = f"http://{host}:{puerto}/"
    threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    print(f"Abriendo {url}  (Ctrl+C para detener el servidor)")
    uvicorn.run(app, host=host, port=puerto)


def elegir_modo():
    """Pregunta si se abre la interfaz web o la consola."""
    while True:
        print("\n======================")
        print(" VIAJES AVENTURA ")
        print("======================")
        print("¿Cómo desea abrir la aplicación?")
        print("1. Interfaz web (navegador)")
        print("2. Consola")
        print("0. Salir")
        try:
            opcion = input("Seleccione: ").strip()
        except EOFError:
            return None
        if opcion == "1":
            return "web"
        if opcion == "2":
            return "consola"
        if opcion == "0":
            return None
        print("Opción inválida.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Viajes Aventura")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--web",
        action="store_true",
        help="abre la interfaz web sin preguntar",
    )
    modo.add_argument(
        "--consola",
        action="store_true",
        help="abre el menú de consola sin preguntar",
    )
    parser.add_argument(
        "--puerto",
        type=int,
        default=8000,
        help="puerto de la interfaz web (por defecto 8000)",
    )
    argumentos = parser.parse_args()

    if argumentos.web:
        seleccion = "web"
    elif argumentos.consola:
        seleccion = "consola"
    else:
        seleccion = elegir_modo()

    if seleccion == "web":
        iniciar_web(puerto=argumentos.puerto)
    elif seleccion == "consola":
        main()
    else:
        print("Hasta pronto.")