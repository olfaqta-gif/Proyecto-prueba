"""Convierte un guion educativo (tips, mito vs realidad, pasos, ¿sabías que?) en un reel con
motion graphics y música propia, en 4 formatos, y si se pide, en carrusel de imágenes.

    python3 generar.py temas/<slug>                      # HTML + caption + vistas previas
    python3 generar.py temas/<slug> --video              # además los MP4 con música y efectos
    python3 generar.py temas/<slug> --carrusel           # además las imágenes del carrusel (4:5)
    python3 generar.py temas/<slug> --formatos 9x16,1x1  # solo esos formatos
    python3 generar.py temas/<slug> --variacion 3        # otra música, otras transiciones

Todo sale en salida/<slug>/:
    caption.txt              texto listo para pegar
    video-<formato>.html     la animación (se abre en cualquier navegador)
    previa-<formato>.jpg     cuadros clave para revisar
    video-<formato>.mp4      video final (con --video)
    carrusel/01.jpg …        una imagen por pantalla (con --carrusel)

Reutiliza de agente-contenido/: el motor de la plantilla (base.css, base.js), las fuentes,
el render cuadro por cuadro (render.cjs) y los instrumentos de sonido.py.
"""
import argparse
import base64
import importlib.util
import json
import random
import re
import shutil
import sys
import tempfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / 'herramientas'))
import rutas  # noqa: E402  (node y ffmpeg que deja herramientas/instalar_videos.py)
rutas.preparar()
AC = RAIZ / 'agente-contenido'
sys.path.insert(0, str(AC))      # sonido.py
sys.path.insert(0, str(AQUI))    # musica.py
# El generador de anuncios (formatos, render y video) se carga con otro nombre para no chocar con este archivo
_spec = importlib.util.spec_from_file_location('anuncios', AC / 'generar.py')
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)

PLANTILLA = AQUI / 'plantilla'
TIPOS = ['tips', 'mito', 'pasos', 'dato']
FORMATOS = ac.FORMATOS
ACCIONES = {
    'guardar': ('guardar', 'Guárdalo para después 🔖'),
    'compartir': ('compartir', 'Compártelo con tu amiga 💌'),
    'seguir': ('corazon', 'Sígueme para más ✨'),
    'escribir': ('mensaje', ''),
}
ETIQUETAS = {'tips': 'Tip', 'mito': 'Mito', 'pasos': 'Paso', 'dato': 'Dato'}
CANTIDAD = {'tips': (2, 5), 'mito': (1, 3), 'pasos': (2, 5), 'dato': (1, 3)}
TRANSICIONES = {'tips': ['iris', 'wipe', 'diag', 'sube', 'zoom'], 'mito': ['iris', 'zoom'],
                'pasos': ['push'], 'dato': ['zoom', 'iris', 'diag', 'sube']}
KINETICOS = ['kin-sube', 'kin-pop', 'kin-desliza']
# Palabras que no pueden ir en contenido de Farmasi (promesas médicas o de dinero)
PROHIBIDAS = ['cura', 'curar', 'elimina', 'garantiza', 'garantizado', 'milagro', 'adelgaza', 'quema grasa',
              'trata el acné', 'medicamento', 'ganar dinero', 'ingresos', 'hazte rica']
LARGOS = {'gancho.kicker': 30, 'gancho.titulo': 60, 'gancho.subtitulo': 70, 'cierre.frase1': 26, 'cierre.frase2': 26,
          'cierre.palabra': 12}
LARGO_ITEM = {'titulo': 60, 'detalle': 90, 'mito': 90, 'realidad': 150, 'clave': 18, 'unidad': 14}


def palabras(s):
    return len(re.sub(r'\*', '', s or '').split())


def limpiar(s):
    return re.sub(r'\*', '', s or '')


def get(o, path):
    return ac.get(o, path)


