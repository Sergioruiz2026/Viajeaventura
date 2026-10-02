
# ViajesAventura

Aplicación de consola para administrar destinos, paquetes, clientes y reservas.

## Requisitos

- Python 3.10 o posterior

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
