""" IMPLEMENTACION DEL SERVICIO DE PAQUETES """

from modelo.paquete import Paquete
from excepciones import ValidacionError
 
 
class PaqueteServicio:
 
def __init__(
self,
paquete_repo,
destino_repo
):
self.__paquete_repo = paquete_repo
self.__destino_repo = destino_repo
 
def crear_paquete(
self,
nombre,
nombres_destinos,
fecha_salida,
fecha_regreso,
cupo_maximo
):
 
destinos = []
 
for nombre_destino in nombres_destinos:
 
destino = (
self.__destino_repo
.buscar_por_nombre(nombre_destino)
)
 
if not destino:
raise ValidacionError(
f"Destino no encontrado: "
f"{nombre_destino}"
)
 
destinos.append(destino)
 
paquete = Paquete(
nombre,
destinos,
fecha_salida,
fecha_regreso,
cupo_maximo
)
 
self.__paquete_repo.agregar(paquete)
 
return paquete
 
def listar_paquetes(self):
return self.__paquete_repo.listar()
 
def listar_vigentes(self):
return self.__paquete_repo.paquetes_vigentes()
 
def buscar_paquete(self, nombre):
return self.__paquete_repo.buscar_por_nombre(nombre)
 
def eliminar_paquete(self, nombre):
return self.__paquete_repo.eliminar(nombre)