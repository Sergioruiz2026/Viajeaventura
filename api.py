"""API HTTP para el registro de clientes y gestión web."""

import os
import secrets
from datetime import date
from decimal import Decimal

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from excepciones import (
    AutenticacionError,
    AutorizacionError,
    CorreoDuplicadoError,
    CupoInsuficienteError,
    DestinoDuplicadoError,
    PaqueteDuplicadoError,
    ReservaNoPermitidaError,
    SesionExpiradaError,
    ValidacionError,
    ViajesAventuraError,
)
from modelos.sesion import Sesion
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from repositorios.destino_repositorio import DestinoRepositorio
from repositorios.paquete_repositorio import PaqueteRepositorio
from repositorios.reserva_repositorio import ReservaRepositorio
from repositorios.salida_repositorio import SalidaRepositorio
from seguridad.logging_config import enmascarar_texto
from servicios.autenticacion_servicio import AutenticacionServicio
from servicios.catalogo_servicio import CatalogoServicio
from servicios.paquete_servicio import PaqueteServicio
from servicios.reserva_servicio import ReservaServicio


# ---------------------------------------------------------------------------
# Modelos de request
# ---------------------------------------------------------------------------

class RegistroClienteRequest(BaseModel):
    nombre: str
    rut: str
    email: str
    telefono: str
    password: str


class LoginRequest(BaseModel):
    usuario: str
    password: str


class DestinoRequest(BaseModel):
    nombre: str
    zona: str
    descripcion: str
    duracion_dias: int
    costo_base: Decimal


class PaqueteRequest(BaseModel):
    nombre: str
    destinos: list[str]
    fecha_salida: date
    fecha_regreso: date
    cupo_maximo: int
    margen_operacion: Decimal = Decimal("0.20")


class ReservaRequest(BaseModel):
    salida_id: int
    cantidad_personas: int


class NuevaSalidaRequest(BaseModel):
    fecha_salida: date
    fecha_regreso: date
    cupo_maximo: int


class ActualizarSalidaRequest(NuevaSalidaRequest):
    pass


class RecuperarContrasenaRequest(BaseModel):
    correo: str
    rut: str
    nueva_password: str


class ActualizarPaqueteRequest(BaseModel):
    nombre: str | None = None
    fecha_salida: date | None = None
    fecha_regreso: date | None = None
    cupo_maximo: int | None = None
    margen_operacion: Decimal | None = None


# ---------------------------------------------------------------------------
# Almacén de sesiones en memoria
# ---------------------------------------------------------------------------

_sesiones: dict[str, Sesion] = {}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _sanitizar_detalle(detalle):
    if isinstance(detalle, str):
        return enmascarar_texto(detalle)
    if isinstance(detalle, list):
        return [_sanitizar_detalle(e) for e in detalle]
    if isinstance(detalle, dict):
        return {k: _sanitizar_detalle(v) for k, v in detalle.items()}
    return detalle


def _serializar_paquete(p) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "precio_por_persona": int(p.precio_por_persona),
        "fecha_salida": p.fecha_salida.isoformat(),
        "fecha_regreso": p.fecha_regreso.isoformat(),
        "cupo_maximo": p.cupo_maximo,
        "cupo_disponible": p.cupo_disponible,
        "margen_operacion": float(p.margen_operacion),
        "estado": p.estado,
    }


def _serializar_salida(salida) -> dict:
    return {
        "id": salida.id,
        "paquete_id": salida.paquete_id,
        "nombre": salida.paquete_nombre,
        "precio_por_persona": int(salida.precio_por_persona),
        "fecha_salida": salida.fecha_salida.isoformat(),
        "fecha_regreso": salida.fecha_regreso.isoformat(),
        "cupo_maximo": salida.cupo_maximo,
        "cupo_disponible": salida.cupo_disponible,
        "estado": "Vigente",
    }


def _exc_a_http(error: ViajesAventuraError) -> HTTPException:
    if isinstance(error, SesionExpiradaError):
        return HTTPException(status_code=401, detail="Sesión expirada. Inicia sesión nuevamente.")
    if isinstance(error, AutenticacionError):
        return HTTPException(status_code=401, detail=str(error))
    if isinstance(error, AutorizacionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, (CorreoDuplicadoError, DestinoDuplicadoError, PaqueteDuplicadoError)):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, (CupoInsuficienteError, ReservaNoPermitidaError)):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, ValidacionError):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


# ---------------------------------------------------------------------------
# Dependencias
# ---------------------------------------------------------------------------

