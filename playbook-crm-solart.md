# Playbook CRM SOLART

## 1. Estandar de nomenclatura para automatizaciones Bitrix24

### Objetivo

Establecer una nomenclatura clara, auditable y escalable para las automatizaciones del CRM, sin modificar la logica de negocio existente. El objetivo es que cualquier persona de Comercial, Marketing, CRM u Operaciones pueda entender que hace cada robot, en que etapa aplica y que tipo de accion ejecuta.

Este estandar aplica a reglas de automatizacion, recordatorios, cambios de responsable, observadores, tareas, mensajes internos, limpieza de datos y movimientos entre procesos.

### Principio rector

Cada automatizacion debe tener un nombre que explique su proposito operativo.

No deben existir nombres genericos como:

- `Modificar elemento`
- `Cambiar persona responsable (copia)`
- `Cambiar observadores (copia) (copia)`
- `Seguimiento Notificacion`
- `Generacion de nombre de prospecto (copia)`

Estos nombres impiden auditoria, mantenimiento y escalabilidad.

### Formato obligatorio

`TIPO | Etapa o caso | Accion concreta`

Ejemplos:

- `SYS | Espera recibo | Generar nombre prospecto`
- `SEG | Espera recibo | Recordatorio D+5`
- `ASIG | No util | Responsable segun usuario a asignar`
- `OBS | Credenciales | Observadores Adri`

### Tipos de automatizacion

| Tipo | Uso |
| --- | --- |
| `SYS` | Sistema, normalizacion, campos internos o controles tecnicos. |
| `DATA` | Limpieza, origen, estrategia, clasificacion o datos comerciales. |
| `ASIG` | Cambio o asignacion de responsable. |
| `OBS` | Alta o ajuste de observadores. |
| `TASK` | Creacion de tareas, actividades o pendientes. |
| `SEG` | Seguimiento, recordatorio o escalamiento. |
| `MSG` | Comentario, notificacion o mensaje interno. |
| `DOC` | Solicitud, validacion o entrega documental. |
| `TUNEL` | Movimiento, copia o creacion de elementos en otro pipeline. |

### Reglas operativas

- No cambiar la logica de una automatizacion durante un ejercicio de nomenclatura.
- No borrar robots solo porque parezcan duplicados; primero validar si responden a condiciones distintas.
- Incluir el plazo cuando la regla sea diferida: `D+2`, `D+5`, `D+10`.
- Incluir el caso cuando la regla dependa de una condicion: `Observadores Adri`, `segun usuario a asignar`, `origen segun caso`.
- Usar nombres sin acentos para reducir friccion tecnica y mantener consistencia.
- Guardar cambios en Bitrix24 despues de renombrar cada bloque de etapas.
- Documentar en matriz toda automatizacion renombrada.

### Criterio de calidad

Una automatizacion esta bien nombrada si otra persona puede responder, sin abrir el robot:

- Que tipo de accion ejecuta.
- En que etapa aplica.
- Cual es su proposito principal.
- Si es inmediata o de seguimiento diferido.
- Si pertenece a un caso especifico.

## 2. Prospectos - Automatizaciones documentadas

Estado: aplicado en Bitrix24.

Alcance: se renombraron las automatizaciones visibles del pipeline Prospectos sin modificar acciones, condiciones, responsables, campos ni logica.

### Confirmar Datos (Etapa estrategica)

| Automatizacion |
| --- |
| `SYS | Estrategica | Usuario a asignar = responsable` |
| `OBS | Estrategica | Agregar usuario si observadores vacio` |
| `OBS | Estrategica | Agregar usuario si observadores no vacio` |
| `ASIG | Estrategica | Responsable Adriana Madrid` |
| `DATA | Estrategica | Marcar trabajado por estrategica` |

### Datos por confirmar

| Automatizacion |
| --- |
| `SYS | Datos por confirmar | Generar nombre prospecto` |
| `DATA | Datos por confirmar | Marcar trabajado por estrategica` |
| `DATA | Datos por confirmar | Limpiar origen segun caso` |

