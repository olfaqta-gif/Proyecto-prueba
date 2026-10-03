#!/usr/bin/env python3
"""Asesora de rutinas de Isabella: de lo que cuenta una clienta a su rutina de mañana y noche.

Una clienta escribe "tengo la piel grasa y me salen granitos". La asesora (el agente) lee el
mensaje, decide su tipo de piel y lo que le preocupa, y este programa elige los productos
Farmasi de asesora/catalogo.json, arma una tarjeta bonita para mandarle por WhatsApp
(imagen 1080×1920) con el mensaje ya escrito, y la anota en la libreta de clientas.

Uso (desde la carpeta del proyecto):
  python3 asesora/rutina.py armar consulta.json     # tarjeta + mensaje + libreta
  python3 asesora/rutina.py armar --nombre Lucía --piel mixta --necesidad granitos --necesidad manchas
  python3 asesora/rutina.py opciones                # tipos de piel, necesidades y productos
  python3 asesora/rutina.py lista                   # rutinas que ya se mandaron
  python3 asesora/rutina.py demo                    # 3 rutinas de ejemplo (no tocan la libreta)

La consulta es un JSON (ver asesora/README.md):
  {"nombre": "Lucía", "usuario": "lu.martinez", "red": "instagram", "telefono": "",
   "mensaje": "lo que escribió ella", "piel": ["mixta"], "necesidades": ["granitos", "manchas"],
   "elegir": {"tratar": "serum-lumi"}, "quitar": ["serum-retinol"], "texto_whatsapp": "(opcional)"}

Queda en asesora/rutinas/<fecha>-<nombre>.html (+ .png si hay Chromium) y .json.
Solo librería estándar (la imagen la saca Chromium con playwright si está; si no, la
página tiene el botón «Guardar imagen»).
"""
import argparse
import base64
import datetime
import html
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CATALOGO = AQUI / 'catalogo.json'
TIENDA = AQUI / 'tienda.json'
RUTINAS = AQUI / 'rutinas'
COMPARTIDO = Path('/mnt/project-files')

PIELES = {
    'grasa': 'grasa', 'mixta': 'mixta', 'normal': 'normal', 'seca': 'seca',
    'sensible': 'sensible', 'madura': 'madura',
}
NECESIDADES = {
    'granitos': 'los granitos', 'brillo': 'el brillo', 'poros': 'los poros', 'manchas': 'las manchas',
    'opaca': 'la piel apagada', 'resequedad': 'la resequedad', 'sensibilidad': 'la sensibilidad',
    'arrugas': 'las líneas finas', 'firmeza': 'la firmeza', 'textura': 'la textura',
    'ojeras': 'las ojeras', 'maquillaje': 'desmaquillarse bien',
}
# Para deducir del mensaje lo que la asesora no anotó (ella decide primero).
PISTAS_PIEL = [
    ('grasa', r'\bgras[ao]s?a?\b|grasosa|\boily\b|brillos?\b|me brilla'),
    ('seca', r'\bsec[ao]s?\b|reseca|tirante|\bdry\b|descam'),
    ('mixta', r'\bmixta\b|combinad|zona t\b'),
    ('sensible', r'sensible|se irrita|irritaci|rojez|enrojec|me arde|sensitive'),
    ('madura', r'\b(4\d|5\d|6\d) ?anos\b|madura|menopaus'),
]
PISTAS_NECESIDAD = [
    ('granitos', r'granit|espinill|\bacne\b|barrit|brotes?\b|imperfecci|puntos? negros?'),
    ('brillo', r'brillo|me brilla|grasosa'),
    ('poros', r'\bporos?\b'),
    ('manchas', r'mancha|paño|melasma|tono disparejo|cicatri|marcas?\b|hiperpigment'),
    ('opaca', r'opaca|apagada|sin luz|sin brillo|cansada|sin vida|glow'),
    ('resequedad', r'resec|\bseca\b|tirante|descam|deshidrat'),
    ('sensibilidad', r'sensible|irrita|rojez|enrojec|arde\b'),
    ('arrugas', r'arruga|lineas? de expresi|lineas finas|patas de gallo|envejec|anti ?edad'),
    ('firmeza', r'flacid|firmeza|caid[ao]|colageno'),
    ('textura', r'textura|aspera|rugos'),
    ('ojeras', r'ojera|bolsas|ojos cansados|ojos hinchados'),
    ('maquillaje', r'maquill'),
]
# Lo que no le toca a la asesora: va al médico o al dermatólogo.
EMBARAZO = re.compile(r'embaraz|lactan|amamant|dando pecho|pregnan|bebe en camino|estoy esperando', re.I)
MEDICO = re.compile(r'dermatitis|rosacea|psoriasis|eccema|eczema|acne (?:severo|quistico|fuerte|hormonal)|quistes?\b|'
                    r'infecci|herida|quemadura|alergi|roaccutan|isotretino|tretino|antibiotic|medicament|receta|'
                    r'tratamiento (?:del|con|de) (?:el |la )?dermat|hongos?\b|vitiligo|me sangra|pus\b', re.I)
COLORES = {'tinta': '#2b2321', 'hueso': '#f6f1ea', 'rosa': '#9e4f5c', 'champan': '#c9a66b'}


def sin_tildes(t):
    t = unicodedata.normalize('NFD', str(t or '').lower())
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn')


