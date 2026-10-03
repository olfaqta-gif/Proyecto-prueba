#!/usr/bin/env python3
"""Kit de marca de Isabella: que todo lo que publica se vea de la misma marca.

Arma con sus colores y letras (marca/kit.json):
- las portadas de sus historias destacadas de Instagram (Rutinas, Mi piel, Maquillaje…),
- historias listas a partir de un texto: producto nuevo, opinión de una clienta, oferta,
  pregunta del día, rutina en pasos y gracias por tu pedido (y los fondos vacíos para
  escribir encima en Instagram),
- la guía de marca: colores con su código, letras, qué sí y qué no.

Uso (desde la carpeta del proyecto):
  python3 marca/kit.py portadas                     # salida/portadas/<nombre>.png (1080×1920)
  python3 marca/kit.py historia nuevo --producto 1002167 --titulo "Vitamin C Glow Serum" --texto "Luz desde el primer día"
  python3 marca/kit.py historia opinion --texto "Me encantó, mi piel se siente suave" --quien "Carla" --producto 1000290
  python3 marca/kit.py historia oferta --titulo "Semana de la piel" --texto "Llévate tu rutina con un regalo" --hasta "domingo 12"
  python3 marca/kit.py historia pregunta --texto "¿Qué te preocupa más de tu piel?"
  python3 marca/kit.py historia rutina --titulo "Mi rutina de noche" --paso "Limpia" --paso "Sérum" --paso "Crema"
  python3 marca/kit.py historia gracias --quien "Lucía"
  python3 marca/kit.py fondos                       # las 6 plantillas vacías para escribir encima en Instagram
  python3 marca/kit.py guia                         # salida/guia-de-marca.html
  python3 marca/kit.py demo                         # todo, con textos de ejemplo

Las imágenes salen con Chromium (playwright). Si no está, se abre el .html y se toma captura.
Solo librería estándar.
"""
import argparse
import base64
import datetime
import html
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
KIT = AQUI / 'kit.json'
VOZ = AQUI / 'voz-isabella.md'
SALIDA = AQUI / 'salida'
FOTOS = AQUI / 'datos' / 'fotos'
COMPARTIDO = Path('/mnt/project-files')

# Íconos de línea (24×24) para las portadas
ICONOS = {
    'rutina': '<circle cx="8" cy="8.5" r="2.8"/><path d="M8 3v1.3M8 12.7V14M2.5 8.5h1.3M12.2 8.5h1.3M4.1 4.6l.9.9M11 11.5l.9.9M4.1 12.4l.9-.9M11 5.5l.9-.9"/><path d="M21.5 18A4.6 4.6 0 1 1 16.8 13a3.6 3.6 0 0 0 4.7 5z"/>',
    'gota': '<path d="M12 3.2C9 7.4 6.2 10.6 6.2 14a5.8 5.8 0 0 0 11.6 0c0-3.4-2.8-6.6-5.8-10.8z"/><path d="M9.4 14.6a2.7 2.7 0 0 0 2.4 2.6"/>',
    'labial': '<path d="M9 21h6v-8H9z"/><path d="M9.6 13V8.5L13.8 5v8"/><path d="M8 21h8"/>',
    'corazon': '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.6 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/>',
    'estrella': '<path d="M12 3.6l2.5 5.2 5.6.7-4.1 3.9 1 5.6-5-2.8-5 2.8 1-5.6-4.1-3.9 5.6-.7z"/>',
    'bolsa': '<path d="M5 8h14l-1.2 12H6.2z"/><path d="M9 10V6.5a3 3 0 0 1 6 0V10"/>',
    'manos': '<circle cx="8.5" cy="8" r="2.8"/><circle cx="16" cy="9" r="2.4"/><path d="M3.5 19c.4-3.4 2.4-5.3 5-5.3s4.6 1.9 5 5.3"/><path d="M13.6 14.2c.7-.5 1.5-.8 2.4-.8 2.2 0 3.8 1.6 4.2 4.6"/>',
    'brillo': '<path d="M12 3l1.9 6.1L20 11l-6.1 1.9L12 19l-1.9-6.1L4 11l6.1-1.9z"/><path d="M19 3.5v3M17.5 5h3"/>',
}
TIPOS = ('nuevo', 'opinion', 'oferta', 'pregunta', 'rutina', 'gracias')


def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def e(t):
    return html.escape(str(t if t is not None else ''))


