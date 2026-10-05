
# ViajesAventura

Aplicación de consola y web para administrar destinos, paquetes, clientes y reservas.

## Requisitos

- Python 3.10 o posterior
- Dependencias: `python -m pip install -r requirements.txt`

## Configuración de seguridad

Las contraseñas se almacenan con Argon2id. RUT y teléfono se cifran con
Fernet; configura una clave estable y mantenla fuera del repositorio. En
PowerShell, genera una clave una sola vez y guárdala de forma segura:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$env:VIAJES_FERNET_KEY = "clave-generada"
```

La clave debe conservarse entre ejecuciones y respaldarse por separado de la
base de datos. Si se pierde o cambia, los datos cifrados existentes no podrán
descifrarse. Los eventos de logging se escriben en `app.log` y el filtro
enmascara RUT, teléfonos y valores asociados a etiquetas de credenciales.
Si la variable no está definida o contiene una clave inválida, la consola
mostrará un error de configuración y no intentará registrar datos sensibles.
En Windows, la aplicación también recupera la variable de usuario si la
terminal actual no la heredó; una clave nueva puede requerir reiniciar la
aplicación.

## Ejecución

En PowerShell, configura las credenciales del administrador para la sesión actual y ejecuta la aplicación:

```powershell
$env:VIAJES_FERNET_KEY = "clave-generada"
$env:VIAJES_ADMIN_USUARIO = "admin"
$env:VIAJES_ADMIN_PASSWORD = "define-una-clave-segura"
python main.py
```

Las variables `VIAJES_ADMIN_USUARIO` y `VIAJES_ADMIN_PASSWORD` solo se usan
para crear el primer administrador cuando la base no contiene ninguno.
Después, las credenciales se administran desde `6. Administrar usuarios`
dentro del menú ADMIN y quedan guardadas en `app.db`.

Los destinos, paquetes, clientes y reservas se almacenan en SQLite, en `app.db` en la raíz del proyecto. El archivo se crea automáticamente al iniciar la aplicación y conserva los datos entre ejecuciones.
Al iniciar, la aplicación incorpora automáticamente los seis destinos de
referencia del caso si todavía no existen. Los paquetes se crean desde el
menú ADMIN, donde se deben definir sus fechas y cupo.
También se solicita el margen de operación como porcentaje; si se deja vacío,
se aplica el valor predeterminado de 20 %.

## Autenticación compartida entre equipos

El registro y el login se procesan en el backend. El correo/usuario, el rol y
el hash Argon2id de la contraseña se guardan en la base SQLite del servidor;
el navegador no guarda usuarios, contraseñas ni roles. La cookie `session`
solo contiene un token opaco `HttpOnly`, y el servidor guarda únicamente su
hash junto al usuario y la última actividad. La sesión se renueva mientras se
usa y vence tras 30 minutos de inactividad; logout la invalida en la base.

Para que distintos PCs compartan cuentas, **todos deben abrir la misma
instancia del backend** y, por tanto, la misma base de datos del equipo
servidor. No inicies una copia independiente de `main.py` en cada PC: cada
copia local tendría su propio `app.db` y sus propios usuarios. El archivo
SQLite debe permanecer en el disco local del servidor; no lo compartas como
archivo por una carpeta de red ni lo copies a cada equipo.

Un paquete puede tener varias salidas. Al agregar una nueva fecha desde la
interfaz web, la salida anterior se conserva con sus propias fechas y cupo;
cada salida mantiene sus reservas y disponibilidad de forma independiente.
En el panel ADMIN, todas las salidas se muestran como filas independientes.

## API de registro

Inicia la API con `python -m uvicorn api:app --reload`. El registro está disponible en `POST /clientes/registro` y recibe un JSON con `nombre`, `rut`, `email`, `telefono` y `password`. Responde con HTTP 201 al registrar, HTTP 409 si el correo ya existe y HTTP 422 ante datos inválidos. La respuesta no incluye RUT, teléfono ni contraseña.

```json
{
	"nombre": "Ana Pérez",
	"rut": "12.345.678-5",
	"email": "ana@example.com",
	"telefono": "+56912345678",
	"password": "<definida-localmente>"
}
```

Para usar otra ruta de base de datos, define `VIAJES_DB_PATH` antes de iniciar:

```powershell
$env:VIAJES_DB_PATH = "C:\datos\viajes_aventura.db"
python main.py
```

## Usuarios

Cada instalación crea su administrador inicial con las variables
`VIAJES_ADMIN_USUARIO` y `VIAJES_ADMIN_PASSWORD`, y los clientes se registran
desde la aplicación. Las cuentas de demostración no se crean por defecto. Para
habilitarlas únicamente en una instalación local de prueba, define
`VIAJES_DEMO_USUARIOS=1` antes de iniciar; se crearán y podrán usar estas
cuentas:

| Rol | Nombre | Usuario de acceso | Contraseña |
|---|---|---|---|
| Cliente | Cliente Demo | `cliente.demo@viajeaventura.local` | `ClienteDemo1!` |
| Administrador | Administrador Demo | `admin-demo` | `AdminDemo1!` |

El cliente inicia sesión usando su correo y el administrador usando su
usuario. Estas credenciales son únicamente para pruebas locales; cámbielas o
elimínelas antes de usar datos reales. Si se utiliza otra base con
`VIAJES_DB_PATH`, se crearán allí si se habilitan las cuentas demo.
La creación automática solo se habilita con
`$env:VIAJES_DEMO_USUARIOS = "1"`.
Desactivar la creación no elimina cuentas demo que ya existan en una base:
el login con esos nombres queda bloqueado mientras la opción esté desactivada.
Antes de exponer una base existente, cambia o elimina esas credenciales desde
una sesión ADMIN.

En un equipo nuevo, después de clonar el repositorio, ejecuta:

```powershell
$env:VIAJES_FERNET_KEY = "genera-y-conserva-una-clave-local"
python main.py
```

La clave Fernet es obligatoria porque el registro del cliente cifra su RUT y
teléfono. No se debe subir esa clave a GitHub.

### Acceso desde otro PC de la misma red

Por defecto, la aplicación escucha solo en el equipo local (`127.0.0.1`).
Ese valor es adecuado para desarrollo local, pero no acepta conexiones desde
otros equipos. Para compartir la misma cuenta/base de datos, inicia **una sola
instancia** en el PC servidor, en todas las interfaces:

```powershell
$env:VIAJES_FERNET_KEY = "clave-estable-del-servidor"
$env:VIAJES_DEMO_USUARIOS = "0"
$env:VIAJES_COOKIE_SECURE = "0"
python main.py --web --host 0.0.0.0 --puerto 8000
```

También puedes iniciar Uvicorn directamente:

```powershell
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