### Lograr primer contacto

| Automatizacion |
| --- |
| `SYS | Primer contacto | Generar nombre prospecto` |
| `DATA | Primer contacto | Marcar trabajado por estrategica` |
| `DATA | Primer contacto | Limpiar origen segun caso` |

### Datos confirmados

| Automatizacion |
| --- |
| `SYS | Datos confirmados | Generar nombre prospecto` |
| `DATA | Datos confirmados | Marcar trabajado por estrategica` |
| `DATA | Datos confirmados | Limpiar origen segun caso` |

### E1 - Contacto Inicial

| Automatizacion |
| --- |
| `SYS | Contacto inicial | Generar nombre prospecto` |
| `ASIG | Contacto inicial | Responsable segun usuario a asignar` |
| `OBS | Contacto inicial | Observadores Adri` |
| `DATA | Contacto inicial | Limpiar origen segun caso` |

### E1 - Presentacion de Credenciales

| Automatizacion |
| --- |
| `SYS | Credenciales | Generar nombre prospecto` |
| `TASK | Credenciales | Generar CV SOLART` |
| `TASK | Credenciales | Agendar presentacion CV` |
| `SYS | Credenciales | Actualizar campos de control` |
| `ASIG | Credenciales | Responsable segun usuario a asignar` |
| `OBS | Credenciales | Observadores Adri` |
| `DATA | Credenciales | Limpiar origen segun caso` |

### En espera de RECIBO LUZ

| Automatizacion |
| --- |
| `SYS | Espera recibo | Generar nombre prospecto` |
| `SEG | Espera recibo | Notificar inmediato` |
| `SEG | Espera recibo | Recordatorio D+2` |
| `SEG | Espera recibo | Recordatorio D+5` |
| `SEG | Espera recibo | Escalar D+10 a Daniel` |
| `ASIG | Espera recibo | Responsable segun usuario a asignar` |
| `OBS | Espera recibo | Observadores Adri` |
| `DATA | Espera recibo | Limpiar origen segun caso` |

### Recibos Obtenidos SOLO ADRI

| Automatizacion |
| --- |
| `SYS | Recibo obtenido Adri | Generar nombre prospecto` |
| `ASIG | Recibo obtenido Adri | Responsable segun usuario a asignar` |
| `OBS | Recibo obtenido Adri | Observadores Adri` |

### E2 - Obtencion de Recibo

| Automatizacion |
| --- |
| `SYS | Obtencion de recibo | Generar nombre prospecto` |

### Prospecto no util

| Automatizacion |
| --- |
| `ASIG | No util | Responsable segun usuario a asignar` |
| `MSG | No util | Registrar comentario automatico` |
| `MSG | No util | Avisar empleado responsable` |
| `OBS | No util | Observadores Adri` |

## 3. Negociaciones - Automatizaciones documentadas

Estado: aplicado en Bitrix24 para las etapas visibles revisadas de `PROCESO DE VENTA`.

Alcance aplicado: se renombraron y guardaron las automatizaciones visibles de `1_Generacion de propuesta`, `2_Propuesta Preliminar`, `3_Se agendo/presento propuesta inicial`, `4_Visita Tecnica`, `5_Propuesta Formal`, `6_Evaluacion Interna`, `7_Propuesta Final (SI VERBAL)`, `Generacion de recibo SOLART`, `Envio Email automatico acelerador`, `Abrio Email (Acelerador)`, `Recuperada`, `8_Si Verbal` y `Cerrado Perdido` sin modificar acciones, condiciones, responsables, campos ni logica.

Bitacora de continuidad: `Propuesta financiera` fue revisada sin robots visibles en la vista actual. `Generacion de recibo SOLART`, `Envio Email automatico acelerador`, `Abrio Email (Acelerador)` y `Recuperada` quedaron aplicadas, guardadas y revalidadas visualmente en Bitrix24. No se modifico logica, acciones, condiciones, responsables ni campos.

