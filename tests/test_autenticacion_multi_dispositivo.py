import hashlib
import os
import secrets
import sqlite3

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from api import crear_app
from modelos.administrador import Administrador
from modelos.cliente import Cliente
from repositorios.base_datos import BaseDatos
from repositorios.cliente_repositorio import ClienteRepositorio
from seguridad.contraseñas import GestorContrasenas
from seguridad.usuarios_demo import (
    PASSWORD_DEMO_ADMIN,
    PASSWORD_DEMO_CLIENTE,
    USUARIO_DEMO_ADMIN,
    USUARIO_DEMO_CLIENTE,
)


ADMIN_EMAIL = "admin.prueba@test.com"
CLIENTE_EMAIL = "cliente.prueba@test.com"
HEADERS_CSRF = {"X-Requested-With": "XMLHttpRequest"}


def _contrasena_prueba(variable):
    return os.environ.get(variable) or f"PruebaSegura1!{secrets.token_urlsafe(8)}"


@pytest.fixture
def entorno_autenticacion(tmp_path, monkeypatch):
    ruta_db = tmp_path / "autenticacion_compartida.db"
    monkeypatch.setenv("VIAJES_DB_PATH", str(ruta_db))
    monkeypatch.setenv("VIAJES_FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("VIAJES_DEMO_USUARIOS", "0")
    monkeypatch.setenv("VIAJES_COOKIE_SECURE", "0")
    return ruta_db


def _crear_admin(ruta_db, password):
    base_datos = BaseDatos(ruta_db)
    try:
        repositorio = ClienteRepositorio(base_datos)
        repositorio.agregar(
            Administrador(
                ADMIN_EMAIL,
                GestorContrasenas.generar_hash(password),
                nombre="Administrador Prueba",
            )
        )
        repositorio.agregar(
            Administrador(
                USUARIO_DEMO_ADMIN,
                GestorContrasenas.generar_hash(PASSWORD_DEMO_ADMIN),
                nombre="Administrador Demo Existente",
            )
        )
        repositorio.agregar(
            Cliente(
                "Cliente Demo Existente",
                "11.111.111-1",
                USUARIO_DEMO_CLIENTE,
                "+56987654321",
                GestorContrasenas.generar_hash(PASSWORD_DEMO_CLIENTE),
            )
        )
    finally:
        base_datos.cerrar()


def test_registro_login_roles_sesion_y_logout_multi_dispositivo(
    entorno_autenticacion,
):
    password_admin = _contrasena_prueba(
        "VIAJES_TEST_MULTI_PC_ADMIN_PASSWORD"
    )
    password_cliente = _contrasena_prueba(
        "VIAJES_TEST_MULTI_PC_CLIENTE_PASSWORD"
    )
    _crear_admin(entorno_autenticacion, password_admin)

    # PC A registra al cliente en la base compartida del servidor.
    pc_a = TestClient(crear_app())
    registro = pc_a.post(
        "/clientes/registro",
        headers=HEADERS_CSRF,
        json={
            "nombre": "Cliente Prueba",
            "rut": "12.345.678-5",
            "email": CLIENTE_EMAIL,
            "telefono": "+56987654321",
            "password": password_cliente,
        },
    )
    assert registro.status_code == 201

    with sqlite3.connect(entorno_autenticacion) as conexion:
        fila = conexion.execute(
            "SELECT password_hash, rol FROM usuarios WHERE correo = ?",
            (CLIENTE_EMAIL,),
        ).fetchone()
    assert fila is not None
    assert fila[0].startswith("$argon2id$")
    assert fila[0] != password_cliente
    assert fila[1] == "CLIENTE"
    with sqlite3.connect(entorno_autenticacion) as conexion:
        fila_admin = conexion.execute(
            "SELECT password_hash, rol FROM usuarios WHERE correo = ?",
            (ADMIN_EMAIL,),
        ).fetchone()
    assert fila_admin is not None
    assert fila_admin[0].startswith("$argon2id$")
    assert fila_admin[0] != password_admin
    assert fila_admin[1] == "ADMIN"

    # PC B inicia sesión de forma independiente contra el mismo backend.
    pc_b = TestClient(crear_app())
    login_cliente = pc_b.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={"usuario": CLIENTE_EMAIL, "password": password_cliente},
    )
    assert login_cliente.status_code == 200
    assert login_cliente.json()["rol"] == "CLIENTE"
    cookie_cliente = pc_b.cookies.get("session")
    assert cookie_cliente
    assert "httponly" in login_cliente.headers["set-cookie"].lower()
    assert "samesite=strict" in login_cliente.headers["set-cookie"].lower()
    assert "max-age=1800" in login_cliente.headers["set-cookie"].lower()

    respuesta_sesion = pc_b.get("/api/yo")
    assert respuesta_sesion.json()["rol"] == "CLIENTE"
    assert "max-age=1800" in respuesta_sesion.headers["set-cookie"].lower()
    assert pc_b.get("/api/paquetes").status_code == 200
    assert pc_b.get("/api/reservas").status_code == 200
    assert pc_b.get("/api/destinos").status_code == 403
    acceso_admin_cliente = pc_b.post(
        "/api/destinos",
        headers=HEADERS_CSRF,
        json={
            "nombre": "No autorizado",
            "zona": "Prueba",
            "descripcion": "Prueba",
            "duracion_dias": 1,
            "costo_base": 100,
        },
    )
    assert acceso_admin_cliente.status_code == 403

    # Un navegador nuevo recupera la sesión desde la base tras recrear la app.
    navegador_reabierto = TestClient(
        crear_app(),
        cookies={"session": cookie_cliente},
    )
    assert navegador_reabierto.get("/api/yo").json()["rol"] == "CLIENTE"

    # Una contraseña incorrecta no emite cookie ni crea sesión.
    navegador_invalido = TestClient(crear_app())
    with sqlite3.connect(entorno_autenticacion) as conexion:
        sesiones_antes = conexion.execute(
            "SELECT COUNT(*) FROM sesiones"
        ).fetchone()[0]
    login_invalido = navegador_invalido.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={
            "usuario": ADMIN_EMAIL,
            "password": "ContraseñaIncorrecta123!",
        },
    )
    assert login_invalido.status_code == 401
    assert login_invalido.json()["detail"] == "Correo o contraseña incorrectos."
    assert "session" not in navegador_invalido.cookies
    assert navegador_invalido.get("/api/yo").status_code == 401
    usuario_inexistente = navegador_invalido.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={
            "usuario": "usuario.inexistente@test.com",
            "password": "Password123!",
        },
    )
    assert usuario_inexistente.status_code == 401
    assert usuario_inexistente.json()["detail"] == "Correo o contraseña incorrectos."
    assert "session" not in navegador_invalido.cookies
    assert navegador_invalido.get("/api/destinos").status_code == 401
    with sqlite3.connect(entorno_autenticacion) as conexion:
        assert conexion.execute(
            "SELECT COUNT(*) FROM sesiones"
        ).fetchone()[0] == sesiones_antes
    login_demo_bloqueado = navegador_invalido.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={
            "usuario": USUARIO_DEMO_ADMIN,
            "password": PASSWORD_DEMO_ADMIN,
        },
    )
    assert login_demo_bloqueado.status_code == 401
    assert "session" not in navegador_invalido.cookies
    login_cliente_demo_bloqueado = navegador_invalido.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={
            "usuario": USUARIO_DEMO_CLIENTE,
            "password": PASSWORD_DEMO_CLIENTE,
        },
    )
    assert login_cliente_demo_bloqueado.status_code == 401

    # ADMIN autentica contra la misma base y puede realizar una operación admin.
    pc_admin = TestClient(crear_app())
    login_admin = pc_admin.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={"usuario": ADMIN_EMAIL, "password": password_admin},
    )
    assert login_admin.status_code == 200
    assert login_admin.json()["rol"] == "ADMIN"
    assert pc_admin.get("/api/yo").json()["rol"] == "ADMIN"
    assert pc_admin.get("/api/destinos").status_code == 200
    assert pc_admin.get("/api/paquetes").status_code == 200
    assert pc_admin.get("/api/reservas").status_code == 200
    crear_destino = pc_admin.post(
        "/api/destinos",
        headers=HEADERS_CSRF,
        json={
            "nombre": "Destino Administrativo",
            "zona": "Prueba",
            "descripcion": "Destino de validación",
            "duracion_dias": 1,
            "costo_base": 100,
        },
    )
    assert crear_destino.status_code == 201

    # La base almacena solo el digest del token; logout invalida también el
    # token que conserva otro navegador.
    with sqlite3.connect(entorno_autenticacion) as conexion:
        digests = {
            fila[0]
            for fila in conexion.execute(
                "SELECT token_hash FROM sesiones"
            ).fetchall()
        }
    assert hashlib.sha256(cookie_cliente.encode()).hexdigest() in digests
    assert cookie_cliente not in digests

    logout_admin = pc_admin.post("/api/logout", headers=HEADERS_CSRF)
    assert logout_admin.status_code == 200
    assert pc_admin.get("/api/yo").status_code == 401

    logout = pc_b.post("/api/logout", headers=HEADERS_CSRF)
    assert logout.status_code == 200
    assert pc_b.get("/api/yo").status_code == 401
    assert navegador_reabierto.get("/api/yo").status_code == 401


