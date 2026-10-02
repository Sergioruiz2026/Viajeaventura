"""Operaciones monetarias exactas para importes expresados en CLP."""

from decimal import Decimal, ROUND_HALF_UP


def a_decimal(valor) -> Decimal:
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


def redondear_clp(valor) -> Decimal:
    return a_decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def aplicar_margen_clp(costo, margen) -> Decimal:
    return redondear_clp(a_decimal(costo) * (Decimal("1") + a_decimal(margen)))