def slug(t):
    t = unicodedata.normalize('NFD', str(t or '').lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-') or 'pieza'


def kit():
    k = leer_json(KIT, {})
    k['c'] = {c['id']: c['hex'] for c in k['colores']}
    k['firma'] = 'Isabella'
    if VOZ.exists():
        t = VOZ.read_text(encoding='utf-8')
        m = re.search(r'Nombre en redes:\s*(.+)', t)
        if m and 'PENDIENTE' not in m.group(1):
            k['firma'] = m.group(1).strip()
        m = re.search(r'Qué palabra usan sus clientas para pedir por mensaje:\s*(.+)', t)
        if m and 'PENDIENTE' not in m.group(1):
            k['palabra_pedido'] = m.group(1).strip().strip('"«»')
    return k


def base_css(k):
    c = k['c']
    return f'''
:root {{ --hueso:{c["hueso"]}; --tinta:{c["tinta"]}; --rosa:{c["rosa"]}; --rubor:{c["rubor"]}; --champan:{c["champan"]};
  --serif:{k["letras"]["titulos"]["css"]}; --sans:{k["letras"]["texto"]["css"]}; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#e9e1d8; font-family:var(--sans); color:var(--tinta); }}
.todo {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:18px; padding:20px 16px 50px; max-width:1200px; margin:auto; }}
.marco {{ aspect-ratio:9/16; position:relative; overflow:hidden; border-radius:14px; box-shadow:0 14px 34px rgba(60,40,30,.18); }}
.lienzo {{ width:1080px; height:1920px; position:absolute; top:0; left:0; transform-origin:0 0; overflow:hidden; }}
body.foto {{ background:none; }} body.foto .todo {{ display:block; padding:0; }}
body.foto .marco {{ width:1080px; height:1920px; border-radius:0; box-shadow:none; }}
'''


ESCALAR = '''<script>(function(){ var f=/[?&]foto\\b/.test(location.search); if(f) document.body.classList.add('foto');
function a(){ document.querySelectorAll('.marco').forEach(function(m){ m.firstElementChild.style.transform = f ? 'none' : 'scale(' + (m.clientWidth/1080) + ')'; }); }
a(); addEventListener('resize', a); })();</script>'''


def documento(titulo, css, cuerpo):
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(titulo)}</title><link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,500;0,600;1,500;1,600'
            f'&family=Jost:wght@300;400;500&display=swap" rel="stylesheet"><style>{css}</style></head><body>'
            f'<div class="todo">{cuerpo}</div>{ESCALAR}</body></html>')


