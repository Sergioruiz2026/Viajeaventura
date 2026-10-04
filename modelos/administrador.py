"""Administrador concreto de la jerarquia de usuarios."""

from modelos.usuario import Usuario


class Administrador(Usuario):
    def __init__(
        self, usuario, password_hash="", usuario_id=None, nombre=None
    ):
        super().__init__(
            nombre or "Administrador", usuario, password_hash, usuario_id
        )

    @property
    def usuario(self):
        return self.correo

    @property
    def rol(self):
        return "ADMIN"

    def puede_reservar(self):
        return False

    @property
    def rut(self):
        return ""

    @property
    def telefono(self):
        return ""

    def __str__(self):
        return f"Administrador: {self.usuario}"