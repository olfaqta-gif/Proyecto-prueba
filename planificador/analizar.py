#!/usr/bin/env python3
"""Analizador de oportunidades de contenido Farmasi.

Estudia TODO el catálogo que leyó el scraper (lector-farmasi/salida/catalogo.json) y
califica cada producto con varias variables, no solo las reseñas:

  confianza      calificación ajustada por cantidad de reseñas (4.9 con 10 reseñas vale menos que con 1000)
  popularidad    cuántas personas lo han reseñado (lo que más se vende en la tienda)
  temporada      si encaja con las fechas y la época del periodo que se planifica
  novedad        producto nuevo o edición limitada (algo que contar, urgencia)
  contenido      cuántos ángulos de contenido ofrece (tonos, ingredientes, modo de uso, resultados…)
  empuje         la tienda lo está promocionando (no se mencionan precios, solo es una señal)
  disponibilidad que haya stock (y tonos disponibles)
  tus_ventas     lo que más te compran tus clientas (planificador/datos/ventas.csv, opcional)
  rendimiento    cómo le fue a esa categoría en tus publicaciones (resultados guardados en los planes)

Luego aplica variedad (no repetir lo ya anunciado ni la misma categoría) y entrega una
lista de oportunidades balanceada, con el porqué y las ideas de contenido de cada una.

Uso (desde la raíz del repositorio):
  python3 planificador/analizar.py oportunidades --objetivo ventas --inicio 2026-10-05 --dias 14
  python3 planificador/analizar.py mercado          # resumen por categoría
  python3 planificador/analizar.py aprendizaje      # qué funcionó en tus publicaciones

Solo usa la librería estándar de Python.
"""
import argparse
import csv
import datetime
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CATALOGO = RAIZ / 'lector-farmasi' / 'salida' / 'catalogo.json'
PRODUCTOS = RAIZ / 'agente-contenido' / 'productos'
PLANES = AQUI / 'planes'
VENTAS = AQUI / 'datos' / 'ventas.csv'
ANALISIS = AQUI / 'analisis'

# ---------- categorías ----------

NO_VENTA = re.compile(r'\b(sample|tester|muestra|guide|gu[ií]a|catalog|cat[aá]logo|brochure|paper|bag|'
                      r'business|starter|kit de inicio|sachet)\b', re.I)
REGLAS = [  # (categoría, patrón) en orden: la primera que coincide gana
    ('accesorios', r'\b(brush|brocha|sponge|esponja|sharpener|tajador|puff|applicator)\b'),
    ('uñas', r'\b(nail|uñas|esmalte)\b'),
    ('sets y regalos', r'\b(set|gift|regalo|collection|colecci[oó]n)\b'),
    ('fragancias', r'\b(edp|edt|parfum|perfume|fragrance|fragancia|body mist|cologne)\b'),
    ('cabello', r'\b(hair|cabello|shampoo|champ[uú]|conditioner|acondicionador|scalp)\b'),
    ('piel', r'\b(eye cream|eye balm|eye serum|eye gel|contorno de ojos)\b'),
    ('labios', r'\b(lip|lips|lipstick|labial|gloss|lacquer|stylo|labios)\b'),
    ('ojos y cejas', r'\b(eyeshadow|eyeliner|palette|paleta|eye|eyes|brow|brows|lash|lashes|mascara|m[aá]scara|liner|kohl|shadow|sombra|cejas|pesta[nñ]as)\b'),
    ('maquillaje de rostro', r'\b(foundation|base|concealer|corrector|primer|powder|polvo|blush|rubor|bronzer|'
                             r'highlighter|iluminador|bb|cc|contour|setting|fijador|cushion|tint)\b'),
    ('cuerpo', r'\b(body|hand|manos|foot|pies|massage|masaje|pferde|balsam|b[aá]lsamo|lotion|loci[oó]n|shower|'
               r'deodorant|desodorante|sculpting|after sun|sun|solar|spf)\b'),
    ('piel', r'\b(cream|crema|serum|suero|cleanser|limpiador|tonic|t[oó]nico|toner|mask|mascarilla|essence|'
             r'esencia|peel|exfoliat\w*|face|facial|elixir|oil|aceite|gel)\b'),
]
HOMBRE = re.compile(r'\b(men|man|masculine|hombre|beard|barba|shave|afeitar)\b', re.I)


