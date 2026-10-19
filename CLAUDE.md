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

```bash
python3 detectar_duplicados.py   # consolidado.json (+ consolidado-unico.json) → duplicados.json (pares sospechosos)
```

```bash
python3 panorama_exportar.py     # Panorama de propuestas → PDF y PPTX en el Escritorio (matplotlib + python-pptx)
```

**Orden del pipeline de datos:** `consolidar_bbdd.py` → `consolidar_monday.py` → `detectar_duplicados.py` →
(en la máquina Windows con OneDrive) los tres `.ps1` → `git push`. Después de regenerar, `front-consolidado.html`
y `front-panorama.html` leen los JSON nuevos al recargar; no hay nada más que tocar.

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File extraer_propuestas.ps1   # OneDrive: pptx → propuestas-historico.json
powershell -NoProfile -ExecutionPolicy Bypass -File extraer_excels.ps1       # OneDrive: xlsx → excels-historico.json
powershell -NoProfile -ExecutionPolicy Bypass -File consolidar_unico.ps1     # + consolidado.json → consolidado-unico.json
```

Los tres de OneDrive van en ese orden. Leen `~/OneDrive/Comerciales e Industriales` (sincronizada "solo en línea":
**no** marcarla "Siempre disponible", son ~140 GB y llena el disco). Cada archivo se baja al leerlo y se devuelve a la
nube; reanudan por ruta+fecha, así que una segunda corrida solo procesa lo nuevo. `extraer_propuestas.ps1 -SoloRededucir`
re-aplica las reglas de `Deducir` sobre el texto ya guardado sin tocar OneDrive. Los dos `*-historico.json` (materia
prima, 32 y 186 MB) están en `.gitignore`; `consolidado-unico.json` sí se versiona porque `front-consolidado.html` lo
carga y engancha a cada registro por `idCRM`.

No hay tests ni linter. La verificación es manual: abrir la página en el navegador y revisar la consola.
Antes de cada push, valida la sintaxis del `<script>` principal (extraerlo con una regex y pasarlo por
`new Function(...)`; en macOS sirve `osascript -l JavaScript`). Un HTML con error de sintaxis deja la página en blanco
para todo el equipo.

**Caché de borde:** GitHub Pages sirve con `max-age=600`. Tras un push, verifica con
`curl -s "https://app.solart.mx/<archivo>?nc=$RANDOM" | grep <marcador nuevo>` antes de probar en el navegador, y
navega con un query string fresco (`?v=<timestamp>`); el navegador puede seguir sirviendo la versión vieja aunque el
borde ya tenga la nueva. Si el push "se cuelga", casi siempre es porque `git add -A` arrastró una carpeta pesada
(`tmp/`, `output/` están en `.gitignore` por eso): revisa `git diff --stat origin/main..main` antes de empujar.

**Trabajo en equipo (varias personas y sesiones de Claude sobre este repo):**
- `git pull` siempre antes de empezar; commits chicos; un push a `main` es producción en 1–2 minutos.
- Los JSON de datos (`consolidado*.json`, `duplicados.json`, `datos-propuesta.json`) los regenera **una sola persona**;
  no se editan a mano y chocan feo en git si dos los tocan.
- Cambios grandes en un front van en rama y se unen ya probados; ajustes chicos directo a `main`.
- Credenciales de GitHub: cada quien con su cuenta. Nunca pegar tokens en el remoto ni en archivos del repo.
- La memoria de Claude Code (`~/.claude/projects/.../memory`) es por máquina: lo que deba saber todo el equipo va aquí.

Advertencias de entorno en macOS: no hay `node`, `soffice` ni PowerPoint; `python3` es el 3.9 de Xcode (sin
`match`), con `openpyxl`, `matplotlib`, `python-pptx`, `pdfplumber` instalados vía pip. Keynote no abre los `.pptx`
generados con python-pptx: para entregables usa `panorama_exportar.py` (PDF + PPTX de imágenes).

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
| `UF_CRM_1758675881434` | Ahorro mensual CON SOLART, MXN (se escribe como `"<monto>|MXN"`) |
| `UF_CRM_67A2ED1D84E1E` | Monto del recibo CFE (`"<monto>|MXN"`) |
| `UF_CRM_1743795019024` | Tipo de proyecto, selección múltiple: `312` FOTOVOLTAICO, `310` BESS, `336` Suministro Calificado, `526` MANTENIMIENTO |
| `OPPORTUNITY` | Total de la propuesta (lo mantiene el vendedor); `CURRENCY_ID` MXN o USD |

**Nomenclatura del título del deal:** `TIPO_Contacto_Empresa_Vendedor_<kWp>kWp_Proyecto` (el tipo y el kWp pueden
faltar). Para sacar empresa/proyecto del título descarta primero las piezas que son tipo, nombre de vendedor o kWp
(`empresaYProyecto()` en front-negociaciones, `empresa_bitrix()` en consolidar_bbdd.py); si no, se toma al contacto
por empresa. La empresa buena es la **compañía ligada** (`COMPANY_ID` → `crm.company.list`), que el listado de deals no
trae por nombre.

**Paginación del REST:** `crm.deal.list` sin `order` fijo devuelve páginas inestables (repite unos registros y omite
otros). Pide siempre `order: {ID: 'ASC'}` y deduplica por ID (`bx_all` en consolidar_bbdd.py).

**Usuarios clave (ID Bitrix):** Luis Amor 12 (dueño de los webhooks), Daniel González 8 (BESS, aprobador),
Javier Olmos 36 (ingeniería, flujo normal), Gerardo Vite 86 (subtareas `Ing_`), Arturo Chávez 34 (subtareas `Op_`,
entrega las infografías), Carlos Mariscal 40 (visitas técnicas), Samantha Miranda 390 (financiero y suministro
calificado; sustituyó a Erick 344), Victor Linaldi 158 (CEO), Arturo López Gallo 188 (director comercial).
Vendedores: Christian 44, Samuel 48, Alberto 296 (inactivo, su cartera pasó a Arturo López), Moises 356 (heredó la de
Rafael de la Cuadra 46). Grupo de tareas del flujo de ingeniería: `GROUP_ID 16`; subtareas en grupos 22 (Ing) y 24 (Op).

**Reparto de tareas por tipo de proyecto** (`ejecutarTarea` en front-negociaciones): FOTOVOLTAICO y MANTENIMIENTO →
Javier 36; BESS → Daniel 8; Suministro Calificado → Samantha 390. Si el deal trae varios tipos se crea **una tarea por
tipo** (título prefijado `BESS_…`, `SUMINISTRO CALIFICADO_…`), todas en el grupo 16 y ligadas al deal. La visita técnica
sigue siendo una sola tarea (Carlos 40). Red de seguridad `corregirRuteoTareas`: una tarea del flujo que caiga
vendedor→vendedor se reasigna a 36 con `GROUP_ID 16`.

### Dos límites del API de Bitrix que explican mucho del código

1. **Los comentarios de tareas no se pueden leer por API.** Por eso todo lo que la app comenta se duplica
   dentro de la *descripción* de la tarea, delimitado con marcadores `===BITACORA===`, `===DEPENDENCIA===`,
   `===APROBADA===`, `===DATO_VENDEDOR===`. Esos bloques son el canal real entre fronts
   (p. ej. ingeniería marca `===APROBADA===` y la app del vendedor lo lee para mostrar los PDFs).
   Al tocarlos, usa los helpers que ya existen (`rxMarca`, `parseBitacora`) y conserva el formato.
   Formato de `===BITACORA===`: una línea por entrada `YYYY-MM-DD HH:MM|Autor|texto` (saltos de línea como `⏎`,
   `|` como `¦`, máximo 40 entradas). En front-ingenieria la única puerta es `bx()`: todo `task.commentitem.add`
   anota en la bitácora; se lee con `leerComentarios()`. En front-dashboard: `comentarTarea`/`comentariosTarea`;
   en front-negociaciones: `seccionSeguimiento()`. Lo escrito directo en Bitrix sigue siendo invisible para la app.
2. **Adjuntar un archivo a una tarea exige el prefijo `n`**: `UF_TASK_WEBDAV_FILES: [...existentes, 'n' + fileId]`,
   y hay que releer los existentes primero o se borran. Los PDF entregables viven en la **subtarea de Arturo**
   (`Op_…`) y los insumos en la de Gerardo (`Ing_…`): las vistas de archivos deben leer la tarea **y sus subtareas**
   (`archivosDeTarea`, `cargarArchivosTask`). Lecturas de `disk.*` solo con el webhook técnico (`1hh732…`); el
   general no tiene scope `disk`.

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
Paridad verificada con recibos reales (Vanplastic: 669.51 kWp, ahorro $3,551,862, precio $8,905,334.43). Trampa
corregida en ambos lados: en tarifa **GDMTO** la energía se publica bajo la clave `NA`, no `B/I/P`; sin ese caso el
recibo salía a la mitad. Lo que no es portable: el parser de PDF (pdfplumber) y la infografía PPTX; en la app el
asesor captura el recibo a mano y la propuesta se genera como HTML imprimible. `front-propuesta.html` precarga del
deal (`?dealId=`), mapea estado → ciudad de radiación (32 ciudades medidas; marca "aproximada" cuando no hay), y al
guardar escribe en el deal OPPORTUNITY, kWp, % energía, ROI, ahorro mensual y monto del recibo, que son los mismos
campos que precarga `front-recibo.html`.

`front-recibo.html` (recibo simulado + flyer + imagen del dólar): el PDF se genera con html2canvas + jsPDF a 750 px
de ancho fijo (la impresión nativa salía en blanco en iPhone) y deja un enlace de descarga visible porque Chrome
bloquea descargas que tardan más que el clic. Los montos de Bitrix traen centavos: redondear antes de `fmtDinero`,
que borra todo lo que no es dígito.

Sus datos de entrada están en `datos-propuesta.json` (tarifas CNE por división/mes, HSP, perfiles mensuales,
factor de carga) y se inyectan con `MotorSolar.cargarDatos(DATOS)`. Los JSON se versionan con query string
(`?v=3`) para saltarse el caché de GitHub Pages — súbela cuando cambien.

### Consolidado comercial

`consolidar_bbdd.py` y `consolidar_monday.py` generan `consolidado.json`, que `front-consolidado.html` lee
como archivo estático (no hay API). Los tres CRMs históricos (Bitrix, Pipedrive, Monday) se cruzan por nombre
de empresa normalizado; Monday no crea duplicados: se cuelga como bloque `monday` del registro existente.
`consolidar_monday.py` **reconstruye** los registros de origen Monday, así que es idempotente, pero depende de
que `consolidar_bbdd.py` haya corrido antes.

Campos por registro que usan los fronts: `origen` (bitrix / pipedrive / monday / onedrive), `estado`
(abierto / ganado / perdido), `pipeline` y `etapa` (nombres reales), `tipo` (lista: FV, SC, BESS, MANT; de Bitrix sale
del campo de tipo, en Pipedrive/Monday se infiere por siglas y casi siempre viene vacío), `dueno` y
`duenosAnteriores` (creador del deal + nombre de vendedor que quedó en el título; Bitrix no guarda historial de
reasignaciones), `enBitrix` (registro de Pipedrive cuyo cliente ya existe en Bitrix: se cuenta una sola vez),
`monday` (bloque comparativo), `completitud` (0–10), `precioUSD` (los de Pipedrive en MXN se convierten a 17.22; los
campos "USD" del export de Pipedrive **mienten**: traen la moneda original).

**OneDrive (`consolidado-unico.json`, lo genera la máquina Windows):** se engancha por `idCRM` como `r.od`. Sus campos
sueltos (`od.kwp`, `od.precioUSD`, `od.pctEnergia`) traen **copiado el valor del CRM**; lo puro de OneDrive está en
`od.propuestas[]` (una entrada por infografía leída, con fecha) y en `od.carpeta` (kW del nombre de la subcarpeta
cuando la carpeta no se ha descargado). `odDatos(r)` elige la infografía más reciente, o la **suma de la última
propuesta de cada sitio** cuando el cliente tiene varios (`01_CLUB / …`, `02_Carcamo / …`), y rellena kW/% desde
una propuesta anterior si a la última no se le pudieron leer. Las columnas principales muestran solo el CRM: no se
rellenan huecos desde OneDrive.

**Reglas de la base comercial (`front-consolidado.html`):**
- *Prioridad* = ≥150 kWp y (% energía ≥50 o vacío), sin importar el estado; dato dudoso (kWp >20,000 o precio
  >$100 M MXN) queda fuera de prioridades y de las sumas. Cuatro clases excluyentes por el primer dato faltante:
  contacto → % energía → precio (precio real = ≥1,000 USD; `$1 MXN` es relleno). Subfiltro "Con datos en OneDrive"
  acota; las cuatro clases se suman entre sí.
- *⭐ Selección de leads (híbrido)*: eliminatorios (abierto, sin dato dudoso, con tel/correo, ≤180 días sin contacto,
  ≥150 kWp, precio real o propuesta) y puntaje etapa 35 % · recencia 20 % · valor USD 15 % (tope 600k) · retorno 15 % ·
  cobertura 10 % · propuestas OneDrive 5 % (`seleccionDe()`). Al marcarlo ordena por score.
- *Posibles duplicados* (`duplicados.json`): señales con peso RPU 5, carpeta OneDrive 4, teléfono 4, correo 4, USD
  exacto 3, nombre normalizado 3, nombre contenido 2, kWp exacto + vendedor 2, contacto 2, "cascarón" 2, fechas
  cercanas 1; alta ≥4, media ≥2. Si los dos registros tienen tipos de proyecto distintos (FV vs SC vs BESS) no es
  duplicado: se clasifica solo como "mismo cliente, otro servicio". Las decisiones (`mismo` / `otro` / `distinto`) se
  guardan en `localStorage.dup_decisiones` del navegador de quien decide (pendiente: moverlas a un archivo compartido);
  el registro descartado de un duplicado confirmado entra a `DUP_OCULTOS` y deja de contarse.
- Capacidad se etiqueta **kWp** en toda la base. Filtros laterales con conteos vivos (patrón de buscador de vuelos):
  origen, estado, tipo, especiales, embudo, etapa, vendedor (con buscador), rangos.

`front-panorama.html` es la lámina de dirección: pastel del universo de clientes con propuesta (estado según CRM),
propuestas por cliente, valor (última propuesta por sitio) y kW; calcula todo en vivo desde los mismos JSON.
`panorama_exportar.py` produce la misma lámina en PDF/PPTX.

### Mi día (front-dashboard) y panel directivo (front-ingenieria)

Embudo de 6 niveles acumulativos (Clientes → Con recibo → Propuesta presentada → Visita técnica → En cierre →
Ganados) con "% que avanzó"; los leads `CONVERTED`/`JUNK` no se cuentan para no duplicar con los deals. Filtro
global *Todo / Mío / Heredado* (`esHeredadaG`: el título trae el nombre de **otro** vendedor; se excluye el propio por
ID de usuario, no por texto, porque los títulos traen apellidos que la app no tiene). Prioridades del mes: ≥150 kW o
≥50 % energía, ordenadas por etapa, tamaño y %, lista completa con scroll. Pestañas: Prospectos · Clientes esperando
cierre · Clientes en cierre · Seguimientos con cliente (actividades + tareas del vendedor) · Seguimientos internos
(tareas de ingeniería). Toda sección lleva un glosario ℹ️ de cómo se calcula. Los filtros con `endsWith('WON'/'LOSE')`
cubren los dos pipelines (`WON` y `C2:WON`). Fechas de tarea `9999-12-31` se muestran como "sin fecha límite".

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

## Asistente conversacional sobre Bitrix (`solart.py`)

Cuando alguien pregunte en lenguaje natural por actividad de vendedores, proyectos viables, datos de una negociación,
o pida crear un cliente o mover una etapa, **usa `python3 solart.py`** en vez de improvisar llamadas al API:

```bash
python3 solart.py actividad --vendedor samuel [--fecha 2026-10-19 | --dias 7]   # qué hizo (etapas, prospectos, llamadas, comentarios, tareas)
python3 solart.py viables [--top 20] [--vendedor christian] [--detalle]        # selección ⭐ con datos vivos de Bitrix
python3 solart.py negociacion --buscar "grupo dafna"                           # ficha de una negociación
python3 solart.py cliente --empresa "X" --contacto "Nombre Apellido" --tel ... --email ... --vendedor samuel --tipo FV [--como negociacion] --por dani
python3 solart.py mover --deal 724 --etapa "Propuesta Formal" --por dani [--justificacion "..."]
python3 solart.py etapas
```

Reglas:
- **Lecturas** (`actividad`, `viables`, `negociacion`, `etapas`): ejecútalas directo y resume el resultado en español; no
  inventes datos que el comando no haya devuelto. Si la persona pregunta "hoy", usa la fecha de hoy; si no hay
  movimiento, dilo tal cual.
- **Escrituras** (`cliente`, `mover`): corre primero el comando **sin** `--confirmar`, muestra el plan a la persona y
  solo si responde que sí lo repites con `--confirmar`. Nunca confirmes por tu cuenta. Pasa siempre `--por <quien pide>`
  para que quede la autoría en el comentario (todo corre con el webhook de Luis, id 12). Marcar PERDIDA exige
  `--justificacion`.
- Un cliente nuevo entra como **prospecto** (lead) salvo que pidan explícitamente negociación (`--como negociacion`:
  crea compañía + contacto + deal en 1_Generación de propuesta). Los robots de Bitrix reasignan lo recién creado; el
  script vuelve a asignar al vendedor y lo verifica.
- Las fechas de Bitrix vienen en `+03:00`; `actividad` ya lo contempla. Las actividades creadas desde la app tienen
  `AUTHOR_ID 12` y `RESPONSIBLE_ID` del vendedor: el comando busca por ambos.
- Este script es la base de la fase 2 (conector MCP para Claude Team): si agregas comandos, mantén la misma forma
  (lectura directa / escritura con `--confirmar`).

## Pendientes conocidos

- Proxy de IA sin desplegar (falta tarjeta/RFC para la llave de Anthropic).
- Robot BESS de Bitrix crea tareas vendedor→vendedor; la app lo corrige, pero el robot sigue mal (arreglo manual en Bitrix).
- Decisiones de duplicados y de ⭐ viven en el navegador: pasarlas a un archivo compartido cuando haya equipo.
- Datos mal capturados en Bitrix que ensucian totales: Camino Real SC (deal 488, kWp y monto imposibles), 38 deals con
  precio `$1 MXN`, retorno vacío en la mayoría de los deals con propuesta.
- Los webhooks son públicos en el HTML: al crecer el equipo, moverlos detrás de un proxy.
- Rodamex ↔ Tanques Menher: la carpeta "Rodamex - Tanques Menher" quedó enganchada a Tanques Menher; confirmar si son el
  mismo cliente.
