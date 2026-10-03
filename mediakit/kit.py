#!/usr/bin/env python3
"""Media kit de Isabella: su carta de presentación para marcas, tiendas y otras creadoras.

Junta sus números reales (los que guardó la Analista de redes con las capturas de sus
estadísticas), su público (la captura de "Audiencia" de Instagram o TikTok), su perfil
y las colaboraciones que ofrece, y arma un PDF de dos páginas listo para mandar.
Cada vez que la Analista guarda capturas nuevas, se vuelve a armar y sale actualizado.

Uso (desde la carpeta del proyecto):
  python3 mediakit/kit.py armar [--dias 90]          # media kit con los números de los últimos 90 días
  python3 mediakit/kit.py audiencia --red instagram --mujeres 86 \\
      --edades "18-24:14,25-34:41,35-44:29,45-54:12" --lugares "Miami:31,Houston:9,Orlando:7"
  python3 mediakit/kit.py falta                      # lo que falta completar del perfil
  python3 mediakit/kit.py demo                       # ejemplo con números inventados (dice EJEMPLO)

El perfil (nombre, foto, bio, contacto, colaboraciones) está en mediakit/perfil.json: se crea
solo la primera vez a partir de perfil.ejemplo.json, y Isabella o Isa lo completan.
Queda en mediakit/salida/media-kit.html, .pdf y una imagen por página (si hay Chromium).
Solo librería estándar. Sin números inventados: lo que no hay, no sale.
"""
import argparse
import base64
import datetime
import html
import importlib.util
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PERFIL = AQUI / 'perfil.json'
EJEMPLO = AQUI / 'perfil.ejemplo.json'
DATOS = AQUI / 'datos'
AUDIENCIA = DATOS / 'audiencia.json'
SALIDA = AQUI / 'salida'
ANALISTA = RAIZ / 'analista' / 'datos'
VOZ = RAIZ / 'marca' / 'voz-isabella.md'
ASESORA = RAIZ / 'asesora'
COMPARTIDO = Path('/mnt/project-files')
HOY = datetime.date.today()

NOMBRE_RED = {'instagram': 'Instagram', 'tiktok': 'TikTok', 'facebook': 'Facebook', 'youtube': 'YouTube'}
VIDEOS = ('reel', 'anuncio', 'educativo', 'video', 'en-vivo')
NOMBRE_TIPO = {'reel': 'Reel', 'anuncio': 'Video de producto', 'educativo': 'Video educativo', 'carrusel': 'Carrusel',
               'post': 'Publicación', 'historia': 'Historia', 'en-vivo': 'En vivo', 'video': 'Video'}


def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def e(t):
    return html.escape(str(t if t is not None else ''))


def pendiente(v):
    return v is None or (isinstance(v, str) and (not v.strip() or 'PENDIENTE' in v or v.strip().startswith('[')))


def corto(n):
    """12400 → 12,4 mil; 1250000 → 1,3 M (como se lee en redes)."""
    if n is None:
        return '—'
    n = float(n)
    if n >= 1_000_000:
        return f'{n / 1_000_000:.1f} M'.replace('.', ',').replace(',0 ', ' ')
    if n >= 10_000:
        return f'{n / 1000:.0f} mil'
    if n >= 1000:
        return f'{n / 1000:.1f} mil'.replace('.', ',').replace(',0 ', ' ')
    return f'{n:.0f}'


def pct(v, dec=1):
    return '—' if v is None else f'{v:.{dec}f} %'.replace('.', ',')


# ---------- el perfil ----------

def de_la_voz():
    """Lo que ya está en la ficha de la voz de Isabella (si no dice PENDIENTE)."""
    sale = {}
    if not VOZ.exists():
        return sale
    t = VOZ.read_text(encoding='utf-8')
    for campo, patron in (('nombre', r'Nombre en redes:\s*(.+)'), ('usuario', r'Usuario de Instagram / TikTok:\s*(.+)'),
                          ('ciudad', r'Dónde vive \(ciudad o país\):\s*(.+)')):
        m = re.search(patron, t)
        if m and 'PENDIENTE' not in m.group(1):
            sale[campo] = m.group(1).strip()
    return sale


def cargar_perfil():
    if not PERFIL.exists():
        shutil.copy(EJEMPLO, PERFIL)
    p = leer_json(PERFIL, {}) or {}
    for k, v in de_la_voz().items():
        if pendiente(p.get(k)):
            p[k] = v
    return p


