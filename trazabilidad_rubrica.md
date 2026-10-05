# Trazabilidad de la rúbrica

Este documento vincula cada regla del caso con el código que la implementa y
la prueba automatizada que la verifica. La suite tiene 49 pruebas en 11
archivos y se ejecuta con `py -m pytest -q`.

## Reglas de negocio del caso (R1 a R17)

| Regla | Qué exige | Dónde se implementa | Prueba que la verifica |
|---|---|---|---|
| R1 | Destino con sus datos y nombre único | `modelos/destino.py`, `repositorios/destino_repositorio.py` (`UNIQUE` sin distinguir mayúsculas) | `test_destinos.py` :: `test_registro_valida_datos_y_rechaza_nombre_duplicado_sin_case` |
| R2 | Costo base mayor que cero | `Destino` (validación) y `CHECK` en la tabla `destinos` | `test_destinos.py` :: `test_registro_valida_datos_y_rechaza_nombre_duplicado_sin_case` |
| R3 | Paquete con 2 a 5 destinos, sin repetir | `modelos/paquete.py`, `PaqueteServicio.crear_paquete`, triggers de `paquete_destinos` | `test_paquetes.py` :: `test_rechaza_selecciones_invalidas_y_margen_negativo`; `test_persistencia.py` :: `test_paquete_exige_entre_dos_y_cinco_destinos` |
| R4 | Un destino puede estar en varios paquetes | Tabla intermedia `paquete_destinos` | Sin prueba dedicada |
| R5 | Regreso posterior a la salida y cupo mayor que cero | `Paquete` (validación) y `CHECK` en `paquetes` y `paquete_salidas` | `test_paquetes.py` :: `test_rechaza_selecciones_invalidas_y_margen_negativo` |
| R6 | Precio = suma de costos base más margen; margen no negativo | `Paquete`, `seguridad/montos.py` (`aplicar_margen_clp`) | `test_paquetes.py` :: `test_calcula_redondea_y_conserva_precio_publicado`; `test_seguridad.py` :: `test_montos_clp_usando_decimal_y_redondeo_half_up` |
| R7 | El precio publicado no cambia aunque cambie un costo | Columna `paquetes.precio_publicado`; `api.py` rechaza modificar el margen | `test_destinos.py` :: `test_modificar_destino_no_cambia_precio_de_paquete_publicado`; `test_paquetes.py` :: `test_calcula_redondea_y_conserva_precio_publicado` |
| R8 | Destino libre se elimina; destino en un paquete queda no disponible | `DestinoRepositorio.eliminar` | `test_destinos.py` :: `test_elimina_destino_sin_paquetes_y_desactiva_destino_asociado` |
| R9 | Registro de cliente con correo único | `AutenticacionServicio.registrar_cliente`, `seguridad/validadores.py` | `test_persistencia.py` :: `test_registro_exige_rut_mod11_y_correo_unico`; `test_api_registro.py` :: `test_responde_409_para_correo_duplicado` |
| R10 | La contraseña no se guarda tal como se escribió | `seguridad/seguridad.py` (`hash_password`, Argon2id) | `test_seguridad.py` :: `test_hash_argon2id_verifica_sin_guardar_clave` |
| R11 | Solo un cliente autenticado reserva y ve sus propias reservas | `seguridad/autorizacion.py`, `ReservaServicio`, `ReservaRepositorio.reservas_por_cliente` | `test_reservas.py` :: `test_historial_aislado_por_usuario_y_cancelacion_propia`; `test_destinos.py` :: `test_cliente_no_puede_gestionar_destinos`; `test_paquetes.py` :: `test_roles_no_pueden_invocar_operaciones_de_paquetes_ajenas` |
| R12 | La reserva registra cliente, paquete, fecha, personas y total | `modelos/reserva.py`, tabla `reservas` | `test_reservas.py` :: `test_reserva_por_id_guarda_fecha_actual_y_total_publicado` |
| R13 | Total = precio por persona por cantidad, y no cambia | `Reserva` (cálculo del total) | `test_reservas.py` :: `test_reserva_por_id_guarda_fecha_actual_y_total_publicado` |
| R14 | No se supera el cupo disponible | `ReservaRepositorio.agregar` (transacción) y triggers de cupo | `test_reservas.py` :: `test_cupo_se_calcula_con_reservas_activas_en_transaccion`; `test_pytest_suite.py` :: `test_cupo_no_se_sobrecarga_con_reservas_concurrentes` |
| R15 | No se reserva un paquete con salida vencida | `ReservaServicio.crear_reserva` | `test_reservas.py` :: `test_rechaza_cantidad_invalida_paquete_inexistente_y_fecha_pasada` |
| R16 | Al menos una persona por reserva | `Reserva`, `ReservaServicio.crear_reserva`, `CHECK` en `reservas` | `test_reservas.py` :: `test_rechaza_cantidad_invalida_paquete_inexistente_y_fecha_pasada` |
| R17 | RUT y teléfono no se muestran en listados ni errores | `seguridad/enmascarado.py`, `seguridad/logging_config.py`, cifrado Fernet en `ClienteRepositorio` | `test_persistencia.py` :: `test_rut_y_telefono_se_guardan_cifrados`; `test_presentacion.py` :: `test_cliente_se_muestra_con_rut_y_telefono_enmascarados`; `test_api_registro.py` :: `test_enmascara_rut_y_telefono_en_errores_http` |

