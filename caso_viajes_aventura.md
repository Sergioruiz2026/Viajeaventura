# Caso · Agencia de Viajes — Viajes Aventura

**TI3V21 · Programación Orientada a Objeto Seguro · Unidad 4**
Antecedentes para el levantamiento de requerimientos · Unidad 4.
Acompaña a la guía oficial de la evaluación, que define los entregables y las condiciones de entrega.
Sección V-IEI-N2-P3-C1 · INACAP Valparaíso · Prof. Rubén Schnettler

> Agencia que arma y vende paquetes turísticos combinando destinos. Administra el catálogo en una planilla, toma las reservas por mensajería y guarda los datos de sus clientes en un cuaderno.

---

## 1. El negocio

**Viajes Aventura** es una agencia creada hace dos años por tres socios en Valparaíso, en una oficina de calle Esmeralda. Paulina Ovalle venía de trabajar en un operador mayorista, Matías Bórquez era guía de trekking e Ignacio Salas llevaba la administración de un hostal familiar. No revenden paquetes de otros: **arman los suyos combinando destinos** que ellos mismos han recorrido.

El ingreso proviene de la venta de esos paquetes a personas naturales, que pagan por transferencia. El costo principal son los servicios contratados en cada destino: transporte, alojamiento y guías. La agencia no tiene sistema: todo lo que existe es una planilla de cálculo, un cuaderno de reservas y las conversaciones de mensajería con cada cliente.

| Antecedente | Valor actual |
|---|---|
| Años de operación | Dos |
| Personas | 3 socios, sin otro personal |
| Destinos en el catálogo | 18, de los cuales 4 ya no se operan |
| Paquetes publicados por temporada | Entre 8 y 12 |
| Reservas en la última temporada | 214 |
| Forma de pago | Transferencia bancaria, verificada a mano por un socio |
| Costo principal | Transporte, alojamiento y guías contratados en cada destino |

### 1.1 Los destinos del catálogo

Un destino es un lugar con un servicio ya cotizado: la agencia conoce cuánto le cuesta llevar a una persona allí. Estos son seis de los dieciocho.

| Destino | Zona | Duración | Costo base por persona |
|---|---|---|---|
| Valle del Elqui | Región de Coquimbo | 2 días | 120.000 |
| Salar de Surire | Región de Arica y Parinacota | 3 días | 310.000 |
| Cajón del Maipo | Región Metropolitana | 1 día | 45.000 |
| Parque Conguillío | Región de La Araucanía | 3 días | 185.000 |
| Carretera Austral | Región de Aysén | 7 días | 640.000 |
| Isla Damas | Región de Coquimbo | 1 día | 38.000 |

### 1.2 Cómo se arma un paquete

Un paquete reúne varios destinos bajo un nombre comercial, con una fecha de salida, una de regreso y un cupo máximo de personas. La agencia **fija el margen** con que quiere vender cada paquete, y el precio resulta de sumar el costo de los destinos incluidos y agregar ese margen.

| Paquete | Destinos que combina | Cupo | Temporada |
|---|---|---|---|
| Norte Grande en 5 días | Salar de Surire · Valle del Elqui | 12 personas | Julio |
| Escapada de fin de semana | Cajón del Maipo · Isla Damas | 20 personas | Todo el año |
| Sur profundo | Parque Conguillío · Carretera Austral | 8 personas | Enero y febrero |

### 1.3 Quiénes participan

| Rol | Qué hace hoy |
|---|---|
| Cliente | Consulta los paquetes disponibles, pregunta por cupos y fechas, entrega sus datos personales y reserva. Después pregunta por el estado de su reserva. |
| Administrador | Mantiene el catálogo de destinos, arma los paquetes, fija los cupos y publica las temporadas. Hoy es uno de los socios. |

---

## 2. Cómo trabajan hoy

El catálogo de destinos vive en una planilla de cálculo compartida. Los tres socios la editan, y cada uno agregó columnas cuando las necesitó. Hay destinos repetidos con nombres distintos, destinos que ya no operan pero que siguen apareciendo, y costos que nadie recuerda cuándo se actualizaron por última vez.

Los paquetes se arman escribiendo, en otra hoja de la misma planilla, qué destinos incluye cada uno. La suma del precio se hace con una fórmula que a veces se rompe al copiar filas. Cuando un socio corrige el costo de un destino, los paquetes ya vendidos cambian de precio en la planilla, aunque el cliente haya pagado otro valor.

