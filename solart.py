#!/usr/bin/env python3
"""Asistente SOLART por línea de comandos: lee y escribe en Bitrix24 con las reglas del equipo.

Pensado para que Claude lo ejecute cuando alguien pregunta en lenguaje natural. Las LECTURAS
van directo; las ESCRITURAS (cliente nuevo, mover etapa) muestran el plan y solo se ejecutan
con --confirmar, después de que la persona dijo que sí.

  python3 solart.py actividad --vendedor samuel [--fecha 2026-10-19 | --dias 7]
  python3 solart.py viables [--top 20] [--vendedor christian]
  python3 solart.py negociacion --buscar "grupo dafna"
  python3 solart.py cliente --empresa "X SA de CV" --contacto "Juan Pérez" --tel 4421234567 \\
                    --email j@x.com --vendedor samuel --tipo FV [--como negociacion] --por dani [--confirmar]
  python3 solart.py mover --deal 724 --etapa "Propuesta Formal" --por dani [--confirmar]
  python3 solart.py etapas
"""
import argparse, json, os, re, sys, unicodedata, urllib.parse, urllib.request
from datetime import date, datetime, timedelta

WEBHOOK = 'https://crm-solart.bitrix24.mx/rest/12/128t1gaxhgz3aoue/'
WEBHOOK_TAREAS = 'https://crm-solart.bitrix24.mx/rest/12/1hh732gngri1wfwt/'
AQUI = os.path.dirname(os.path.abspath(__file__))

# Personas (ID de Bitrix). Alias en minúsculas y sin acentos.
PERSONAS = {
    'luis': (12, 'Luis Amor'), 'daniel': (8, 'Daniel González'), 'dani': (8, 'Daniel González'),
    'javier': (36, 'Javier Olmos'), 'gerardo': (86, 'Gerardo Vite'), 'arturo chavez': (34, 'Arturo Chávez'),
    'carlos': (40, 'Carlos Mariscal'), 'samantha': (390, 'Samantha Miranda'), 'victor': (158, 'Victor Linaldi'),
    'arturo lopez': (188, 'Arturo López Gallo'), 'arturo': (188, 'Arturo López Gallo'),
    'christian': (44, 'Christian González'), 'samuel': (48, 'Samuel Capuano'), 'alberto': (296, 'Alberto Atilano'),
    'moises': (356, 'Moises Jimenez'), 'rafael': (46, 'Rafael De la cuadra'), 'lilia': (126, 'Lilia Ventura'),
    'erick': (344, 'Erick Hernandez'), 'ulises': (282, 'Ulises Navarro'),
}
VENDEDORES = {44, 48, 296, 356, 188, 126, 282}
TIPO_ID = {'FV': 312, 'FOTOVOLTAICO': 312, 'BESS': 310, 'SC': 336, 'SUMINISTRO': 336, 'MANT': 526, 'MANTENIMIENTO': 526}
TIPO_NOMBRE = {312: 'FOTOVOLTAICO', 310: 'BESS', 336: 'SUMINISTRO CALIFICADO', 526: 'MANTENIMIENTO'}
UF = {'proyecto': 'UF_CRM_1741392978542', 'kwp': 'UF_CRM_1741208352117', 'energia': 'UF_CRM_1753209254287',
      'retorno': 'UF_CRM_1758676152864', 'tipo': 'UF_CRM_1743795019024'}
TZ_BITRIX = '+03:00'


