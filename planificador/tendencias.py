#!/usr/bin/env python3
"""Tendencias de la semana para el plan de Isabella: de qué se está hablando en belleza y cómo
subirse a eso con sus productos. Las busca el estratega (en noticias, blogs y revistas, nunca
entrando a Instagram ni TikTok) y las guarda aquí; el plan de la semana lleva al menos una.

Uso (desde la carpeta del proyecto):
  python3 planificador/tendencias.py pendiente            # ¿ya hay tendencias de esta semana? y qué buscar
  python3 planificador/tendencias.py guardar lote.json    # guarda las de esta semana (con su fuente)
  python3 planificador/tendencias.py actuales             # las de esta semana (lo que leen los agentes)
  python3 planificador/tendencias.py usada 2 --plan planificador/planes/x.json --id p3
  python3 planificador/tendencias.py historial            # las de semanas pasadas y cuáles se usaron

El lote es una lista (máximo 5) con: tema, que_es, por_que (por qué le sirve a Isabella), idea
(qué publicar), formato (reel, educativo, anuncio, historia, carrusel, en-vivo), productos
(códigos de farmasius.com, opcional) y fuente (enlace de donde salió; sin fuente no se guarda).
Queda en planificador/tendencias/<año>-S<semana>.json y una página .html para Isabella.
Solo librería estándar.
"""
import argparse
import datetime
import html
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
CARPETA = AQUI / 'tendencias'
COMPARTIDO = Path('/mnt/project-files')
FORMATOS = ('reel', 'educativo', 'anuncio', 'historia', 'carrusel', 'en-vivo')
MAX = 5


def semana(dia=None):
    a, s, _ = (dia or datetime.date.today()).isocalendar()
    return f'{a}-S{s:02d}'


def lunes(dia=None):
    dia = dia or datetime.date.today()
    return dia - datetime.timedelta(days=dia.weekday())


def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def e(t):
    return html.escape(str(t if t is not None else ''))


def temporada(dia=None):
    try:
        spec = importlib.util.spec_from_file_location('analizar', AQUI / 'analizar.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.TEMPORADAS[(dia or datetime.date.today()).month][0]
    except Exception:  # noqa: BLE001
        return ''


def busquedas(dia=None):
    """Qué buscar esta semana (en español e inglés: muchas tendencias llegan primero en inglés)."""
    dia = dia or datetime.date.today()
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
             'octubre', 'noviembre', 'diciembre']
    mes, anio = meses[dia.month - 1], dia.year
    month = dia.strftime('%B')
    return [f'tendencias de maquillaje {mes} {anio}', f'tendencias skincare {mes} {anio}',
            f'beauty trends {month} {anio}', f'viral makeup trend this week {anio}',
            f'skincare trend {month} {anio} dermatologists', f'{temporada(dia)} belleza ideas {anio}']


def archivo(clave=None):
    return CARPETA / f'{clave or semana()}.json'