Documento operativo: [bitrix24-negociaciones-nomenclatura.md](/Users/luisamor/Documents/BITRIX_SOLART/bitrix24-negociaciones-nomenclatura.md)

### 1_Generacion de propuesta

| Automatizacion |
| --- |
| `SYS | Gen propuesta | Generar titulo negociacion` |
| `TASK | Gen propuesta | Generar propuesta Sunwise` |
| `TASK | Gen propuesta | Generar propuesta especial` |
| `MSG | Gen propuesta | Avisar propuesta especial D+10m` |
| `MSG | Gen propuesta | Avisar Sunwise D+10m` |
| `SEG | Gen propuesta | Seguimiento D+3 chat grupal` |
| `DATA | Gen propuesta | Actualizar compania potencial` |
| `DATA | Gen propuesta | Actualizar monto potencial` |

### 2_Propuesta Preliminar

| Automatizacion |
| --- |
| `SYS | Propuesta preliminar | Generar titulo negociacion` |
| `SEG | Propuesta preliminar | Seguimiento D+2 chat grupal` |
| `DATA | Propuesta preliminar | Actualizar compania potencial` |
| `DATA | Propuesta preliminar | Actualizar monto potencial` |

### 3_Se agendo/presento propuesta inicial

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `SYS | Presentacion inicial | Actualizar campos de control` |
| `TASK | Presentacion inicial | Planificar actividad responsable` |
| `SEG | Presentacion inicial | Seguimiento D+5 chat grupal` |
| `SEG | Presentacion inicial | Seguimiento D+3 chat grupal` |
| `DATA | Presentacion inicial | Actualizar compania potencial` |
| `DATA | Presentacion inicial | Actualizar monto potencial` |

### 4_Visita Tecnica

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `SYS | Visita tecnica | Actualizar campos de control` |
| `SYS | Visita tecnica | Control actualizacion propuesta` |
| `MSG | Visita tecnica | Comentario control actualizacion` |
| `TASK | Visita tecnica | Crear tarea Carlos Mariscal` |
| `MSG | Visita tecnica | Comentario visita tecnica` |
| `SEG | Visita tecnica | Seguimiento D+5 chat grupal` |
| `DATA | Visita tecnica | Validar BESS financiera VT` |
| `DATA | Visita tecnica | Actualizar compania potencial` |
| `DATA | Visita tecnica | Actualizar monto potencial` |

### 5_Propuesta Formal

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `DATA | Propuesta formal | Validar BESS financiera VT` |
| `TASK | Propuesta formal | Actualizar propuesta` |
| `TASK | Propuesta formal | Actualizar propuesta BESS` |
| `SYS | Propuesta formal | Actualizar campos de control` |
| `MSG | Propuesta formal | Comentario post visita` |
| `DATA | Propuesta formal | Actualizar compania potencial` |
| `DATA | Propuesta formal | Actualizar monto potencial` |
| `MSG | Propuesta formal | Avisar propuesta BESS` |

### 6_Evaluacion Interna

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `SYS | Evaluacion interna | Actualizar campos de control` |
| `TASK | Evaluacion interna | Programar llamada D+3` |
| `SYS | Evaluacion interna | Control actualizacion propuesta` |
| `MSG | Evaluacion interna | Comentario control actualizacion` |
| `SEG | Evaluacion interna | Seguimiento D+5 chat grupal` |
| `DATA | Evaluacion interna | Compra financiera pendiente` |
| `DATA | Evaluacion interna | Financiera pendiente` |
| `DATA | Evaluacion interna | Actualizar compania potencial` |
| `DATA | Evaluacion interna | Actualizar monto potencial` |

### 7_Propuesta Final (SI VERBAL)

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `SYS | SI verbal preliminar | Actualizar campos de control` |
| `TASK | SI verbal preliminar | Actualizar propuesta` |
| `MSG | SI verbal preliminar | Comentario actualizacion propuesta` |
| `DATA | SI verbal preliminar | Forma de compra pendiente` |
| `DATA | SI verbal preliminar | Financiera pendiente` |
| `DATA | SI verbal preliminar | Actualizar compania potencial` |
| `DATA | SI verbal preliminar | Actualizar monto potencial` |
| `DATA | SI verbal preliminar | Confirmar fecha probable cierre` |

