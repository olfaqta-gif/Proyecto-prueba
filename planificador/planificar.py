#!/usr/bin/env python3
"""Planificador de contenido Farmasi.

El agente estratega-contenido escribe el plan (un plan.json con la estrategia y el
calendario). Este script lo revisa, lo muestra como calendario (plan.html) y lleva la
cuenta de qué ya se hizo, para que Jarvis le pase cada anuncio al agente de contenido.

Uso (desde la raíz del repositorio):
  python3 planificador/planificar.py estado                       # qué hay hecho y qué planes existen
  python3 planificador/planificar.py revisar planificador/planes/<plan>.json
  python3 planificador/planificar.py siguiente planificador/planes/<plan>.json
  python3 planificador/planificar.py marcar planificador/planes/<plan>.json <id> hecho
  python3 planificador/planificar.py resultado planificador/planes/<plan>.json <id> --vistas 1500 --mensajes 9 --ventas 3

Solo usa la librería estándar de Python.
"""
import argparse
import base64
import datetime
import html
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PRODUCTOS = RAIZ / 'agente-contenido' / 'productos'
SALIDA_ANUNCIOS = RAIZ / 'agente-contenido' / 'salida'
CATALOGO = RAIZ / 'lector-farmasi' / 'salida' / 'catalogo.json'
PLANES = AQUI / 'planes'

ESTILOS = ('clasico', 'favorito', 'razones')
FORMATOS = ('9x16', '4x5', '1x1', '16x9')
# anuncio = video que hace el agente creador-contenido; el resto lo graba o publica Julio
TIPOS = {
    'anuncio': 'Anuncio en video (lo hace el agente de contenido)',
    'reel': 'Reel o TikTok que grabas tú',
    'historia': 'Historia (Stories)',
    'carrusel': 'Carrusel de fotos',
    'post': 'Post con foto',
    'en-vivo': 'En vivo',
}
ESTADOS = ('pendiente', 'hecho', 'publicado', 'saltado')
DIAS = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')

# Lo que nunca debe salir en un plan (mismas reglas que el agente de contenido)
PROHIBIDO = [
    (re.compile(r'\$\s?\d|\d\s?(usd|dólares|dolares)\b|\bprecio\b', re.I),
     'menciona precios (Julio los maneja aparte)'),
    (re.compile(r'\d+\s?%'), 'usa porcentajes de resultados'),
    (re.compile(r'\bcura\b|\bcuran\b|\belimina\w* (el |la |los |las )?(acné|acne|arrugas|manchas)|\bgarantiz', re.I),
     'hace una promesa médica o garantizada'),
    (re.compile(r'gana\w* dinero|\bingresos\b|hazte ric|libertad financiera|\bsueldo\b', re.I),
     'promete ingresos'),
]
CAMPOS_TEXTO = ('idea', 'gancho', 'guion', 'caption', 'llamado')


# ---------- utilidades ----------

def leer_json(archivo):
    return json.loads(Path(archivo).read_text(encoding='utf-8'))


def escribir_json(archivo, datos):
    Path(archivo).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fecha(texto):
    return datetime.date.fromisoformat(texto)


def carpeta_producto(prod):
    """Carpeta del producto en agente-contenido/productos (si existe)."""
    slug = (prod or {}).get('slug')
    if slug and (PRODUCTOS / slug).is_dir():
        return PRODUCTOS / slug
    codigo = str((prod or {}).get('codigo') or '')
    if codigo:
        for d in PRODUCTOS.glob('*/datos.json'):
            try:
                if str(leer_json(d).get('codigo')) == codigo:
                    return d.parent
            except (OSError, ValueError):
                pass
    return None


def foto_producto(prod):
    slug = (prod or {}).get('slug')
    for c in (carpeta_producto(prod), RAIZ / 'lector-farmasi' / 'salida' / slug if slug else None):
        if not c:
            continue
        for nombre in ('producto.jpg', 'producto.png', 'producto.webp'):
            if (c / nombre).exists():
                return c / nombre
    return None


