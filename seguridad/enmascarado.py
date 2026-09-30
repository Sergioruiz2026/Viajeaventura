"""" creacion de la clase enmascarador para enmascarar datos sensibles como correo, rut y telefono""" 

class Enmascarador:
 
@staticmethod
def correo(correo):
 
usuario, dominio = correo.split("@")
 
if len(usuario) <= 2:
return "*" * len(usuario) + "@" + dominio
 
* visible = usuario[:2]
* oculto = "*" * (len(usuario) - 2)
 
return f"{visible}{oculto}@{dominio}"
 
@staticmethod
def rut(rut):
 
if len(rut) < 4:
return "***"
 
return "*" * (len(rut) - 4) + rut[-4:]
 
@staticmethod
def telefono(telefono):
 
if len(telefono) < 4:
return "***"
 
return "*" * (len(telefono) - 4) + telefono[-4:]