"""" creacion de repositorio (paquete_repositorio) para el proyecto ViajesAventura"""
 
 
class PaqueteRepositorio:
 
def __init__(self):
self.__paquetes = []
 
def agregar(self, paquete):
self.__paquetes.append(paquete)
 
def listar(self):
return self.__paquetes.copy()
 
def buscar_por_nombre(self, nombre):
 
for paquete in self.__paquetes:
if paquete.nombre.lower() == nombre.lower():
return paquete
 
return None
 
def eliminar(self, nombre):
 
paquete = self.buscar_por_nombre(nombre)
 
if paquete:
self.__paquetes.remove(paquete)
return True
 
return False
 
def paquetes_vigentes(self):
 
return [
paquete
for paquete in self.__paquetes
if not paquete.esta_vencido()
]