def revisar(texto):
    try:
        spec = importlib.util.spec_from_file_location('responder', RAIZ / 'comunidad' / 'responder.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.revisar_texto(texto, True)
    except Exception:  # noqa: BLE001
        return []


def validar(lote):
    if not isinstance(lote, list) or not lote:
        sys.exit('El lote tiene que ser una lista de tendencias (ver el inicio de este archivo).')
    if len(lote) > MAX:
        sys.exit(f'Son {len(lote)}: elige las {MAX} que mejor le sirvan a Isabella.')
    problemas = []
    for i, t in enumerate(lote, 1):
        for campo in ('tema', 'que_es', 'por_que', 'idea', 'fuente'):
            if not str(t.get(campo) or '').strip():
                problemas.append(f'{i}. falta «{campo}»')
        if t.get('fuente') and not re.match(r'https?://', t['fuente']):
            problemas.append(f'{i}. la fuente tiene que ser un enlace')
        if re.search(r'instagram\.com|tiktok\.com', t.get('fuente') or ''):
            problemas.append(f'{i}. la fuente no puede ser Instagram ni TikTok: busca una nota o un blog que lo cuente')
        if t.get('formato') and t['formato'] not in FORMATOS:
            problemas.append(f'{i}. formato «{t["formato"]}»: usa {", ".join(FORMATOS)}')
        for aviso in revisar(t.get('idea', '')):
            problemas.append(f'{i}. la idea {aviso}')
        t['productos'] = [str(c) for c in t.get('productos') or []]
    return problemas


def pagina(datos):
    filas = ''.join(
        f'<article><div class="n">{i:02d}</div><div><span class="f">{e(t.get("formato") or "idea")}</span>'
        f'<h2>{e(t["tema"])}</h2><p>{e(t["que_es"])}</p><p class="por"><b>Por qué te sirve:</b> {e(t["por_que"])}</p>'
        f'<p class="idea"><b>Qué publicar:</b> {e(t["idea"])}</p>'
        + (f'<p class="usada">✓ En el plan ({e(t["usada"]["id"])})</p>' if t.get('usada') else '')
        + f'<a href="{e(t["fuente"])}" target="_blank" rel="noopener">De dónde salió</a></div></article>'
        for i, t in enumerate(datos['tendencias'], 1))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tendencias de la semana</title><style>
body {{ margin:0; background:#f4efe8; color:#221c1c; font-family:"Avenir Next","Helvetica Neue",Arial,sans-serif; }}
main {{ max-width:720px; margin:auto; padding:30px 16px 60px; }}
.chico {{ font-size:12px; letter-spacing:.3em; text-transform:uppercase; color:#8c3b4a; }}
h1 {{ font-family:Georgia,serif; font-style:italic; font-weight:500; font-size:44px; margin:6px 0; }}
.sub {{ color:#6f6763; margin:0 0 10px; }}
article {{ display:grid; grid-template-columns:52px 1fr; gap:14px; background:#fff; border-radius:16px; padding:18px; margin-top:14px; box-shadow:0 8px 22px rgba(90,60,40,.07); }}
.n {{ font-family:Georgia,serif; font-size:30px; color:#b39a73; }}
.f {{ font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:#8c3b4a; }}
h2 {{ font-family:Georgia,serif; font-size:24px; margin:4px 0 8px; }}
p {{ margin:0 0 8px; line-height:1.5; font-size:15px; }} .idea {{ background:#f6ece8; padding:8px 10px; border-radius:10px; }}
.usada {{ color:#3d6b52; font-size:14px; }} a {{ color:#8c3b4a; font-size:14px; }}
</style></head><body><main><div class="chico">Semana del {datos["desde"]}</div><h1>Lo que se está hablando</h1>
<p class="sub">{e(datos.get("temporada") or "")}. Ideas para subirte a la conversación con tus productos.</p>{filas}</main></body></html>'''


def cmd_pendiente(_):
    datos = leer_json(archivo())
    if datos:
        print(f'Ya hay {len(datos["tendencias"])} tendencias de esta semana ({semana()}). Míralas con «actuales».')
        return
    print(f'No hay tendencias de esta semana ({semana()}). Temporada: {temporada()}.')
    print('Busca en noticias, blogs y revistas de belleza (nunca entrando a Instagram ni TikTok), por ejemplo:')
    for q in busquedas():
        print('  -', q)
    print('Elige hasta 5 que Isabella pueda hacer con productos Farmasi y guárdalas con «guardar».')


def cmd_guardar(a):
    lote = leer_json(a.lote)
    problemas = validar(lote)
    if problemas:
        print('No se guardó. Corrige:')
        for p in problemas:
            print('  ' + p)
        sys.exit(1)
    datos = {'semana': semana(), 'desde': lunes().isoformat(), 'temporada': temporada(), 'tendencias': lote}
    CARPETA.mkdir(exist_ok=True)
    archivo().write_text(json.dumps(datos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    web = archivo().with_suffix('.html')
    web.write_text(pagina(datos), encoding='utf-8')
    if COMPARTIDO.is_dir():
        (COMPARTIDO / 'planes').mkdir(exist_ok=True)
        shutil.copy2(web, COMPARTIDO / 'planes' / f'tendencias-{web.name}')
    print(f'Guardadas {len(lote)} tendencias de la semana {semana()}: {archivo().relative_to(RAIZ)} y {web.relative_to(RAIZ)}')


def cmd_actuales(_):
    datos = leer_json(archivo())
    if not datos:
        print(f'No hay tendencias de esta semana ({semana()}): corre «pendiente» para ver qué buscar.')
        return
    print(f'Tendencias de la semana {datos["semana"]} (desde el {datos["desde"]}) · {datos.get("temporada", "")}')
    for i, t in enumerate(datos['tendencias'], 1):
        print(f'\n{i}. {t["tema"]}' + (f' [{t["formato"]}]' if t.get('formato') else '') + (' ✓ usada' if t.get('usada') else ''))
        print(f'   Qué es: {t["que_es"]}')
        print(f'   Por qué le sirve: {t["por_que"]}')
        print(f'   Idea: {t["idea"]}')
        if t.get('productos'):
            print(f'   Productos: {", ".join(t["productos"])}')
        print(f'   Fuente: {t["fuente"]}')


def cmd_usada(a):
    datos = leer_json(archivo())
    if not datos or not 1 <= a.numero <= len(datos['tendencias']):
        sys.exit('No encontré esa tendencia en las de esta semana.')
    datos['tendencias'][a.numero - 1]['usada'] = {'plan': a.plan, 'id': a.id}
    archivo().write_text(json.dumps(datos, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    archivo().with_suffix('.html').write_text(pagina(datos), encoding='utf-8')
    print(f'Tendencia {a.numero} marcada como usada en {a.id}.')


def cmd_historial(_):
    for f in sorted(CARPETA.glob('*.json')) if CARPETA.is_dir() else []:
        d = leer_json(f, {})
        usadas = sum(1 for t in d.get('tendencias', []) if t.get('usada'))
        print(f"{d.get('semana')}: {len(d.get('tendencias', []))} tendencias, {usadas} en el plan · "
              + ', '.join(t['tema'] for t in d.get('tendencias', [])))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('pendiente').set_defaults(f=cmd_pendiente)
    g = sub.add_parser('guardar')
    g.add_argument('lote')
    g.set_defaults(f=cmd_guardar)
    sub.add_parser('actuales').set_defaults(f=cmd_actuales)
    u = sub.add_parser('usada')
    u.add_argument('numero', type=int)
    u.add_argument('--plan', required=True)
    u.add_argument('--id', required=True)
    u.set_defaults(f=cmd_usada)
    sub.add_parser('historial').set_defaults(f=cmd_historial)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
