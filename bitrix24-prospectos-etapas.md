# Bitrix24 - Prospectos - Nomenclatura de etapas

Fecha de trabajo: 30 de mayo de 2026

Objetivo: renombrar las etapas de Prospectos con prefijos numericos para que reportes, filtros y vistas se ordenen en la secuencia comercial correcta.

Alcance: cambio de etiquetas visibles de etapas. No se modifican automatizaciones, condiciones, responsables, campos, tareas, tuneles ni integraciones.

## Nomenclatura aplicada

| Orden | Nombre anterior | Nombre nuevo |
| --- | --- | --- |
| 00 | Confirmar Datos (Etapa estrategica) | `00_Validacion estrategica` |
| 01 | Datos por confirmar | `01_Datos por confirmar` |
| 02 | Lograr primer contacto | `02_Primer contacto pendiente` |
| 03 | Datos confirmados | `03_Datos confirmados` |
| 04 | E1 - Contacto Inicial | `04_Contacto comercial inicial` |
| 05 | E1 - Presentacion de Credenciales | `05_Credenciales presentadas` |
| 06 | En espera de RECIBO LUZ | `06_Espera recibo CFE` |
| 07 | Recibos Obtenidos SOLO ADRI | `07_Recibo recibido Adri` |
| 08 | E2 - Obtencion de Recibo | `08_Recibo validado` |
| 99 | Prospecto no util | `99_Prospecto no util` |

## Criterio de nomenclatura

- `00`: etapa previa o excepcional de validacion estrategica.
- `01` a `08`: avance comercial normal del prospecto.
- `99`: salida fallida o no util para mantenerla al final en reportes.

## Reglas

- Mantener dos digitos en el prefijo.
- Usar nombres comerciales claros y accionables.
- Evitar acentos en nombres tecnicos de etapa para reducir friccion en filtros, exportaciones e integraciones.
- No cambiar nombres de etapas sin revisar automatizaciones, reportes, dashboards e integraciones dependientes.
