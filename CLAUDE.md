# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> El código, los comentarios y la documentación de este repo están en español. Mantén ese idioma al editar.

## Qué es esto

Conjunto de apps web para el equipo comercial y de ingeniería de SOLART (energía solar, México).
No hay build, ni framework, ni dependencias de npm: **cada `front-*.html` es una app completa y autónoma**
(HTML + CSS + JS en el mismo archivo, sin `<script src>` salvo `motor-propuesta.js` en front-propuesta).

Se publica tal cual con GitHub Pages en **https://app.solart.mx** (`CNAME` + `.nojekyll`).
Desplegar = `git push` a `main`. No hay staging: lo que se sube está en producción para el equipo.

## Comandos

```bash
python3 -m http.server 3456    # servidor local (también en .claude/launch.json como "front-solart")
```

```bash
python3 consolidar_bbdd.py     # Bitrix (API) + respaldo Pipedrive (xlsx) → consolidado.json
```

```bash
python3 consolidar_monday.py [ruta_respaldo]   # suma Monday a consolidado.json (correr DESPUÉS del anterior)
```

No hay tests ni linter. La verificación es manual: abrir la página en el navegador y revisar la consola.

Advertencias de entorno en esta máquina Windows: `git` y `python` no están en el PATH del shell, y los scripts
de consolidación traen rutas hardcodeadas de macOS (`/Users/luisamor/...`) que hay que ajustar antes de correrlos.
`consolidar_bbdd.py` también requiere `openpyxl`.

## Arquitectura

### Bitrix24 es la base de datos

No hay backend propio. Las apps hablan directo contra el REST de Bitrix24 con un **webhook entrante incrustado
en el HTML** (público, por diseño: la seguridad real vive en los permisos del webhook):

- `https://crm-solart.bitrix24.mx/rest/12/128t1gaxhgz3aoue/` — webhook general (deals, contactos, usuarios).
- `https://crm-solart.bitrix24.mx/rest/12/1hh732gngri1wfwt/` — webhook de `front-ingenieria.html` (tareas, `PROJECT_ID = 16`).

Cada front define su propio helper `bx(endpoint, params)` que hace `POST WEBHOOK + endpoint` con JSON.
Como todo corre con el usuario 12 (Luis Amor), varias acciones necesitan **reasignar después** lo que las
automatizaciones de Bitrix crean a nombre de 12 (ver `reasignarTareasNuevas` en `front-cambiar-etapa.html`).

Pipelines por `CATEGORY_ID`: `0` = Proceso de Venta, `2` = Proceso de Cierre (sus `STAGE_ID` llevan prefijo `C2:`),
`4` y `6` = pipelines posteriores (se tratan como ganadas). Los nombres de etapa que ve el usuario están
hardcodeados en listas tipo `ETAPAS_DEAL_VENTA` / `ETAPAS_DEAL_CIERRE`; los `STAGE_ID` reales son opacos
(`UC_OF6DF0`, `UC_Y3LUYS`, …). Al agregar una etapa hay que tocar esas listas en cada front que la use.

Los campos personalizados son `UF_CRM_<timestamp>` sin nombre legible. Los recurrentes:

| Campo | Significado |
| --- | --- |
| `UF_CRM_1741392978542` | Nombre del proyecto |
| `UF_CRM_1741208352117` | Tamaño del sistema (kWp) |
| `UF_CRM_1753209254287` | % de energía cubierto |
| `UF_CRM_1758676152864` | Retorno de inversión |
| `UF_CRM_1758675881434` | Ahorro mensual MXN (se escribe como `"<monto>|MXN"`) |

### Dos límites del API de Bitrix que explican mucho del código