def categoria(d):
    marca = (d.get('marca') or '').lower()
    texto = f'{d.get("nombre", "")} {d.get("slug", "").replace("-", " ")}'
    if 'nutriplus' in marca or 'nutriplus' in texto.lower():
        return 'nutrición'
    for cat, patron in REGLAS:
        if re.search(patron, texto, re.I):
            return cat
    if 'mup' in marca or 'makeup' in marca:
        return 'maquillaje de rostro'
    return 'piel' if 'tuna' in marca else 'otros'


# ---------- temporadas ----------
# Por mes: fechas especiales, categorías que encajan y palabras que suman.
TEMPORADAS = {
    1: ('Año nuevo, propósitos y rutina', ['nutrición', 'piel'], r'detox|cleanse|vitamin|protein|shake|routine|serum'),
    2: ('San Valentín', ['labios', 'fragancias', 'sets y regalos'], r'red|rojo|love|kiss|rose|rosa|heart|cherry'),
    3: ('Primavera: piel fresca y maquillaje ligero', ['piel', 'maquillaje de rostro'], r'glow|bb|cc|tint|exfoliat|vitamin c|light'),
    4: ('Primavera y preparación para el verano', ['piel', 'cuerpo'], r'exfoliat|body|glow|sun|aloe'),
    5: ('Día de las Madres', ['sets y regalos', 'fragancias', 'piel'], r'set|gift|edp|cream|rose'),
    6: ('Día del Padre y verano', ['fragancias', 'cuerpo', 'piel'], r'men|masculine|sun|spf|aloe|after sun|waterproof'),
    7: ('Verano: sol, calor e hidratación', ['cuerpo', 'piel', 'nutrición'], r'sun|spf|aloe|after sun|hydr|waterproof|water'),
    8: ('Verano y regreso a clases', ['maquillaje de rostro', 'piel', 'nutrición'], r'waterproof|long|matte|quick|energy|hydr'),
    9: ('Otoño y Mes de la Herencia Hispana (15 sep–15 oct)', ['piel', 'maquillaje de rostro', 'labios'], r'latina|hydr|moist|nourish|repair'),
    10: ('Otoño y Halloween', ['ojos y cejas', 'labios', 'piel'], r'black|negro|dark|red|rojo|berry|plum|smoky|liner|mascara|hydr|repair|night'),
    11: ('Black Friday, Cyber Monday y Acción de Gracias', ['sets y regalos', 'fragancias', 'labios'], r'set|gift|edp|best|favorite'),
    12: ('Navidad y fiestas', ['sets y regalos', 'fragancias', 'labios'], r'set|gift|glitter|shine|shimmer|gold|red|party|highlighter|edp'),
}

# ---------- objetivos: cuánto pesa cada variable ----------
OBJETIVOS = {
    'ventas':      {'confianza': .20, 'popularidad': .25, 'temporada': .15, 'novedad': .05, 'contenido': .10,
                    'empuje': .10, 'disponibilidad': .05, 'tus_ventas': .10},
    'alcance':     {'confianza': .10, 'popularidad': .15, 'temporada': .20, 'novedad': .20, 'contenido': .30,
                    'empuje': .00, 'disponibilidad': .05, 'tus_ventas': .00},
    'confianza':   {'confianza': .35, 'popularidad': .30, 'temporada': .05, 'novedad': .00, 'contenido': .20,
                    'empuje': .00, 'disponibilidad': .05, 'tus_ventas': .05},
    'lanzamiento': {'confianza': .10, 'popularidad': .05, 'temporada': .15, 'novedad': .45, 'contenido': .20,
                    'empuje': .00, 'disponibilidad': .05, 'tus_ventas': .00},
    'equilibrado': {'confianza': .18, 'popularidad': .18, 'temporada': .16, 'novedad': .12, 'contenido': .18,
                    'empuje': .06, 'disponibilidad': .05, 'tus_ventas': .07},
}
NOMBRES = {'confianza': 'confianza', 'popularidad': 'popularidad', 'temporada': 'temporada', 'novedad': 'novedad',
           'contenido': 'potencial de contenido', 'empuje': 'empuje de la tienda',
           'disponibilidad': 'disponibilidad', 'tus_ventas': 'tus ventas'}