def slug(t):
    return re.sub(r'[^a-z0-9]+', '-', sin_tildes(t)).strip('-') or 'clienta'


def relativa(ruta):
    try:
        return str(Path(ruta).relative_to(RAIZ))
    except ValueError:
        return str(ruta)


def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def modulo(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, archivo)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def catalogo():
    cat = leer_json(CATALOGO)
    tienda = (leer_json(TIENDA, {}) or {}).get('productos', {})
    for p in cat['productos']:
        p.update({k: v for k, v in tienda.get(p['id'], {}).items() if k not in ('codigo',)})
        p.setdefault('momento', ['manana', 'noche'])
    return cat


# ---------- entender la consulta ----------

def como_lista(x):
    if not x:
        return []
    if isinstance(x, str):
        x = re.split(r'[,y/]+\s*|\s+y\s+', x)
    return [sin_tildes(v).strip() for v in x if str(v).strip()]


def entender(consulta):
    """Tipo de piel, necesidades y avisos (lo que la asesora anotó, o lo que dice el mensaje)."""
    texto = sin_tildes(consulta.get('mensaje', ''))
    pieles = [p for p in como_lista(consulta.get('piel')) if p in PIELES]
    necs = [n for n in como_lista(consulta.get('necesidades')) if n in NECESIDADES]
    deducido = []
    if not pieles:
        pieles = [p for p, patron in PISTAS_PIEL if re.search(patron, texto)]
        # "grasa" y "seca" a la vez casi siempre es mixta
        if 'grasa' in pieles and 'seca' in pieles:
            pieles = ['mixta'] + [p for p in pieles if p not in ('grasa', 'seca', 'mixta')]
        if pieles:
            deducido.append('piel')
    if not necs:
        necs = [n for n, patron in PISTAS_NECESIDAD if re.search(patron, texto)]
        if necs:
            deducido.append('necesidades')
    maquillaje = bool(re.search(r'maquill|base\b|labial', texto))
    avisos = []
    todo = texto + ' ' + sin_tildes(consulta.get('notas', ''))
    embarazo = bool(EMBARAZO.search(todo)) or bool(consulta.get('embarazo'))
    if embarazo:
        avisos.append('Está embarazada o dando pecho: la rutina va sin retinol y conviene que le pregunte a su médico '
                      'antes de empezar productos nuevos.')
    m = MEDICO.search(todo)
    if m:
        avisos.append(f'Menciona algo de salud («{m.group(0)}»): dile con cariño que lo vea con su dermatólogo; '
                      'la rutina va suave y sin retinol ni exfoliante.')
    if not pieles:
        avisos.append('No se sabe su tipo de piel: la rutina es para todo tipo de piel. Pregúntale cómo siente la piel '
                      'al final del día (brillante, tirante, normal).')
    return {'pieles': pieles, 'necesidades': necs, 'deducido': deducido, 'avisos': avisos, 'maquillaje': maquillaje,
            'consultar': 'su médico' if embarazo else ('su dermatólogo' if m else ''),
            'suave': embarazo or bool(m) or 'sensible' in pieles, 'sin_retinol': embarazo or bool(m) or 'sensible' in pieles}


# ---------- elegir los productos ----------

def sirve(p, perfil, quitar):
    if p['id'] in quitar:
        return False
    if perfil['sin_retinol'] and p.get('cuidado') == 'retinol':
        return False
    if perfil['suave'] and p['id'].startswith('exfoliante'):
        return False
    ps = set(p['pieles'])
    if 'todas' in ps or (not perfil['pieles'] and not perfil['suave']):
        return True
    if 'sensible' in perfil['pieles'] or perfil['suave']:   # piel sensible o algo de salud: solo lo suave
        return 'sensible' in ps or 'todas' in ps
    return bool(ps & set(perfil['pieles']))


def puntaje(p, perfil, necs=None):
    necs = perfil['necesidades'] if necs is None else necs
    ps = set(p['pieles'])
    s = 1.5 if 'todas' in ps else 2 * len(ps & set(perfil['pieles']))
    pesos = [3, 2, 1.5, 1]
    for i, n in enumerate(necs):
        if n in p['necesidades']:
            s += pesos[min(i, 3)]
    # desempate: lo mejor calificado y más comprado de la tienda
    s += (float(p.get('nota') or 4.9) - 4.9) * 4 + math.log10(max(10, p.get('resenas') or 10)) * 0.25
    return s


def mejor(cat, paso, perfil, quitar, momento=None, necs=None, evitar=()):
    opciones = [p for p in cat['productos'] if p['paso'] == paso and sirve(p, perfil, quitar)
                and p['id'] not in evitar and (momento is None or momento in p['momento'])]
    return max(opciones, key=lambda p: puntaje(p, perfil, necs)) if opciones else None


def por_id(cat, pid):
    return next((p for p in cat['productos'] if p['id'] == pid), None)


