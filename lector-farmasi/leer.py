#!/usr/bin/env python3
"""Lector de productos de farmasius.com.

Lee la ficha oficial de cada producto (nombre, descripción, ingredientes,
calificación y foto; sin precios) y la guarda como datos.json + producto.jpg, listos para que el
agente de contenido (agente-contenido/) escriba su ficha.json.

Uso:
  python3 leer.py buscar "tea tree"          # lista productos que coinciden
  python3 leer.py producto <url|código|texto> [--destino DIR]
  python3 leer.py catalogo [--destino DIR] [--limite N]

Solo usa la librería estándar de Python. Cada página de producto de farmasius.com
trae sus datos en el HTML (__NEXT_DATA__), así que no hace falta un navegador.
"""
import argparse
import datetime
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SITIO = 'https://www.farmasius.com'
SITEMAP = SITIO + '/sitemap.xml'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36'
PAUSA = 0.6  # segundos entre páginas, para no cargar la tienda

AQUI = Path(__file__).resolve().parent
DESTINO_DEFECTO = AQUI / 'salida'


def bajar(url, intentos=3):
    url = urllib.parse.quote(url, safe=':/?&=%')  # algunas URLs del sitemap traen espacios raros
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception as e:  # red inestable: reintenta con espera creciente
            if i == intentos - 1:
                raise RuntimeError(f'No se pudo leer {url}: {e}') from e
            time.sleep(2 ** (i + 1))


# ---------- mapa del sitio ----------

def mapa_productos():
    """Lista [{codigo, slug, url}] de todos los productos publicados en el sitemap."""
    xml = bajar(SITEMAP).decode('utf-8', 'replace')
    productos = []
    for url in re.findall(r'<loc>\s*([^<]+?)\s*</loc>', xml):
        url = html.unescape(url)
        m = re.search(r'/product-detail/([^?]+)\?pid=(\d+)', url)
        if m:
            productos.append({'codigo': m.group(2), 'slug': m.group(1), 'url': url})
    return productos


def buscar(texto, productos):
    palabras = [p for p in re.split(r'[\s\-]+', texto.lower()) if p]
    return [p for p in productos if all(w in p['slug'] for w in palabras)]


def resolver(ref, productos):
    """Convierte una URL, un código (pid) o un texto en la URL de un producto."""
    if ref.startswith('http'):
        return ref
    if ref.isdigit():
        for p in productos:
            if p['codigo'] == ref:
                return p['url']
        return f'{SITIO}/farmasi/product-detail/producto?pid={ref}'
    exactos = [p for p in productos if p['slug'] == ref.lower()]
    if exactos:
        return exactos[0]['url']
    hallados = buscar(ref, productos)
    if len(hallados) == 1:
        return hallados[0]['url']
    if not hallados:
        sys.exit(f'Ningún producto coincide con "{ref}". Prueba: python3 leer.py buscar "<palabras>"')
    lista = '\n'.join(f'  {p["codigo"]}  {p["slug"]}' for p in hallados[:25])
    sys.exit(f'"{ref}" coincide con {len(hallados)} productos; usa el código:\n{lista}')


# ---------- página de producto ----------

def limpiar(texto):
    if not texto:
        return ''
    texto = re.sub(r'<br\s*/?>', '\n', texto)
    texto = html.unescape(re.sub(r'<[^>]+>', '', texto)).replace(' ', ' ')
    lineas = [re.sub(r'[ \t]+', ' ', l).strip() for l in texto.splitlines()]
    return '\n'.join(l for l in lineas if l)


def separar_ingredientes(texto):
    """La tienda junta 'ingredientes clave: explicación' con la lista INCI completa.
    La lista INCI casi siempre empieza por Water/Aqua; si no, se deja todo junto."""
    m = re.search(r'\b(Water\s*/\s*Aqua|Aqua\s*/\s*Water|Aqua|Water)\b\s*(\(|,)', texto)
    if m:
        return texto[:m.start()].strip(), texto[m.start():].strip()
    # sin agua (maquillaje, aceites): si no hay explicaciones "x: y" y es una lista de comas, es INCI
    if not re.search(r'[A-Za-z]\s*:\s+[a-z]', texto) and texto.count(',') >= 5:
        return '', texto
    return texto, ''


