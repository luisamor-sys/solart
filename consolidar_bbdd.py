#!/usr/bin/env python3
"""Consolida la BBDD comercial: Bitrix (API) + respaldo Pipedrive → consolidado.json
Uso: python3 consolidar_bbdd.py  (correr desde la carpeta del repo; luego git push)"""
import json, re, urllib.request, unicodedata
import openpyxl
from collections import defaultdict

WEBHOOK = 'https://crm-solart.bitrix24.mx/rest/12/128t1gaxhgz3aoue/'
PIPE = "/private/tmp/claude-501/-Users-luisamor-Documents-Valle-de-san-miguel/89fce07d-a546-44b2-9518-fde77859183e/scratchpad/bbdd/Pipedrive/Respaldo 19-03-25/"
TC = 17.22  # para convertir MXN→USD cuando Bitrix no trae USD

def bx(method, params):
    req = urllib.request.Request(WEBHOOK + method + '.json',
        data=json.dumps(params).encode(), headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))

def bx_all(method, params):
    out, start = [], 0
    while True:
        r = bx(method, {**params, 'start': start})
        out += r.get('result', [])
        if r.get('next') is None: break
        start = r['next']
    return out

def norm(s):
    s = unicodedata.normalize('NFD', str(s or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\b(sa de cv|s\.a\.|sapi|s de rl|de cv|sa|cv)\b|[^a-z0-9 ]', '', s).strip()

# ── BITRIX ──
users = {u['ID']: (u.get('NAME','') + ' ' + (u.get('LAST_NAME') or '')).strip()
         for u in bx('user.get', {'ADMIN_MODE': 'True'}).get('result', [])}
sel = ['ID','TITLE','CATEGORY_ID','STAGE_ID','ASSIGNED_BY_ID','OPPORTUNITY','CURRENCY_ID','CONTACT_ID',
       'DATE_CREATE','DATE_MODIFY','LAST_ACTIVITY_TIME','COMPANY_TITLE',
       'UF_CRM_1741392978542','UF_CRM_1741208352117','UF_CRM_1753209254287','UF_CRM_1758676152864']
bit = []
for cat in [0, 2, 4, 6]:
    bit += bx_all('crm.deal.list', {'filter': {'CATEGORY_ID': cat}, 'select': sel})

def empresa_bitrix(title):
    partes = [p.strip() for p in str(title or '').split('_') if p.strip()]
    razon = next((p for p in partes if re.search(r'\b(SA|S\.A\.|CV|SAPI|S DE RL)\b', p, re.I)), None)
    return razon or (partes[1] if len(partes) > 1 else (partes[0] if partes else ''))

# Contactos de Bitrix (teléfono/email) en lotes
contact_ids = sorted({d['CONTACT_ID'] for d in bit if d.get('CONTACT_ID') and str(d['CONTACT_ID']) != '0'})
contactos = {}
for i in range(0, len(contact_ids), 50):
    lote = contact_ids[i:i+50]
    for c in bx('crm.contact.list', {'filter': {'@ID': lote}, 'select': ['ID','NAME','LAST_NAME','PHONE','EMAIL']}).get('result', []):
        tel = (c.get('PHONE') or [{}])[0].get('VALUE')
        mail = (c.get('EMAIL') or [{}])[0].get('VALUE')
        contactos[str(c['ID'])] = {
            'nombre': (c.get('NAME','') + ' ' + (c.get('LAST_NAME') or '')).strip(),
            'tel': tel, 'email': mail
        }
print('contactos Bitrix resueltos:', len(contactos), 'de', len(contact_ids))

registros, emp_bitrix = [], set()
for d in bit:
    emp = d.get('COMPANY_TITLE') or empresa_bitrix(d.get('TITLE'))
    partes = [p.strip() for p in str(d.get('TITLE') or '').split('_') if p.strip()]
    contacto = contactos.get(str(d.get('CONTACT_ID')), {}).get('nombre') or (partes[0] if partes else '')
    monto = float(d.get('OPPORTUNITY') or 0)
    usd = round(monto if d.get('CURRENCY_ID') == 'USD' else monto / TC, 2) if monto else None
    emp_bitrix.add(norm(emp))
    registros.append({
        'origen': 'bitrix', 'id': f"BX-{d['ID']}", 'bitrixId': d['ID'],
        'proyecto': (d.get('UF_CRM_1741392978542') or '').strip() or None,
        'empresa': emp or None, 'contacto': contacto or None, 'descripcion': None,
        'kwp': float(d['UF_CRM_1741208352117']) if d.get('UF_CRM_1741208352117') else None,
        'precio': monto or None, 'moneda': d.get('CURRENCY_ID') or 'MXN', 'precioUSD': usd,
        'retorno': float(d['UF_CRM_1758676152864']) if d.get('UF_CRM_1758676152864') else None,
        'energia': str(d['UF_CRM_1753209254287']).replace('%','').strip() if d.get('UF_CRM_1753209254287') else None,
        'tel': contactos.get(str(d.get('CONTACT_ID')), {}).get('tel'),
        'email': contactos.get(str(d.get('CONTACT_ID')), {}).get('email'),
        'ultContacto': (d.get('LAST_ACTIVITY_TIME') or d.get('DATE_MODIFY') or '')[:10] or None,
        'estado': 'ganado' if str(d.get('STAGE_ID','')).endswith('WON') or str(d.get('CATEGORY_ID')) in ('4','6')
                  else ('perdido' if str(d.get('STAGE_ID','')).endswith('LOSE') else 'abierto'),
        'dueno': users.get(str(d.get('ASSIGNED_BY_ID')), ''),
    })

# ── PIPEDRIVE ──
def leer(f):
    ws = openpyxl.load_workbook(PIPE + f, read_only=True).active
    rows = ws.iter_rows(values_only=True)
    hdr = list(next(rows))
    return hdr, [dict(zip(hdr, r)) for r in rows if any(v not in (None, '') for v in r)]

_, notas = leer('notes-13728019-117.xlsx')
nota_por_deal = {}
for n in notas:
    did = n.get('ID del trato')
    if not did: continue
    prev = nota_por_deal.get(did)
    if not prev or str(n.get('Hora de añadición') or '') > str(prev.get('Hora de añadición') or ''):
        nota_por_deal[did] = n

_, gente = leer('people-13728019-114.xlsx')
tel_por_persona, mail_por_persona = {}, {}
for p in gente:
    tel = p.get('Teléfono - Móvil') or p.get('Teléfono - Trabajo') or p.get('Teléfono - Personal') or p.get('Teléfono - Otro')
    if tel: tel_por_persona[p['ID']] = str(tel)
    mail = p.get('Correo electrónico - Trabajo') or p.get('Correo electrónico - Personal') or p.get('Correo electrónico - Otro')
    if mail: mail_por_persona[p['ID']] = str(mail)

_, deals_pd = leer('deals-13728019-112.xlsx')
for d in deals_pd:
    emp = d.get('Organización') or ''
    nota = nota_por_deal.get(d.get('ID'), {})
    desc = re.sub(r'<[^>]+>', ' ', str(nota.get('Contenido') or '')).strip()[:400] or None
    usd = d.get('Valor Venta + IVA USD') or d.get('Valor de Venta (sin IVA) USD') or (d.get('Valor') if d.get('Moneda de Valor') == 'USD' else None)
    ult = str(d.get('Fecha de la última actividad') or d.get('Hora de actualización') or '')[:10] or None
    registros.append({
        'origen': 'pipedrive', 'id': f"PD-{d['ID']}", 'bitrixId': None,
        'proyecto': (str(d.get('Título') or '').replace('Trato ', '').strip()) or None,
        'empresa': emp or None,
        'contacto': d.get('Persona de contacto') or None,
        'tel': tel_por_persona.get(d.get('ID de la persona de contacto')),
        'email': mail_por_persona.get(d.get('ID de la persona de contacto')),
        'descripcion': desc,
        'kwp': float(d['Potencia instalada (kW)']) if d.get('Potencia instalada (kW)') else None,
        'precio': float(d['Valor']) if d.get('Valor') else None,
        'moneda': d.get('Moneda de Valor') or 'USD',
        'precioUSD': round(float(usd), 2) if usd else None,
        'retorno': None,
        'energia': str(d['% Energía cubierto']).replace('%','').strip() if d.get('% Energía cubierto') else None,
        'ultContacto': ult,
        'estado': {'Ganado': 'ganado', 'Perdido': 'perdido'}.get(d.get('Estado'), 'abierto'),
        'dueno': d.get('Propietario') or '',
        'enBitrix': norm(emp) in emp_bitrix if emp else False,
    })

CAMPOS = ['proyecto','empresa','contacto','descripcion','kwp','precio','retorno','energia','ultContacto','precioUSD']
for r in registros:
    r['completitud'] = sum(1 for c in CAMPOS if r.get(c) not in (None, '', 0))

salida = {'generado': __import__('datetime').datetime.now().isoformat()[:16], 'tc': TC,
          'total': len(registros), 'registros': registros}
open('consolidado.json', 'w').write(json.dumps(salida, ensure_ascii=False))
from collections import Counter
print('Total:', len(registros),
      '· Bitrix:', sum(1 for r in registros if r['origen']=='bitrix'),
      '· Pipedrive:', sum(1 for r in registros if r['origen']=='pipedrive'))
print('Pipedrive abiertos NO en Bitrix (pool rifa):',
      sum(1 for r in registros if r['origen']=='pipedrive' and r['estado']=='abierto' and not r.get('enBitrix')))
print('Completitud promedio:', round(sum(r['completitud'] for r in registros)/len(registros), 1), '/10')
