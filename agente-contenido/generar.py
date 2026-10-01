"""Convierte la ficha de un producto en anuncios de 15 s (varios estilos y formatos) + caption.

    python3 generar.py productos/<slug>                          # HTML + caption + vistas previas
    python3 generar.py productos/<slug> --video                  # además los MP4 con sonido
    python3 generar.py productos/<slug> --estilo razones         # otro estilo (o "todos")
    python3 generar.py productos/<slug> --formatos 9x16,1x1      # solo esos formatos

Estilos: clasico (problema → solución), favorito (mi favorito, tipo TikTok), razones (3 razones).
Formatos: 9x16 (Reels/TikTok/Stories), 4x5 (feed de Instagram/Facebook), 1x1 (cuadrado), 16x9 (YouTube).

Todo sale en salida/<slug>/:
    caption.txt                    texto listo para pegar en Instagram / TikTok / Facebook
    <estilo>/anuncio-<formato>.html   el anuncio animado (se abre en cualquier navegador)
    <estilo>/previa-<formato>.jpg     cuadros clave para revisar
    <estilo>/anuncio-<formato>.mp4    video final (solo con --video)
"""
import argparse
import base64
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / 'plantilla'
PALETAS = {'coral', 'dorado', 'verde', 'lavanda', 'rosa'}
ESTILOS = ['clasico', 'favorito', 'razones']
# formato -> (ancho, alto, escala u, orientación). u escala todas las medidas del diseño vertical.
FORMATOS = {
    '9x16': (1080, 1920, 1.0, 'v'),
    '4x5': (1080, 1350, 0.78, 'v'),
    '1x1': (1080, 1080, 0.68, 'v'),
    '16x9': (1920, 1080, 0.9, 'h'),
}
MIME = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}

# Campo -> largo máximo recomendado (caracteres). Más largo se ve apretado en pantalla.
LARGOS = {
    'gancho.kicker': 32, 'gancho.linea1': 40, 'gancho.linea2': 28,
    'producto.categoria': 24, 'producto.nombre': 34, 'producto.nombre_corto': 30,
    'beneficios.titulo': 40, 'cierre.frase1': 24, 'cierre.frase2': 24,
    'cierre.precio': 40, 'cierre.palabra': 12,
}
OBLIGATORIOS = ['imagen', 'gancho.linea1', 'gancho.linea2', 'producto.categoria', 'producto.nombre',
                'beneficios.titulo', 'beneficios.lista', 'cierre.frase1', 'cierre.frase2',
                'cierre.palabra', 'cierre.aviso', 'caption.texto', 'caption.hashtags']


def get(o, path):
    for k in path.split('.'):
        if o is None:
            return None
        o = o[int(k)] if isinstance(o, list) else o.get(k)
    return o


def validar(f):
    errores, avisos = [], []
    for k in OBLIGATORIOS:
        if not get(f, k):
            errores.append(f'falta "{k}"')
    for k, n in LARGOS.items():
        v = get(f, k)
        if v and len(v) > n:
            avisos.append(f'"{k}" tiene {len(v)} caracteres (recomendado ≤ {n}); la letra se achicará')
    lista = get(f, 'beneficios.lista') or []
    if not 2 <= len(lista) <= 3:
        errores.append('"beneficios.lista" debe tener 2 o 3 beneficios')
    for i, b in enumerate(lista):
        if len(b) > 34:
            avisos.append(f'beneficio {i + 1} tiene {len(b)} caracteres (recomendado ≤ 34)')
    if f.get('estilo', 'clasico') not in ESTILOS:
        errores.append(f'"estilo" debe ser uno de: {", ".join(ESTILOS)}')
    for e in (f.get('estilos') or {}):
        if e not in ESTILOS:
            errores.append(f'"estilos.{e}" no existe; los estilos son: {", ".join(ESTILOS)}')
    if f.get('paleta', 'coral') not in PALETAS:
        errores.append(f'"paleta" debe ser una de: {", ".join(sorted(PALETAS))}')
    tags = get(f, 'caption.hashtags') or []
    if len(tags) > 30:
        errores.append('Instagram acepta máximo 30 hashtags')
    if len(armar_caption(f)) > 2200:
        errores.append('el caption pasa de 2200 caracteres (límite de Instagram)')
    return errores, avisos