Las reservas se anotan en un cuaderno y se confirman por mensajería. Los datos del cliente —nombre, RUT, teléfono y correo— quedan en ese mismo cuaderno y, a veces, solo en la conversación de mensajería del socio que atendió.

### Hoja «Reservas temporada» — una fila por reserva, escrita por quien atendió

```
Cliente          | Paquete              | Personas | Fecha | Total     | Estado
Carolina Reyes   | Norte Grande         | 2        | 12-06 | 1.050.000 | Pagado
c. reyes         | norte grande 5 días  | 2        | 14-06 | 1.050.000 |
Andrés Pinto     | Escapada fin semana  | 4        | 02-07 | 380.000   | Pagado
Familia Pinto    | Escapada             | 4        |       | 380.000   | Pagado
Sofía Larraín    | Sur profundo         | 3        | 20-12 | 2.100.000 | Pendiente
Sofía Larraín    | Sur profundo         | 3        | 20-12 | 2.475.000 | Pagado
```

Las dos primeras filas son la misma reserva, escrita por dos socios distintos. Las filas tres y cuatro también. Las dos últimas corresponden a la misma clienta y al mismo paquete, con dos totales distintos: entre una y otra, alguien actualizó el costo de un destino. Nadie sabe cuál de los dos valores se cobró.

---

## 3. Entrevistas

### 3.1 Entrevista con la socia a cargo del catálogo

**Paulina Ovalle · Socia fundadora, catálogo y paquetes**

> «Tengo dieciocho destinos en la planilla y cuatro ya no los operamos, pero no los borro porque están dentro de paquetes que vendimos el año pasado. Si los borro, esas filas quedan sin nada.»
>
> «Lo que más me cuesta es armar un paquete nuevo. Tengo que ir buscando destino por destino, copiar el costo a mano, sumar y recién ahí aplicarle el margen con que lo quiero vender. La última vez me equivoqué en un cero y el paquete salió publicado a la décima parte de lo que costaba. Lo vendimos así.»

### 3.2 Entrevista con el socio que toma las reservas

**Matías Bórquez · Socio, atención y reservas**

> «El cupo lo llevo en la cabeza y en el cuaderno. La temporada pasada vendí catorce lugares en un paquete que tenía doce. Tuve que llamar a dos personas para decirles que no había espacio, y una de ellas ya había comprado el pasaje para llegar al punto de encuentro.»
>
> «También me ha pasado vender un paquete cuya fecha de salida ya había pasado. Estaba en la planilla, se veía disponible, y nadie lo había sacado.»

### 3.3 Entrevista con el socio a cargo de la administración

**Ignacio Salas · Socio, administración y datos**

> «Los datos de los clientes están en el cuaderno, en la planilla y en los teléfonos de los tres. Si alguien me pregunta cuántas personas han viajado con nosotros, no tengo cómo responder con certeza.»
>
> «Me preocupa el RUT y el teléfono. Están escritos en una planilla que cualquiera de los tres abre desde su computador personal, y esa planilla se ha enviado por correo varias veces. Si se pierde, se pierde con todo lo de los clientes adentro.»
>
> «Y cuando un cliente pregunta qué reservó el año pasado, tengo que revisar el cuaderno hoja por hoja.»

---

## 4. La temporada en cifras

| Indicador | Valor |
|---|---|
| Reservas registradas | 214 |
| Reservas duplicadas detectadas al cierre | 19 |
| Reservas aceptadas por sobre el cupo del paquete | 6 |
| Reservas tomadas sobre paquetes con fecha de salida vencida | 3 |
| Paquetes publicados con un precio distinto del que se cobró | 4 |
| Consultas de clientes por reservas anteriores, respondidas revisando el cuaderno | 31 |
| Destinos del catálogo que ya no se operan y siguen visibles | 4 |

> **PISTA PARA EL ANÁLISIS**
> Las seis reservas por sobre el cupo y las tres sobre fechas vencidas **no son el mismo problema**: la primera exige comparar contra un dato que el sistema debe llevar, y la segunda, comparar contra la fecha del día. Las cuatro diferencias de precio tampoco son un error de suma: son consecuencia de que el costo de un destino cambie después de vendido un paquete.