En el PC servidor, consulta su dirección IPv4:

```powershell
ipconfig
```

Desde el otro PC abre `http://IP_DEL_SERVIDOR:8000/`, por ejemplo
`http://192.168.1.25:8000/`. Ambos equipos deben estar en la misma red.
Cada PC cliente debe abrir esa dirección en el navegador, registrarse o
iniciar sesión ahí; no debe ejecutar una copia local. La interfaz usa rutas
relativas (`/api/...`), así que navegador y API comparten origen y no requieren
configuración CORS adicional. `localhost` y `127.0.0.1` desde el PC cliente
apuntan al propio cliente, no al servidor.
Si Windows Firewall solicita permiso, permite Python/Uvicorn en redes
privadas. Si el puerto sigue bloqueado, crea una regla como administrador:

```powershell
New-NetFirewallRule -DisplayName "Viajes Aventura 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

No uses `http://127.0.0.1:8000/` desde el segundo PC: esa dirección siempre
apunta al propio segundo PC. El proceso anterior debe detenerse y reiniciarse
con `--host 0.0.0.0`; cambiar solo la URL del navegador no modifica dónde
escucha el servidor.

Para que equipos fuera de la red local accedan desde cualquier lugar, hace
falta desplegar el backend en un servidor accesible por Internet y configurar
DNS, firewall y HTTPS. No basta con cambiar `localhost` por una URL en el
frontend. Cuando el sitio se sirva por HTTPS, configura
`VIAJES_COOKIE_SECURE=1` en el backend; en desarrollo HTTP local/LAN déjalo en
`0`. Mantén `VIAJES_FERNET_KEY` estable en el servidor y restringida a ese
backend.

Los administradores se autentican con su nombre de usuario y los clientes con
su correo.

## Verificación de la rúbrica

La implementación mantiene la jerarquía `Usuario` abstracta con las clases
concretas `Cliente` y `Administrador`. La persistencia usa SQLite y los
servicios aplican las reglas de destinos, paquetes, reservas y seguridad.

Para ejecutar todas las pruebas:

```powershell
py -3 -m pytest -q
```

La interfaz web se inicia con:

```powershell
py -3 -m uvicorn api:app --reload
```

Luego se abre `http://127.0.0.1:8000/`. El administrador inicial se crea con
`VIAJES_ADMIN_USUARIO` y `VIAJES_ADMIN_PASSWORD`; los seis destinos de
demostración se cargan al iniciar `main.py`.

La trazabilidad entre requisitos, código y pruebas se encuentra en
`trazabilidad_rubrica.md`.
