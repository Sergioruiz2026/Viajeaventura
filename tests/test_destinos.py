import os
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from cryptography.fernet import Fernet

from excepciones import DestinoDuplicadoError, ValidacionError
from modelos.destino import Destino
from repositorios.base_datos import BaseDatos
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from servicios.catalogo_servicio import CatalogoServicio
from servicios.paquete_servicio import PaqueteServicio


class GestionDestinosTests(unittest.TestCase):
    def setUp(self):
        self.entorno = patch.dict(os.environ, {
            "VIAJES_FERNET_KEY": Fernet.generate_key().decode()
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.base_datos = BaseDatos(":memory:")
        self.addCleanup(self.base_datos.cerrar)
        self.destinos = DestinoRepositorio(self.base_datos)
        self.catalogo = CatalogoServicio(self.destinos)
        self.paquetes = PaqueteRepositorio(self.base_datos)
        self.servicio_paquetes = PaqueteServicio(
            self.paquetes, self.destinos
        )

    def registrar_destino(self, nombre, costo=100):
        return self.catalogo.registrar_destino(
            nombre, "Zona", f"Descripción de {nombre}", 3, costo
        )

    def test_registro_valida_datos_y_rechaza_nombre_duplicado_sin_case(self):
        self.registrar_destino("Atacama")

        with self.assertRaises(DestinoDuplicadoError):
            self.registrar_destino("aTaCaMa")
        with self.assertRaises(ValidacionError):
            self.catalogo.registrar_destino("Inválido", "Zona", "Desc", 2, 0)
        with self.assertRaises(ValidacionError):
            self.catalogo.registrar_destino("Inválido", "Zona", "Desc", True, 10)
        with self.assertRaises(ValidacionError):
            self.catalogo.registrar_destino(None, "Zona", "Desc", 2, 10)

    def test_modificar_destino_no_cambia_precio_de_paquete_publicado(self):
        self.registrar_destino("Norte", 100)
        self.registrar_destino("Sur", 200)
        salida = date.today() + timedelta(days=30)
        self.servicio_paquetes.crear_paquete(
            "Ruta", ["Norte", "Sur"], salida, salida + timedelta(days=5), 4
        )
        precio_publicado = self.paquetes.buscar_por_nombre(
            "Ruta"
        ).precio_por_persona

        actualizado = self.catalogo.modificar_destino(
            "Norte", "Norte actualizado", "Nueva zona", "Nueva descripción",
            6, 900
        )

        self.assertEqual(actualizado.nombre, "Norte actualizado")
        paquete_guardado = self.paquetes.buscar_por_nombre("Ruta")
        self.assertEqual(paquete_guardado.precio_por_persona, precio_publicado)
        self.assertEqual(paquete_guardado.destinos[0].costo_base, 900)

    def test_elimina_destino_sin_paquetes_y_desactiva_destino_asociado(self):
        self.registrar_destino("Libre")
        self.assertTrue(self.catalogo.eliminar_destino("Libre"))
        self.assertIsNone(self.destinos.buscar_por_nombre("Libre"))

        self.registrar_destino("Norte")
        self.registrar_destino("Sur")
        salida = date.today() + timedelta(days=30)
        self.servicio_paquetes.crear_paquete(
            "Ruta", ["Norte", "Sur"], salida, salida + timedelta(days=5), 4
        )

        self.assertTrue(self.catalogo.eliminar_destino("Norte"))
        desactivado = self.destinos.buscar_por_nombre("Norte")
        self.assertIsNotNone(desactivado)
        self.assertFalse(desactivado.disponible)
        self.assertEqual(
            {destino.nombre: destino.disponible
             for destino in self.catalogo.listar_destinos()}["Norte"],
            False
        )
        with self.assertRaises(ValidacionError):
            self.servicio_paquetes.crear_paquete(
                "Ruta nueva", ["Norte", "Sur"], salida,
                salida + timedelta(days=7), 4
            )


if __name__ == "__main__":
    unittest.main()