def armar_caption(f):
    c = f.get('caption', {})
    tags = ' '.join('#' + t.lstrip('#') for t in c.get('hashtags', []))
    partes = [c.get('texto', '').strip(), tags]
    if c.get('aviso'):
        partes.append(c['aviso'].strip())
    return '\n\n'.join(p for p in partes if p) + '\n'


def mezclar(base, extra):
    """Copia de base con los campos de extra encima (para los textos propios de cada estilo)."""
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = mezclar(out.get(k) or {}, v) if isinstance(v, dict) else v
    return out


def ficha_de_estilo(f, estilo):
    return mezclar(f, (f.get('estilos') or {}).get(estilo))


def unidades(css):
    """12u -> calc(12px*var(--u)): así un mismo diseño sirve para todos los formatos."""
    return re.sub(r'(?<![\w.#-])(-?\d+(?:\.\d+)?)u\b', r'calc(\1px*var(--u))', css)


def tiempos_de(estilo):
    return json.loads((PLANTILLA / 'estilos' / estilo / 'tiempos.json').read_text())


def armar_html(f, dir_producto, estilo, formato, tiempos):
    img = dir_producto / f['imagen']
    mime = MIME.get(img.suffix.lower())
    if not mime:
        sys.exit(f'Formato de imagen no soportado: {img.name} (usa jpg, png o webp)')
    data = base64.b64encode(img.read_bytes()).decode()
    w, h, u, orient = FORMATOS[formato]
    cuerpo = unidades((PLANTILLA / 'estilos' / estilo / 'plantilla.html').read_text())
    # </ dentro del JSON cerraría el <script>; se escapa
    ficha_js = json.dumps(f, ensure_ascii=False).replace('</', '<\\/')
    titulo = get(f, 'producto.nombre')
    return f"""<!doctype html>
<html lang="es" data-estilo="{estilo}" data-formato="{formato}" data-orient="{orient}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anuncio · {titulo}</title>
<style>{(PLANTILLA / 'fonts' / 'fonts.css').read_text()}</style>
<style>:root{{--W:{w}px;--H:{h}px;--u:{u}}}
{unidades((PLANTILLA / 'base.css').read_text())}</style>
</head>
<body>
<div id="stage">
{cuerpo}
</div>
<script>
const T = {json.dumps(tiempos)};
const F = {ficha_js};
const IMG = "data:{mime};base64,{data}";
const W = {w}, H = {h};
{(PLANTILLA / 'base.js').read_text()}
</script>
</body>
</html>
"""


def momento(T, expr):
    """'producto.dato+1.2' -> segundos."""
    m = re.fullmatch(r'([\w.]+)\s*([+-]\s*[\d.]+)?', expr)
    return get(T, m.group(1)) + float((m.group(2) or '0').replace(' ', ''))


def capturar(html, modo, carpeta, formato, T, tiempos=''):
    w, h = FORMATOS[formato][:2]
    subprocess.run(['node', str(AQUI / 'render.cjs'), str(html), modo, str(carpeta), str(T['duracion']),
                    tiempos, str(w), str(h)], check=True)


def previa(html, destino, formato, T):
    """Cuadros clave de cada escena en una sola imagen."""
    t = [momento(T, x) for x in T['previa']]
    with tempfile.TemporaryDirectory() as tmp:
        capturar(html, 'preview', tmp, formato, T, ','.join(f'{x:.2f}' for x in t))
        w, h = FORMATOS[formato][:2]
        alto = 480 if h >= w else 300
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-pattern_type', 'glob', '-i', f'{tmp}/p_*.jpg',
                        '-vf', f'scale=-2:{alto},tile={len(t)}x1:padding=8:color=white', '-frames:v', '1',
                        str(destino)], check=True)
    return destino


def audio(estilo, T, f, tmp, voz=None):
    """Música y efectos del estilo (y la voz, si hay). Un solo audio sirve para todos los formatos."""
    import sonido
    wav = Path(tmp) / f'audio-{estilo}.wav'
    sonido.generar(T, str(wav), estilo, f)
    if voz:
        # La voz entra en voz["inicio"] segundos y la música baja cuando ella habla
        ms = int(float(voz.get('inicio', 0.3)) * 1000)
        mezcla = Path(tmp) / f'mezcla-{estilo}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-i', str(voz['ruta']), '-filter_complex',
                        f'[1:a]aresample=48000,adelay={ms}|{ms},apad,asplit=2[v1][v2];'
                        '[0:a][v1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[m];'
                        '[m][v2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]',
                        '-map', '[a]', str(mezcla)], check=True)
        wav = mezcla
    return wav


