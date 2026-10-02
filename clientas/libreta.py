#!/usr/bin/env python3
"""Libreta de clientas de Isabella: quién le compra, qué compró y a quién escribirle hoy.

La forma cómoda de usarla es la página: en el panel de Isa toca "Clientas".
Este programa es lo que hay por detrás, y lo usan Isa y el agente de comunidad.

Uso (desde la carpeta del proyecto):
  python3 clientas/libreta.py hoy                       # lo que hay que hacer hoy
  python3 clientas/libreta.py agregar --nombre "Carla Ruiz" --usuario carlita.r --red instagram \\
      --etapa pregunto --origen comentario --nota "Preguntó por el sérum de vitamina C"
  python3 clientas/libreta.py pedido "Carla Ruiz" --producto "Vitamin C Glow Serum" --total 25 --pagado
  python3 clientas/libreta.py entregado p3              # el pedido p3 ya se entregó
  python3 clientas/libreta.py nota "Carla" "Le encantó, quiere probar la crema"
  python3 clientas/libreta.py etapa "Carla" interesada
  python3 clientas/libreta.py seguimiento "Carla" --fecha 2026-10-09 --motivo "Le llega el sueldo"
  python3 clientas/libreta.py hecho recompra:p3:0       # tarea de hoy resuelta
  python3 clientas/libreta.py lista [--etapa pidio]     # todas las clientas
  python3 clientas/libreta.py buscar carla
  python3 clientas/libreta.py resumen                   # números del negocio
  python3 clientas/libreta.py ventas-csv                # le pasa al estratega lo que más se vende
  python3 clientas/libreta.py pagina                    # copia para ver sin el panel (solo lectura)
  python3 clientas/libreta.py demo                      # libreta de ejemplo (clientas/datos/demo.json)

Todo vive en clientas/datos/libreta.json, solo en esta computadora: no se sube a internet.
Con --archivo se usa otra libreta (por ejemplo la de ejemplo). Solo librería estándar.
"""
import argparse
import base64
import csv
import datetime
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DATOS = AQUI / 'datos'
LIBRETA = DATOS / 'libreta.json'
PAGINA = AQUI / 'libreta.html'
VOZ = RAIZ / 'marca' / 'voz-isabella.md'
VENTAS_CSV = RAIZ / 'planificador' / 'datos' / 'ventas.csv'
COMPARTIDO = Path('/mnt/project-files')

# Los pasos de una clienta, de la primera pregunta a clienta fiel.
ETAPAS = [
    {'id': 'pregunto', 'nombre': 'Preguntó', 'icono': '💬', 'color': '#8f7cf6'},
    {'id': 'interesada', 'nombre': 'Interesada', 'icono': '✨', 'color': '#f2a541'},
    {'id': 'pidio', 'nombre': 'Pidió', 'icono': '🛍️', 'color': '#ef6f8e'},
    {'id': 'entregado', 'nombre': 'Ya lo tiene', 'icono': '📦', 'color': '#3fb68b'},
    {'id': 'fiel', 'nombre': 'Clienta fiel', 'icono': '💖', 'color': '#d64f8a'},
]
PAUSA = {'id': 'pausa', 'nombre': 'En pausa', 'icono': '🌙', 'color': '#9aa0b4'}
ID_ETAPAS = [e['id'] for e in ETAPAS] + ['pausa']
REDES = ['instagram', 'tiktok', 'whatsapp', 'facebook', 'en persona']

# Cuántos días le dura a una clienta cada tipo de producto (aproximado, para avisar
# una semana antes de que se le acabe). Isabella puede cambiarlo en cada pedido.
DURACIONES = [
    (r'\bte\b|\btea\b(?!\s*tree)|cafe|coffee|batido|shake|vitamin[ae]s?\b|suplement|collagen|colageno|nutriplus|fiber|fibra|protein', 30),
    (r'serum|suero|ampolla|ampoule', 45),
    (r'limpiador|cleanser|gel|tonico|toner|micelar|exfol|scrub|jabon|soap', 45),
    (r'shampoo|champu|acondicionador|conditioner|hair|cabello|desodorante|deodorant|pasta dental|toothpaste|body|corporal|loci?on|lotion|ducha|shower', 45),
    (r'protector|spf|sunscreen|bloqueador', 45),
    (r'crema|cream|contorno|eye|mascarilla|mask|aceite|oil|balm|balsamo|hidrat|moistur', 60),
    (r'mascara|pestan|lash|delineador|liner|ceja|brow', 90),
    (r'base|foundation|corrector|concealer|bb\b|cc\b|primer', 90),
    (r'labial|lipstick|lip|gloss|polvo|powder|rubor|blush|bronze|sombra|shadow|iluminador|highlight', 120),
    (r'perfume|parfum|fragan|fragrance|colonia|edp|edt', 120),
]
DURACION_DEFECTO = 60
AVISO_ANTES = 7          # días antes de que se acabe para ofrecerle otra vez
DIAS_SIN_RESPUESTA = 3   # una clienta que preguntó y no volvió a escribir
DIAS_OPINION = 5         # después de entregar, preguntarle cómo le fue
MAX_INSISTIR = 2         # mensajes sin respuesta antes de dejarla en pausa

# A la clienta no se le hacen preguntas para llenar su ficha: se conoce por lo que ya
# dijo en sus mensajes, lo que tocó en los botones del asistente y lo que compró.
PIEL = [('grasa', r'\bgras[ao]s?a?\b|grasosa|oily|brillo|poros abiertos'),
        ('seca', r'\bsec[ao]\b|reseca|tirante|\bdry\b'),
        ('mixta', r'\bmixta\b|combinad|combination'),
        ('sensible', r'sensible|se irrita|irritaci|rojez|sensitive')]
GUSTOS = [('cuidado de la piel', r'serum|crema|cream|mascarilla|mask|limpiador|cleanser|tonico|spf|protector|piel|acne|manchas|arrugas|tea tree|vitamin c'),
          ('maquillaje', r'labial|lipstick|lip|base|foundation|mascara|pestan|sombra|rubor|corrector|polvo|maquill|tono'),
          ('bienestar', r'\bte\b|\btea\b(?!\s*tree)|cafe|coffee|nutriplus|vitaminas?\b(?!\s*c\b)|colageno|collagen|batido'),
          ('cabello', r'shampoo|champu|acondicionador|cabello|hair|pelo'),
          ('fragancias', r'perfume|parfum|fragan|colonia')]


# ---------- guardar y leer ----------

def hoy():
    return datetime.date.today()


def nuevo():
    return {'clientas': [], 'pedidos': [], 'hechos': {}, 'creada': hoy().isoformat()}


def cargar(archivo=None):
    archivo = Path(archivo or LIBRETA)
    if not archivo.exists():
        return nuevo()
    datos = json.loads(archivo.read_text(encoding='utf-8'))
    for k, v in nuevo().items():
        datos.setdefault(k, v)
    return datos


def guardar(datos, archivo=None):
    """Escribe de una sola vez (si algo falla a medias, la libreta anterior queda intacta)."""
    archivo = Path(archivo or LIBRETA)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=archivo.parent, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(tmp, archivo)


def sin_tildes(t):
    t = unicodedata.normalize('NFKD', str(t or '')).encode('ascii', 'ignore').decode()
    return t.lower().strip()


def usuario_limpio(u):
    return (u or '').strip().lstrip('@').strip().lower()


def nuevo_id(lista, letra):
    n = 0
    for x in lista:
        m = re.fullmatch(letra + r'(\d+)', str(x.get('id', '')))
        if m:
            n = max(n, int(m.group(1)))
    return f'{letra}{n + 1}'