## Acceso seguro

| Control | Dónde se implementa | Prueba que lo verifica |
|---|---|---|
| Bloqueo de 15 minutos tras 5 intentos fallidos de inicio de sesión | `AutenticacionServicio.iniciar_sesion`, `ClienteRepositorio.registrar_intento_fallido` | `test_autenticacion.py` :: `test_bloquea_al_quinto_fallo_y_permite_login_a_los_15_minutos` |
| Mismo mensaje para correo inexistente, clave incorrecta y cuenta bloqueada | `AutenticacionServicio.iniciar_sesion` (hash señuelo) | `test_autenticacion.py` :: `test_credenciales_invalidas_siempre_tienen_mensaje_generico`; `test_rubrica.py` :: `test_correo_inexistente_y_cuenta_bloqueada_comparten_mensaje` |
| La recuperación de contraseña comparte el límite de intentos | `AutenticacionServicio.recuperar_contrasena` | `test_rubrica.py` :: `test_recuperacion_se_bloquea_tras_cinco_rut_incorrectos` |
| La sesión expira tras 30 minutos de inactividad | `modelos/sesion.py` | `test_autenticacion.py` :: `test_sesion_expira_tras_30_minutos_inactiva` |
| Contraseña de 10 a 128 caracteres con mayúscula, minúscula, número y símbolo | `Validador.validar_contrasena` | `test_rubrica.py` :: `test_politica_de_contrasena_tiene_limite_superior`; `test_seguridad.py` :: `test_validadores_de_rut_mod11_y_password_con_caracter_especial` |
| RUT y teléfono cifrados en la base de datos | `seguridad/seguridad.py` (`encrypt_data`, Fernet) | `test_seguridad.py` :: `test_cifrado_fernet_hace_round_trip`; `test_persistencia.py` :: `test_rut_y_telefono_se_guardan_cifrados` |
| El registro de eventos no contiene datos sensibles | `seguridad/logging_config.py` (`FiltroDatosSensibles`) | `test_seguridad.py` :: `test_filtro_enmascara_datos_sensibles` |
| Los errores internos muestran un mensaje genérico | `api.py` (manejador de errores), `main.py` | `test_presentacion.py` :: `test_error_tecnico_muestra_mensaje_generico_y_registra_traza` |
| La respuesta del registro no devuelve credenciales | `api.py` (`/clientes/registro`) | `test_api_registro.py` :: `test_registra_y_no_devuelve_datos_credenciales` |

## Programación orientada a objetos

| Principio | Dónde se aplica |
|---|---|
| Abstracción | `modelos/usuario.py`: `Usuario` es una clase abstracta; `rol` y `puede_reservar()` son abstractos |
| Herencia | `Cliente` y `Administrador` heredan de `Usuario` y reutilizan `id`, `nombre`, `correo` y `password_hash` |
| Polimorfismo | `seguridad/autorizacion.py`: `exigir_permiso_reserva` llama a `usuario.puede_reservar()` sin consultar el tipo; cada clase responde distinto |
| Encapsulamiento | `Destino`, `Paquete` y `Reserva` guardan sus atributos como privados y los exponen con propiedades de solo lectura |

Prueba asociada: `test_rubrica.py` :: `test_uml_usuario_cliente_administrador_y_permisos`.

## Persistencia

- `repositorios/db_setup.py` crea seis tablas en SQLite: `destinos`, `paquetes`,
  `paquete_destinos`, `paquete_salidas`, `usuarios` y `reservas`.
- Las reglas críticas se refuerzan en la base con `CHECK`, `UNIQUE`, claves
  foráneas y triggers.
- Las operaciones que dependen del cupo se ejecutan dentro de una transacción
  (`BEGIN IMMEDIATE`).
- Pruebas: `test_persistencia.py` :: `test_cliente_paquete_y_reserva_sobreviven_reapertura`
  y `test_constraints_sql_relacion_y_cupo_transaccional`.

## Interfaces

- Consola: `main.py`, con menús numerados para cliente y administrador.
- Web: `api.py` (FastAPI) y `web/index.html`. Se inicia con
  `py -m uvicorn api:app --reload` y se abre en `http://127.0.0.1:8000/`.

## Pendientes conocidos

- La regla R4 no tiene una prueba dedicada.
- `Viaje_Aventura.pdf` corresponde a una versión anterior del informe: no
  describe la interfaz web ni las 49 pruebas actuales.