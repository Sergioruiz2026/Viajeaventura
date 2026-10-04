"""Normalización ortográfica para nombres, lugares y descripciones."""

# Artículos, preposiciones y conjunciones que van en minúscula en posición
# no inicial dentro de un título en español.
_MINUSCULAS = frozenset({
    'a', 'al', 'ante', 'con', 'de', 'del', 'desde', 'durante', 'e',
    'el', 'en', 'entre', 'la', 'las', 'lo', 'los', 'ni', 'o', 'para',
    'pero', 'por', 'que', 'se', 'sin', 'sobre', 'u', 'un', 'una', 'y',
})


def capitalizar_titulo(texto: str) -> str:
    """Primera letra de cada palabra en mayúscula; artículos y preposiciones
    intermedios permanecen en minúscula (estilo título en español)."""
    if not isinstance(texto, str):
        return texto
    palabras = texto.strip().split()
    resultado = []
    for i, p in enumerate(palabras):
        pl = p.lower()
        resultado.append(pl.capitalize() if (i == 0 or pl not in _MINUSCULAS) else pl)
    return ' '.join(resultado)


def capitalizar_oracion(texto: str) -> str:
    """Solo la primera letra del texto en mayúscula; el resto no se modifica."""
    if not isinstance(texto, str):
        return texto
    texto = texto.strip()
    return (texto[0].upper() + texto[1:]) if texto else texto
