# Trazabilidad de la rúbrica

## Modelo orientado a objetos

- `modelos/usuario.py`: abstracción `Usuario`.
- `modelos/cliente.py`: especialización cliente y permiso de reserva.
- `modelos/administrador.py`: especialización administrador sin permiso de reserva.
- `modelos/destino.py`, `modelos/paquete.py` y `modelos/reserva.py`: entidades de dominio encapsuladas.
- `tests/test_rubrica.py`: verifica herencia y polimorfismo de permisos.

## Persistencia y reglas

- `repositorios/db_setup.py`: SQLite, claves foráneas, `CHECK`, `UNIQUE`, índices y transacciones.
- `repositorios/destino_repositorio.py`: alta, consulta, modificación y eliminación/desactivación.
- `repositorios/paquete_repositorio.py`: alta, consulta y precio publicado congelado.
- `repositorios/reserva_repositorio.py`: reserva transaccional, cupos, historial y cancelación.
- `servicios/`: validación y reglas de negocio fuera de la interfaz.

## Seguridad

- `seguridad/seguridad.py`: Argon2id para contraseñas y Fernet para RUT/teléfono.
- `seguridad/validadores.py`: política de contraseña de 10 a 128 caracteres y validadores de entrada.
- `servicios/autenticacion_servicio.py`: hash señuelo, bloqueo temporal y sesión autenticada.
- `api.py`: mensajes HTTP controlados y logging de errores internos sin exponer datos sensibles.

## Interfaz web

- `web/index.html`: registro, login, recuperación, paquetes, reservas, cancelación,
  destinos, precio previo, cupos, salidas y desactivación.
- Las respuestas `401` devuelven al usuario a la pantalla de inicio de sesión.

## Verificación ejecutable

El comando `py -3 -m pytest -q` ejecuta la suite completa. La suite cubre reglas
R1-R17, persistencia, seguridad, concurrencia, autenticación y la jerarquía UML.
El informe PDF original debe regenerarse si se desea que su texto refleje el
número actual de pruebas y la incorporación posterior de la interfaz web.