def armar_rutina(cat, perfil, elegir=None, quitar=()):
    """Devuelve la lista de pasos: cada uno con su producto, cuándo se usa y si es esencial."""
    elegir, quitar = elegir or {}, set(quitar)
    necs = perfil['necesidades']

    def tomar(paso, momento=None, necs_=None, evitar=()):
        if paso in elegir and por_id(cat, elegir[paso]) and elegir[paso] not in evitar:
            p = por_id(cat, elegir[paso])
            if momento is None or momento in p['momento']:
                return p
        return mejor(cat, paso, perfil, quitar, momento, necs_, evitar)

    filas = []

    def poner(p, cuando, esencial, paso=None):
        if not p:
            return
        ya = next((f for f in filas if f['producto'] and f['producto']['id'] == p['id']), None)
        if ya:
            ya['cuando'] = sorted(set(ya['cuando']) | set(cuando), key=['manana', 'noche', 'semana'].index)
            ya['esencial'] = ya['esencial'] or esencial
            return
        filas.append({'paso': paso or p['paso'], 'producto': p, 'cuando': list(cuando), 'esencial': esencial})

    # Desmaquillar (de noche) y limpiar
    if 'maquillaje' in necs or perfil.get('maquillaje'):
        poner(tomar('desmaquillar', 'noche'), ['noche'], False)
    poner(tomar('limpiar'), ['manana', 'noche'], True)
    poner(tomar('tonificar'), ['manana', 'noche'], False)

    # Tratar: el sérum para lo que más le preocupa (esencial) y, si hay otra cosa, uno para eso
    t1 = tomar('tratar')
    t2 = None
    if t1 and len(necs) > 1:
        faltan = [n for n in necs if n not in t1['necesidades']] + [n for n in necs if n in t1['necesidades']]
        if faltan != necs:
            t2 = mejor(cat, 'tratar', perfil, quitar, None, faltan, evitar={t1['id']})
            if t2 and not set(t2['necesidades']) & set(faltan[:1]):
                t2 = None
    if t1 and t2:
        # Cada sérum en su momento: el de vitamina C de día, el retinol de noche…
        for a, b in (('noche', 'manana'), ('manana', 'noche')):
            if a in t1['momento'] and b in t2['momento']:
                poner(t1, [a], True)
                poner(t2, [b], False)
                break
        else:
            poner(t1, t1['momento'], True)
            t2 = None
    elif t1:
        poner(t1, t1['momento'], True)

    poner(tomar('contorno'), ['manana', 'noche'], False) if (
        set(necs) & {'ojeras', 'arrugas', 'firmeza'} or 'madura' in perfil['pieles']) else None

    # Hidratar: una crema para mañana y noche (o una de día y otra de noche)
    h = tomar('hidratar') if 'hidratar' in elegir else None
    if not h:
        ambas = [p for p in cat['productos'] if p['paso'] == 'hidratar' and len(p['momento']) == 2 and sirve(p, perfil, quitar)]
        h = max(ambas, key=lambda p: puntaje(p, perfil)) if ambas else tomar('hidratar')
    if h:
        poner(h, h['momento'], True)
        if len(h['momento']) == 1:
            otro = 'noche' if h['momento'] == ['manana'] else 'manana'
            poner(tomar('hidratar', otro, evitar={h['id']}), [otro], True)
    filas.append({'paso': 'proteger', 'producto': None, 'cuando': ['manana'], 'esencial': True})

    # Una o dos veces por semana (si ya usa retinol, mejor una mascarilla que un exfoliante)
    evitar = {p['id'] for p in cat['productos'] if p['id'].startswith('exfoliante')} if any(
        f['producto'] and f['producto'].get('cuidado') == 'retinol' for f in filas) else set()
    poner(tomar('semanal', evitar=evitar), ['semana'], False)

    orden = [p['id'] for p in cat['pasos']]
    filas.sort(key=lambda f: orden.index(f['paso']))
    return filas


# ---------- el mensaje para WhatsApp ----------

def nombre_paso(cat, paso):
    return next((p['nombre'] for p in cat['pasos'] if p['id'] == paso), paso)


def lista_es(cosas):
    cosas = [c for c in cosas if c]
    return cosas[0] if len(cosas) == 1 else ', '.join(cosas[:-1]) + ' y ' + cosas[-1] if cosas else ''


def frase_perfil(perfil):
    piel = 'piel ' + lista_es([PIELES[p] for p in perfil['pieles']]) if perfil['pieles'] else ''
    obvio = {'sensible': 'sensibilidad', 'seca': 'resequedad', 'grasa': 'brillo'}
    necs = lista_es([NECESIDADES[n] for n in perfil['necesidades']
                     if n not in {obvio.get(x) for x in perfil['pieles']}][:3])
    if piel and necs:
        return f'{piel}, pensando en {necs}'
    return piel or (f'pensando en {necs}' if necs else 'todo tipo de piel')


