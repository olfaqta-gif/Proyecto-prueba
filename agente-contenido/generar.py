"""Convierte la ficha de un producto en un anuncio vertical (1080x1920, 15 s) + caption.

    python3 generar.py productos/<slug>                 # HTML + caption + vistas previas
    python3 generar.py productos/<slug> --video         # además el MP4 final con sonido

Todo sale en salida/<slug>/:
    anuncio.html     el anuncio animado (se abre en cualquier navegador)
    caption.txt      texto listo para pegar en Instagram / TikTok / Facebook
    previa/          cuadros clave + hoja de contacto (previa.jpg) para revisar
    anuncio.mp4      video final (solo con --video)
"""
import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / 'plantilla'
PALETAS = {'coral', 'dorado', 'verde', 'lavanda', 'rosa'}
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


def armar_html(f, dir_producto, tiempos):
    img = dir_producto / f['imagen']
    mime = MIME.get(img.suffix.lower())
    if not mime:
        sys.exit(f'Formato de imagen no soportado: {img.name} (usa jpg, png o webp)')
    data = base64.b64encode(img.read_bytes()).decode()
    s = (PLANTILLA / 'anuncio.template.html').read_text()
    # </ dentro del JSON cerraría el <script>; se escapa
    ficha_js = json.dumps(f, ensure_ascii=False).replace('</', '<\\/')
    s = s.replace('/*FUENTES*/', (PLANTILLA / 'fonts' / 'fonts.css').read_text())
    s = s.replace('/*TIEMPOS*/', json.dumps(tiempos))
    s = s.replace('/*FICHA*/', ficha_js)
    s = s.replace('/*IMAGEN*/', f'data:{mime};base64,{data}')
    titulo = get(f, 'producto.nombre')
    return s.replace('<title>Anuncio Farmasi</title>', f'<title>Anuncio · {titulo}</title>')


def previa(html, destino, T):
    """Cuadros clave de cada escena + hoja de contacto."""
    t = [T['gancho']['linea2'] + 1.0, T['producto']['dato'] + 1.2, T['beneficios']['b3'] + 1.0,
         T['cierre']['aviso'] + 1.0, T['duracion'] - 0.1]
    if destino.exists():
        shutil.rmtree(destino)
    subprocess.run(['node', str(AQUI / 'render.cjs'), str(html), 'preview', str(destino),
                    str(T['duracion']), ','.join(f'{x:.2f}' for x in t)], check=True)
    hoja = destino / 'previa.jpg'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-pattern_type', 'glob', '-i', str(destino / 'p_*.jpg'),
                    '-vf', 'scale=270:480,tile=5x1:padding=8:color=white', '-frames:v', '1', str(hoja)], check=True)
    return hoja


def video(html, salida, T, voz=None):
    import sonido
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        print('· sintetizando música y efectos…')
        sonido.generar(T, str(tmp / 'audio.wav'))
        print('· capturando cuadros (30 fps)…')
        subprocess.run(['node', str(AQUI / 'render.cjs'), str(html), 'full', str(tmp / 'f'), str(T['duracion'])], check=True)
        audio = tmp / 'audio.wav'
        if voz:
            # La voz entra en voz["inicio"] segundos y la música baja cuando ella habla
            print('· mezclando la voz…')
            ms = int(float(voz.get('inicio', 0.3)) * 1000)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(audio), '-i', str(voz['ruta']), '-filter_complex',
                            f'[1:a]aresample=48000,adelay={ms}|{ms},apad,asplit=2[v1][v2];'
                            '[0:a][v1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[m];'
                            '[m][v2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]',
                            '-map', '[a]', str(tmp / 'mezcla.wav')], check=True)
            audio = tmp / 'mezcla.wav'
        print('· codificando MP4…')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', str(tmp / 'f' / 'f_%04d.jpg'),
                        '-i', str(audio), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', str(salida)], check=True)
    return salida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('producto', help='carpeta del producto (con ficha.json e imagen)')
    ap.add_argument('--video', action='store_true', help='renderizar también el MP4 final')
    ap.add_argument('--sin-previa', action='store_true', help='no generar las vistas previas')
    a = ap.parse_args()

    dir_producto = Path(a.producto).resolve()
    ficha = json.loads((dir_producto / 'ficha.json').read_text())
    tiempos = json.loads((PLANTILLA / 'tiempos.json').read_text())
    errores, avisos = validar(ficha)
    for x in avisos:
        print('aviso:', x)
    if errores:
        for x in errores:
            print('ERROR:', x)
        sys.exit(1)

    out = AQUI / 'salida' / dir_producto.name
    out.mkdir(parents=True, exist_ok=True)
    html = out / 'anuncio.html'
    html.write_text(armar_html(ficha, dir_producto, tiempos))
    (out / 'caption.txt').write_text(armar_caption(ficha))
    print('✓', html.relative_to(AQUI))
    print('✓', (out / 'caption.txt').relative_to(AQUI))
    if not a.sin_previa:
        print('✓', previa(html, out / 'previa', tiempos).relative_to(AQUI))
    if a.video:
        voz = ficha.get('voz')
        if voz and voz.get('archivo'):
            voz = {**voz, 'ruta': dir_producto / voz['archivo']}
            if not voz['ruta'].exists():
                sys.exit(f'No encuentro la voz: {voz["ruta"]}')
        else:
            voz = None
        print('✓', video(html, out / 'anuncio.mp4', tiempos, voz).relative_to(AQUI))


if __name__ == '__main__':
    sys.path.insert(0, str(AQUI))
    main()
