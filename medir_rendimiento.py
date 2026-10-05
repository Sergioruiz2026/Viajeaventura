"""Mide el tiempo de respuesta del listado de paquetes y de una reserva (RNF-06).

Usa una base de datos temporal con 20 paquetes y 214 reservas, que es el
volumen de una temporada segun el caso. No toca la base de datos real.

Uso:  py medir_rendimiento.py
"""
import os
import shutil
import statistics
import tempfile
import time
from datetime import date, timedelta

from cryptography.fernet import Fernet

os.environ.setdefault("VIAJES_FERNET_KEY", Fernet.generate_key().decode())

from modelos.destino import Destino  # noqa: E402
from modelos.sesion import Sesion  # noqa: E402
from repositorios.base_datos import BaseDatos  # noqa: E402
from repositorios.cliente_repositorio import ClienteRepositorio  # noqa: E402
from repositorios.destino_repositorio import DestinoRepositorio  # noqa: E402
from repositorios.paquete_repositorio import PaqueteRepositorio  # noqa: E402
from repositorios.reserva_repositorio import ReservaRepositorio  # noqa: E402
from servicios.autenticacion_servicio import AutenticacionServicio  # noqa: E402
from servicios.paquete_servicio import PaqueteServicio  # noqa: E402
from servicios.reserva_servicio import ReservaServicio  # noqa: E402

RESERVAS = 214
PAQUETES = 20
REPETICIONES = 30


def preparar(base_datos):
    clientes = ClienteRepositorio(base_datos)
    autenticacion = AutenticacionServicio(clientes)
    autenticacion.registrar_cliente(
        "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
        "ClaveFuerte1!"
    )
    sesion = autenticacion.iniciar_sesion("ana@example.com", "ClaveFuerte1!")
    administrador = Sesion.administrador("admin")

    destinos = DestinoRepositorio(base_datos)
    paquetes = PaqueteRepositorio(base_datos)
    nombres = []
    for i in range(12):
        nombre = f"Destino {chr(65 + i)}"
        nombres.append(nombre)
        destinos.agregar(Destino(nombre, "Zona", "Descripcion", 3, 100000 + i * 1000))

    servicio_paquetes = PaqueteServicio(paquetes, destinos)
    salida = date.today() + timedelta(days=30)
    for i in range(PAQUETES):
        servicio_paquetes.crear_paquete(
            f"Paquete {chr(65 + i)}",
            [nombres[i % 12], nombres[(i + 1) % 12], nombres[(i + 2) % 12]],
            salida, salida + timedelta(days=5), 60, sesion=administrador
        )

    conexion = base_datos.conexion
    ids = [fila["id"] for fila in conexion.execute(
        "SELECT id FROM paquetes ORDER BY id"
    ).fetchall()]
    # Las reservas de otros clientes se insertan directo para no esperar
    # el hash Argon2id de 214 registros.
    for k in range(RESERVAS):
        conexion.execute(
            "INSERT INTO usuarios (nombre, rut, correo, telefono, password_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"Cliente {k}", f"rut-{k}", f"cliente{k}@example.com", "tel", "hash")
        )
        usuario_id = conexion.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]
        conexion.execute(
            "INSERT INTO reservas (usuario_id, paquete_id, cantidad_personas, "
            "fecha_emision, total) VALUES (?, ?, ?, ?, ?)",
            (usuario_id, ids[k % (PAQUETES - 1)], 2, date.today().isoformat(), 100)
        )
    conexion.commit()
    servicio_reservas = ReservaServicio(ReservaRepositorio(base_datos), paquetes)
    return sesion, servicio_paquetes, servicio_reservas, ids[-1]


def main():
    carpeta = tempfile.mkdtemp()
    base_datos = BaseDatos(os.path.join(carpeta, "medicion.db"))
    try:
        sesion, servicio_paquetes, servicio_reservas, paquete_libre = preparar(base_datos)

        tiempos = []
        for _ in range(REPETICIONES):
            inicio = time.perf_counter()
            servicio_paquetes.listar_vigentes(sesion=sesion)
            tiempos.append(time.perf_counter() - inicio)
        listado_ms = statistics.median(tiempos) * 1000

        inicio = time.perf_counter()
        servicio_reservas.crear_reserva(sesion, paquete_libre, 2)
        reserva_ms = (time.perf_counter() - inicio) * 1000

        print(f"Base de prueba: {PAQUETES} paquetes y {RESERVAS} reservas.")
        print(f"Listado de paquetes vigentes: {listado_ms:.1f} ms "
              f"(mediana de {REPETICIONES} ejecuciones)")
        print(f"Reserva de un paquete:        {reserva_ms:.1f} ms")
        limite = 1000
        estado = "CUMPLE" if max(listado_ms, reserva_ms) < limite else "NO CUMPLE"
        print(f"RNF-06 (menos de 1 segundo): {estado}")
    finally:
        base_datos.cerrar()
        shutil.rmtree(carpeta, ignore_errors=True)


if __name__ == "__main__":
    main()
