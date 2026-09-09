#!/usr/bin/env python3
"""Suma el respaldo de Monday a consolidado.json.

- Los clientes que YA existen en la base (Bitrix o Pipedrive) NO se agregan otra vez:
  se les cuelga un bloque `monday` con kWp, % de energía y precio para comparar.
- Los que no existen entran como registros nuevos con origen 'monday'.

Uso:  python3 consolidar_monday.py [ruta_del_respaldo]
"""
import json, os, re, sys, unicodedata
from datetime import datetime

RESPALDO = sys.argv[1] if len(sys.argv) > 1 else \
    '/Users/luisamor/Documents/Respaldo MONDAY/backups/monday-backup-20260602-044158'
BOARDS = os.path.join(RESPALDO, 'boards')
CONSOLIDADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'consolidado.json')

# Tableros de clientes B2B (los demás son residenciales, tareas internas o catálogos técnicos)
TABLEROS = [
    'Opptys Javier Arista', 'Oportunidades Alfredo Boni', 'Duplicado de Oportunidades Alfredo Boni',
    'Opptys Yezmin Ampudia', 'Recuperación Adrián Escamilla', 'Opptys Eduardo Moreno',
    'Opptys Daniela Cuellar', 'Opptys Samantha Caro', 'Oportunidades Mario Moncada',
    'Prospección Javier Arista', 'Prospección Salvador Sosa', 'Prospección Yezmin Ampudia',
    'Prospección Eduardo Moreno', 'Prospección Samantha Caro', 'Prospección Daniela Cuellar',
    'Pipeline Industriales VL',
]

# Título de columna (normalizado, por coincidencia parcial) → campo
MAPA = [
    (['potencia instalada', 'potencia sfv dc', 'potencia (kw)'], 'kwp'),
    (['% energia cubierto', '% de energia', 'energia cubierta', '% de ahorro'], 'energia'),
    (['valor venta + iva', 'valor venta con iva'], 'precioIvaUSD'),
    (['valor venta (sin iva)', 'valor venta sin iva'], 'precioUSD'),
    (['# de modulos', 'numero de modulos'], 'modulos'),
    (['tarifa'], 'tarifa'),
    (['ciudad'], 'ciudad'),
    (['telefono'], 'tel'),
    (['email', 'correo'], 'email'),
    (['nombre'], 'nombre'),
    (['apellido'], 'apellido'),
    (['ultima nota', 'ultima  nota'], 'nota'),
    (['ultima fecha de contacto', 'fecha de ultimo contacto'], 'ultContacto'),
    (['estatus', 'estado del proyecto'], 'estatus'),
    (['respuesta del cliente'], 'respuesta'),
    (['fecha de cierre'], 'fechaCierre'),
    (['asignado a', 'vendedor', 'persona'], 'asignado'),
]

GENERICO = re.compile(r'^(propuesta|cotizacion|subelemento|prueba|sin nombre|nuevo elemento|item)\b', re.I)


def limpiar_vendedor(txt):
    """Monday guarda varios asignados y a veces el correo: deja un solo nombre legible."""
    if not txt:
        return None
    primero = str(txt).split(',')[0].strip()
    if '@' in primero:  # nombre.apellido@solart.mx → Nombre Apellido
        usuario = primero.split('@')[0].replace('.', ' ').replace('_', ' ')
        primero = ' '.join(p.capitalize() for p in usuario.split())
    return primero or None


