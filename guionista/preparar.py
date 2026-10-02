#!/usr/bin/env python3
"""Guionista de Isabella: convierte un guion.json en lo que ella necesita para grabar.

    python3 guionista/preparar.py guiones/<slug>          (desde guionista/ o desde la raíz)

Crea en guionista/salida/<slug>/:
  hoja.html          la hoja de grabación: qué preparar, toma por toma qué decir y qué mostrar
  teleprompter.html  el texto grande que se desliza solo, para leer mientras graba
  caption.txt        el texto para publicar con sus hashtags

Solo usa Python estándar. Revisa también las reglas (sin precios, porcentajes, promesas
médicas ni de ingresos) y avisa si el guion está muy largo o el gancho muy lento.
"""
import base64
import html
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
VOZ = RAIZ / 'marca' / 'voz-isabella.md'

FORMATOS = {
    'grwm': 'Arréglate conmigo',
    'prueba': 'Lo probé',
    'tutorial': 'Tutorial',
    'en-mi-bolsa': 'Lo que hay en mi bolsa / mis favoritos',
    'opinion': 'Mi opinión honesta',
    'dia': 'Un día conmigo',
    'respuesta': 'Respondo un comentario',
    'historias': 'Historias (Stories)',
    'en-vivo': 'En vivo',
}
PLANOS = {
    'cerca': ('🙂', 'Cara de cerca'),
    'medio': ('🧍‍♀️', 'De la cintura para arriba'),
    'detalle': ('🔍', 'Detalle del producto'),
    'manos': ('✋', 'Tus manos aplicando'),
    'pantalla': ('📱', 'Captura o texto en pantalla'),
    'ambiente': ('🏠', 'El lugar, sin ti'),
}
AUDIOS = {
    'voz': 'Tu voz, hablando a cámara',
    'voz-en-off': 'Grabas sin hablar y luego pones tu voz encima',
    'tendencia': 'Un sonido de moda de la app (búscalo al publicar) + texto en pantalla',
    'musica-suave': 'Música suave de la app de fondo + texto en pantalla',
}
PALABRAS_POR_SEGUNDO = 2.8   # más que esto suena apurado