# ---------- datos ----------

def leer_json(archivo):
    return json.loads(Path(archivo).read_text(encoding='utf-8'))


def cargar_catalogo():
    if not CATALOGO.exists():
        sys.exit('No hay catálogo. Pídele al scraper: python3 lector-farmasi/leer.py catalogo')
    c = leer_json(CATALOGO)
    leido = c.get('leido', '')
    try:
        edad = (datetime.date.today() - datetime.date.fromisoformat(leido)).days
    except ValueError:
        edad = 999
    if edad > 7:
        print(f'aviso: el catálogo es del {leido} ({edad} días). Conviene actualizarlo con el scraper.',
              file=sys.stderr)
    return c['productos'], leido


def familias(productos):
    """Une los tonos de un mismo producto (cada tono es una página, pero comparten reseñas)."""
    grupos = defaultdict(list)
    for d in productos:
        codigos = tuple(sorted(str(t.get('codigo')) for t in d.get('tonos') or []))
        grupos[codigos or (str(d['codigo']),)].append(d)
    salida = []
    for miembros in grupos.values():
        miembros.sort(key=lambda d: d['nombre'])
        base = miembros[0]
        if len(miembros) > 1:
            nombre = nombre_comun([m['nombre'] for m in miembros])
        else:
            nombre = base['nombre']
            tono = next((t['nombre'] for t in base.get('tonos') or [] if t.get('actual')), None)
            if tono and nombre.endswith(tono) and len(base['tonos']) > 1:
                nombre = nombre[: -len(tono)].rstrip(' -0123456789') or nombre
        tonos = base.get('tonos') or []
        salida.append({
            'familia': nombre,
            'codigo': base['codigo'], 'slug': base['slug'], 'marca': base.get('marca', ''),
            'categoria': categoria(base),
            'hombre': bool(HOMBRE.search(base['nombre'])),
            'promedio': base['resenas'].get('promedio') or 0,
            'resenas': max(m['resenas'].get('cantidad') or 0 for m in miembros),
            'tonos': len(tonos),
            'tonos_disponibles': sum(1 for t in tonos if t.get('disponible')),
            'nuevo': any(m.get('nuevo') for m in miembros),
            'edicion_limitada': any(m.get('edicion_limitada') for m in miembros),
            'disponible': any(m.get('disponible') and not m.get('descontinuado') for m in miembros),
            'promocion': any(re.search(r'off|bogo|deal|sale|savings|friday|monday|11\.11|12\.12', t, re.I)
                             for m in miembros for t in m.get('etiquetas_tienda') or []),
            'texto': ' '.join(f'{m["nombre"]} {m.get("descripcion", "")}' for m in miembros[:3]),
            'ingredientes_clave': base.get('ingredientes_clave') or '',
            'modo_de_uso': bool(base.get('modo_de_uso')),
            'resultados': bool(base.get('resultados_declarados')),
            'atributos': base.get('atributos') or [],
            'descripcion': base.get('descripcion') or '',
            'codigos': [m['codigo'] for m in miembros],
            'no_venta': all(NO_VENTA.search(f'{m["nombre"]} {m["slug"].replace("-", " ")}') or
                            (m.get('marca') or '').lower() == 'sales support' for m in miembros),
        })
    return salida


