#!/usr/bin/env python3
"""Busca posibles proyectos duplicados en consolidado.json y escribe duplicados.json.

Cada par trae su puntaje y las señales que lo delatan. La app (front-consolidado.html,
vista "Posibles duplicados") lo muestra para que una persona confirme o descarte.

Uso:  python3 detectar_duplicados.py      (correr después de consolidar_bbdd.py / consolidar_monday.py)
"""
import json, os, re, unicodedata
from collections import defaultdict
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
PESOS = {
    'Mismo RPU (número de servicio CFE)': 5,
    'Misma carpeta de propuesta en OneDrive': 4,
    'Mismo teléfono': 4,
    'Mismo correo': 4,
    'Mismo precio USD exacto': 3,
    'Mismo nombre de empresa': 3,
    'Un nombre contenido en el otro': 2,
    'Mismo kWp exacto y mismo vendedor': 2,
    'Misma persona de contacto': 2,
    'Mismo vendedor y un registro casi vacío con nombre parecido': 2,
    'Creados o actualizados con pocos días de diferencia': 1,
}
UMBRAL_ALTA, UMBRAL_MEDIA = 4, 2
RUIDO = {'sa', 'sapi', 'cv', 'srl', 'sc', 'de', 'del', 'la', 'el', 'los', 'las', 'y', 'planta', 'bodega', 'grupo', 'nave',
         'frenos', 'mexico', 'industrial', 'industrias', 'industries', 'internacional', 'international', 'company', 'corp',
         'copy', 'planta1', 'planta2', 'sucursal', 'matriz'}


