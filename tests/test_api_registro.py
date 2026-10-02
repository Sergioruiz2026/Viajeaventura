import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from api import crear_app
from excepciones import ValidacionError
from repositorios.base_datos import BaseDatos

class ApiRegistroClienteTests(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        self.ruta = str(Path(self.directorio.name) / "registro.db")
        self.entorno = patch.dict(os.environ, {
            "VIAJES_FERNET_KEY": Fernet.generate_key().decode(),
            "VIAJES_DB_PATH": self.ruta
        })
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.base_datos = BaseDatos(self.ruta)
        self.addCleanup(self.base_datos.cerrar)
        self.client = TestClient(crear_app())
        self.datos = {
            "nombre": "Ana Pérez",
            "rut": "12.345.678-5",
            "email": "ana@example.com",
            "telefono": "+56912345678",
            "password": "ClaveFuerte1!"
        }

    def test_registra_y_no_devuelve_datos_credenciales(self):
        respuesta = self.client.post("/clientes/registro", json=self.datos)

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            respuesta.json(),
            {"mensaje": "Cliente registrado correctamente."}
        )
        cuerpo_respuesta = respuesta.text
        self.assertNotIn(self.datos["rut"], cuerpo_respuesta)
        self.assertNotIn(self.datos["telefono"], cuerpo_respuesta)
        self.assertNotIn(self.datos["password"], cuerpo_respuesta)

        fila = self.base_datos.conexion.execute(
            "SELECT rut, telefono, password_hash FROM usuarios"
        ).fetchone()
        self.assertNotEqual(fila["rut"], self.datos["rut"])
        self.assertNotEqual(fila["telefono"], self.datos["telefono"])
        self.assertTrue(fila["password_hash"].startswith("$argon2id$"))

    def test_responde_409_para_correo_duplicado(self):
        self.client.post("/clientes/registro", json=self.datos)
        datos_duplicados = {**self.datos, "email": "ANA@example.com"}

        respuesta = self.client.post(
            "/clientes/registro", json=datos_duplicados
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertNotIn(self.datos["telefono"], respuesta.text)

    def test_responde_422_para_rut_o_password_invalidos(self):
        rut_invalido = {**self.datos, "rut": "12.345.678-9"}
        respuesta_rut = self.client.post(
            "/clientes/registro", json=rut_invalido
        )
        self.assertEqual(respuesta_rut.status_code, 422)
        self.assertNotIn(self.datos["telefono"], respuesta_rut.text)

        password_invalido = {**self.datos, "password": "ClaveFuerte1"}
        respuesta_password = self.client.post(
            "/clientes/registro", json=password_invalido
        )
        self.assertEqual(respuesta_password.status_code, 422)
        self.assertNotIn(self.datos["password"], respuesta_password.text)

    def test_enmascara_rut_y_telefono_en_errores_http(self):
        class ServicioConError:
            def registrar_cliente(self, *args):
                raise ValidacionError(
                    "RUT 12.345.678-K y teléfono +56 9 1234 1234 inválidos."
                )

        cliente_api = TestClient(crear_app(ServicioConError()))
        respuesta = cliente_api.post(
            "/clientes/registro", json=self.datos
        )

        self.assertEqual(respuesta.status_code, 422)
        self.assertIn("12.XXX.XXX-K", respuesta.text)
        self.assertIn("+56 9 XXXX 1234", respuesta.text)
        self.assertNotIn("12.345.678-K", respuesta.text)
        self.assertNotIn("+56 9 1234 1234", respuesta.text)


if __name__ == "__main__":
    unittest.main()