def test_cambio_de_usuario_no_reutiliza_estado_de_sesion(
    entorno_autenticacion,
):
    password_admin = _contrasena_prueba(
        "VIAJES_TEST_MULTI_PC_ADMIN_PASSWORD"
    )
    password_cliente = _contrasena_prueba(
        "VIAJES_TEST_MULTI_PC_CLIENTE_PASSWORD"
    )
    _crear_admin(entorno_autenticacion, password_admin)
    pc_a = TestClient(crear_app())
    pc_a.post(
        "/clientes/registro",
        headers=HEADERS_CSRF,
        json={
            "nombre": "Cliente Prueba",
            "rut": "12.345.678-5",
            "email": CLIENTE_EMAIL,
            "telefono": "+56987654321",
            "password": password_cliente,
        },
    )
    navegador = TestClient(crear_app())

    for correo, password, rol in (
        (ADMIN_EMAIL, password_admin, "ADMIN"),
        (CLIENTE_EMAIL, password_cliente, "CLIENTE"),
        (CLIENTE_EMAIL, password_cliente, "CLIENTE"),
        (ADMIN_EMAIL, password_admin, "ADMIN"),
    ):
        login = navegador.post(
            "/api/login",
            headers=HEADERS_CSRF,
            json={"usuario": correo, "password": password},
        )
        assert login.status_code == 200
        assert login.json()["rol"] == rol
        assert navegador.get("/api/yo").json()["rol"] == rol

        logout = navegador.post("/api/logout", headers=HEADERS_CSRF)
        assert logout.status_code == 200
        assert navegador.get("/api/yo").status_code == 401


