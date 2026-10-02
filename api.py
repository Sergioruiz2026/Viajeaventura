"""API HTTP para el registro de clientes."""

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from excepciones import CorreoDuplicadoError, ValidacionError
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from seguridad.logging_config import enmascarar_texto
from servicios.autenticacion_servicio import AutenticacionServicio


class RegistroClienteRequest(BaseModel):
    nombre: str
    rut: str
    email: str
    telefono: str
    password: str


def _sanitizar_detalle(detalle):
    if isinstance(detalle, str):
        return enmascarar_texto(detalle)
    if isinstance(detalle, list):
        return [_sanitizar_detalle(elemento) for elemento in detalle]
    if isinstance(detalle, dict):
        return {
            clave: _sanitizar_detalle(valor)
            for clave, valor in detalle.items()
        }
    return detalle


def _servicio_autenticacion():
    base_datos = BaseDatos()
    try:
        yield AutenticacionServicio(ClienteRepositorio(base_datos))
    finally:
        base_datos.cerrar()


def crear_app(servicio=None):
    app = FastAPI()
    dependencia_servicio = _servicio_autenticacion
    if servicio is not None:
        dependencia_servicio = lambda: servicio

    @app.exception_handler(RequestValidationError)
    async def solicitud_invalida(request: Request, error: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "La solicitud contiene datos inválidos."}
        )

    @app.exception_handler(HTTPException)
    async def error_http(request: Request, error: HTTPException):
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": jsonable_encoder(
                _sanitizar_detalle(error.detail)
            )},
            headers=error.headers
        )

    @app.post("/clientes/registro", status_code=status.HTTP_201_CREATED)
    def registrar_cliente(
        datos: RegistroClienteRequest,
        autenticacion=Depends(dependencia_servicio)
    ):
        try:
            autenticacion.registrar_cliente(
                datos.nombre,
                datos.rut,
                datos.email,
                datos.telefono,
                datos.password
            )
        except CorreoDuplicadoError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error)
            ) from error
        except ValidacionError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(error)
            ) from error
        return {"mensaje": "Cliente registrado correctamente."}

    return app


app = crear_app()