def fecha(t):
    if not t:
        return None
    try:
        return datetime.date.fromisoformat(str(t)[:10])
    except ValueError:
        return None


# ---------- clientas ----------

def buscar_clienta(datos, quien):
    """Por id (c3), usuario (@carla), teléfono o nombre (también parte del nombre)."""
    if not quien:
        return None
    q = str(quien).strip()
    for c in datos['clientas']:
        if c['id'] == q:
            return c
    u = usuario_limpio(q)
    for c in datos['clientas']:
        if u and usuario_limpio(c.get('usuario')) == u:
            return c
    digitos = re.sub(r'\D', '', q)
    if len(digitos) >= 7:
        for c in datos['clientas']:
            if re.sub(r'\D', '', c.get('telefono') or '').endswith(digitos[-9:]):
                return c
    n = sin_tildes(q)
    exactas = [c for c in datos['clientas'] if sin_tildes(c.get('nombre')) == n]
    if exactas:
        return exactas[0]
    parecidas = [c for c in datos['clientas'] if n and n in sin_tildes(c.get('nombre'))]
    return parecidas[0] if len(parecidas) == 1 else None


CAMPOS_CLIENTA = ('nombre', 'usuario', 'red', 'telefono', 'ciudad', 'cumple', 'piel', 'piel_fuente', 'tono',
                  'intereses', 'notas', 'etapa', 'origen', 'foto', 'publicacion', 'email')


def guardar_clienta(datos, campos, nota=None):
    """Crea la clienta o, si ya existe (mismo id, usuario, teléfono o nombre), la completa."""
    editando = bool(campos.get('id'))  # desde la ficha: lo que viene vacío se borra
    campos = {k: v for k, v in campos.items() if k in CAMPOS_CLIENTA + ('id',)
              and v is not None and (editando or v != '') and not (k in ('nombre', 'etapa', 'red') and v == '')}
    if 'usuario' in campos:
        campos['usuario'] = usuario_limpio(campos['usuario'])
    if campos.get('cumple'):
        campos['cumple'] = cumple_limpio(campos['cumple'])
    if 'etapa' in campos and campos['etapa'] not in ID_ETAPAS:
        raise ValueError(f"Etapa desconocida: {campos['etapa']}. Usa: {', '.join(ID_ETAPAS)}")
    if isinstance(campos.get('intereses'), str):
        campos['intereses'] = [x.strip() for x in campos['intereses'].split(',') if x.strip()]
    c = None
    for clave in ('id', 'usuario', 'telefono', 'nombre'):
        if campos.get(clave):
            c = buscar_clienta(datos, ('@' + campos[clave]) if clave == 'usuario' else campos[clave])
            if c and (clave != 'nombre' or sin_tildes(c['nombre']) == sin_tildes(campos['nombre'])):
                break
            c = None
    hoy_t = hoy().isoformat()
    if c is None:
        if not campos.get('nombre') and not campos.get('usuario'):
            raise ValueError('Falta el nombre o el usuario de la clienta.')
        c = {'id': nuevo_id(datos['clientas'], 'c'), 'nombre': campos.get('nombre') or '@' + campos['usuario'],
             'etapa': 'pregunto', 'creada': hoy_t, 'ultimo_contacto': hoy_t, 'historial': []}
        datos['clientas'].append(c)
        c['historial'].append({'fecha': hoy_t, 'texto': 'Entró a la libreta' +
                               (f" (vino por {campos['origen']})" if campos.get('origen') else '')})
    else:
        if c['nombre'].startswith('@') and campos.get('nombre'):
            c['nombre'] = campos['nombre']
    for k, v in campos.items():
        if k == 'id' or (k == 'nombre' and not editando and not c['nombre'].startswith('@')):
            continue
        if k == 'intereses':
            c['intereses'] = v if editando else list(dict.fromkeys(c.get('intereses', []) + v))
        elif k == 'etapa':
            mover(datos, c, v)
        else:
            c[k] = v
    if nota:
        anotar(c, nota)
    return c


def cumple_limpio(t):
    """Acepta 2026-03-14, 14/03, 14-3 o "14 de marzo" y guarda MM-DD."""
    t = str(t).strip().lower()
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
             'septiembre', 'octubre', 'noviembre', 'diciembre']
    m = re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})', t)
    if m:
        return f'{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    if re.fullmatch(r'\d{2}-\d{2}', t):
        return t  # ya viene como MM-DD
    m = re.fullmatch(r'(\d{1,2})[/.-](\d{1,2})(?:[/.-]\d{2,4})?', t)
    if m:
        return f'{int(m.group(2)):02d}-{int(m.group(1)):02d}'  # día/mes
    m = re.fullmatch(r'(\d{1,2})\s*(?:de\s+)?([a-z]+)', sin_tildes(t))
    if m and m.group(2) in meses:
        return f'{meses.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}'
    return t


def anotar(c, texto, cuando=None):
    cuando = cuando or hoy().isoformat()
    c.setdefault('historial', []).append({'fecha': cuando, 'texto': texto})
    c['ultimo_contacto'] = max(c.get('ultimo_contacto') or cuando, cuando)


def mover(datos, c, etapa):
    if etapa not in ID_ETAPAS:
        raise ValueError(f'Etapa desconocida: {etapa}')
    if c.get('etapa') != etapa:
        nombre = next((e['nombre'] for e in ETAPAS + [PAUSA] if e['id'] == etapa), etapa)
        c['etapa'] = etapa
        c.setdefault('historial', []).append({'fecha': hoy().isoformat(), 'texto': f'Pasó a «{nombre}»'})


def borrar_clienta(datos, cid):
    datos['clientas'] = [c for c in datos['clientas'] if c['id'] != cid]
    datos['pedidos'] = [p for p in datos['pedidos'] if p['clienta'] != cid]


# ---------- pedidos ----------

def dias_que_dura(nombre):
    t = sin_tildes(nombre)
    for patron, dias in DURACIONES:
        if re.search(patron, t):
            return dias
    return DURACION_DEFECTO


def producto_limpio(p):
    if isinstance(p, str):
        p = {'nombre': p}
    nombre = (p.get('nombre') or '').strip()
    if not nombre:
        return None
    try:
        cantidad = max(1, int(p.get('cantidad') or 1))
    except (TypeError, ValueError):
        cantidad = 1
    try:
        dias = int(p.get('dias') or 0) or dias_que_dura(nombre)
    except (TypeError, ValueError):
        dias = dias_que_dura(nombre)
    limpio = {'nombre': nombre, 'cantidad': cantidad, 'dias': dias}
    for k in ('codigo', 'foto'):
        if p.get(k):
            limpio[k] = p[k]
    return limpio


def guardar_pedido(datos, campos):
    c = buscar_clienta(datos, campos.get('clienta'))
    if not c:
        raise ValueError(f"No encontré a la clienta «{campos.get('clienta')}». Agrégala primero.")
    productos = [x for x in (producto_limpio(p) for p in campos.get('productos') or []) if x]
    if not productos:
        raise ValueError('El pedido necesita al menos un producto.')
    total = campos.get('total')
    try:
        total = round(float(total), 2) if total not in (None, '') else None
    except (TypeError, ValueError):
        total = None
    p = next((x for x in datos['pedidos'] if campos.get('id') and x['id'] == campos['id']), None)
    nuevo_pedido = p is None
    if nuevo_pedido:
        p = {'id': nuevo_id(datos['pedidos'], 'p'), 'estado': 'pedido'}
        datos['pedidos'].append(p)
    p.update({'clienta': c['id'], 'fecha': campos.get('fecha') or p.get('fecha') or hoy().isoformat(),
              'productos': productos, 'total': total, 'pagado': bool(campos.get('pagado')),
              'nota': campos.get('nota') or p.get('nota') or ''})
    if nuevo_pedido:
        nombres = ', '.join(x['nombre'] for x in productos)
        anotar(c, f'Pidió: {nombres}', p['fecha'])
        entregados_antes = [x for x in datos['pedidos'] if x['clienta'] == c['id'] and x['id'] != p['id']]
        mover(datos, c, 'fiel' if entregados_antes else 'pidio')
    if campos.get('entregado'):
        entregar(datos, p['id'], campos.get('entregado') if fecha(campos.get('entregado')) else None)
    return p