def leer_producto(url):
    pagina = bajar(url).decode('utf-8', 'replace')
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', pagina, re.S)
    if not m:
        raise RuntimeError(f'La página no trae datos de producto: {url}')
    props = json.loads(m.group(1))['props']['pageProps']
    p = props.get('productData') or (props.get('getProductDetailSSR') or {}).get('product')
    if not p:
        raise RuntimeError(f'Producto no encontrado (¿descontinuado?): {url}')

    clave, inci = separar_ingredientes(limpiar(p.get('productTechnicalDetails')))
    detalle = limpiar(p.get('extraDescription'))  # a veces aquí explican los activos
    if detalle and detalle not in clave:
        clave = (clave + '\n' + detalle).strip()
    tamano = re.search(r'(?:Product size|Size|Net (?:wt|content))\s*:\s*([^\n]+)', limpiar(p.get('content')), re.I)
    resenas = p.get('reviews') or {}
    imagenes = [i.get('imageUrl') for i in (p.get('images') or []) if i.get('mediaType', 'image') == 'image']

    tonos = []
    for v in p.get('variants') or []:
        for o in v.get('options') or []:
            tonos.append({'tipo': v.get('key'), 'nombre': o.get('label'), 'codigo': o.get('code'),
                          'disponible': o.get('hasStock'), 'actual': o.get('isSelected')})

    datos = {
        'fuente': p.get('baseUrl') or url,
        'leido': datetime.date.today().isoformat(),
        'codigo': p.get('code'),
        'slug': p.get('slugName'),
        'nombre': p.get('name'),
        'marca': p.get('brandName') or '',
        'etiquetas_tienda': list(dict.fromkeys(c.strip(' !') for c in p.get('categories') or [])),
        'contenido': tamano.group(1).strip() if tamano else '',
        'descripcion': limpiar(p.get('productDescription')),
        'resultados_declarados': limpiar(p.get('provenResults')),
        'ingredientes_clave': clave,
        'ingredientes_inci': inci,
        'modo_de_uso': limpiar(p.get('termOfUse')),
        'atributos': [l for l in limpiar(p.get('sustainability')).splitlines() if l],
        'precauciones': limpiar(p.get('precautions')),
        'resenas': {
            'promedio': resenas.get('avarageRating'),
            'cantidad': resenas.get('count') or 0,
        },
        'tonos': tonos,
        'imagenes_url': imagenes,
        'disponible': bool(p.get('stock')),
        'nuevo': bool(p.get('isNew')),
        'edicion_limitada': bool(p.get('limitedEdition')),
        'descontinuado': bool(p.get('discontinued')),
    }
    return datos


def bajar_foto(url_imagen, archivo, ancho=1080):
    """Baja la foto a través del optimizador de imágenes del propio sitio
    (content.farmasius.com no siempre es accesible directamente)."""
    caminos = [f'{SITIO}/_next/image?url={urllib.parse.quote(url_imagen, safe="")}&w={ancho}&q=90', url_imagen]
    for c in caminos:
        try:
            datos = bajar(c, intentos=2)
        except RuntimeError:
            continue
        if datos[:3] == b'\xff\xd8\xff':
            ext = '.jpg'
        elif datos[:8] == b'\x89PNG\r\n\x1a\n':
            ext = '.png'
        elif datos[:4] == b'RIFF' and datos[8:12] == b'WEBP':
            ext = '.webp'
        else:
            continue
        destino = archivo.with_suffix(ext)
        destino.write_bytes(datos)
        return destino
    return None


def para_ficha(d, foto):
    """Los campos de la ficha del agente de contenido que salen tal cual de la tienda.
    El copy (gancho, beneficios, cierre, caption) lo escribe el agente en español."""
    r = d['resenas']
    dato = {}
    if r['cantidad'] and r['promedio']:
        dato = {'destacado': '★' * max(1, round(r['promedio'])),
                'texto': f'{r["promedio"]:.2f}'.rstrip('0').rstrip('.') + f' · {r["cantidad"]} reseñas'}
    marca = d['marca'] or 'Farmasi'
    nombre = re.sub(rf'^{re.escape(d["marca"])}\s+', '', d['nombre']) if d['marca'] else d['nombre']
    return {  # misma forma que ficha.json: se copia tal cual y se completa el resto
        'imagen': foto.name if foto else '',
        'producto': {
            'nombre': nombre,
            'nombre_corto': f'{marca} · Farmasi' if marca != 'Farmasi' else 'Farmasi',
            'dato': dato,
        },
    }


