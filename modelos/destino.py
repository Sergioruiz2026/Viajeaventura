""" creacion de la clase Destino para el proyecto ViajesAventura """

from excepciones import ValidacionError
from seguridad.montos import redondear_clp


class Destino:
    def __init__(self, nombre, zona, descripcion, duracion_dias, costo_base):
        datos = self.__validar_datos(
            nombre, zona, descripcion, duracion_dias, costo_base
        )
        self.__nombre, self.__zona, self.__descripcion = datos[:3]
        self.__duracion_dias, self.__costo_base = datos[3:]
        self.__disponible = True

    @staticmethod
    def __validar_datos(nombre, zona, descripcion, duracion_dias, costo_base):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValidacionError("El nombre del destino es obligatorio.")
        if not isinstance(zona, str) or not zona.strip():
            raise ValidacionError("La zona del destino es obligatoria.")
        if not isinstance(descripcion, str) or not descripcion.strip():
            raise ValidacionError("La descripción del destino es obligatoria.")
        if isinstance(duracion_dias, bool) or not isinstance(duracion_dias, int):
            raise ValidacionError("La duración debe ser un número entero.")
        if duracion_dias <= 0:
            raise ValidacionError("La duración debe ser mayor que cero.")
        try:
            costo_base = redondear_clp(costo_base)
        except (TypeError, ValueError, ArithmeticError) as error:
            raise ValidacionError("El costo base debe ser un monto válido.") from error
        if not costo_base.is_finite() or costo_base <= 0:
            raise ValidacionError("El costo base debe ser mayor que cero.")
        return nombre.strip(), zona.strip(), descripcion.strip(), duracion_dias, costo_base

    @property
    def nombre(self):
        return self.__nombre

    @property
    def zona(self):
        return self.__zona

    @property
    def descripcion(self):
        return self.__descripcion

    @property
    def duracion_dias(self):
        return self.__duracion_dias

    @property
    def costo_base(self):
        return self.__costo_base

    @property
    def disponible(self):
        return self.__disponible

    def actualizar_costo(self, nuevo_costo):
        self.actualizar_datos(
            self.__nombre,
            self.__zona,
            self.__descripcion,
            self.__duracion_dias,
            nuevo_costo
        )

    def actualizar_datos(
        self, nombre, zona, descripcion, duracion_dias, costo_base
    ):
        datos = self.__validar_datos(
            nombre, zona, descripcion, duracion_dias, costo_base
        )
        self.__nombre, self.__zona, self.__descripcion = datos[:3]
        self.__duracion_dias, self.__costo_base = datos[3:]

    def marcar_no_disponible(self):
        self.__disponible = False

    def __str__(self):
        estado = "Disponible" if self.__disponible else "No disponible"
        return (
            f"{self.__nombre} | {self.__zona} | "
            f"${self.__costo_base:,.0f} | {estado}"
        )