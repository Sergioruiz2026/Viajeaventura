from seguridad.usuarios_demo import (
    USUARIO_DEMO_CLIENTE,
    asegurar_usuarios_demo,
)
from seguridad.validadores import Validador


class RepositorioDemo:
    def __init__(self, ruts_existentes):
        self.ruts_existentes = set(ruts_existentes)
        self.usuarios = {}
        self.administradores = []

    def buscar_por_correo(self, correo):
        return self.usuarios.get(correo)

    def buscar_por_rut(self, rut):
        return rut if rut in self.ruts_existentes else None

    def agregar(self, administrador):
        self.administradores.append(administrador)


class AutenticacionDemo:
    def __init__(self, repositorio):
        self.repositorio = repositorio
        self.registros = []

    def registrar_cliente(self, nombre, rut, correo, telefono, password):
        Validador.validar_rut(rut)
        if self.repositorio.buscar_por_rut(rut):
            raise AssertionError("Se intentó registrar un RUT existente.")
        self.repositorio.ruts_existentes.add(rut)
        self.repositorio.usuarios[correo] = object()
        self.registros.append((nombre, rut, correo, telefono, password))


def test_cuenta_demo_usa_otro_rut_valido_si_el_fijo_ya_existe(monkeypatch):
    monkeypatch.setenv("VIAJES_DEMO_USUARIOS", "1")
    repositorio = RepositorioDemo({"12.345.678-5"})
    autenticacion = AutenticacionDemo(repositorio)

    asegurar_usuarios_demo(repositorio, autenticacion)

    assert len(autenticacion.registros) == 1
    assert autenticacion.registros[0][2] == USUARIO_DEMO_CLIENTE
    assert autenticacion.registros[0][1] != "12.345.678-5"
    Validador.validar_rut(autenticacion.registros[0][1])


def test_cuenta_demo_conserva_el_rut_original_si_esta_disponible(monkeypatch):
    monkeypatch.setenv("VIAJES_DEMO_USUARIOS", "1")
    repositorio = RepositorioDemo(set())
    autenticacion = AutenticacionDemo(repositorio)

    asegurar_usuarios_demo(repositorio, autenticacion)

    assert autenticacion.registros[0][1] == "12.345.678-5"


def test_cuentas_demo_no_se_crean_por_defecto(monkeypatch):
    monkeypatch.delenv("VIAJES_DEMO_USUARIOS", raising=False)
    repositorio = RepositorioDemo(set())
    autenticacion = AutenticacionDemo(repositorio)

    asegurar_usuarios_demo(repositorio, autenticacion)

    assert autenticacion.registros == []
    assert repositorio.administradores == []