def foto_incrustada(foto):
    """La foto dentro del html, para que el calendario se vea aunque se mueva de carpeta."""
    tipo = {'.png': 'png', '.webp': 'webp'}.get(foto.suffix, 'jpeg')
    return f'data:image/{tipo};base64,' + base64.b64encode(foto.read_bytes()).decode()


def nombre_producto(prod):
    if not prod:
        return ''
    return prod.get('nombre') or prod.get('slug') or str(prod.get('codigo') or '')


# ---------- estado ----------

def historial_anuncios():
    """Productos con ficha en el agente de contenido: estilo y si ya tiene videos."""
    filas = []
    for ficha in sorted(PRODUCTOS.glob('*/ficha.json'), key=lambda f: f.stat().st_mtime):
        try:
            f = leer_json(ficha)
        except ValueError:
            continue
        slug = ficha.parent.name
        videos = sorted(p.parent.name for p in (SALIDA_ANUNCIOS / slug).glob('*/anuncio-*.mp4'))
        filas.append({
            'slug': slug,
            'nombre': (f.get('producto') or {}).get('nombre', slug),
            'estilo': f.get('estilo') or 'clasico',
            'videos': sorted(set(videos)),
            'fecha': datetime.date.fromtimestamp(ficha.stat().st_mtime).isoformat(),
        })
    return filas


def cmd_estado(a):
    filas = historial_anuncios()
    print('Anuncios ya trabajados (del más viejo al más reciente):')
    for r in filas:
        v = ', '.join(r['videos']) if r['videos'] else 'sin video en esta copia'
        print(f'  - {r["nombre"]} ({r["slug"]}): estilo {r["estilo"]}; videos: {v}')
    if filas:
        print(f'  Último estilo usado: {filas[-1]["estilo"]} (el próximo anuncio debe usar otro).')
    else:
        print('  (ninguno)')

    if CATALOGO.exists():
        c = leer_json(CATALOGO)
        print(f'\nCatálogo del scraper: {len(c.get("productos", []))} productos, leído el {c.get("leido")}'
              f' ({CATALOGO.relative_to(RAIZ)}).')
    else:
        print('\nCatálogo del scraper: no hay copia; pídele al scraper-farmasi "mejores N" o "buscar".')

    planes = sorted(PLANES.glob('*.json'))
    print('\nPlanes:')
    if not planes:
        print('  (ninguno)')
    for p in planes:
        try:
            plan = leer_json(p)
        except ValueError:
            print(f'  - {p.relative_to(RAIZ)}: no se puede leer')
            continue
        pubs = plan.get('publicaciones', [])
        cuenta = {e: sum(1 for x in pubs if x.get('estado', 'pendiente') == e) for e in ESTADOS}
        resumen = ', '.join(f'{n} {e}' for e, n in cuenta.items() if n)
        print(f'  - {p.relative_to(RAIZ)}: "{plan.get("nombre")}" desde {plan.get("inicio")}; {resumen}')


# ---------- revisar ----------