class _Servicios:
    def __init__(self, base_datos: BaseDatos):
        destino_repo = DestinoRepositorio(base_datos)
        paquete_repo = PaqueteRepositorio(base_datos)
        cliente_repo = ClienteRepositorio(base_datos)
        reserva_repo = ReservaRepositorio(base_datos)
        salida_repo  = SalidaRepositorio(base_datos)
        self.autenticacion = AutenticacionServicio(cliente_repo)
        self.catalogo = CatalogoServicio(destino_repo)
        self.paquetes = PaqueteServicio(paquete_repo, destino_repo, salida_repo)
        self.reservas = ReservaServicio(reserva_repo, paquete_repo, salida_repo)
        self.salidas  = salida_repo


def _servicios_dep():
    bd = BaseDatos()
    try:
        yield _Servicios(bd)
    finally:
        bd.cerrar()


def _obtener_sesion(session: str | None = Cookie(default=None)) -> Sesion:
    if not session or session not in _sesiones:
        raise HTTPException(status_code=401, detail="No autenticado.")
    try:
        _sesiones[session].renovar()
    except SesionExpiradaError:
        _sesiones.pop(session, None)
        raise HTTPException(status_code=401, detail="Sesión expirada.")
    return _sesiones[session]


def _verificar_csrf(request: Request) -> None:
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise HTTPException(status_code=403, detail="Cabecera CSRF requerida.")


# ---------------------------------------------------------------------------
# Factory de la aplicación
# ---------------------------------------------------------------------------