def texto_whatsapp(cat, rutina, perfil, nombre, firma):
    n = (nombre or '').split()[0].capitalize() if nombre else ''

    def de(momento):
        return lista_es([f['producto']['nombre'] if f['producto'] else 'tu protector solar'
                         for f in rutina if momento in f['cuando']])
    esenciales = [f['producto']['nombre'] for f in rutina if f['esencial'] and f['producto']]
    extras = [f['producto']['nombre'] for f in rutina if not f['esencial'] and f['producto']]
    lineas = [f'¡Hola{", " + n if n else ""}! 💕 Te armé tu rutina para {frase_perfil(perfil)}. '
              'Te mando la tarjeta con cada paso explicado.',
              '', f'☀️ Mañana: {de("manana")}.', f'🌙 Noche: {de("noche")}.']
    semana = de('semana')
    if semana:
        lineas.append(f'✨ Una o dos veces por semana: {semana}.')
    lineas += ['', f'Para empezar, lo esencial son {len(esenciales)}: {lista_es(esenciales)}.']
    if extras:
        lineas.append(f'Y si quieres la rutina completa, súmale {lista_es(extras)}.')
    if perfil.get('consultar'):
        lineas += ['', f"Como me contaste lo de tu {'embarazo' if 'médico' in perfil['consultar'] else 'piel'}, "
                       f"te armé todo suave, y antes de empezar coméntalo también con {perfil['consultar'].replace('su ', 'tu ')} 🤍"]
    lineas += ['', '¿Te armo el kit esencial o la rutina completa? 🛍️']
    return '\n'.join(lineas)


# ---------- la tarjeta ----------

SOL = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><g stroke-linecap="round">'
       + ''.join(f'<line x1="{12 + 7 * math.cos(a):.1f}" y1="{12 + 7 * math.sin(a):.1f}" x2="{12 + 9.6 * math.cos(a):.1f}" '
                 f'y2="{12 + 9.6 * math.sin(a):.1f}"/>' for a in [i * math.pi / 4 for i in range(8)])
       + '</g></svg>')
LUNA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z"/></svg>'
BRILLO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.2 7.8L22 12l-7.8 2.2L12 22l-2.2-7.8L2 12l7.8-2.2z"/></svg>'
ICONO = {'manana': (SOL, 'Mañana'), 'noche': (LUNA, 'Noche'), 'semana': (BRILLO, '1–2 por semana')}


def foto_datos(p):
    """La foto dentro de la página (así se puede guardar como imagen y mandar sin internet)."""
    ruta = AQUI / (p.get('foto') or '')
    if not p.get('foto') or not ruta.is_file():
        return ''
    tipo = {'.png': 'png', '.webp': 'webp'}.get(ruta.suffix.lower(), 'jpeg')
    return f'data:image/{tipo};base64,' + base64.b64encode(ruta.read_bytes()).decode()


def e(t):
    return html.escape(str(t or ''))


def pagina(cat, rutina, perfil, consulta, mensaje, firma, png=None):
    nombre = (consulta.get('nombre') or '').strip()
    primer = nombre.split()[0].capitalize() if nombre else ''
    filas_html = []
    n = 0
    for f in rutina:
        n += 1
        p = f['producto']
        cuando = ''.join(f'<span class="chip {c}">{ICONO[c][0]}{ICONO[c][1]}</span>' for c in f['cuando'])
        if p:
            foto = foto_datos(p)
            img = f'<img src="{foto}" alt="">' if foto else '<span class="sinfoto"></span>'
            texto = (f'<div class="arriba"><div class="paso">Paso {n} · {e(nombre_paso(cat, f["paso"]))}</div>'
                     f'<div class="prod">{e(p["nombre"])}</div><div class="para">{e(p["para"])}</div>')
        else:
            img = f'<span class="sol">{SOL}</span>'
            texto = (f'<div class="arriba"><div class="paso">Paso {n} · {e(nombre_paso(cat, "proteger"))}</div>'
                     f'<div class="prod">Tu protector solar</div><div class="para">{e(cat["proteger"])}</div>')
        esencial = '<span class="esencial">Esencial</span>' if f['esencial'] else ''
        texto = texto.replace('</div>', f'</div><div class="cuando">{esencial}{cuando}</div></div>', 1)
        filas_html.append(f'<li class="fila"><span class="num">{n:02d}</span><span class="tile">{img}</span>'
                          f'<div class="txt">{texto}</div></li>')
    esenciales = [i + 1 for i, f in enumerate(rutina) if f['esencial'] and f['producto']]
    alto_fila = max(124, min(190, int(1150 / max(1, len(rutina)))))
    aviso_salud = ('<p class="nota-salud">Si estás embarazada, en tratamiento o tienes alguna condición en la piel, '
                   'consúltalo también con tu médico.</p>') if perfil['avisos'] and any(
        'médico' in a or 'dermatólogo' in a for a in perfil['avisos']) else ''
    chat = enlace_chat(consulta, mensaje)
    avisos = ''.join(f'<li>{e(a)}</li>' for a in perfil['avisos'])
    usos = ''.join(f'<li><b>{e(f["producto"]["nombre"])}:</b> {e(f["producto"]["uso"])}</li>'
                   for f in rutina if f['producto'])
    titulo = f'Rutina de {primer}' if primer else 'Tu rutina'
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,500;0,600;1,500;1,600&family=Jost:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{ --tinta:#2b2321; --hueso:#f6f1ea; --rosa:#9e4f5c; --champan:#c9a66b; --gris:#7b6f6a; --linea:#e6dcd2; --fila:{alto_fila}px; --lineas:{2 if alto_fila >= 140 else 1};
  --serif:"Cormorant","Cormorant Garamond","Didot","Bodoni 72",Georgia,"Liberation Serif","DejaVu Serif",serif;
  --sans:"Jost","Avenir Next","Avenir","Helvetica Neue",Arial,"Liberation Sans","DejaVu Sans",sans-serif; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#e9e1d8; color:var(--tinta); font-family:var(--sans); }}
.vista {{ display:flex; gap:28px; align-items:flex-start; justify-content:center; padding:24px 16px 48px; flex-wrap:wrap; }}
.marco {{ width:min(432px, 100%); aspect-ratio:9/16; position:relative; overflow:hidden; border-radius:22px; box-shadow:0 24px 60px rgba(60,40,30,.22); }}
#tarjeta {{ width:1080px; height:1920px; transform-origin:0 0; position:absolute; top:0; left:0;
  background:radial-gradient(120% 60% at 100% 0%, #f3e3dc 0%, rgba(243,227,220,0) 60%), var(--hueso);
  padding:96px 84px 80px; display:flex; flex-direction:column; }}
