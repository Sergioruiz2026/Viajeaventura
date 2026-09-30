"""creacion de excepciones personalizadas para el proyecto ViajesAventura"""


class ViajesAventuraError(Exception):
pass
 
class ValidacionError(ViajesAventuraError):
pass
 
class DestinoDuplicadoError(ViajesAventuraError):
pass
 
class CorreoDuplicadoError(ViajesAventuraError):
pass
 
class CupoInsuficienteError(ViajesAventuraError):
pass
 
class ReservaNoPermitidaError(ViajesAventuraError):
pass
 
class AutenticacionError(ViajesAventuraError):
pass 
