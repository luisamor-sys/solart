# SOLART - Nomenclatura de automatizaciones Bitrix24: Negociaciones

## Objetivo

Ordenar las automatizaciones del pipeline `PROCESO DE VENTA` sin modificar logica, condiciones, acciones, responsables ni campos. El trabajo consiste en cambiar nombres visibles para que cada robot sea auditable por Comercial, CRM, Direccion y Operaciones.

## Estado de avance

- `1_Generacion de propuesta`: aplicado y guardado en Bitrix24.
- `2_Propuesta Preliminar`: aplicado y guardado en Bitrix24.
- `3_Se agendo/presento propuesta inicial`: aplicado y guardado en Bitrix24.
- `4_Visita Tecnica`: aplicado, guardado y revalidado visualmente en Bitrix24.
- `5_Propuesta Formal`: aplicado y guardado en Bitrix24.
- `6_Evaluacion Interna`: aplicado y guardado en Bitrix24.
- `7_Propuesta Final (SI VERBAL)`: aplicado y guardado en Bitrix24.
- `Propuesta financiera`: revisada; sin robots visibles en la vista actual.
- `Generacion de recibo SOLART`: aplicado y guardado en Bitrix24.
- `Envio Email automatico acelerador`: aplicado y guardado en Bitrix24.
- `Abrio Email (Acelerador)`: aplicado y guardado en Bitrix24.
- `Recuperada`: aplicado y guardado en Bitrix24.
- `8_Si Verbal`: aplicado y guardado en Bitrix24.
- `Cerrado Perdido`: aplicado y guardado en Bitrix24.
- Resto de etapas: pendiente revisar si existen etapas adicionales fuera de la vista actual.

## Convencion

Formato:

`TIPO | Etapa o caso | Accion concreta`

Tipos:

- `SYS`: sistema, normalizacion, campos internos o controles tecnicos.
- `DATA`: datos comerciales, limpieza, calculos o clasificacion.
- `ASIG`: asignacion o cambio de responsable.
- `OBS`: observadores.
- `TASK`: tareas o actividades.
- `SEG`: seguimiento, recordatorio o escalamiento.
- `MSG`: comentario, notificacion o mensaje interno.
- `DOC`: documentos.
- `TUNEL`: movimiento entre pipelines.

## Pipeline Negociaciones

### 1_Generacion de propuesta

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Titulo de negociacion_1 | `SYS | Gen propuesta | Generar titulo negociacion` | Aplicado en Bitrix |
| Tarea de generacion de propuesta SUNWISE | `TASK | Gen propuesta | Generar propuesta Sunwise` | Aplicado en Bitrix |
| Tarea de generacion de propuesta (Especial) | `TASK | Gen propuesta | Generar propuesta especial` | Aplicado en Bitrix |
| Propuesta especial_messenger | `MSG | Gen propuesta | Avisar propuesta especial D+10m` | Aplicado en Bitrix |
| SUNWISE_Menssenger | `MSG | Gen propuesta | Avisar Sunwise D+10m` | Aplicado en Bitrix |
| Enviar mensaje al chat grupal | `SEG | Gen propuesta | Seguimiento D+3 chat grupal` | Aplicado en Bitrix |
| Modificar compania potencial | `DATA | Gen propuesta | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial | `DATA | Gen propuesta | Actualizar monto potencial` | Aplicado en Bitrix |

### 2_Propuesta Preliminar

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Titulo de negociacion_1 (copia) | `SYS | Propuesta preliminar | Generar titulo negociacion` | Aplicado en Bitrix |
| Enviar mensaje al chat grupal (copia) | `SEG | Propuesta preliminar | Seguimiento D+2 chat grupal` | Aplicado en Bitrix |
| Modificar compania potencial (copia) | `DATA | Propuesta preliminar | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial (copia) | `DATA | Propuesta preliminar | Actualizar monto potencial` | Aplicado en Bitrix |

