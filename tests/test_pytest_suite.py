from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier, Lock

import pytest
from cryptography.fernet import Fernet

from excepciones import CupoInsuficienteError
from modelos.cliente import Cliente
from modelos.destino import Destino
from modelos.sesion import Sesion
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.reserva_servicio import ReservaServicio


@pytest.fixture
def base_datos_memoria(monkeypatch):
    monkeypatch.setenv(
        "VIAJES_FERNET_KEY", Fernet.generate_key().decode("ascii")
    )
    base_datos = BaseDatos(":memory:")
    try:
        yield base_datos
    finally:
        base_datos.cerrar()


def test_fixture_aisla_usuarios_en_memoria(base_datos_memoria):
    cantidad = base_datos_memoria.conexion.execute(
        "SELECT COUNT(*) FROM usuarios"
    ).fetchone()[0]
    assert cantidad == 0


def test_cupo_no_se_sobrecarga_con_reservas_concurrentes(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(
        "VIAJES_FERNET_KEY", Fernet.generate_key().decode("ascii")
    )
    ruta_bd = tmp_path / "reservas_concurrentes.db"
    base_datos = BaseDatos(str(ruta_bd))
    clientes = ClienteRepositorio(base_datos)
    autenticacion = AutenticacionServicio(clientes)
    autenticacion.registrar_cliente(
        "Ana", "12.345.678-5", "ana@example.com", "+56912345678",
        "ClaveFuerte1!"
    )
    autenticacion.registrar_cliente(
        "Bea", "11.111.111-1", "bea@example.com", "+56987654321",
        "ClaveFuerte2!"
    )
    sesiones = (
        autenticacion.iniciar_sesion("ana@example.com", "ClaveFuerte1!"),
        autenticacion.iniciar_sesion("bea@example.com", "ClaveFuerte2!")
    )
    destinos = DestinoRepositorio(base_datos)
    destinos.agregar(Destino("Norte", "Zona", "Desierto", 3, 100))
    destinos.agregar(Destino("Sur", "Zona", "Lagos", 4, 200))
    paquetes = PaqueteRepositorio(base_datos)
    PaqueteServicio(paquetes, destinos).crear_paquete(
        "Cupo concurrente",
        ["Norte", "Sur"],
        date.today() + timedelta(days=30),
        date.today() + timedelta(days=35),
        1,
        sesion=Sesion.administrador("admin")
    )
    paquete_id = base_datos.conexion.execute(
        "SELECT id FROM paquetes WHERE nombre = ?",
        ("Cupo concurrente",)
    ).fetchone()["id"]
    base_datos.cerrar()

    barrera = Barrier(2)
    inicializacion_db = Lock()

    def reservar_en_hilo(sesion):
        with inicializacion_db:
            conexion_db = BaseDatos(str(ruta_bd))
        servicio = ReservaServicio(
            ReservaRepositorio(conexion_db),
            PaqueteRepositorio(conexion_db)
        )
        barrera.wait(timeout=10)
        try:
            servicio.crear_reserva(sesion, paquete_id, 1)
            return "confirmada"
        except CupoInsuficienteError:
            return "sin_cupo"
        finally:
            conexion_db.cerrar()

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(reservar_en_hilo, sesiones))

    verificacion = BaseDatos(str(ruta_bd))
    try:
        ocupadas = verificacion.conexion.execute(
            """
            SELECT COALESCE(SUM(cantidad_personas), 0)
            FROM reservas WHERE paquete_id = ? AND estado = 'ACTIVA'
            """,
            (paquete_id,)
        ).fetchone()[0]
    finally:
        verificacion.cerrar()

    assert Counter(resultados) == Counter({"confirmada": 1, "sin_cupo": 1})
    assert ocupadas == 1