def test_cookie_segura_se_activa_para_https(entorno_autenticacion, monkeypatch):
    monkeypatch.setenv("VIAJES_COOKIE_SECURE", "1")
    password_admin = _contrasena_prueba(
        "VIAJES_TEST_MULTI_PC_ADMIN_PASSWORD"
    )
    _crear_admin(entorno_autenticacion, password_admin)
    cliente = TestClient(crear_app(), base_url="https://testserver")

    respuesta = cliente.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={"usuario": ADMIN_EMAIL, "password": password_admin},
    )

    assert respuesta.status_code == 200
    assert "; secure" in respuesta.headers["set-cookie"].lower()
    assert cliente.get("/api/yo").status_code == 200


def test_cookie_invalida_se_limpia_y_rutas_protegidas_rechazan_sin_sesion(
    entorno_autenticacion,
):
    cliente = TestClient(
        crear_app(),
        cookies={"session": "token-invalido"},
    )

    respuesta_yo = cliente.get("/api/yo")
    assert respuesta_yo.status_code == 401
    assert "max-age=0" in respuesta_yo.headers.get("set-cookie", "").lower()
    assert cliente.get("/api/destinos").status_code == 401


def test_sesion_expirada_se_invalida_y_limpia_cookie(
    entorno_autenticacion,
):
    password_admin = _contrasena_prueba(
        "VIAJES_TEST_MULTI_PC_ADMIN_PASSWORD"
    )
    _crear_admin(entorno_autenticacion, password_admin)
    cliente = TestClient(crear_app())
    login = cliente.post(
        "/api/login",
        headers=HEADERS_CSRF,
        json={"usuario": ADMIN_EMAIL, "password": password_admin},
    )
    assert login.status_code == 200
    assert cliente.cookies.get("session")

    with sqlite3.connect(entorno_autenticacion) as conexion:
        conexion.execute(
            "UPDATE sesiones SET ultima_actividad = '2000-01-01T00:00:00'"
        )
        conexion.commit()

    respuesta = cliente.get("/api/yo")

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Sesión expirada."
    assert "max-age=0" in respuesta.headers.get("set-cookie", "").lower()
    with sqlite3.connect(entorno_autenticacion) as conexion:
        assert conexion.execute("SELECT COUNT(*) FROM sesiones").fetchone()[0] == 0