def nombre_comun(nombres):
    pref = nombres[0]
    for n in nombres[1:]:
        while not n.startswith(pref):
            pref = pref[:-1]
    pref = pref.rstrip(' -0123456789(')
    return pref if len(pref) >= 6 else nombres[0]


def ventas_propias():
    """planificador/datos/ventas.csv con columnas fecha,codigo,cantidad (opcional)."""
    if not VENTAS.exists():
        return {}
    cuenta = Counter()
    with VENTAS.open(encoding='utf-8') as f:
        for fila in csv.DictReader(f):
            try:
                cuenta[str(fila['codigo']).strip()] += float(fila.get('cantidad') or 1)
            except (KeyError, ValueError):
                pass
    return cuenta


def publicaciones_de_planes():
    for p in sorted(PLANES.glob('*.json')):
        try:
            plan = leer_json(p)
        except ValueError:
            continue
        for pub in plan.get('publicaciones', []):
            yield p, pub


def ya_trabajados():
    """Códigos y slugs con anuncio hecho o planeado."""
    hechos, planeados = set(), set()
    for d in PRODUCTOS.glob('*/'):
        hechos.add(d.name)
        if (d / 'datos.json').exists():
            try:
                hechos.add(str(leer_json(d / 'datos.json').get('codigo')))
            except ValueError:
                pass
    for _, pub in publicaciones_de_planes():
        prod = pub.get('producto') or {}
        destino = hechos if pub.get('estado') in ('hecho', 'publicado') else planeados
        for clave in (prod.get('slug'), str(prod.get('codigo') or '')):
            if clave:
                destino.add(clave)
    return hechos, planeados


# ---------- aprendizaje de resultados ----------

def aprendizaje(cat_por_codigo=None):
    """Promedio de resultados por estilo, pilar, tipo, día, hora y categoría."""
    filas = []
    for _, pub in publicaciones_de_planes():
        r = pub.get('resultados')
        if not r:
            continue
        prod = pub.get('producto') or {}
        try:
            dia = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')[
                datetime.date.fromisoformat(pub['fecha']).weekday()]
        except (KeyError, ValueError):
            dia = ''
        filas.append({
            'estilo': pub.get('estilo') or '', 'pilar': pub.get('pilar') or '', 'tipo': pub.get('tipo') or '',
            'dia': dia, 'hora': (pub.get('hora') or '')[:2] and f'{pub["hora"][:2]}h', 'red': pub.get('red') or '',
            'categoria': (cat_por_codigo or {}).get(str(prod.get('codigo') or ''), ''),
            'vistas': r.get('vistas') or 0, 'mensajes': r.get('mensajes') or 0, 'ventas': r.get('ventas') or 0,
        })
    resumen = {}
    for campo in ('tipo', 'pilar', 'estilo', 'categoria', 'dia', 'hora', 'red'):
        grupos = defaultdict(list)
        for f in filas:
            if f[campo]:
                grupos[f[campo]].append(f)
        resumen[campo] = sorted(({'valor': k, 'publicaciones': len(v),
                                  'vistas': round(sum(x['vistas'] for x in v) / len(v)),
                                  'mensajes': round(sum(x['mensajes'] for x in v) / len(v), 1),
                                  'ventas': round(sum(x['ventas'] for x in v) / len(v), 1)}
                                 for k, v in grupos.items()),
                                key=lambda x: (x['mensajes'], x['ventas'], x['vistas']), reverse=True)
    return len(filas), resumen


# ---------- calificación ----------