def reglas():
    """Las mismas palabras prohibidas que usa el planificador."""
    archivo = RAIZ / 'planificador' / 'planificar.py'
    spec = importlib.util.spec_from_file_location('planificar', archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PROHIBIDO


def e(t):
    return html.escape(str(t or ''))


def resaltar(t):
    """*palabra* sale resaltada; [completa: …] sale marcado para que Isabella lo llene."""
    t = e(t)
    t = re.sub(r'\*(.+?)\*', r'<mark>\1</mark>', t)
    return re.sub(r'\[completa:\s*(.+?)\]', r'<span class="completa">✍️ \1</span>', t)


def plano_de(toma):
    return PLANOS.get(toma.get('plano'), ('🎬', toma.get('plano') or 'Toma'))


def foto_producto(guion):
    prod = guion.get('producto') or {}
    if not prod.get('carpeta'):
        return None, None
    carpeta = RAIZ / prod['carpeta']
    datos = {}
    if (carpeta / 'datos.json').exists():
        datos = json.loads((carpeta / 'datos.json').read_text(encoding='utf-8'))
    for nombre in (datos.get('imagen'), 'producto.jpg', 'producto.png', 'producto.webp'):
        if nombre and (carpeta / nombre).exists():
            f = carpeta / nombre
            tipo = {'.png': 'png', '.webp': 'webp'}.get(f.suffix, 'jpeg')
            return datos, f'data:image/{tipo};base64,' + base64.b64encode(f.read_bytes()).decode()
    return datos, None


def revisar(guion):
    errores, avisos = [], []
    if guion.get('formato') not in FORMATOS:
        errores.append(f'"formato" debe ser uno de: {", ".join(FORMATOS)}')
    if guion.get('audio') and guion['audio'] not in AUDIOS:
        errores.append(f'"audio" debe ser uno de: {", ".join(AUDIOS)}')
    tomas = guion.get('tomas') or []
    if not tomas:
        errores.append('faltan "tomas"')
    for i, t in enumerate(tomas, 1):
        if not (t.get('dice') or t.get('texto_pantalla')):
            errores.append(f'toma {i}: necesita "dice" o "texto_pantalla"')
        if not t.get('segundos'):
            errores.append(f'toma {i}: falta "segundos"')
        if t.get('plano') and t['plano'] not in PLANOS:
            avisos.append(f'toma {i}: plano "{t["plano"]}" no es de la lista ({", ".join(PLANOS)})')
        palabras = len(re.findall(r'\w+', re.sub(r'\[completa:.*?\]', 'algo', t.get('dice') or '')))
        if t.get('segundos') and palabras / t['segundos'] > PALABRAS_POR_SEGUNDO:
            avisos.append(f'toma {i}: {palabras} palabras en {t["segundos"]} s suena apurado; '
                          f'acorta o dale {math.ceil(palabras / PALABRAS_POR_SEGUNDO)} s')
    if tomas:
        g = tomas[0]
        if (g.get('segundos') or 0) > 3:
            avisos.append('la primera toma (el gancho) dura más de 3 s; la gente decide en 2')
        if len(re.findall(r'\w+', g.get('dice') or '')) > 14:
            avisos.append('el gancho tiene más de 14 palabras; hazlo más corto')
    total = sum(t.get('segundos') or 0 for t in tomas)
    objetivo = guion.get('duracion_objetivo')
    if objetivo and total > objetivo * 1.25:
        avisos.append(f'las tomas suman {total} s y el objetivo era {objetivo} s')

    textos = [guion.get('titulo'), (guion.get('caption') or {}).get('texto')]
    textos += guion.get('ganchos_alternativos') or []
    for t in tomas:
        textos += [t.get('dice'), t.get('texto_pantalla'), t.get('muestra')]
    for texto in filter(None, textos):
        for patron, motivo in reglas():
            if patron.search(texto):
                errores.append(f'{motivo}: «{texto[:70]}»')
    return errores, avisos, total


def pendientes_de_voz():
    if not VOZ.exists():
        return None
    return len(re.findall(r'PENDIENTE', VOZ.read_text(encoding='utf-8')))


CSS = """
:root { --fondo:#fbf7f9; --tarjeta:#fff; --texto:#2a1f27; --suave:#7a6874; --linea:#ecdde5;
        --acento:#d63d7e; --marca:#ffe1ef; --completa:#fff3c4; }
@media (prefers-color-scheme: dark) { :root { --fondo:#17121a; --tarjeta:#221b26; --texto:#f4ecf1;
        --suave:#b6a4b0; --linea:#3a2e3f; --acento:#ff6fa8; --marca:#5a2340; --completa:#4d4113; } }
* { box-sizing:border-box; } body { margin:0; background:var(--fondo); color:var(--texto);
  font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:760px; margin:0 auto; padding:20px 16px 48px; }
h1 { font-size:26px; line-height:1.2; margin:4px 0 6px; } h2 { font-size:18px; margin:28px 0 10px; }
.kicker { color:var(--acento); font-weight:700; text-transform:uppercase; letter-spacing:.06em; font-size:13px; }
.meta { color:var(--suave); font-size:14px; display:flex; flex-wrap:wrap; gap:6px 14px; }
.producto { display:flex; gap:14px; align-items:center; background:var(--tarjeta); border:1px solid var(--linea);
  border-radius:14px; padding:10px; margin-top:16px; } .producto img { width:72px; height:72px; object-fit:cover; border-radius:10px; }
.lista { list-style:none; padding:0; margin:0; } .lista li { padding:6px 0; border-bottom:1px solid var(--linea); }
.lista label { display:flex; gap:10px; align-items:flex-start; cursor:pointer; }
input[type=checkbox] { width:20px; height:20px; accent-color:var(--acento); margin-top:2px; flex:none; }
.toma { background:var(--tarjeta); border:1px solid var(--linea); border-radius:16px; padding:14px 16px; margin-bottom:12px; }
.toma .cabeza { display:flex; justify-content:space-between; align-items:center; gap:8px; color:var(--suave); font-size:14px; }
.toma .num { background:var(--acento); color:#fff; border-radius:999px; padding:2px 10px; font-weight:700; }
.toma.gancho { border:2px solid var(--acento); }
.dice { font-size:20px; font-weight:600; margin:10px 0 6px; } .dice::before { content:"🗣️ "; }
.fila { font-size:15px; margin-top:4px; } .fila b { color:var(--suave); font-weight:600; }
mark { background:var(--marca); color:inherit; padding:0 3px; border-radius:4px; }
.completa { background:var(--completa); border-radius:4px; padding:0 4px; font-style:italic; }
.aviso { background:var(--completa); border-radius:12px; padding:10px 14px; font-size:15px; margin-top:16px; }
pre { white-space:pre-wrap; background:var(--tarjeta); border:1px solid var(--linea); border-radius:14px; padding:14px;
  font:15px/1.5 system-ui,sans-serif; margin:0; }
button, a.boton { background:var(--acento); color:#fff; border:0; border-radius:999px; padding:10px 18px; font-size:15px;
  font-weight:600; cursor:pointer; text-decoration:none; display:inline-block; margin-top:10px; }
@media print { button, a.boton { display:none; } .toma { break-inside:avoid; } }
"""


def hoja_html(guion, slug, total, faltan_voz):
    datos, foto = foto_producto(guion)
    tomas = guion['tomas']
    partes = [f'<div class="kicker">{e(FORMATOS.get(guion.get("formato"), ""))}</div>',
              f'<h1>{resaltar(guion.get("titulo"))}</h1>',
              '<div class="meta">'
              f'<span>⏱️ {total} s en total</span><span>🎬 {len(tomas)} tomas</span>'
              f'<span>📲 {e(guion.get("red") or "Reels / TikTok")}</span>'
              f'<span>🎵 {e(AUDIOS.get(guion.get("audio"), guion.get("audio") or "Tu voz"))}</span></div>']
    if guion.get('por_que'):
        partes.append(f'<p>{resaltar(guion["por_que"])}</p>')
    if foto or datos:
        nombre = (datos or {}).get('nombre') or (guion.get('producto') or {}).get('nombre', '')
        img = f'<img src="{foto}" alt="">' if foto else ''
        partes.append(f'<div class="producto">{img}<div><b>{e(nombre)}</b><br>'
                      f'<span class="meta">Tenlo a la mano, limpio y con la etiqueta hacia la cámara.</span></div></div>')
    if any('[completa:' in (t.get('dice') or '') for t in tomas):
        partes.append('<div class="aviso">✍️ Lo marcado en amarillo lo dices con tus palabras: es algo tuyo '
                      'que el guion no puede inventar.</div>')

    preparar = guion.get('preparar') or []
    if preparar:
        partes.append('<h2>Antes de grabar</h2><ul class="lista">' + ''.join(
            f'<li><label><input type="checkbox"><span>{resaltar(p)}</span></label></li>' for p in preparar) + '</ul>')

    partes.append('<h2>Toma por toma</h2>')
    for i, t in enumerate(tomas, 1):
        icono, plano = plano_de(t)
        filas = []
        if t.get('muestra'):
            filas.append(f'<div class="fila"><b>Muestra:</b> {resaltar(t["muestra"])}</div>')
        if t.get('texto_pantalla'):
            filas.append(f'<div class="fila"><b>Texto en pantalla:</b> {resaltar(t["texto_pantalla"])}</div>')
        if t.get('consejo'):
            filas.append(f'<div class="fila"><b>Tip:</b> {resaltar(t["consejo"])}</div>')
        dice = f'<div class="dice">{resaltar(t["dice"])}</div>' if t.get('dice') else ''
        etiqueta = ' · el gancho' if i == 1 else ''
        partes.append(f'<div class="toma{" gancho" if i == 1 else ""}"><div class="cabeza">'
                      f'<span class="num">{i}{etiqueta}</span><span>{icono} {e(plano)} · {t.get("segundos")} s</span></div>'
                      f'{dice}{"".join(filas)}</div>')

    alternativos = guion.get('ganchos_alternativos') or []
    if alternativos:
        partes.append('<h2>Otros ganchos para probar</h2><p class="meta">Si grabas el mismo video otro día, '
                      'cambia solo la primera frase y mira cuál funciona mejor.</p><ul class="lista">' +
                      ''.join(f'<li>{resaltar(g)}</li>' for g in alternativos) + '</ul>')

    cap = guion.get('caption') or {}
    if cap.get('texto'):
        texto = caption_texto(guion)
        partes.append('<h2>Para publicar</h2>'
                      f'<pre id="caption">{e(texto)}</pre>'
                      '<button onclick="navigator.clipboard.writeText(document.getElementById(\'caption\').innerText)'
                      '.then(()=>{this.textContent=\'¡Copiado!\'})">Copiar texto</button>')
    partes.append('<p><a class="boton" href="teleprompter.html">Abrir el teleprompter</a></p>')
    if faltan_voz:
        partes.append(f'<p class="meta">Nota: la ficha de tu voz tiene {faltan_voz} datos pendientes; '
                      'con ellos los guiones suenan más a ti.</p>')
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Guion · {e(re.sub(r"[*]", "", guion.get("titulo", slug)))}</title><style>{CSS}</style></head>'
            f'<body><main>{"".join(partes)}</main></body></html>')


