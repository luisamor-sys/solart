# SOLART - Nomenclatura de automatizaciones Bitrix24: Cierre

## Objetivo

Ordenar las automatizaciones del pipeline `PROCESO DE CIERRE` sin modificar logica, condiciones, acciones, responsables ni campos. El trabajo consiste en cambiar nombres visibles para que cada robot sea auditable por Comercial, CRM, Direccion y Operaciones.

## Estado de avance

- `9_SI VERBAL (Cierre)`: revisada; sin robots visibles en la vista actual.
- `10_Generacion y obtencion de documentos para contrato`: aplicado y guardado en Bitrix24.
- `11_Firma de Contrato`: revisada; sin robots visibles en la vista actual.
- `Espera anticipo`: revisada; sin robots visibles en la vista actual.
- `Anticipo PAGADO`: aplicado y guardado en Bitrix24.
- `Cerrado Perdido`: revisada; sin robots visibles en la vista actual.

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

## Pipeline Cierre

### 9_SI VERBAL (Cierre)

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### 10_Generacion y obtencion de documentos para contrato

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Planificar actividad | `TASK | Docs contrato | Planificar actividad responsable` | Aplicado en Bitrix |
| Tarea checklist documentos contrato | `TASK | Docs contrato | Checklist documentos Eduardo` | Aplicado en Bitrix |

### 11_Firma de Contrato

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### Espera anticipo

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

### Anticipo PAGADO

| Nombre anterior | Nombre nuevo | Estado |
| --- | --- | --- |
| Mover negociacion | `TUNEL | Anticipo pagado | Mover negociacion` | Aplicado en Bitrix |

### Cerrado Perdido

Estado: revisada en Bitrix24; sin robots visibles en la vista actual.

## Notas operativas

- No se modifico logica, acciones, condiciones, responsables ni campos; solo nombres visibles.
- El robot de `Anticipo PAGADO` debe mantenerse como control de traspaso operativo posterior al cierre comercial.
- La documentacion contractual queda concentrada en la etapa `10_Generacion y obtencion de documentos para contrato`.
- Siguiente bloque recomendado: continuar con `PROCESO INSTALACION E INTERCONEXION`.