def norm(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn').lower()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    toks = [t for t in s.split() if t not in RUIDO and len(t) > 1]
    return ' '.join(toks)


def tel(t):
    d = re.sub(r'\D', '', str(t or ''))
    return d[-10:] if len(d) >= 10 else ''


def num(v):
    try:
        return float(str(v or 0).replace('%', '').replace(',', ''))
    except ValueError:
        return 0.0


def dias(a, b):
    try:
        return abs((datetime.fromisoformat(str(a)[:10]) - datetime.fromisoformat(str(b)[:10])).days)
    except Exception:
        return None


def main():
    regs = json.load(open(os.path.join(AQUI, 'consolidado.json')))['registros']
    uni = {}
    try:
        for c in json.load(open(os.path.join(AQUI, 'consolidado-unico.json')))['clientes']:
            if c.get('idCRM'):
                uni[c['idCRM']] = c
    except FileNotFoundError:
        pass

    # Los repetidos de Pipedrive que ya existen en Bitrix ya se cuentan una sola vez: no hace falta volver a señalarlos
    regs = [r for r in regs if not (r.get('origen') != 'bitrix' and r.get('enBitrix'))]
    for r in regs:
        r['_n'] = norm(r.get('empresa'))
        r['_np'] = norm(r.get('proyecto'))
        r['_tel'] = tel(r.get('tel'))
        r['_mail'] = str(r.get('email') or '').strip().lower() if '@' in str(r.get('email') or '') else ''
        r['_rpu'] = re.sub(r'\D', '', str((uni.get(r['id']) or {}).get('rpu') or ''))
        r['_carp'] = str((uni.get(r['id']) or {}).get('cliente') or '').strip().lower()
        r['_cont'] = norm(r.get('contacto'))
        r['_kw'] = round(num(r.get('kwp')), 1)
        r['_usd'] = round(num(r.get('precioUSD')))
        r['_due'] = norm(r.get('dueno'))
        r['_vacio'] = sum(1 for k in ('kwp', 'precioUSD', 'tel', 'email', 'energia') if r.get(k) not in (None, '', 0)) <= 1

    señales = defaultdict(set)

    def marca(a, b, s):
        if a['id'] != b['id']:
            señales[tuple(sorted([a['id'], b['id']]))].add(s)

    def por_clave(campo, señal, minimo=1):
        idx = defaultdict(list)
        for r in regs:
            k = r[campo]
            if k and len(str(k)) >= minimo:
                idx[k].append(r)
        for grp in idx.values():
            if len(grp) > 60:  # claves basura (ej. un teléfono genérico): no sirven
                continue
            for i, a in enumerate(grp):
                for b in grp[i + 1:]:
                    marca(a, b, señal)

    por_clave('_rpu', 'Mismo RPU (número de servicio CFE)', 10)
    por_clave('_carp', 'Misma carpeta de propuesta en OneDrive', 3)
    por_clave('_tel', 'Mismo teléfono', 10)
    por_clave('_mail', 'Mismo correo', 5)
    por_clave('_n', 'Mismo nombre de empresa', 3)

    # kWp exacto + vendedor; precio USD exacto; persona de contacto
    idx = defaultdict(list)
    for r in regs:
        if r['_kw'] >= 30:
            idx[(r['_kw'], r['_due'])].append(r)
    for (kw, due), grp in idx.items():
        if due and len(grp) <= 40:
            for i, a in enumerate(grp):
                for b in grp[i + 1:]:
                    marca(a, b, 'Mismo kWp exacto y mismo vendedor')
    idx = defaultdict(list)
    for r in regs:
        if r['_usd'] >= 10000:
            idx[r['_usd']].append(r)
    for grp in idx.values():
        if len(grp) <= 40:
            for i, a in enumerate(grp):
                for b in grp[i + 1:]:
                    marca(a, b, 'Mismo precio USD exacto')
    idx = defaultdict(list)
    for r in regs:
        if r['_cont'] and len(r['_cont']) >= 8:
            idx[r['_cont']].append(r)
    for grp in idx.values():
        if len(grp) <= 20:
            for i, a in enumerate(grp):
                for b in grp[i + 1:]:
                    marca(a, b, 'Misma persona de contacto')

    # Nombre contenido en el otro (solo nombres con sustancia); cascarón; fechas cercanas
    con_nombre = [r for r in regs if len(r['_n']) >= 5]
    primera = defaultdict(list)
    for r in con_nombre:
        primera[r['_n'].split()[0]].append(r)
    for grp in primera.values():
        if len(grp) > 80:
            continue
        for i, a in enumerate(grp):
            for b in grp[i + 1:]:
                na, nb = a['_n'], b['_n']
                if na == nb:
                    continue
                if na in nb or nb in na or (a['_np'] and a['_np'] == b['_np']):
                    marca(a, b, 'Un nombre contenido en el otro')
                    if a['_due'] and a['_due'] == b['_due'] and (a['_vacio'] != b['_vacio']):
                        marca(a, b, 'Mismo vendedor y un registro casi vacío con nombre parecido')

    byid = {r['id']: r for r in regs}
    pares = []
    for (ia, ib), ss in señales.items():
        a, b = byid[ia], byid[ib]
        d = dias(a.get('ultContacto'), b.get('ultContacto'))
        if d is not None and d <= 7 and len(ss) >= 1:
            ss.add('Creados o actualizados con pocos días de diferencia')
        puntos = sum(PESOS[s] for s in ss)
        if puntos < UMBRAL_MEDIA:
            continue
        pares.append({
            'a': ia, 'b': ib, 'puntos': puntos,
            'nivel': 'alta' if puntos >= UMBRAL_ALTA else 'media',
            'senales': sorted(ss, key=lambda s: -PESOS[s]),
            'origenes': [a['origen'], b['origen']],
        })
    pares.sort(key=lambda p: (-p['puntos'], p['a']))
    salida = {'generado': datetime.now().isoformat(timespec='seconds'), 'pesos': PESOS,
              'umbrales': {'alta': UMBRAL_ALTA, 'media': UMBRAL_MEDIA},
              'total': len(pares), 'alta': sum(1 for p in pares if p['nivel'] == 'alta'), 'pares': pares}
    json.dump(salida, open(os.path.join(AQUI, 'duplicados.json'), 'w'), ensure_ascii=False)
    print(f"pares: {len(pares)} (alta {salida['alta']}, media {len(pares) - salida['alta']})")
    cuenta = defaultdict(int)
    for p in pares:
        for s in p['senales']:
            cuenta[s] += 1
    for s, n in sorted(cuenta.items(), key=lambda x: -x[1]):
        print(f'  {n:5d}  {s}')


if __name__ == '__main__':
    main()