body.foto {{ background:var(--hueso); }}
body.foto .vista {{ padding:0; display:block; }}
body.foto .marco {{ width:1080px; height:1920px; border-radius:0; box-shadow:none; }}
body.foto .lado {{ display:none; }}
.sobre {{ font-size:26px; letter-spacing:.42em; text-transform:uppercase; color:var(--rosa); font-weight:500; }}
.nombre {{ font-family:var(--serif); font-style:italic; font-weight:500; font-size:150px; line-height:.95; margin:14px 0 18px; }}
.perfil {{ font-size:32px; font-weight:300; color:var(--gris); line-height:1.35; max-width:860px; }}
.perfil b {{ font-weight:500; color:var(--tinta); }}
.raya {{ height:1px; background:linear-gradient(90deg, var(--champan), rgba(201,166,107,0)); margin:40px 0 18px; }}
.leyenda {{ display:flex; gap:14px; margin-bottom:12px; }}
ol {{ list-style:none; flex:1; display:flex; flex-direction:column; justify-content:flex-start; }}
.fila {{ height:var(--fila); display:grid; grid-template-columns:50px calc(var(--fila) - 26px) 1fr; gap:26px; align-items:center; border-bottom:1px solid var(--linea); }}
.fila:last-child {{ border-bottom:0; }}
.num {{ font-family:var(--serif); font-size:40px; color:var(--champan); font-weight:600; }}
.tile {{ width:calc(var(--fila) - 26px); height:calc(var(--fila) - 26px); background:#fff; border-radius:22px; display:grid; place-items:center; overflow:hidden; box-shadow:0 6px 18px rgba(90,60,40,.08); }}
.tile img {{ width:100%; height:100%; object-fit:contain; }}
.sol {{ display:grid; place-items:center; width:100%; height:100%; background:linear-gradient(160deg,#fbe9c8,#f3d29b); }}
.sol svg {{ width:46%; fill:#e3a34a; stroke:#e3a34a; stroke-width:1.6; }}
.txt {{ min-width:0; }}
.arriba {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
.paso {{ font-size:20px; letter-spacing:.18em; white-space:nowrap; text-transform:uppercase; color:var(--rosa); font-weight:500; }}
.prod {{ font-family:var(--serif); font-size:38px; font-weight:600; line-height:1.04; margin:4px 0 4px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.para {{ font-size:22px; color:var(--gris); line-height:1.25; font-weight:300; display:-webkit-box; -webkit-line-clamp:var(--lineas,2); -webkit-box-orient:vertical; overflow:hidden; }}
.cuando {{ display:flex; gap:6px; align-items:center; flex-shrink:0; }}
.chip {{ display:inline-flex; align-items:center; gap:6px; font-size:18px; padding:5px 12px 5px 9px; border-radius:99px; background:#fff; border:1px solid var(--linea); white-space:nowrap; }}
.chip svg {{ width:20px; height:20px; }}
.chip.manana svg {{ fill:#e3a34a; stroke:#e3a34a; stroke-width:1.6; }}
.chip.noche svg {{ fill:#6b5b8e; }}
.chip.semana svg {{ fill:var(--champan); }}
.esencial {{ font-size:15px; letter-spacing:.16em; text-transform:uppercase; color:#fff; background:var(--rosa); padding:7px 12px; border-radius:99px; }}
.pie {{ margin-top:22px; padding:30px 38px; border-radius:28px; background:#fff; display:flex; justify-content:space-between; align-items:center; gap:24px; box-shadow:0 10px 30px rgba(90,60,40,.08); }}
.pie .t1 {{ font-size:22px; letter-spacing:.2em; text-transform:uppercase; color:var(--rosa); font-weight:500; }}
.pie .t2 {{ font-family:var(--serif); font-size:38px; font-weight:600; margin-top:6px; }}
.firma {{ text-align:right; }}
.firma .con {{ font-size:22px; color:var(--gris); }}
.firma .quien {{ font-family:var(--serif); font-style:italic; font-size:62px; line-height:1; color:var(--rosa); }}
.nota-salud {{ font-size:20px; color:var(--gris); margin-top:16px; text-align:center; }}
.lado {{ width:min(440px,100%); background:#fffaf5; border-radius:20px; padding:22px; box-shadow:0 10px 30px rgba(60,40,30,.1); }}
.lado h2 {{ font-family:var(--serif); font-size:28px; margin-bottom:10px; }}
.lado h3 {{ font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--rosa); margin:18px 0 8px; }}
textarea {{ width:100%; height:270px; border:1px solid var(--linea); border-radius:12px; padding:12px; font:15px/1.45 var(--sans); background:#fff; color:var(--tinta); resize:vertical; }}
.botones {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:12px; }}
.boton {{ border:0; border-radius:99px; padding:11px 18px; font:500 15px var(--sans); cursor:pointer; background:var(--rosa); color:#fff; text-decoration:none; }}
.boton.claro {{ background:#efe4da; color:var(--tinta); }}
.avisos {{ background:#fff3cd; border-radius:12px; padding:12px 14px 12px 30px; font-size:14px; line-height:1.45; }}
.usos {{ padding-left:18px; font-size:14px; line-height:1.5; color:#4b403c; }}
.usos li {{ margin-bottom:6px; }}
.ok {{ font-size:13px; color:#2f9e76; margin-top:8px; min-height:18px; }}
</style></head>
<body>
<div class="vista">
  <div class="marco"><div id="tarjeta">
    <div class="sobre">Tu rutina</div>
    <div class="nombre">{e(primer) or 'Para ti'}</div>
    <p class="perfil">Para <b>{e(frase_perfil(perfil))}</b>. Úsala todos los días y en unas semanas me cuentas cómo vas.</p>
    <div class="raya"></div>
    <ol>{''.join(filas_html)}</ol>
    <div class="pie">
      <div><div class="t1">Para empezar, lo esencial</div><div class="t2">Pasos {lista_es([str(i) for i in esenciales])}{' + protector' if any(not f['producto'] for f in rutina) else ''}</div></div>
      <div class="firma"><div class="con">Con cariño,</div><div class="quien">{e(firma)}</div></div>
    </div>
    {aviso_salud}
  </div></div>
  <aside class="lado">
    <h2>{e(titulo)}</h2>
    {('<h3>Antes de mandarla</h3><ul class="avisos">' + avisos + '</ul>') if avisos else ''}
    <h3>Mensaje para mandarle</h3>
    <textarea id="mensaje">{e(mensaje)}</textarea>
    <div class="botones">
      <button class="boton" id="copiar">Copiar mensaje</button>
      {f'<a class="boton claro" href="{e(chat)}" target="_blank" rel="noopener">Abrir su chat</a>' if chat else ''}
      {f'<a class="boton claro" href="{e(png)}" download>Guardar imagen</a>' if png else '<button class="boton claro" id="guardar">Guardar imagen</button>'}
    </div>
    <div class="ok" id="ok"></div>
    <h3>Cómo se usa cada uno (por si pregunta)</h3>
    <ul class="usos">{usos}</ul>
  </aside>
</div>
<script>
(function () {{
  var foto = /[?&]foto\\b/.test(location.search);
  if (foto) document.body.classList.add('foto');
  var marco = document.querySelector('.marco'), t = document.getElementById('tarjeta');
  function ajustar() {{ if (!foto) t.style.transform = 'scale(' + (marco.clientWidth / 1080) + ')'; }}
  ajustar(); window.addEventListener('resize', ajustar);
  var ok = document.getElementById('ok');
  document.getElementById('copiar').onclick = function () {{
    var m = document.getElementById('mensaje');
    (navigator.clipboard ? navigator.clipboard.writeText(m.value) : Promise.reject()).then(function () {{
      ok.textContent = 'Copiado ✓ Ahora pégalo en su chat.';
    }}, function () {{ m.select(); document.execCommand('copy'); ok.textContent = 'Copiado ✓'; }});
  }};
  var g = document.getElementById('guardar');
  if (g) g.onclick = function () {{
    ok.textContent = 'Preparando la imagen…';
    function hacer() {{
      t.style.transform = 'none';
      html2canvas(t, {{ width: 1080, height: 1920, scale: 1, backgroundColor: '#f6f1ea' }}).then(function (c) {{
        ajustar();
        var a = document.createElement('a');
        a.download = {json.dumps(slug(titulo) + '.png')}; a.href = c.toDataURL('image/png'); a.click();
        ok.textContent = 'Imagen guardada ✓ Búscala en Descargas.';
      }}, function () {{ ajustar(); ok.textContent = 'No se pudo. Saca una captura de pantalla de la tarjeta.'; }});
    }}
    if (window.html2canvas) return hacer();
    var s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    s.onload = hacer; s.onerror = function () {{ ok.textContent = 'Sin internet: saca una captura de pantalla de la tarjeta.'; }};
    document.head.appendChild(s);
  }};
}})();
</script>
</body></html>
'''


def enlace_chat(consulta, texto):
    from urllib.parse import quote
    tel = re.sub(r'\D', '', consulta.get('telefono') or '')
    if tel:
        return f'https://wa.me/{tel}?text={quote(texto)}'
    u = (consulta.get('usuario') or '').lstrip('@').strip()
    if not u:
        return ''
    return {'tiktok': f'https://www.tiktok.com/@{u}', 'facebook': f'https://m.me/{u}'}.get(
        consulta.get('red') or 'instagram', f'https://ig.me/m/{u}')


def sacar_foto(html_archivo, png):
    """La imagen 1080×1920 con Chromium (si está playwright). Si no, queda el botón de la página."""
    if not shutil.which('node'):
        return False
    try:
        r = subprocess.run(['node', str(AQUI / 'foto.cjs'), str(html_archivo), str(png)],
                           capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and png.exists()


# ---------- revisar lo que se le va a mandar ----------

def revisar(mensaje):
    avisos = []
    try:
        resp = modulo('responder', RAIZ / 'comunidad' / 'responder.py')
        avisos += resp.revisar_texto(mensaje, (RAIZ / 'comunidad' / 'precios.md').exists())
    except Exception:  # noqa: BLE001  (si falta el agente de comunidad, se revisa lo básico)
        if re.search(r'\bcura\b|elimina|garantiza|100 ?%', mensaje, re.I):
            avisos.append('promete resultados')
    return avisos


# ---------- la libreta ----------

def anotar_en_libreta(consulta, perfil, rutina, archivo_libreta=None):
    if not (consulta.get('nombre') or consulta.get('usuario') or consulta.get('telefono')):
        return None
    l = modulo('libreta', RAIZ / 'clientas' / 'libreta.py')
    archivo = archivo_libreta or l.LIBRETA
    datos = l.cargar(archivo)
    ya = next((c for c in (l.buscar_clienta(datos, q) for q in
                           ('@' + consulta['usuario'] if consulta.get('usuario') else None,
                            consulta.get('telefono'), consulta.get('nombre')) if q) if c), None)
    esenciales = [f['producto']['nombre'] for f in rutina if f['esencial'] and f['producto']]
    todos = [f['producto']['nombre'] for f in rutina if f['producto']]
    campos = {'nombre': consulta.get('nombre') or None, 'usuario': consulta.get('usuario'),
              'red': consulta.get('red') or ('whatsapp' if consulta.get('telefono') else 'instagram'),
              'telefono': consulta.get('telefono'), 'intereses': esenciales,
              'origen': consulta.get('origen') or 'asesora de rutinas'}
    if perfil['pieles'] and not (ya or {}).get('piel'):
        campos['piel'] = perfil['pieles'][0] if len(perfil['pieles']) == 1 else ' y '.join(perfil['pieles'])
        campos['piel_fuente'] = 'lo contó ella' if 'piel' not in perfil['deducido'] else 'por su mensaje'
    if not ya:
        campos['etapa'] = 'interesada'
    texto = (consulta.get('mensaje') or '').strip().replace('\n', ' ')
    nota = (f"Le armé su rutina ({frase_perfil(perfil)}): {', '.join(todos)}"
            + (f" · ella escribió: «{texto[:140]}»" if texto else ''))
    c = l.guardar_clienta(datos, campos, nota)
    if ya and c.get('etapa') in ('pregunto', 'pausa'):
        l.mover(datos, c, 'interesada')
    l.guardar(datos, archivo)
    return {'id': c['id'], 'nombre': c['nombre'], 'nueva': not ya, 'etapa': c['etapa']}


# ---------- comandos ----------

def hacer(consulta, libreta=True, archivo_libreta=None, carpeta=RUTINAS, con_foto=True):
    cat = catalogo()
    perfil = entender(consulta)
    rutina = armar_rutina(cat, perfil, consulta.get('elegir'), consulta.get('quitar', []))
    firma = 'Isabella'
    try:
        firma = modulo('libreta', RAIZ / 'clientas' / 'libreta.py').voz()['firma']
    except Exception:  # noqa: BLE001
        pass
    mensaje = (consulta.get('texto_whatsapp') or '').strip() or texto_whatsapp(cat, rutina, perfil, consulta.get('nombre'), firma)
    problemas = revisar(mensaje)
    carpeta.mkdir(parents=True, exist_ok=True)
    hoy = datetime.date.today().isoformat()
    base = carpeta / f"{hoy}-{slug(consulta.get('nombre') or consulta.get('usuario') or 'clienta')}"
    archivo = base.with_suffix('.html')
    png = base.with_suffix('.png')
    archivo.write_text(pagina(cat, rutina, perfil, consulta, mensaje, firma), encoding='utf-8')
    tiene_png = con_foto and sacar_foto(archivo, png)
    if tiene_png:  # la página ofrece la imagen ya hecha
        archivo.write_text(pagina(cat, rutina, perfil, consulta, mensaje, firma, png.name), encoding='utf-8')
    clienta = anotar_en_libreta(consulta, perfil, rutina, archivo_libreta) if libreta else None
    registro = {'fecha': hoy, 'consulta': consulta, 'pieles': perfil['pieles'], 'necesidades': perfil['necesidades'],
                'deducido': perfil['deducido'], 'avisos': perfil['avisos'], 'revisar': problemas,
                'productos': [{'id': f['producto']['id'], 'nombre': f['producto']['nombre'], 'codigo': f['producto']['codigo'],
                               'cuando': f['cuando'], 'esencial': f['esencial']} for f in rutina if f['producto']],
                'mensaje': mensaje, 'pagina': relativa(archivo),
                'imagen': relativa(png) if tiene_png else None, 'clienta': clienta}
    base.with_suffix('.json').write_text(json.dumps(registro, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if COMPARTIDO.is_dir() and carpeta == RUTINAS:
        destino = COMPARTIDO / 'rutinas'
        destino.mkdir(exist_ok=True)
        for f in (archivo, png):
            if f.exists():
                shutil.copy2(f, destino / f.name)
    return registro


def imprimir(r):
    print(f"Rutina para {r['consulta'].get('nombre') or r['consulta'].get('usuario') or 'la clienta'}"
          f" · piel: {', '.join(r['pieles']) or 'sin saber'} · necesidades: {', '.join(r['necesidades']) or '—'}"
          + (f" (deducido del mensaje: {', '.join(r['deducido'])})" if r['deducido'] else ''))
    for p in r['productos']:
        print(f"  {'★' if p['esencial'] else '·'} {p['nombre']}  [{', '.join(p['cuando'])}]")
    print(f"Página: {r['pagina']}" + (f"\nImagen: {r['imagen']}" if r['imagen'] else
                                       '\nImagen: ábrela y toca «Guardar imagen» (aquí no hay Chromium)'))
    if r['clienta']:
        c = r['clienta']
        print(f"Libreta: {c['nombre']} ({'nueva' if c['nueva'] else 'ya estaba'}) → {c['etapa']}")
    for a in r['avisos']:
        print('AVISO:', a)
    for a in r['revisar']:
        print('REVISAR el mensaje:', a)


def cmd_armar(a):
    if a.consulta:
        consulta = leer_json(a.consulta)
        if not isinstance(consulta, dict):
            sys.exit('La consulta tiene que ser un JSON con los datos de la clienta (ver asesora/README.md).')
    else:
        consulta = {}
    for k in ('nombre', 'usuario', 'red', 'telefono', 'mensaje'):
        if getattr(a, k):
            consulta[k] = getattr(a, k)
    if a.piel:
        consulta['piel'] = a.piel
    if a.necesidad:
        consulta['necesidades'] = a.necesidad
    imprimir(hacer(consulta, libreta=not a.sin_libreta, con_foto=not a.sin_foto))


def cmd_opciones(_):
    cat = catalogo()
    print('Tipos de piel:', ', '.join(PIELES))
    print('Necesidades:', ', '.join(NECESIDADES))
    for paso in cat['pasos']:
        prods = [p for p in cat['productos'] if p['paso'] == paso['id']]
        if not prods:
            continue
        print(f"\n{paso['nombre']} ({paso['id']}):")
        for p in prods:
            m = '' if p['momento'] == ['manana', 'noche'] else f" [solo {', '.join(p['momento'])}]"
            print(f"  {p['id']:<26} {p['nombre']}{m} · piel {'/'.join(p['pieles'])} · {', '.join(p['necesidades'])}")


def cmd_lista(_):
    hechas = sorted(RUTINAS.glob('*.json')) if RUTINAS.is_dir() else []
    if not hechas:
        print('Todavía no hay rutinas.')
    for f in hechas:
        r = leer_json(f, {})
        print(f"{r.get('fecha')}  {(r.get('consulta') or {}).get('nombre') or '-':<18} "
              f"{', '.join(r.get('pieles', [])) or '-':<14} {len(r.get('productos', []))} productos  {r.get('pagina')}")


EJEMPLOS = [
    {'nombre': 'Lucía Martínez', 'usuario': 'lu.martinez', 'red': 'instagram',
     'mensaje': 'Hola! tengo la piel mixta, me brilla mucho la frente y me salen granitos, y tengo manchitas de los granitos que ya se fueron. qué me recomiendas?',
     'piel': ['mixta'], 'necesidades': ['granitos', 'manchas', 'brillo']},
    {'nombre': 'Marta Gómez', 'telefono': '+1 305 555 0142', 'red': 'whatsapp',
     'mensaje': 'Buenas, tengo 52 años y siento la piel seca y ya se me notan las arrugas y las ojeras. Quiero algo para cuidarme',
     'piel': ['seca', 'madura'], 'necesidades': ['arrugas', 'resequedad', 'ojeras']},
    {'nombre': 'Daniela Ortiz', 'usuario': 'dani.ortiz', 'red': 'tiktok',
     'mensaje': 'Hola!! mi piel es súper sensible, todo me irrita y se me pone roja. Ah y estoy embarazada 🤰 qué puedo usar?',
     'piel': ['sensible'], 'necesidades': ['sensibilidad', 'resequedad']},
]


def cmd_demo(_):
    carpeta = RUTINAS / 'ejemplos'
    for c in EJEMPLOS:
        imprimir(hacer(dict(c), libreta=False, carpeta=carpeta))
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('armar', help='arma la rutina, la tarjeta y la anota en la libreta')
    a.add_argument('consulta', nargs='?', help='archivo .json con la consulta')
    for k in ('nombre', 'usuario', 'red', 'telefono', 'mensaje'):
        a.add_argument('--' + k)
    a.add_argument('--piel', action='append', help='tipo de piel (se puede repetir: seca y madura)')
    a.add_argument('--necesidad', action='append', help='lo que le preocupa, en orden (se puede repetir)')
    a.add_argument('--sin-libreta', action='store_true', help='no la anota en la libreta')
    a.add_argument('--sin-foto', action='store_true', help='no saca la imagen con Chromium')
    sub.add_parser('opciones', help='tipos de piel, necesidades y productos del catálogo')
    sub.add_parser('lista', help='rutinas que ya se armaron')
    sub.add_parser('demo', help='3 rutinas de ejemplo en asesora/rutinas/ejemplos (no tocan la libreta)')
    args = ap.parse_args()
    {'armar': cmd_armar, 'opciones': cmd_opciones, 'lista': cmd_lista, 'demo': cmd_demo}[args.cmd](args)


if __name__ == '__main__':
    main()