### 3_Se agendo/presento propuesta inicial

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Modificar elemento (copia) (copia) (copia) | `SYS | Presentacion inicial | Actualizar campos de control` | Aplicado en Bitrix |
| Planificar actividad | `TASK | Presentacion inicial | Planificar actividad responsable` | Aplicado en Bitrix |
| Enviar mensaje al chat grupal (copia) (copia) | `SEG | Presentacion inicial | Seguimiento D+5 chat grupal` | Aplicado en Bitrix |
| Enviar mensaje al chat grupal (copia) (copia) (copia) | `SEG | Presentacion inicial | Seguimiento D+3 chat grupal` | Aplicado en Bitrix |
| Modificar compania potencial (copia) (copia) | `DATA | Presentacion inicial | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial (copia) (copia) | `DATA | Presentacion inicial | Actualizar monto potencial` | Aplicado en Bitrix |

### 4_Visita Tecnica

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Modificar elemento (copia) (copia) | `SYS | Visita tecnica | Actualizar campos de control` | Aplicado en Bitrix |
| Control actualizacion de propuesta (copia) | `SYS | Visita tecnica | Control actualizacion propuesta` | Aplicado en Bitrix |
| Control actualizacion de propuesta comentario (copia) | `MSG | Visita tecnica | Comentario control actualizacion` | Aplicado en Bitrix |
| Crear tarea | `TASK | Visita tecnica | Crear tarea Carlos Mariscal` | Aplicado en Bitrix |
| Comentario visita tecnica | `MSG | Visita tecnica | Comentario visita tecnica` | Aplicado en Bitrix |
| Enviar mensaje al chat grupal (copia) (copia) (copia) (copia) | `SEG | Visita tecnica | Seguimiento D+5 chat grupal` | Aplicado en Bitrix |
| BESS/Financiera VT | `DATA | Visita tecnica | Validar BESS financiera VT` | Aplicado en Bitrix |
| Modificar compania potencial (copia) (copia) (copia) | `DATA | Visita tecnica | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial (copia) (copia) (copia) | `DATA | Visita tecnica | Actualizar monto potencial` | Aplicado en Bitrix |

### 5_Propuesta Formal

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| BESS/Financiera VT (copia) | `DATA | Propuesta formal | Validar BESS financiera VT` | Aplicado en Bitrix |
| Tarea de generacion de propuesta (actualizacion) | `TASK | Propuesta formal | Actualizar propuesta` | Aplicado en Bitrix |
| BESSTarea de generacion de propuesta (actualizacion) | `TASK | Propuesta formal | Actualizar propuesta BESS` | Aplicado en Bitrix |
| Modificar elemento | `SYS | Propuesta formal | Actualizar campos de control` | Aplicado en Bitrix |
| Comentario post visita | `MSG | Propuesta formal | Comentario post visita` | Aplicado en Bitrix |
| Modificar compania potencial (copia) (copia) (copia) (copia) | `DATA | Propuesta formal | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial (copia) (copia) (copia) (copia) | `DATA | Propuesta formal | Actualizar monto potencial` | Aplicado en Bitrix |
| Propuesta BESS_Messenger | `MSG | Propuesta formal | Avisar propuesta BESS` | Aplicado en Bitrix |

### 6_Evaluacion Interna

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Modificar elemento (copia) | `SYS | Evaluacion interna | Actualizar campos de control` | Aplicado en Bitrix |
| Programar una llamada | `TASK | Evaluacion interna | Programar llamada D+3` | Aplicado en Bitrix |
| Control actualizacion de propuesta | `SYS | Evaluacion interna | Control actualizacion propuesta` | Aplicado en Bitrix |
| Control actualizacion de propuesta comentario | `MSG | Evaluacion interna | Comentario control actualizacion` | Aplicado en Bitrix |
| Enviar mensaje al chat grupal (copia) (copia) (copia) (copia) (copia) | `SEG | Evaluacion interna | Seguimiento D+5 chat grupal` | Aplicado en Bitrix |
| Modificar elemento aun no saben financiera | `DATA | Evaluacion interna | Compra financiera pendiente` | Aplicado en Bitrix |
| Modificar elemento aun no saben financiera (copia) | `DATA | Evaluacion interna | Financiera pendiente` | Aplicado en Bitrix |
| Modificar compania potencial (copia) (copia) (copia) (copia) (copia) | `DATA | Evaluacion interna | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial (copia) (copia) (copia) (copia) (copia) | `DATA | Evaluacion interna | Actualizar monto potencial` | Aplicado en Bitrix |