def entregar(datos, pid, cuando=None):
    p = next((x for x in datos['pedidos'] if x['id'] == pid), None)
    if not p:
        raise ValueError(f'No encontré el pedido {pid}.')
    p['estado'] = 'entregado'
    p['entregado'] = cuando or hoy().isoformat()
    c = buscar_clienta(datos, p['clienta'])
    if c:
        anotar(c, 'Recibió su pedido', p['entregado'])
        anteriores = sum(1 for x in datos['pedidos'] if x['clienta'] == c['id'] and x['estado'] == 'entregado')
        if c.get('etapa') != 'pausa':
            mover(datos, c, 'fiel' if anteriores > 1 else 'entregado')
    return p


def borrar_pedido(datos, pid):
    datos['pedidos'] = [p for p in datos['pedidos'] if p['id'] != pid]


# ---------- lo que hay que hacer hoy ----------

def voz():
    """Saludo, trato y despedida de Isabella si ya están en su ficha (si no, los de siempre)."""
    v = {'trato': '', 'firma': 'Isabella'}
    if VOZ.exists():
        texto = VOZ.read_text(encoding='utf-8')
        m = re.search(r'Nombre en redes:\s*(.+)', texto)
        if m and 'PENDIENTE' not in m.group(1):
            v['firma'] = m.group(1).strip()
        m = re.search(r'¿dice "amiga".*?…\?\s*(.*)', texto)
        if m and m.group(1).strip() and 'PENDIENTE' not in m.group(1):
            v['trato'] = m.group(1).strip().split(',')[0].strip(' "')
    return v


def primer_nombre(c):
    n = (c.get('nombre') or '').lstrip('@').split()
    return n[0].capitalize() if n else ''


def mensaje(tipo, c, extra=''):
    n = primer_nombre(c)
    if tipo == 'recompra':
        return (f'¡Hola, {n}! 💕 ¿Cómo te ha ido con {extra}? Ya debe estar por acabarse. '
                '¿Quieres que te aparte otro para que no te quedes sin él?')
    if tipo == 'cumple':
        return (f'¡Feliz cumpleaños, {n}! 🎉 Que tengas un día precioso. Gracias por confiar en mí, '
                'te mando un abrazo enorme.')
    if tipo == 'opinion':
        return (f'¡Hola, {n}! ¿Qué tal te pareció {extra}? Cuéntame cómo te va, me encanta saber. '
                'Y si te animas, mándame una foto o un audio contándolo 🥰')
    if tipo == 'frio':
        return (f'¡Hola, {n}! Te escribo por si te quedó alguna duda {extra}. '
                'Aquí estoy para ayudarte a elegir lo que mejor te vaya 😊')
    if tipo == 'entrega':
        return f'¡Hola, {n}! Tu pedido ya está listo 🛍️ ¿Cuándo te queda bien que te lo entregue?'
    if tipo == 'seguimiento':
        return f'¡Hola, {n}! Te escribo como quedamos {extra}😊'
    return f'¡Hola, {n}!'


def enlace_chat(c, texto=''):
    """Abre el chat con la clienta con el mensaje ya escrito (WhatsApp) o su perfil."""
    tel = re.sub(r'\D', '', c.get('telefono') or '')
    if tel:
        return f'https://wa.me/{tel}' + (f'?text={quote(texto)}' if texto else '')
    u = usuario_limpio(c.get('usuario'))
    if u and c.get('red') == 'tiktok':
        return f'https://www.tiktok.com/@{u}'
    if u and c.get('red') == 'facebook':
        return f'https://m.me/{u}'
    if u:
        return f'https://ig.me/m/{u}'
    return ''


def corto(nombre):
    """El nombre sin la marca adelante, como lo diría Isabella (Vitamin C Glow Serum)."""
    return re.sub(r'^(dr\.?\s*c\.?\s*tuna|farmasi|nutriplus)\s+', '', nombre or '', flags=re.I)


def nombres_productos(productos):
    nombres = [corto(x['nombre']) for x in productos]
    return nombres[0] if len(nombres) == 1 else ', '.join(nombres[:-1]) + ' y ' + nombres[-1]


def n_dias(n):
    return '1 día' if n == 1 else f'{n} días'


def conocerla(c, pedidos):
    """Lo que se sabe de ella sin preguntarle: de sus mensajes, sus botones y sus compras."""
    pistas = []
    textos = ' '.join(sin_tildes(h.get('texto')) for h in c.get('historial', []))
    if c.get('piel'):
        pistas.append({'que': 'Piel ' + c['piel'], 'de': c.get('piel_fuente') or 'anotado'})
    else:
        for piel, patron in PIEL:
            if re.search(patron, textos):
                pistas.append({'que': f'Piel {piel} (probable)', 'de': 'lo dijo en un mensaje'})
                break
    compras = ' '.join(sin_tildes(x['nombre']) for p in pedidos for x in p['productos'])
    for gusto, patron in GUSTOS:
        if re.search(patron, compras):
            pistas.append({'que': f'Le gusta {gusto}', 'de': 'por lo que compró'})
        elif re.search(patron, textos + ' ' + sin_tildes(' '.join(c.get('intereses', [])))):
            pistas.append({'que': f'Le interesa {gusto}', 'de': 'por lo que preguntó'})
    if c.get('publicacion'):
        pistas.append({'que': f"Llegó por «{c['publicacion']}»", 'de': 'comentó esa publicación'})
    if len(pedidos) >= 2:
        dias = sorted(fecha(p['fecha']) for p in pedidos if fecha(p['fecha']))
        if len(dias) >= 2:
            cada = round((dias[-1] - dias[0]).days / (len(dias) - 1))
            pistas.append({'que': f'Compra cada {n_dias(cada)} más o menos', 'de': 'por sus pedidos'})
    return pistas