### Propuesta financiera

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### Generacion de recibo SOLART

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `SYS | Recibo SOLART | Actualizar campos de control` |
| `DATA | Recibo SOLART | Sumar meses transcurridos` |
| `DATA | Recibo SOLART | Limpiar control meses transcurridos` |
| `DATA | Recibo SOLART | Calcular ahorro acumulado` |
| `DOC | Recibo SOLART | Crear documento` |

### Envio Email automatico acelerador

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `DATA | Email acelerador | Sumar meses transcurridos` |
| `DATA | Email acelerador | Limpiar control meses transcurridos` |
| `DATA | Email acelerador | Calcular ahorro acumulado` |
| `DOC | Email acelerador | Crear documento` |
| `MSG | Email acelerador | Enviar correo cliente` |

### Abrio Email (Acelerador)

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `MSG | Abrio email acelerador | Avisar empleado` |
| `DATA | Abrio email acelerador | Sumar meses transcurridos` |
| `DATA | Abrio email acelerador | Limpiar control meses transcurridos` |
| `DATA | Abrio email acelerador | Calcular ahorro acumulado` |

### Recuperada

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `ASIG | Recuperada | Responsable del contacto` |
| `SYS | Recuperada | Actualizar campos de control` |
| `DATA | Recuperada | Actualizar datos comerciales` |
| `DATA | Recuperada | Actualizar control recuperada` |

### 8_Si Verbal

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `TUNEL | Si verbal | Mover a cierre` |
| `DATA | Si verbal | Actualizar compania potencial` |
| `DATA | Si verbal | Actualizar monto potencial` |
| `DATA | Si verbal | Confirmar fecha probable cierre` |

### Cerrado Perdido

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `MSG | Cerrado perdido | Registrar comentario` |
| `DATA | Cerrado perdido | Actualizar contacto` |
| `OBS | Cerrado perdido | Observadores segun caso` |
| `OBS | Cerrado perdido | Observadores adicionales` |
| `ASIG | Cerrado perdido | Responsable Adriana Madrid` |
| `TASK | Cerrado perdido | Crear tarea Adriana Madrid` |

## 4. Cierre - Automatizaciones documentadas

Estado: aplicado en Bitrix24 para las etapas visibles revisadas de `PROCESO DE CIERRE`.

Alcance aplicado: se renombraron y guardaron las automatizaciones visibles de `10_Generacion y obtencion de documentos para contrato` y `Anticipo PAGADO`. Se revisaron `9_SI VERBAL (Cierre)`, `11_Firma de Contrato`, `Espera anticipo` y `Cerrado Perdido` sin robots visibles en la vista actual. No se modifico logica, acciones, condiciones, responsables ni campos.

Documento operativo: [bitrix24-cierre-nomenclatura.md](/Users/luisamor/Documents/BITRIX_SOLART/bitrix24-cierre-nomenclatura.md)

### 9_SI VERBAL (Cierre)

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### 10_Generacion y obtencion de documentos para contrato

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `TASK | Docs contrato | Planificar actividad responsable` |
| `TASK | Docs contrato | Checklist documentos Eduardo` |

### 11_Firma de Contrato

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### Espera anticipo

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### Anticipo PAGADO

Estado: aplicado en Bitrix24.

| Automatizacion |
| --- |
| `TUNEL | Anticipo pagado | Mover negociacion` |

### Cerrado Perdido

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

## 5. Proceso recomendado para siguientes pipelines

### Paso 1. Inventario

Registrar cada automatizacion con:

- Pipeline.
- Etapa.
- Nombre actual.
- Nombre propuesto.
- Tipo.
- Responsable afectado.
- Condicion principal.
- Accion principal.
- Riesgo operativo.

