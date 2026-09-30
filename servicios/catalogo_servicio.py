"""" IMPLEMENTACION DEL CATALOGO DE SERVICIOS """

 
from modelo.destino import Destino
 
 
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
 
def eliminar_destino(self, nombre):
return self.__destino_repo.eliminar(nombre)