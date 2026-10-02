import io
import unittest
from contextlib import redirect_stdout
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

    def test_menu_invitado_muestra_opciones_numeradas(self):
        salida = io.StringIO()
        with patch("builtins.input", return_value="0"), redirect_stdout(salida):
            opcion = main.menu_invitado()

        self.assertEqual(opcion, "0")
        self.assertIn("MENÚ INVITADO", salida.getvalue())
        self.assertIn("1. Registrar cliente", salida.getvalue())
        self.assertIn("2. Iniciar sesión cliente", salida.getvalue())
        self.assertIn("3. Iniciar sesión administrador", salida.getvalue())

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


if __name__ == "__main__":
    unittest.main()