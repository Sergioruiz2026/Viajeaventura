""""implementacion de la clase reserva para el proyecto ViajesAventura"""
 
from datetime import datetime
 
from excepciones import ValidacionError
 
 
class Reserva:
 
def __init__(
self,
cliente,
paquete,
cantidad_personas
):
 
if cantidad_personas < 1:
raise ValidacionError(
"Debe reservar al menos una persona."
)
 
self.__cliente = cliente
self.__paquete = paquete
self.__cantidad_personas = cantidad_personas
 
self.__fecha_emision = datetime.now()
 
self.__total = (
paquete.precio_por_persona
* cantidad_personas
)
 
@property
def cliente(self):
return self.__cliente
 
@property
def paquete(self):
return self.__paquete
 
@property
def cantidad_personas(self):
return self.__cantidad_personas
 
@property
def total(self):
return self.__total
 
@property
def fecha_emision(self):
return self.__fecha_emision
 
def __str__(self):
return (
f"Reserva de {self.__cliente.nombre} "
f"- Total: ${self.__total:,.0f}"
)