def revisar(plan):
    """Devuelve (errores, avisos)."""
    errores, avisos = [], []
    for campo in ('nombre', 'inicio', 'objetivo', 'pilares', 'publicaciones'):
        if not plan.get(campo):
            errores.append(f'falta "{campo}" en el plan')
    if errores:
        return errores, avisos
    try:
        fecha(plan['inicio'])
    except ValueError:
        errores.append(f'"inicio" no es una fecha AAAA-MM-DD: {plan["inicio"]}')

    pilares = {p.get('id') for p in plan['pilares']}
    for p in plan['pilares']:
        if not p.get('id') or not p.get('nombre'):
            errores.append(f'cada pilar necesita "id" y "nombre": {p}')

    ids = set()
    anuncios = []
    for i, pub in enumerate(plan['publicaciones'], 1):
        etiqueta = f'publicación {pub.get("id", f"#{i}")}'
        if 'id' not in pub:
            errores.append(f'{etiqueta}: falta "id"')
        elif pub['id'] in ids:
            errores.append(f'{etiqueta}: el id se repite')
        ids.add(pub.get('id'))
        try:
            fecha(pub.get('fecha', ''))
        except ValueError:
            errores.append(f'{etiqueta}: "fecha" no es AAAA-MM-DD ({pub.get("fecha")})')
        if pub.get('tipo') not in TIPOS:
            errores.append(f'{etiqueta}: tipo "{pub.get("tipo")}" no existe (usa {", ".join(TIPOS)})')
        if pub.get('pilar') not in pilares:
            errores.append(f'{etiqueta}: pilar "{pub.get("pilar")}" no está en "pilares"')
        if pub.get('estado', 'pendiente') not in ESTADOS:
            errores.append(f'{etiqueta}: estado "{pub.get("estado")}" no existe (usa {", ".join(ESTADOS)})')
        if not pub.get('idea'):
            errores.append(f'{etiqueta}: falta "idea" (qué se publica, en una frase)')

        prod = pub.get('producto')
        if prod is not None and not (prod.get('codigo') or prod.get('slug')):
            errores.append(f'{etiqueta}: el producto necesita "codigo" o "slug"')
        if pub.get('tipo') == 'anuncio':
            if not prod:
                errores.append(f'{etiqueta}: un anuncio necesita "producto" (codigo, slug y nombre)')
            if pub.get('estilo') not in ESTILOS:
                errores.append(f'{etiqueta}: "estilo" debe ser {", ".join(ESTILOS)}')
            malos = [f for f in pub.get('formatos', []) if f not in FORMATOS]
            if malos:
                errores.append(f'{etiqueta}: formatos que no existen: {", ".join(malos)}')
            if prod and not carpeta_producto(prod):
                avisos.append(f'{etiqueta}: {nombre_producto(prod)} todavía no tiene carpeta en '
                              'agente-contenido/productos (el agente de contenido lo traerá con el scraper)')
            if not pub.get('porque'):
                avisos.append(f'{etiqueta}: explica en "porque" por qué este producto (sale de analizar.py)')
            anuncios.append(pub)
        elif not (pub.get('guion') or pub.get('caption')):
            avisos.append(f'{etiqueta}: como lo haces tú, conviene escribir "guion" o "caption"')

        for campo in CAMPOS_TEXTO:
            texto = pub.get(campo) or ''
            for patron, motivo in PROHIBIDO:
                if patron.search(texto):
                    errores.append(f'{etiqueta}: "{campo}" {motivo}: «{texto[:70]}»')

    # Que los anuncios no se vean iguales: estilos alternados, también con el último hecho
    anuncios.sort(key=lambda p: p.get('fecha', ''))
    hist = historial_anuncios()
    previo = hist[-1]['estilo'] if hist else None
    for pub in anuncios:
        if pub.get('estado', 'pendiente') == 'pendiente' and pub.get('estilo') == previo:
            avisos.append(f'publicación {pub.get("id")}: repite el estilo "{previo}" del anuncio anterior')
        previo = pub.get('estilo')

    # El mismo producto dos veces en menos de una semana
    vistos = {}
    for pub in sorted(plan['publicaciones'], key=lambda p: p.get('fecha', '')):
        clave = str((pub.get('producto') or {}).get('codigo') or (pub.get('producto') or {}).get('slug') or '')
        if not clave:
            continue
        try:
            f = fecha(pub['fecha'])
        except (KeyError, ValueError):
            continue
        if clave in vistos and (f - vistos[clave]).days < 7:
            avisos.append(f'publicación {pub.get("id")}: {nombre_producto(pub["producto"])} '
                          'sale dos veces en la misma semana')
        vistos[clave] = f

    # Mezcla de pilares
    total = len(plan['publicaciones'])
    for p in plan['pilares']:
        n = sum(1 for x in plan['publicaciones'] if x.get('pilar') == p.get('id'))
        if n == 0:
            avisos.append(f'el pilar "{p.get("nombre")}" no tiene ninguna publicación')
        meta = p.get('porcentaje')
        if meta and total and abs(100 * n / total - meta) > 15:
            avisos.append(f'el pilar "{p.get("nombre")}" tiene {round(100 * n / total)}% '
                          f'de las publicaciones y la meta era {meta}%')
    return errores, avisos


# ---------- calendario html ----------

