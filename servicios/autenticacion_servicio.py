""""CREACION DE SERVICIO DE AUTENTICACION"""

 from modelo.cliente import Cliente
 
from seguridad.validadores import (
Validador
)
 
from seguridad.contrasenas import (
GestorContrasenas
)
 
from excepciones import (
AutenticacionError
)
 
 
class AutenticacionServicio:
 
def __init__(self, cliente_repo):
self.__cliente_repo = cliente_repo
 
def registrar_cliente(
self,
nombre,
rut,
correo,
telefono,
password
):
 
Validador.validar_nombre(nombre)
Validador.validar_rut(rut)
Validador.validar_correo(correo)
Validador.validar_telefono(telefono)
Validador.validar_contrasena(password)
 
password_hash = (
GestorContrasenas
.generar_hash(password)
)
 
cliente = Cliente(
nombre,
rut,
correo,
telefono,
password_hash
)
 
self.__cliente_repo.agregar(cliente)
 
return cliente
 
def iniciar_sesion(
self,
correo,
password
):
 
cliente = (
self.__cliente_repo
.buscar_por_correo(correo)
)
 
if not cliente:
raise AutenticacionError(
"Usuario no encontrado."
)
 
valido = (
GestorContrasenas.verificar(
password,
cliente.password_hash
)
)
 
if not valido:
raise AutenticacionError(
"Contraseña incorrecta."
)
 
return cliente