def guardar(d, destino, con_foto=True):
    carpeta = destino / d['slug']
    carpeta.mkdir(parents=True, exist_ok=True)
    foto = None
    if con_foto and d['imagenes_url']:
        foto = bajar_foto(d['imagenes_url'][0], carpeta / 'producto')
    d = dict(d, imagen=foto.name if foto else '', para_ficha=para_ficha(d, foto))
    (carpeta / 'datos.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return carpeta, foto


# ---------- comandos ----------

def cmd_buscar(a):
    hallados = buscar(a.texto, mapa_productos())
    for p in hallados:
        print(f'{p["codigo"]}  {p["slug"]}')
    print(f'\n{len(hallados)} productos.', file=sys.stderr)


def cmd_producto(a):
    productos = mapa_productos()
    destino = Path(a.destino)
    for ref in a.refs:
        d = leer_producto(resolver(ref, productos))
        carpeta, foto = guardar(d, destino, con_foto=not a.sin_foto)
        r = d['resenas']
        print(f'✓ {d["nombre"]}'
              + (f' — {r["promedio"]} ★ ({r["cantidad"]} reseñas)' if r['cantidad'] else ' — sin reseñas'))
        print(f'  {carpeta}/datos.json' + (f' + {foto.name}' if foto else '  (sin foto)'))
        if len(a.refs) > 1:
            time.sleep(PAUSA)


def leer_varios(productos, hilos=3):
    """Lee muchas páginas con pocas conexiones a la vez. Devuelve (datos, fallos)."""
    from concurrent.futures import ThreadPoolExecutor

    def uno(p):
        time.sleep(PAUSA)
        try:
            return leer_producto(p['url']), None
        except Exception as e:
            return None, {'url': p['url'], 'error': str(e)}

    todos, fallos = [], []
    with ThreadPoolExecutor(hilos) as ex:
        for i, (d, fallo) in enumerate(ex.map(uno, productos), 1):
            if d:
                todos.append(d)
            else:
                fallos.append(fallo)
            if i % 25 == 0 or i == len(productos):
                print(f'  leídos {i}/{len(productos)}', file=sys.stderr)
    return todos, fallos


def guardar_catalogo(todos, fallos, archivo):
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps({'leido': datetime.date.today().isoformat(), 'fuente': SITIO,
                                   'productos': todos, 'fallos': fallos},
                                  ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def cmd_catalogo(a):
    productos = mapa_productos()
    if a.filtro:
        productos = buscar(a.filtro, productos)
    if a.limite:
        productos = productos[:a.limite]
    destino = Path(a.destino)
    todos, fallos = leer_varios(productos)
    if a.fotos:
        for d in todos:
            guardar(d, destino)
    salida = destino / ('catalogo.json' if not (a.filtro or a.limite) else 'catalogo-parcial.json')
    guardar_catalogo(todos, fallos, salida)
    print(f'{len(todos)} productos en {salida}' + (f' ({len(fallos)} fallaron)' if fallos else ''))


NO_VENTA = re.compile(r'tester|sample|muestra|starter-kit|business-kit|catalog|brochure|bag\b')


def cmd_mejores(a):
    """Los N productos mejor calificados (promedio y luego cantidad de reseñas)."""
    destino = Path(a.destino)
    cache = destino / 'catalogo.json'
    hoy = datetime.date.today().isoformat()
    todos = None
    if cache.exists() and not a.actualizar:
        c = json.loads(cache.read_text(encoding='utf-8'))
        if c.get('leido') == hoy:
            todos = c['productos']
            print(f'Usando el catálogo leído hoy ({len(todos)} productos).', file=sys.stderr)
    if todos is None:
        productos = mapa_productos()
        print(f'Leyendo el catálogo completo ({len(productos)} productos)…', file=sys.stderr)
        todos, fallos = leer_varios(productos)
        guardar_catalogo(todos, fallos, cache)

    candidatos = [d for d in todos
                  if d['resenas']['cantidad'] >= a.min_resenas and d['resenas']['promedio']
                  and d['disponible'] and not d['descontinuado'] and not NO_VENTA.search(d['slug'])]
    if a.filtro:
        palabras = [w for w in re.split(r'[\s\-]+', a.filtro.lower()) if w]
        candidatos = [d for d in candidatos
                      if all(w in (d['slug'] + ' ' + d['marca'].lower()) for w in palabras)]
    candidatos.sort(key=lambda d: (d['resenas']['promedio'], d['resenas']['cantidad']), reverse=True)

    top = candidatos[:a.n]
    for i, d in enumerate(top, 1):
        carpeta, foto = guardar(d, destino)
        r = d['resenas']
        print(f'{i}. {d["nombre"]} — {r["promedio"]} ★ ({r["cantidad"]} reseñas) — código {d["codigo"]}')
        print(f'   {carpeta}/datos.json' + (f' + {foto.name}' if foto else '  (sin foto)'))
    if not top:
        print('Ningún producto cumple el filtro.')
        return
    vitrina = destino / 'vitrina.html'
    vitrina.write_text(hacer_vitrina(top, a.filtro), encoding='utf-8')
    print(f'\nVitrina para ver con fotos: {vitrina}')


def hacer_vitrina(productos, filtro=None):
    """Página simple con foto, nombre, calificación y descripción de cada producto."""
    tarjetas = []
    for i, d in enumerate(productos, 1):
        r = d['resenas']
        esc = html.escape
        tarjetas.append(f'''<article>
  <span class="n">{i}</span>
  <img src="{esc(d['slug'])}/producto.jpg" alt="{esc(d['nombre'])}">
  <h2>{esc(d['nombre'])}</h2>
  <p class="r">{'★' * round(r['promedio'])} {r['promedio']} · {r['cantidad']} reseñas</p>
  <p>{esc(d['descripcion'][:260])}{'…' if len(d['descripcion']) > 260 else ''}</p>
  <p class="c">Código {esc(d['codigo'])} · <a href="{esc(d['fuente'])}">ver en la tienda</a></p>
</article>''')
    titulo = 'Mejores reseñas' + (f' · {html.escape(filtro)}' if filtro else '')
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{titulo}</title>
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#faf7f5;color:#2a2224}}
h1{{text-align:center;font-weight:600;margin:28px 16px 8px}} .sub{{text-align:center;color:#7a6c70;margin:0 16px 24px}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;max-width:1100px;margin:auto;padding:0 16px 40px}}
article{{background:#fff;border-radius:16px;padding:18px;box-shadow:0 2px 12px #0001;position:relative}}
img{{width:100%;aspect-ratio:1;object-fit:contain;border-radius:12px;background:#fff}}
.n{{position:absolute;top:12px;left:12px;background:#c2185b;color:#fff;border-radius:50%;width:32px;height:32px;display:grid;place-items:center;font-weight:700}}
h2{{font-size:1.1rem;margin:12px 0 4px}} .r{{color:#b8860b;margin:0 0 8px}} .c{{font-size:.85rem;color:#7a6c70}}
a{{color:#c2185b}}
</style></head><body><h1>{titulo}</h1><p class="sub">Datos de farmasius.com · leídos el {datetime.date.today().isoformat()}</p>
<main>{''.join(tarjetas)}</main></body></html>
'''


def main():
    ap = argparse.ArgumentParser(description='Lector de productos de farmasius.com')
    sub = ap.add_subparsers(dest='cmd', required=True)

    b = sub.add_parser('buscar', help='buscar productos por palabras del nombre')
    b.add_argument('texto')
    b.set_defaults(f=cmd_buscar)

    p = sub.add_parser('producto', help='leer uno o varios productos')
    p.add_argument('refs', nargs='+', help='URL, código (pid) o palabras del nombre')
    p.add_argument('--destino', default=str(DESTINO_DEFECTO), help='carpeta donde crear <slug>/datos.json')
    p.add_argument('--sin-foto', action='store_true', help='no bajar la foto')
    p.set_defaults(f=cmd_producto)

    c = sub.add_parser('catalogo', help='leer todo el catálogo (o lo que coincida con --filtro)')
    c.add_argument('--destino', default=str(DESTINO_DEFECTO))
    c.add_argument('--filtro', help='solo productos cuyo nombre tenga estas palabras')
    c.add_argument('--limite', type=int, help='máximo de productos a leer')
    c.add_argument('--fotos', action='store_true', help='crear también <slug>/datos.json + foto por producto')
    c.set_defaults(f=cmd_catalogo)

    m = sub.add_parser('mejores', help='los N productos con mejores reseñas (con datos.json y foto)')
    m.add_argument('n', nargs='?', type=int, default=3)
    m.add_argument('--filtro', help='solo productos cuyo nombre o marca tenga estas palabras')
    m.add_argument('--min-resenas', type=int, default=50, help='mínimo de reseñas para contar (defecto 50)')
    m.add_argument('--actualizar', action='store_true', help='volver a leer el catálogo aunque ya se haya leído hoy')
    m.add_argument('--destino', default=str(DESTINO_DEFECTO))
    m.set_defaults(f=cmd_mejores)

    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
