#!/usr/bin/env python3
"""Kit para sumar socias al equipo de Isabella: a quién le interesa, qué decirle y cómo acompañar
a las nuevas en su primer mes. Sin prometer dinero, nunca.

Uso (desde la carpeta del proyecto):
  python3 equipo/socias.py agregar --nombre "Paola Ríos" --usuario pao.rios --red instagram \\
      --nota "Comentó que quiere vender Farmasi"         # una persona interesada
  python3 equipo/socias.py paso "Paola" explicada         # interesada → explicada → se-unio → primera-venta → activa (o pausa)
  python3 equipo/socias.py hoy                            # a quién escribirle hoy, con el mensaje listo
  python3 equipo/socias.py lista
  python3 equipo/socias.py presentacion                   # 6 imágenes para mandar por WhatsApp o subir como carrusel
  python3 equipo/socias.py mensajes                       # hoja de mensajes para invitar (copiar con un toque)
  python3 equipo/socias.py guia "Paola"                   # guía de bienvenida de 30 días para una socia nueva
  python3 equipo/socias.py falta                          # lo que Isabella tiene que completar en negocio.json
  python3 equipo/socias.py demo                           # ejemplo en equipo/salida/ejemplo/ (no toca los datos)

Las personas quedan en equipo/datos/socias.json, solo en esta computadora.
Solo librería estándar (las imágenes salen con Chromium si está playwright).
"""
import argparse
import datetime
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / 'herramientas'))
import rutas  # noqa: E402  (node y ffmpeg que deja herramientas/instalar_videos.py)
rutas.preparar()
NEGOCIO = AQUI / 'negocio.json'
DATOS = AQUI / 'datos'
SOCIAS = DATOS / 'socias.json'
SALIDA = AQUI / 'salida'
COMPARTIDO = Path('/mnt/project-files')

ETAPAS = [('interesada', 'Le interesa', '💬'), ('explicada', 'Ya le expliqué', '📋'), ('se-unio', 'Se unió', '🎉'),
          ('primera-venta', 'Primera venta', '🛍️'), ('activa', 'Activa', '💖'), ('pausa', 'En pausa', '🌙')]
ID_ETAPAS = [x[0] for x in ETAPAS]
MAX_INSISTIR = 2
# Acompañamiento de una socia nueva: día después de unirse → qué hacer y qué decirle
BIENVENIDA = [
    (0, 'Bienvenida', '¡Bienvenida al equipo, {n}! 🎉 Estoy feliz de que empecemos juntas. Te mando tu guía de los primeros 30 días: '
                      'vamos paso a paso y a tu ritmo. Cualquier duda, me escribes.'),
    (3, 'Primeros pasos', '¡Hola, {n}! ¿Cómo vas con los primeros pasos? ¿Ya elegiste tus 3 productos favoritos? '
                          'Si quieres, hacemos una llamadita de 10 minutos y armamos tu lista juntas.'),
    (7, 'Primera semana', '¡{n}, ya cumpliste una semana! 💪 Cuéntame qué tal tus primeros mensajes. '
                          '¿Te ayudo a preparar tu primera publicación?'),
    (14, 'Mitad del mes', '¡Hola, {n}! ¿Cómo te sientes? Revisemos juntas qué te está funcionando y qué cambiamos. '
                          '¿Tienes a alguien que preguntó y no volvió a escribir? Te paso el mensaje para retomarlo.'),
    (30, 'Primer mes', '¡{n}, cumpliste tu primer mes! 🥳 Gracias por tu esfuerzo. ¿Nos sentamos un ratito a ver '
                       'qué aprendiste y qué quieres lograr el próximo mes?'),
]
GUIA = [
    ('Día 1', ['Únete con mi enlace y entra al grupo del equipo', 'Pon tu foto y una frase en tu perfil de redes',
               'Guarda en tu celular las respuestas rápidas (/info, /precio, /pedir)']),
    ('Días 2 y 3', ['Elige tus 3 productos favoritos y úsalos', 'Escribe una lista de 20 personas: amigas, familia, compañeras',
                    'Mira cómo publico yo y elige 2 ideas que te gusten']),
    ('Semana 1', ['Cuenta en una historia que empezaste y por qué', 'Escríbele a 5 personas de tu lista contándoles de un producto, sin presionar',
                  'Anota a cada persona que te pregunte algo']),
    ('Semana 2', ['Cierra tu primera venta (te ayudo a responder)', 'Publica 2 veces mostrando cómo usas tus productos',
                  'Escríbele otra vez a quien preguntó y no volvió']),
    ('Semana 3', ['Publica 3 veces: un tip, un producto y algo tuyo', 'Pregúntale a tu primera clienta cómo le fue',
                  'Suma 10 personas más a tu lista']),
    ('Semana 4', ['Revisamos juntas el mes: qué funcionó y qué no', 'Elige tu meta del próximo mes (ventas o clientas nuevas)',
                  'Ofrécele a tu primera clienta volver a comprar']),
]