# ---------------- validación ----------------
def validar(g):
    errores, avisos = [], []
    tipo = g.get('tipo')
    if tipo not in TIPOS:
        return [f'"tipo" debe ser uno de: {", ".join(TIPOS)}'], []
    for k in ('gancho.titulo', 'cierre.frase1', 'caption.texto', 'caption.hashtags'):
        if not get(g, k):
            errores.append(f'falta "{k}"')
    items = g.get('items') or []
    lo, hi = CANTIDAD[tipo]
    if not lo <= len(items) <= hi:
        errores.append(f'un "{tipo}" lleva entre {lo} y {hi} items (tiene {len(items)})')
    for i, it in enumerate(items):
        n = i + 1
        if tipo == 'mito':
            for k in ('mito', 'realidad'):
                if not it.get(k):
                    errores.append(f'item {n}: falta "{k}"')
        elif not it.get('titulo'):
            errores.append(f'item {n}: falta "titulo"')
        if tipo == 'dato' and it.get('numero') and not it.get('fuente'):
            errores.append(f'item {n}: una cifra necesita "fuente" (de dónde sale el dato)')
        for k, lim in LARGO_ITEM.items():
            v = limpiar(str(it.get(k) or ''))
            if len(v) > lim:
                avisos.append(f'item {n}: "{k}" tiene {len(v)} caracteres (recomendado ≤ {lim}); la letra se achicará')
    for k, lim in LARGOS.items():
        v = limpiar(get(g, k) or '')
        if len(v) > lim:
            avisos.append(f'"{k}" tiene {len(v)} caracteres (recomendado ≤ {lim}); la letra se achicará')
    accion = get(g, 'cierre.accion') or ('escribir' if get(g, 'cierre.palabra') else 'guardar')
    if accion not in ACCIONES:
        errores.append(f'"cierre.accion" debe ser una de: {", ".join(ACCIONES)}')
    if accion == 'escribir' and not get(g, 'cierre.palabra'):
        errores.append('"cierre.accion" = escribir necesita "cierre.palabra"')
    if g.get('paleta', 'coral') not in ac.PALETAS:
        errores.append(f'"paleta" debe ser una de: {", ".join(sorted(ac.PALETAS))}')
    if g.get('fondo', 'claro') not in ('claro', 'oscuro'):
        errores.append('"fondo" debe ser "claro" u "oscuro"')
    texto = json.dumps({k: v for k, v in g.items() if k != 'caption'}, ensure_ascii=False).lower() + ' ' + \
        str(get(g, 'caption.texto') or '').lower()
    for p in PROHIBIDAS:
        if re.search(r'\b' + re.escape(p) + r'\b', texto):
            errores.append(f'el texto dice "{p}": sin promesas médicas, de peso ni de dinero')
    if '%' in texto:
        avisos.append('hay un "%": usa porcentajes solo si vienen de una fuente que puedas citar')
    tags = get(g, 'caption.hashtags') or []
    if len(tags) > 30:
        errores.append('Instagram acepta máximo 30 hashtags')
    return errores, avisos


# ---------------- producto opcional (al final: "Lo que yo uso") ----------------
def foto_producto(g):
    p = g.get('producto') or {}
    if not p:
        return '', {}
    carpeta = RAIZ / p['carpeta'] if p.get('carpeta') else None
    datos = {}
    for nombre in ('ficha.json', 'datos.json'):
        if carpeta and (carpeta / nombre).exists():
            datos = json.loads((carpeta / nombre).read_text())
            break
    nombre = p.get('nombre') or get(datos, 'producto.nombre') or datos.get('nombre')
    img = None
    if p.get('imagen'):
        img = (carpeta or AQUI) / p['imagen']
    elif carpeta:
        img = next((carpeta / x for x in (datos.get('imagen') or '', 'producto.jpg', 'producto.png', 'producto.webp')
                    if x and (carpeta / x).exists()), None)
    info = {'nombre': nombre, 'texto': p.get('texto') or 'Lo que yo uso'}
    if img and img.exists():
        info['imagen'] = img.name
        mime = ac.MIME.get(img.suffix.lower(), 'image/jpeg')
        return f'data:{mime};base64,' + base64.b64encode(img.read_bytes()).decode(), info
    return '', info


