from datetime import date
import os
from datetime import date

from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio

from servicios.catalogo_servicio import CatalogoServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.reserva_servicio import ReservaServicio

from excepciones import ViajesAventuraError


# ==========================
# INICIALIZACIÓN
# ==========================

destino_repo = DestinoRepositorio()
paquete_repo = PaqueteRepositorio()
cliente_repo = ClienteRepositorio()
reserva_repo = ReservaRepositorio()

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

def menu_admin():
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
                costo = float(input("Costo base: "))
                catalogo.registrar_destino(
                    nombre,
                    zona,
                    descripcion,
                    duracion,
                    costo
                )
                print("Destino registrado.")

            elif opcion == "2":
                for destino in catalogo.listar_destinos():
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
                    cupo
                )
                print("Paquete creado.")

            elif opcion == "4":
                for paquete in paquetes.listar_paquetes():
                    print(paquete)

            elif opcion == "5":
                todas = reservas.listar_reservas()
                if not todas:
                    print("No existen reservas.")
                for reserva in todas:
                    print(reserva)

            elif opcion == "0":
                break

            else:
                print("Opción inválida.")

        except ViajesAventuraError as error:
            print(f"Error: {error}")
        except ValueError as error:
            print(f"Dato inválido: {error}")


# ==========================
# MENÚ CLIENTE
# ==========================

def menu_cliente(cliente):
    while True:
        print(f"\n===== BIENVENIDO {cliente.nombre} =====")
        print("1. Ver paquetes")
        print("2. Reservar paquete")
        print("3. Mis reservas")
        print("0. Cerrar sesión")

        opcion = input("Seleccione: ")
        try:
            if opcion == "1":
                lista = paquetes.listar_vigentes()
                if not lista:
                    print("No existen paquetes.")
                for paquete in lista:
                    print(paquete)

            elif opcion == "2":
                nombre_paquete = input("Nombre paquete: ")
                personas = int(input("Cantidad personas: "))
                reserva = reservas.crear_reserva(
                    cliente,
                    nombre_paquete,
                    personas
                )
                print("Reserva realizada.")
                print(f"Total: ${reserva.total:,.0f}")

            elif opcion == "3":
                mis_reservas = reservas.reservas_cliente(
                    cliente.correo
                )
                if not mis_reservas:
                    print("No posee reservas.")
                for reserva in mis_reservas:
                    print(reserva)

            elif opcion == "0":
                break

            else:
                print("Opción inválida.")

        except ViajesAventuraError as error:
            print(f"Error: {error}")
        except ValueError as error:
            print(f"Dato inválido: {error}")


# ==========================
# REGISTRO CLIENTE
# ==========================

def registrar_cliente():
    try:
        nombre = input("Nombre: ")
        rut = input("RUT: ")
        correo = input("Correo: ")
        telefono = input("Teléfono: ")
        password = input("Contraseña: ")

        auth.registrar_cliente(
            nombre,
            rut,
            correo,
            telefono,
            password
        )
        print("Cliente registrado correctamente.")
    except ViajesAventuraError as error:
        print(f"Error: {error}")


# ==========================
# LOGIN CLIENTE
# ==========================

def login_cliente():
    try:
        correo = input("Correo: ")
        password = input("Contraseña: ")
        cliente = auth.iniciar_sesion(correo, password)
        menu_cliente(cliente)
    except ViajesAventuraError as error:
        print(f"Error: {error}")


# ==========================
# LOGIN ADMIN
# ==========================

def login_admin():
    usuario = input("Usuario: ")
    password = input("Contraseña: ")

    if ADMIN_PASSWORD is None:
        print("Credenciales de administrador no configuradas.")
    elif usuario == ADMIN_USUARIO and password == ADMIN_PASSWORD:
        menu_admin()
    else:
        print("Credenciales incorrectas.")


# ==========================
# MENÚ PRINCIPAL
# ==========================

def main():
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