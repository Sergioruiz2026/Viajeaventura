"""Configuración de logs con eliminación de datos sensibles reconocibles."""

import logging
import re


_RUT = re.compile(
    r"(?<!\d)(?:\d{1,2}\.)?\d{3}\.\d{3}-[\dkK]|(?<!\d)\d{7,8}-[\dkK](?!\w)"
)
_TELEFONO = re.compile(r"(?<!\w)\+?\d{8,15}(?!\w)")
_ETIQUETA_SENSIBLE = re.compile(
    r"(?i)(password|contraseña|clave|rut|teléfono|telefono)(\s*[=:]\s*)([^\r\n]*)"
)


def enmascarar_texto(texto: str) -> str:
    texto = _ETIQUETA_SENSIBLE.sub(r"\1\2[REDACTADO]", texto)
    texto = _RUT.sub("[RUT REDACTADO]", texto)
    return _TELEFONO.sub("[TELÉFONO REDACTADO]", texto)


class FiltroDatosSensibles(logging.Filter):
    def filter(self, record):
        record.msg = enmascarar_texto(record.getMessage())
        record.args = ()
        return True


def configurar_logging(ruta: str = "app.log") -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if not any(getattr(handler, "_viajes_log", False) for handler in logger.handlers):
        handler = logging.FileHandler(ruta, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        handler.addFilter(FiltroDatosSensibles())
        handler._viajes_log = True
        logger.addHandler(handler)
    return logger