# ---------------- línea de tiempo ----------------
def armar(g, variacion):
    """Ficha completa (F) y línea de tiempo (T) con los momentos de cada animación y sonido."""
    tipo = g['tipo']
    rnd = random.Random(zlib.crc32((limpiar(g['gancho']['titulo']) + tipo).encode()) + variacion * 7919)
    F = json.loads(json.dumps(g))
    F['etiqueta'] = F.get('etiqueta') or ETIQUETAS[tipo]
    F['firma'] = F.get('firma') or (get(g, 'cierre.usuario') or 'FARMASi')
    F['paleta'] = F.get('paleta') or rnd.choice(sorted(ac.PALETAS))
    F['fondo'] = F.get('fondo') or rnd.choice(['claro', 'oscuro'])
    c = F.setdefault('cierre', {})
    accion = c.get('accion') or ('escribir' if c.get('palabra') else 'guardar')
    c['icono'], texto = ACCIONES[accion]
    c['accion_texto'] = c.get('accion_texto') or texto
    c.setdefault('boton_pre', 'Escríbeme')
    if c.get('palabra'):
        c['accion_texto'] = ''
    ev = []                                   # (segundo, efecto) para el sonido
    T = {'gancho': {}, 'items': [], 'cierre': {}}
    capturas = []

    # gancho
    G = T['gancho']
    G['insignia'] = 0.1
    G['kicker'] = 0.25 if tipo != 'mito' else 0.9
    G['titulo'] = G['kicker'] + 0.25
    n = palabras(g['gancho']['titulo'])
    G['subtitulo'] = G['titulo'] + n * 0.09 + 0.25
    fin_texto = G['subtitulo'] + (0.5 if get(g, 'gancho.subtitulo') else 0)
    G['sale'] = round(max(2.8, fin_texto + 1.3 + 0.12 * palabras(get(g, 'gancho.subtitulo'))), 2)
    ev += [(0.0, 'intro'), (G['insignia'], 'pop'), (G['titulo'], 'palabras', n, 0.09)]
    if tipo == 'mito':
        ev += [(G['insignia'], 'golpe'), (G['insignia'] + 0.45, 'golpe')]
    if tipo == 'pasos':
        ev += [(G['insignia'] + 0.2 + k * 0.12, 'tic') for k in range(len(g['items']))]
    capturas.append(G['sale'] - 0.35)

    t = G['sale']
    tr = TRANSICIONES[tipo]
    for i, it in enumerate(g['items']):
        I = {'entra': round(t, 2)}
        ev.append((t - 0.15, 'whoosh'))
        if tipo == 'mito':
            nm, nr = palabras(it['mito']), palabras(it['realidad'])
            I['mito'] = t + 0.55
            I['sello'] = I['mito'] + nm * 0.06 + max(0.9, 0.17 * nm)
            I['giro'] = I['sello'] + 0.85
            I['realidad_t'] = I['giro'] + 0.5
            dur = I['realidad_t'] - t + nr * 0.055 + max(1.6, 0.19 * nr)
            ev += [(I['mito'], 'palabras', nm, 0.06), (I['sello'], 'sello'), (I['giro'], 'giro'), (I['giro'] + 0.5, 'bien')]
            capturas += [I['sello'] + 0.7, t + dur - 0.3]
        else:
            nt, nd = palabras(it.get('titulo')), palabras(it.get('detalle'))
            I['cifra'] = t + 0.3
            I['titulo'] = t + (0.95 if tipo == 'dato' and (it.get('numero') or it.get('clave')) else 0.5)
            I['detalle'] = I['titulo'] + nt * 0.08 + 0.3
            lectura = 0.2 * (nt + nd)
            base = {'tips': (2.8, 4.3), 'pasos': (2.6, 4.0), 'dato': (3.6, 5.4)}[tipo]
            dur = min(max(I['detalle'] - t + 0.8 + lectura, base[0]), base[1])
            ev += [(t + 0.15, 'pop'), (I['titulo'], 'palabras', nt, 0.08)]
            if tipo == 'dato' and it.get('numero'):
                ev.append((I['cifra'], 'cuenta'))
            elif tipo == 'dato' and it.get('clave'):
                ev.append((I['cifra'], 'golpe'))
            else:
                ev.append((t + 0.45 + 0.6, 'ding'))
            if tipo == 'pasos':
                ev.append((t + 0.3, 'tic'))
            capturas.append(t + dur - 0.3)
            F['items'][i].setdefault('icono', 'chispa')
            if tipo == 'dato':
                if not (it.get('numero') or it.get('clave')):
                    F['items'][i]['solo_icono'] = True
                if it.get('fuente'):
                    F['items'][i]['fuente_txt'] = 'Fuente: ' + it['fuente']
        if tipo == 'mito':
            F['items'][i]['sello'] = it.get('sello') or 'FALSO'
        I['sale'] = round(t + dur, 2)
        I['tr'] = tr[(i + rnd.randrange(len(tr))) % len(tr)] if len(tr) > 1 else tr[0]
        T['items'].append(I)
        t = I['sale']

    C = T['cierre']
    C['entra'] = round(t, 2)
    C['medalla'] = t + 0.15
    C['marca'] = t + 0.4
    C['frase1'] = t + 0.6
    C['frase2'] = C['frase1'] + palabras(c.get('frase1')) * 0.1 + 0.15
    C['boton'] = C['frase2'] + 0.55
    C['producto'] = C['boton'] + 0.35
    C['aviso'] = C['producto'] + 0.3
    D = C['aviso'] + 2.4 + (0.5 if F.get('producto') else 0)
    ev += [(t - 0.15, 'whoosh'), (C['medalla'], 'pop'), (C['medalla'] + 0.6, 'ding'), (C['marca'], 'golpe'),
           (C['frase1'], 'palabras', palabras(c.get('frase1')), 0.1), (C['boton'], 'boton'), (D - 1.6, 'final')]
    capturas.append(D - 0.15)
    T['duracion'] = round(D, 2)
    T['eventos'] = [list(e) for e in sorted(ev, key=lambda e: e[0])]
    T['capturas'] = [round(x, 2) for x in capturas]
    T['drop'] = T['items'][0]['entra']
    T['transicion_cierre'] = rnd.choice(['iris', 'diag', 'zoom'])
    T['kin'] = rnd.choice(KINETICOS)
    T['clases'] = [['', 'color', '', 'color2', ''][(k + rnd.randrange(2)) % 5] if tipo in ('tips', 'dato') else ''
                   for k in range(len(g['items']))]
    return F, T


