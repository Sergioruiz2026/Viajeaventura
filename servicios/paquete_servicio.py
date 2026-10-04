""" IMPLEMENTACION DEL SERVICIO DE PAQUETES """

from decimal import Decimal, DecimalException

from modelos.paquete import Paquete
from excepciones import ValidacionError
from seguridad.montos import a_decimal, aplicar_margen_clp
from seguridad.autorizacion import exigir_rol
from seguridad.normalizador import capitalizar_titulo
from excepciones import ValidacionError


class PaqueteServicio:

    def __init__(self, paquete_repo, destino_repo, salida_repo=None):
        self.__paquete_repo = paquete_repo
        self.__destino_repo = destino_repo
        self.__salida_repo = salida_repo

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
        nombre = capitalizar_titulo(nombre)
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
        if self.__salida_repo is not None:
            return self.__salida_repo.salidas_vigentes()
        return self.__paquete_repo.paquetes_vigentes()

    def listar_salidas_por_paquete(self, paquete_id, *, sesion):
        exigir_rol(sesion, "ADMIN")
        if self.__salida_repo is None:
            return []
        return self.__salida_repo.listar_por_paquete(paquete_id)

    def agregar_salida(
        self, paquete_id, fecha_salida, fecha_regreso, cupo_maximo, *, sesion
    ):
        exigir_rol(sesion, "ADMIN")
        if self.__salida_repo is None:
            raise ValidacionError("Repositorio de salidas no disponible.")
        if not self.__paquete_repo.buscar_por_id(paquete_id):
            raise ValidacionError("Paquete no encontrado.")
        if fecha_regreso <= fecha_salida:
            raise ValidacionError(
                "La fecha de regreso debe ser posterior a la de salida."
            )
        if cupo_maximo <= 0:
            raise ValidacionError("El cupo debe ser mayor que cero.")
        salida_id = self.__salida_repo.agregar(
            paquete_id, fecha_salida, fecha_regreso, cupo_maximo
        )
        return self.__salida_repo.buscar_por_id(salida_id)

    def actualizar_salida(
        self, salida_id, fecha_salida, fecha_regreso, cupo_maximo, *, sesion
    ):
        exigir_rol(sesion, "ADMIN")
        if self.__salida_repo is None:
            raise ValidacionError("Repositorio de salidas no disponible.")
        salida = self.__salida_repo.buscar_por_id(salida_id)
        if not salida:
            raise ValidacionError("Salida no encontrada.")
        if fecha_regreso <= fecha_salida:
            raise ValidacionError(
                "La fecha de regreso debe ser posterior a la de salida."
            )
        if cupo_maximo <= 0:
            raise ValidacionError("El cupo debe ser mayor que cero.")
        if not self.__salida_repo.actualizar(
            salida_id, fecha_salida, fecha_regreso, cupo_maximo
        ):
            raise ValidacionError(
                "El cupo no puede ser menor que las reservas activas."
            )
        return self.__salida_repo.buscar_por_id(salida_id)

    def buscar_paquete(self, nombre, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__paquete_repo.buscar_por_nombre(nombre)

    def actualizar_paquete(
        self,
        paquete_id,
        nombre=None,
        fecha_salida=None,
        fecha_regreso=None,
        cupo_maximo=None,
        margen_operacion=None,
        *,
        sesion
    ):
        exigir_rol(sesion, "ADMIN")
        paquete = self.__paquete_repo.buscar_por_id(paquete_id)
        if not paquete:
            raise ValidacionError("Paquete no encontrado.")

        nuevo_nombre = (
            capitalizar_titulo(nombre.strip())
            if isinstance(nombre, str) and nombre.strip()
            else paquete.nombre
        )
        nueva_salida  = fecha_salida  if fecha_salida  is not None else paquete.fecha_salida
        nuevo_regreso = fecha_regreso if fecha_regreso is not None else paquete.fecha_regreso
        nuevo_cupo    = cupo_maximo   if cupo_maximo   is not None else paquete.cupo_maximo

        if nuevo_regreso <= nueva_salida:
            raise ValidacionError(
                "La fecha de regreso debe ser posterior a la de salida."
            )
        if nuevo_cupo <= 0:
            raise ValidacionError("El cupo debe ser mayor que cero.")

        reservado = paquete.cupo_maximo - paquete.cupo_disponible
        if nuevo_cupo < reservado:
            raise ValidacionError(
                f"El cupo no puede quedar por debajo de las "
                f"{reservado} reservas activas."
            )

        if margen_operacion is not None:
            nuevo_margen = a_decimal(margen_operacion)
            if not nuevo_margen.is_finite() or nuevo_margen < 0:
                raise ValidacionError("El margen no puede ser negativo.")
            costo_total = sum(
                (a_decimal(d.costo_base) for d in paquete.destinos),
                start=a_decimal(0)
            )
            nuevo_precio = int(aplicar_margen_clp(costo_total, nuevo_margen))
        else:
            nuevo_margen = paquete.margen_operacion
            nuevo_precio = int(paquete.precio_por_persona)

        self.__paquete_repo.actualizar(
            paquete_id, nuevo_nombre, nueva_salida, nuevo_regreso,
            nuevo_cupo, nuevo_margen, nuevo_precio
        )
        return self.__paquete_repo.buscar_por_id(paquete_id)

    def eliminar_paquete(self, nombre, *, sesion):
        exigir_rol(sesion, "ADMIN")
        return self.__paquete_repo.eliminar(nombre)