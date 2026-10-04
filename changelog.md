# CHANGELOG

## [2026-10-03]

### Revisión y corrección de scripts para compilación óptima
**Prompt:** _"En base a pdf Viaje_aventura revisar el scripts creado y si se necesita algún ajuste realizarlo para que quede en óptimas condiciones de compilación"_

Archivos corregidos:
- **`excepciones.py`** — Indentación con tabs (`\t`) reemplazada por espacios (PEP 8).
- **`repositorios/paquete_repositorio.py`** — Importación duplicada de `PaqueteDuplicadoError` eliminada.
- **`modelos/administrador.py`** — Docstring corregido: `""""` → `"""`.
- **`modelos/cliente.py`** — Docstring corregido: `""""` → `"""`.
- **`modelos/reserva.py`** — Docstring corregido: `""""` → `"""`.
- **`servicios/autenticacion_servicio.py`** — Docstring corregido: `""""` → `"""`.
- **`servicios/catalogo_servicio.py`** — Docstring corregido: `""""` → `"""`.
- **`seguridad/validadores.py`** — Docstring corregido: `""""` → `"""`.
- **`repositorios/reserva_repositorio.py`** — Typo en docstring corregido: `"cracion"` → `"creacion"`.

Resultado: 44/44 tests pasan sin regresiones.

---

### Consulta de usuarios registrados
**Prompt:** _"Muéstrame los usuarios ya creados y administradores"_

Se consultó directamente `app.db` y se listaron los 4 usuarios existentes:

| ID | Rol     | Nombre        | Correo / Usuario      |
|----|---------|---------------|-----------------------|
| 1  | CLIENTE | Sergio Ruiz   | ruiz.2006@hotmail.com |
| 2  | CLIENTE | Loreto        | loreto@gmail.com      |
| 3  | ADMIN   | Administrador | admin                 |
| 4  | ADMIN   | Administrador | SergioR               |

---

### Documentación de usuarios en README
**Prompt:** _"Dejemos estos usuarios y admin en readme"_

Se agregó la sección **Usuarios registrados en app.db** al final de `README.md` con la tabla de usuarios activos.

---

## [2026-10-04]

### Registro de prompts en CHANGELOG
**Prompt:** _"Regista los prompt realizados a changelog.md"_

Creación de este archivo `CHANGELOG.md` con el historial de prompts y cambios de la sesión.

---

### Interfaz web + extensión de API REST
**Prompt:** _"Lee solo api.py, servicios/ y modelos/sesion.py [...] Tarea: agregar una interfaz web al proyecto, reutilizando los servicios actuales sin cambiar su lógica."_

Archivos creados/modificados:
- **`api.py`** — Extendido con 9 endpoints bajo `/api`:
  - `POST /api/login` — autentica, emite cookie HttpOnly SameSite=Strict, guarda sesión en memoria.
  - `POST /api/logout` — invalida token y borra cookie.
  - `GET  /api/yo` — devuelve nombre y rol de la sesión activa.
  - `GET  /api/destinos` / `POST /api/destinos` — listado y creación (solo ADMIN).
  - `GET  /api/paquetes` / `POST /api/paquetes` — listado y creación; admin ve todos, cliente solo vigentes.
  - `GET  /api/reservas` / `POST /api/reservas` — listado y creación según rol.
  - `POST /api/reservas/{id}/cancelar` — cancela reserva propia.
  - Protección CSRF: `_verificar_csrf` exige `X-Requested-With: XMLHttpRequest` en todos los POST.
  - Mapeo de excepciones → HTTP: 401 Auth, 403 Autorización, 409 Duplicado/Cupo, 422 Validación.
  - Servicio de archivos estáticos montado en `/` desde `web/` (html=True).
  - Compatibilidad mantenida con tests existentes de `/clientes/registro`.
- **`web/index.html`** — SPA de un solo archivo (HTML + CSS + JS puro):
  - Vista de autenticación con tabs login / registro.
  - Vista cliente: paquetes disponibles con botón "Reservar" (form inline) + mis reservas con "Cancelar".
  - Vista admin con tabs Destinos / Paquetes / Reservas + formularios de creación.
  - Nunca usa `innerHTML`; todo el DOM se construye con `createElement` y `textContent`.
  - Todos los POST envían `X-Requested-With: XMLHttpRequest`.

Resultado: 44/44 tests pasan sin regresiones.