def norm(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.strip().lower()


def clave_empresa(nombre):
    """Nombre comparable: sin acentos, sin razón social ni puntuación."""
    n = norm(nombre)
    n = re.sub(r'\b(s\.?a\.?p\.?i\.?|s\.?a\.?|de\s+c\.?v\.?|s\.?\s*de\s*r\.?l\.?|s\.?c\.?|sapi|cv|srl)\b', ' ', n)
    n = re.sub(r'\(.*?\)', ' ', n)
    n = re.sub(r'[^a-z0-9 ]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n


def numero(txt):
    if txt in (None, ''): return None
    t = str(txt).replace(',', '').replace('$', '').replace('%', '').strip()
    try:
        v = float(t)
        return v if v != 0 else None
    except ValueError:
        return None


def leer_tableros():
    if not os.path.isdir(BOARDS):
        sys.exit('No encuentro los tableros en: ' + BOARDS)
    registros = []
    for d in sorted(os.listdir(BOARDS)):
        bj = os.path.join(BOARDS, d, 'board.json')
        ij = os.path.join(BOARDS, d, 'items.json')
        if not (os.path.exists(bj) and os.path.exists(ij)):
            continue
        try:
            b = json.load(open(bj))
            if isinstance(b, list): b = b[0]
        except Exception:
            continue
        nombre_tab = b.get('name', '')
        if nombre_tab not in TABLEROS:
            continue
        try:
            items = json.load(open(ij))
            if isinstance(items, dict): items = items.get('items', [])
        except Exception:
            continue
        for it in items:
            emp = (it.get('name') or '').strip()
            if not emp or GENERICO.match(emp) or '@' in emp:
                continue
            datos = {}
            for cv in it.get('column_values', []):
                titulo = norm((cv.get('column') or {}).get('title') or '')
                txt = (cv.get('text') or '').strip()
                if not txt:
                    continue
                for claves, campo in MAPA:
                    if any(k in titulo for k in claves):
                        if campo not in datos:
                            datos[campo] = txt
                        break
            contacto = ' '.join(x for x in [datos.get('nombre'), datos.get('apellido')] if x).strip()
            registros.append({
                'empresa': emp,
                'tablero': nombre_tab,
                'itemId': str(it.get('id')),
                'url': it.get('url'),
                'creado': (it.get('created_at') or '')[:10],
                'actualizado': (it.get('updated_at') or '')[:10],
                'contacto': contacto or None,
                'tel': datos.get('tel'),
                'email': datos.get('email'),
                'kwp': numero(datos.get('kwp')),
                'energia': numero(datos.get('energia')),
                'precioUSD': numero(datos.get('precioUSD')),
                'precioIvaUSD': numero(datos.get('precioIvaUSD')),
                'modulos': numero(datos.get('modulos')),
                'tarifa': datos.get('tarifa'),
                'ciudad': datos.get('ciudad'),
                'nota': (datos.get('nota') or '')[:300] or None,
                'estatus': datos.get('estatus') or datos.get('respuesta'),
                'ultContacto': datos.get('ultContacto') or (it.get('updated_at') or '')[:10],
                'dueno': limpiar_vendedor(datos.get('asignado')),
            })
    return registros


def mejor(a, b):
    """De dos fichas del mismo cliente, deja la que trae más datos técnicos."""
    peso = lambda r: sum(1 for k in ('kwp', 'energia', 'precioUSD', 'precioIvaUSD', 'tel', 'email') if r.get(k))
    if peso(b) > peso(a):
        a, b = b, a
    for k, v in b.items():
        if a.get(k) in (None, '') and v not in (None, ''):
            a[k] = v
    return a


def main():
    print('Leyendo respaldo de Monday…')
    crudos = leer_tableros()
    print(f'  {len(crudos)} fichas en {len(TABLEROS)} tableros')

    # Dedupe interno por empresa
    porEmpresa = {}
    for r in crudos:
        k = clave_empresa(r['empresa'])
        if len(k) < 3:
            continue
        porEmpresa[k] = mejor(porEmpresa[k], r) if k in porEmpresa else r
    print(f'  {len(porEmpresa)} clientes distintos en Monday')

    base = json.load(open(CONSOLIDADO))
    registros = [r for r in base['registros'] if r.get('origen') != 'monday']  # se reconstruye Monday

    # Índice de la base actual
    indice = {}
    for r in registros:
        for campo in ('empresa', 'proyecto'):
            k = clave_empresa(r.get(campo) or '')
            if len(k) >= 3:
                indice.setdefault(k, r)

    cruzados, nuevos = 0, 0
    for k, m in porEmpresa.items():
        destino = indice.get(k)
        if not destino:  # coincidencia por contención (nombres largos con planta/sucursal)
            for k2, r2 in indice.items():
                if (k in k2 or k2 in k) and min(len(k), len(k2)) >= 6:
                    destino = r2
                    break
        bloque = {
            'kwp': m['kwp'], 'energia': m['energia'],
            'precioUSD': m['precioIvaUSD'] or m['precioUSD'],
            'precioSinIvaUSD': m['precioUSD'],
            'modulos': m['modulos'], 'tarifa': m['tarifa'], 'dueno': m['dueno'],
            'tablero': m['tablero'], 'url': m['url'], 'fecha': m['actualizado'],
            'estatus': m['estatus'], 'nota': m['nota'],
        }
        if destino is not None:
            destino['monday'] = bloque
            cruzados += 1
        else:
            nuevos += 1
            registros.append({
                'origen': 'monday', 'id': 'MDY-' + m['itemId'], 'bitrixId': None,
                'proyecto': m['empresa'], 'empresa': m['empresa'],
                'contacto': m['contacto'], 'tel': m['tel'], 'email': m['email'],
                'descripcion': m['nota'],
                'kwp': m['kwp'], 'precio': None, 'moneda': 'USD',
                'precioUSD': m['precioIvaUSD'] or m['precioUSD'],
                'retorno': None, 'energia': str(m['energia']) if m['energia'] else None,
                'ultContacto': m['ultContacto'], 'estado': 'abierto',
                'dueno': m['dueno'] or '', 'enBitrix': False,
                'pipeline': m['tablero'], 'etapa': m['estatus'] or None,
                'monday': bloque,
            })

    # Completitud (mismos 10 atributos que el resto de la base)
    CAMPOS = ['proyecto', 'empresa', 'contacto', 'descripcion', 'kwp', 'precio',
              'retorno', 'energia', 'ultContacto', 'precioUSD']
    for r in registros:
        if r.get('origen') == 'monday':
            r['completitud'] = sum(1 for c in CAMPOS if r.get(c) not in (None, '', 0))

    base['registros'] = registros
    base['total'] = len(registros)
    base['generado'] = datetime.now().isoformat(timespec='seconds')
    base['monday'] = {'clientes': len(porEmpresa), 'cruzados': cruzados, 'nuevos': nuevos,
                      'respaldo': os.path.basename(RESPALDO)}
    json.dump(base, open(CONSOLIDADO, 'w'), ensure_ascii=False)

    print(f'\n  Ya existían en la base (se les agregó el comparativo): {cruzados}')
    print(f'  Nuevos con origen Monday: {nuevos}')
    print(f'  Total de la base: {len(registros)}')

    # Qué tanto cuadra Monday contra lo que ya teníamos
    dif_kwp = dif_precio = comparables = 0
    for r in registros:
        m = r.get('monday')
        if not m or r.get('origen') == 'monday':
            continue
        if m.get('kwp') and r.get('kwp'):
            comparables += 1
            if abs(m['kwp'] - r['kwp']) / max(r['kwp'], 1) > 0.10:
                dif_kwp += 1
        if m.get('precioUSD') and r.get('precioUSD'):
            if abs(m['precioUSD'] - r['precioUSD']) / max(r['precioUSD'], 1) > 0.10:
                dif_precio += 1
    print(f'  Comparables en kWp: {comparables} · difieren más de 10%: {dif_kwp} · precio distinto: {dif_precio}')


if __name__ == '__main__':
    main()