def teleprompter_html(guion):
    bloques = []
    for i, t in enumerate(guion['tomas'], 1):
        icono, plano = plano_de(t)
        texto = resaltar(t.get('dice') or f'({t.get("texto_pantalla")})')
        bloques.append(f'<section><div class="plano">{i} · {icono} {e(plano)} · {t.get("segundos")} s</div>'
                       f'<p>{texto}</p></section>')
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>Teleprompter</title><style>
* {{ box-sizing:border-box; }} html,body {{ margin:0; height:100%; background:#000; color:#fff;
  font-family:system-ui,-apple-system,sans-serif; overflow:hidden; }}
#rollo {{ position:absolute; inset:0; overflow-y:scroll; padding:45vh 7vw 80vh; scrollbar-width:none; }}
#rollo::-webkit-scrollbar {{ display:none; }}
body.espejo #rollo {{ transform:scaleX(-1); }}
section {{ margin-bottom:9vh; }} p {{ font-size:var(--tam,44px); line-height:1.35; font-weight:600; margin:.2em 0; }}
.plano {{ color:#ff8fbd; font-size:16px; letter-spacing:.04em; }}
mark {{ background:none; color:#ffd54d; }} .completa {{ color:#ffd54d; font-style:italic; }}
#guia {{ position:fixed; left:0; right:0; top:45vh; height:2px; background:rgba(255,111,168,.6); pointer-events:none; }}
#mandos {{ position:fixed; left:0; right:0; bottom:0; display:flex; flex-wrap:wrap; gap:8px; justify-content:center;
  align-items:center; padding:10px 12px 18px; background:linear-gradient(transparent,#000 40%); font-size:14px; }}
button {{ background:#ff4f93; color:#fff; border:0; border-radius:999px; padding:12px 18px; font-size:16px; font-weight:700; }}
button.sec {{ background:#333; }} label {{ display:flex; gap:6px; align-items:center; color:#ccc; }}
input[type=range] {{ width:110px; accent-color:#ff4f93; }}
</style></head><body>
<div id="rollo">{''.join(bloques)}<p style="color:#888">✨ ¡Listo! ✨</p></div>
<div id="guia"></div>
<div id="mandos">
  <button id="play">▶ Empezar</button>
  <button class="sec" id="inicio">⟲</button>
  <label>Velocidad <input id="vel" type="range" min="10" max="140" value="45"></label>
  <label>Letra <input id="tam" type="range" min="26" max="80" value="44"></label>
  <button class="sec" id="espejo">Espejo</button>
</div>
<script>
const rollo = document.getElementById('rollo'), play = document.getElementById('play');
let andando = false, ultimo = 0, resto = 0;
function paso(t) {{
  if (!andando) return;
  const dt = ultimo ? (t - ultimo) / 1000 : 0; ultimo = t;
  resto += dt * Number(document.getElementById('vel').value);
  const px = Math.floor(resto); resto -= px; rollo.scrollTop += px;
  if (rollo.scrollTop + rollo.clientHeight >= rollo.scrollHeight - 2) parar();
  requestAnimationFrame(paso);
}}
function arrancar() {{ andando = true; ultimo = 0; play.textContent = '❚❚ Pausa'; requestAnimationFrame(paso); }}
function parar() {{ andando = false; play.textContent = '▶ Seguir'; }}
play.onclick = () => andando ? parar() : arrancar();
rollo.onclick = () => andando ? parar() : arrancar();
document.getElementById('inicio').onclick = () => {{ parar(); rollo.scrollTop = 0; play.textContent = '▶ Empezar'; }};
document.getElementById('tam').oninput = (ev) => document.body.style.setProperty('--tam', ev.target.value + 'px');
document.getElementById('espejo').onclick = () => document.body.classList.toggle('espejo');
document.addEventListener('keydown', (ev) => {{ if (ev.code === 'Space') {{ ev.preventDefault(); andando ? parar() : arrancar(); }} }});
</script></body></html>"""


def caption_texto(guion):
    cap = guion.get('caption') or {}
    tags = ' '.join('#' + h.lstrip('#') for h in cap.get('hashtags') or [])
    return (cap.get('texto') or '').strip() + ('\n\n' + tags if tags else '')


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    carpeta = Path(sys.argv[1])
    if not carpeta.is_absolute() and not carpeta.exists():
        carpeta = AQUI / carpeta
    archivo = carpeta / 'guion.json'
    if not archivo.exists():
        print(f'No encuentro {archivo}')
        sys.exit(1)
    guion = json.loads(archivo.read_text(encoding='utf-8'))
    slug = carpeta.resolve().name

    errores, avisos, total = revisar(guion)
    for a in avisos:
        print('Aviso:', a)
    if errores:
        for x in errores:
            print('Error:', x)
        print('Corrige el guion y vuelve a correrlo.')
        sys.exit(1)

    faltan_voz = pendientes_de_voz()
    salida = AQUI / 'salida' / slug
    salida.mkdir(parents=True, exist_ok=True)
    (salida / 'hoja.html').write_text(hoja_html(guion, slug, total, faltan_voz), encoding='utf-8')
    (salida / 'teleprompter.html').write_text(teleprompter_html(guion), encoding='utf-8')
    (salida / 'caption.txt').write_text(caption_texto(guion) + '\n', encoding='utf-8')
    completar = sum('[completa:' in (t.get('dice') or '') for t in guion['tomas'])
    print(f'Listo ({len(guion["tomas"])} tomas, {total} s, {len(avisos)} avisos). Carpeta: {salida}')
    print('  hoja.html · teleprompter.html · caption.txt')
    if completar:
        print(f'  {completar} tomas tienen partes [completa: …] que Isabella dice con sus palabras')
    if faltan_voz:
        print(f'  La ficha marca/voz-isabella.md tiene {faltan_voz} datos PENDIENTE')


if __name__ == '__main__':
    main()
