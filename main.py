from modelos.destino import Destino

destino1 = Destino(
    "Valle del Elqui",
    "Región de Coquimbo",
    "Destino turístico del Valle del Elqui",
    2,
    120000
)


print(destino1.nombre)
print(destino1.zona)
print(destino1.descripcion)
print(destino1.duracion)
print(destino1.costo_base)