def que_falta(p, n):
    falta = []
    for campo, que in (('nombre', 'tu nombre como aparece en redes'), ('usuario', 'tu usuario (@)'),
                       ('foto', 'una foto tuya (ruta del archivo)'), ('bio', 'una frase sobre ti'),
                       ('ciudad', 'tu ciudad'), ('email', 'un correo para marcas'), ('whatsapp', 'tu WhatsApp')):
        if pendiente(p.get(campo)):
            falta.append(que)
    if p.get('foto') and not pendiente(p.get('foto')) and not (RAIZ / p['foto']).exists() and not Path(p['foto']).exists():
        falta.append(f"la foto no está en {p['foto']}")
    if not n['redes']:
        falta.append('los seguidores de tu perfil (captura del perfil para la Analista)')
    if not n['publicaciones']:
        falta.append('las estadísticas de tus publicaciones (capturas para la Analista)')
    if not n['audiencia']:
        falta.append('quién te sigue (captura de "Audiencia" de Instagram o TikTok)')
    return falta


# ---------- los números ----------

def calcular():
    """Usa la misma cuenta que la Analista para cada publicación."""
    spec = importlib.util.spec_from_file_location('redes', RAIZ / 'analista' / 'redes.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.calcular


def numeros(pubs, cuenta, audiencia, dias):
    desde = (HOY - datetime.timedelta(days=dias)).isoformat()
    periodo = [p for p in pubs if p.get('fecha', '') > desde]
    calc = calcular()
    medidas = [(p, calc(p)) for p in periodo]
    redes = []
    for red in sorted({c['red'] for c in cuenta}):
        filas = sorted((c for c in cuenta if c['red'] == red), key=lambda c: c['fecha'])
        ultima = filas[-1]
        hace30 = (datetime.date.fromisoformat(ultima['fecha']) - datetime.timedelta(days=30)).isoformat()
        antes = [c for c in filas if c['fecha'] <= hace30] or filas[:1]
        cambio = ultima['seguidores'] - antes[-1]['seguidores'] if antes[-1] is not ultima else None
        redes.append({'red': red, 'seguidores': ultima['seguidores'], 'fecha': ultima['fecha'],
                      'crecimiento': cambio, 'desde': antes[-1]['fecha']})
    videos = [p.get('vistas') for p in periodo if p.get('tipo') in VIDEOS and p.get('vistas')]
    alcances = [p.get('alcance') or p.get('vistas') for p in periodo if p.get('alcance') or p.get('vistas')]
    inter = [m['interaccion'] for _, m in medidas if m['interaccion'] is not None]
    valor = [m['valor'] for _, m in medidas if m['valor'] is not None]
    tops = sorted((p for p in periodo if p.get('vistas')), key=lambda p: -p['vistas'])[:3]
    semanas = max(1, dias / 7)
    return {
        'dias': dias, 'desde': desde, 'publicaciones': len(periodo),
        'por_semana': round(len(periodo) / semanas, 1) if periodo else None,
        'redes': redes, 'seguidores': sum(r['seguidores'] for r in redes) or None,
        'vistas_video': round(statistics.median(videos)) if videos else None,
        'alcance': round(statistics.median(alcances)) if alcances else None,
        'vistas_total': sum(p.get('vistas') or 0 for p in periodo) or None,
        'interaccion': statistics.mean(inter) if inter else None,
        'valor': statistics.mean(valor) if valor else None,
        'guardados': sum((p.get('guardados') or 0) + (p.get('compartidos') or 0) for p in periodo) or None,
        'mensajes': sum(p.get('mensajes') or 0 for p in periodo) or None,
        'mejores': [{'tema': p.get('tema') or NOMBRE_TIPO.get(p.get('tipo'), 'Publicación'), 'red': p['red'],
                     'tipo': p.get('tipo'), 'fecha': p['fecha'], 'vistas': p.get('vistas'),
                     'interaccion': calc(p)['interaccion'], 'guardados': (p.get('guardados') or 0) + (p.get('compartidos') or 0)}
                    for p in tops],
        'audiencia': audiencia,
    }


def cmd_audiencia(a):
    datos = leer_json(AUDIENCIA, {}) or {}

    def pares(texto):
        sale = []
        for parte in (texto or '').split(','):
            if ':' in parte:
                k, v = parte.rsplit(':', 1)
                try:
                    sale.append([k.strip(), float(v.strip().rstrip('%').replace(',', '.'))])
                except ValueError:
                    sys.exit(f'No entiendo «{parte}»: usa nombre:porcentaje, por ejemplo 25-34:41')
        return sale
    fila = {'fecha': a.fecha or HOY.isoformat()}
    if a.mujeres is not None:
        fila['mujeres'] = a.mujeres
    for campo in ('edades', 'lugares'):
        if getattr(a, campo):
            fila[campo] = pares(getattr(a, campo))
    datos[a.red] = fila
    DATOS.mkdir(parents=True, exist_ok=True)
    AUDIENCIA.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'Audiencia de {NOMBRE_RED.get(a.red, a.red)} guardada ({fila["fecha"]}).')