def crear_app(servicio=None):
    app = FastAPI()

    if servicio is not None:
        def _dep_registro():
            yield servicio
    else:
        def _dep_registro():
            bd = BaseDatos()
            try:
                yield AutenticacionServicio(ClienteRepositorio(bd))
            finally:
                bd.cerrar()

    # --- manejadores de error globales ---------------------------------- #

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
            content={"detail": jsonable_encoder(_sanitizar_detalle(error.detail))},
            headers=error.headers,
        )

    # --- endpoint legado ------------------------------------------------ #

    @app.post("/clientes/registro", status_code=status.HTTP_201_CREATED)
    def registrar_cliente(
        datos: RegistroClienteRequest,
        autenticacion=Depends(_dep_registro),
    ):
        try:
            autenticacion.registrar_cliente(
                datos.nombre, datos.rut, datos.email,
                datos.telefono, datos.password,
            )
        except CorreoDuplicadoError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
        except ValidacionError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        return {"mensaje": "Cliente registrado correctamente."}

    # --- autenticación web ---------------------------------------------- #

    @app.post("/api/login")
    def login(
        datos: LoginRequest,
        response: Response,
        _: None = Depends(_verificar_csrf),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            sesion = svcs.autenticacion.iniciar_sesion(datos.usuario, datos.password)
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        token = secrets.token_hex(32)
        _sesiones[token] = sesion
        response.set_cookie(
            key="session",
            value=token,
            httponly=True,
            samesite="strict",
            max_age=1800,
        )
        return {"nombre": sesion.nombre, "rol": sesion.rol}

    @app.post("/api/logout")
    def logout(
        response: Response,
        _: None = Depends(_verificar_csrf),
        session: str | None = Cookie(default=None),
    ):
        if session:
            _sesiones.pop(session, None)
        response.delete_cookie("session")
        return {"mensaje": "Sesión cerrada."}

    @app.get("/api/yo")
    def yo(sesion: Sesion = Depends(_obtener_sesion)):
        return {"nombre": sesion.nombre, "rol": sesion.rol}

    # --- destinos -------------------------------------------------------- #

    @app.get("/api/destinos")
    def listar_destinos(
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            lista = svcs.catalogo.listar_destinos(sesion=sesion)
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return [
            {
                "nombre": d.nombre,
                "zona": d.zona,
                "descripcion": d.descripcion,
                "duracion_dias": d.duracion_dias,
                "costo_base": int(d.costo_base),
                "disponible": d.disponible,
            }
            for d in lista
        ]

    @app.post("/api/destinos", status_code=201)
    def crear_destino(
        datos: DestinoRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            d = svcs.catalogo.registrar_destino(
                datos.nombre, datos.zona, datos.descripcion,
                datos.duracion_dias, datos.costo_base,
                sesion=sesion,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return {"nombre": d.nombre, "zona": d.zona}

    # --- paquetes -------------------------------------------------------- #

    @app.get("/api/paquetes")
    def listar_paquetes(
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            if sesion.rol == "ADMIN":
                lista = svcs.paquetes.listar_paquetes(sesion=sesion)
                respuesta = [_serializar_paquete(p) for p in lista]
            else:
                lista = svcs.paquetes.listar_vigentes(sesion=sesion)
                respuesta = [_serializar_salida(salida) for salida in lista]
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return respuesta

    @app.post("/api/paquetes/{paquete_id}/salidas", status_code=201)
    def agregar_salida(
        paquete_id: int,
        datos: NuevaSalidaRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            salida = svcs.paquetes.agregar_salida(
                paquete_id,
                datos.fecha_salida,
                datos.fecha_regreso,
                datos.cupo_maximo,
                sesion=sesion,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return _serializar_salida(salida)

    @app.get("/api/paquetes/{paquete_id}/salidas")
    def listar_salidas(
        paquete_id: int,
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            salidas = svcs.paquetes.listar_salidas_por_paquete(
                paquete_id, sesion=sesion
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return [_serializar_salida(salida) for salida in salidas]

    @app.patch("/api/salidas/{salida_id}")
    def actualizar_salida(
        salida_id: int,
        datos: ActualizarSalidaRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            salida = svcs.paquetes.actualizar_salida(
                salida_id,
                datos.fecha_salida,
                datos.fecha_regreso,
                datos.cupo_maximo,
                sesion=sesion,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return _serializar_salida(salida)

    @app.patch("/api/paquetes/{paquete_id}/salidas/{salida_id}")
    def actualizar_salida_del_paquete(
        paquete_id: int,
        salida_id: int,
        datos: ActualizarSalidaRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            salida = svcs.salidas.buscar_por_id(salida_id)
            if not salida or salida.paquete_id != paquete_id:
                raise ValidacionError("Salida no encontrada para este paquete.")
            salida = svcs.paquetes.actualizar_salida(
                salida_id,
                datos.fecha_salida,
                datos.fecha_regreso,
                datos.cupo_maximo,
                sesion=sesion,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return _serializar_salida(salida)

    @app.patch("/api/paquetes/{paquete_id}")
    def actualizar_paquete(
        paquete_id: int,
        datos: ActualizarPaqueteRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            p = svcs.paquetes.actualizar_paquete(
                paquete_id,
                nombre=datos.nombre,
                fecha_salida=datos.fecha_salida,
                fecha_regreso=datos.fecha_regreso,
                cupo_maximo=datos.cupo_maximo,
                margen_operacion=datos.margen_operacion,
                sesion=sesion,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return _serializar_paquete(p)

    @app.post("/api/paquetes", status_code=201)
    def crear_paquete(
        datos: PaqueteRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            p = svcs.paquetes.crear_paquete(
                datos.nombre,
                datos.destinos,
                datos.fecha_salida,
                datos.fecha_regreso,
                datos.cupo_maximo,
                margen_operacion=datos.margen_operacion,
                sesion=sesion,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return {"nombre": p.nombre, "precio_por_persona": int(p.precio_por_persona)}

    # --- reservas -------------------------------------------------------- #

    @app.get("/api/reservas")
    def listar_reservas(
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            if sesion.rol == "ADMIN":
                lista = svcs.reservas.listar_reservas(sesion=sesion)
            else:
                lista = svcs.reservas.reservas_cliente(sesion)
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return [
            {
                "id": r.id,
                "paquete": r.paquete.nombre,
                "cantidad_personas": r.cantidad_personas,
                "total": int(r.total),
                "estado": r.estado,
                "fecha_emision": r.fecha_emision.isoformat(),
            }
            for r in lista
        ]

    @app.post("/api/reservas", status_code=201)
    def crear_reserva(
        datos: ReservaRequest,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            r = svcs.reservas.crear_reserva(
                sesion, None, datos.cantidad_personas,
                salida_id=datos.salida_id,
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return {"id": r.id, "total": int(r.total)}

    @app.post("/api/recuperar-contrasena")
    def recuperar_contrasena(
        datos: RecuperarContrasenaRequest,
        _: None = Depends(_verificar_csrf),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            svcs.autenticacion.recuperar_contrasena(
                datos.correo, datos.rut, datos.nueva_password
            )
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return {"mensaje": "Contraseña actualizada correctamente."}

    @app.post("/api/reservas/{reserva_id}/cancelar")
    def cancelar_reserva(
        reserva_id: int,
        _: None = Depends(_verificar_csrf),
        sesion: Sesion = Depends(_obtener_sesion),
        svcs: _Servicios = Depends(_servicios_dep),
    ):
        try:
            svcs.reservas.cancelar_reserva(sesion, reserva_id)
        except ViajesAventuraError as e:
            raise _exc_a_http(e) from e
        return {"mensaje": "Reserva cancelada."}

    # --- archivos estáticos --------------------------------------------- #

    _web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    if os.path.isdir(_web_dir):
        app.mount("/", StaticFiles(directory=_web_dir, html=True), name="web")

    return app


app = crear_app()