1. **Los comentarios de tareas no se pueden leer por API.** Por eso todo lo que la app comenta se duplica
   dentro de la *descripción* de la tarea, delimitado con marcadores `===BITACORA===`, `===DEPENDENCIA===`,
   `===APROBADA===`, `===DATO_VENDEDOR===`. Esos bloques son el canal real entre fronts
   (p. ej. ingeniería marca `===APROBADA===` y la app del vendedor lo lee para mostrar los PDFs).
   Al tocarlos, usa los helpers que ya existen (`rxMarca`, `parseBitacora`) y conserva el formato.
2. **Adjuntar un archivo a una tarea exige el prefijo `n`**: `UF_TASK_WEBDAV_FILES: [...existentes, 'n' + fileId]`,
   y hay que releer los existentes primero o se borran.

### Sesión y navegación

Login con PIN de 4 dígitos contra un mapa `PINES` hardcodeado por ID de usuario de Bitrix; la sesión queda en
`localStorage.solart_user` (`{id, nombre}`). Los fronts se pasan contexto entre sí también por localStorage
(`solart_deal_id_preload`, `solart_neg_preload`, `solart_notif_vistas`). Los enlaces van con URL absoluta a
`https://app.solart.mx/...` y `target="_top"` porque las páginas se embeben en iframes dentro de Bitrix.
`front-ingenieria.html` tiene además su propio mapa `ROLES` (supervisor / ejecutor / aprobador / visitas /
financiero / ceo / comercial) que decide qué se ve.

### Motor de propuestas

`motor-propuesta.js` es un **port a JavaScript** de un paquete Python aparte (`solart-propuestas`, ignorado en
`.gitignore`). Es cálculo puro sin dependencias, expuesto como `window.MotorSolar`. Flujo:
generación (HSP × PR 0.755) → dimensionado (módulo 645 W, ratio DC/AC ≤ 1.35, tope 499 kW AC) →
simulación de factura CFE (12 meses, con y sin solar) → precio (margen que cierra el crédito en ≤72 meses,
con piso de mercado 20/18/17 % por tamaño) → ROI y beneficio fiscal.
Si cambia una regla de negocio aquí, debe cambiar igual en el paquete Python: son dos copias de la misma lógica.

Sus datos de entrada están en `datos-propuesta.json` (tarifas CNE por división/mes, HSP, perfiles mensuales,
factor de carga) y se inyectan con `MotorSolar.cargarDatos(DATOS)`. Los JSON se versionan con query string
(`?v=3`) para saltarse el caché de GitHub Pages — súbela cuando cambien.

### Consolidado comercial

`consolidar_bbdd.py` y `consolidar_monday.py` generan `consolidado.json`, que `front-consolidado.html` lee
como archivo estático (no hay API). Los tres CRMs históricos (Bitrix, Pipedrive, Monday) se cruzan por nombre
de empresa normalizado; Monday no crea duplicados: se cuelga como bloque `monday` del registro existente.
`consolidar_monday.py` **reconstruye** los registros de origen Monday, así que es idempotente, pero depende de
que `consolidar_bbdd.py` haya corrido antes.

### Proxy de IA

`apps-script-resumen-ia.gs` se despliega como Google Apps Script y existe solo para que la llave de Anthropic
no quede en el HTML público. Recibe el historial de una negociación y devuelve un resumen ejecutivo.
La URL `/exec` se pone en `IA_PROXY_URL` de `front-dashboard.html`.

## Documentación operativa (no es código)

Los `.md` y `playbook-solart-v2.html` documentan la configuración del CRM, no el software. La convención de
nombres de automatizaciones de Bitrix es `TIPO | Etapa o caso | Accion concreta` con tipos fijos
(`SYS`, `DATA`, `ASIG`, `OBS`, `TASK`, `SEG`, `MSG`, `DOC`, `TUNEL`), y las etapas llevan prefijo numérico
de dos dígitos. Regla sostenida en todo ese trabajo: **renombrar nunca implica tocar lógica, condiciones,
responsables ni campos.** Los enlaces internos de esos documentos apuntan a rutas macOS viejas
(`/Users/luisamor/Documents/BITRIX_SOLART/`) aunque los archivos ya viven en este repo.