# ---------------- HTML ----------------
def secciones(tipo):
    txt = (PLANTILLA / 'tipos' / f'{tipo}.html').read_text()
    estilo = txt.split('<!--INSIGNIA-->')[0]
    resto = txt.split('<!--INSIGNIA-->')[1]
    insignia, resto = resto.split('<!--ITEM-->')
    item, extra = (resto.split('<!--EXTRA-->') + [''])[:2]
    return estilo, insignia, item, extra


def armar_html(F, T, img, formato, modo='video'):
    tipo = F['tipo']
    N = len(F['items'])
    estilo, insignia, item, extra = secciones(tipo)
    escenas = []
    for i, I in enumerate(T['items']):
        prog = ''.join(
            f'<i class="lleno"></i>' if k < i else
            (f'<i class="activo" data-d="items.{i}.entra+0.3" style="--dur:{I["sale"] - I["entra"] - 0.3:.2f}s"></i>' if k == i else '<i></i>')
            for k in range(N))
        cuerpo = (item.replace('{PROGRESO}', prog).replace('{i}', str(i)).replace('{n1}', str(i + 1))
                  .replace('{n}', f'{i + 1:02d}').replace('{N}', str(N)))
        capa = 'capa b' if i % 2 else 'capa'
        tapa = f'items.{i + 1}.entra+0.9' if i + 1 < N else 'cierre.entra+0.9'   # cuando la tapa la escena siguiente
        escenas.append(f'<div class="{capa} tr-{I["tr"]}" data-in="items.{i}.entra-0.12" data-out="items.{i}.entra+0.9"></div>\n'
                       f'<section class="escena {T["clases"][i]} tr-{I["tr"]}" data-in="items.{i}.entra" data-out="{tapa}">\n{cuerpo}</section>')
    puntos = ''.join(f'<i class="lleno" data-d="gancho.insignia+{0.2 + k * 0.12:.2f}">{k + 1}</i>' for k in range(N))
    nodos = ''.join(f'<div class="nodo">{k + 1}<b class="crece" data-d="items.{k}.entra+0.35">{k + 1}</b></div>' for k in range(N))
    avance = ''.join(
        f'<div class="avance" style="animation:avanza{k} .6s cubic-bezier(.6,0,.3,1) var(--d) both" data-d="items.{k}.entra+0.1"></div>'
        f'<style>@keyframes avanza{k}{{from{{transform:scaleX({(k - 1) / (N - 1):.4f})}}to{{transform:scaleX({k / (N - 1):.4f})}}}}</style>'
        for k in range(1, N))
    insignia = insignia.replace('{PUNTOS_GANCHO}', puntos)
    extra = extra.replace('{NODOS}', nodos).replace('{AVANCE}', avance)
    cuerpo = ((PLANTILLA / 'comun.html').read_text()
              .replace('{{INSIGNIA}}', insignia).replace('{{ESCENAS}}', '\n'.join(escenas))
              .replace('{{EXTRA}}', extra).replace('{{TR_CIERRE}}', T['transicion_cierre'])
              .replace('{{CLASE_GANCHO}}', '').replace('{kin}', T['kin']))
    cuerpo = ac.unidades(estilo + cuerpo)
    w, h, u, orient = FORMATOS[formato]
    ficha_js = json.dumps(F, ensure_ascii=False).replace('</', '<\\/')
    Tjs = {k: v for k, v in T.items() if k not in ('eventos',)}
    return f"""<!doctype html>
<html lang="es" data-tipo="{tipo}" data-formato="{formato}" data-orient="{orient}" data-fondo="{F['fondo']}" data-modo="{modo}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{limpiar(F['gancho']['titulo'])}</title>
<style>{(AC / 'plantilla' / 'fonts' / 'fonts.css').read_text()}</style>
<style>:root{{--W:{w}px;--H:{h}px;--u:{u}}}
{ac.unidades((AC / 'plantilla' / 'base.css').read_text())}
{ac.unidades((PLANTILLA / 'edu.css').read_text())}</style>
</head>
<body>
<div id="stage">
{cuerpo}
</div>
<script>
const T = {json.dumps(Tjs)};
const F = {ficha_js};
const IMG = "{img}";
const W = {w}, H = {h};
{(AC / 'plantilla' / 'base.js').read_text()}
{(PLANTILLA / 'edu.js').read_text()}
</script>
</body>
</html>
"""


