# Agente local Gemini: Viajes Aventura

## Rol y alcance

- Trabaja como agente de programación local de este repositorio usando Gemini CLI y los archivos del workspace.
- Antes de cada tarea, lee `README.md`, `caso_viajes_aventura.md`, `informe_viajes_aventura.md` y el código relacionado que sea pertinente.
- Analiza `main.py` como punto de entrada existente. No lo renombres ni reemplaces su contenido sin una necesidad justificada por la solicitud.
- Implementa directamente los cambios solicitados en los archivos del workspace; no te limites a proponerlos.
- Si la solicitud no define el comportamiento que se debe implementar, no inventes requisitos: explica qué falta y pregunta antes de realizar cambios funcionales.
- Mantén los cambios pequeños, coherentes con el diseño orientado a objetos y las reglas de negocio documentadas. Prioriza seguridad, validación e invariantes del modelo.
- Ejecuta validaciones adecuadas para los archivos modificados e informa con precisión qué se ejecutó y su resultado.

## Uso de herramientas y privacidad

- No delegues generación, análisis ni edición de código a GitHub Copilot u otro agente de Copilot. Gemini CLI es el agente de este repositorio.
- No uses GitHub para guardar, sincronizar, publicar o revisar cambios. No crees commits, ramas o pull requests ni subas archivos, salvo autorización explícita.
- No inventes archivos, dependencias, resultados de pruebas ni capacidades locales. No registres secretos ni datos personales sensibles.
- Conserva cambios preexistentes del usuario y limita cada tarea a su alcance.

## Registro obligatorio

Después de cada solicitud atendida, añade una entrada al final de `changelog.md` en orden cronológico inverso, con la fecha local y exactamente esta estructura:

```markdown
### AAAA-MM-DD

- **Prompt:** Descripción o transcripción de la solicitud del usuario.
- **Respuesta y acciones:** Resumen de la respuesta y de los cambios realizados.
- **Archivos modificados:** Lista de archivos creados o editados, o `Ninguno`.
- **Validaciones:** Pruebas o comprobaciones ejecutadas, o `Ninguna`.
```

Usa el ancla en minúsculas correspondiente a la fecha de la entrada. Actualiza la lista de archivos y validaciones con los resultados reales de cada tarea.