def ideas_de_contenido(f):
    ideas = []
    if f['tonos'] >= 4:
        ideas.append(f'muestra de tonos en tu piel ({f["tonos"]} tonos)')
    if f['modo_de_uso']:
        ideas.append('tutorial de cómo se usa')
    primera = f['ingredientes_clave'].strip().split('\n')[0]
    clave = primera.split(':')[0].strip(' -•*') if ':' in primera else ''
    if clave and len(clave) < 40 and not re.match(r'(key|main|active)? ?ingredients?$', clave, re.I):
        ideas.append(f'explica para qué sirve: {clave}')
    if f['resenas'] >= 300:
        ideas.append(f'prueba social: {f["resenas"]} reseñas en la tienda')
    if f['nuevo']:
        ideas.append('lanzamiento: "llegó lo nuevo"')
    if f['edicion_limitada']:
        ideas.append('edición limitada: "hasta agotar"')
    if f['resultados']:
        ideas.append('reto de 7 días con tu propia experiencia (sin porcentajes)')
    if f['categoria'] == 'sets y regalos' or f['hombre']:
        ideas.append('idea de regalo' + (' para él' if f['hombre'] else ''))
    if any(re.search(r'vegan|paraben|cruelty|vegano', a, re.I) for a in f['atributos']):
        ideas.append('sin parabenos / vegano: por qué importa')
    return ideas


def calificar(fams, inicio, dias, objetivo, ventas, hechos, planeados, rendimiento_cat):
    meses = sorted({(inicio + datetime.timedelta(days=i)).month for i in range(dias)})
    temporadas = [TEMPORADAS[m] for m in meses]
    max_res = max((f['resenas'] for f in fams), default=1) or 1
    max_ventas = max(ventas.values(), default=0)
    # promedio general para ajustar la calificación (promedio bayesiano)
    con_res = [f for f in fams if f['resenas']]
    media = sum(f['promedio'] * f['resenas'] for f in con_res) / max(1, sum(f['resenas'] for f in con_res))
    m = 50
    pesos = OBJETIVOS[objetivo]

    for f in fams:
        bayes = (m * media + f['resenas'] * f['promedio']) / (m + f['resenas']) if f['promedio'] else media - .2
        v = {
            'confianza': max(0.0, min(1.0, (bayes - 4.5) / 0.5)),
            'popularidad': math.log1p(f['resenas']) / math.log1p(max_res),
            'novedad': 1.0 if f['nuevo'] else (0.7 if f['edicion_limitada'] else 0.0),
            'contenido': min(1.0, len(ideas_de_contenido(f)) / 5),
            'empuje': 1.0 if f['promocion'] else 0.0,
            'disponibilidad': (f['tonos_disponibles'] / f['tonos'] if f['tonos'] else 1.0) if f['disponible'] else 0.0,
            'tus_ventas': (sum(ventas.get(str(c), 0) for c in f['codigos']) / max_ventas) if max_ventas else 0.0,
        }
        temp, motivo_temp = 0.0, ''
        for nombre, cats, palabras in temporadas:
            t = (0.6 if f['categoria'] in cats else 0.0) + (0.4 if re.search(palabras, f['texto'], re.I) else 0.0)
            if t > temp:
                temp, motivo_temp = t, nombre
        if f['hombre'] and 6 in meses:
            temp, motivo_temp = 1.0, TEMPORADAS[6][0]
        v['temporada'] = temp
        puntaje = sum(pesos[k] * v[k] for k in pesos)
        if rendimiento_cat:
            puntaje *= rendimiento_cat.get(f['categoria'], 1.0)
        variedad = 1.0
        claves = {f['slug'], *map(str, f['codigos'])}
        if claves & hechos or any(len(h) > 8 and not h.isdigit() and h in f['slug'] for h in hechos):
            variedad = 0.6
        elif claves & planeados:
            variedad = 0.75
        f['variables'] = {k: round(x, 2) for k, x in v.items()}
        f['puntaje'] = round(100 * puntaje * variedad, 1)
        f['variedad'] = variedad
        f['temporada_motivo'] = motivo_temp if temp >= 0.6 else ''
        f['ideas'] = ideas_de_contenido(f)
        fuertes = sorted(((pesos[k] * v[k], k) for k in pesos if v[k] >= 0.6 and pesos[k]), reverse=True)[:3]
        motivos = []
        for _, k in fuertes:
            if k == 'confianza':
                motivos.append(f'{f["promedio"]} ★ con {f["resenas"]} reseñas')
            elif k == 'popularidad':
                motivos.append(f'de los más reseñados ({f["resenas"]})')
            elif k == 'temporada':
                motivos.append(f'encaja con {motivo_temp}')
            elif k == 'novedad':
                motivos.append('es nuevo' if f['nuevo'] else 'edición limitada')
            elif k == 'contenido':
                motivos.append(f'da para {len(f["ideas"])} tipos de contenido')
            elif k == 'empuje':
                motivos.append('la tienda lo está promocionando')
            elif k == 'tus_ventas':
                motivos.append('tus clientas ya lo compran')
            elif k == 'disponibilidad':
                motivos.append('con buen stock')
        if variedad < 1:
            motivos.append('ya tiene anuncio' if variedad == 0.6 else 'ya está en un plan')
        f['porque'] = '; '.join(motivos)
    return temporadas


