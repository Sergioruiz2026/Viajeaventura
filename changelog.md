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

---

### Ejecución del servidor web
**Prompt:** _"ejecuta index"_

Se levantó el servidor FastAPI con uvicorn en `http://127.0.0.1:8000 --reload`. Verificación: `GET /` → HTTP 200, `GET /api/yo` → HTTP 401 (correcto sin sesión).

---

### Recuperación de contraseña, toggle mostrar/ocultar y login limpio al cerrar sesión
**Prompt:** _"creemos en la inicializacion de la web una recuperacion de contraseña por si al cliente se le olvida y otra al colacar la contraseña dar la opcion de ver o no esta y una vez que pueda entrar al sistema con los datos y quiera salir la seccion del login aparesca refrescado no mostrando en memoria la ultima coneccion"_

Archivos modificados:
- **`servicios/autenticacion_servicio.py`** — Nuevo método `recuperar_contrasena(correo, rut, nueva_password)`: verifica identidad por correo + RUT, rechaza admins, actualiza hash.
- **`api.py`** — Modelo `RecuperarContrasenaRequest` · endpoint `POST /api/recuperar-contrasena`.
- **`web/index.html`** — Tres mejoras:
  1. Tercera pestaña "Recuperar contraseña" con formulario (correo + RUT + nueva contraseña).
  2. Botón Mostrar/Ocultar en todos los campos de contraseña (login, registro, recuperar).
  3. `resetFormularioAuth()` al cerrar sesión: vacía campos, restaura toggles, limpia alertas y activa pestaña "Iniciar sesión".

Resultado: 44/44 tests pasan sin regresiones.

---

### Normalización ortográfica de nombres y lugares
**Prompt:** _"cuando se solicita alguna informacion de ingreso de datos, paquetes, reservas o informacion importante aunque esta se escriba con minulscula al aparecer en pantalla se muestre con mayuscula la primera palabra y todo los que sea nombres paises ciudades etc siempre deben ser con mayuscula las primera letra para mantener un orden ortografico"_

Archivos creados/modificados:
- **`seguridad/normalizador.py`** — Nuevo módulo con `capitalizar_titulo()` y `capitalizar_oracion()`.
- **`servicios/autenticacion_servicio.py`** — Normaliza nombre del cliente al registrar.
- **`servicios/catalogo_servicio.py`** — Normaliza nombre y zona (título) y descripcion (oración) al registrar destino.
- **`servicios/paquete_servicio.py`** — Normaliza nombre del paquete al crear.
- **`web/index.html`** — Funciones `fTitulo()` y `fOracion()` en todas las celdas con nombres, zonas, paquetes y cabecera de usuario.

Resultado: 44/44 tests pasan sin regresiones.

---

## [2026-10-04]

### Edición de paquetes (cupo y fechas)
**Prompt:** _"Al crear un paquete no hay ninguna opcion de modificar este, por ejemplo se agotaron las reservas y si el admin quisiera aumentar la cantidad de disponibilidad no hay como hacerlo o por ejemplo si pusimos de una fecha x a una fecha y no hay como agregar sobre la misma otra disponibilidad del paquete en otras fechas"_

Archivos creados/modificados:
- **`repositorios/paquete_repositorio.py`** — Nuevo método `actualizar()`: UPDATE sobre `paquetes` por `id`.
- **`servicios/paquete_servicio.py`** — Nuevo método `actualizar_paquete()`: aplica defaults para campos no enviados, valida cupo ≥ reservas activas, recalcula precio si cambia el margen.
- **`api.py`** — Helper `_serializar_paquete()` · modelo `ActualizarPaqueteRequest` · `PATCH /api/paquetes/{id}` · listado incluye `cupo_maximo` y `margen_operacion`.
- **`web/index.html`** — Columnas Cupo máx / Disponibles · botón Editar por fila · formulario inline pre-cargado.

Resultado: 44/44 tests pasan sin regresiones.

---

### Registro de prompts en CHANGELOG
**Prompt:** _"registrar los ultimos prompts utilizados sin borrar los que estan"_

Se agregaron al `CHANGELOG.md` los 5 prompts de la sesión pendientes de registro.

---

### Rediseño del formulario de edición de paquete como "Nueva salida"
**Prompt:** _"me da la opcion de editar pero esta edicion debe ser para agregar otra fecha del mismo paquete y asi debe quedar mas limpia la iteracion"_

Cambios en `web/index.html`:
- Botón renombrado de "Editar" a **"+ Nueva salida"**.
- Función `toggleFormEditarPaquete` reemplazada por `toggleFormNuevaSalida`: formulario simplificado con solo 3 campos (fecha de salida, fecha de regreso, cupo máximo).
- Encabezado contextual: "Nueva salida para: *[nombre del paquete]*".
- Bloque de referencia que muestra la salida vigente antes de editar.
- Envía únicamente los 3 campos al `PATCH /api/paquetes/{id}`.

Resultado: 44/44 tests pasan sin regresiones.

---

### Diagnóstico y corrección de error 405 + formato de fechas
**Prompt:** _[imagen mostrando "Method Not Allowed" al guardar nueva salida]_

Causa raíz: dos procesos uvicorn corriendo simultáneamente en el puerto 8000; el proceso original (sin el endpoint PATCH) seguía atendiendo peticiones.

Acciones:
- Se terminaron ambos procesos y se relanzó uvicorn limpiamente.
- Verificación vía `netstat` y prueba directa del endpoint confirmaron el fix.

---

### Diagnóstico "no lo guarda" + formato DD/MM/YYYY + confirmación de guardado
**Prompt:** _"no os guarda ya no genera el error pero como menciono no lo guarda"_

Diagnóstico: el PATCH **sí guardaba** en la DB (fechas cambiaron de `2026-10-31→2026-11-10` a `2026-11-09→2026-11-16`). El problema era de percepción:
1. Las fechas en la tabla se mostraban en `YYYY-MM-DD` (ISO) mientras el datepicker las mostraba en `DD/MM/YYYY`.
2. No había confirmación visual de que el guardado fue exitoso.

Cambios en `web/index.html`:
- Nueva función `fFecha(iso)` que convierte `YYYY-MM-DD` → `DD/MM/YYYY`.
- Aplicada en todas las columnas de fechas: paquetes (cliente y admin), reservas (ambas vistas), panel de referencia de la salida actual.
- Al guardar una nueva salida se muestra un **mensaje de confirmación verde** durante 5 segundos con las fechas y cupo efectivamente guardados (tomados de la respuesta real de la API).

Resultado: 44/44 tests pasan sin regresiones.

---

### Registro de prompts en CHANGELOG
**Prompt:** _"registra los prompts"_

Se agregaron al `CHANGELOG.md` los 4 prompts de la sesión pendientes de registro.
