#!/usr/bin/env python3
"""Agente de comunidad: respuestas listas para los comentarios y mensajes de Isabella.

Isabella deja capturas de sus comentarios y mensajes en comunidad/capturas/ (o le pega el
texto a Isa). El agente de comunidad los lee, escribe una respuesta para cada uno en la voz
de Isabella y este programa arma la hoja para copiar y pegar. Además anota en la libreta de
clientas a cada persona interesada, para que nadie se pierda.

Uso (desde la carpeta del proyecto):
  python3 comunidad/responder.py pendientes          # capturas sin leer
  python3 comunidad/responder.py hoja lote.json      # hoja de respuestas + libreta
  python3 comunidad/responder.py rapidas             # kit de respuestas rápidas para guardar en el celular
  python3 comunidad/responder.py resumen             # cuántos mensajes se respondieron y de qué

El lote es una lista de conversaciones (ver comunidad/README.md):
  [{"red": "instagram", "donde": "mensaje", "usuario": "dani.ortiz", "nombre": "Daniela",
    "texto": "Hola! cuanto cuesta el serum?", "intencion": "precio", "producto": "Vitamin C Glow Serum",
    "respuesta": "¡Hola, Daniela! ...", "otra": "(opcional) otra forma de decirlo",
    "captura": "comunidad/capturas/IMG_1.png"}]
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
CAPTURAS = AQUI / 'capturas'
RESPUESTAS = AQUI / 'respuestas'
DATOS = AQUI / 'datos'
HISTORIAL = DATOS / 'historial.json'
RAPIDAS = AQUI / 'respuestas-rapidas.json'
PRECIOS = AQUI / 'precios.md'
COMPARTIDO = Path('/mnt/project-files')
IMAGENES = ('.png', '.jpg', '.jpeg', '.heic', '.webp')

# Qué quiere la persona, en orden de importancia (lo que más cerca está de comprar va primero).
INTENCIONES = {
    'comprar': {'nombre': 'Quiere comprar', 'icono': '🛍️', 'color': '#d64f8a', 'etapa': 'interesada'},
    'precio': {'nombre': 'Pregunta el precio', 'icono': '💲', 'color': '#e07a3f', 'etapa': 'pregunto'},
    'producto': {'nombre': 'Duda del producto', 'icono': '🧴', 'color': '#8f7cf6', 'etapa': 'pregunto'},
    'envio': {'nombre': 'Envío o entrega', 'icono': '📦', 'color': '#2f9e76', 'etapa': 'pregunto'},
    'negocio': {'nombre': 'Quiere vender Farmasi', 'icono': '🤝', 'color': '#5b8def', 'etapa': 'pregunto'},
    'queja': {'nombre': 'Problema o queja', 'icono': '⚠️', 'color': '#d9534f', 'etapa': None},
    'elogio': {'nombre': 'Cariño y elogios', 'icono': '💕', 'color': '#c99a5b', 'etapa': None},
    'otro': {'nombre': 'Otro', 'icono': '💬', 'color': '#8f7d8c', 'etapa': None},
    'spam': {'nombre': 'No responder', 'icono': '🚫', 'color': '#9aa0b4', 'etapa': None},
}

# Promesas que Isabella no puede hacer (ni de dinero ni de salud).
PROMESAS = re.compile(
    r'ganar(?:ás|as)? (?:dinero|\$)|ingresos? (?:extra|seguros?|garantizad)|libertad financiera|hazte ric|'
    r'gana(?:r)? desde casa|sueldo|renuncia a tu trabajo|'
    r'\bcura\b|\bcurar|elimina(?:r)? (?:el |las |los )?(?:acn[eé]|manchas|arrugas|celulitis)|'
    r'garantiza|100 ?%|resultados? (?:seguros?|garantizad)|baja(?:r)? de peso|adelgaz|quema grasa|'
    r'sin efectos secundarios|m[eé]dicamente probado|aprobado por (?:la )?fda', re.I)
PRECIO = re.compile(r'\$\s?\d|\d+(?:[.,]\d+)?\s?(?:d[oó]lares|usd|pesos|soles|euros)\b', re.I)


def libreta():
    spec = importlib.util.spec_from_file_location('libreta', RAIZ / 'clientas' / 'libreta.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def leer_json(archivo, defecto):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def esc(t):
    return html.escape(str(t or ''))


def revisar_texto(t, hay_precios):
    """Lo que hay que cambiar antes de mandar una respuesta."""
    avisos = []
    m = PROMESAS.search(t or '')
    if m:
        avisos.append(f'promete algo que no se puede prometer («{m.group(0)}»)')
    if PRECIO.search(t or '') and not hay_precios:
        avisos.append('tiene un precio y no hay lista de precios de Isabella (usa [precio])')
    return avisos


def enlace(item):
    u = (item.get('usuario') or '').lstrip('@').strip()
    tel = re.sub(r'\D', '', item.get('telefono') or '')
    red = item.get('red', 'instagram')
    if tel:
        return f'https://wa.me/{tel}'
    if not u:
        return ''
    return {'tiktok': f'https://www.tiktok.com/@{u}', 'facebook': f'https://m.me/{u}'}.get(red, f'https://ig.me/m/{u}')


# ---------- pendientes ----------

def cmd_pendientes(_):
    capturas = sorted(f for f in CAPTURAS.glob('*') if f.suffix.lower() in IMAGENES) if CAPTURAS.is_dir() else []
    if not capturas:
        print('No hay capturas nuevas en comunidad/capturas/.')
    else:
        print(f'{len(capturas)} capturas por leer:')
        for f in capturas:
            print(f'  {f.relative_to(RAIZ)}')
    print('Lista de precios de Isabella: ' + ('sí (comunidad/precios.md)' if PRECIOS.exists() else
                                                'no hay; en las respuestas usa [precio]'))


# ---------- hoja de respuestas ----------

def cmd_hoja(a):
    lote = leer_json(a.lote, None)
    if not isinstance(lote, list) or not lote:
        sys.exit('El lote tiene que ser una lista de conversaciones (ver comunidad/README.md).')
    hay_precios = PRECIOS.exists()
    l = libreta()
    datos = l.cargar()
    ahora = datetime.datetime.now()
    hoy = ahora.date().isoformat()
    anotadas, problemas, movidas = [], [], []
    for i, item in enumerate(lote, 1):
        item.setdefault('red', 'instagram')
        item.setdefault('donde', 'mensaje')
        if item.get('intencion') not in INTENCIONES:
            item['intencion'] = 'otro'
        item['avisos'] = revisar_texto(item.get('respuesta', ''), hay_precios) + \
            [f'(otra) {x}' for x in revisar_texto(item.get('otra', ''), hay_precios)]
        if item['intencion'] != 'spam' and not (item.get('respuesta') or '').strip():
            item['avisos'].append('falta la respuesta')
        if item['avisos']:
            problemas.append(f"{i}. @{item.get('usuario') or item.get('nombre')}: " + '; '.join(item['avisos']))
        item['enlace'] = enlace(item)
        # A la libreta: cada persona que pregunta o quiere comprar (y quien se queja, para no olvidarla)
        etapa = INTENCIONES[item['intencion']]['etapa']
        if (etapa or item['intencion'] == 'queja') and (item.get('usuario') or item.get('nombre')):
            ya = next((c for c in (l.buscar_clienta(datos, q) for q in
                                   ('@' + item['usuario'] if item.get('usuario') else None,
                                    item.get('telefono'), item.get('nombre')) if q) if c), None)
            texto = (item.get('texto') or '').strip().replace('\n', ' ')
            nota = f"{INTENCIONES[item['intencion']]['nombre']} por {item['donde']} de {item['red']}: «{texto[:140]}»"
            campos = {'nombre': item.get('nombre') or None, 'usuario': item.get('usuario'), 'red': item['red'],
                      'telefono': item.get('telefono'), 'origen': f"{item['donde']} de {item['red']}",
                      'intereses': [item['producto']] if item.get('producto') else []}
            if not ya and etapa:
                campos['etapa'] = etapa
            c = l.guardar_clienta(datos, campos, nota)
            if ya and etapa == 'interesada' and c.get('etapa') == 'pregunto':
                l.mover(datos, c, 'interesada')
            item['clienta'] = c['id']
            anotadas.append(('nueva' if not ya else 'ya estaba', c['nombre']))
        # La captura ya se leyó
        cap = item.get('captura')
        if cap and not a.sin_mover:
            origen = (RAIZ / cap) if not Path(cap).is_absolute() else Path(cap)
            if origen.exists() and origen.parent == CAPTURAS:
                (CAPTURAS / 'leidas').mkdir(parents=True, exist_ok=True)
                destino = CAPTURAS / 'leidas' / origen.name
                shutil.move(str(origen), destino)
                item['captura'] = str(destino.relative_to(RAIZ))
                movidas.append(origen.name)
    l.guardar(datos)

    orden = list(INTENCIONES)
    lote.sort(key=lambda x: orden.index(x['intencion']))
    RESPUESTAS.mkdir(parents=True, exist_ok=True)
    nombre = ahora.strftime('%Y-%m-%d-%H%M')
    salida = RESPUESTAS / f'{nombre}.html'
    salida.write_text(pagina_hoja(lote, ahora, hay_precios), encoding='utf-8')
    if COMPARTIDO.is_dir() and not a.sin_copia:
        (COMPARTIDO / 'comunidad').mkdir(exist_ok=True)
        shutil.copy(salida, COMPARTIDO / 'comunidad' / salida.name)

    historial = leer_json(HISTORIAL, [])
    historial.append({'fecha': hoy, 'hoja': str(salida.relative_to(RAIZ)), 'total': len(lote),
                      'intenciones': {k: sum(1 for x in lote if x['intencion'] == k) for k in INTENCIONES if any(x['intencion'] == k for x in lote)},
                      'anotadas': len(anotadas), 'nuevas': sum(1 for x in anotadas if x[0] == 'nueva'),
                      'avisos': len(problemas)})
    DATOS.mkdir(parents=True, exist_ok=True)
    HISTORIAL.write_text(json.dumps(historial, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(f'Hoja de respuestas: {salida.relative_to(RAIZ)} ({len(lote)} conversaciones)')
    for k in INTENCIONES:
        n = sum(1 for x in lote if x['intencion'] == k)
        if n:
            print(f"  {INTENCIONES[k]['icono']} {INTENCIONES[k]['nombre']}: {n}")
    if anotadas:
        n = sum(1 for x in anotadas if x[0] == 'nueva')
        print(f"En la libreta de clientas: {n} {'nueva' if n == 1 else 'nuevas'}, "
              f"{sum(1 for x in anotadas if x[0] != 'nueva')} ya estaban (" + ', '.join(n for _, n in anotadas[:8]) + ')')
    if movidas:
        print(f'{len(movidas)} capturas pasadas a comunidad/capturas/leidas/')
    if problemas:
        print('REVISAR ANTES DE ENTREGAR:')
        for p in problemas:
            print('  ' + p)


def burbuja_respuesta(texto, clase=''):
    """La respuesta con los [huecos] en amarillo para que Isabella los complete."""
    partes = re.split(r'(\[[^\]]+\])', texto or '')
    cuerpo = ''.join(f'<mark>{esc(p)}</mark>' if p.startswith('[') else esc(p) for p in partes)
    return f'<div class="resp {clase}" contenteditable="true" spellcheck="false">{cuerpo}</div>'


def pagina_hoja(lote, ahora, hay_precios):
    conteo = {k: sum(1 for x in lote if x['intencion'] == k) for k in INTENCIONES}
    tarjetas = []
    for x in lote:
        k = INTENCIONES[x['intencion']]
        quien = x.get('nombre') or ('@' + x['usuario'] if x.get('usuario') else 'Alguien')
        ini = ''.join(p[0] for p in quien.lstrip('@').split()[:2]).upper() or '?'
        red = x.get('red', '')
        etiqueta_red = {'instagram': 'IG', 'tiktok': 'TT', 'whatsapp': 'WA', 'facebook': 'FB'}.get(red, red[:2].upper())
        donde = {'comentario': 'en un comentario', 'mensaje': 'por mensaje', 'historia': 'respondiendo una historia'}.get(x.get('donde'), x.get('donde', ''))
        pub = f" · en «{esc(x['publicacion'])}»" if x.get('publicacion') else ''
        avisos = ''.join(f'<p class="aviso">⚠️ {esc(t)}</p>' for t in x.get('avisos', []))
        en_libreta = '<span class="libreta">📒 anotada en tu libreta</span>' if x.get('clienta') else ''
        if x['intencion'] == 'spam':
            tarjetas.append(f'<article class="tarjeta apagada" data-i="{x["intencion"]}"><div class="quien"><span class="av">{esc(ini)}</span>'
                            f'<div><b>{esc(quien)}</b> <span class="red {esc(red)}">{esc(etiqueta_red)}</span><small>{esc(donde)}</small></div></div>'
                            f'<div class="suyo">{esc(x.get("texto"))}</div><p class="nota">🚫 Mejor no responder{": " + esc(x["motivo"]) if x.get("motivo") else ""}.</p></article>')
            continue
        otra = (f'<details><summary>Otra forma de decirlo</summary>{burbuja_respuesta(x["otra"], "b")}'
                f'<button class="btn chico" data-copiar="b">Copiar esta</button></details>') if x.get('otra') else ''
        abrir = (f'<a class="btn principal" data-abrir href="{esc(x["enlace"])}" target="_blank" rel="noopener">💬 Copiar y abrir chat</a>'
                 if x.get('enlace') and x.get('donde') != 'comentario' else '')
        tarjetas.append(f'''<article class="tarjeta" data-i="{x["intencion"]}" style="--c:{k["color"]}">
  <span class="tipo">{k["icono"]} {esc(k["nombre"])}</span>
  <div class="quien"><span class="av">{esc(ini)}</span><div><b>{esc(quien)}</b> <span class="red {esc(red)}">{esc(etiqueta_red)}</span>
    <small>{esc('@' + x['usuario'] + ' · ' if x.get('usuario') and x.get('nombre') else '')}{esc(donde)}{pub}</small></div></div>
  <div class="suyo">{esc(x.get("texto"))}</div>
  {burbuja_respuesta(x.get("respuesta"))}
  {avisos}
  <div class="acciones">{abrir}<button class="btn" data-copiar="a">Copiar</button><button class="btn suave" data-listo>Listo ✓</button>{en_libreta}</div>
  {otra}
  {f'<p class="nota">💡 {esc(x["consejo"])}</p>' if x.get('consejo') else ''}
</article>''')
    chips = ''.join(f'<button class="filtro" data-f="{k}">{v["icono"]} {esc(v["nombre"])} · {conteo[k]}</button>'
                    for k, v in INTENCIONES.items() if conteo[k])
    responder = sum(1 for x in lote if x['intencion'] != 'spam')
    cerca = conteo['comprar'] + conteo['precio']
    frase = (f'Tienes <b>{responder} respuestas listas</b>' +
             (f', y <b>{cerca}</b> de esas personas están cerca de comprar' if cerca else '') + '. '
             'Toca «Copiar y abrir chat», pega y envía. Puedes cambiar cualquier palabra antes de copiar.')
    aviso_precios = '' if hay_precios else ('<p class="banda">Donde dice <mark>[precio]</mark> o algo en amarillo, '
                                            'complétalo tú antes de enviar. Si nos pasas tu lista de precios, '
                                            'el agente los pone solo.</p>')
    fecha = ahora.strftime('%d/%m/%Y %H:%M')
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Respuestas para tus clientas</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{{--fondo:#fbf5f1;--fondo-2:#f5ebe5;--papel:#fff;--tinta:#2b1a2c;--tinta-2:#5d4a5c;--tenue:#8f7d8c;--linea:#eadcd6;--rosa:#d64f8a;--rosa-suave:#fbe3ec;--rosa-osc:#a8326a;
--sombra:0 1px 2px rgba(60,30,50,.05),0 8px 24px -12px rgba(80,30,60,.18);--titulo:"Fraunces",Georgia,serif;--cuerpo:"Plus Jakarta Sans","Segoe UI",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root{{--fondo:#1a1219;--fondo-2:#231822;--papel:#2a1d29;--tinta:#f7ecf1;--tinta-2:#d9c6d2;--tenue:#a8939f;--linea:#3d2c3a;--rosa-suave:#4a2338}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--tinta);font:15px/1.5 var(--cuerpo);
background-image:radial-gradient(1000px 420px at 90% -10%,rgba(214,79,138,.10),transparent 60%)}}
main{{max-width:1180px;margin:0 auto;padding:36px 24px 80px}}
h1{{font:400 40px/1.1 var(--titulo);margin:0 0 8px;letter-spacing:-.02em}}h1 em{{color:var(--rosa)}}
.sub{{color:var(--tinta-2);max-width:640px;margin:0}}.fecha{{color:var(--tenue);font-size:13px;margin-bottom:6px}}
.banda{{background:#fff4d6;color:#6b4b00;border:1px solid #f0d58a;border-radius:14px;padding:10px 14px;margin:18px 0 0;font-size:14px}}
mark{{background:#ffe58a;color:#4a3500;border-radius:5px;padding:0 3px}}
.filtros{{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0}}
.filtro{{border:1px solid var(--linea);background:var(--papel);color:var(--tinta-2);border-radius:999px;padding:6px 13px;font:600 13px var(--cuerpo);cursor:pointer}}
.filtro.on{{background:var(--tinta);color:var(--fondo);border-color:var(--tinta)}}
.grilla{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}
.tarjeta{{background:var(--papel);border:1px solid var(--linea);border-radius:20px;padding:18px;box-shadow:var(--sombra);display:flex;flex-direction:column;gap:12px;transition:opacity .3s}}
.tarjeta.hecha{{opacity:.45}}.tarjeta.apagada{{opacity:.6;box-shadow:none}}
.tipo{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--c);background:color-mix(in srgb,var(--c) 13%,transparent);padding:4px 10px;border-radius:999px;width:fit-content}}
.quien{{display:flex;gap:10px;align-items:center}}.quien small{{display:block;color:var(--tenue);font-size:12.5px}}
.av{{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;color:#fff;font-weight:700;background:linear-gradient(135deg,#f29bb8,#d64f8a);flex:none}}
.red{{font-size:10.5px;font-weight:800;padding:2px 6px;border-radius:6px;color:#fff}}.red.instagram{{background:linear-gradient(45deg,#f09433,#dc2743,#bc1888)}}
.red.tiktok{{background:#111}}.red.whatsapp{{background:#25d366}}.red.facebook{{background:#1877f2}}
.suyo{{background:var(--fondo-2);border-radius:16px 16px 16px 4px;padding:10px 13px;font-size:14px;color:var(--tinta-2);white-space:pre-wrap}}
.resp{{background:var(--rosa-suave);border-radius:16px 16px 4px 16px;padding:11px 14px;font-size:14.5px;margin-left:22px;outline:none;white-space:pre-wrap}}
.resp:focus{{box-shadow:0 0 0 2px var(--rosa)}}
.acciones{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.btn{{border:1px solid var(--linea);background:var(--papel);border-radius:999px;padding:8px 14px;font:600 13.5px var(--cuerpo);color:var(--tinta);cursor:pointer;text-decoration:none}}
.btn.principal{{background:var(--rosa);color:#fff;border-color:transparent}}.btn.suave{{background:var(--rosa-suave);color:var(--rosa-osc);border-color:transparent}}
.btn.chico{{padding:5px 11px;font-size:12.5px;margin-top:8px}}
.libreta{{font-size:12px;color:var(--tenue);margin-left:auto}}
.aviso{{margin:0;color:#b03a37;font-size:13px;font-weight:600}}.nota{{margin:0;color:var(--tinta-2);font-size:13px}}
details summary{{cursor:pointer;color:var(--tenue);font-size:13px;font-weight:600}}details .resp{{margin-top:8px}}
.toast{{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--tinta);color:var(--fondo);padding:11px 18px;border-radius:999px;font-weight:600;opacity:0;transition:opacity .3s;pointer-events:none}}
.toast.on{{opacity:1}}
@media (max-width:640px){{main{{padding:24px 16px 60px}}h1{{font-size:32px}}.grilla{{grid-template-columns:1fr}}}}
</style></head><body><main>
<div class="fecha">{esc(fecha)} · {len(lote)} conversaciones</div>
<h1>Respuestas para <em>tus clientas</em></h1>
<p class="sub">{frase}</p>
{aviso_precios}
<div class="filtros"><button class="filtro on" data-f="todas">Todas · {len(lote)}</button>{chips}</div>
<div class="grilla">{''.join(tarjetas)}</div>
</main><div class="toast" id="toast"></div>
<script>
const toast=(t)=>{{const e=document.getElementById("toast");e.textContent=t;e.classList.add("on");clearTimeout(toast.t);toast.t=setTimeout(()=>e.classList.remove("on"),2000)}};
const copiar=async(el)=>{{try{{await navigator.clipboard.writeText(el.innerText.trim())}}catch(e){{const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand("copy");s.removeAllRanges()}}}};
document.querySelectorAll(".tarjeta").forEach((t)=>t.addEventListener("click",async(ev)=>{{
  const b=ev.target.closest("[data-copiar],[data-abrir],[data-listo]");if(!b)return;
  if(b.dataset.listo!==undefined){{t.classList.toggle("hecha");return}}
  const el=b.dataset.copiar==="b"?t.querySelector("details .resp"):t.querySelector(".resp");
  await copiar(el);toast(b.dataset.abrir!==undefined?"Copiado: pégalo en el chat 💕":"Respuesta copiada");
}}));
document.querySelectorAll(".filtro").forEach((f)=>f.onclick=()=>{{
  document.querySelectorAll(".filtro").forEach((x)=>x.classList.toggle("on",x===f));
  document.querySelectorAll(".tarjeta").forEach((t)=>t.hidden=f.dataset.f!=="todas"&&t.dataset.i!==f.dataset.f);
}});
</script></body></html>'''


# ---------- respuestas rápidas ----------

def cmd_rapidas(a):
    kit = leer_json(RAPIDAS, None)
    if not kit:
        sys.exit('No encontré comunidad/respuestas-rapidas.json')
    hay_precios = PRECIOS.exists()
    problemas = [f"{r['atajo']}: " + '; '.join(av) for r in kit['respuestas']
                 for av in [revisar_texto(r['texto'], hay_precios)] if av]
    RESPUESTAS.mkdir(parents=True, exist_ok=True)
    salida = RESPUESTAS / 'respuestas-rapidas.html'
    salida.write_text(pagina_rapidas(kit), encoding='utf-8')
    if COMPARTIDO.is_dir() and not a.sin_copia:
        (COMPARTIDO / 'comunidad').mkdir(exist_ok=True)
        shutil.copy(salida, COMPARTIDO / 'comunidad' / salida.name)
    print(f"Kit de respuestas rápidas: {salida.relative_to(RAIZ)} ({len(kit['respuestas'])} respuestas)")
    for p in problemas:
        print('REVISAR: ' + p)


def pagina_rapidas(kit):
    tarjetas = ''.join(f'''<article class="tarjeta"><div class="cab"><span class="atajo">{esc(r["atajo"])}</span><b>{esc(r["cuando"])}</b></div>
  {burbuja_respuesta(r["texto"])}<button class="btn" data-copiar>Copiar</button></article>''' for r in kit['respuestas'])
    pasos = ''.join(f'<li>{esc(p)}</li>' for p in kit.get('como_guardar', []))
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Respuestas rápidas</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{{--fondo:#fbf5f1;--fondo-2:#f5ebe5;--papel:#fff;--tinta:#2b1a2c;--tinta-2:#5d4a5c;--tenue:#8f7d8c;--linea:#eadcd6;--rosa:#d64f8a;--rosa-suave:#fbe3ec;
--sombra:0 1px 2px rgba(60,30,50,.05),0 8px 24px -12px rgba(80,30,60,.18);--titulo:"Fraunces",Georgia,serif;--cuerpo:"Plus Jakarta Sans","Segoe UI",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root{{--fondo:#1a1219;--fondo-2:#231822;--papel:#2a1d29;--tinta:#f7ecf1;--tinta-2:#d9c6d2;--tenue:#a8939f;--linea:#3d2c3a;--rosa-suave:#4a2338}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--fondo);color:var(--tinta);font:15px/1.5 var(--cuerpo)}}
main{{max-width:1100px;margin:0 auto;padding:36px 24px 80px}}h1{{font:400 40px/1.1 var(--titulo);margin:0 0 8px}}h1 em{{color:var(--rosa)}}
.sub{{color:var(--tinta-2);max-width:660px}}
.guia{{background:var(--papel);border:1px solid var(--linea);border-radius:20px;padding:16px 22px;margin:20px 0 26px;box-shadow:var(--sombra)}}
.guia h2{{font:600 19px var(--titulo);margin:0 0 6px}}.guia ol{{margin:0;padding-left:20px;color:var(--tinta-2)}}.guia li{{margin:4px 0}}
.grilla{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.tarjeta{{background:var(--papel);border:1px solid var(--linea);border-radius:20px;padding:18px;box-shadow:var(--sombra);display:flex;flex-direction:column;gap:12px}}
.cab{{display:flex;gap:10px;align-items:center}}.atajo{{font:700 14px ui-monospace,Menlo,monospace;background:var(--rosa);color:#fff;padding:4px 10px;border-radius:10px}}
.resp{{background:var(--rosa-suave);border-radius:16px;padding:11px 14px;font-size:14.5px;outline:none;white-space:pre-wrap;flex:1}}
mark{{background:#ffe58a;color:#4a3500;border-radius:5px;padding:0 3px}}
.btn{{align-self:flex-start;border:1px solid var(--linea);background:var(--papel);border-radius:999px;padding:7px 14px;font:600 13.5px var(--cuerpo);color:var(--tinta);cursor:pointer}}
.toast{{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--tinta);color:var(--fondo);padding:11px 18px;border-radius:999px;font-weight:600;opacity:0;transition:opacity .3s}}.toast.on{{opacity:1}}
@media (max-width:640px){{main{{padding:24px 16px 60px}}h1{{font-size:32px}}.grilla{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Tus <em>respuestas rápidas</em></h1>
<p class="sub">{esc(kit.get("intro", ""))}</p>
<div class="guia"><h2>Cómo guardarlas (una sola vez)</h2><ol>{pasos}</ol></div>
<div class="grilla">{tarjetas}</div>
</main><div class="toast" id="toast"></div>
<script>
document.querySelectorAll("[data-copiar]").forEach((b)=>b.onclick=async()=>{{
  const el=b.parentElement.querySelector(".resp");try{{await navigator.clipboard.writeText(el.innerText.trim())}}catch(e){{}}
  const t=document.getElementById("toast");t.textContent="Copiada";t.classList.add("on");setTimeout(()=>t.classList.remove("on"),1600)}});
</script></body></html>'''


# ---------- resumen ----------

def cmd_resumen(_):
    h = leer_json(HISTORIAL, [])
    if not h:
        print('Todavía no hay respuestas preparadas.')
        return
    total = sum(x['total'] for x in h)
    nuevas = sum(x.get('nuevas', 0) for x in h)
    inten = {}
    for x in h:
        for k, v in x.get('intenciones', {}).items():
            inten[k] = inten.get(k, 0) + v
    print(f'{len(h)} hojas, {total} conversaciones respondidas, {nuevas} clientas nuevas en la libreta. '
          f'Última: {h[-1]["fecha"]} ({h[-1]["hoja"]})')
    print('De qué: ' + ', '.join(f"{INTENCIONES.get(k, {}).get('nombre', k)} {v}" for k, v in sorted(inten.items(), key=lambda kv: -kv[1])))


def main():
    p = argparse.ArgumentParser(description='Agente de comunidad de Isabella')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('pendientes')
    h = sub.add_parser('hoja')
    h.add_argument('lote')
    h.add_argument('--sin-mover', action='store_true', help='no mover las capturas a leidas/')
    h.add_argument('--sin-copia', action='store_true', help='no copiar a la carpeta compartida')
    r = sub.add_parser('rapidas')
    r.add_argument('--sin-copia', action='store_true')
    sub.add_parser('resumen')
    a = p.parse_args()
    {'pendientes': cmd_pendientes, 'hoja': cmd_hoja, 'rapidas': cmd_rapidas, 'resumen': cmd_resumen}[a.cmd](a)


if __name__ == '__main__':
    main()