def seleccion_variada(fams, n, max_por_categoria):
    elegidos, por_cat = [], Counter()
    for f in sorted(fams, key=lambda f: f['puntaje'], reverse=True):
        if por_cat[f['categoria']] >= max_por_categoria:
            continue
        elegidos.append(f)
        por_cat[f['categoria']] += 1
        if len(elegidos) == n:
            break
    return elegidos


def candidatas(productos):
    return [f for f in familias(productos) if f['disponible'] and not f['no_venta']]


def rendimiento_por_categoria(fams):
    cat_por_codigo = {str(c): f['categoria'] for f in fams for c in f['codigos']}
    n, resumen = aprendizaje(cat_por_codigo)
    filas = resumen.get('categoria', [])
    if sum(x['publicaciones'] for x in filas) < 6:  # con pocos datos no se ajusta nada
        return {}, cat_por_codigo
    media = sum(x['mensajes'] * x['publicaciones'] for x in filas) / sum(x['publicaciones'] for x in filas) or 1
    return ({x['valor']: max(0.75, min(1.3, x['mensajes'] / media)) for x in filas if x['publicaciones'] >= 2},
            cat_por_codigo)


# ---------- comandos ----------

def cmd_mercado(a):
    productos, leido = cargar_catalogo()
    fams = candidatas(productos)
    por_cat = defaultdict(list)
    for f in fams:
        por_cat[f['categoria']].append(f)
    print(f'Catálogo del {leido}: {len(productos)} páginas = {len(fams)} productos a la venta (los tonos se cuentan juntos)\n')
    print(f'{"categoría":24} {"productos":>9} {"reseñas":>9} {"★ prom":>7} {"nuevos":>7} {"en promo":>9}')
    for cat, fs in sorted(por_cat.items(), key=lambda x: -sum(f['resenas'] for f in x[1])):
        res = sum(f['resenas'] for f in fs)
        prom = sum(f['promedio'] * f['resenas'] for f in fs) / res if res else 0
        print(f'{cat:24} {len(fs):9} {res:9} {prom:7.2f} {sum(f["nuevo"] for f in fs):7} '
              f'{sum(f["promocion"] for f in fs):9}')


def cmd_aprendizaje(a):
    productos, _ = cargar_catalogo() if CATALOGO.exists() else ([], '')
    cat_por_codigo = {str(c): f['categoria'] for f in familias(productos) for c in f['codigos']}
    n, resumen = aprendizaje(cat_por_codigo)
    if not n:
        print('Todavía no hay resultados guardados. Cuando publiques, guarda vistas, mensajes y ventas con:\n'
              '  python3 planificador/planificar.py resultado <plan> <id> --vistas 1200 --mensajes 8 --ventas 2')
        return
    print(f'Resultados de {n} publicaciones (promedio por publicación, ordenado por mensajes):')
    for campo, filas in resumen.items():
        if filas:
            print(f'\n{campo}:')
            for x in filas:
                print(f'  {x["valor"]:24} {x["publicaciones"]:3} pub · {x["vistas"]:6} vistas · '
                      f'{x["mensajes"]:5} mensajes · {x["ventas"]:4} ventas')