def video(html, salida, formato, T, wav):
    with tempfile.TemporaryDirectory() as tmp:
        capturar(html, 'full', Path(tmp) / 'f', formato, T)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', str(Path(tmp) / 'f' / 'f_%04d.jpg'),
                        '-i', str(wav), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', str(salida)], check=True)
    return salida


def lista(valor, opciones, nombre):
    if valor in (None, '', 'todos'):
        return list(opciones)
    elegidos = [x.strip() for x in valor.split(',') if x.strip()]
    for x in elegidos:
        if x not in opciones:
            sys.exit(f'{nombre} "{x}" no existe; opciones: {", ".join(opciones)} o "todos"')
    return elegidos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('producto', help='carpeta del producto (con ficha.json e imagen)')
    ap.add_argument('--estilo', help=f'{", ".join(ESTILOS)} o "todos" (defecto: el de la ficha, o clasico)')
    ap.add_argument('--formatos', help=f'{",".join(FORMATOS)} o "todos" (defecto: los de la ficha, o todos)')
    ap.add_argument('--video', action='store_true', help='renderizar también los MP4 finales')
    ap.add_argument('--sin-previa', action='store_true', help='no generar las vistas previas')
    a = ap.parse_args()

    dir_producto = Path(a.producto).resolve()
    ficha = json.loads((dir_producto / 'ficha.json').read_text())
    estilos = lista(a.estilo or ficha.get('estilo', 'clasico'), ESTILOS, 'estilo')
    fmt_ficha = ','.join(ficha['formatos']) if ficha.get('formatos') else None
    formatos = lista(a.formatos or fmt_ficha, FORMATOS, 'formato')

    errores, avisos = validar(ficha)
    for e in estilos:
        if e in (ficha.get('estilos') or {}):
            err, av = validar(ficha_de_estilo(ficha, e))
            errores += [f'[{e}] {x}' for x in err if x not in errores]
            avisos += [f'[{e}] {x}' for x in av if x not in avisos]
    if 'razones' in estilos and not get(ficha, 'estilos.razones.gancho.linea1'):
        avisos.append('[razones] conviene escribir "estilos.razones.gancho" (p. ej. linea1 "razones para probar")')
    for x in avisos:
        print('aviso:', x)
    if errores:
        for x in errores:
            print('ERROR:', x)
        sys.exit(1)

    voz = ficha.get('voz')
    if a.video and voz and voz.get('archivo'):
        voz = {**voz, 'ruta': dir_producto / voz['archivo']}
        if not voz['ruta'].exists():
            sys.exit(f'No encuentro la voz: {voz["ruta"]}')
    else:
        voz = None

    out = AQUI / 'salida' / dir_producto.name
    out.mkdir(parents=True, exist_ok=True)
    (out / 'caption.txt').write_text(armar_caption(ficha))
    print('✓', (out / 'caption.txt').relative_to(AQUI))

    # Chromium por formato en paralelo (hasta 3 a la vez)
    with ThreadPoolExecutor(max_workers=3) as pool, tempfile.TemporaryDirectory() as tmp:
        for estilo in estilos:
            f = ficha_de_estilo(ficha, estilo)
            T = tiempos_de(estilo)
            if estilo == 'razones' and len(get(f, 'beneficios.lista')) == 2:
                T['razon']['r3'] = T['razon']['sale']   # con 2 razones, la segunda dura hasta el cierre
            dest = out / estilo
            dest.mkdir(exist_ok=True)
            htmls = {}
            for fmt in formatos:
                htmls[fmt] = dest / f'anuncio-{fmt}.html'
                htmls[fmt].write_text(armar_html(f, dir_producto, estilo, fmt, T))
                print('✓', htmls[fmt].relative_to(AQUI))
            if not a.sin_previa:
                for r in pool.map(lambda fmt: previa(htmls[fmt], dest / f'previa-{fmt}.jpg', fmt, T), formatos):
                    print('✓', r.relative_to(AQUI))
            if a.video:
                print(f'· {estilo}: sintetizando música y efectos…')
                wav = audio(estilo, T, f, tmp, voz)
                print(f'· {estilo}: capturando cuadros y codificando {len(formatos)} video(s)…')
                for r in pool.map(lambda fmt: video(htmls[fmt], dest / f'anuncio-{fmt}.mp4', fmt, T, wav), formatos):
                    print('✓', r.relative_to(AQUI))


if __name__ == '__main__':
    sys.path.insert(0, str(AQUI))
    main()