# ---------- la página ----------

def incrustar(ruta, ancho=None):
    if not ruta:
        return ''
    f = Path(ruta)
    f = f if f.is_absolute() else RAIZ / f
    if not f.is_file():
        return ''
    tipo = {'.png': 'png', '.webp': 'webp'}.get(f.suffix.lower(), 'jpeg')
    return f'data:image/{tipo};base64,' + base64.b64encode(f.read_bytes()).decode()


def favoritos(p):
    cat = (leer_json(ASESORA / 'catalogo.json', {}) or {}).get('productos', [])
    tienda = (leer_json(ASESORA / 'tienda.json', {}) or {}).get('productos', {})
    sale = []
    for pid in p.get('favoritos') or []:
        prod = next((x for x in cat if x['id'] == pid), None)
        if prod:
            sale.append({'nombre': prod['nombre'], 'foto': incrustar(ASESORA / (tienda.get(pid, {}).get('foto') or '-'))})
    return sale


def barras(filas, maximo=None):
    if not filas:
        return ''
    maximo = maximo or max(v for _, v in filas) or 1
    return ''.join(f'<div class="barra"><span class="et">{e(k)}</span><span class="pista"><i style="width:{100 * v / maximo:.0f}%"></i></span>'
                   f'<b>{v:.0f} %</b></div>' for k, v in filas)