### Paso 2. Renombrado

Renombrar un bloque de etapas a la vez, validar visualmente y guardar cambios en Bitrix24.

### Paso 3. Validacion

Confirmar que:

- Las automatizaciones siguen activas.
- No se cambiaron acciones.
- No se cambiaron condiciones.
- No se alteraron campos.
- No se modificaron responsables.

### Paso 4. Documentacion

Actualizar la matriz operativa y este playbook. La matriz mantiene el detalle granular; el playbook conserva el estandar y el resumen ejecutivo.

## 6. Nomenclatura de etapas CRM

Estado: Prospectos aplicado en Bitrix24 el 30 de mayo de 2026. Negociaciones - Proceso de venta documentado y listo para aplicar en Bitrix24. Cierre permanece como propuesta antes de aplicar en Bitrix24.

Objetivo: ordenar las etapas en forma secuencial/operativa con prefijos numericos, evitar nombres ambiguos y facilitar reportes, filtros, vistas Kanban y conversaciones internas. Regla de cambio: modificar unicamente etiquetas visibles de etapa; no alterar automatizaciones, condiciones, responsables, campos, tareas ni integraciones sin validacion previa.

### Prospectos

Nota: nomenclatura aplicada para que los informes puedan ordenarse alfabeticamente respetando el flujo comercial real.

| Orden | Nombre aplicado |
| --- | --- |
| 00 | `00_Validacion estrategica` |
| 01 | `01_Datos por confirmar` |
| 02 | `02_Primer contacto pendiente` |
| 03 | `03_Datos confirmados` |
| 04 | `04_Contacto comercial inicial` |
| 05 | `05_Credenciales presentadas` |
| 06 | `06_Espera recibo CFE` |
| 07 | `07_Recibo recibido Adri` |
| 08 | `08_Recibo validado` |
| 99 | `99_Prospecto no util` |

### Negociaciones - Proceso de venta

Documento operativo: [bitrix24-negociaciones-etapas.md](/Users/luisamor/Documents/BITRIX_SOLART/bitrix24-negociaciones-etapas.md)

Nota: nomenclatura definida para que los informes puedan ordenarse alfabeticamente respetando el flujo comercial real. Pendiente aplicar en Bitrix24 cuando la ventana correcta de configuracion este al frente.

| Orden | Nombre para aplicar |
| --- | --- |
| 01 | `01_Generacion propuesta` |
| 02 | `02_Propuesta preliminar` |
| 03 | `03_Presentacion inicial` |
| 04 | `04_Visita tecnica` |
| 05 | `05_Propuesta formal` |
| 06 | `06_Evaluacion interna` |
| 07 | `07_Propuesta final SI verbal` |
| 08 | `08_Propuesta financiera` |
| 09 | `09_Generacion recibo SOLART` |
| 10 | `10_Envio email acelerador` |
| 11 | `11_Abrio email acelerador` |
| 12 | `12_Recuperada` |
| 13 | `13_Si verbal` |
| 99 | `99_Cerrado perdido` |

### Cierre

| Orden | Nombre recomendado |
| --- | --- |
| 01 | `01_SI verbal cierre` |
| 02 | `02_Documentos contractuales` |
| 03 | `03_Firma contrato` |
| 04 | `04_Espera anticipo` |
| 05 | `05_Anticipo pagado` |
| 99 | `99_Cerrado perdido` |

Regla de aplicacion: no cambiar nombres de etapas hasta terminar la limpieza de nombres de automatizaciones del pipeline activo y guardar respaldo documental. El cambio de etapas debe hacerse en una ventana controlada, con validacion posterior de robots, filtros, dashboards y reportes.

## 7. Backlog sugerido

Siguientes procesos a documentar con el mismo estandar:

- Siguiente bloque recomendado: `PROCESO INSTALACION E INTERCONEXION`.
- Instalacion e interconexion.
- Entrega final.
- Servicio posventa.
- Mantenimientos.
