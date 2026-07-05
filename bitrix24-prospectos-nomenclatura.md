# SOLART - Paso 1: nomenclatura de automatizaciones en Bitrix24

## Objetivo

Ordenar las automatizaciones existentes sin cambiar su logica. Cada robot se conserva porque responde a un caso especifico; el problema actual es que muchos nombres vienen de copias y no explican el proposito real.

## Convencion recomendada

Formato:

`TIPO | Etapa o caso | Accion concreta`

Tipos:

- `SYS`: sistema, normalizacion o campos internos.
- `DATA`: limpieza, origen, estrategia o clasificacion.
- `ASIG`: cambio de responsable.
- `OBS`: observadores.
- `TASK`: tareas o actividades.
- `SEG`: seguimiento, recordatorio o escalamiento.
- `MSG`: comentario o mensaje interno.
- `DOC`: documentos o informacion requerida.
- `TUNEL`: mover, copiar o crear elementos en otro pipeline.

Reglas:

- Evitar nombres genericos como `(copia)`, `(copia)(copia)` o `Modificar elemento`.
- Incluir el caso cuando la regla dependa de una condicion.
- Incluir el plazo si es una regla diferida: `D+2`, `D+5`, `D+10`.
- Incluir responsable destino solo cuando sea relevante para auditoria.
- No renombrar para "embellecer"; renombrar para que otra persona entienda que hace y cuando aplica.

## Inventario inicial - Pipeline Prospectos

### Confirmar Datos (Etapa estrategica)

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Modificar elemento | `SYS | Estrategica | Usuario a asignar = responsable` | Aplicado en Bitrix. Actualiza el campo "Usuario a asignar" con la persona responsable. |
| Cambiar observadores | `OBS | Estrategica | Agregar usuario si observadores vacio` | Aplicado en Bitrix. Condicion: Observadores vacio. Accion: agregar "Usuario a asignar" como observador. |
| Cambiar observadores (copia) | `OBS | Estrategica | Agregar usuario si observadores no vacio` | Aplicado en Bitrix. Condicion: Observadores no vacio. Accion: agregar "Usuario a asignar" como observador. |
| Cambiar persona responsable | `ASIG | Estrategica | Responsable Adriana Madrid` | Aplicado en Bitrix. Regla posterior a observadores; cambia responsable a Adriana Madrid. |
| Trabajado por estrategica | `DATA | Estrategica | Marcar trabajado por estrategica` | Aplicado en Bitrix. Marca el prospecto como trabajado por estrategica para trazabilidad. |

### Datos por confirmar

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) | `SYS | Datos por confirmar | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Trabajado por estrategica (copia) | `DATA | Datos por confirmar | Marcar trabajado por estrategica` | Aplicado en Bitrix. Marca el prospecto como trabajado por estrategica para trazabilidad. |
| Borra origen | `DATA | Datos por confirmar | Limpiar origen segun caso` | Aplicado en Bitrix. Mantener en observacion para confirmar que no afecte atribucion historica. |

### Lograr primer contacto

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) (copia) | `SYS | Primer contacto | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Trabajado por estrategica (copia) (copia) | `DATA | Primer contacto | Marcar trabajado por estrategica` | Aplicado en Bitrix. Marca el prospecto como trabajado por estrategica para trazabilidad. |
| Borra origen (copia) | `DATA | Primer contacto | Limpiar origen segun caso` | Aplicado en Bitrix. Mantener en observacion para confirmar condicion exacta. |

### Datos confirmados

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) (copia) (copia) | `SYS | Datos confirmados | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Trabajado por estrategica (copia) (copia) | `DATA | Datos confirmados | Marcar trabajado por estrategica` | Aplicado en Bitrix. Marca el prospecto como trabajado por estrategica para trazabilidad. |
| Borra origen (copia) | `DATA | Datos confirmados | Limpiar origen segun caso` | Aplicado en Bitrix. Mantener en observacion para confirmar condicion exacta. |

### E1 - Contacto Inicial

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto | `SYS | Contacto inicial | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Cambiar persona responsable (copia) (copia) | `ASIG | Contacto inicial | Responsable segun usuario a asignar` | Aplicado en Bitrix. Condicion basada en usuario a asignar. |
| Cambiar observadores (Adri) | `OBS | Contacto inicial | Observadores Adri` | Aplicado en Bitrix. Caso Adri. |
| Borra origen (copia) | `DATA | Contacto inicial | Limpiar origen segun caso` | Aplicado en Bitrix. Mantener en observacion para confirmar condicion exacta. |