def fotos(html_archivo, selector='.lienzo'):
    if not shutil.which('node'):
        return []
    try:
        r = subprocess.run(['node', str(AQUI / 'fotos.cjs'), str(html_archivo), selector], capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [Path(x) for x in r.stdout.split()] if r.returncode == 0 else []


def compartir(archivos, sub):
    if COMPARTIDO.is_dir():
        d = COMPARTIDO / 'marca' / sub
        d.mkdir(parents=True, exist_ok=True)
        for f in archivos:
            if Path(f).exists():
                shutil.copy2(f, d / Path(f).name)


# ---------- portadas de destacados ----------

def portadas(k, carpeta):
    css = base_css(k) + '''
.portada { background:var(--hueso); display:grid; place-items:center; }
.circulo { width:640px; height:640px; border-radius:50%; background:var(--rubor); display:grid; place-items:center; align-content:center; gap:26px; }
.circulo svg { width:250px; height:250px; fill:none; stroke:var(--rosa); stroke-width:1.15; stroke-linecap:round; stroke-linejoin:round; }
.circulo span { font-family:var(--serif); font-style:italic; font-size:76px; color:var(--rosa); line-height:1; }
'''
    piezas = ''.join(f'<div class="marco"><div class="lienzo portada" data-nombre="{e(d["id"])}"><div class="circulo">'
                     f'<svg viewBox="0 0 24 24">{ICONOS[d["icono"]]}</svg><span>{e(d["nombre"])}</span></div></div></div>'
                     for d in k['destacados'])
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / 'portadas.html'
    archivo.write_text(documento('Portadas de destacados', css, piezas), encoding='utf-8')
    imgs = fotos(archivo)
    nombradas = []
    for img, d in zip(imgs, k['destacados']):
        destino = carpeta / f"portada-{d['id']}.png"
        img.replace(destino)
        nombradas.append(destino)
    return [archivo] + nombradas


# ---------- historias ----------

def foto_producto(ref):
    """Foto grande del producto: la del agente de contenido, la del scraper o la baja de la tienda."""
    if not ref:
        return ''
    ruta = Path(ref)
    if (RAIZ / ref).is_file() or ruta.is_file():
        f = ruta if ruta.is_file() else RAIZ / ref
    else:
        codigo = str(ref)
        if not codigo.isdigit():   # id de la asesora (serum-vitamina-c) → código
            prod = next((p for p in (leer_json(RAIZ / 'asesora' / 'catalogo.json', {}) or {}).get('productos', [])
                         if p['id'] == ref), None)
            codigo = prod['codigo'] if prod else codigo
        f = None
        for carpeta in (RAIZ / 'agente-contenido' / 'productos', RAIZ / 'lector-farmasi' / 'salida'):
            for datos in carpeta.glob('*/datos.json') if carpeta.is_dir() else []:
                if str((leer_json(datos, {}) or {}).get('codigo')) == codigo and (datos.parent / 'producto.jpg').exists():
                    f = datos.parent / 'producto.jpg'
                    break
            if f:
                break
        if not f:
            f = next(iter(FOTOS.glob(codigo + '.*')), None) if FOTOS.is_dir() else None
        if not f and codigo.isdigit():
            try:
                sys.path.insert(0, str(RAIZ / 'lector-farmasi'))
                import leer
                d = leer.leer_producto(leer.resolver(codigo, leer.mapa_productos()))
                FOTOS.mkdir(parents=True, exist_ok=True)
                f = leer.bajar_foto(d['imagenes_url'][0], FOTOS / codigo, ancho=1080) if d['imagenes_url'] else None
            except Exception as err:  # noqa: BLE001
                print(f'No pude bajar la foto del producto {codigo}: {err}')
        if not f:
            return ''
    tipo = {'.png': 'png', '.webp': 'webp'}.get(f.suffix.lower(), 'jpeg')
    return f'data:image/{tipo};base64,' + base64.b64encode(f.read_bytes()).decode()


def css_historias(k):
    return base_css(k) + '''
.h { background:var(--hueso); padding:150px 100px 170px; display:flex; flex-direction:column; }
.h.oscura { background:var(--tinta); color:var(--hueso); }
.chico { font-size:30px; letter-spacing:.36em; text-transform:uppercase; color:var(--rosa); }
.oscura .chico { color:var(--champan); }
.t { font-family:var(--serif); font-weight:500; font-size:128px; line-height:.98; margin-top:30px; }
.t em { font-style:italic; color:var(--rosa); }
.oscura .t em { color:#e3aeb6; }
.oscura .t { margin-top:auto !important; }
.p { font-size:44px; line-height:1.4; font-weight:300; margin-top:36px; }
.pie { margin-top:auto; display:flex; justify-content:space-between; align-items:flex-end; }
.cta { background:var(--rosa); color:#fff; font-size:38px; letter-spacing:.06em; padding:24px 44px; border-radius:99px; }
.oscura .cta { background:var(--champan); color:var(--tinta); }
.firma { font-family:var(--serif); font-style:italic; font-size:60px; color:var(--rosa); }
.oscura .firma { color:var(--champan); }
.arco { margin:60px auto 0; width:760px; height:860px; border-radius:380px 380px 40px 40px; background:#fff; display:grid; place-items:center; overflow:hidden; box-shadow:0 30px 70px rgba(90,60,40,.12); }
.arco img { width:88%; height:88%; object-fit:contain; }
.comillas { font-family:var(--serif); font-size:340px; line-height:.6; color:var(--champan); margin-top:80px; height:180px; }
.cita { font-family:var(--serif); font-style:italic; font-size:92px; line-height:1.12; }
.quien { font-size:38px; letter-spacing:.2em; text-transform:uppercase; color:var(--rosa); margin-top:50px; }
.estrellas { color:var(--champan); font-size:56px; letter-spacing:.2em; margin-top:20px; }
.mini { display:flex; align-items:center; gap:28px; margin-top:70px; background:#fff; border-radius:30px; padding:20px 34px 20px 20px; width:fit-content; }
.mini img { width:150px; height:150px; object-fit:contain; } .mini span { font-family:var(--serif); font-size:46px; font-weight:600; }
.linea { width:120px; height:3px; background:var(--champan); margin-top:46px; }
.hasta { font-size:36px; color:#cdbfb4; margin-top:30px; letter-spacing:.06em; }
.caja { margin-top:80px; height:560px; border:4px dashed rgba(140,59,74,.35); border-radius:40px; display:grid; place-items:center; font-size:34px; color:rgba(140,59,74,.55); text-align:center; padding:40px; }
.pasos { list-style:none; margin-top:70px; }
.pasos li { display:flex; gap:40px; align-items:center; padding:38px 0; border-bottom:2px solid rgba(179,154,115,.35); font-family:var(--serif); font-size:74px; font-weight:600; }
.pasos li b { flex:0 0 120px; height:120px; border-radius:50%; background:var(--rubor); color:var(--rosa); display:grid; place-items:center; font-size:60px; }
.vacio { color:rgba(34,28,28,.28); }
'''


def historia(k, tipo, d):
    palabra = k.get('palabra_pedido') or 'INFO'
    firma = f'<div class="firma">{e(k["firma"])}</div>'
    cta = f'<div class="cta">Escríbeme {e(palabra)}</div>'
    hueco = lambda v, que: e(v) if v else f'<span class="vacio">{e(que)}</span>'
    if tipo == 'nuevo':
        foto = foto_producto(d.get('producto'))
        return ('', f'<div class="chico">Nuevo en mi tocador</div>'
                    + (f'<div class="arco"><img src="{foto}" alt=""></div>' if foto else '<div class="arco"></div>')
                    + f'<div class="t" style="font-size:96px;margin-top:56px">{hueco(d.get("titulo"), "Nombre del producto")}</div>'
                    + f'<p class="p">{hueco(d.get("texto"), "Una frase sobre por qué te gusta")}</p>'
                    + f'<div class="pie">{cta}{firma}</div>')
    if tipo == 'opinion':
        foto = foto_producto(d.get('producto'))
        mini = (f'<div class="mini"><img src="{foto}" alt=""><span>{e(d.get("titulo") or "")}</span></div>' if foto else '')
        return ('', f'<div class="chico">Lo que dicen ellas</div><div class="comillas">“</div>'
                    f'<div class="cita">{hueco(d.get("texto"), "Lo que te escribió tu clienta")}</div>'
                    f'<div class="estrellas">★★★★★</div><div class="quien">— {hueco(d.get("quien"), "Su nombre")}</div>{mini}'
                    f'<div class="pie">{cta}{firma}</div>')
    if tipo == 'oferta':
        return ('oscura', f'<div class="chico">Solo por estos días</div>'
                          f'<div class="t" style="margin-top:120px">{hueco(d.get("titulo"), "Nombre de la oferta")}</div><div class="linea"></div>'
                          f'<p class="p">{hueco(d.get("texto"), "Qué incluye (y el precio solo si tú lo pones)")}</p>'
                          + (f'<div class="hasta">Hasta el {e(d["hasta"])}</div>' if d.get('hasta') else '')
                          + f'<div class="pie">{cta}{firma}</div>')
    if tipo == 'pregunta':
        return ('', f'<div class="chico">Pregunta del día</div>'
                    f'<div class="t">{hueco(d.get("texto"), "Tu pregunta")}</div>'
                    f'<div class="caja">Pon aquí la encuesta o la caja de preguntas de Instagram</div><div class="pie">{firma}</div>')
    if tipo == 'rutina':
        pasos = d.get('pasos') or []
        filas = ''.join(f'<li><b>{i}</b>{e(p)}</li>' for i, p in enumerate(pasos, 1)) or \
            ''.join(f'<li><b>{i}</b><span class="vacio">Paso {i}</span></li>' for i in range(1, 5))
        return ('', f'<div class="chico">Paso a paso</div><div class="t"><em>{hueco(d.get("titulo"), "Mi rutina")}</em></div>'
                    f'<ol class="pasos">{filas}</ol><div class="pie">{cta}{firma}</div>')
    if tipo == 'gracias':
        quien = d.get('quien')
        return ('oscura', f'<div class="chico">Tu pedido</div><div class="t" style="margin-top:200px">¡Gracias'
                          + (f', <em>{e(quien)}</em>' if quien else '') + '!</div><div class="linea"></div>'
                          f'<p class="p">{e(d.get("texto") or "Gracias por confiar en mí. Cuéntame cómo te va con tus productos: me encanta saber.")}</p>'
                          f'<div class="pie"><span></span>{firma}</div>')
    raise ValueError(f'Tipo de historia desconocido: {tipo}. Usa: {", ".join(TIPOS)}')


def hacer_historias(k, lista, carpeta, nombre):
    piezas = ''
    for tipo, d in lista:
        clase, cuerpo = historia(k, tipo, d)
        piezas += f'<div class="marco"><div class="lienzo h {clase}">{cuerpo}</div></div>'
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f'{nombre}.html'
    archivo.write_text(documento('Historias', css_historias(k), piezas), encoding='utf-8')
    imgs = fotos(archivo)
    if len(lista) == 1 and imgs:
        destino = carpeta / f'{nombre}.png'
        imgs[0].replace(destino)
        imgs = [destino]
    return [archivo] + imgs


def revisar(textos):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('responder', RAIZ / 'comunidad' / 'responder.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return [a for t in textos if t for a in m.revisar_texto(t, (RAIZ / 'comunidad' / 'precios.md').exists())]
    except Exception:  # noqa: BLE001
        return []


# ---------- la guía ----------

def guia(k, carpeta):
    c = k['c']
    colores = ''.join(f'<div class="color"><div class="muestra" style="background:{x["hex"]}"></div><b>{e(x["nombre"])}</b>'
                      f'<code>{e(x["hex"])}</code><p>{e(x["uso"])}</p></div>' for x in k['colores'])
    portadas_html = ''.join(f'<div class="dest"><div class="bola"><svg viewBox="0 0 24 24">{ICONOS[d["icono"]]}</svg></div><span>{e(d["nombre"])}</span></div>'
                            for d in k['destacados'])
    reglas = ''.join(f'<li>{e(r)}</li>' for r in k['reglas'])
    css = f'''
:root {{ --hueso:{c["hueso"]}; --tinta:{c["tinta"]}; --rosa:{c["rosa"]}; --rubor:{c["rubor"]}; --champan:{c["champan"]};
  --serif:{k["letras"]["titulos"]["css"]}; --sans:{k["letras"]["texto"]["css"]}; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:var(--hueso); color:var(--tinta); font-family:var(--sans); }}
main {{ max-width:900px; margin:auto; padding:48px 16px 70px; }}
.chico {{ font-size:12px; letter-spacing:.34em; text-transform:uppercase; color:var(--rosa); }}
h1 {{ font-family:var(--serif); font-style:italic; font-weight:500; font-size:clamp(52px,9vw,84px); line-height:1; margin:8px 0 10px; }}
h2 {{ font-family:var(--serif); font-weight:600; font-size:32px; margin:44px 0 16px; }}
p {{ line-height:1.5; }}
.colores {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:14px; }}
.color {{ background:#fff; border-radius:16px; overflow:hidden; padding-bottom:12px; box-shadow:0 8px 22px rgba(90,60,40,.07); }}
.muestra {{ height:96px; border-bottom:1px solid rgba(0,0,0,.05); }}
.color b, .color code, .color p {{ display:block; padding:0 14px; }} .color b {{ margin-top:10px; }}
.color code {{ font-size:13px; color:#7b6f6a; margin:2px 0 6px; user-select:all; }} .color p {{ font-size:13px; color:#5d5450; }}
.letras {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.letra {{ background:#fff; border-radius:16px; padding:20px; }} .letra .ej1 {{ font-family:var(--serif); font-style:italic; font-size:48px; }}
.letra .ej2 {{ font-family:var(--sans); font-size:22px; }} .letra p {{ font-size:13px; color:#7b6f6a; margin-top:8px; }}
.dests {{ display:flex; flex-wrap:wrap; gap:18px; }}
.dest {{ text-align:center; font-size:13px; }} .bola {{ width:84px; height:84px; border-radius:50%; background:var(--rubor); display:grid; place-items:center; margin-bottom:6px; }}
.bola svg {{ width:40px; fill:none; stroke:var(--rosa); stroke-width:1.3; stroke-linecap:round; stroke-linejoin:round; }}
ul {{ padding-left:20px; }} li {{ margin-bottom:10px; line-height:1.5; }}
@media (max-width:600px) {{ .letras {{ grid-template-columns:1fr; }} }}
'''
    cuerpo = f'''<main><div class="chico">Guía de marca</div><h1>{e(k["firma"])}</h1>
<p>Así se ve todo lo que publica: historias, portadas, anuncios y su página. Si alguien le hace un diseño, le manda esta guía.</p>
<h2>Colores</h2><div class="colores">{colores}</div>
<h2>Letras</h2><div class="letras">
<div class="letra"><div class="ej1">Cormorant</div><p>Para títulos. {e(k["letras"]["titulos"]["en_instagram"])}.</p></div>
<div class="letra"><div class="ej2">Jost: texto corto y claro</div><p>Para el texto. {e(k["letras"]["texto"]["en_instagram"])}.</p></div></div>
<h2>Portadas de destacados</h2><div class="dests">{portadas_html}</div>
<h2>Reglas</h2><ul>{reglas}</ul></main>'''
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / 'guia-de-marca.html'
    archivo.write_text(f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                       f'<title>Guía de marca</title><link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,500;0,600;1,500'
                       f'&family=Jost:wght@300;400;500&display=swap" rel="stylesheet"><style>{css}</style></head><body>{cuerpo}</body></html>',
                       encoding='utf-8')
    return [archivo]


# ---------- comandos ----------

def mostrar(hechos):
    for f in hechos:
        try:
            print('Listo:', Path(f).relative_to(RAIZ))
        except ValueError:
            print('Listo:', f)
    if not any(str(f).endswith('.png') for f in hechos):
        print('(Sin Chromium aquí: abre el .html en el navegador y toma captura de cada pieza.)')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('portadas')
    h = sub.add_parser('historia')
    h.add_argument('tipo', choices=TIPOS)
    h.add_argument('--titulo')
    h.add_argument('--texto')
    h.add_argument('--quien')
    h.add_argument('--producto', help='código de farmasius.com, id de la asesora o ruta de una foto')
    h.add_argument('--hasta')
    h.add_argument('--paso', action='append', dest='pasos')
    h.add_argument('--nombre', help='nombre del archivo (si no, el tipo y la fecha)')
    sub.add_parser('fondos')
    sub.add_parser('guia')
    sub.add_parser('demo')
    a = ap.parse_args()
    k = kit()
    if a.cmd == 'portadas':
        hechos = portadas(k, SALIDA / 'portadas')
        compartir(hechos, 'portadas')
    elif a.cmd == 'historia':
        d = {x: getattr(a, x) for x in ('titulo', 'texto', 'quien', 'producto', 'hasta', 'pasos')}
        for aviso in revisar([d['titulo'], d['texto']]):
            print('REVISAR:', aviso)
        nombre = a.nombre or f"{datetime.date.today().isoformat()}-{a.tipo}-{slug(d['titulo'] or d['quien'] or d['texto'] or '')[:30]}"
        hechos = hacer_historias(k, [(a.tipo, d)], SALIDA / 'historias', nombre)
        compartir(hechos, 'historias')
    elif a.cmd == 'fondos':
        hechos = hacer_historias(k, [(t, {}) for t in TIPOS], SALIDA / 'fondos', 'fondos')
        for img, t in zip([f for f in hechos if f.suffix == '.png'], TIPOS):
            img.replace(img.with_name(f'fondo-{t}.png'))
        hechos = [hechos[0]] + [SALIDA / 'fondos' / f'fondo-{t}.png' for t in TIPOS if (SALIDA / 'fondos' / f'fondo-{t}.png').exists()]
        compartir(hechos, 'fondos')
    elif a.cmd == 'guia':
        hechos = guia(k, SALIDA)
        compartir(hechos, '')
    else:  # demo
        hechos = portadas(k, SALIDA / 'ejemplo') + guia(k, SALIDA / 'ejemplo')
        ejemplos = [('nuevo', {'producto': '1002167', 'titulo': 'Vitamin C Glow Serum', 'texto': 'Mi secreto para una piel con luz desde el primer día.'}),
                    ('opinion', {'texto': 'Me encantó la crema, mi piel se siente suave y sin brillo.', 'quien': 'Carla', 'producto': '1000290', 'titulo': 'Tea Tree Face Cream'}),
                    ('oferta', {'titulo': 'Semana de la piel', 'texto': 'Arma tu rutina conmigo y te llevas una sorpresa.', 'hasta': 'domingo'}),
                    ('pregunta', {'texto': '¿Qué te preocupa más de tu piel?'}),
                    ('rutina', {'titulo': 'Mi rutina de noche', 'pasos': ['Limpia', 'Tónico', 'Sérum', 'Crema']}),
                    ('gracias', {'quien': 'Lucía'})]
        hechos += hacer_historias(k, ejemplos, SALIDA / 'ejemplo', 'historias')
        compartir(hechos, 'ejemplo')
    mostrar(hechos)


if __name__ == '__main__':
    main()