def cmd_oportunidades(a):
    productos, leido = cargar_catalogo()
    inicio = datetime.date.fromisoformat(a.inicio) if a.inicio else proximo_lunes()
    fams = candidatas(productos)
    if a.categoria:
        fams = [f for f in fams if a.categoria.lower() in f['categoria']]
    hechos, planeados = ya_trabajados()
    ventas = ventas_propias()
    rend, _ = rendimiento_por_categoria(fams)
    temporadas = calificar(fams, inicio, a.dias, a.objetivo, ventas, hechos, planeados, rend)
    top = seleccion_variada(fams, a.n, a.max_por_categoria)

    fin = inicio + datetime.timedelta(days=a.dias - 1)
    print(f'Oportunidades para "{a.objetivo}" del {inicio} al {fin} '
          f'(catálogo del {leido}, {len(fams)} productos analizados)')
    print('Temporada: ' + ' / '.join(t[0] for t in temporadas))
    print(f'Pesos: ' + ', '.join(f'{NOMBRES[k]} {int(p * 100)}%' for k, p in OBJETIVOS[a.objetivo].items() if p))
    if ventas:
        print(f'Usando tus ventas: {VENTAS.relative_to(RAIZ)}')
    if rend:
        print('Ajuste por tus resultados: ' + ', '.join(f'{k} ×{v:.2f}' for k, v in rend.items()))
    print()
    for i, f in enumerate(top, 1):
        print(f'{i}. {f["familia"]}  [{f["categoria"]}]  puntaje {f["puntaje"]}')
        print(f'   código {f["codigo"]} · slug {f["slug"]} · {f["promedio"]} ★ ({f["resenas"]} reseñas)'
              + (f' · {f["tonos"]} tonos' if f['tonos'] else ''))
        print(f'   por qué: {f["porque"]}')
        if f['ideas']:
            print(f'   ideas: {"; ".join(f["ideas"][:4])}')

    ANALISIS.mkdir(exist_ok=True)
    salida = ANALISIS / f'{inicio}-{a.objetivo}.json'
    salida.write_text(json.dumps({
        'creado': datetime.date.today().isoformat(), 'catalogo_leido': leido, 'objetivo': a.objetivo,
        'inicio': str(inicio), 'dias': a.dias, 'temporada': [t[0] for t in temporadas],
        'pesos': OBJETIVOS[a.objetivo], 'ajuste_resultados': rend, 'usa_ventas': bool(ventas),
        'oportunidades': [{k: f[k] for k in ('familia', 'codigo', 'slug', 'categoria', 'promedio', 'resenas',
                                             'tonos', 'nuevo', 'edicion_limitada', 'puntaje', 'variables',
                                             'porque', 'ideas')} for f in top],
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'\nAnálisis guardado en {salida.relative_to(RAIZ)}')


def proximo_lunes():
    hoy = datetime.date.today()
    return hoy + datetime.timedelta(days=(7 - hoy.weekday()) % 7 or 7)


def main():
    ap = argparse.ArgumentParser(description='Analizador de oportunidades de contenido Farmasi')
    sub = ap.add_subparsers(dest='cmd', required=True)
    o = sub.add_parser('oportunidades', help='los mejores productos para el periodo, con el porqué')
    o.add_argument('--objetivo', choices=OBJETIVOS, default='equilibrado')
    o.add_argument('--inicio', help='AAAA-MM-DD (por defecto el próximo lunes)')
    o.add_argument('--dias', type=int, default=14)
    o.add_argument('--n', type=int, default=12, help='cuántas oportunidades (defecto 12)')
    o.add_argument('--max-por-categoria', type=int, default=2)
    o.add_argument('--categoria', help='solo una categoría (ej. labios, piel, nutrición)')
    o.set_defaults(f=cmd_oportunidades)
    sub.add_parser('mercado', help='resumen del catálogo por categoría').set_defaults(f=cmd_mercado)
    sub.add_parser('aprendizaje', help='qué funcionó en tus publicaciones').set_defaults(f=cmd_aprendizaje)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