def pagina(p, n, ejemplo=False):
    nombre = p.get('nombre') if not pendiente(p.get('nombre')) else 'Isabella'
    usuario = (p.get('usuario') or '').lstrip('@') if not pendiente(p.get('usuario')) else ''
    foto = incrustar(p.get('foto')) if not pendiente(p.get('foto')) else ''
    bio = p.get('bio') if not pendiente(p.get('bio')) else 'Cuidado de la piel y maquillaje real, explicado fácil.'
    ciudad = p.get('ciudad') if not pendiente(p.get('ciudad')) else ''
    temas = [t for t in p.get('temas') or [] if not pendiente(t)]
    falta = que_falta(p, n)

    kpis = []
    if n['seguidores']:
        kpis.append((corto(n['seguidores']), 'seguidores'))
    if n['vistas_video']:
        kpis.append((corto(n['vistas_video']), 'vistas por video'))
    if n['interaccion'] is not None:
        kpis.append((pct(n['interaccion']), 'de interacción'))
    if n['guardados']:
        kpis.append((corto(n['guardados']), 'guardados y compartidos'))
    kpi_html = ''.join(f'<div class="kpi"><b>{e(v)}</b><span>{e(t)}</span></div>' for v, t in kpis[:4])

    redes_html = ''.join(
        f'<div class="red"><span class="rn">{e(NOMBRE_RED.get(r["red"], r["red"]))}</span><b>{corto(r["seguidores"])}</b>'
        + (f'<small>{"+" if r["crecimiento"] >= 0 else ""}{corto(r["crecimiento"])} en 30 días</small>' if r['crecimiento'] else '<small>seguidores</small>')
        + '</div>' for r in n['redes'])

    aud = n['audiencia'] or {}
    a_red = next((aud[k] for k in ('instagram', 'tiktok', 'facebook') if k in aud), None)
    aud_html = ''
    if a_red:
        partes = []
        if a_red.get('mujeres') is not None:
            partes.append(f'<div class="dona" style="--p:{a_red["mujeres"]}"><b>{a_red["mujeres"]:.0f} %</b><span>mujeres</span></div>')
        cols = ''
        if a_red.get('edades'):
            cols += f'<div><h4>Edades</h4>{barras(a_red["edades"])}</div>'
        if a_red.get('lugares'):
            cols += f'<div><h4>Dónde viven</h4>{barras(a_red["lugares"][:5])}</div>'
        aud_html = f'<section class="bloque"><h3>Mi comunidad</h3><div class="aud">{"".join(partes)}{cols}</div></section>'

    mejores = ''.join(
        f'<div class="pub"><span class="tag">{e(NOMBRE_TIPO.get(m["tipo"], "Publicación"))} · {e(NOMBRE_RED.get(m["red"], m["red"]))}</span>'
        f'<b class="tema">{e(m["tema"])}</b><div class="cifras"><span><b>{corto(m["vistas"])}</b> vistas</span>'
        + (f'<span><b>{pct(m["interaccion"])}</b> interacción</span>' if m['interaccion'] is not None else '')
        + (f'<span><b>{corto(m["guardados"])}</b> guardados</span>' if m['guardados'] else '')
        + '</div></div>' for m in n['mejores'])
    mejores_html = f'<section class="bloque"><h3>Lo que más vio mi comunidad</h3><div class="pubs">{mejores}</div></section>' if mejores else ''

    colabs = p.get('colaboraciones') or []
    colab_html = ''.join(f'<div class="colab"><span class="ico">{e(c.get("icono", "✦"))}</span><b>{e(c["nombre"])}</b><p>{e(c.get("que", ""))}</p></div>'
                         for c in colabs)
    porque = [x for x in p.get('por_que') or [] if not pendiente(x)]
    if n['mensajes']:
        porque.append(f'Mi contenido trae conversaciones reales: {corto(n["mensajes"])} mensajes de personas interesadas en {n["dias"]} días.')
    porque_html = ''.join(f'<li>{e(x)}</li>' for x in porque[:4])
    favs = favoritos(p)
    favs_html = ''.join('<div class="fav">' + (f'<img src="{f["foto"]}" alt="">' if f['foto'] else '')
                        + f'<span>{e(f["nombre"])}</span></div>' for f in favs[:4])
    marcas = [m for m in p.get('marcas') or [] if not pendiente(m)]
    tarifas = p.get('tarifas') if not pendiente(p.get('tarifas')) else 'Te mando las tarifas según lo que necesites: escríbeme y armamos la propuesta.'
    contacto = []
    if not pendiente(p.get('email')):
        contacto.append(('Correo', p['email']))
    if not pendiente(p.get('whatsapp')):
        contacto.append(('WhatsApp', p['whatsapp']))
    for red in ('instagram', 'tiktok'):
        u = (p.get(red) or usuario or '').lstrip('@')
        if u and not pendiente(u):
            contacto.append((NOMBRE_RED[red], '@' + u))
    contacto_html = ''.join(f'<div><span>{e(k)}</span><b>{e(v)}</b></div>' for k, v in contacto) or '<div><span>Contacto</span><b>[completa tu correo o WhatsApp]</b></div>'

    datos_de = (f'Números de los últimos {n["dias"]} días · {n["publicaciones"]} publicaciones · actualizado el '
                f'{HOY.strftime("%d/%m/%Y")}') if n['publicaciones'] else f'Actualizado el {HOY.strftime("%d/%m/%Y")}'
    sello = '<div class="sello">EJEMPLO · números inventados</div>' if ejemplo else ''
    retrato = (f'<img src="{foto}" alt="">' if foto else f'<span class="mono">{e(nombre[:1])}</span>')
    falta_html = ''.join(f'<li>{e(x)}</li>' for x in falta)

    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Media kit · {e(nombre)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,500;0,600;1,500;1,600&family=Jost:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{ --tinta:#2b2321; --hueso:#f6f1ea; --rosa:#9e4f5c; --champan:#c9a66b; --gris:#7b6f6a; --linea:#e6dcd2;
  --serif:"Cormorant","Cormorant Garamond","Didot","Bodoni 72",Georgia,"Liberation Serif",serif;
  --sans:"Jost","Avenir Next","Avenir","Helvetica Neue",Arial,"Liberation Sans",sans-serif; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
@page {{ size:A4; margin:0; }}
body {{ background:#e9e1d8; color:var(--tinta); font-family:var(--sans); -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
.todo {{ display:flex; gap:28px; justify-content:center; align-items:flex-start; padding:28px 16px 60px; flex-wrap:wrap; }}
.hojas {{ display:flex; flex-direction:column; gap:28px; }}
.marco {{ width:min(794px, calc(100vw - 32px)); aspect-ratio:794/1123; position:relative; overflow:hidden; box-shadow:0 24px 60px rgba(60,40,30,.2); border-radius:6px; }}
.hoja {{ width:794px; height:1123px; position:absolute; top:0; left:0; transform-origin:0 0; background:var(--hueso); padding:58px 60px 46px; display:flex; flex-direction:column; overflow:hidden; }}
.hoja.uno {{ background:radial-gradient(90% 45% at 100% 0%, #f2ddd5 0%, rgba(242,221,213,0) 70%), var(--hueso); }}
@media print {{ body {{ background:none; }} .todo {{ padding:0; display:block; }} .lado {{ display:none; }} .hojas {{ gap:0; }}
  .marco {{ width:794px; height:1123px; box-shadow:none; border-radius:0; break-after:page; }} .hoja {{ transform:none !important; }} }}
body.foto {{ background:var(--hueso); }} body.foto .todo {{ padding:0; display:block; }} body.foto .lado {{ display:none; }}
body.foto .hojas {{ gap:0; }} body.foto .marco {{ width:794px; height:1123px; box-shadow:none; border-radius:0; }}
.sello {{ position:absolute; top:18px; left:50%; transform:translateX(-50%); background:var(--rosa); color:#fff; font-size:10px; letter-spacing:.2em; padding:4px 14px; border-radius:99px; text-transform:uppercase; }}
.arriba {{ display:flex; justify-content:space-between; align-items:center; font-size:11px; letter-spacing:.32em; text-transform:uppercase; color:var(--rosa); }}
.portada {{ display:grid; grid-template-columns:220px 1fr; gap:36px; align-items:center; margin:26px 0 24px; }}
.retrato {{ width:220px; height:280px; border-radius:110px 110px 18px 18px; overflow:hidden; background:linear-gradient(160deg,#ead2c8,#d9b6a8); display:grid; place-items:center; box-shadow:0 18px 40px rgba(110,60,50,.18); }}
.retrato img {{ width:100%; height:100%; object-fit:cover; }}
.mono {{ font-family:var(--serif); font-style:italic; font-size:150px; color:#fff; }}
.nombre {{ font-family:var(--serif); font-style:italic; font-weight:500; font-size:76px; line-height:.92; }}
.usuario {{ font-size:17px; color:var(--rosa); margin:12px 0 16px; letter-spacing:.04em; }}
.bio {{ font-family:var(--serif); font-size:25px; line-height:1.25; font-weight:500; }}
.temas {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:16px; }}
.temas span {{ font-size:12.5px; border:1px solid var(--linea); background:#fff; padding:5px 11px; border-radius:99px; color:var(--gris); }}
.kpis {{ display:grid; grid-template-columns:repeat({max(1, min(4, len(kpis)))}, 1fr); background:#fff; border-radius:18px; box-shadow:0 10px 30px rgba(90,60,40,.07); }}
.kpi {{ padding:16px 14px; text-align:center; border-right:1px solid var(--linea); }}
.kpi:last-child {{ border-right:0; }}
.kpi b {{ display:block; font-family:var(--serif); font-size:40px; font-weight:600; line-height:1; }}
.kpi span {{ font-size:12px; color:var(--gris); letter-spacing:.08em; text-transform:uppercase; }}
.redes {{ display:flex; gap:12px; margin-top:14px; }}
.red {{ flex:1; border:1px solid var(--linea); border-radius:14px; padding:12px 16px; display:flex; align-items:baseline; gap:10px; }}
.red .rn {{ font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:var(--rosa); }}
.red b {{ font-family:var(--serif); font-size:26px; }}
.red small {{ margin-left:auto; color:#2f8f6c; font-size:12.5px; }}
.bloque {{ margin-top:22px; }}
h3 {{ font-family:var(--serif); font-size:28px; font-weight:600; margin-bottom:12px; }}
h3::after {{ content:""; display:block; width:56px; height:2px; background:var(--champan); margin-top:8px; }}
h4 {{ font-size:11.5px; letter-spacing:.2em; text-transform:uppercase; color:var(--gris); margin-bottom:10px; font-weight:500; }}
.aud {{ display:grid; grid-template-columns:130px 1fr 1fr; gap:30px; align-items:center; }}
.dona {{ width:130px; height:130px; border-radius:50%; background:conic-gradient(var(--rosa) calc(var(--p) * 1%), #ecdcd5 0); display:grid; place-items:center; align-content:center; position:relative; }}
.dona::before {{ content:""; position:absolute; inset:16px; background:var(--hueso); border-radius:50%; }}
.dona b, .dona span {{ position:relative; text-align:center; }} .dona b {{ font-family:var(--serif); font-size:34px; line-height:1; }} .dona span {{ font-size:12px; color:var(--gris); }}
.barra {{ display:grid; grid-template-columns:86px 1fr 44px; gap:10px; align-items:center; font-size:13px; margin-bottom:6px; }}
.barra .et {{ color:var(--gris); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.pista {{ height:8px; background:#ecdcd5; border-radius:9px; overflow:hidden; }} .pista i {{ display:block; height:100%; background:linear-gradient(90deg,var(--champan),var(--rosa)); border-radius:9px; }}
.barra b {{ text-align:right; font-weight:500; }}
.pubs {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
.pub {{ background:#fff; border-radius:16px; padding:16px 16px 14px; box-shadow:0 8px 24px rgba(90,60,40,.06); }}
.tag {{ font-size:10.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--rosa); }}
.tema {{ display:block; font-family:var(--serif); font-size:21px; line-height:1.1; margin:6px 0 8px; }}
.cifras {{ display:flex; flex-direction:column; gap:3px; font-size:12.5px; color:var(--gris); }} .cifras b {{ color:var(--tinta); font-weight:500; }}
.pie {{ margin-top:auto; padding-top:16px; border-top:1px solid var(--linea); display:flex; justify-content:space-between; font-size:11px; color:var(--gris); letter-spacing:.04em; }}
.colabs {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
.colab {{ background:#fff; border-radius:16px; padding:16px; box-shadow:0 8px 24px rgba(90,60,40,.06); }}
.colab .ico {{ font-size:20px; }} .colab b {{ display:block; font-family:var(--serif); font-size:21px; margin:6px 0 4px; }} .colab p {{ font-size:12.5px; color:var(--gris); line-height:1.4; }}
.dos {{ display:grid; grid-template-columns:1.1fr .9fr; gap:28px; }}
.porque {{ list-style:none; }} .porque li {{ position:relative; padding-left:24px; margin-bottom:11px; font-size:14px; line-height:1.45; }}
.porque li::before {{ content:"✦"; position:absolute; left:0; color:var(--champan); }}
.favs {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }}
.fav {{ background:#fff; border-radius:14px; padding:10px; display:flex; align-items:center; gap:10px; font-size:12.5px; }}
.fav img {{ width:54px; height:54px; object-fit:contain; }}
.marcas {{ font-size:13px; color:var(--gris); margin-top:10px; }}
.tarifas {{ background:var(--tinta); color:var(--hueso); border-radius:20px; padding:24px 28px; display:grid; grid-template-columns:1fr 1fr; gap:24px; align-items:center; margin-top:26px; }}
.tarifas h3 {{ color:var(--hueso); font-size:28px; margin-bottom:8px; }} .tarifas p {{ font-size:14px; line-height:1.5; color:#e6dad0; }}
.contacto div {{ display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,.15); padding:7px 0; font-size:14px; }}
.contacto span {{ color:#cbb8a9; letter-spacing:.1em; text-transform:uppercase; font-size:11px; }}
.firma {{ font-family:var(--serif); font-style:italic; font-size:44px; color:var(--rosa); text-align:right; margin-top:18px; }}
.lado {{ width:min(360px,100%); background:#fffaf5; border-radius:18px; padding:20px; box-shadow:0 10px 30px rgba(60,40,30,.1); position:sticky; top:20px; }}
.lado h2 {{ font-family:var(--serif); font-size:26px; margin-bottom:8px; }} .lado p, .lado li {{ font-size:14px; line-height:1.5; }}
.lado ul {{ background:#fff3cd; border-radius:12px; padding:10px 12px 10px 28px; margin:10px 0; }}
.boton {{ display:inline-block; border:0; border-radius:99px; padding:11px 18px; font:500 15px var(--sans); cursor:pointer; background:var(--rosa); color:#fff; text-decoration:none; margin-top:8px; }}
</style></head><body>
<div class="todo">
<div class="hojas">
 <div class="marco"><div class="hoja uno">{sello}
  <div class="arriba"><span>Media kit</span><span>{e(ciudad)}</span></div>
  <div class="portada">
   <div class="retrato">{retrato}</div>
   <div><div class="nombre">{e(nombre)}</div>
    <div class="usuario">{('@' + e(usuario)) if usuario else 'Creadora de contenido de belleza'}</div>
    <p class="bio">{e(bio)}</p>
    {('<div class="temas">' + ''.join(f'<span>{e(t)}</span>' for t in temas) + '</div>') if temas else ''}
   </div>
  </div>
  {f'<div class="kpis">{kpi_html}</div>' if kpi_html else ''}
  {f'<div class="redes">{redes_html}</div>' if redes_html else ''}
  {aud_html}
  {mejores_html}
  <div class="pie"><span>{e(datos_de)}</span><span>1 / 2</span></div>
 </div></div>
 <div class="marco"><div class="hoja dos-h">{sello}
  <div class="arriba"><span>{e(nombre)}</span><span>Trabajemos juntas</span></div>
  <section class="bloque"><h3>Cómo podemos trabajar juntas</h3><div class="colabs">{colab_html}</div></section>
  <div class="dos bloque">
   <section><h3>Por qué conmigo</h3><ul class="porque">{porque_html}</ul></section>
   <section><h3>Lo que recomiendo</h3><div class="favs">{favs_html}</div>
    {f'<p class="marcas">Marcas con las que trabajo: {e(", ".join(marcas))}</p>' if marcas else ''}</section>
  </div>
  <div class="tarifas"><div><h3>Hablemos</h3><p>{e(tarifas)}</p></div><div class="contacto">{contacto_html}</div></div>
  <div class="firma">Con cariño, {e(nombre)}</div>
  <div class="pie"><span>{e(datos_de)}</span><span>2 / 2</span></div>
 </div></div>
</div>
<aside class="lado"><h2>Tu media kit</h2>
 <p>Mándalo como PDF a marcas, tiendas o creadoras con las que quieras colaborar. Se actualiza cada vez que la Analista guarda capturas nuevas.</p>
 {f'<p><b>Falta completar:</b></p><ul>{falta_html}</ul><p>Díselo a Isa y vuelve a armarlo.</p>' if falta else '<p>Está todo completo ✓</p>'}
 <button class="boton" onclick="window.print()">Guardar como PDF</button>
 <p style="margin-top:10px;color:#7b6f6a">En la ventana que se abre elige «Guardar como PDF».</p>
</aside>
</div>
<script>
(function () {{
  var foto = /[?&]foto\\b/.test(location.search);
  if (foto) document.body.classList.add('foto');
  function ajustar() {{ document.querySelectorAll('.marco').forEach(function (m) {{
    m.firstElementChild.style.transform = foto ? 'none' : 'scale(' + (m.clientWidth / 794) + ')'; }}); }}
  ajustar(); window.addEventListener('resize', ajustar);
}})();
</script>
</body></html>
'''


def exportar(html_archivo):
    """PDF e imágenes de cada página con Chromium (si está playwright)."""
    if not shutil.which('node'):
        return []
    try:
        r = subprocess.run(['node', str(AQUI / 'exportar.cjs'), str(html_archivo)], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l.strip() for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else []


def armar(perfil, n, carpeta, nombre='media-kit', ejemplo=False):
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f'{nombre}.html'
    archivo.write_text(pagina(perfil, n, ejemplo), encoding='utf-8')
    hechos = [archivo] + [Path(x) for x in exportar(archivo)]
    if COMPARTIDO.is_dir():
        destino = COMPARTIDO / 'mediakit'
        destino.mkdir(exist_ok=True)
        for f in hechos:
            if f.exists():
                shutil.copy2(f, destino / f.name)
    return hechos


def resumen(n, hechos, falta):
    if n['seguidores']:
        print(f"Seguidores: {n['seguidores']} · " + ', '.join(f"{NOMBRE_RED.get(r['red'], r['red'])} {r['seguidores']}" for r in n['redes']))
    print(f"Publicaciones en {n['dias']} días: {n['publicaciones']}"
          + (f" · vistas por video (mediana): {n['vistas_video']}" if n['vistas_video'] else '')
          + (f" · interacción: {n['interaccion']:.1f} %" if n['interaccion'] is not None else ''))
    for f in hechos:
        try:
            print('Listo:', f.relative_to(RAIZ))
        except ValueError:
            print('Listo:', f)
    for x in falta:
        print('FALTA:', x)


def cmd_armar(a):
    perfil = cargar_perfil()
    n = numeros(leer_json(ANALISTA / 'publicaciones.json', []) or [], leer_json(ANALISTA / 'cuenta.json', []) or [],
                leer_json(AUDIENCIA, {}) or {}, a.dias)
    hechos = armar(perfil, n, SALIDA)
    resumen(n, hechos, que_falta(perfil, n))


def cmd_falta(_):
    perfil = cargar_perfil()
    n = numeros(leer_json(ANALISTA / 'publicaciones.json', []) or [], leer_json(ANALISTA / 'cuenta.json', []) or [],
                leer_json(AUDIENCIA, {}) or {}, 90)
    falta = que_falta(perfil, n)
    print('\n'.join('- ' + x for x in falta) if falta else 'Está todo completo.')


def cmd_demo(_):
    import random
    azar = random.Random(7)
    temas = [('reel', 'Rutina de noche en 3 pasos'), ('educativo', 'Mitos de la piel grasa'), ('anuncio', 'Vitamin C Glow Serum'),
             ('reel', 'Arréglate conmigo: look de oficina'), ('carrusel', 'Cómo hacer que el labial dure'),
             ('educativo', '¿Sabías que el sol mancha los labios?'), ('reel', 'Lo probé: mascarilla de noche'),
             ('anuncio', 'Tea Tree Face Cream'), ('reel', 'Mis 5 favoritos de Farmasi')]
    pubs = []
    for i in range(24):
        tipo, tema = temas[i % len(temas)]
        vistas = int(azar.lognormvariate(7.6, 0.6)) + (2600 if tema.startswith('Rutina') else 0)
        alcance = int(vistas * azar.uniform(.7, .9))
        pubs.append({'red': 'instagram' if i % 3 else 'tiktok', 'tipo': tipo, 'tema': tema,
                     'fecha': (HOY - datetime.timedelta(days=3 + i * 3)).isoformat(), 'vistas': vistas, 'alcance': alcance,
                     'me_gusta': int(alcance * azar.uniform(.04, .08)), 'comentarios': azar.randint(4, 30),
                     'guardados': int(vistas * azar.uniform(.01, .03)), 'compartidos': int(vistas * azar.uniform(.004, .015)),
                     'mensajes': azar.randint(0, 9)})
    cuenta = [{'red': 'instagram', 'fecha': (HOY - datetime.timedelta(days=60)).isoformat(), 'seguidores': 3480},
              {'red': 'instagram', 'fecha': (HOY - datetime.timedelta(days=30)).isoformat(), 'seguidores': 3890},
              {'red': 'instagram', 'fecha': HOY.isoformat(), 'seguidores': 4370},
              {'red': 'tiktok', 'fecha': (HOY - datetime.timedelta(days=30)).isoformat(), 'seguidores': 1910},
              {'red': 'tiktok', 'fecha': HOY.isoformat(), 'seguidores': 2640}]
    audiencia = {'instagram': {'fecha': HOY.isoformat(), 'mujeres': 87,
                               'edades': [['18-24', 13], ['25-34', 39], ['35-44', 31], ['45-54', 12], ['55+', 5]],
                               'lugares': [['Miami', 28], ['Houston', 9], ['Orlando', 7], ['Los Ángeles', 6], ['Bogotá', 4]]}}
    perfil = leer_json(EJEMPLO, {})
    perfil.update({'nombre': 'Isabella', 'usuario': 'isabella.belleza', 'ciudad': 'Miami, Florida',
                   'bio': 'Te enseño a cuidar tu piel y a maquillarte con productos que de verdad uso.',
                   'email': 'hola@isabella.com', 'whatsapp': '+1 305 555 0100'})
    n = numeros(pubs, cuenta, audiencia, 90)
    hechos = armar(perfil, n, SALIDA / 'ejemplo', 'media-kit-ejemplo', ejemplo=True)
    resumen(n, hechos, [])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('armar', help='arma el media kit con los números de la Analista')
    a.add_argument('--dias', type=int, default=90, help='cuántos días de publicaciones cuentan (90)')
    au = sub.add_parser('audiencia', help='guarda quién la sigue (de la captura de Audiencia)')
    au.add_argument('--red', required=True, choices=list(NOMBRE_RED))
    au.add_argument('--mujeres', type=float, help='% de mujeres')
    au.add_argument('--edades', help='"18-24:14,25-34:41,35-44:29"')
    au.add_argument('--lugares', help='"Miami:31,Houston:9" (ciudades o países, los principales)')
    au.add_argument('--fecha')
    sub.add_parser('falta', help='lo que falta completar')
    sub.add_parser('demo', help='ejemplo con números inventados en salida/ejemplo/')
    args = ap.parse_args()
    {'armar': cmd_armar, 'audiencia': cmd_audiencia, 'falta': cmd_falta, 'demo': cmd_demo}[args.cmd](args)


if __name__ == '__main__':
    main()
