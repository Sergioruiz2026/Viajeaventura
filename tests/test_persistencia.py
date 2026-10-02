import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from modelos.destino import Destino
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.reserva_servicio import ReservaServicio


class PersistenciaSQLiteTests(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.ruta = str(Path(self.directorio.name) / "viajes.db")
        self.base_datos = BaseDatos(self.ruta)

    def tearDown(self):
        self.base_datos.cerrar()
        self.directorio.cleanup()

    def test_cliente_paquete_y_reserva_sobreviven_reapertura(self):
        clientes = ClienteRepositorio(self.base_datos)
        destinos = DestinoRepositorio(self.base_datos)
        paquetes = PaqueteRepositorio(self.base_datos)
        reservas = ReservaRepositorio(self.base_datos)

        cliente = AutenticacionServicio(clientes).registrar_cliente(
            "Ana",
            "12345678-9",
            "ana@example.com",
            "+56912345678",
            "ClaveFuerte1"
        )
        destinos.agregar(Destino("Norte", "Norte", "Desierto", 4, 100))
        destinos.agregar(Destino("Sur", "Sur", "Lagos", 5, 200))

        salida = date.today() + timedelta(days=30)
        PaqueteServicio(paquetes, destinos).crear_paquete(
            "Ruta Chile",
            ["Norte", "Sur"],
            salida,
            salida + timedelta(days=7),
            4
        )
        ReservaServicio(reservas, paquetes).crear_reserva(
            cliente,
            "Ruta Chile",
            2
        )
        self.base_datos.cerrar()

        self.base_datos = BaseDatos(self.ruta)
        clientes = ClienteRepositorio(self.base_datos)
        destinos = DestinoRepositorio(self.base_datos)
        paquetes = PaqueteRepositorio(self.base_datos)
        reservas = ReservaRepositorio(self.base_datos)

        cliente_guardado = clientes.buscar_por_correo("ANA@example.com")
        paquete_guardado = paquetes.buscar_por_nombre("ruta chile")
        reservas_guardadas = reservas.reservas_por_cliente(
            "ana@example.com"
        )

        self.assertIsNotNone(cliente_guardado)
        self.assertEqual(cliente_guardado.nombre, "Ana")
        self.assertEqual(len(destinos.listar()), 2)
        self.assertEqual(
            [destino.nombre for destino in paquete_guardado.destinos],
            ["Norte", "Sur"]
        )
        self.assertEqual(paquete_guardado.precio_por_persona, 360)
        self.assertEqual(len(reservas_guardadas), 1)
        self.assertEqual(reservas_guardadas[0].cantidad_personas, 2)
        self.assertEqual(reservas_guardadas[0].total, 720)
        self.assertEqual(reservas.cupos_ocupados("Ruta Chile"), 2)


if __name__ == "__main__":
    unittest.main()