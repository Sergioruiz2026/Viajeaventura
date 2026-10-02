import io
from contextlib import redirect_stdout
from decimal import Decimal
from unittest.mock import Mock, patch

import main


def test_margen_de_operacion_se_interpreta_como_porcentaje():
    with patch("builtins.input", return_value="15"):
        assert main.solicitar_margen_operacion() == Decimal("0.15")


def test_registro_muestra_error_de_configuracion_para_fallo_fernet():
    salida = io.StringIO()
    with (
        patch.object(main, "solicitar_dato", return_value="dato"),
        patch.object(main, "solicitar_contrasena", return_value="ClaveFuerte1!"),
        patch.object(
            main,
            "auth",
            Mock(
                registrar_cliente=Mock(
                    side_effect=RuntimeError(
                        "Configure VIAJES_FERNET_KEY con una clave Fernet válida."
                    )
                )
            ),
            create=True,
        ),
        redirect_stdout(salida),
    ):
        main.registrar_cliente()

    assert salida.getvalue().strip() == main.MENSAJE_ERROR_CONFIGURACION
