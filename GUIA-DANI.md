# Guía para Dani: operar el portal y Bitrix con Claude Code

Con esto puedes hacer lo mismo que Luis desde su sesión: cambiar las páginas de `app.solart.mx`,
consultar y mover cosas en Bitrix, regenerar la base comercial y publicar.

## 1. Lo que necesitas instalado (una sola vez)

1. **Claude Code (app de escritorio)** con tu cuenta del equipo SOLART en Claude Team.
   Descarga: https://claude.ai/download. No uses la versión web (claude.ai/code) para publicar:
   ahí el push da error 403 salvo que Luis instale la app de Claude en GitHub.
2. **Git** (ya lo tienes con GitHub Desktop). Inicia sesión en GitHub Desktop con tu usuario
   `danielgonzalez-ui` y acepta la invitación al repo `luisamor-sys/solart`
   (te llegó por correo; también en https://github.com/luisamor-sys/solart/invitations).
3. **Python 3.10 o más nuevo** desde https://www.python.org/downloads/ (marca "Add python to PATH").
   Luego, en una terminal: `pip install openpyxl matplotlib python-pptx` (solo hacen falta para
   regenerar la base y el panorama; para consultar Bitrix no necesitas nada extra).

## 2. Clonar el repo (fuera de OneDrive)

OneDrive y git se pelean (archivos bloqueados, cambios a medias). Clona en una carpeta normal:

```
git clone https://github.com/luisamor-sys/solart.git C:\Proyectos\solart
```

Abre esa carpeta en Claude Code. Claude lee `CLAUDE.md` automáticamente: ahí está todo el
contexto (equipo, campos de Bitrix, reglas de nomenclatura, criterios de selección de leads,
flujo de publicación, asistente `solart.py`). No hace falta explicarle nada más.

## 3. Cómo se publica un cambio en el portal

El portal son archivos HTML en la raíz del repo (`front-*.html`). GitHub Pages publica lo que hay
en la rama `main`; el borde tarda 1 a 2 minutos en refrescar.

Flujo que sigue Claude (pídeselo así: "cambia X en el dashboard y publícalo"):

1. Edita el archivo.
2. Valida la sintaxis del JavaScript.
3. `git add` + `git commit` + `git push origin main`.
4. Espera 1–2 minutos y abre `https://app.solart.mx/front-xxx.html?v=123` para verificar.

Si el push falla por credenciales, abre GitHub Desktop una vez (él guarda tu sesión de GitHub
y git la reutiliza).

## 4. Bitrix: consultar y operar por chat

El asistente `solart.py` ya trae los webhooks de Bitrix (los mismos que usan las páginas del
portal). Pide las cosas en lenguaje natural y Claude corre el comando adecuado:

| Pregunta | Comando que corre Claude |
|---|---|
| ¿Qué hizo Samuel hoy? | `python solart.py actividad --vendedor samuel --dias 1` |
| Dame los 30 proyectos más viables | `python solart.py viables --top 30` |
| ¿Cómo va la negociación de Rodin? | `python solart.py negociacion --buscar rodin` |
| Mete al cliente X como lead de Christian | `python solart.py cliente "X" --por dani ...` |
| Mueve el deal 334 a propuesta formal | `python solart.py mover --deal 334 --etapa "5_Propuesta Formal" --por dani` |

Regla del equipo: las **lecturas** se ejecutan directo; las **escrituras** (crear cliente,
mover etapa) primero te muestran el plan y solo se ejecutan cuando dices "sí" (Claude agrega
`--confirmar`). Siempre lleva `--por <tu nombre>` para que quede registrado quién lo hizo.

Para cualquier otra operación de Bitrix (tareas, archivos, campos), Claude usa el REST API con
los webhooks que están en `CLAUDE.md`; pídeselo y te muestra el plan antes de escribir.

## 5. Regenerar la base comercial (opcional)

`consolidado.json` ya viene en el repo, así que el dashboard de la base comercial funciona sin
regenerar nada. Si quieres actualizarlo con Bitrix vivo:

```
python consolidar_bbdd.py "C:\ruta\al\respaldo\Pipedrive"
python consolidar_monday.py "C:\ruta\al\respaldo\Monday\monday-backup-20260602-044158"
python detectar_duplicados.py
```

Los respaldos de Pipedrive y Monday no están en el repo (pídeselos a Luis por OneDrive).
También puedes fijar las rutas una vez con las variables de entorno `SOLART_PIPEDRIVE` y
`SOLART_MONDAY`. Después haz push de los `.json` que cambiaron.

El consolidado de OneDrive (`consolidado-unico.json`) se genera con los scripts PowerShell
`extraer_propuestas.ps1`, `extraer_excels.ps1` y `consolidar_unico.ps1` en la compu que tiene la
carpeta de OneDrive sincronizada.

## 6. Lo que Claude en tu compu NO sabe de Luis

La memoria personal de Claude vive en cada computadora. Todo lo acordado con Luis está en
`CLAUDE.md`; si acuerdas una regla nueva, pídele a Claude que la escriba en `CLAUDE.md` y haz
push para que todos la tengan.

## 7. Buenas prácticas

- Un cambio a la vez y verifica en vivo antes de avisar que está listo.
- No pongas llaves ni contraseñas nuevas en archivos del repo; los webhooks que ya están ahí son
  los del equipo y se renuevan desde Bitrix si hace falta.
- Si algo sale mal en el portal: `git revert HEAD` y push regresa la versión anterior.