### E1 - Presentacion de Credenciales

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) | `SYS | Credenciales | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Generacion de CV SOLART | `TASK | Credenciales | Generar CV SOLART` | Aplicado en Bitrix. Actividad para persona responsable. |
| Agendar sesion de presentacion de CV | `TASK | Credenciales | Agendar presentacion CV` | Aplicado en Bitrix. Actividad para persona responsable. |
| Modificar elemento | `SYS | Credenciales | Actualizar campos de control` | Aplicado en Bitrix. Confirmar campos exactos modificados. |
| Cambiar persona responsable (copia) | `ASIG | Credenciales | Responsable segun usuario a asignar` | Aplicado en Bitrix. Condicion basada en usuario a asignar. |
| Cambiar observadores (Adri) (copia) | `OBS | Credenciales | Observadores Adri` | Aplicado en Bitrix. Caso Adri. |
| Borra origen (copia) (copia) | `DATA | Credenciales | Limpiar origen segun caso` | Aplicado en Bitrix. Mantener en observacion para confirmar condicion exacta. |

### En espera de RECIBO LUZ

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) (copia) | `SYS | Espera recibo | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Seguimiento Notificacion | `SEG | Espera recibo | Notificar inmediato` | Aplicado en Bitrix. Para persona responsable. |
| Seguimiento Notificacion | `SEG | Espera recibo | Recordatorio D+2` | Aplicado en Bitrix. Regla a 2 dias por condicion. |
| Seguimiento Notificacion | `SEG | Espera recibo | Recordatorio D+5` | Aplicado en Bitrix. Regla a 5 dias por condicion. |
| Seguimiento Notificacion a supervisor | `SEG | Espera recibo | Escalar D+10 a Daniel` | Aplicado en Bitrix. Escalamiento a Daniel Gonzalez. |
| Cambiar persona responsable (copia) (copia) | `ASIG | Espera recibo | Responsable segun usuario a asignar` | Aplicado en Bitrix. Condicion basada en usuario a asignar. |
| Cambiar observadores (Adri) (copia) | `OBS | Espera recibo | Observadores Adri` | Aplicado en Bitrix. Caso Adri. |
| Borra origen (copia) (copia) (copia) | `DATA | Espera recibo | Limpiar origen segun caso` | Aplicado en Bitrix. Mantener en observacion para confirmar condicion exacta. |

### Recibos Obtenidos SOLO ADRI

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) (copia) (copia) | `SYS | Recibo obtenido Adri | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |
| Cambiar persona responsable (copia) (copia) (copia) | `ASIG | Recibo obtenido Adri | Responsable segun usuario a asignar` | Aplicado en Bitrix. Condicion basada en usuario a asignar. |
| Cambiar observadores (Adri) (copia) (copia) | `OBS | Recibo obtenido Adri | Observadores Adri` | Aplicado en Bitrix. Caso Adri. |

### E2 - Obtencion de Recibo

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Generacion de nombre de prospecto (copia) (copia) (copia) (copia) | `SYS | Obtencion de recibo | Generar nombre prospecto` | Aplicado en Bitrix. Normaliza el nombre del prospecto en esta etapa. |

### Prospecto no util

| Nombre actual | Nombre propuesto | Nota operativa |
| --- | --- | --- |
| Cambiar persona responsable (copia) (copia) | `ASIG | No util | Responsable segun usuario a asignar` | Aplicado en Bitrix. Condicion basada en usuario a asignar. |
| Agregar un comentario al elemento | `MSG | No util | Registrar comentario automatico` | Aplicado en Bitrix. Documentar texto del comentario. |
| Enviar un mensaje directo al empleado | `MSG | No util | Avisar empleado responsable` | Aplicado en Bitrix. Documentar destinatario y mensaje. |
| Cambiar observadores (Adri) (copia) (copia) (copia) | `OBS | No util | Observadores Adri` | Aplicado en Bitrix. Caso Adri. |

## Siguiente paso recomendado

1. Completar la columna "Nota operativa" con la condicion real en los robots que aun dicen confirmar/documentar.
2. Repetir el mismo inventario para Negociacion, Cierre, Instalacion, Entrega Final, Servicio Posventa y Mantenimientos.
