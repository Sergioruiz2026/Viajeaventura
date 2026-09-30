""" creacion de la clase Destino para el proyecto ViajesAventura """

from excepciones import ValidacionError
 
 
class Destino:
 
def __init__(self, nombre, zona, descripcion,
duracion_dias, costo_base):
 
if not nombre.strip():
raise ValidacionError(
"El nombre del destino es obligatorio."
)
 
if costo_base <= 0:
raise ValidacionError(
"El costo base debe ser mayor que cero."
)
 
if duracion_dias <= 0:
raise ValidacionError(
"La duración debe ser mayor que cero."
)
 
self.__nombre = nombre
self.__zona = zona
self.__descripcion = descripcion
self.__duracion_dias = duracion_dias
self.__costo_base = costo_base
self.__disponible = True
 
@property
def nombre(self):
return self.__nombre
 
@property
def costo_base(self):
return self.__costo_base
 
@property
def disponible(self):
return self.__disponible
 
def actualizar_costo(self, nuevo_costo):
 
if nuevo_costo <= 0:
raise ValidacionError(
"Costo inválido."
)
 
self.__costo_base = nuevo_costo
 
def marcar_no_disponible(self):
self.__disponible = False
 
def __str__(self):
estado = "Disponible" if self.__disponible else "No disponible"
 
return (
f"{self.__nombre} | "
f"{self.__zona} | "
f"${self.__costo_base:,.0f} | "
f"{estado}"
)