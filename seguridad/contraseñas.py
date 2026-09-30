""""implementación de la clase GestorContrasenas para generar y verificar hashes de contraseñas. generando la 
seguridad de las contraseñas de los clientes y administradores del proyecto ViajesAventura"""


import hashlib
 
 
class GestorContrasenas:
 
@staticmethod
def generar_hash(password):
"""
Genera el hash SHA-256 de una contraseña.
"""
return hashlib.sha256(
password.encode("utf-8")
).hexdigest()
 
@staticmethod
def verificar(password, password_hash):
"""
Verifica si la contraseña coincide
con el hash almacenado.
"""
return (
GestorContrasenas.generar_hash(password)
== password_hash
)