def hoy():
    return datetime.date.today()


def sin_tildes(t):
    t = unicodedata.normalize('NFD', str(t or '').lower())
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn')


def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def e(t):
    return html.escape(str(t if t is not None else ''))


def falta(v):
    return not v or '[' in str(v)


def negocio():
    return leer_json(NEGOCIO, {}) or {}


def firma():
    try:
        spec = importlib.util.spec_from_file_location('libreta', RAIZ / 'clientas' / 'libreta.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.voz()['firma']
    except Exception:  # noqa: BLE001
        return 'Isabella'


def revisar(texto):
    """Lo mismo que revisa el agente de comunidad: nada de prometer dinero ni resultados."""
    try:
        spec = importlib.util.spec_from_file_location('responder', RAIZ / 'comunidad' / 'responder.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.revisar_texto(texto, True)
    except Exception:  # noqa: BLE001
        return ['promete dinero'] if re.search(r'ganar(?:ás|as)? (?:dinero|\$)|ingresos? (?:extra|seguros?)', texto, re.I) else []


# ---------- las personas ----------

def cargar(archivo=None):
    return leer_json(archivo or SOCIAS, {'personas': []}) or {'personas': []}


def guardar(datos, archivo=None):
    archivo = Path(archivo or SOCIAS)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    tmp = archivo.with_suffix('.tmp')
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(archivo)


def buscar(datos, quien):
    q = sin_tildes(quien).lstrip('@')
    for p in datos['personas']:
        if q in (sin_tildes(p.get('usuario')), re.sub(r'\D', '', p.get('telefono') or '') or '-'):
            return p
    exactas = [p for p in datos['personas'] if sin_tildes(p['nombre']) == q]
    parecidas = [p for p in datos['personas'] if q and q in sin_tildes(p['nombre'])]
    return (exactas or (parecidas if len(parecidas) == 1 else [None]))[0]


def agregar(datos, campos, nota=None):
    p = None
    for clave in ('usuario', 'telefono', 'nombre'):
        if campos.get(clave):
            p = buscar(datos, campos[clave])
            if p:
                break
    t = hoy().isoformat()
    if not p:
        if not (campos.get('nombre') or campos.get('usuario')):
            raise ValueError('Falta el nombre o el usuario.')
        p = {'id': f"s{max([int(x['id'][1:]) for x in datos['personas']] + [0]) + 1}",
             'nombre': campos.get('nombre') or '@' + campos['usuario'].lstrip('@'), 'etapa': 'interesada',
             'desde': t, 'ultimo': t, 'insistir': 0, 'historial': []}
        datos['personas'].append(p)
        p['historial'].append({'fecha': t, 'texto': 'Le interesa el negocio' + (f" (por {campos['origen']})" if campos.get('origen') else '')})
    for k in ('usuario', 'red', 'telefono', 'origen', 'ciudad'):
        if campos.get(k):
            p[k] = campos[k].lstrip('@') if k == 'usuario' else campos[k]
    if nota:
        p['historial'].append({'fecha': t, 'texto': nota})
        p['ultimo'] = t
    return p


def mover(p, etapa, cuando=None):
    if etapa not in ID_ETAPAS:
        raise ValueError(f'Paso desconocido: {etapa}. Usa: {", ".join(ID_ETAPAS)}')
    cuando = cuando or hoy().isoformat()
    p['etapa'], p['ultimo'], p['insistir'] = etapa, cuando, 0
    if etapa == 'se-unio':
        p['unio'] = cuando
    p['historial'].append({'fecha': cuando, 'texto': 'Pasó a «' + dict((a, b) for a, b, _ in ETAPAS)[etapa] + '»'})


def chat(p, texto):
    tel = re.sub(r'\D', '', p.get('telefono') or '')
    if tel:
        return f'https://wa.me/{tel}?text={quote(texto)}'
    u = (p.get('usuario') or '').lstrip('@')
    if not u:
        return ''
    return {'tiktok': f'https://www.tiktok.com/@{u}', 'facebook': f'https://m.me/{u}'}.get(p.get('red'), f'https://ig.me/m/{u}')


def tareas(datos, dia=None):
    dia = dia or hoy()
    neg = negocio()
    sale = []
    for p in datos['personas']:
        n = p['nombre'].lstrip('@').split()[0].capitalize()
        ultimo = datetime.date.fromisoformat(p['ultimo'])
        dias = (dia - ultimo).days
        hechas = set(p.get('hechas', []))
        if p['etapa'] == 'interesada' and dias >= 1 and p.get('insistir', 0) < MAX_INSISTIR:
            texto = (f'¡Hola, {n}! 😊 Como te interesó Farmasi, te mando cómo funciona en unas imágenes cortitas. '
                     'Míralas con calma y me cuentas qué te parece, sin compromiso.')
            sale.append({'id': f"explicar:{p['id']}:{p['ultimo']}", 'quien': p, 'que': 'Mándale la presentación',
                         'texto': texto, 'urgencia': 2 if dias > 2 else 1})
        elif p['etapa'] == 'explicada' and dias >= 3 and p.get('insistir', 0) < MAX_INSISTIR:
            texto = (f'¡Hola, {n}! ¿Pudiste ver lo que te mandé? Si te quedó alguna duda, la vemos en una llamadita '
                     'de 10 minutos. Y si ahora no es el momento, también está perfecto 🤍')
            sale.append({'id': f"seguir:{p['id']}:{p['ultimo']}", 'quien': p, 'que': 'Pregúntale si le quedó alguna duda',
                         'texto': texto, 'urgencia': 2})
        elif p['etapa'] in ('se-unio', 'primera-venta') and p.get('unio'):
            desde = (dia - datetime.date.fromisoformat(p['unio'])).days
            for d, que, plantilla in BIENVENIDA:
                clave = f"bienvenida:{p['id']}:{d}"
                if desde >= d and clave not in hechas and desde - d <= 6:
                    texto = plantilla.format(n=n)
                    if d == 0 and not falta(neg.get('grupo_equipo')):
                        texto += f" Aquí está el grupo del equipo: {neg['grupo_equipo']}"
                    sale.append({'id': clave, 'quien': p, 'que': f'Acompáñala: {que.lower()}', 'texto': texto,
                                 'urgencia': 3 if d == 0 else 2})
                    break
    for t in sale:
        t['enlace'] = chat(t['quien'], t['texto'])
    return sorted(sale, key=lambda t: -t['urgencia'])


def hecho(datos, tid):
    tipo, pid = tid.split(':')[:2]
    p = next((x for x in datos['personas'] if x['id'] == pid), None)
    if not p:
        raise ValueError(f'No encontré la tarea {tid}')
    if tipo == 'bienvenida':
        p.setdefault('hechas', []).append(tid)
    else:
        p['insistir'] = p.get('insistir', 0) + 1
        p['ultimo'] = hoy().isoformat()
        if p['insistir'] >= MAX_INSISTIR and tipo == 'seguir':
            mover(p, 'pausa')
        if tipo == 'explicar':
            mover(p, 'explicada')
    p['historial'].append({'fecha': hoy().isoformat(), 'texto': 'Le escribí'})


# ---------- la presentación (6 imágenes) ----------

def diapositivas(neg, quien):
    pendiente = lambda v, que: f'<span class="hueco">[completa: {e(que)}]</span>' if falta(v) else e(v)
    lista = lambda xs: ''.join(f'<li><span>{i}</span>{e(x)}</li>' for i, x in enumerate(xs, 1))
    return [
        ('portada', f'<div class="chico">Farmasi · con {e(quien)}</div><h1>¿Y si empiezas tu propio <em>negocio de belleza</em>?</h1>'
                    '<p class="sub">Te cuento cómo funciona en 6 imágenes. Sin compromiso.</p>'),
        ('que', f'<div class="chico">Qué es Farmasi</div><h2>Belleza que se recomienda</h2><p class="grande">{e(neg.get("que_es"))}</p>'),
        ('como', f'<div class="chico">Cómo funciona</div><h2>A tu manera, desde tu celular</h2><ol>{lista(neg.get("como_se_gana", []))}</ol>'),
        ('empezar', f'<div class="chico">Para empezar</div><h2>Lo que necesitas</h2>'
                    f'<p class="grande">{pendiente(neg.get("como_empezar"), "qué hace falta para unirse")}</p>'
                    f'<p class="grande">{pendiente(neg.get("beneficio_socia"), "qué recibe como socia")}</p>'),
        ('conmigo', f'<div class="chico">Lo que te doy yo</div><h2>No empiezas sola</h2><ol>{lista(neg.get("lo_que_te_doy", []))}</ol>'),
        ('verdad', f'<div class="chico">Te lo digo claro</div><h2>Lo que sí es verdad</h2><p class="grande">{e(neg.get("aviso"))}</p>'
                   '<p class="cta">¿Te cuento más? Escríbeme 💬</p>'),
    ]


def pagina_presentacion(neg, quien):
    hojas = diapositivas(neg, quien)
    slides = ''.join(f'<div class="marco"><section class="slide {k}"><div class="num">{i:02d} / {len(hojas):02d}</div>{c}'
                     f'<div class="firma">{e(quien)}</div></section></div>' for i, (k, c) in enumerate(hojas, 1))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Emprende conmigo</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant:ital,wght@0,500;0,600;1,500&family=Jost:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{ --tinta:#2b2321; --hueso:#f6f1ea; --rosa:#9e4f5c; --champan:#c9a66b; --gris:#7b6f6a;
  --serif:"Cormorant","Didot","Bodoni 72",Georgia,"Liberation Serif",serif; --sans:"Jost","Avenir Next","Helvetica Neue",Arial,"Liberation Sans",sans-serif; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#e9e1d8; font-family:var(--sans); color:var(--tinta); }}
.todo {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:18px; padding:20px 16px 50px; max-width:1200px; margin:auto; }}
.marco {{ aspect-ratio:4/5; position:relative; overflow:hidden; border-radius:14px; box-shadow:0 14px 34px rgba(60,40,30,.18); }}
.slide {{ width:1080px; height:1350px; position:absolute; top:0; left:0; transform-origin:0 0; padding:110px 100px; display:flex; flex-direction:column; justify-content:center;
  background:radial-gradient(90% 50% at 100% 0%, #f2ddd5 0%, rgba(242,221,213,0) 70%), var(--hueso); }}
.slide.portada, .slide.verdad {{ background:var(--tinta); color:var(--hueso); }}
body.foto {{ background:none; }} body.foto .todo {{ display:block; padding:0; }} body.foto .marco {{ width:1080px; height:1350px; border-radius:0; box-shadow:none; }}
.num {{ position:absolute; top:70px; right:100px; font-size:24px; letter-spacing:.3em; color:var(--champan); }}
.chico {{ font-size:28px; letter-spacing:.34em; text-transform:uppercase; color:var(--rosa); margin-bottom:30px; }}
.portada .chico, .verdad .chico {{ color:var(--champan); }}
h1 {{ font-family:var(--serif); font-weight:500; font-size:124px; line-height:.98; }}
h1 em {{ color:#e9b8b0; }}
h2 {{ font-family:var(--serif); font-weight:600; font-size:96px; line-height:1; margin-bottom:46px; }}
.sub {{ font-size:38px; font-weight:300; margin-top:40px; color:#d9cbc0; }}
.grande {{ font-size:42px; line-height:1.4; font-weight:300; margin-bottom:26px; }}
ol {{ list-style:none; }} ol li {{ display:flex; gap:30px; align-items:flex-start; font-size:40px; line-height:1.35; font-weight:300; margin-bottom:36px; }}
ol li span {{ flex:0 0 76px; height:76px; border-radius:50%; background:var(--rosa); color:#fff; display:grid; place-items:center; font-family:var(--serif); font-size:42px; font-weight:600; }}
.hueco {{ background:#fff3cd; color:#7a5a00; padding:2px 10px; border-radius:8px; }}
.cta {{ font-family:var(--serif); font-style:italic; font-size:64px; color:#e9b8b0; margin-top:40px; }}
.firma {{ position:absolute; bottom:70px; left:100px; font-family:var(--serif); font-style:italic; font-size:44px; color:var(--rosa); }}
.portada .firma, .verdad .firma {{ color:var(--champan); }}
</style></head><body><div class="todo">{slides}</div>
<script>(function(){{ var f=/[?&]foto\\b/.test(location.search); if(f) document.body.classList.add('foto');
function a(){{ document.querySelectorAll('.marco').forEach(function(m){{ m.firstElementChild.style.transform = f ? 'none' : 'scale(' + (m.clientWidth/1080) + ')'; }}); }}
a(); addEventListener('resize', a); }})();</script></body></html>'''


def fotos(html_archivo, selector, ancho, alto):
    if not shutil.which('node'):
        return []
    try:
        r = subprocess.run(['node', str(AQUI / 'fotos.cjs'), str(html_archivo), selector, str(ancho), str(alto)],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [Path(x) for x in r.stdout.splitlines() if x.strip()] if r.returncode == 0 else []


# ---------- los mensajes para invitar ----------

def plantillas(neg, quien):
    enlace = neg.get('enlace_unirse') if not falta(neg.get('enlace_unirse')) else '[tu enlace]'
    return [
        ('Preguntó cómo vender Farmasi', '¡Qué lindo que te interese! 🤝 Te cuento cómo funciona y qué hace falta para empezar, sin compromiso. '
         'Te aviso desde ya: lo que se gana depende del trabajo de cada una, así que no te voy a prometer cifras. '
         '¿Te mando la info por aquí o prefieres una llamadita?'),
        ('Clienta fiel que ama los productos', '¡Hola, [nombre]! Como te encantan los productos, se me ocurrió contarte algo: '
         'también puedes recomendarlos tú y tener tu propio negocio de belleza. Si te da curiosidad, te cuento cómo funciona, sin compromiso 💕'),
        ('Alguien que comentó "yo también quiero"', '¡Hola, [nombre]! Vi tu comentario 🥰 ¿Te cuento cómo empecé yo y cómo funciona? '
         'Sin presión: tú decides si es para ti.'),
        ('Después de mandar la presentación', '¿Qué te pareció? Cualquier duda me la preguntas, de verdad. '
         'Si quieres, hacemos una llamadita de 10 minutos y te cuento cómo es mi día con Farmasi.'),
        ('Ya decidió unirse', f'¡Qué alegría! 🎉 Este es mi enlace para que te unas a mi equipo: {enlace}. '
         'Cuando termines me avisas y te mando tu guía de los primeros 30 días. Vamos juntas.'),
        ('Ahora no es el momento', 'Te entiendo perfecto 🤍 Si más adelante te da curiosidad, aquí estoy. '
         'Y mientras, sigo contándote de los productos que te gustan.'),
    ]


def pagina_mensajes(neg, quien):
    filas = []
    for i, (cuando, texto) in enumerate(plantillas(neg, quien)):
        avisos = revisar(texto)
        filas.append(f'<div class="msg"><h3>{e(cuando)}</h3><p id="m{i}">{e(texto)}</p>'
                     + (f'<p class="aviso">Revisar: {e("; ".join(avisos))}</p>' if avisos else '')
                     + f'<button onclick="copiar({i},this)">Copiar</button></div>')
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mensajes para invitar</title><style>
body {{ margin:0; background:#f6f1ea; color:#2b2321; font-family:"Avenir Next","Helvetica Neue",Arial,sans-serif; }}
main {{ max-width:680px; margin:auto; padding:24px 16px 50px; }}
h1 {{ font-family:Georgia,serif; font-weight:600; font-size:30px; margin:0 0 6px; }} .nota {{ color:#7b6f6a; font-size:15px; line-height:1.5; }}
.msg {{ background:#fff; border-radius:16px; padding:16px 18px; margin-top:14px; box-shadow:0 8px 22px rgba(90,60,40,.07); }}
.msg h3 {{ margin:0 0 8px; font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:#9e4f5c; }}
.msg p {{ margin:0 0 10px; font-size:16px; line-height:1.5; }} .aviso {{ background:#fff3cd; padding:6px 10px; border-radius:8px; font-size:14px; }}
button {{ border:0; border-radius:99px; padding:9px 16px; background:#9e4f5c; color:#fff; font-size:14px; cursor:pointer; }}
</style></head><body><main><h1>Mensajes para invitar</h1>
<p class="nota">Cámbiales lo que quieras para que suenen a ti. Lo que está entre [corchetes] lo completas tú. Nunca prometas cuánto se gana.</p>
{''.join(filas)}</main><script>
function copiar(i,b){{ var t=document.getElementById('m'+i).innerText; (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){{b.textContent='Copiado ✓';}},function(){{b.textContent='Selecciona y copia';}}); }}
</script></body></html>'''


# ---------- la guía de bienvenida ----------

def pagina_guia(neg, nombre, quien):
    n = nombre.split()[0].capitalize() if nombre else ''
    grupo = '' if falta(neg.get('grupo_equipo')) else f'<p class="nota">Grupo del equipo: <a href="{e(neg["grupo_equipo"])}">entrar</a></p>'
    bloques = ''.join(f'<section><h2>{e(cuando)}</h2>' + ''.join(
        f'<label><input type="checkbox" data-k="{i}-{j}"><span>{e(x)}</span></label>' for j, x in enumerate(cosas))
        + '</section>' for i, (cuando, cosas) in enumerate(GUIA))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tus primeros 30 días</title><style>
body {{ margin:0; background:#f6f1ea; color:#2b2321; font-family:"Avenir Next","Helvetica Neue",Arial,sans-serif; }}
main {{ max-width:620px; margin:auto; padding:28px 16px 50px; }}
.chico {{ font-size:12px; letter-spacing:.3em; text-transform:uppercase; color:#9e4f5c; }}
h1 {{ font-family:Georgia,serif; font-style:italic; font-weight:500; font-size:44px; margin:6px 0 4px; }}
.nota {{ color:#7b6f6a; font-size:15px; line-height:1.5; }}
.barra {{ height:10px; background:#ecdcd5; border-radius:9px; overflow:hidden; margin:16px 0 6px; }} .barra i {{ display:block; height:100%; width:0; background:linear-gradient(90deg,#c9a66b,#9e4f5c); transition:width .3s; }}
section {{ background:#fff; border-radius:16px; padding:14px 18px; margin-top:14px; box-shadow:0 8px 22px rgba(90,60,40,.07); }}
h2 {{ font-family:Georgia,serif; font-size:21px; margin:0 0 8px; }}
label {{ display:flex; gap:12px; align-items:flex-start; padding:9px 0; border-top:1px solid #f0e6dd; font-size:16px; line-height:1.4; cursor:pointer; }}
label:first-of-type {{ border-top:0; }} input {{ width:20px; height:20px; accent-color:#9e4f5c; margin-top:1px; flex:none; }}
input:checked + span {{ color:#9aa0a6; text-decoration:line-through; }}
.aviso {{ font-size:13px; color:#7b6f6a; margin-top:20px; line-height:1.5; }}
</style></head><body><main>
<div class="chico">Bienvenida al equipo</div><h1>{('¡Hola, ' + e(n) + '!') if n else '¡Bienvenida!'}</h1>
<p class="nota">Esta es tu guía de los primeros 30 días. Ve marcando lo que haces: se guarda en tu celular. Cualquier duda, me escribes. — {e(quien)}</p>
{grupo}<div class="barra"><i id="b"></i></div><p class="nota" id="t"></p>
{bloques}
<p class="aviso">{e(neg.get("aviso"))}</p></main>
<script>(function(){{ var k='guia-socia', s={{}}; try{{ s=JSON.parse(localStorage.getItem(k)||'{{}}'); }}catch(e){{}}
var cs=document.querySelectorAll('input'); function pinta(){{ var h=0; cs.forEach(function(c){{ if(c.checked) h++; }});
document.getElementById('b').style.width=(100*h/cs.length)+'%'; document.getElementById('t').textContent=h+' de '+cs.length+' pasos hechos'; }}
cs.forEach(function(c){{ c.checked=!!s[c.dataset.k]; c.onchange=function(){{ s[c.dataset.k]=c.checked; try{{ localStorage.setItem(k, JSON.stringify(s)); }}catch(e){{}} pinta(); }}; }}); pinta(); }})();</script>
</body></html>'''


# ---------- comandos ----------

def copiar_compartido(archivos, sub='equipo'):
    if COMPARTIDO.is_dir():
        d = COMPARTIDO / sub
        d.mkdir(exist_ok=True)
        for f in archivos:
            if Path(f).exists():
                shutil.copy2(f, d / Path(f).name)


def hacer_presentacion(carpeta, neg):
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / 'presentacion.html'
    archivo.write_text(pagina_presentacion(neg, firma()), encoding='utf-8')
    imgs = fotos(archivo, '.slide', 1080, 1350)
    return [archivo] + imgs


def lo_que_falta(neg):
    nombres = {'enlace_unirse': 'tu enlace de Farmasi para que se unan', 'grupo_equipo': 'el enlace del grupo de WhatsApp del equipo',
               'como_empezar': 'qué hace falta para unirse', 'beneficio_socia': 'qué recibe como socia'}
    return [que for k, que in nombres.items() if falta(neg.get(k))]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--archivo', help='otro archivo de personas (por defecto equipo/datos/socias.json)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('agregar')
    for c in ('nombre', 'usuario', 'red', 'telefono', 'origen', 'ciudad', 'nota'):
        a.add_argument('--' + c)
    pa = sub.add_parser('paso')
    pa.add_argument('quien')
    pa.add_argument('etapa', choices=ID_ETAPAS)
    pa.add_argument('--fecha')
    h = sub.add_parser('hecho', help='ya le escribí (id de la tarea de hoy)')
    h.add_argument('tarea')
    sub.add_parser('hoy')
    sub.add_parser('lista')
    sub.add_parser('presentacion')
    sub.add_parser('mensajes')
    g = sub.add_parser('guia')
    g.add_argument('quien', nargs='?', default='')
    sub.add_parser('falta')
    sub.add_parser('demo')
    x = ap.parse_args()
    neg = negocio()
    try:
        if x.cmd == 'agregar':
            datos = cargar(x.archivo)
            p = agregar(datos, vars(x), x.nota)
            guardar(datos, x.archivo)
            print(f"{p['nombre']} ({p['id']}) · {p['etapa']}")
        elif x.cmd == 'paso':
            datos = cargar(x.archivo)
            p = buscar(datos, x.quien)
            if not p:
                sys.exit(f'No encontré a «{x.quien}».')
            mover(p, x.etapa, x.fecha)
            guardar(datos, x.archivo)
            print(f"{p['nombre']} → {x.etapa}" + ('  (mándale su guía: python3 equipo/socias.py guia "' + p['nombre'] + '")'
                                                   if x.etapa == 'se-unio' else ''))
        elif x.cmd == 'hecho':
            datos = cargar(x.archivo)
            hecho(datos, x.tarea)
            guardar(datos, x.archivo)
            print('Hecho ✔')
        elif x.cmd == 'hoy':
            lista = tareas(cargar(x.archivo))
            if not lista:
                print('Hoy no hay a quién escribirle del equipo.')
            for t in lista:
                print(f"• {t['quien']['nombre']}: {t['que']}  [{t['id']}]\n  {t['texto']}" + (f"\n  {t['enlace']}" if t['enlace'] else ''))
        elif x.cmd == 'lista':
            datos = cargar(x.archivo)
            nombres = dict((a, f'{c} {b}') for a, b, c in ETAPAS)
            for p in sorted(datos['personas'], key=lambda p: ID_ETAPAS.index(p['etapa'])):
                print(f"{p['id']:>4}  {p['nombre']:<22} {nombres[p['etapa']]:<18} desde {p['desde']}")
            if not datos['personas']:
                print('Todavía no hay nadie. Cuando alguien pregunte cómo vender Farmasi, agrégala.')
        elif x.cmd == 'presentacion':
            hechos = hacer_presentacion(SALIDA, neg)
            copiar_compartido(hechos)
            for f in hechos:
                print('Listo:', f.relative_to(RAIZ))
        elif x.cmd == 'mensajes':
            SALIDA.mkdir(parents=True, exist_ok=True)
            f = SALIDA / 'mensajes.html'
            f.write_text(pagina_mensajes(neg, firma()), encoding='utf-8')
            copiar_compartido([f])
            print('Listo:', f.relative_to(RAIZ))
        elif x.cmd == 'guia':
            SALIDA.mkdir(parents=True, exist_ok=True)
            nombre = x.quien
            if nombre:
                p = buscar(cargar(x.archivo), nombre)
                nombre = p['nombre'] if p else nombre
            f = SALIDA / ('guia-' + (re.sub(r'[^a-z0-9]+', '-', sin_tildes(nombre)).strip('-') or 'socia') + '.html')
            f.write_text(pagina_guia(neg, nombre.lstrip('@'), firma()), encoding='utf-8')
            print('Listo:', f.relative_to(RAIZ), '(mándale el archivo por WhatsApp: lo abre en su celular)')
        elif x.cmd == 'falta':
            print('\n'.join('- ' + q for q in lo_que_falta(neg)) or 'Está todo completo.')
        elif x.cmd == 'demo':
            carpeta = SALIDA / 'ejemplo'
            hechos = hacer_presentacion(carpeta, neg)
            (carpeta / 'mensajes.html').write_text(pagina_mensajes(neg, firma()), encoding='utf-8')
            (carpeta / 'guia-paola.html').write_text(pagina_guia(neg, 'Paola', firma()), encoding='utf-8')
            datos = {'personas': []}
            for nombre, u, etapa, hace in (('Paola Ríos', 'pao.rios', 'interesada', 2), ('Carmen Díaz', 'carmen.d', 'explicada', 4),
                                           ('Rosa Méndez', 'rosi.m', 'se-unio', 0)):
                p = agregar(datos, {'nombre': nombre, 'usuario': u, 'red': 'instagram'})
                fecha = (hoy() - datetime.timedelta(days=hace)).isoformat()
                if etapa != 'interesada':
                    mover(p, etapa, fecha)
                p['ultimo'] = fecha
            for t in tareas(datos):
                print(f"• {t['quien']['nombre']}: {t['que']}\n  {t['texto']}")
            hechos += [carpeta / 'mensajes.html', carpeta / 'guia-paola.html']
            copiar_compartido(hechos)
            for f in hechos:
                print('Listo:', f.relative_to(RAIZ))
        if x.cmd in ('presentacion', 'mensajes', 'guia', 'demo'):
            for q in lo_que_falta(neg):
                print('FALTA en equipo/negocio.json:', q)
    except ValueError as err:
        sys.exit(str(err))


if __name__ == '__main__':
    main()
