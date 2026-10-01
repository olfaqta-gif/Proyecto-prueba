#!/usr/bin/env python3
"""Lector de productos de farmasius.com.

Lee la ficha oficial de cada producto (nombre, descripción, ingredientes, precio,
calificación y foto) y la guarda como datos.json + producto.jpg, listos para que el
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
    precio, regular = p.get('price'), p.get('retailPrice')
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
        'precio': {
            'valor': precio,
            'regular': regular,
            'moneda': p.get('currencyCode') or 'USD',
            'texto': f'{p.get("currency") or "$"}{precio:.2f}' if precio is not None else '',
            'oferta_pct': round(100 * (1 - precio / regular)) if precio and regular and precio < regular else 0,
        },
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
    return {
        'imagen': foto.name if foto else '',
        'producto.nombre': re.sub(rf'^{re.escape(d["marca"])}\s+', '', d['nombre']) if d['marca'] else d['nombre'],
        'producto.nombre_corto': f'{marca} · Farmasi' if marca != 'Farmasi' else 'Farmasi',
        'producto.dato': dato,
        'cierre.precio': d['precio']['texto'],
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
        print(f'✓ {d["nombre"]} — {d["precio"]["texto"]}'
              + (f' (antes ${d["precio"]["regular"]:.2f})' if d['precio']['oferta_pct'] else '')
              + (f' — {r["promedio"]} ★ ({r["cantidad"]} reseñas)' if r['cantidad'] else ' — sin reseñas'))
        print(f'  {carpeta}/datos.json' + (f' + {foto.name}' if foto else '  (sin foto)'))
        if len(a.refs) > 1:
            time.sleep(PAUSA)


def cmd_catalogo(a):
    productos = mapa_productos()
    if a.filtro:
        productos = buscar(a.filtro, productos)
    if a.limite:
        productos = productos[:a.limite]
    destino = Path(a.destino)
    destino.mkdir(parents=True, exist_ok=True)
    todos, fallos = [], []
    for i, p in enumerate(productos, 1):
        try:
            d = leer_producto(p['url'])
            if a.fotos:
                guardar(d, destino)
            todos.append(d)
            print(f'[{i}/{len(productos)}] {d["nombre"]}', file=sys.stderr)
        except Exception as e:
            fallos.append({'url': p['url'], 'error': str(e)})
            print(f'[{i}/{len(productos)}] ✗ {p["slug"]}: {e}', file=sys.stderr)
        time.sleep(PAUSA)
    salida = destino / 'catalogo.json'
    salida.write_text(json.dumps({'leido': datetime.date.today().isoformat(), 'fuente': SITIO,
                                  'productos': todos, 'fallos': fallos},
                                 ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(todos)} productos en {salida}' + (f' ({len(fallos)} fallaron)' if fallos else ''))


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

    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
