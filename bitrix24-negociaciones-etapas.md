# SOLART - Nomenclatura de etapas Bitrix24: Negociaciones

## Objetivo

Ordenar las etapas del pipeline `PROCESO DE VENTA` con prefijos numericos para que los reportes, filtros, vistas Kanban y conversaciones comerciales sigan el flujo real de venta.

## Regla de cambio

Cambiar unicamente la etiqueta visible de la etapa. No modificar automatizaciones, condiciones, acciones, responsables, campos, tuneles, tareas, integraciones ni reglas de negocio.

## Estado

Lista para aplicar en Bitrix24. La ejecucion requiere tener al frente la ventana correcta de Bitrix24 en `Listas de seleccion > PROCESO DE VENTA estado de la negociacion`.

## Mapeo de etapas

| Orden | Nombre anterior | Nombre nuevo |
| --- | --- | --- |
| 01 | `1_Generacion de propuesta` | `01_Generacion propuesta` |
| 02 | `2_Propuesta Preliminar` | `02_Propuesta preliminar` |
| 03 | `3_Se agendo/presento propuesta inicial` | `03_Presentacion inicial` |
| 04 | `4_Visita Tecnica` | `04_Visita tecnica` |
| 05 | `5_Propuesta Formal` | `05_Propuesta formal` |
| 06 | `6_Evaluacion Interna` | `06_Evaluacion interna` |
| 07 | `7_Propuesta Final (SI VERBAL)` | `07_Propuesta final SI verbal` |
| 08 | `Propuesta financiera` | `08_Propuesta financiera` |
| 09 | `Generacion de recibo SOLART` | `09_Generacion recibo SOLART` |
| 10 | `Envio Email automatico acelerador` | `10_Envio email acelerador` |
| 11 | `Abrio Email (Acelerador)` | `11_Abrio email acelerador` |
| 12 | `Recuperada` | `12_Recuperada` |
| 13 | `8_Si Verbal` | `13_Si verbal` |
| 99 | `Cerrado Perdido` | `99_Cerrado perdido` |

## Criterios de validacion

- El Kanban de Negociaciones debe mostrar las etapas en orden ascendente por prefijo.
- Las automatizaciones deben seguir visibles y activas despues del cambio.
- No deben modificarse robots, condiciones, acciones, responsables ni campos.
- Los dashboards deben poder ordenar las etapas por nombre de forma consistente.

## Nota operativa

El prefijo `13_Si verbal` conserva la funcion de disparador hacia cierre, pero elimina la ambiguedad de tener una etapa avanzada nombrada como `8_Si Verbal`.
