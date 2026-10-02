
# ViajesAventura

Aplicación de consola para administrar destinos, paquetes, clientes y reservas.

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

## Ejecución

En PowerShell, configura las credenciales del administrador para la sesión actual y ejecuta la aplicación:

```powershell
$env:VIAJES_ADMIN_USUARIO = "admin"
$env:VIAJES_ADMIN_PASSWORD = "define-una-clave-segura"
python main.py
```

Los destinos, paquetes, clientes y reservas se almacenan en memoria y se pierden al cerrar la aplicación.
Los destinos, paquetes, clientes y reservas se almacenan en SQLite, en `viajes_aventura.db` en la raíz del proyecto. El archivo se crea automáticamente al iniciar la aplicación y conserva los datos entre ejecuciones.

Para usar otra ruta de base de datos, define `VIAJES_DB_PATH` antes de iniciar:

```powershell
$env:VIAJES_DB_PATH = "C:\datos\viajes_aventura.db"
python main.py
```