### 7_Propuesta Final (SI VERBAL)

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Modificar elemento (copia) (copia) | `SYS | SI verbal preliminar | Actualizar campos de control` | Aplicado en Bitrix |
| Tarea de generacion de propuesta (actualizacion) (copia) | `TASK | SI verbal preliminar | Actualizar propuesta` | Aplicado en Bitrix |
| Comentario actualizacion de propuesta | `MSG | SI verbal preliminar | Comentario actualizacion propuesta` | Aplicado en Bitrix |
| Modificar elemento aun no saben forma de compra | `DATA | SI verbal preliminar | Forma de compra pendiente` | Aplicado en Bitrix |
| Modificar elemento aun no saben financiera (copia) | `DATA | SI verbal preliminar | Financiera pendiente` | Aplicado en Bitrix |
| Modificar compania potencial (copia) (copia) (copia) (copia) (copia) (copia) | `DATA | SI verbal preliminar | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial (copia) (copia) (copia) (copia) (copia) (copia) | `DATA | SI verbal preliminar | Actualizar monto potencial` | Aplicado en Bitrix |
| Fecha probable de cierre (confirmacion) | `DATA | SI verbal preliminar | Confirmar fecha probable cierre` | Aplicado en Bitrix |

### Propuesta financiera

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### Generacion de recibo SOLART

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Modificar elemento | `SYS | Recibo SOLART | Actualizar campos de control` | Aplicado en Bitrix |
| Sumar meses transcurridos | `DATA | Recibo SOLART | Sumar meses transcurridos` | Aplicado en Bitrix |
| Limpiar control meses transcurridos | `DATA | Recibo SOLART | Limpiar control meses transcurridos` | Aplicado en Bitrix |
| Calcular ahorro acumulado | `DATA | Recibo SOLART | Calcular ahorro acumulado` | Aplicado en Bitrix |
| Crear documento | `DOC | Recibo SOLART | Crear documento` | Aplicado en Bitrix |

### Envio Email automatico acelerador

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Sumar meses transcurridos | `DATA | Email acelerador | Sumar meses transcurridos` | Aplicado en Bitrix |
| Limpiar control meses transcurridos | `DATA | Email acelerador | Limpiar control meses transcurridos` | Aplicado en Bitrix |
| Calcular ahorro acumulado | `DATA | Email acelerador | Calcular ahorro acumulado` | Aplicado en Bitrix |
| Crear documento | `DOC | Email acelerador | Crear documento` | Aplicado en Bitrix |
| Enviar mensaje de correo electronico | `MSG | Email acelerador | Enviar correo cliente` | Aplicado en Bitrix |

### Abrio Email (Acelerador)

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Enviar un mensaje directo al empleado | `MSG | Abrio email acelerador | Avisar empleado` | Aplicado en Bitrix |
| Sumar meses transcurridos | `DATA | Abrio email acelerador | Sumar meses transcurridos` | Aplicado en Bitrix |
| Limpiar control meses transcurridos | `DATA | Abrio email acelerador | Limpiar control meses transcurridos` | Aplicado en Bitrix |
| Calcular ahorro acumulado | `DATA | Abrio email acelerador | Calcular ahorro acumulado` | Aplicado en Bitrix |

### Recuperada

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Cambiar persona responsable | `ASIG | Recuperada | Responsable del contacto` | Aplicado en Bitrix |
| Modificar elemento | `SYS | Recuperada | Actualizar campos de control` | Aplicado en Bitrix |
| Modificar elemento | `DATA | Recuperada | Actualizar datos comerciales` | Aplicado en Bitrix |
| Modificar elemento | `DATA | Recuperada | Actualizar control recuperada` | Aplicado en Bitrix |

### 8_Si Verbal

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Mover negociacion | `TUNEL | Si verbal | Mover a cierre` | Aplicado en Bitrix |
| Modificar compania potencial | `DATA | Si verbal | Actualizar compania potencial` | Aplicado en Bitrix |
| Monto potencial | `DATA | Si verbal | Actualizar monto potencial` | Aplicado en Bitrix |
| Fecha probable de cierre (confirmacion) (copia) | `DATA | Si verbal | Confirmar fecha probable cierre` | Aplicado en Bitrix |

### Cerrado Perdido

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Agregar un comentario al elemento | `MSG | Cerrado perdido | Registrar comentario` | Aplicado en Bitrix |
| Modificar contacto | `DATA | Cerrado perdido | Actualizar contacto` | Aplicado en Bitrix |
| Cambiar observadores | `OBS | Cerrado perdido | Observadores segun caso` | Aplicado en Bitrix |
| Cambiar observadores (copia) | `OBS | Cerrado perdido | Observadores adicionales` | Aplicado en Bitrix |
| Cambiar persona responsable | `ASIG | Cerrado perdido | Responsable Adriana Madrid` | Aplicado en Bitrix |
| Crear tarea | `TASK | Cerrado perdido | Crear tarea Adriana Madrid` | Aplicado en Bitrix |

## Notas operativas

- Toda propuesta debe seguir pasando por Sunwise y por validacion de Ingenieria.
- No se debe entregar propuesta formal sin validacion.
- Los robots de monto, compania potencial y fecha probable de cierre son controles de trazabilidad; no eliminarlos aunque parezcan repetidos.
- Los seguimientos diferidos deben conservar su temporalidad en el nombre (`D+2`, `D+3`, `D+5`, `D+10m`).
- En la sesion actual no se modifico logica, acciones, condiciones, responsables ni campos; solo nombres visibles.
- Nota de control actualizada: `Propuesta financiera` fue revisada sin robots visibles; `Generacion de recibo SOLART`, `Envio Email automatico acelerador`, `Abrio Email (Acelerador)` y `Recuperada` quedaron aplicadas y guardadas visualmente en Bitrix24.
- Siguiente bloque recomendado: revisar si quedan automatizaciones ocultas o etapas adicionales en `PROCESO DE VENTA`; despues continuar con el pipeline `PROCESO DE CIERRE`.
