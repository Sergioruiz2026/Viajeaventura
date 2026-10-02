"""" IMPLEMENTACION DEL CATALOGO DE SERVICIOS """


from modelos.destino import Destino
from excepciones import ValidacionError


class CatalogoServicio:

    def __init__(self, destino_repo):
        self.__destino_repo = destino_repo

    def registrar_destino(
        self,
        nombre,
        zona,
        descripcion,
        duracion_dias,
        costo_base
    ):

        destino = Destino(
            nombre,
            zona,
            descripcion,
            duracion_dias,
            costo_base
        )

        self.__destino_repo.agregar(destino)

        return destino

    def listar_destinos(self):
        return self.__destino_repo.listar()

    def buscar_destino(self, nombre):
        return self.__destino_repo.buscar_por_nombre(nombre)

    def modificar_destino(
        self,
        nombre_actual,
        nombre,
        zona,
        descripcion,
        duracion_dias,
        costo_base
    ):
        destino = self.__destino_repo.buscar_por_nombre(nombre_actual)
        if destino is None:
            raise ValidacionError("El destino no existe.")
        destino.actualizar_datos(
            nombre, zona, descripcion, duracion_dias, costo_base
        )
        if not self.__destino_repo.actualizar(nombre_actual, destino):
            raise ValidacionError("No se pudo actualizar el destino.")
        return destino

    def eliminar_destino(self, nombre):
        return self.__destino_repo.eliminar(nombre)