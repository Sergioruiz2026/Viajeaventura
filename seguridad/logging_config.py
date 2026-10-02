"""Configuración de logs con eliminación de datos sensibles reconocibles."""

import logging
import re

from seguridad.enmascarado import mask_phone, mask_rut

_RUT = re.compile(
    r"(?<!\w)(?:[0-9]{1,2}\.)?[0-9]{3}\.[0-9]{3}-[0-9Kk]|"
    r"(?<!\w)[0-9]{7,8}-[0-9Kk](?!\w)"
)
_TELEFONO = re.compile(
    r"(?<!\w)(?:\+?56[\s.-]*)?9(?:[\s.-]*[0-9]){8}(?!\w)"
)
_ETIQUETA_CREDENCIAL = re.compile(
    r"(?i)(password|contraseña|clave)(\s*[=:]\s*)([^\r\n]*)"
)


def enmascarar_texto(texto: str) -> str:
    texto = _ETIQUETA_CREDENCIAL.sub(r"\1\2[REDACTADO]", texto)
    texto = _RUT.sub(lambda coincidencia: mask_rut(coincidencia.group()), texto)
    return _TELEFONO.sub(
        lambda coincidencia: mask_phone(coincidencia.group()), texto
    )


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