def tareas(datos, dia=None):
    dia = dia or hoy()
    hechos = datos.get('hechos', {})
    por_id = {c['id']: c for c in datos['clientas']}
    lista = []

    def tarea(id_, tipo, c, titulo, detalle, cuando, texto, urgencia, **extra):
        if id_ in hechos:
            return
        lista.append(dict({'id': id_, 'tipo': tipo, 'clienta': c['id'], 'nombre': c['nombre'],
                           'titulo': titulo, 'detalle': detalle, 'fecha': cuando.isoformat(),
                           'mensaje': texto, 'enlace': enlace_chat(c, texto), 'urgencia': urgencia}, **extra))

    # 1. Se le está acabando un producto: ofrecérselo otra vez.
    for p in datos['pedidos']:
        c = por_id.get(p['clienta'])
        entregado = fecha(p.get('entregado'))
        if not c or c.get('etapa') == 'pausa' or p.get('estado') != 'entregado' or not entregado:
            continue
        for i, prod in enumerate(p['productos']):
            se_acaba = entregado + datetime.timedelta(days=prod.get('dias') or DURACION_DEFECTO)
            avisar = se_acaba - datetime.timedelta(days=AVISO_ANTES)
            if dia < avisar:
                continue
            ya_repitio = any(q['clienta'] == c['id'] and fecha(q['fecha']) and fecha(q['fecha']) > entregado
                             and any(sin_tildes(x['nombre']) == sin_tildes(prod['nombre']) for x in q['productos'])
                             for q in datos['pedidos'])
            if ya_repitio:
                continue
            faltan = (se_acaba - dia).days
            cuando = (f'se le acabó hace {n_dias(-faltan)}' if faltan < 0 else
                      'se le acaba hoy' if faltan == 0 else f'se le acaba en {n_dias(faltan)}')
            tarea(f"recompra:{p['id']}:{i}", 'recompra', c, f"Ofrécele otra vez {corto(prod['nombre'])}",
                  f"Lo recibió hace {n_dias((dia - entregado).days)}: {cuando}.", avisar,
                  mensaje('recompra', c, 'tu ' + corto(prod['nombre'])),
                  3 if faltan <= 0 else 2, producto=prod['nombre'], foto=prod.get('foto', ''))

    # 2. Cumpleaños de esta semana.
    for c in datos['clientas']:
        cum = c.get('cumple') or ''
        m = re.fullmatch(r'(\d{2})-(\d{2})', cum)
        if not m:
            continue
        try:
            este = datetime.date(dia.year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            este = datetime.date(dia.year, 3, 1)  # 29 de febrero en año normal
        if este < dia - datetime.timedelta(days=1):
            continue
        faltan = (este - dia).days
        if faltan > 7:
            continue
        cuando = 'es hoy 🎂' if faltan == 0 else 'fue ayer' if faltan < 0 else f'en {n_dias(faltan)}'
        tarea(f"cumple:{c['id']}:{dia.year}", 'cumple', c, f"Cumpleaños de {primer_nombre(c)}",
              f'Su cumpleaños {cuando}.', este, mensaje('cumple', c), 3 if faltan <= 0 else 1)

    # 3. Pedidos por entregar o por cobrar.
    for p in datos['pedidos']:
        c = por_id.get(p['clienta'])
        if not c or p.get('estado') == 'entregado':
            continue
        f = fecha(p['fecha']) or dia
        detalle = f"{nombres_productos(p['productos'])} · pedido {'hoy' if dia == f else 'hace ' + n_dias((dia - f).days)}"
        if not p.get('pagado'):
            detalle += ' · falta cobrar'
        tarea(f"entrega:{p['id']}", 'entrega', c, 'Entregar su pedido', detalle, f,
              mensaje('entrega', c), 2 if (dia - f).days >= 3 else 1, pedido=p['id'])

    # 4. Preguntarle cómo le fue (y de paso conseguir una opinión para las redes).
    for p in datos['pedidos']:
        c = por_id.get(p['clienta'])
        e = fecha(p.get('entregado'))
        if not c or not e or c.get('etapa') == 'pausa':
            continue
        if DIAS_OPINION <= (dia - e).days <= DIAS_OPINION + 10:
            tarea(f"opinion:{p['id']}", 'opinion', c, '¿Cómo le fue?',
                  f"Hace {n_dias((dia - e).days)} recibió {nombres_productos(p['productos'])}. "
                  'Si le encantó, pídele una foto o un audio para tus redes.', e + datetime.timedelta(days=DIAS_OPINION),
                  mensaje('opinion', c, 'tu ' + corto(p['productos'][0]['nombre']) if len(p['productos']) == 1 else 'tus productos'), 1)

    # 5. Seguimientos que Isabella se anotó.
    for c in datos['clientas']:
        s = c.get('seguimiento') or {}
        f = fecha(s.get('fecha'))
        if f and f <= dia and c.get('etapa') != 'pausa':
            motivo = s.get('motivo') or 'Quedaste en escribirle'
            tarea(f"seg:{c['id']}:{f.isoformat()}", 'seguimiento', c, motivo,
                  'Te lo anotaste para hoy.' if f == dia else f'Te lo anotaste para el {f.strftime("%d/%m")}.', f,
                  mensaje('seguimiento', c, ''), 3 if f < dia else 2)

    # 6. Preguntó y no volvió a escribir (se le insiste 2 veces como máximo).
    for c in datos['clientas']:
        u = fecha(c.get('ultimo_contacto'))
        if c.get('etapa') not in ('pregunto', 'interesada') or not u or (c.get('seguimiento') or {}).get('fecha'):
            continue
        if sum(1 for h in hechos if h.startswith(f"frio:{c['id']}:")) >= MAX_INSISTIR:
            continue
        if (dia - u).days >= DIAS_SIN_RESPUESTA:
            interes = ', '.join(c.get('intereses', [])[:2])
            tarea(f"frio:{c['id']}:{u.isoformat()}", 'frio', c, 'Escríbele otra vez',
                  f"Hace {n_dias((dia - u).days)} que no hablan" + (f' · le interesa {interes}' if interes else '') + '.',
                  u + datetime.timedelta(days=DIAS_SIN_RESPUESTA),
                  mensaje('frio', c, f'sobre {interes}' if interes else ''), 1)

    lista.sort(key=lambda t: (-t['urgencia'], t['fecha']))
    return lista


def marcar_hecho(datos, tid):
    datos.setdefault('hechos', {})[tid] = hoy().isoformat()
    tipo, cid = tid.split(':')[0], tid.split(':')[1]
    if tipo == 'entrega':
        entregar(datos, cid)
        return
    c = buscar_clienta(datos, cid)
    if tipo in ('recompra', 'opinion', 'entrega'):
        p = next((x for x in datos['pedidos'] if x['id'] == cid), None)
        c = buscar_clienta(datos, p['clienta']) if p else None
    if c:
        que = {'recompra': 'Le ofrecí otra vez su producto', 'cumple': 'Le escribí por su cumpleaños',
               'opinion': 'Le pregunté cómo le fue', 'seguimiento': 'Le escribí como quedamos',
               'frio': 'Le escribí otra vez'}.get(tipo, 'Le escribí')
        anotar(c, que)
        if tipo == 'seguimiento':
            c.pop('seguimiento', None)
        if tipo == 'frio' and sum(1 for h in datos['hechos'] if h.startswith(f"frio:{c['id']}:")) >= MAX_INSISTIR:
            mover(datos, c, 'pausa')
            anotar(c, f'No respondió a {MAX_INSISTIR} mensajes: queda en pausa (si vuelve a escribir, muévela)')


def deshacer(datos, tid):
    datos.get('hechos', {}).pop(tid, None)


# ---------- números ----------

def resumen(datos, dia=None):
    dia = dia or hoy()
    mes = dia.strftime('%Y-%m')
    pedidos_mes = [p for p in datos['pedidos'] if str(p.get('fecha', '')).startswith(mes)]
    con_total = [p for p in pedidos_mes if p.get('total') is not None]
    por_cliente = {}
    for p in datos['pedidos']:
        por_cliente[p['clienta']] = por_cliente.get(p['clienta'], 0) + 1
    compradoras = len(por_cliente)
    productos = {}
    for p in datos['pedidos']:
        for x in p['productos']:
            k = sin_tildes(x['nombre'])
            r = productos.setdefault(k, {'nombre': x['nombre'], 'cantidad': 0, 'foto': x.get('foto', '')})
            r['cantidad'] += x.get('cantidad', 1)
            r['foto'] = r['foto'] or x.get('foto', '')
    etapas = {e['id']: 0 for e in ETAPAS + [PAUSA]}
    for c in datos['clientas']:
        etapas[c.get('etapa', 'pregunto')] = etapas.get(c.get('etapa', 'pregunto'), 0) + 1
    preguntaron = len(datos['clientas'])
    nuevas_mes = sum(1 for c in datos['clientas'] if str(c.get('creada', '')).startswith(mes))
    return {
        'clientas': preguntaron,
        'nuevas_mes': nuevas_mes,
        'compradoras': compradoras,
        'fieles': sum(1 for n in por_cliente.values() if n > 1),
        'conversion': round(100 * compradoras / preguntaron) if preguntaron else 0,
        'pedidos_mes': len(pedidos_mes),
        'ventas_mes': round(sum(p['total'] for p in con_total), 2) if con_total else None,
        'por_cobrar': sum(1 for p in datos['pedidos'] if not p.get('pagado')),
        'por_entregar': sum(1 for p in datos['pedidos'] if p.get('estado') != 'entregado'),
        'etapas': etapas,
        'top_productos': sorted(productos.values(), key=lambda r: -r['cantidad'])[:6],
        'meses': ventas_por_mes(datos, dia),
    }


def ventas_por_mes(datos, dia, n=6):
    meses = []
    a, m = dia.year, dia.month
    for _ in range(n):
        meses.append(f'{a}-{m:02d}')
        a, m = (a - 1, 12) if m == 1 else (a, m - 1)
    meses.reverse()
    nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
    return [{'mes': k, 'nombre': nombres[int(k[5:]) - 1],
             'pedidos': sum(1 for p in datos['pedidos'] if str(p.get('fecha', '')).startswith(k))}
            for k in meses]


# ---------- productos de la tienda (para elegir con foto) ----------

def catalogo():
    """Productos que ya leyó el scraper, con su foto, para el buscador de la página."""
    vistos, lista = set(), []

    def poner(nombre, codigo='', foto=''):
        k = sin_tildes(nombre)
        if not nombre or k in vistos:
            return
        vistos.add(k)
        lista.append({'nombre': nombre, 'codigo': str(codigo or ''), 'foto': foto, 'dias': dias_que_dura(nombre)})

    # Fotos que ya están en la computadora (scraper y anuncios)
    for carpeta in (RAIZ / 'lector-farmasi' / 'salida', RAIZ / 'agente-contenido' / 'productos'):
        if not carpeta.is_dir():
            continue
        for d in sorted(carpeta.iterdir()):
            ficha = next((d / n for n in ('datos.json', 'ficha.json') if (d / n).exists()), None)
            if not ficha:
                continue
            try:
                info = json.loads(ficha.read_text(encoding='utf-8'))
            except ValueError:
                continue
            prod = info.get('producto') if isinstance(info.get('producto'), dict) else {}
            nombre = info.get('nombre') or prod.get('nombre')
            foto = next((d / n for n in ('producto.jpg', 'producto.png') if (d / n).exists()), None)
            poner(nombre, info.get('codigo'), f'/archivo?ruta={quote(str(foto.relative_to(RAIZ)))}' if foto else '')
    # Todo el catálogo de la tienda (si el scraper lo leyó), con la foto de internet
    cat = RAIZ / 'lector-farmasi' / 'salida' / 'catalogo.json'
    if cat.exists():
        try:
            for p in json.loads(cat.read_text(encoding='utf-8')).get('productos', []):
                poner(p.get('nombre'), p.get('codigo'), (p.get('imagenes_url') or [''])[0])
        except ValueError:
            pass
    return lista


# ---------- lo que ve la página ----------

def vista(datos, dia=None):
    dia = dia or hoy()
    pedidos_de = {}
    for p in sorted(datos['pedidos'], key=lambda p: p.get('fecha', ''), reverse=True):
        pedidos_de.setdefault(p['clienta'], []).append(p)
    clientas = []
    for c in datos['clientas']:
        c = dict(c)
        mios = pedidos_de.get(c['id'], [])
        c['pedidos'] = [p['id'] for p in mios]
        c['n_pedidos'] = len(mios)
        c['gastado'] = round(sum(p['total'] for p in mios if p.get('total') is not None), 2) if any(p.get('total') is not None for p in mios) else None
        c['ultimo_pedido'] = mios[0]['fecha'] if mios else None
        c['productos'] = list(dict.fromkeys(x['nombre'] for p in mios for x in p['productos']))
        c['enlace'] = enlace_chat(c)
        c['pistas'] = conocerla(c, mios)
        clientas.append(c)
    return {'hoy': dia.isoformat(), 'etapas': ETAPAS, 'pausa': PAUSA, 'redes': REDES,
            'clientas': clientas, 'pedidos': datos['pedidos'], 'tareas': tareas(datos, dia),
            'resumen': resumen(datos, dia), 'catalogo': catalogo(), 'voz': voz(),
            'asistente': {k: v for k, v in leer_config().items() if k in ('hoja', 'ultima')}}


# ---------- traer clientas del asistente de mensajes (ManyChat u otro) ----------

CONFIG = DATOS / 'config.json'
# Nombres de columna que puede traer la hoja (en español o inglés, como los exporta el asistente)
COLUMNAS = {
    'nombre': ['nombre', 'name', 'full name', 'nombre completo'],
    'nombre1': ['first name', 'primer nombre'],
    'apellido': ['last name', 'apellido'],
    'usuario': ['usuario', 'username', 'instagram username', 'ig username', 'instagram', 'tiktok username', 'tiktok', 'user name'],
    'telefono': ['telefono', 'phone', 'whatsapp', 'whatsapp phone', 'celular', 'numero'],
    'email': ['email', 'correo', 'e-mail'],
    'red': ['red', 'canal', 'channel', 'plataforma', 'platform'],
    'piel': ['piel', 'tipo de piel', 'skin', 'skin type'],
    'interes': ['interes', 'producto', 'product', 'interest', 'le interesa'],
    'mensaje': ['mensaje', 'ultimo mensaje', 'last input', 'last text input', 'pregunta', 'last message'],
    'publicacion': ['publicacion', 'post', 'reel', 'video', 'comento en'],
    'etiquetas': ['etiquetas', 'tags', 'tag'],
    'cumple': ['cumpleanos', 'birthday', 'fecha de cumpleanos', 'cumple'],
    'ciudad': ['ciudad', 'city'],
    'origen': ['origen', 'source', 'vino por'],
    'fecha': ['fecha', 'last interaction', 'ultima interaccion', 'subscribed', 'date'],
}


def leer_config():
    try:
        return json.loads(CONFIG.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def guardar_config(cfg):
    DATOS.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def enlace_csv(url):
    """Un enlace de Google Sheets se convierte en su descarga como tabla."""
    m = re.search(r'docs\.google\.com/spreadsheets/d/([\w-]+)', url)
    if m and 'output=csv' not in url and 'format=csv' not in url:
        gid = re.search(r'[#&?]gid=(\d+)', url)
        return f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv' + (f'&gid={gid.group(1)}' if gid else '')
    return url


def leer_tabla(origen):
    import io
    import urllib.request
    if re.match(r'https?://', origen):
        try:
            with urllib.request.urlopen(enlace_csv(origen), timeout=20) as r:
                texto = r.read().decode('utf-8-sig')
        except OSError as e:
            raise ValueError(f'No pude abrir la hoja ({e}). Revisa el enlace y que haya internet.')
        if texto.lstrip().startswith('<'):
            raise ValueError('El enlace no deja leer la hoja. En Google Sheets: Compartir → '
                             '"Cualquier persona con el enlace" puede ver.')
    else:
        texto = Path(origen).read_text(encoding='utf-8-sig')
    return list(csv.DictReader(io.StringIO(texto)))


def sincronizar(datos, origen=None):
    """Trae las personas que escribieron al asistente y las anota o completa en la libreta."""
    cfg = leer_config()
    origen = origen or cfg.get('hoja')
    if not origen:
        raise ValueError('Todavía no hay una hoja conectada.')
    filas = leer_tabla(origen)
    nuevas, actualizadas = [], 0
    for fila in filas:
        col = {sin_tildes(k).strip(): (v or '').strip() for k, v in fila.items() if k}
        dato = lambda campo: next((col[n] for n in COLUMNAS[campo] if col.get(n)), '')
        nombre = dato('nombre') or ' '.join(x for x in (dato('nombre1'), dato('apellido')) if x)
        usuario, telefono = usuario_limpio(dato('usuario')), dato('telefono')
        if not (nombre or usuario or telefono):
            continue
        red = sin_tildes(dato('red'))
        red = next((r for r in REDES if r in red), '') or ('whatsapp' if telefono and not usuario else 'instagram')
        etiquetas = sin_tildes(dato('etiquetas'))
        etapa = 'interesada' if re.search(r'comprar|pedido|quiere|interesad|apart', etiquetas) else 'pregunto'
        ya = next((c for c in (buscar_clienta(datos, q) for q in ('@' + usuario if usuario else None, telefono, nombre) if q) if c), None)
        campos = {'nombre': nombre or None, 'usuario': usuario, 'telefono': telefono, 'red': red,
                  'email': dato('email'), 'ciudad': dato('ciudad'), 'publicacion': dato('publicacion'),
                  'origen': dato('origen') or 'asistente de mensajes', 'intereses': [dato('interes')] if dato('interes') else []}
        if dato('piel') and not (ya or {}).get('piel'):
            campos['piel'] = sin_tildes(dato('piel')).split()[0]
            campos['piel_fuente'] = 'lo eligió en el asistente'
        if dato('cumple') and not (ya or {}).get('cumple'):
            campos['cumple'] = dato('cumple')
        if not ya:
            campos['etapa'] = etapa
        mensaje_nuevo = dato('mensaje')
        nota = None
        if mensaje_nuevo and (not ya or ya.get('ultimo_mensaje') != mensaje_nuevo):
            nota = f'Escribió al asistente: «{mensaje_nuevo[:160]}»'
        c = guardar_clienta(datos, campos, nota)
        if mensaje_nuevo:
            c['ultimo_mensaje'] = mensaje_nuevo
        if ya and etapa == 'interesada' and c.get('etapa') in ('pregunto', 'pausa'):
            mover(datos, c, 'interesada')
        elif ya and c.get('etapa') == 'pausa' and nota:
            mover(datos, c, 'pregunto')   # volvió a escribir
        if ya:
            actualizadas += 1 if nota or campos.get('piel') else 0
        else:
            nuevas.append(c['nombre'])
    cfg.update({'hoja': origen if re.match(r'https?://', origen) else cfg.get('hoja', ''),
                'ultima': datetime.datetime.now().isoformat(timespec='minutes')})
    if re.match(r'https?://', origen) or not cfg.get('hoja'):
        guardar_config(cfg)
    return {'filas': len(filas), 'nuevas': nuevas, 'actualizadas': actualizadas}


def aplicar(datos, pedido):
    """Los cambios que hace Isabella desde la página."""
    accion = pedido.get('accion')
    if accion == 'clienta':
        return guardar_clienta(datos, pedido.get('clienta') or {}, pedido.get('nota'))
    if accion == 'borrar_clienta':
        return borrar_clienta(datos, pedido['id'])
    if accion == 'mover':
        c = buscar_clienta(datos, pedido['id'])
        if not c:
            raise ValueError('No encontré a esa clienta.')
        return mover(datos, c, pedido['etapa'])
    if accion == 'nota':
        c = buscar_clienta(datos, pedido['id'])
        if not c:
            raise ValueError('No encontré a esa clienta.')
        return anotar(c, pedido['texto'])
    if accion == 'seguimiento':
        c = buscar_clienta(datos, pedido['id'])
        if not c:
            raise ValueError('No encontré a esa clienta.')
        if pedido.get('fecha'):
            c['seguimiento'] = {'fecha': pedido['fecha'], 'motivo': pedido.get('motivo', '')}
        else:
            c.pop('seguimiento', None)
        return c
    if accion == 'pedido':
        return guardar_pedido(datos, pedido.get('pedido') or {})
    if accion == 'entregar':
        return entregar(datos, pedido['id'])
    if accion == 'pagado':
        p = next((x for x in datos['pedidos'] if x['id'] == pedido['id']), None)
        if p:
            p['pagado'] = bool(pedido.get('valor', True))
        return p
    if accion == 'borrar_pedido':
        return borrar_pedido(datos, pedido['id'])
    if accion == 'hecho':
        return marcar_hecho(datos, pedido['id'])
    if accion == 'deshacer':
        return deshacer(datos, pedido['id'])
    if accion == 'sincronizar':
        return sincronizar(datos)
    raise ValueError(f'No sé hacer «{accion}».')


def pagina_estatica(datos, destino):
    """La misma página, con los datos adentro, para verla sin el panel (no guarda cambios)."""
    html = PAGINA.read_text(encoding='utf-8')
    v = vista(datos)
    v['catalogo'] = [p for p in v['catalogo'] if any(sin_tildes(p['nombre']) == sin_tildes(x['nombre'])
                                                      for q in v['pedidos'] for x in q['productos'])]
    fotos = {}

    def adentro(ruta):
        """Las fotos de la computadora van dentro de la página (sin el panel no se pueden abrir)."""
        if not ruta.startswith('/archivo?ruta='):
            return ruta
        if ruta not in fotos:
            f = RAIZ / unquote(ruta[len('/archivo?ruta='):])
            fotos[ruta] = ('data:image/jpeg;base64,' + base64.b64encode(f.read_bytes()).decode()
                           if f.is_file() and f.stat().st_size < 400_000 else '')
        return fotos[ruta]
    for p in v['catalogo']:
        p['foto'] = adentro(p['foto'])
    for q in v['pedidos']:
        for x in q['productos']:
            if x.get('foto'):
                x['foto'] = adentro(x['foto'])
    for t in v['tareas']:
        if t.get('foto'):
            t['foto'] = adentro(t['foto'])
    for x in v['resumen']['top_productos']:
        x['foto'] = adentro(x.get('foto') or '')
    incrustado = json.dumps(v, ensure_ascii=False).replace('</', '<\\/')
    html = html.replace('window.LIBRETA_FIJA = null;', f'window.LIBRETA_FIJA = {incrustado};', 1)
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    Path(destino).write_text(html, encoding='utf-8')
    return destino


# ---------- ejemplo ----------

def demo(archivo):
    """Una libreta inventada para ver cómo se ve (no son clientas reales)."""
    d = nuevo()
    dia = hoy()
    hace = lambda n: (dia - datetime.timedelta(days=n)).isoformat()
    cumple_en = lambda n: (dia + datetime.timedelta(days=n)).strftime('%m-%d')
    ejemplo = [
        ('Carla Méndez', 'carla.mendez', 'instagram', '+1 305 555 0142', 'Miami', cumple_en(2), 'mixta', ['skincare'], 'fiel', 70),
        ('Daniela Ortiz', 'dani.ortiz', 'instagram', '', 'Houston', '', '', ['vitamina C'], 'pregunto', 5),
        ('Mariana López', 'marilopez', 'tiktok', '+1 713 555 0199', 'Dallas', cumple_en(25), 'seca', ['maquillaje'], 'entregado', 40),
        ('Sofía Ramírez', 'sofi.ramirez', 'instagram', '+1 407 555 0110', 'Orlando', '', 'sensible', ['té', 'bienestar'], 'pidio', 12),
        ('Valentina Cruz', 'vale.cruz', 'whatsapp', '+1 786 555 0175', 'Miami', cumple_en(0), 'mixta', ['labiales'], 'entregado', 50),
        ('Lucía Herrera', 'luciah', 'instagram', '', 'Chicago', '', '', ['sérum'], 'interesada', 2),
        ('Camila Torres', 'cami.torres', 'tiktok', '', 'Los Ángeles', '', 'grasa', ['acné'], 'pregunto', 1),
        ('Andrea Vega', 'andre.vega', 'instagram', '+1 305 555 0163', 'Miami', '', 'normal', ['rutina de noche'], 'fiel', 95),
        ('Paola Jiménez', 'pao.jimenez', 'facebook', '', 'Atlanta', '', '', [], 'pausa', 60),
    ]
    for nombre, u, red, tel, ciudad, cum, piel, intereses, etapa, dias in ejemplo:
        c = guardar_clienta(d, {'nombre': nombre, 'usuario': u, 'red': red, 'telefono': tel, 'ciudad': ciudad,
                                'cumple': cum, 'piel': piel, 'intereses': intereses,
                                'origen': 'comentario' if red != 'whatsapp' else 'recomendación'})
        c['creada'] = c['ultimo_contacto'] = hace(dias)
        c['historial'] = [{'fecha': hace(dias), 'texto': 'Entró a la libreta (vino por un comentario)'}]
        c['etapa'] = 'pregunto'
        if etapa in ('pregunto', 'interesada', 'pausa'):
            c['etapa'] = etapa
            c['historial'].append({'fecha': hace(dias), 'texto': f'Preguntó por {intereses[0] if intereses else "los productos"}'})
    foto = lambda slug: f'/archivo?ruta=agente-contenido/productos/{slug}/producto.jpg'
    serum = {'nombre': 'Dr. C. Tuna Vitamin C Glow Serum', 'foto': foto('vitamin-c-glow-serum')}
    crema = {'nombre': 'Dr. C. Tuna Tea Tree Face Cream', 'foto': foto('tea-tree-face-cream')}
    te = {'nombre': 'Nutriplus Serenity Earl Grey Tea', 'foto': foto('nutriplus-serenity-earl-grey-tea')}
    mascara = {'nombre': 'Dr. C. Tuna Age Reversist All Night Beauty Mask', 'foto': foto('dr-c-tuna-age-reversist-all-night-beauty-mask')}
    labial = {'nombre': 'Farmasi Matte Liquid Lipstick'}
    pedidos = [
        ('Carla Méndez', [serum], 25, 62, 60), ('Carla Méndez', [crema, mascara], 48, 20, 18),
        ('Mariana López', [labial, crema], 36, 38, 36), ('Sofía Ramírez', [te], 18, 1, None),
        ('Valentina Cruz', [serum], 25, 44, 42), ('Andrea Vega', [mascara], 30, 92, 90),
        ('Andrea Vega', [mascara, serum], 55, 34, 33), ('Andrea Vega', [te], 18, 8, 6),
    ]
    for quien, prods, total, hace_dias, entregado in pedidos:
        p = guardar_pedido(d, {'clienta': quien, 'productos': [dict(x) for x in prods], 'total': total,
                               'pagado': entregado is not None or quien == 'Sofía Ramírez', 'fecha': hace(hace_dias)})
        if entregado is not None:
            entregar(d, p['id'], hace(entregado))
    c = buscar_clienta(d, 'Daniela Ortiz')
    anotar(c, 'Preguntó si el sérum sirve para piel grasa', hace(5))
    c['publicacion'] = '3 mitos de la piel grasa'
    c = buscar_clienta(d, 'Lucía Herrera')
    c['seguimiento'] = {'fecha': dia.isoformat(), 'motivo': 'Escribirle: cobra el viernes y quiere el sérum'}
    guardar(d, archivo)
    return d


# ---------- programa ----------

def imprimir_tareas(lista):
    if not lista:
        print('Nada pendiente para hoy. 🌸')
        return
    iconos = {'recompra': '🔁', 'cumple': '🎂', 'entrega': '📦', 'opinion': '💬', 'seguimiento': '📌', 'frio': '👋'}
    for t in lista:
        print(f"{iconos.get(t['tipo'], '•')} {t['nombre']}: {t['titulo']}. {t['detalle']}")
        print(f"   Mensaje: {t['mensaje']}")
        if t['enlace']:
            print(f"   Abrir chat: {t['enlace']}")
        print(f"   (cuando esté hecho: libreta.py hecho {t['id']})")


def main():
    p = argparse.ArgumentParser(description='Libreta de clientas de Isabella')
    p.add_argument('--archivo', default=str(LIBRETA), help='otra libreta (por defecto clientas/datos/libreta.json)')
    sub = p.add_subparsers(dest='cmd', required=True)

    a = sub.add_parser('agregar', help='agrega o completa una clienta')
    for campo in ('nombre', 'usuario', 'red', 'telefono', 'ciudad', 'cumple', 'piel', 'tono', 'origen', 'etapa'):
        a.add_argument('--' + campo)
    a.add_argument('--interes', action='append', default=[], help='lo que le interesa (se puede repetir)')
    a.add_argument('--nota')

    e = sub.add_parser('editar', help='cambia datos de una clienta')
    e.add_argument('clienta')
    for campo in ('nombre', 'usuario', 'red', 'telefono', 'ciudad', 'cumple', 'piel', 'tono', 'origen', 'etapa', 'notas'):
        e.add_argument('--' + campo)

    n = sub.add_parser('nota', help='anota algo en el historial de una clienta')
    n.add_argument('clienta')
    n.add_argument('texto')

    et = sub.add_parser('etapa', help='mueve a una clienta de paso')
    et.add_argument('clienta')
    et.add_argument('etapa', choices=ID_ETAPAS)

    s = sub.add_parser('seguimiento', help='recordatorio para escribirle un día')
    s.add_argument('clienta')
    s.add_argument('--fecha', required=True)
    s.add_argument('--motivo', default='')

    pe = sub.add_parser('pedido', help='anota un pedido')
    pe.add_argument('clienta')
    pe.add_argument('--producto', action='append', required=True,
                    help='nombre del producto; "nombre x2" para 2; se puede repetir')
    pe.add_argument('--total', type=float, help='lo que cobró Isabella (opcional)')
    pe.add_argument('--pagado', action='store_true')
    pe.add_argument('--entregado', action='store_true')
    pe.add_argument('--fecha')
    pe.add_argument('--dias', type=int, help='cuántos días le dura (si no, se calcula)')
    pe.add_argument('--nota')

    en = sub.add_parser('entregado', help='el pedido ya se entregó')
    en.add_argument('pedido')

    h = sub.add_parser('hecho', help='una tarea de hoy ya se hizo')
    h.add_argument('tarea')

    sub.add_parser('hoy', help='lo que hay que hacer hoy')
    li = sub.add_parser('lista', help='todas las clientas')
    li.add_argument('--etapa', choices=ID_ETAPAS)
    b = sub.add_parser('buscar')
    b.add_argument('texto')
    sub.add_parser('resumen', help='números del negocio')
    sub.add_parser('ventas-csv', help='planificador/datos/ventas.csv para el estratega')
    pa = sub.add_parser('pagina', help='copia de la página para ver sin el panel')
    pa.add_argument('--salida', default=str(DATOS / 'libreta-vista.html'))
    sub.add_parser('demo', help='libreta de ejemplo en clientas/datos/demo.json')
    si = sub.add_parser('sincronizar', help='trae las clientas del asistente de mensajes (hoja de Google o archivo)')
    si.add_argument('origen', nargs='?', help='enlace de la hoja o archivo .csv (si no, la hoja ya conectada)')

    a_ = p.parse_args()
    archivo = Path(a_.archivo)
    if a_.cmd == 'demo':
        destino = archivo if a_.archivo != str(LIBRETA) else DATOS / 'demo.json'
        demo(destino)
        print(f'Libreta de ejemplo en {destino}')
        return
    datos = cargar(archivo)

    try:
        if a_.cmd == 'agregar':
            campos = {k: getattr(a_, k) for k in ('nombre', 'usuario', 'red', 'telefono', 'ciudad', 'cumple',
                                                   'piel', 'tono', 'origen', 'etapa')}
            campos['intereses'] = a_.interes
            nueva = not (buscar_clienta(datos, '@' + a_.usuario) if a_.usuario else None) and not (
                buscar_clienta(datos, a_.nombre) if a_.nombre else None)
            c = guardar_clienta(datos, campos, a_.nota)
            guardar(datos, archivo)
            print(f"{'Nueva clienta' if nueva else 'Ya estaba, la completé'}: {c['nombre']} ({c['id']}) · {c['etapa']}")
        elif a_.cmd == 'editar':
            c = buscar_clienta(datos, a_.clienta)
            if not c:
                sys.exit(f'No encontré a «{a_.clienta}».')
            campos = {k: getattr(a_, k) for k in ('nombre', 'usuario', 'red', 'telefono', 'ciudad', 'cumple', 'piel',
                                                   'tono', 'origen', 'etapa', 'notas') if getattr(a_, k)}
            campos['id'] = c['id']
            if 'nombre' in campos:
                c['nombre'] = campos.pop('nombre')
            guardar_clienta(datos, campos)
            guardar(datos, archivo)
            print(f"Listo: {c['nombre']} ({c['id']})")
        elif a_.cmd == 'nota':
            c = buscar_clienta(datos, a_.clienta)
            if not c:
                sys.exit(f'No encontré a «{a_.clienta}».')
            anotar(c, a_.texto)
            guardar(datos, archivo)
            print(f"Anotado en {c['nombre']}.")
        elif a_.cmd == 'etapa':
            c = buscar_clienta(datos, a_.clienta)
            if not c:
                sys.exit(f'No encontré a «{a_.clienta}».')
            mover(datos, c, a_.etapa)
            guardar(datos, archivo)
            print(f"{c['nombre']} → {a_.etapa}")
        elif a_.cmd == 'seguimiento':
            c = buscar_clienta(datos, a_.clienta)
            if not c:
                sys.exit(f'No encontré a «{a_.clienta}».')
            c['seguimiento'] = {'fecha': a_.fecha, 'motivo': a_.motivo}
            guardar(datos, archivo)
            print(f"Recordatorio para {c['nombre']} el {a_.fecha}.")
        elif a_.cmd == 'pedido':
            productos = []
            for x in a_.producto:
                m = re.match(r'(.+?)\s*[x×]\s*(\d+)$', x.strip())
                productos.append({'nombre': m.group(1) if m else x, 'cantidad': int(m.group(2)) if m else 1,
                                  'dias': a_.dias})
            cat = {sin_tildes(c['nombre']): c for c in catalogo()}
            for prod in productos:
                info = cat.get(sin_tildes(prod['nombre']))
                if info:
                    prod.setdefault('codigo', info['codigo'])
                    if info['foto']:
                        prod['foto'] = info['foto']
            pd = guardar_pedido(datos, {'clienta': a_.clienta, 'productos': productos, 'total': a_.total,
                                        'pagado': a_.pagado, 'fecha': a_.fecha, 'nota': a_.nota,
                                        'entregado': a_.entregado})
            guardar(datos, archivo)
            print(f"Pedido {pd['id']} anotado: {nombres_productos(pd['productos'])}")
        elif a_.cmd == 'entregado':
            pd = entregar(datos, a_.pedido)
            guardar(datos, archivo)
            print(f"Pedido {pd['id']} entregado.")
        elif a_.cmd == 'hecho':
            marcar_hecho(datos, a_.tarea)
            guardar(datos, archivo)
            print('Hecho. ✔')
        elif a_.cmd == 'hoy':
            imprimir_tareas(tareas(datos))
        elif a_.cmd in ('lista', 'buscar'):
            filtro = sin_tildes(getattr(a_, 'texto', ''))
            for c in vista(datos)['clientas']:
                if getattr(a_, 'etapa', None) and c.get('etapa') != a_.etapa:
                    continue
                linea = f"{c['id']:>4}  {c['nombre']}  @{c.get('usuario') or '-'}  {c.get('etapa')}  " \
                        f"{c['n_pedidos']} pedidos  {', '.join(c['productos'][:3])}"
                if filtro and filtro not in sin_tildes(linea + ' ' + json.dumps(c, ensure_ascii=False)):
                    continue
                print(linea)
        elif a_.cmd == 'resumen':
            r = resumen(datos)
            print(f"Clientas: {r['clientas']} ({r['nuevas_mes']} nuevas este mes) · compraron: {r['compradoras']} "
                  f"({r['conversion']}%) · volvieron a comprar: {r['fieles']}")
            print(f"Pedidos este mes: {r['pedidos_mes']}" + (f" · ventas anotadas: {r['ventas_mes']}" if r['ventas_mes'] is not None else '')
                  + f" · por entregar: {r['por_entregar']} · por cobrar: {r['por_cobrar']}")
            print('Por paso: ' + ', '.join(f'{k} {v}' for k, v in r['etapas'].items()))
            print('Lo que más se vende: ' + (', '.join(f"{x['nombre']} ×{x['cantidad']}" for x in r['top_productos']) or '—'))
        elif a_.cmd == 'ventas-csv':
            filas = [(p['fecha'], x.get('codigo'), x.get('cantidad', 1)) for p in datos['pedidos']
                     for x in p['productos'] if x.get('codigo')]
            VENTAS_CSV.parent.mkdir(parents=True, exist_ok=True)
            with VENTAS_CSV.open('w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(['fecha', 'codigo', 'cantidad'])
                w.writerows(filas)
            sin = sum(1 for p in datos['pedidos'] for x in p['productos'] if not x.get('codigo'))
            print(f'{len(filas)} ventas en {VENTAS_CSV}' + (f' ({sin} productos sin código de la tienda, no van)' if sin else ''))
        elif a_.cmd == 'sincronizar':
            r = sincronizar(datos, a_.origen)
            guardar(datos, archivo)
            print(f"{r['filas']} personas en la hoja · {len(r['nuevas'])} nuevas en la libreta"
                  + (f" ({', '.join(r['nuevas'][:8])})" if r['nuevas'] else '') + f" · {r['actualizadas']} actualizadas")
        elif a_.cmd == 'pagina':
            destino = pagina_estatica(datos, a_.salida)
            print(f'Página en {destino}')
            if COMPARTIDO.is_dir():
                copia = COMPARTIDO / 'clientas' / Path(a_.salida).name
                pagina_estatica(datos, copia)
                print(f'Copia en {copia}')
    except ValueError as err:
        sys.exit(str(err))


if __name__ == '__main__':
    main()