COLORES = ['#d9677a', '#c9a227', '#4f9d7a', '#8a6fc4', '#3f86c4', '#d9823b', '#6b7a8f']


def calendario_html(plan, archivo_plan):
    e = html.escape
    color = {p['id']: COLORES[i % len(COLORES)] for i, p in enumerate(plan['pilares'])}
    pilar_nombre = {p['id']: p['nombre'] for p in plan['pilares']}
    total = len(plan['publicaciones']) or 1

    pilares = []
    for p in plan['pilares']:
        n = sum(1 for x in plan['publicaciones'] if x.get('pilar') == p['id'])
        pilares.append(f'<li><span class="punto" style="background:{color[p["id"]]}"></span>'
                       f'<b>{e(p["nombre"])}</b> · {round(100 * n / total)}%'
                       f'<br><small>{e(p.get("porque", ""))}</small></li>')

    por_dia = {}
    for pub in plan['publicaciones']:
        por_dia.setdefault(pub['fecha'], []).append(pub)
    fechas = sorted(por_dia)
    inicio = min(fecha(plan['inicio']), fecha(fechas[0])) if fechas else fecha(plan['inicio'])
    inicio -= datetime.timedelta(days=inicio.weekday())
    fin = fecha(fechas[-1]) if fechas else inicio

    semanas = []
    dia = inicio
    while dia <= fin:
        celdas = []
        for _ in range(7):
            tarjetas = []
            for pub in sorted(por_dia.get(dia.isoformat(), []), key=lambda p: p.get('hora', '')):
                estado = pub.get('estado', 'pendiente')
                foto = foto_producto(pub.get('producto'))
                img = f'<img src="{foto_incrustada(foto)}" alt="">' if foto else ''
                detalles = []
                if pub.get('tipo') == 'anuncio':
                    detalles.append(f'Estilo {e(pub.get("estilo", ""))} · '
                                    f'{e(", ".join(pub.get("formatos") or ["los 4 formatos"]))}')
                if pub.get('porque'):
                    detalles.append(f'<b>Por qué:</b> {e(pub["porque"])}')
                r = pub.get('resultados')
                if r:
                    detalles.append('<b>Resultado:</b> ' + ' · '.join(
                        f'{r[k]} {k}' for k in ('vistas', 'mensajes', 'ventas') if r.get(k) is not None))
                if pub.get('gancho'):
                    detalles.append(f'<i>«{e(pub["gancho"])}»</i>')
                if pub.get('guion'):
                    detalles.append(f'<b>Guion:</b> {e(pub["guion"])}')
                if pub.get('llamado'):
                    detalles.append(f'<b>Llamado:</b> {e(pub["llamado"])}')
                tarjetas.append(
                    f'<div class="tarjeta {e(estado)}" style="border-color:{color.get(pub.get("pilar"), "#999")}">'
                    f'<div class="cabeza"><span class="tipo">{e(pub.get("tipo", ""))}</span>'
                    f'<span class="estado">{e(estado)}</span></div>{img}'
                    f'<div class="pilar" style="color:{color.get(pub.get("pilar"), "#999")}">'
                    f'{e(pilar_nombre.get(pub.get("pilar"), ""))}</div>'
                    f'<div class="idea">{e(pub.get("idea", ""))}</div>'
                    f'<div class="red">{e(pub.get("red", ""))} {e(pub.get("hora", ""))}</div>'
                    f'{"".join(f"<p>{d}</p>" for d in detalles)}</div>')
            vacio = '' if tarjetas else ' vacio'
            celdas.append(f'<div class="dia{vacio}"><div class="fecha">{DIAS[dia.weekday()]} '
                          f'{dia.day}/{dia.month}</div>{"".join(tarjetas)}</div>')
            dia += datetime.timedelta(days=1)
        semanas.append(f'<div class="semana">{"".join(celdas)}</div>')

    hechos = sum(1 for x in plan['publicaciones'] if x.get('estado') in ('hecho', 'publicado'))
    notas = ''.join(f'<li>{e(n)}</li>' for n in plan.get('notas', []))
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(plan["nombre"])}</title>
<style>
:root {{ --fondo:#faf7f5; --texto:#2b2326; --suave:#7a6c70; --tarjeta:#fff; --linea:#eadfe2; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fondo:#1b1719; --texto:#f3ecee; --suave:#b4a6aa; --tarjeta:#262023; --linea:#3a3135; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px 16px 48px; font:15px/1.45 system-ui, sans-serif; background:var(--fondo); color:var(--texto); }}
main {{ max-width:1400px; margin:0 auto; }}
h1 {{ margin:0 0 4px; font-size:26px; }}
.sub {{ color:var(--suave); margin:0 0 20px; }}
.resumen {{ display:grid; gap:16px; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); margin-bottom:24px; }}
.caja {{ background:var(--tarjeta); border:1px solid var(--linea); border-radius:12px; padding:14px 16px; }}
.caja h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.06em; color:var(--suave); margin:0 0 8px; }}
.caja ul {{ margin:0; padding-left:0; list-style:none; }} .caja li {{ margin-bottom:8px; }}
.notas ul {{ padding-left:18px; list-style:disc; }}
.punto {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }}
.semana {{ display:grid; grid-template-columns:repeat(7, minmax(0, 1fr)); gap:8px; margin-bottom:8px; }}
.dia {{ background:var(--tarjeta); border:1px solid var(--linea); border-radius:10px; padding:8px; min-height:90px; }}
.dia.vacio {{ opacity:.55; }}
.fecha {{ font-size:12px; color:var(--suave); text-transform:capitalize; margin-bottom:6px; }}
.tarjeta {{ border-left:4px solid; border-radius:6px; padding:6px 8px; margin-bottom:8px; background:var(--fondo); font-size:13px; }}
.tarjeta img {{ width:100%; max-height:120px; object-fit:contain; background:#fff; border-radius:4px; margin:4px 0; }}
.tarjeta p {{ margin:4px 0 0; }}
.cabeza {{ display:flex; justify-content:space-between; gap:4px; font-size:11px; text-transform:uppercase; letter-spacing:.04em; }}
.tipo {{ font-weight:700; }} .estado {{ color:var(--suave); }}
.hecho .estado, .publicado .estado {{ color:#4f9d7a; font-weight:700; }}
.saltado {{ opacity:.45; text-decoration:line-through; }}
.pilar {{ font-size:12px; font-weight:600; margin-top:2px; }}
.idea {{ font-weight:600; margin-top:2px; }}
.red {{ color:var(--suave); font-size:12px; }}
@media (max-width: 900px) {{
  .semana {{ grid-template-columns:1fr; }}
  .dia.vacio {{ display:none; }}
}}
</style></head>
<body><main>
<h1>{e(plan["nombre"])}</h1>
<p class="sub">Desde el {fecha(plan["inicio"]).strftime("%d/%m/%Y")} · {len(plan["publicaciones"])} publicaciones · {hechos} listas</p>
<div class="resumen">
  <div class="caja"><h2>Objetivo</h2>{e(plan["objetivo"])}{f'<br><br><b>Basado en:</b> {e(plan["basado_en"])}' if plan.get("basado_en") else ''}<br><br><b>Para quién:</b> {e(plan.get("publico", ""))}<br><b>Ritmo:</b> {e(plan.get("frecuencia", ""))}</div>
  <div class="caja"><h2>Pilares de contenido</h2><ul>{"".join(pilares)}</ul></div>
  {f'<div class="caja notas"><h2>Notas</h2><ul>{notas}</ul></div>' if notas else ''}
</div>
{"".join(semanas)}
</main></body></html>
'''


def cmd_revisar(a):
    archivo = Path(a.plan)
    plan = leer_json(archivo)
    errores, avisos = revisar(plan)
    for x in errores:
        print(f'ERROR: {x}')
    for x in avisos:
        print(f'aviso: {x}')
    if errores:
        print(f'\n{len(errores)} errores: corrige el plan y vuelve a revisar.')
        sys.exit(1)
    salida = archivo.with_suffix('.html')
    salida.write_text(calendario_html(plan, archivo), encoding='utf-8')
    print(f'Plan correcto ({len(avisos)} avisos). Calendario: {salida}')


# ---------- siguiente / marcar ----------

def cmd_siguiente(a):
    plan = leer_json(a.plan)
    pendientes = sorted((p for p in plan['publicaciones']
                         if p.get('tipo') == 'anuncio' and p.get('estado', 'pendiente') == 'pendiente'),
                        key=lambda p: p['fecha'])
    if not pendientes:
        print('No quedan anuncios pendientes en este plan.')
        return
    p = pendientes[0]
    prod = p['producto']
    carpeta = carpeta_producto(prod)
    print(f'Siguiente anuncio del plan "{plan["nombre"]}" (quedan {len(pendientes)}):')
    print(f'  id: {p["id"]}  ·  fecha: {p["fecha"]}  ·  red: {p.get("red", "")}')
    print(f'  producto: {nombre_producto(prod)}  ·  código: {prod.get("codigo", "")}  ·  slug: {prod.get("slug", "")}')
    print(f'  carpeta: {carpeta.relative_to(RAIZ) if carpeta else "no existe todavía (traerla con el scraper)"}')
    print(f'  estilo: {p["estilo"]}  ·  formatos: {", ".join(p.get("formatos") or FORMATOS)}')
    print(f'  idea: {p["idea"]}')
    if p.get('gancho'):
        print(f'  gancho sugerido: {p["gancho"]}')
    if p.get('llamado'):
        print(f'  llamado: {p["llamado"]}')
    print(f'\nAl terminar: python3 planificador/planificar.py marcar {a.plan} {p["id"]} hecho')


def cmd_marcar(a):
    archivo = Path(a.plan)
    plan = leer_json(archivo)
    for p in plan['publicaciones']:
        if str(p.get('id')) == str(a.id):
            p['estado'] = a.estado
            if a.nota:
                p['nota'] = a.nota
            escribir_json(archivo, plan)
            archivo.with_suffix('.html').write_text(calendario_html(plan, archivo), encoding='utf-8')
            print(f'Publicación {a.id} marcada como {a.estado}. Calendario actualizado.')
            return
    print(f'No hay publicación con id {a.id} en {archivo}')
    sys.exit(1)


def cmd_resultado(a):
    archivo = Path(a.plan)
    plan = leer_json(archivo)
    for p in plan['publicaciones']:
        if str(p.get('id')) == str(a.id):
            r = p.setdefault('resultados', {})
            for k in ('vistas', 'mensajes', 'ventas', 'guardados', 'compartidos'):
                if getattr(a, k) is not None:
                    r[k] = getattr(a, k)
            if p.get('estado', 'pendiente') in ('pendiente', 'hecho'):
                p['estado'] = 'publicado'
            escribir_json(archivo, plan)
            archivo.with_suffix('.html').write_text(calendario_html(plan, archivo), encoding='utf-8')
            print(f'Resultados de la publicación {a.id} guardados: {r}. El estratega los usará en el próximo plan.')
            return
    print(f'No hay publicación con id {a.id} en {archivo}')
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description='Planificador de contenido Farmasi')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('estado', help='anuncios hechos, último estilo, catálogo y planes').set_defaults(f=cmd_estado)
    r = sub.add_parser('revisar', help='revisar un plan.json y crear su calendario plan.html')
    r.add_argument('plan')
    r.set_defaults(f=cmd_revisar)
    s = sub.add_parser('siguiente', help='el próximo anuncio pendiente, listo para el agente de contenido')
    s.add_argument('plan')
    s.set_defaults(f=cmd_siguiente)
    m = sub.add_parser('marcar', help='cambiar el estado de una publicación')
    m.add_argument('plan')
    m.add_argument('id')
    m.add_argument('estado', choices=ESTADOS)
    m.add_argument('--nota', help='dónde quedó el video, etc.')
    m.set_defaults(f=cmd_marcar)
    r = sub.add_parser('resultado', help='guardar cómo le fue a una publicación (para aprender)')
    r.add_argument('plan')
    r.add_argument('id')
    for k in ('vistas', 'mensajes', 'ventas', 'guardados', 'compartidos'):
        r.add_argument(f'--{k}', type=int)
    r.set_defaults(f=cmd_resultado)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