def norm(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').strip().lower()


def bx(metodo, params=None, webhook=WEBHOOK):
    datos = json.dumps(params or {}).encode()
    req = urllib.request.Request(webhook + metodo, data=datos, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if 'error' in out:
        raise SystemExit(f"Bitrix respondió error en {metodo}: {out.get('error_description') or out['error']}")
    return out


def bx_all(metodo, params, webhook=WEBHOOK):
    out, start, vistos = [], 0, set()
    while True:
        r = bx(metodo, {**params, 'order': {'ID': 'ASC'}, 'start': start}, webhook)
        res = r.get('result', [])
        if isinstance(res, dict) and 'tasks' in res:
            res = res['tasks']
        for x in res:
            k = x.get('ID') or x.get('id')
            if k not in vistos:
                vistos.add(k); out.append(x)
        if r.get('next') is None:
            break
        start = r['next']
    return out


def persona(texto):
    """Nombre o alias → (id, nombre). Acepta también un ID numérico."""
    if texto is None:
        return None
    t = norm(texto)
    if t.isdigit():
        uid = int(t)
        for k, (i, n) in PERSONAS.items():
            if i == uid:
                return (i, n)
        return (uid, f'usuario {uid}')
    if t in PERSONAS:
        return PERSONAS[t]
    for k, v in PERSONAS.items():
        if t in norm(v[1]) or norm(v[1]).startswith(t):
            return v
    raise SystemExit(f"No conozco a '{texto}'. Opciones: {', '.join(sorted(set(n for _, n in PERSONAS.values())))}")


def etapas():
    """Nombre legible → STAGE_ID, para los pipelines de venta (0) y cierre (2)."""
    out = {}
    for ent in ('DEAL_STAGE', 'DEAL_STAGE_2'):
        for st in bx('crm.status.list', {'filter': {'ENTITY_ID': ent}}).get('result', []):
            out[st['STATUS_ID']] = st['NAME']
    return out


def etapa_por_nombre(texto, mapa):
    t = norm(texto)
    exacto = [k for k, v in mapa.items() if norm(v) == t or k.lower() == t]
    if exacto:
        return exacto[0]
    parcial = [k for k, v in mapa.items() if t in norm(v)]
    if len(parcial) == 1:
        return parcial[0]
    if not parcial:
        raise SystemExit(f"No hay una etapa que se llame '{texto}'. Usa: python3 solart.py etapas")
    raise SystemExit("Varias etapas coinciden: " + ' | '.join(mapa[k] for k in parcial) + ". Sé más específico.")


_RX_TIPO = re.compile(r'^(FOTOVOLTAICO|BESS|SUMINISTRO( CALIFICADO)?|MANTENIMIENTO|SC|FV|PVT)(\s*,\s*(FOTOVOLTAICO|BESS|SUMINISTRO( CALIFICADO)?|MANTENIMIENTO|SC|FV))*$', re.I)
_RX_KWP = re.compile(r'^\d+([.,]\d+)?\s*kwp?$', re.I)
_NOMBRES = {norm(n) for _, (_, n) in PERSONAS.items()} | {'alberto atilano taylor', 'javier ronces', 'adriana madrid'}

def empresa_de(d):
    """Empresa según la nomenclatura TIPO_Contacto_Empresa_Vendedor_kWp_Proyecto."""
    partes = [x.strip() for x in str(d.get('TITLE') or '').split('_') if x.strip()]
    partes = [p for p in partes if not _RX_TIPO.match(p) and not _RX_KWP.match(p) and norm(p) not in _NOMBRES and not re.fullmatch(r'[\d.,\s]+', p)]
    razon = next((p for p in partes if re.search(r'\b(SA|S\.A\.|CV|SAPI|S DE RL|S\.C\.)\b', p, re.I)), None)
    return razon or (partes[1] if len(partes) > 1 else (partes[0] if partes else str(d.get('TITLE') or '')))

def titulo_deal(d, mapa=None):
    emp = empresa_de(d)
    p = (d.get(UF['proyecto']) or '').strip()
    if p and not _RX_TIPO.match(p) and norm(p) != norm(emp) and norm(p) not in norm(emp):
        return f"#{d['ID']} {emp} ({p})"
    return f"#{d['ID']} {emp}"


def fmt_num(v):
    try:
        return f"{float(v):,.0f}"
    except (TypeError, ValueError):
        return '—'


# ─────────────────────────────── actividad ───────────────────────────────
def cmd_actividad(a):
    uid, nombre = persona(a.vendedor)
    if a.dias:
        desde = date.today() - timedelta(days=a.dias - 1)
    else:
        desde = date.fromisoformat(a.fecha) if a.fecha else date.today()
    hasta = date.today() if a.dias else desde
    d1, d2 = f'{desde}T00:00:00{TZ_BITRIX}', f'{hasta}T23:59:59{TZ_BITRIX}'
    rango = f'el {desde:%d/%m/%Y}' if desde == hasta else f'del {desde:%d/%m} al {hasta:%d/%m/%Y}'
    print(f"ACTIVIDAD DE {nombre.upper()} {rango}\n")

    mapa = etapas()
    # 1. Negociaciones que movió de etapa
    movidas = bx_all('crm.deal.list', {'filter': {'MOVED_BY_ID': uid, '>=MOVED_TIME': d1, '<=MOVED_TIME': d2},
                                       'select': ['ID', 'TITLE', 'STAGE_ID', 'MOVED_TIME', UF['proyecto'], 'OPPORTUNITY']})
    print(f"Negociaciones que movió de etapa: {len(movidas)}")
    for d in movidas:
        print(f"  · {titulo_deal(d)} → {mapa.get(d['STAGE_ID'], d['STAGE_ID'])}  ({d['MOVED_TIME'][11:16]})")
    # 2. Prospectos y negociaciones nuevos
    leads = bx_all('crm.lead.list', {'filter': {'ASSIGNED_BY_ID': uid, '>=DATE_CREATE': d1, '<=DATE_CREATE': d2},
                                     'select': ['ID', 'TITLE', 'STATUS_ID', 'DATE_CREATE']})
    nuevos = bx_all('crm.deal.list', {'filter': {'ASSIGNED_BY_ID': uid, '>=DATE_CREATE': d1, '<=DATE_CREATE': d2},
                                      'select': ['ID', 'TITLE', 'STAGE_ID', UF['proyecto']]})
    print(f"\nProspectos nuevos: {len(leads)}")
    for l in leads:
        print(f"  · #{l['ID']} {l['TITLE']}")
    print(f"Negociaciones nuevas: {len(nuevos)}")
    for d in nuevos:
        print(f"  · {titulo_deal(d)} en {mapa.get(d['STAGE_ID'], d['STAGE_ID'])}")
    # 3. Actividades CRM (llamadas, reuniones, correos) tocadas en el rango
    sel_act = ['ID', 'SUBJECT', 'DESCRIPTION', 'TYPE_ID', 'COMPLETED', 'OWNER_TYPE_ID', 'OWNER_ID', 'DEADLINE', 'LAST_UPDATED']
    acts = bx_all('crm.activity.list', {'filter': {'RESPONSIBLE_ID': uid, '>=LAST_UPDATED': d1, '<=LAST_UPDATED': d2}, 'select': sel_act})
    ids_vistos = {x['ID'] for x in acts}
    acts += [x for x in bx_all('crm.activity.list', {'filter': {'AUTHOR_ID': uid, '>=LAST_UPDATED': d1, '<=LAST_UPDATED': d2}, 'select': sel_act}) if x['ID'] not in ids_vistos]
    tipos = {'1': 'reunión', '2': 'llamada', '3': 'tarea', '4': 'correo', '6': 'actividad'}
    hechas = [x for x in acts if x.get('COMPLETED') == 'Y']
    pend = [x for x in acts if x.get('COMPLETED') != 'Y']
    print(f"\nActividades con clientes completadas: {len(hechas)} · agendadas/pendientes: {len(pend)}")
    desc = lambda x: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>|\[.*?\]', '', str(x.get('DESCRIPTION') or ''))).strip()[:120]
    for x in hechas:
        print(f"  ✓ {tipos.get(str(x.get('TYPE_ID')), 'actividad')}: {x.get('SUBJECT')} (deal/lead {x.get('OWNER_ID')}, {x.get('LAST_UPDATED','')[:10]})" + (f" — {desc(x)}" if desc(x) else ''))
    for x in pend:
        print(f"  ○ {tipos.get(str(x.get('TYPE_ID')), 'actividad')}: {x.get('SUBJECT')} · vence {str(x.get('DEADLINE') or '')[:10]}" + (f" — {desc(x)}" if desc(x) else ''))
    # 4. Comentarios que escribió en negociaciones
    coms = bx_all('crm.timeline.comment.list', {'filter': {'AUTHOR_ID': uid, '>=CREATED': d1, '<=CREATED': d2},
                                                 'select': ['ID', 'ENTITY_ID', 'ENTITY_TYPE', 'COMMENT', 'CREATED']})
    print(f"\nComentarios/seguimientos escritos: {len(coms)}")
    for c in coms:
        txt = re.sub(r'\s+', ' ', re.sub(r'\[.*?\]', '', str(c.get('COMMENT') or ''))).strip()
        print(f"  · {c['ENTITY_TYPE']} {c['ENTITY_ID']}: {txt[:140]}")
    # 5. Tareas que completó o creó
    try:
        cerradas = bx_all('tasks.task.list', {'filter': {'RESPONSIBLE_ID': uid, '>=CLOSED_DATE': d1, '<=CLOSED_DATE': d2},
                                              'select': ['ID', 'TITLE', 'CLOSED_DATE']}, WEBHOOK_TAREAS)
        creadas = bx_all('tasks.task.list', {'filter': {'CREATED_BY': uid, '>=CREATED_DATE': d1, '<=CREATED_DATE': d2},
                                             'select': ['ID', 'TITLE', 'RESPONSIBLE_ID']}, WEBHOOK_TAREAS)
        print(f"\nTareas completadas: {len(cerradas)} · tareas que pidió: {len(creadas)}")
        for t in cerradas:
            print(f"  ✓ #{t['id']} {t['title'][:80]}")
        for t in creadas:
            print(f"  → #{t['id']} {t['title'][:80]} (responsable {t['responsibleId']})")
    except SystemExit as e:
        print(f"\n(tareas no consultadas: {e})")
    total = len(movidas) + len(leads) + len(nuevos) + len(hechas) + len(coms)
    print(f"\nResumen: {total} acciones registradas en Bitrix {rango}." + ('' if total else ' Sin movimiento registrado.'))


# ─────────────────────────────── viables ───────────────────────────────
ETAPA_PESO = {'11_Firma de Contrato': 1, '10_Generación y obtención de documentos para contrato': .95, 'Espera anticipo': .95,
              '9_SI VERBAL (Cierre)': .9, 'Revision financiera ERICK_V2': .85, '7_Propuesta Final (SI VERBAL)': .75,
              'Propuesta financiera': .65, '6_Evaluación Interna': .6, '5_Propuesta Formal': .5, '4_Visita Técnica': .4,
              '3_Se agendo/presento propuesta inicial': .3, '2_Propuesta Preliminar': .15, '1_Generación de propuesta': .08,
              '04_Contacto comercial inicial': .1}
PESO = {'etapa': .35, 'recencia': .20, 'valor': .15, 'retorno': .15, 'cobertura': .10, 'propuesta': .05}


def cmd_viables(a):
    mapa = etapas()
    filtro = {'CATEGORY_ID': [0, 2]}
    if a.vendedor:
        filtro['ASSIGNED_BY_ID'] = persona(a.vendedor)[0]
    deals = bx_all('crm.deal.list', {'filter': filtro, 'select': ['ID', 'TITLE', 'STAGE_ID', 'ASSIGNED_BY_ID', 'OPPORTUNITY',
                                     'CURRENCY_ID', 'CONTACT_ID', 'LAST_ACTIVITY_TIME', 'DATE_MODIFY', UF['proyecto'], UF['kwp'],
                                     UF['energia'], UF['retorno'], UF['tipo']]})
    deals = [d for d in deals if not str(d['STAGE_ID']).endswith('WON') and not str(d['STAGE_ID']).endswith('LOSE')]
    # Propuestas en OneDrive (si el repo trae el consolidado único)
    nprop = {}
    try:
        for c in json.load(open(os.path.join(AQUI, 'consolidado-unico.json')))['clientes']:
            if c.get('idCRM', '').startswith('BX-'):
                nprop[c['idCRM'][3:]] = c.get('nPropuestas') or 0
    except Exception:
        pass
    # Contactos: ¿tiene teléfono o correo?
    cids = sorted({str(d['CONTACT_ID']) for d in deals if d.get('CONTACT_ID') and str(d['CONTACT_ID']) != '0'})
    contacto = {}
    for i in range(0, len(cids), 50):
        for c in bx('crm.contact.list', {'filter': {'ID': cids[i:i+50]}, 'select': ['ID', 'HAS_PHONE', 'HAS_EMAIL']}).get('result', []):
            contacto[str(c['ID'])] = c.get('HAS_PHONE') == 'Y' or c.get('HAS_EMAIL') == 'Y'
    usuarios = {i: n for _, (i, n) in PERSONAS.items()}
    filas, fuera = [], {}

    def f(v):
        try:
            return float(str(v or 0).replace('%', '').replace(',', ''))
        except ValueError:
            return 0.0
    for d in deals:
        kw, en, ret = f(d.get(UF['kwp'])), f(d.get(UF['energia'])), f(d.get(UF['retorno']))
        monto = f(d.get('OPPORTUNITY')); usd = monto if d.get('CURRENCY_ID') == 'USD' else monto / 17.22
        ult = (d.get('LAST_ACTIVITY_TIME') or d.get('DATE_MODIFY') or '')[:10]
        try:
            dias = (date.today() - date.fromisoformat(ult)).days
        except ValueError:
            dias = 9999
        np_ = nprop.get(str(d['ID']), 0)
        motivo = None
        if kw > 20000 or monto > 1e8: motivo = 'dato dudoso'
        elif not contacto.get(str(d.get('CONTACT_ID')), False): motivo = 'sin teléfono ni correo'
        elif dias > 180: motivo = 'más de 180 días sin contacto'
        elif kw < 150: motivo = 'menos de 150 kWp'
        elif usd < 1000 and not np_: motivo = 'sin precio ni propuesta'
        if motivo:
            fuera[motivo] = fuera.get(motivo, 0) + 1; continue
        etapa = mapa.get(d['STAGE_ID'], d['STAGE_ID'])
        partes = {'etapa': ETAPA_PESO.get(etapa, 0), 'recencia': 1 if dias <= 30 else .7 if dias <= 90 else .4,
                  'valor': min(usd, 600000) / 600000, 'retorno': .5 if ret <= 0 else max(0, min(1, (7 - ret) / 4)),
                  'cobertura': min(en, 100) / 100 if en else .5, 'propuesta': min(np_, 3) / 3}
        score = sum(partes[k] * PESO[k] for k in PESO)
        filas.append((score, d, etapa, kw, en, ret, usd, dias, np_, partes))
    filas.sort(key=lambda t: -t[0])
    print(f"LEADS MÁS VIABLES (datos vivos de Bitrix, {date.today():%d/%m/%Y})")
    print(f"Pasan los filtros: {len(filas)} · fuera: " + ', '.join(f'{v} {k}' for k, v in sorted(fuera.items(), key=lambda x: -x[1])) + '\n')
    print(f"{'#':>2} {'score':>5}  {'negociación':34s} {'vendedor':18s} {'kWp':>6} {'%en':>4} {'ROI':>4} {'USD':>9} {'días':>4}  etapa")
    for i, (s, d, etapa, kw, en, ret, usd, dias, np_, partes) in enumerate(filas[:a.top], 1):
        v = usuarios.get(int(d.get('ASSIGNED_BY_ID') or 0), str(d.get('ASSIGNED_BY_ID')))
        print(f"{i:2d} {s:5.2f}  {titulo_deal(d)[:34]:34s} {v[:18]:18s} {kw:6.0f} {en:4.0f} {ret:4.1f} {usd:9,.0f} {dias:4d}  {etapa}")
        if a.detalle:
            print('        ' + ' · '.join(f'{k} {x:.2f}' for k, x in partes.items()) + (f' · {np_} propuestas' if np_ else ''))
    print("\nCómo se calcula: pasan solo negociaciones abiertas con contacto, ≤180 días sin hablar, ≥150 kWp y precio o propuesta. "
          "Puntaje: etapa 35 % · recencia 20 % · valor 15 % · retorno 15 % · cobertura 10 % · propuestas 5 %.")


# ─────────────────────────────── negociacion ───────────────────────────────
def cmd_negociacion(a):
    mapa = etapas()
    r = bx('crm.deal.list', {'filter': {'%TITLE': a.buscar}, 'select': ['ID', 'TITLE', 'STAGE_ID', 'ASSIGNED_BY_ID', 'OPPORTUNITY',
                             'CURRENCY_ID', UF['proyecto'], UF['kwp'], UF['energia'], UF['retorno'], UF['tipo'], 'DATE_CREATE', 'LAST_ACTIVITY_TIME']})
    res = r.get('result', [])
    if not res:
        print(f"No hay negociaciones cuyo título contenga '{a.buscar}'."); return
    usuarios = {i: n for _, (i, n) in PERSONAS.items()}
    for d in res:
        tipos = [TIPO_NOMBRE.get(int(t), t) for t in (d.get(UF['tipo']) or [])]
        print(f"{titulo_deal(d)}\n  título: {d['TITLE']}\n  etapa: {mapa.get(d['STAGE_ID'], d['STAGE_ID'])} · vendedor: {usuarios.get(int(d.get('ASSIGNED_BY_ID') or 0), d.get('ASSIGNED_BY_ID'))}"
              f"\n  {fmt_num(d.get(UF['kwp']))} kWp · {d.get(UF['energia']) or '—'}% energía · retorno {d.get(UF['retorno']) or '—'} · "
              f"{fmt_num(d.get('OPPORTUNITY'))} {d.get('CURRENCY_ID')} · tipo {', '.join(tipos) or '—'}"
              f"\n  creada {str(d.get('DATE_CREATE'))[:10]} · última actividad {str(d.get('LAST_ACTIVITY_TIME') or '')[:10]}\n")


# ─────────────────────────────── cliente nuevo ───────────────────────────────
def cmd_cliente(a):
    vid, vnombre = persona(a.vendedor)
    if vid not in VENDEDORES:
        raise SystemExit(f"{vnombre} no es vendedor; la negociación debe asignarse a un vendedor.")
    por = persona(a.por)[1] if a.por else 'el asistente'
    tipo = TIPO_ID.get(norm(a.tipo).upper().replace('FOTOVOLTAICO', 'FV')) or TIPO_ID.get(a.tipo.upper())
    if not tipo:
        raise SystemExit(f"Tipo '{a.tipo}' no válido. Usa FV, BESS, SC o MANT.")
    contacto_nombre = a.contacto.strip().split(' ')[0]
    como_deal = a.como == 'negociacion'
    if como_deal:
        titulo = f"{TIPO_NOMBRE[tipo]}_{contacto_nombre}_{a.empresa}_{vnombre}_{a.proyecto or a.empresa}"
    else:
        titulo = f"{contacto_nombre}_{a.empresa}_{vnombre}"
    plan = [f"Crear {'NEGOCIACIÓN en Proceso de Venta, etapa 1_Generación de propuesta' if como_deal else 'PROSPECTO (lead)'}",
            f"  título: {titulo}", f"  empresa: {a.empresa} · contacto: {a.contacto} · tel: {a.tel or '—'} · correo: {a.email or '—'}",
            f"  vendedor: {vnombre} (id {vid}) · tipo: {TIPO_NOMBRE[tipo]}" + (f" · {a.kwp} kWp" if a.kwp else ''),
            f"  comentario: 'Creado desde el asistente por {por}'"]
    print('\n'.join(plan))
    if not a.confirmar:
        print("\n(No se creó nada. Si la persona confirma, repite el comando con --confirmar.)"); return
    nombre_partes = a.contacto.strip().split(' ', 1)
    if como_deal:
        comp = bx('crm.company.add', {'fields': {'TITLE': a.empresa, 'ASSIGNED_BY_ID': vid}})['result']
        cont_fields = {'NAME': nombre_partes[0], 'LAST_NAME': nombre_partes[1] if len(nombre_partes) > 1 else '', 'COMPANY_ID': comp, 'ASSIGNED_BY_ID': vid}
        if a.tel: cont_fields['PHONE'] = [{'VALUE': a.tel, 'VALUE_TYPE': 'WORK'}]
        if a.email: cont_fields['EMAIL'] = [{'VALUE': a.email, 'VALUE_TYPE': 'WORK'}]
        cont = bx('crm.contact.add', {'fields': cont_fields})['result']
        fields = {'TITLE': titulo, 'CATEGORY_ID': 0, 'STAGE_ID': 'PREPARATION', 'ASSIGNED_BY_ID': vid, 'COMPANY_ID': comp, 'CONTACT_ID': cont,
                  UF['proyecto']: a.proyecto or a.empresa, UF['tipo']: [tipo]}
        if a.kwp: fields[UF['kwp']] = a.kwp
        did = bx('crm.deal.add', {'fields': fields})['result']
        bx('crm.timeline.comment.add', {'fields': {'ENTITY_ID': did, 'ENTITY_TYPE': 'deal', 'COMMENT': f'Creado desde el asistente por {por}.'}})
        asignado = reasignar('deal', did, vid)
        print(f"\n✅ Negociación #{did} creada (empresa #{comp}, contacto #{cont}), asignada a {asignado}. https://crm-solart.bitrix24.mx/crm/deal/details/{did}/")
    else:
        fields = {'TITLE': titulo, 'NAME': nombre_partes[0], 'LAST_NAME': nombre_partes[1] if len(nombre_partes) > 1 else '',
                  'COMPANY_TITLE': a.empresa, 'ASSIGNED_BY_ID': vid, 'OPENED': 'Y'}
        if a.tel: fields['PHONE'] = [{'VALUE': a.tel, 'VALUE_TYPE': 'WORK'}]
        if a.email: fields['EMAIL'] = [{'VALUE': a.email, 'VALUE_TYPE': 'WORK'}]
        lid = bx('crm.lead.add', {'fields': fields})['result']
        bx('crm.timeline.comment.add', {'fields': {'ENTITY_ID': lid, 'ENTITY_TYPE': 'lead', 'COMMENT': f'Creado desde el asistente por {por}. Tipo de proyecto: {TIPO_NOMBRE[tipo]}.'}})
        asignado = reasignar('lead', lid, vid)
        print(f"\n✅ Prospecto #{lid} creado, asignado a {asignado}. https://crm-solart.bitrix24.mx/crm/lead/details/{lid}/")


def reasignar(entidad, eid, vid):
    """Los robots de Bitrix reasignan lo recién creado (p. ej. a Lilia): se insiste y se verifica."""
    import time
    for _ in range(3):
        time.sleep(2)
        bx(f'crm.{entidad}.update', {'id': eid, 'fields': {'ASSIGNED_BY_ID': vid}})
        time.sleep(2)
        actual = bx(f'crm.{entidad}.get', {'id': eid})['result'].get('ASSIGNED_BY_ID')
        if str(actual) == str(vid):
            return persona(str(vid))[1]
    return f"usuario {actual} (un robot de Bitrix lo reasignó; hay que corregirlo a mano)"


# ─────────────────────────────── mover ───────────────────────────────
def cmd_mover(a):
    mapa = etapas()
    d = bx('crm.deal.get', {'id': a.deal})['result']
    nueva = etapa_por_nombre(a.etapa, mapa)
    por = persona(a.por)[1] if a.por else 'el asistente'
    actual = mapa.get(d['STAGE_ID'], d['STAGE_ID'])
    print(f"Mover {titulo_deal(d)}\n  de:  {actual}\n  a:   {mapa[nueva]}\n  registrado como: movida desde el asistente por {por}")
    if nueva == d['STAGE_ID']:
        print("\nYa está en esa etapa; no hay nada que hacer."); return
    if nueva.endswith('LOSE') and not a.justificacion:
        raise SystemExit("Para marcar PERDIDA hace falta --justificacion \"motivo\" (regla del equipo).")
    if not a.confirmar:
        print("\n(No se movió. Si la persona confirma, repite el comando con --confirmar.)"); return
    cat = 2 if nueva.startswith('C2:') else 0
    fields = {'STAGE_ID': nueva}
    if str(d.get('CATEGORY_ID')) != str(cat):
        fields['CATEGORY_ID'] = cat
    bx('crm.deal.update', {'id': a.deal, 'fields': fields})
    txt = f'Etapa cambiada a "{mapa[nueva]}" desde el asistente por {por}.' + (f' Justificación: {a.justificacion}' if a.justificacion else '')
    bx('crm.timeline.comment.add', {'fields': {'ENTITY_ID': a.deal, 'ENTITY_TYPE': 'deal', 'COMMENT': txt}})
    print(f"\n✅ Listo: {titulo_deal(d)} ahora está en {mapa[nueva]}.")


def cmd_etapas(a):
    for k, v in etapas().items():
        print(f"{v:55s} {k}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('actividad'); s.add_argument('--vendedor', required=True); s.add_argument('--fecha'); s.add_argument('--dias', type=int); s.set_defaults(fn=cmd_actividad)
    s = sub.add_parser('viables'); s.add_argument('--top', type=int, default=20); s.add_argument('--vendedor'); s.add_argument('--detalle', action='store_true'); s.set_defaults(fn=cmd_viables)
    s = sub.add_parser('negociacion'); s.add_argument('--buscar', required=True); s.set_defaults(fn=cmd_negociacion)
    s = sub.add_parser('cliente'); s.add_argument('--empresa', required=True); s.add_argument('--contacto', required=True); s.add_argument('--tel'); s.add_argument('--email')
    s.add_argument('--vendedor', required=True); s.add_argument('--tipo', default='FV'); s.add_argument('--proyecto'); s.add_argument('--kwp', type=float)
    s.add_argument('--como', choices=['prospecto', 'negociacion'], default='prospecto'); s.add_argument('--por'); s.add_argument('--confirmar', action='store_true'); s.set_defaults(fn=cmd_cliente)
    s = sub.add_parser('mover'); s.add_argument('--deal', required=True); s.add_argument('--etapa', required=True); s.add_argument('--por'); s.add_argument('--justificacion'); s.add_argument('--confirmar', action='store_true'); s.set_defaults(fn=cmd_mover)
    s = sub.add_parser('etapas'); s.set_defaults(fn=cmd_etapas)
    a = p.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
