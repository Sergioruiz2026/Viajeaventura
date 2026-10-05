import io
import unittest
import os
from contextlib import redirect_stdout
from unittest.mock import Mock
from unittest.mock import patch

import main
from modelos.cliente import Cliente


class PresentacionConsolaTests(unittest.TestCase):
    def test_cliente_se_muestra_con_rut_y_telefono_enmascarados(self):
        cliente = Cliente(
            "Ana", "12.345.678-5", "ana@example.com", "+56912345678", "hash"
        )

        representacion = str(cliente)

        self.assertIn("12.XXX.XXX-5", representacion)
        self.assertIn("+56 9 XXXX 5678", representacion)
        self.assertNotIn("12.345.678-5", representacion)
        self.assertNotIn("+56912345678", representacion)

    def test_menu_principal_original_muestra_opciones_numeradas(self):
        salida = io.StringIO()
        with (
            patch.object(main, "configurar_logging"),
            patch.object(main, "inicializar_aplicacion"),
            patch.object(main, "cargar_destinos_iniciales"),
            patch.object(main, "asegurar_administrador_configurado"),
            patch("builtins.input", return_value="0"),
            redirect_stdout(salida)
        ):
            main.main()

        self.assertIn("VIAJES AVENTURA", salida.getvalue())
        self.assertNotIn("MENÚ INVITADO", salida.getvalue())
        self.assertIn("1. Registrar cliente", salida.getvalue())
        self.assertIn("2. Iniciar sesión cliente", salida.getvalue())
        self.assertIn("3. Iniciar sesión admin", salida.getvalue())

    def test_error_tecnico_muestra_mensaje_generico_y_registra_traza(self):
        salida = io.StringIO()
        with patch.object(main.logger, "error") as registrar_error:
            with redirect_stdout(salida):
                try:
                    raise RuntimeError("detalle técnico interno")
                except RuntimeError:
                    main.mostrar_error_inesperado()

        self.assertEqual(
            salida.getvalue().strip(), main.MENSAJE_ERROR_INESPERADO
        )
        self.assertNotIn("RuntimeError", salida.getvalue())
        self.assertNotIn("detalle técnico interno", salida.getvalue())
        traza = registrar_error.call_args.args[1]
        self.assertIn("Traceback (most recent call last)", traza)
        self.assertIn("RuntimeError: detalle técnico interno", traza)

    def test_inicio_web_en_todas_las_interfaces_abre_loopback_local(self):
        base_datos = Mock()
        salida = io.StringIO()
        with (
            patch.dict(os.environ, {"VIAJES_FERNET_KEY": "clave-de-prueba"}),
            patch.object(main, "cargar_configuracion_entorno_usuario"),
            patch.object(main, "configurar_logging"),
            patch.object(main, "inicializar_aplicacion"),
            patch.object(main, "cargar_destinos_iniciales"),
            patch.object(main, "asegurar_administrador_configurado"),
            patch.object(main, "base_datos", base_datos, create=True),
            patch("threading.Timer") as timer,
            patch("uvicorn.run") as run_server,
            redirect_stdout(salida),
        ):
            main.iniciar_web(host="0.0.0.0", puerto=8765)

        timer.assert_called_once()
        self.assertEqual(
            timer.call_args.kwargs["args"],
            ("http://127.0.0.1:8765/",),
        )
        run_server.assert_called_once()
        self.assertEqual(run_server.call_args.kwargs["host"], "0.0.0.0")
        self.assertEqual(run_server.call_args.kwargs["port"], 8765)


if __name__ == "__main__":
    unittest.main()