# ---------------- salidas ----------------
def capturar(html, carpeta, formato, T, tiempos):
    ac.subprocess.run(['node', str(AC / 'render.cjs'), str(html), 'preview', str(carpeta), str(T['duracion']),
                       ','.join(f'{x:.2f}' for x in tiempos), *map(str, FORMATOS[formato][:2])], check=True)
    return sorted(Path(carpeta).glob('p_*.jpg'))


def previa(html, destino, formato, T):
    with tempfile.TemporaryDirectory() as tmp:
        fotos = capturar(html, tmp, formato, T, T['capturas'])
        w, h = FORMATOS[formato][:2]
        alto = 420 if h >= w else 260
        por_fila = min(len(fotos), 6)
        filas = -(-len(fotos) // por_fila)
        ac.subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{tmp}/p_%02d.jpg', '-vf',
                           f'scale=-2:{alto},tile={por_fila}x{filas}:padding=8:color=white', '-frames:v', '1',
                           str(destino)], check=True)
    return destino


def carrusel(F, T, img, out, formato):
    dest = out / 'carrusel'
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    html = out / f'carrusel-{formato}.html'
    html.write_text(armar_html(F, T, img, formato, 'carrusel'))
    with tempfile.TemporaryDirectory() as tmp:
        for k, f in enumerate(capturar(html, tmp, formato, T, T['capturas'])):
            shutil.copy(f, dest / f'{k + 1:02d}.jpg')
    html.unlink()
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tema', help='carpeta del tema (con guion.json)')
    ap.add_argument('--formatos', help=f'{",".join(FORMATOS)} o "todos" (defecto: los del guion, o todos)')
    ap.add_argument('--video', action='store_true', help='renderizar también los MP4 con sonido')
    ap.add_argument('--carrusel', action='store_true', help='exportar una imagen por pantalla (4:5) para carrusel')
    ap.add_argument('--sin-previa', action='store_true', help='no generar las vistas previas')
    ap.add_argument('--variacion', type=int, help='otro número = otra música, transiciones y colores (defecto: el del guion o 0)')
    a = ap.parse_args()

    dir_tema = Path(a.tema).resolve()
    guion = json.loads((dir_tema / 'guion.json').read_text())
    errores, avisos = validar(guion)
    for x in avisos:
        print('aviso:', x)
    if errores:
        for x in errores:
            print('ERROR:', x)
        sys.exit(1)
    fmt_guion = ','.join(guion['formatos']) if guion.get('formatos') else None
    formatos = ac.lista(a.formatos or fmt_guion, FORMATOS, 'formato')
    variacion = a.variacion if a.variacion is not None else int(get(guion, 'musica.variacion') or 0)

    F, T = armar(guion, variacion)
    img, prod = foto_producto(guion)
    if prod:
        F['producto'] = prod
    import musica
    T['musica'] = musica.elegir(F, T, variacion)
    print(f'· {F["tipo"]}: {T["duracion"]:.1f} s · paleta {F["paleta"]} · fondo {F["fondo"]} · '
          f'música «{T["musica"]["ambiente"]}» en {T["musica"]["tono"]} a {T["musica"]["bpm"]} bpm')

    out = AQUI / 'salida' / dir_tema.name
    out.mkdir(parents=True, exist_ok=True)
    (out / 'caption.txt').write_text(ac.armar_caption(guion))
    print('✓', (out / 'caption.txt').relative_to(AQUI))
    htmls = {}
    for fmt in formatos:
        htmls[fmt] = out / f'video-{fmt}.html'
        htmls[fmt].write_text(armar_html(F, T, img, fmt))
        print('✓', htmls[fmt].relative_to(AQUI))
    with ThreadPoolExecutor(max_workers=3) as pool, tempfile.TemporaryDirectory() as tmp:
        if not a.sin_previa:
            for r in pool.map(lambda fmt: previa(htmls[fmt], out / f'previa-{fmt}.jpg', fmt, T), formatos):
                print('✓', r.relative_to(AQUI))
        if a.carrusel:
            r = carrusel(F, T, img, out, '4x5')
            print('✓', r.relative_to(AQUI), f'({len(list(r.glob("*.jpg")))} imágenes)')
        if a.video:
            print('· sintetizando música y efectos…')
            wav = Path(tmp) / 'audio.wav'
            musica.generar(T, F, str(wav))
            print(f'· capturando cuadros y codificando {len(formatos)} video(s)…')
            for r in pool.map(lambda fmt: ac.video(htmls[fmt], out / f'video-{fmt}.mp4', fmt, T, wav), formatos):
                print('✓', r.relative_to(AQUI))


if __name__ == '__main__':
    main()
