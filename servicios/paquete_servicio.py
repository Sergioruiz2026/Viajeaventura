""" IMPLEMENTACION DEL SERVICIO DE PAQUETES """

from decimal import Decimal, DecimalException

from modelos.paquete import Paquete
from excepciones import ValidacionError
from seguridad.montos import a_decimal
from seguridad.autorizacion import exigir_rol


class PaqueteServicio:

    def __init__(self, paquete_repo, destino_repo):
        self.__paquete_repo = paquete_repo
        self.__destino_repo = destino_repo

    def crear_paquete(
        self,
        nombre,
        nombres_destinos=None,
        fecha_salida=None,
        fecha_regreso=None,
        cupo_maximo=None,
        margen_operacion=Decimal("0.20"),
        *,
        ids_destinos=None,
        sesion
    ):
        exigir_rol(sesion, "ADMIN")
        if ids_destinos is not None:
            if nombres_destinos is not None:
                raise ValidacionError(
                    "Indique destinos usando nombres o IDs, no ambos."
                )
            nombres_destinos = ids_destinos
        try:
            cantidad_destinos = len(nombres_destinos)
        except TypeError as error:
            raise ValidacionError("Debe seleccionar entre 2 y 5 destinos.") from error
        if cantidad_destinos < 2 or cantidad_destinos > 5:
            raise ValidacionError("El paquete debe tener entre 2 y 5 destinos.")

        try:
            margen_operacion = a_decimal(margen_operacion)
        except (TypeError, ValueError, DecimalException) as error:
            raise ValidacionError("El margen debe ser un decimal válido.") from error
        if not margen_operacion.is_finite() or margen_operacion < 0:
            raise ValidacionError("El margen no puede ser negativo.")

        destinos = []
        identidades = set()
        for seleccion in nombres_destinos:
            if isinstance(seleccion, bool):
                destino = None
            elif isinstance(seleccion, int):
                destino = self.__destino_repo.buscar_por_id(seleccion)
            else:
                destino = self.__destino_repo.buscar_por_nombre(seleccion)
            if not destino:
                raise ValidacionError(
                    f"Destino no encontrado: {seleccion}"
                )
            identidad = destino.nombre.casefold()
            if identidad in identidades:
                raise ValidacionError("No se pueden repetir destinos.")
            identidades.add(identidad)
            if not destino.disponible:
                raise ValidacionError(
                    f"El destino '{destino.nombre}' no está disponible."
                )
            destinos.append(destino)

        paquete = Paquete(
            nombre,
            destinos,
            fecha_salida,
            fecha_regreso,
            cupo_maximo,
            margen=margen_operacion
        )
        self.__paquete_repo.agregar(paquete)
        return paquete

    def listar_paquetes(self, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__paquete_repo.listar()

    def listar_vigentes(self, *, sesion):
        exigir_rol(sesion, "CLIENTE")
        return self.__paquete_repo.paquetes_vigentes()

    def buscar_paquete(self, nombre, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__paquete_repo.buscar_por_nombre(nombre)

    def eliminar_paquete(self, nombre, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__paquete_repo.eliminar(nombre)