---

## 5. Reglas de negocio vigentes

Las siguientes reglas están en operación y fueron confirmadas por los socios, pero **no son requerimientos**: una regla describe cómo funciona el negocio y un requerimiento describe qué debe hacer el sistema. Esa traducción es parte del trabajo evaluado.

| N.º | Regla |
|---|---|
| R1 | Un destino tiene nombre, zona, descripción, duración en días y un costo base por persona. El nombre no se repite en el catálogo. |
| R2 | El costo base de un destino es siempre mayor que cero. |
| R3 | Un paquete combina **entre dos y cinco destinos**, y ningún destino se repite dentro del mismo paquete. |
| R4 | Un mismo destino puede formar parte de varios paquetes al mismo tiempo. |
| R5 | Un paquete tiene nombre, fecha de salida, fecha de regreso y cupo máximo de personas. La fecha de regreso es posterior a la de salida y el cupo es mayor que cero. |
| R6 | Al crear un paquete, el administrador **define** sus fechas y su **margen de operación**, que habitualmente es del 20 % y nunca es negativo. El sistema **calcula** el precio por persona como la suma de los costos base de los destinos incluidos, más ese margen. |
| R7 | El precio queda fijado cuando el paquete se publica. Si después cambia el costo de un destino, los paquetes ya publicados conservan su precio. |
| R8 | Un destino que **no forma parte de ningún paquete se elimina** del catálogo. Si forma parte de alguno, no se elimina: se marca como **no disponible** y deja de ofrecerse para paquetes nuevos, de modo que los paquetes ya vendidos conserven su contenido. |
| R9 | Un cliente se registra con nombre, RUT, correo electrónico, teléfono y contraseña. El correo identifica al cliente y no se repite. |
| R10 | La contraseña nunca se almacena tal como el cliente la escribió. |
| R11 | Solo un cliente autenticado puede reservar y consultar reservas, y cada cliente ve **únicamente las suyas**. |
| R12 | Una reserva corresponde a un cliente y a un paquete, y registra la fecha en que se emitió, la cantidad de personas y el total cobrado. |
| R13 | El total de una reserva se calcula al momento de reservar, multiplicando el precio del paquete por la cantidad de personas, y no vuelve a cambiar. |
| R14 | El cupo disponible de un paquete es su cupo máximo menos las personas ya reservadas. No se acepta una reserva que supere el cupo disponible. |
| R15 | No se acepta una reserva sobre un paquete cuya fecha de salida ya pasó. |
| R16 | La cantidad de personas de una reserva es al menos uno. |
| R17 | El RUT y el teléfono de un cliente son datos sensibles: no se muestran en listados ni en mensajes de error. |

---

## 6. Alcance del proyecto

Los socios acordaron el siguiente alcance para la primera versión del sistema.

| Dentro del alcance | Fuera del alcance |
|---|---|
| **Destinos:** registrar, modificar, dejar no disponible y listar los del catálogo. | Pasarela de pago y verificación automática de transferencias. |
| **Paquetes:** crear combinando destinos, definir fechas y cupo, calcular el precio y consultar disponibilidad. | Facturación electrónica ante el Servicio de Impuestos Internos. |
| **Reservas:** registro y autenticación de clientes, reservar un paquete, almacenar la reserva y consultar el historial propio. | Aplicación para teléfonos. |
| **Seguridad del sistema:** autenticación, validación de todo dato ingresado y protección de credenciales y datos sensibles. | Integración con aerolíneas, hoteles u operadores externos. |
| | Envío de correos o mensajería al cliente. |
| | Informes de gestión para los socios. |
| | Contabilidad y remuneraciones. |

> **LOS VACÍOS DEL CASO**
> Ningún caso entrega toda la información, y este tampoco. Detectar qué falta corresponde a su **criterio profesional**. El caso no dice, por ejemplo, qué ocurre cuando un cliente desiste de una reserva, ni cómo se comporta un paquete cuando su temporada termina, ni quién puede modificar el catálogo. Cuando un dato no esté disponible, adopte un **supuesto**, declárelo de forma explícita en el informe y **fundaméntelo técnicamente**: por qué es razonable para este negocio.

---

*Prof. Rubén Schnettler · INACAP Valparaíso — transcrito desde las 5 páginas del enunciado.*
