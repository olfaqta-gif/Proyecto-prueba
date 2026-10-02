#!/usr/bin/env python3
"""Reunión de equipo de Isa: revisa el trabajo de cada agente, le pone nota, compara con
la reunión anterior y guarda los acuerdos para que el equipo mejore en cada reunión.

Uso (desde la carpeta del proyecto):
  python3 reunion/revisar.py reunir                    # revisa todo y arma el acta + informe visual
  python3 reunion/revisar.py nota <agente> "texto"     # comentario de Isa sobre un agente
  python3 reunion/revisar.py resumen "texto"           # lo que Isa le dice al equipo
  python3 reunion/revisar.py acuerdo <agente> "texto"  # compromiso para la próxima reunión
  python3 reunion/revisar.py cumplido <agente> <n>     # el acuerdo n se cumplió
  python3 reunion/revisar.py no-cumplido <agente> <n>  # no se cumplió (sigue activo)
  python3 reunion/revisar.py acuerdos <agente>         # lo que el agente lee antes de trabajar
  python3 reunion/revisar.py historial                 # notas de todas las reuniones

Queda en reunion/actas/<fecha>.json y su informe <fecha>.html (se abre en el navegador).
Los acuerdos viven en reunion/acuerdos.json. Solo usa la librería estándar de Python.
"""
import argparse
import base64
import datetime
import html
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
ACTAS = AQUI / 'actas'
ACUERDOS = AQUI / 'acuerdos.json'
COMPARTIDO = Path('/mnt/project-files')   # carpeta compartida del proyecto (si existe)

ANUNCIOS = RAIZ / 'agente-contenido' / 'productos'
SALIDA_ANUNCIOS = RAIZ / 'agente-contenido' / 'salida'
TEMAS = RAIZ / 'agente-educativo' / 'temas'
SALIDA_EDU = RAIZ / 'agente-educativo' / 'salida'
GUIONES = RAIZ / 'guionista' / 'guiones'
SALIDA_GUION = RAIZ / 'guionista' / 'salida'
PLANES = RAIZ / 'planificador' / 'planes'
LECTOR = RAIZ / 'lector-farmasi' / 'salida'
ANALISTA = RAIZ / 'analista'
COMUNIDAD = RAIZ / 'comunidad'
CLIENTAS = RAIZ / 'clientas'

ESTILOS = ('clasico', 'favorito', 'razones')
FORMAS_EDU = ('tips', 'mito', 'pasos', 'dato')
FORMATOS = ('9x16', '4x5', '1x1', '16x9')
# Quién hace cada tipo de publicación del plan (para repartir los resultados reales)
DUENO_TIPO = {'anuncio': 'creador-contenido', 'educativo': 'creador-educativo',
              'reel': 'guionista', 'historia': 'guionista', 'en-vivo': 'guionista'}
LLAMADO = re.compile(r'escr[ií]beme|cu[eé]ntame|coment|gu[aá]rdal|comp[aá]rtel|mensaje|link|preg[uú]ntame|dime', re.I)

HOY = datetime.date.today()


# ---------- utilidades ----------

def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def escribir_json(archivo, datos):
    Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    Path(archivo).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def cargar_modulo(nombre, archivo):
    """Usa las reglas y el equipo que ya existen (planificador y panel) sin copiarlos."""
    try:
        spec = importlib.util.spec_from_file_location(nombre, archivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception:   # noqa: BLE001 — si falla, la reunión sigue sin ese dato
        return None


PLANIFICAR = cargar_modulo('planificar', RAIZ / 'planificador' / 'planificar.py')
SERVIDOR = cargar_modulo('servidor_panel', RAIZ / 'panel' / 'servidor.py')
PROHIBIDO = PLANIFICAR.PROHIBIDO if PLANIFICAR else []


CON_FUENTE = re.compile(r'\([A-ZÁÉÍÓÚ][^)]{3,}\)')   # "(Skin Cancer Foundation)": un dato citado, no una promesa


def problemas_de_texto(texto):
    salida = []
    for patron, motivo in PROHIBIDO:
        lineas = [l for l in (texto or '').splitlines() if patron.search(l)]
        if 'porcentajes' in motivo:
            lineas = [l for l in lineas if not CON_FUENTE.search(l)]
        if lineas:
            salida.append(motivo)
    return salida


def textos(obj):
    """Todo el texto de una ficha (para buscar precios o promesas)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in ('aviso', 'carpeta', 'imagen', 'precio'):
                yield from textos(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from textos(v)


def revisar_caption(cap):
    """Revisa un caption: gancho corto, llamado a la acción, 5 a 12 hashtags y aviso."""
    if isinstance(cap, dict):
        texto, tags, aviso = cap.get('texto', ''), cap.get('hashtags') or [], cap.get('aviso', '')
    else:
        texto = cap or ''
        tags = re.findall(r'#\w+', texto)
        aviso = 'independiente' if 'independiente' in texto.lower() else ''
    primera = (texto.strip().splitlines() or [''])[0]
    pruebas = {
        'gancho corto (primera línea de 90 letras o menos)': 0 < len(primera) <= 90,
        'llamado a la acción (escríbeme, cuéntame…)': bool(LLAMADO.search(texto)),
        'entre 5 y 12 hashtags': 5 <= len(tags) <= 12,
        'aviso de distribuidora independiente': bool(aviso),
        'sin precios ni promesas': not problemas_de_texto(texto),
    }
    return pruebas


def carpetas_salida(*opciones):
    return [c for c in opciones if c and c.is_dir()]


def archivos(carpetas, patron):
    vistos, salida = set(), []
    for c in carpetas:
        for f in sorted(c.glob(patron)):
            clave = f.relative_to(c).as_posix()
            if clave not in vistos:
                vistos.add(clave)
                salida.append(f)
    return salida


def nota(valor):
    return round(max(0.0, min(10.0, valor)), 1)


def criterio(nombre, valor, detalle, mejorar=None, logro=None):
    """Un criterio con nota 0-10 (None = todavía no hay datos)."""
    return {'nombre': nombre, 'nota': None if valor is None else nota(valor), 'detalle': detalle,
            'mejorar': mejorar, 'logro': logro}


def ruta_rel(f):
    f = Path(f)
    try:
        return f.relative_to(RAIZ).as_posix()
    except ValueError:
        return f.as_posix()


def reciente(lista, n=6):
    return sorted(lista, key=lambda x: x[0].stat().st_mtime)[-n:]


# ---------- revisión de cada agente ----------

def revisar_creador_contenido():
    fichas = []
    for f in ANUNCIOS.glob('*/ficha.json'):
        d = leer_json(f)
        if isinstance(d, dict):
            fichas.append((f, d))
    if not fichas:
        return None
    fichas = reciente(fichas, 8)
    terminados, formatos, captions, problemas, muestras, usados = 0, [], [], [], [], set()
    for f, d in fichas:
        slug = f.parent.name
        salidas = carpetas_salida(SALIDA_ANUNCIOS / slug, COMPARTIDO / 'anuncios' / slug)
        videos = archivos(salidas, '**/anuncio*.mp4')
        if videos:
            terminados += 1
        hechos = {m.group(1) for v in videos if (m := re.search(r'anuncio-(\w+)\.mp4', v.name))}
        usados |= {v.parent.name for v in videos} & set(ESTILOS)
        usados |= {e for e in [d.get('estilo')] + list(d.get('estilos') or []) if e in ESTILOS}
        formatos.append(len(hechos & set(FORMATOS)) or (1 if videos else 0))
        if d.get('caption'):
            captions.append(revisar_caption(d['caption']))
        problemas += [f'{slug}: {p}' for t in textos(d) for p in problemas_de_texto(t)]
        previas = archivos(salidas, '**/previa*.jpg')
        if previas:
            muestras.append(ruta_rel(previas[0]))
        elif (f.parent / 'producto.jpg').exists():
            muestras.append(ruta_rel(f.parent / 'producto.jpg'))
    n = len(fichas)
    estilos = [d.get('estilo') or 'clasico' for _, d in fichas]
    paletas = [d.get('paleta') or '' for _, d in fichas]
    distintos = len(set(estilos) | usados)
    seguidos = max((len(list(g)) for g in _grupos(estilos)), default=0)
    pc = _promedio_pruebas(captions)
    criterios = [
        criterio('Trabajo terminado', 10 * terminados / n, f'{terminados} de {n} anuncios con video listo',
                 'Terminar los anuncios que quedaron sin video' if terminados < n else None,
                 'Todos los anuncios con su video' if terminados == n else None),
        criterio('Variedad de estilos', 10 * min(1, distintos / min(3, n)) - (2 if seguidos >= 3 else 0),
                 f'Estilos usados: {", ".join(sorted(set(estilos) | usados))} · paletas: {len(set(paletas))} distintas',
                 'Alternar los estilos clásico, favorito y razones (no repetir el mismo)' if distintos < min(3, n) or seguidos >= 3 else None,
                 'Usa los tres estilos' if distintos >= 3 else None),
        criterio('Formatos completos', 10 * sum(formatos) / (4 * n), f'{sum(formatos)} de {4 * n} formatos (9:16, 4:5, 1:1, 16:9)',
                 'Entregar los 4 formatos de cada anuncio' if sum(formatos) < 4 * n else None,
                 'Siempre en los 4 formatos' if sum(formatos) == 4 * n else None),
        _criterio_captions(pc, len(captions)),
        _criterio_reglas(problemas),
    ]
    return {'piezas': n, 'que': 'anuncios', 'criterios': criterios, 'muestras': muestras[-3:],
            'evidencia': [ruta_rel(f.parent) for f, _ in fichas]}


def revisar_creador_educativo():
    guiones = []
    for f in TEMAS.glob('*/guion.json'):
        d = leer_json(f)
        if isinstance(d, dict):
            guiones.append((f, d))
    if not guiones:
        return None
    guiones = reciente(guiones, 8)
    n = len(guiones)
    terminados, carruseles, captions, problemas, muestras, items = 0, 0, [], [], [], []
    for f, d in guiones:
        slug = f.parent.name
        salidas = carpetas_salida(SALIDA_EDU / slug, COMPARTIDO / 'educativos' / slug)
        if archivos(salidas, '*.mp4'):
            terminados += 1
        if archivos(salidas, 'carrusel/*.jpg'):
            carruseles += 1
        if d.get('caption'):
            captions.append(revisar_caption(d['caption']))
        problemas += [f'{slug}: {p}' for t in textos(d) for p in problemas_de_texto(t)]
        items.append(len(d.get('items') or []))
        previas = archivos(salidas, 'previa-9x16.jpg') or archivos(salidas, 'previa*.jpg')
        if previas:
            muestras.append(ruta_rel(previas[0]))
    formas = [d.get('tipo') or '' for _, d in guiones]
    distintas = len(set(formas) & set(FORMAS_EDU))
    pc = _promedio_pruebas(captions)
    ritmo = sum(1 for i in items if 2 <= i <= 6)
    criterios = [
        criterio('Trabajo terminado', 10 * terminados / n, f'{terminados} de {n} temas con video listo',
                 'Terminar los videos de los temas pendientes' if terminados < n else None,
                 'Todos los temas con su video' if terminados == n else None),
        criterio('Variedad de formas', 10 * min(1, distintas / min(4, n)), f'Formas: {_conteo(formas)}',
                 'Probar las formas que faltan (tips, mito, pasos, dato)' if distintas < min(4, n) else None,
                 'Usa todas las formas: tips, mito, pasos y dato' if distintas >= 4 else None),
        criterio('Ritmo (2 a 6 ideas por video)', 10 * ritmo / n, f'{ritmo} de {n} videos con 2 a 6 ideas',
                 'Dejar cada video entre 2 y 6 ideas para que se entienda' if ritmo < n else None),
        _criterio_captions(pc, len(captions)),
        _criterio_reglas(problemas),
    ]
    return {'piezas': n, 'que': 'videos educativos', 'extra': f'{carruseles} con carrusel',
            'criterios': criterios, 'muestras': muestras[-3:], 'evidencia': [ruta_rel(f.parent) for f, _ in guiones]}


def revisar_guionista():
    guiones = []
    for f in GUIONES.glob('*/guion.json'):
        d = leer_json(f)
        if isinstance(d, dict):
            guiones.append((f, d))
    if not guiones:
        return None
    guiones = reciente(guiones, 8)
    n = len(guiones)
    terminados, ganchos, duraciones, captions, problemas, huecos, muestras = 0, 0, 0, [], [], 0, []
    for f, d in guiones:
        slug = f.parent.name
        salidas = carpetas_salida(SALIDA_GUION / slug, COMPARTIDO / 'guiones' / slug)
        if archivos(salidas, 'hoja.html'):
            terminados += 1
        tomas = d.get('tomas') or []
        if tomas and len((tomas[0].get('dice') or '').split()) <= 12 and (tomas[0].get('segundos') or 3) <= 3:
            ganchos += 1
        total, meta = sum(t.get('segundos') or 0 for t in tomas), d.get('duracion_objetivo')
        if not meta or (total and abs(total - meta) <= 0.25 * meta):
            duraciones += 1
        if d.get('caption'):
            captions.append(revisar_caption(d['caption']))
        problemas += [f'{slug}: {p}' for t in textos(d) for p in problemas_de_texto(t)]
        huecos += sum(t.count('[completa') for t in textos(d))
        vistas = archivos(salidas, 'vista-hoja.png')
        if vistas:
            muestras.append(ruta_rel(vistas[0]))
    formatos = [d.get('formato') or '' for _, d in guiones]
    pc = _promedio_pruebas(captions)
    criterios = [
        criterio('Trabajo terminado', 10 * terminados / n, f'{terminados} de {n} guiones con hoja de grabación',
                 'Entregar siempre la hoja de grabación y el teleprompter' if terminados < n else None),
        criterio('Gancho en 3 segundos', 10 * ganchos / n, f'{ganchos} de {n} guiones empiezan con una frase corta',
                 'Abrir con una frase de 12 palabras o menos en los primeros 3 segundos' if ganchos < n else None,
                 'Ganchos cortos y directos' if ganchos == n else None),
        criterio('Duración justa', 10 * duraciones / n, f'{duraciones} de {n} duran lo que se planeó',
                 'Ajustar las tomas a la duración que se planeó' if duraciones < n else None),
        criterio('Variedad de formatos', 10 * min(1, len(set(formatos)) / min(4, n)), f'Formatos: {_conteo(formatos)}',
                 'Probar otros formatos (lo probé, tutorial, mis favoritos…)' if len(set(formatos)) < min(4, n) else None),
        _criterio_captions(pc, len(captions)),
        _criterio_reglas(problemas),
    ]
    return {'piezas': n, 'que': 'guiones', 'extra': f'{huecos} partes para que Isabella complete' if huecos else '',
            'criterios': criterios, 'muestras': muestras[-3:], 'evidencia': [ruta_rel(f.parent) for f, _ in guiones]}


def revisar_estratega():
    planes = []
    for f in PLANES.glob('*.json'):
        d = leer_json(f)
        if isinstance(d, dict) and d.get('publicaciones'):
            planes.append((f, d))
    if not planes:
        return None
    planes.sort(key=lambda x: x[1].get('inicio', ''))
    f, plan = planes[-1]
    pubs = plan['publicaciones']
    fin = max((p.get('fecha', '') for p in pubs), default='')
    vigente = fin >= HOY.isoformat()
    # Mezcla de pilares: lo planeado contra lo que dicen los porcentajes
    meta = {p.get('id'): p.get('porcentaje') or 0 for p in plan.get('pilares', [])}
    real = Counter(p.get('pilar') for p in pubs)
    desvio = sum(abs(100 * real.get(k, 0) / len(pubs) - v) for k, v in meta.items()) / 2 if meta else 0
    # Avance: publicaciones con fecha pasada que ya se hicieron
    pasadas = [p for p in pubs if p.get('fecha', '9') < HOY.isoformat()]
    hechas = [p for p in pasadas if p.get('estado') in ('hecho', 'publicado')]
    publicadas = [p for p in pubs if p.get('estado') == 'publicado']
    con_resultado = [p for p in publicadas if p.get('resultados')]
    errores, avisos = (PLANIFICAR.revisar(plan) if PLANIFICAR else ([], []))
    tipos = Counter(p.get('tipo') for p in pubs)
    criterios = [
        criterio('Plan al día', 10 if vigente else 3, f'«{plan.get("nombre", f.stem)}» va hasta el {fin}',
                 None if vigente else 'Armar el plan de las próximas semanas', 'Hay plan para las próximas semanas' if vigente else None),
        criterio('Equilibrio de pilares', 10 - desvio / 3, f'Se aleja {round(desvio)} puntos de los porcentajes que eligió',
                 'Repartir las publicaciones según los porcentajes de cada pilar' if desvio > 10 else None,
                 'Pilares bien repartidos' if desvio <= 5 else None),
        criterio('Avance del plan', 10 * len(hechas) / len(pasadas) if pasadas else None,
                 f'{len(hechas)} de {len(pasadas)} publicaciones con fecha pasada ya hechas' if pasadas else 'El plan todavía no empieza',
                 'Recordar a Isa las publicaciones atrasadas' if pasadas and len(hechas) < len(pasadas) else None),
        criterio('Aprende de los resultados', 10 * len(con_resultado) / len(publicadas) if publicadas else None,
                 f'{len(con_resultado)} de {len(publicadas)} publicadas tienen vistas o mensajes' if publicadas else 'Todavía no hay publicaciones publicadas',
                 'Pedir a Isabella cómo le fue a cada publicación' if publicadas and len(con_resultado) < len(publicadas) else None),
        criterio('Reglas', 10 - 3 * len(errores) - 0.5 * len(avisos), f'{len(errores)} errores y {len(avisos)} avisos al revisar el plan' + (f' (ej.: {(errores + avisos)[0]})' if errores or avisos else ''),
                 'Dejar el plan sin avisos al revisarlo' if errores or avisos else None, 'El plan pasa la revisión sin avisos' if not errores and not avisos else None),
    ]
    return {'piezas': len(pubs), 'que': 'publicaciones planeadas', 'extra': _conteo([p.get('tipo') for p in pubs]),
            'criterios': criterios, 'muestras': [ruta_rel(f.with_suffix('.html'))] if f.with_suffix('.html').exists() else [],
            'evidencia': [ruta_rel(f)], 'tipos': dict(tipos)}


def revisar_scraper():
    fichas = {}
    for base in (LECTOR, ANUNCIOS):
        for f in base.glob('*/datos.json'):
            d = leer_json(f)
            if isinstance(d, dict):
                fichas.setdefault(f.parent.name, (f, d))
    catalogo = leer_json(LECTOR / 'catalogo.json')
    if not fichas and not catalogo:
        return None
    campos = ('nombre', 'descripcion', 'ingredientes_inci', 'resenas', 'imagen')
    completas = sum(1 for f, d in fichas.values() if all(d.get(c) for c in campos) and (f.parent / 'producto.jpg').exists())
    leido = None
    if isinstance(catalogo, dict) and catalogo.get('leido'):
        try:
            leido = datetime.date.fromisoformat(catalogo['leido'][:10])
        except ValueError:
            pass
    dias = (HOY - leido).days if leido else None
    n = len(fichas)
    criterios = [
        criterio('Catálogo al día', None if dias is None else 10 - max(0, dias - 7) * 0.7,
                 f'Catálogo leído hace {dias} días' if dias is not None else 'Todavía no leyó el catálogo completo',
                 'Volver a leer el catálogo (tiene más de una semana)' if dias is not None and dias > 7 else
                 ('Leer el catálogo completo para el estratega' if dias is None else None),
                 'Catálogo fresco' if dias is not None and dias <= 7 else None),
        criterio('Fichas completas', 10 * completas / n if n else None,
                 f'{completas} de {n} productos con descripción, ingredientes, reseñas y foto',
                 'Completar los datos que faltan en las fichas' if n and completas < n else None,
                 'Fichas completas con foto' if n and completas == n else None),
    ]
    return {'piezas': n, 'que': 'productos investigados', 'criterios': criterios,
            'muestras': [ruta_rel(f.parent / 'producto.jpg') for f, _ in list(fichas.values())[-3:] if (f.parent / 'producto.jpg').exists()],
            'evidencia': [ruta_rel(f.parent) for f, _ in fichas.values()]}


def revisar_analista():
    pubs = leer_json(ANALISTA / 'datos' / 'publicaciones.json', []) or []
    informes = sorted((ANALISTA / 'informes').glob('*.json'))
    if not pubs and not informes:
        return None
    ultimo = leer_json(informes[-1], {}) if informes else {}
    try:
        dias = max(0, (HOY - datetime.date.fromisoformat(informes[-1].stem[:10])).days) if informes else None
    except ValueError:
        dias = None
    completas = sum(1 for x in pubs if all(x.get(k) is not None for k in ('vistas', 'me_gusta', 'guardados', 'compartidos')))
    # Publicaciones del plan ya publicadas: ¿la Analista tiene sus números?
    publicadas = [(f, x) for f in PLANES.glob('*.json') for x in (leer_json(f, {}) or {}).get('publicaciones', [])
                  if x.get('estado') == 'publicado']
    medidas = sum(1 for _, x in publicadas if x.get('resultados'))
    consejos = (ultimo or {}).get('consejos', [])
    sin_leer = [f for f in (ANALISTA / 'capturas').glob('*') if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.heic', '.webp')]
    criterios = [
        criterio('Informe al día', None if dias is None else 10 - max(0, dias - 7) * 0.7,
                 f'Último informe hace {dias} días' if dias is not None else 'Todavía no hizo un informe',
                 'Hacer el informe de redes cada semana' if dias is None or dias > 7 else None,
                 'Informe de esta semana listo' if dias is not None and dias <= 7 else None),
        criterio('Capturas leídas', 10 if not sin_leer else max(0, 10 - 2 * len(sin_leer)),
                 f'{len(sin_leer)} capturas esperando' if sin_leer else 'Todas las capturas leídas',
                 'Leer las capturas que mandó Isabella' if sin_leer else None),
        criterio('Números completos', 10 * completas / len(pubs) if pubs else None,
                 f'{completas} de {len(pubs)} publicaciones con vistas, me gusta, guardados y compartidos',
                 'Sacar de las capturas todos los números (también guardados y compartidos)' if pubs and completas < len(pubs) else None),
        criterio('Plan medido', 10 * medidas / len(publicadas) if publicadas else None,
                 f'{medidas} de {len(publicadas)} publicaciones del plan con resultados' if publicadas else 'Todavía no hay publicaciones del plan publicadas',
                 'Pedir las capturas de las publicaciones del plan que faltan' if publicadas and medidas < len(publicadas) else None),
        criterio('Consejos para el equipo', min(10, 2.5 * len(consejos)) if ultimo else None,
                 f'{len(consejos)} consejos en el último informe' if ultimo else 'Sin informe',
                 'Dejar consejos concretos para cada agente' if ultimo and len(consejos) < 3 else None),
    ]
    muestras = [ruta_rel(informes[-1].with_suffix('.html'))] if informes and informes[-1].with_suffix('.html').exists() else []
    return {'piezas': len(pubs), 'que': 'publicaciones medidas', 'criterios': criterios, 'muestras': muestras,
            'evidencia': [ruta_rel(f) for f in informes[-3:]]}


def revisar_comunidad():
    historial = leer_json(COMUNIDAD / 'datos' / 'historial.json', []) or []
    libreta = None
    if (CLIENTAS / 'libreta.py').exists() and (CLIENTAS / 'datos' / 'libreta.json').exists():
        spec = importlib.util.spec_from_file_location('libreta', CLIENTAS / 'libreta.py')
        libreta = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(libreta)
    if not historial and not libreta:
        return None
    sin_leer = [f for f in (COMUNIDAD / 'capturas').glob('*') if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.heic', '.webp')]
    recientes = historial[-5:]
    total = sum(h['total'] for h in recientes)
    avisos = sum(h.get('avisos', 0) for h in recientes)
    interesadas = sum(v for h in recientes for k, v in h.get('intenciones', {}).items()
                      if k in ('comprar', 'precio', 'producto', 'envio', 'negocio', 'queja'))
    anotadas = sum(h.get('anotadas', 0) for h in recientes)
    vencidas, tareas = [], []
    if libreta:
        tareas = libreta.tareas(libreta.cargar())
        vencidas = [t for t in tareas if t['urgencia'] >= 3]
    try:
        dias = (HOY - datetime.date.fromisoformat(historial[-1]['fecha'])).days if historial else None
    except (KeyError, ValueError):
        dias = None
    criterios = [
        criterio('Mensajes al día', 10 if not sin_leer else max(0, 10 - 2 * len(sin_leer)),
                 f'{len(sin_leer)} capturas de mensajes esperando' if sin_leer else
                 (f'Última hoja de respuestas hace {dias} días' if dias is not None else 'Sin capturas pendientes'),
                 'Responder las capturas de mensajes que mandó Isabella' if sin_leer else None,
                 'Ningún mensaje esperando' if not sin_leer and historial else None),
        criterio('Respuestas en regla', 10 * (1 - avisos / total) if total else None,
                 f'{total - avisos} de {total} respuestas sin nada que corregir (precios, promesas, huecos)' if total else 'Todavía no hay respuestas',
                 'Revisar que ninguna respuesta tenga precios inventados ni promesas' if avisos else None,
                 'Respuestas sin promesas ni precios inventados' if total and not avisos else None),
        criterio('Interesadas en la libreta', min(10, 10 * anotadas / interesadas) if interesadas else None,
                 f'{anotadas} de {interesadas} personas interesadas quedaron anotadas' if interesadas else 'Sin personas interesadas todavía',
                 'Anotar en la libreta a cada persona que pregunta o quiere comprar' if interesadas and anotadas < interesadas else None),
        criterio('Clientas atendidas a tiempo', max(0, 10 - 1.5 * len(vencidas)) if libreta else None,
                 f'{len(vencidas)} tareas de la libreta atrasadas o para hoy ({len(tareas)} en total)' if libreta else 'Sin libreta todavía',
                 'Recordarle a Isabella las clientas a las que se les acabó el producto o cumplen años' if len(vencidas) > 2 else None,
                 'Ninguna clienta olvidada' if libreta and not vencidas else None),
    ]
    muestras = [h['hoja'] for h in historial[-2:] if (RAIZ / h['hoja']).exists()]
    return {'piezas': sum(h['total'] for h in historial), 'que': 'mensajes respondidos', 'criterios': criterios,
            'muestras': muestras, 'evidencia': muestras}


REVISORES = {
    'comunidad-ventas': revisar_comunidad,
    'scraper-farmasi': revisar_scraper,
    'estratega-contenido': revisar_estratega,
    'creador-contenido': revisar_creador_contenido,
    'creador-educativo': revisar_creador_educativo,
    'guionista': revisar_guionista,
    'analista-redes': revisar_analista,
}


def _grupos(lista):
    from itertools import groupby
    return [list(g) for _, g in groupby(lista)]


def _conteo(lista):
    c = Counter(x for x in lista if x)
    return ', '.join(f'{k} ×{v}' for k, v in c.most_common()) or '—'


def _promedio_pruebas(lista):
    if not lista:
        return {}
    return {k: sum(1 for p in lista if p[k]) / len(lista) for k in lista[0]}


def _criterio_captions(pc, n):
    if not pc:
        return criterio('Captions', None, 'Sin captions para revisar')
    falla = min(pc, key=pc.get)
    return criterio('Captions', 10 * sum(pc.values()) / len(pc),
                    f'{n} captions revisados · ' + ', '.join(f'{k.split(" (")[0]}: {round(100 * v)}%' for k, v in pc.items()),
                    f'Captions con {falla}' if pc[falla] < 1 else None,
                    'Captions completos: gancho, llamado, hashtags y aviso' if all(v == 1 for v in pc.values()) else None)


def _criterio_reglas(problemas):
    return criterio('Reglas (sin precios ni promesas)', 10 - 3 * len(problemas),
                    'Todo en regla' if not problemas else '; '.join(problemas[:3]),
                    'Revisar que no haya precios, porcentajes ni promesas antes de entregar' if problemas else None, 'Sin precios ni promesas' if not problemas else None)


# ---------- resultados reales y acuerdos ----------

def resultados_reales():
    filas = {}
    for f in PLANES.glob('*.json'):
        plan = leer_json(f, {}) or {}
        for p in plan.get('publicaciones', []):
            r = p.get('resultados')
            if not r:
                continue
            tipo = p.get('tipo') or 'otro'
            t = filas.setdefault(tipo, {'tipo': tipo, 'agente': DUENO_TIPO.get(tipo, ''), 'publicaciones': 0,
                                        'vistas': 0, 'mensajes': 0, 'ventas': 0})
            t['publicaciones'] += 1
            for k in ('vistas', 'mensajes', 'ventas'):
                t[k] += r.get(k) or 0
    # Lo que la Analista guardó de publicaciones que no estaban en un plan
    for p in leer_json(ANALISTA / 'datos' / 'publicaciones.json', []) or []:
        if p.get('plan') or not any(p.get(k) for k in ('vistas', 'mensajes', 'ventas')):
            continue
        tipo = p.get('tipo') or 'otro'
        t = filas.setdefault(tipo, {'tipo': tipo, 'agente': DUENO_TIPO.get(tipo, ''), 'publicaciones': 0,
                                    'vistas': 0, 'mensajes': 0, 'ventas': 0})
        t['publicaciones'] += 1
        for k in ('vistas', 'mensajes', 'ventas'):
            t[k] += p.get(k) or 0
    return sorted(filas.values(), key=lambda x: -x['mensajes'] / max(1, x['publicaciones']))


def criterio_resultados(agente, reales):
    mias = [r for r in reales if r['agente'] == agente]
    if not mias or not reales:
        return None
    por_pub = lambda filas: sum(r['mensajes'] for r in filas) / max(1, sum(r['publicaciones'] for r in filas))
    mio, equipo = por_pub(mias), por_pub(reales)
    valor = 7 if not equipo else 7 + 3 * (mio - equipo) / equipo
    return criterio('Resultados reales', valor, f'{mio:.1f} mensajes por publicación (equipo: {equipo:.1f})',
                    'Revisar qué tienen las publicaciones que más mensajes traen y repetirlo' if mio < equipo else None,
                    'Sus publicaciones traen más mensajes que el promedio' if mio > equipo else None)


def leer_acuerdos():
    datos = leer_json(ACUERDOS, {}) or {}
    return datos if isinstance(datos, dict) else {}


def acuerdos_activos(agente, todos=None):
    return [a for a in (todos or leer_acuerdos()).get(agente, []) if a.get('estado') == 'activo']


# ---------- la reunión ----------

def equipo_del_panel():
    """Nombres, colores y caras de los robots: los mismos que se ven en la oficina."""
    if SERVIDOR:
        try:
            return {a['id']: a for a in SERVIDOR.equipo()['agentes']}
        except Exception:   # noqa: BLE001
            pass
    agentes = {}
    for f in sorted((RAIZ / '.claude' / 'agents').glob('*.md')):
        agentes[f.stem] = {'id': f.stem, 'nombre': f.stem.replace('-', ' ').title(), 'color': '#4cc9ff', 'cara': 0}
    return agentes


def actas_anteriores(antes_de):
    salida = []
    for f in sorted(ACTAS.glob('*.json')):
        if f.stem < antes_de:
            d = leer_json(f)
            if isinstance(d, dict):
                salida.append(d)
    return salida


def promedio(valores):
    valores = [v for v in valores if v is not None]
    return round(sum(valores) / len(valores), 1) if valores else None


def reunir(fecha):
    equipo = equipo_del_panel()
    reales = resultados_reales()
    acuerdos = leer_acuerdos()
    anteriores = actas_anteriores(fecha)
    previa = anteriores[-1] if anteriores else None
    viejo = leer_json(ACTAS / f'{fecha}.json', {}) or {}   # si ya hubo reunión hoy, se guardan las notas de Isa
    agentes = {}
    for id_, info in equipo.items():
        revisor = REVISORES.get(id_)
        r = revisor() if revisor else None
        if r is None:
            r = {'piezas': 0, 'que': 'trabajos', 'criterios': [], 'muestras': [], 'evidencia': [],
                 'sin_datos': 'Todavía no hay trabajo suyo para revisar' if revisor else
                 'Agente nuevo: Isa lo revisa a mano hasta que tenga su propia revisión'}
        extra = criterio_resultados(id_, reales)
        if extra:
            r['criterios'].append(extra)
        r['nota'] = promedio(c['nota'] for c in r['criterios'])
        anterior = (previa or {}).get('agentes', {}).get(id_, {})
        r['nota_anterior'] = anterior.get('nota')
        r['historial'] = [a['agentes'][id_]['nota'] for a in anteriores if id_ in a.get('agentes', {})] + [r['nota']]
        r['logros'] = [c['logro'] for c in r['criterios'] if c.get('logro') and c['nota'] is not None and c['nota'] >= 9]
        r['mejorar'] = [c['mejorar'] for c in sorted(r['criterios'], key=lambda c: c['nota'] if c['nota'] is not None else 99)
                        if c.get('mejorar') and c['nota'] is not None and c['nota'] < 8.5]
        activos = acuerdos_activos(id_, acuerdos)
        # Propuestas de acuerdo: lo peor evaluado que todavía no es un acuerdo
        r['propuestas'] = [m for m in r['mejorar'] if not any(m.lower() == a['texto'].lower() for a in activos)][:2]
        r['nombre'], r['color'], r['cara'] = info.get('nombre', id_), info.get('color', '#4cc9ff'), info.get('cara', 0)
        r['comentario_isa'] = (viejo.get('agentes', {}).get(id_) or {}).get('comentario_isa', '')
        agentes[id_] = r
    nota_equipo = promedio(a['nota'] for a in agentes.values())
    todos_acuerdos = [dict(a, agente=k) for k, lista in acuerdos.items() for a in lista]
    acta = {
        'fecha': fecha,
        'hora': datetime.datetime.now().strftime('%H:%M'),
        'nota_equipo': nota_equipo,
        'nota_equipo_anterior': (previa or {}).get('nota_equipo'),
        'historial_equipo': [{'fecha': a['fecha'], 'nota': a.get('nota_equipo')} for a in anteriores] + [{'fecha': fecha, 'nota': nota_equipo}],
        'piezas': sum(a['piezas'] for a in agentes.values() if a['que'] not in ('publicaciones planeadas', 'productos investigados', 'publicaciones medidas', 'mensajes respondidos')),
        'resultados': reales,
        'acuerdos': {'activos': sum(1 for a in todos_acuerdos if a['estado'] == 'activo'),
                     'cumplidos': sum(1 for a in todos_acuerdos if a['estado'] == 'cumplido')},
        'resumen_isa': viejo.get('resumen_isa', ''),
        'agentes': agentes,
    }
    return acta


# ---------- informe visual ----------

def svg_robot(color, cara, tam=64):
    """Un robot parecido a los de la oficina 3D, con el color de su luz."""
    cabeza = [
        '<ellipse cx="32" cy="27" rx="21" ry="18" fill="#f5f8fd" stroke="#c9d6ee" stroke-width="1.5"/>',
        '<rect x="11" y="10" width="42" height="33" rx="9" fill="#f5f8fd" stroke="#c9d6ee" stroke-width="1.5"/>',
        '<rect x="9" y="12" width="46" height="30" rx="15" fill="#f5f8fd" stroke="#c9d6ee" stroke-width="1.5"/>',
        '<path d="M12 30 Q12 8 32 8 Q52 8 52 30 L52 40 Q52 44 48 44 L16 44 Q12 44 12 40 Z" fill="#f5f8fd" stroke="#c9d6ee" stroke-width="1.5"/>',
    ][int(cara or 0) % 4]
    return (f'<svg viewBox="0 0 64 64" width="{tam}" height="{tam}" aria-hidden="true">'
            f'<line x1="32" y1="2" x2="32" y2="10" stroke="#27324d" stroke-width="2"/><circle cx="32" cy="3" r="3" fill="{color}"/>'
            f'<circle cx="9" cy="28" r="5" fill="{color}"/><circle cx="55" cy="28" r="5" fill="{color}"/>{cabeza}'
            '<rect x="17" y="19" width="30" height="15" rx="7.5" fill="#0b1426"/>'
            f'<rect x="22" y="23" width="5" height="7" rx="2.5" fill="{color}"/><rect x="37" y="23" width="5" height="7" rx="2.5" fill="{color}"/>'
            f'<path d="M14 64 Q14 48 32 48 Q50 48 50 64 Z" fill="#f5f8fd" stroke="#c9d6ee" stroke-width="1.5"/>'
            f'<circle cx="32" cy="56" r="3.5" fill="{color}"/></svg>')


def anillo(valor, color, tam=92, grosor=9):
    r = (tam - grosor) / 2
    largo = 2 * 3.14159 * r
    parte = largo * (valor or 0) / 10
    texto = '–' if valor is None else f'{valor:.1f}'
    return (f'<svg class="anillo" viewBox="0 0 {tam} {tam}" width="{tam}" height="{tam}" role="img" aria-label="Nota {texto} de 10">'
            f'<circle cx="{tam / 2}" cy="{tam / 2}" r="{r}" fill="none" stroke="var(--pista)" stroke-width="{grosor}"/>'
            f'<circle cx="{tam / 2}" cy="{tam / 2}" r="{r}" fill="none" stroke="{color}" stroke-width="{grosor}" stroke-linecap="round" '
            f'stroke-dasharray="{parte:.1f} {largo:.1f}" transform="rotate(-90 {tam / 2} {tam / 2})"/>'
            f'<text x="50%" y="52%" text-anchor="middle" dominant-baseline="middle" class="anillo-num">{texto}</text></svg>')


def flecha(ahora, antes):
    if ahora is None or antes is None:
        return '<span class="tend nueva">primera reunión</span>'
    d = round(ahora - antes, 1)
    if abs(d) < 0.1:
        return '<span class="tend igual">= igual que la vez pasada</span>'
    return f'<span class="tend {"sube" if d > 0 else "baja"}">{"▲" if d > 0 else "▼"} {abs(d):.1f} vs. la vez pasada</span>'


def incrustar(ruta, ancho_max=60_000):
    """Mete la imagen en el informe para que se vea aunque el archivo se mueva."""
    f = Path(ruta) if Path(ruta).is_absolute() else RAIZ / ruta
    if not f.is_file() or f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp') or f.stat().st_size > 900_000:
        return None
    tipo = {'.png': 'png', '.webp': 'webp'}.get(f.suffix.lower(), 'jpeg')
    return f'data:image/{tipo};base64,' + base64.b64encode(f.read_bytes()).decode()


def linea_tiempo(puntos, color, ancho=560, alto=150):
    """Línea de la nota del equipo en cada reunión."""
    validos = [(i, p) for i, p in enumerate(puntos) if p.get('nota') is not None]
    if not validos:
        return ''
    n = max(1, len(puntos) - 1)
    x = lambda i: 40 + (ancho - 60) * (i / n if len(puntos) > 1 else 0.5)
    y = lambda v: 14 + (alto - 40) * (1 - v / 10)
    guias = ''.join(f'<line x1="40" x2="{ancho - 20}" y1="{y(v)}" y2="{y(v)}" class="guia"/><text x="30" y="{y(v) + 4}" class="eje" text-anchor="end">{v}</text>'
                    for v in (0, 5, 10))
    camino = ' '.join(f'{"M" if k == 0 else "L"}{x(i):.1f},{y(p["nota"]):.1f}' for k, (i, p) in enumerate(validos))
    puntos_svg = ''.join(
        f'<g class="pt" data-tip="{html.escape(p["fecha"])} · nota {p["nota"]}"><circle cx="{x(i):.1f}" cy="{y(p["nota"]):.1f}" r="14" fill="transparent"/>'
        f'<circle cx="{x(i):.1f}" cy="{y(p["nota"]):.1f}" r="5" fill="{color}" stroke="var(--superficie)" stroke-width="2"/></g>'
        f'<text x="{x(i):.1f}" y="{alto - 6}" class="eje" text-anchor="middle">{html.escape(p["fecha"][5:])}</text>' for i, p in validos)
    ultima = validos[-1]
    return (f'<svg viewBox="0 0 {ancho} {alto}" class="grafico" role="img" aria-label="Nota del equipo en cada reunión">{guias}'
            f'<path d="{camino}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>{puntos_svg}'
            f'<text x="{x(ultima[0]) + 9:.1f}" y="{y(ultima[1]["nota"]) - 9:.1f}" class="etq-dato">{ultima[1]["nota"]}</text></svg>')


def barras_produccion(agentes):
    filas = [(a['nombre'], a['piezas'], a['que'], a['color']) for a in agentes.values() if a['piezas']]
    if not filas:
        return '<p class="vacio">Todavía no hay trabajos.</p>'
    maximo = max(f[1] for f in filas)
    return '<div class="barras">' + ''.join(
        f'<div class="fila-barra" data-tip="{html.escape(n)}: {v} {html.escape(q)}"><span class="nom">{html.escape(n)}</span>'
        f'<span class="pista"><i style="width:{100 * v / maximo:.0f}%;background:{c}"></i></span><span class="val">{v} <small>{html.escape(q)}</small></span></div>'
        for n, v, q, c in sorted(filas, key=lambda f: -f[1])) + '</div>'


def barras_resultados(reales, agentes):
    if not reales:
        return ('<p class="vacio">Aún no hay resultados de publicaciones. Cuando Isabella publique, cuéntale a Isa '
                'cuántas vistas, mensajes y ventas tuvo cada una: así el equipo aprende qué funciona.</p>')
    maximo = max(r['mensajes'] / max(1, r['publicaciones']) for r in reales) or 1
    salida = '<div class="barras">'
    for r in reales:
        prom = r['mensajes'] / max(1, r['publicaciones'])
        color = agentes.get(r['agente'], {}).get('color', '#7f8fa9')
        salida += (f'<div class="fila-barra" data-tip="{html.escape(r["tipo"])}: {r["publicaciones"]} publicaciones · {r["vistas"]} vistas · '
                   f'{r["mensajes"]} mensajes · {r["ventas"]} ventas"><span class="nom">{html.escape(r["tipo"])}</span>'
                   f'<span class="pista"><i style="width:{100 * prom / maximo:.0f}%;background:{color}"></i></span>'
                   f'<span class="val">{prom:.1f} <small>mensajes por publicación</small></span></div>')
    return salida + '</div>'


def tarjeta_agente(id_, a, acuerdos):
    color = a['color']
    crit = ''.join(
        f'<li data-tip="{html.escape(c["detalle"])}"><span>{html.escape(c["nombre"])}</span>'
        + (f'<span class="mini"><i style="width:{10 * c["nota"]:.0f}%;background:{color}"></i></span><b>{c["nota"]:.1f}</b>'
           if c['nota'] is not None else '<span class="mini"></span><b class="nd">sin datos</b>') + '</li>'
        for c in a['criterios'])
    fotos = ''.join(f'<img src="{src}" alt="" loading="lazy">' for src in filter(None, (incrustar(m) for m in a['muestras'])))
    logros = ''.join(f'<li>{html.escape(t)}</li>' for t in a['logros'][:3])
    mejorar = ''.join(f'<li>{html.escape(t)}</li>' for t in a['mejorar'][:3])
    mios = acuerdos.get(id_, [])
    acu = ''.join(f'<li class="{x["estado"]}"><span class="chip {x["estado"]}">{ {"activo": "en marcha", "cumplido": "cumplido ✓", "no-cumplido": "pendiente"}.get(x["estado"], x["estado"])}</span>'
                  f'{html.escape(x["texto"])}</li>' for x in mios[-4:])
    comentario = f'<blockquote><span>Isa dice</span>{html.escape(a["comentario_isa"])}</blockquote>' if a.get('comentario_isa') else ''
    sin = f'<p class="vacio">{html.escape(a["sin_datos"])}</p>' if a.get('sin_datos') else ''
    resumen = f'{a["piezas"]} {html.escape(a["que"])}' + (f' · {html.escape(a["extra"])}' if a.get('extra') else '')
    return f'''
<article class="agente" style="--c:{color}">
  <header>
    <div class="avatar">{svg_robot(color, a["cara"])}</div>
    <div class="quien"><h3>{html.escape(a["nombre"])}</h3><p>{resumen}</p>{flecha(a["nota"], a["nota_anterior"])}</div>
    {anillo(a["nota"], color, 84, 8)}
  </header>
  {sin}{comentario}
  {f'<ul class="criterios">{crit}</ul>' if crit else ''}
  {f'<div class="fotos">{fotos}</div>' if fotos else ''}
  <div class="dos">
    {f'<div><h4>Lo hizo muy bien</h4><ul class="logros">{logros}</ul></div>' if logros else ''}
    {f'<div><h4>Puede mejorar</h4><ul class="mejorar">{mejorar}</ul></div>' if mejorar else ''}
  </div>
  {f'<h4>Acuerdos con Isa</h4><ul class="acuerdos">{acu}</ul>' if acu else ''}
</article>'''


FECHA_LARGA = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def informe_html(acta):
    acuerdos = leer_acuerdos()
    f = datetime.date.fromisoformat(acta['fecha'])
    fecha = f'{f.day} de {FECHA_LARGA[f.month - 1]} de {f.year}'
    agentes = acta['agentes']
    # Para "mejor nota" cuenta solo quien tiene al menos 3 criterios con datos
    con_nota = {k: a for k, a in agentes.items() if a['nota'] is not None and sum(c['nota'] is not None for c in a['criterios']) >= 3}
    mejor = max(con_nota.items(), key=lambda kv: kv[1]['nota'], default=None)
    sube = max(((k, a) for k, a in con_nota.items() if a['nota_anterior'] is not None),
               key=lambda kv: kv[1]['nota'] - kv[1]['nota_anterior'], default=None)
    destacados = []
    if mejor:
        destacados.append(f'<div class="dest"><span>⭐ Mejor nota</span><b style="color:{mejor[1]["color"]}">{html.escape(mejor[1]["nombre"])}</b><small>{mejor[1]["nota"]:.1f} de 10</small></div>')
    if sube and sube[1]['nota'] > sube[1]['nota_anterior']:
        destacados.append(f'<div class="dest"><span>🚀 Más mejoró</span><b style="color:{sube[1]["color"]}">{html.escape(sube[1]["nombre"])}</b><small>+{sube[1]["nota"] - sube[1]["nota_anterior"]:.1f}</small></div>')
    destacados.append(f'<div class="dest"><span>🎬 Piezas creadas</span><b>{acta["piezas"]}</b><small>anuncios, educativos y guiones</small></div>')
    destacados.append(f'<div class="dest"><span>🤝 Acuerdos</span><b>{acta["acuerdos"]["cumplidos"]} cumplidos</b><small>{acta["acuerdos"]["activos"]} en marcha</small></div>')
    resumen = acta.get('resumen_isa') or 'Isa todavía no escribió su resumen de la reunión.'
    tarjetas = ''.join(tarjeta_agente(k, a, acuerdos) for k, a in sorted(agentes.items(), key=lambda kv: -(kv[1]['nota'] or -1)))
    mesa = ''.join(f'<div class="silla" style="--c:{a["color"]};--i:{i};--n:{len(agentes)}" data-tip="{html.escape(a["nombre"])}: '
                   f'{"sin nota" if a["nota"] is None else a["nota"]}">{svg_robot(a["color"], a["cara"], 64)}'
                   f'<b>{"–" if a["nota"] is None else format(a["nota"], ".1f")}</b></div>'
                   for i, a in enumerate(agentes.values()))
    filas_acuerdos = ''.join(
        f'<tr><td><i class="punto" style="background:{agentes.get(x["agente"], {}).get("color", "#999")}"></i>{html.escape(agentes.get(x["agente"], {}).get("nombre", x["agente"]))}</td>'
        f'<td>{html.escape(x["texto"])}</td><td>{html.escape(x.get("desde", ""))}</td><td><span class="chip {x["estado"]}">'
        f'{ {"activo": "en marcha", "cumplido": "cumplido ✓", "no-cumplido": "pendiente"}.get(x["estado"], x["estado"])}</span></td></tr>'
        for x in sorted((dict(a, agente=k) for k, l in acuerdos.items() for a in l), key=lambda a: (a['estado'] != 'activo', a.get('desde', ''))))
    tabla = (f'<table><thead><tr><th>Agente</th><th>Acuerdo</th><th>Desde</th><th>Estado</th></tr></thead><tbody>{filas_acuerdos}</tbody></table>'
             if filas_acuerdos else '<p class="vacio">Todavía no hay acuerdos. Isa los propone al final de cada reunión.</p>')
    return PLANTILLA.format(
        fecha=fecha, hora=acta.get('hora', ''), anillo=anillo(acta['nota_equipo'], 'var(--acento)', 150, 13),
        tendencia=flecha(acta['nota_equipo'], acta['nota_equipo_anterior']), destacados=''.join(destacados),
        resumen=html.escape(resumen), mesa=mesa, tarjetas=tarjetas, produccion=barras_produccion(agentes),
        evolucion=linea_tiempo(acta['historial_equipo'], 'var(--acento)') +
        ('<p class="nota-pie">La próxima reunión mostrará cómo va mejorando el equipo.</p>' if len(acta['historial_equipo']) < 2 else ''),
        resultados=barras_resultados(acta['resultados'], agentes), acuerdos=tabla)


PLANTILLA = '''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reunión del equipo de Isa · {fecha}</title>
<style>
:root{{--fondo:#eef3fb;--superficie:#ffffff;--tinta:#0f1b33;--suave:#4f6285;--tenue:#7f8fa9;--pista:#e3eaf6;--borde:#dbe4f3;--acento:#2f6bff;
  --bien:#14996b;--aviso:#c27a00;--mal:#d0453b;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--fondo:#081226;--superficie:#0f1e3a;--tinta:#e8f0ff;--suave:#a9b9d8;--tenue:#7f90b3;--pista:#1c2e52;--borde:#1f335a;--acento:#5b94ff;
  --bien:#3fd39b;--aviso:#f2b64c;--mal:#ff7b70;color-scheme:dark}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--fondo);color:var(--tinta);font:15px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}}
.pagina{{max-width:1180px;margin:0 auto;padding:28px 16px 60px}}
.portada{{display:grid;grid-template-columns:1.2fr 1fr;gap:20px;align-items:stretch}}
.caja{{background:var(--superficie);border:1px solid var(--borde);border-radius:20px;padding:22px}}
.titulo>small{{text-transform:uppercase;letter-spacing:.14em;color:var(--acento);font-weight:700;font-size:12px}}
.titulo h1{{margin:6px 0 4px;font-size:32px;line-height:1.15}} .titulo p{{margin:0;color:var(--suave)}}
.nota-equipo{{display:flex;gap:22px;align-items:center;margin-top:20px}} .nota-equipo h2{{margin:0;font-size:15px;color:var(--suave);font-weight:600}}
.anillo-num{{font-weight:800;font-size:22px;fill:var(--tinta)}} .nota-equipo .anillo-num{{font-size:34px}}
.tend{{display:inline-block;margin-top:6px;font-size:13px;font-weight:600;padding:2px 10px;border-radius:99px;background:var(--pista);color:var(--suave)}}
.tend.sube{{color:var(--bien)}} .tend.baja{{color:var(--mal)}}
.destacados{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:20px}}
.dest{{border:1px solid var(--borde);border-radius:14px;padding:10px 14px;display:flex;flex-direction:column}} .dest span{{font-size:12px;color:var(--tenue)}}
.dest b{{font-size:19px}} .dest small{{color:var(--suave)}}
.mesa{{position:relative;min-height:380px;display:flex;align-items:center;justify-content:center}}
.mesa .tabla{{position:absolute;width:44%;aspect-ratio:1;border-radius:50%;background:radial-gradient(circle,#bfe8ff 0,#7fb2ff22 45%,transparent 70%),var(--pista);border:3px solid #4cc9ff66}}
.mesa .isa{{position:absolute;width:62px;height:62px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#e8fbff,#4cc9ff 55%,#2a6dff);box-shadow:0 0 34px #4cc9ffaa;
  display:grid;place-items:center;color:#06264f;font-weight:800}}
.silla{{position:absolute;left:50%;top:50%;width:80px;margin:-46px 0 0 -40px;text-align:center;
  transform:rotate(calc(var(--i) / var(--n) * 360deg - 90deg)) translate(clamp(120px,15vw,160px)) rotate(calc(var(--i) / var(--n) * -360deg + 90deg))}}
.silla b{{display:inline-block;margin-top:-4px;background:var(--c);color:#06142b;border-radius:99px;padding:0 9px;font-size:13px}}
.resumen{{margin-top:20px}} .resumen blockquote{{margin:0;font-size:17px}}
h2.sec{{margin:38px 0 14px;font-size:21px}} h2.sec small{{display:block;font-size:13px;color:var(--suave);font-weight:400}}
.tarjetas{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}}
.agente{{background:var(--superficie);border:1px solid var(--borde);border-top:5px solid var(--c);border-radius:20px;padding:18px}}
.agente header{{display:flex;gap:12px;align-items:center}} .agente .quien{{flex:1;min-width:0}}
.agente h3{{margin:0;font-size:18px}} .agente .quien p{{margin:0;color:var(--suave);font-size:13px}}
.avatar{{width:64px;height:64px;border-radius:18px;background:var(--pista);display:grid;place-items:center;flex:none}}
.criterios{{list-style:none;padding:0;margin:14px 0 0}} .criterios li{{display:grid;grid-template-columns:1fr 90px 60px;gap:8px;align-items:center;font-size:13px;padding:3px 0}}
.mini{{height:8px;border-radius:99px;background:var(--pista);overflow:hidden}} .mini i{{display:block;height:100%;border-radius:99px}}
.criterios b{{text-align:right}} .criterios .nd{{font-weight:400;color:var(--tenue);font-size:12px}}
.fotos{{display:flex;gap:8px;margin-top:12px}} .fotos img{{height:92px;width:31%;border-radius:10px;border:1px solid var(--borde);object-fit:cover;object-position:top}}
.dos{{display:grid;grid-template-columns:1fr 1fr;gap:10px}} h4{{margin:14px 0 4px;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--tenue)}}
.logros,.mejorar,.acuerdos{{margin:0;padding:0;list-style:none;font-size:13px}}
.logros li::before{{content:"✓ ";color:var(--bien);font-weight:700}} .mejorar li::before{{content:"→ ";color:var(--aviso);font-weight:700}}
.acuerdos li{{padding:3px 0}}
.chip{{display:inline-block;font-size:11px;font-weight:700;border-radius:99px;padding:1px 8px;margin-right:6px;background:var(--pista);color:var(--suave)}}
.chip.cumplido{{color:var(--bien)}} .chip.activo{{color:var(--acento)}} .chip.no-cumplido{{color:var(--aviso)}}
blockquote{{margin:12px 0 0;padding:10px 14px;border-left:4px solid var(--c,var(--acento));background:var(--pista);border-radius:0 12px 12px 0}}
blockquote span{{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--tenue);font-weight:700}}
.columnas{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.barras{{display:flex;flex-direction:column;gap:10px}} .fila-barra{{display:grid;grid-template-columns:150px 1fr 150px;gap:10px;align-items:center;font-size:14px}}
.fila-barra .pista{{height:14px;background:var(--pista);border-radius:4px;overflow:hidden}} .fila-barra .pista i{{display:block;height:100%;border-radius:0 4px 4px 0}}
.fila-barra small{{color:var(--suave)}} .nom{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.grafico{{width:100%;height:auto}} .guia{{stroke:var(--borde)}} .eje{{fill:var(--tenue);font-size:11px}} .etq-dato{{fill:var(--tinta);font-weight:700;font-size:13px}}
.vacio,.nota-pie{{color:var(--suave);font-size:14px}}
table{{width:100%;border-collapse:collapse;font-size:14px}} th{{text-align:left;color:var(--tenue);font-size:12px;text-transform:uppercase;letter-spacing:.06em}}
th,td{{padding:8px 6px;border-bottom:1px solid var(--borde)}} .punto{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px}}
#tip{{position:fixed;pointer-events:none;background:var(--tinta);color:var(--superficie);font-size:13px;padding:6px 10px;border-radius:8px;max-width:320px;opacity:0;transition:opacity .12s;z-index:9}}
@media (max-width:820px){{.portada,.columnas{{grid-template-columns:1fr}} .fila-barra{{grid-template-columns:90px 1fr 110px}} .titulo h1{{font-size:26px}}
  .tarjetas{{grid-template-columns:1fr}} .dos{{grid-template-columns:1fr}}}}
</style></head><body><div class="pagina">
<section class="portada">
  <div class="caja titulo">
    <small>Reunión del equipo de Isa</small><h1>{fecha}</h1><p>Isa reunió a todo su equipo a las {hora} para revisar el trabajo, ponerle nota y acordar cómo mejorar.</p>
    <div class="nota-equipo">{anillo}<div><h2>Nota del equipo</h2>{tendencia}</div></div>
    <div class="destacados">{destacados}</div>
  </div>
  <div class="caja mesa" aria-label="El equipo alrededor de Isa"><div class="tabla"></div><div class="isa">Isa</div>{mesa}</div>
</section>
<div class="caja resumen" style="--c:var(--acento)"><blockquote><span>Lo que Isa le dice al equipo</span>{resumen}</blockquote></div>
<h2 class="sec">Cada agente<small>Pasa el mouse por cada criterio para ver en qué se basa la nota.</small></h2>
<div class="tarjetas">{tarjetas}</div>
<div class="columnas">
  <div><h2 class="sec">Lo que produjo cada uno</h2><div class="caja">{produccion}</div></div>
  <div><h2 class="sec">Cómo va mejorando el equipo<small>Nota del equipo en cada reunión</small></h2><div class="caja">{evolucion}</div></div>
</div>
<h2 class="sec">Resultados reales en redes<small>Lo que Isabella contó de sus publicaciones</small></h2><div class="caja">{resultados}</div>
<h2 class="sec">Acuerdos<small>Lo que cada agente se comprometió a mejorar. Cada agente los lee antes de trabajar.</small></h2><div class="caja">{acuerdos}</div>
</div><div id="tip"></div>
<script>
const tip=document.getElementById("tip");
document.addEventListener("pointermove",e=>{{const t=e.target.closest("[data-tip]");if(!t){{tip.style.opacity=0;return}}
tip.textContent=t.dataset.tip;tip.style.opacity=1;const x=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8);tip.style.left=x+"px";tip.style.top=(e.clientY+16)+"px"}});
</script></body></html>
'''


# ---------- comandos ----------

def ultima_acta():
    actas = sorted(ACTAS.glob('*.json'))
    if not actas:
        print('Todavía no hubo ninguna reunión. Primero: python3 reunion/revisar.py reunir')
        sys.exit(1)
    return actas[-1]


def guardar_acta(archivo, acta):
    escribir_json(archivo, acta)
    archivo.with_suffix('.html').write_text(informe_html(acta), encoding='utf-8')
    if COMPARTIDO.is_dir():   # copia para el proyecto compartido
        destino = COMPARTIDO / 'reuniones'
        destino.mkdir(exist_ok=True)
        (destino / archivo.with_suffix('.html').name).write_text(informe_html(acta), encoding='utf-8')


def comprobar_agente(agente):
    equipo = equipo_del_panel()
    if agente not in equipo:
        print(f'No conozco al agente "{agente}". El equipo es: {", ".join(equipo)}')
        sys.exit(1)


def cmd_reunir(a):
    fecha = a.fecha or HOY.isoformat()
    acta = reunir(fecha)
    archivo = ACTAS / f'{fecha}.json'
    guardar_acta(archivo, acta)
    acuerdos = leer_acuerdos()
    print(f'REUNIÓN DEL EQUIPO · {fecha}')
    ant = acta['nota_equipo_anterior']
    print(f'Nota del equipo: {acta["nota_equipo"]}' + (f' (la vez pasada: {ant})' if ant is not None else ' (primera reunión)'))
    for id_, ag in sorted(acta['agentes'].items(), key=lambda kv: -(kv[1]['nota'] or -1)):
        print(f'\n■ {ag["nombre"]} ({id_}) · nota {ag["nota"] if ag["nota"] is not None else "sin datos"}'
              + (f' · antes {ag["nota_anterior"]}' if ag['nota_anterior'] is not None else '')
              + f' · {ag["piezas"]} {ag["que"]}')
        if ag.get('sin_datos'):
            print(f'  {ag["sin_datos"]}')
        for c in ag['criterios']:
            print(f'  - {c["nombre"]}: {c["nota"] if c["nota"] is not None else "—"} · {c["detalle"]}')
        for t in ag['logros']:
            print(f'  ✓ {t}')
        for t in ag['mejorar']:
            print(f'  → {t}')
        activos = acuerdos_activos(id_, acuerdos)
        for i, x in enumerate(acuerdos.get(id_, []), 1):
            if x['estado'] == 'activo':
                print(f'  ACUERDO A REVISAR #{i} (desde {x["desde"]}): {x["texto"]}')
        for p in ag['propuestas']:
            if len(activos) < 3:
                print(f'  PROPUESTA DE ACUERDO: {p}')
        if ag['muestras']:
            print(f'  Muestras para mirar: {", ".join(ag["muestras"])}')
    print(f'\nInforme visual: {ruta_rel(archivo.with_suffix(".html"))}')


def actualizar_acta(cambio):
    archivo = ultima_acta()
    acta = leer_json(archivo)
    cambio(acta)
    guardar_acta(archivo, acta)
    return archivo


def cmd_nota(a):
    comprobar_agente(a.agente)
    archivo = actualizar_acta(lambda acta: acta['agentes'].setdefault(a.agente, {}).__setitem__('comentario_isa', a.texto))
    print(f'Comentario guardado en {ruta_rel(archivo.with_suffix(".html"))}')


def cmd_resumen(a):
    archivo = actualizar_acta(lambda acta: acta.__setitem__('resumen_isa', a.texto))
    print(f'Resumen guardado en {ruta_rel(archivo.with_suffix(".html"))}')


def _contar_acuerdos(acta):
    lista = [x for v in leer_acuerdos().values() for x in v]
    acta['acuerdos'] = {'activos': sum(1 for x in lista if x['estado'] == 'activo'),
                        'cumplidos': sum(1 for x in lista if x['estado'] == 'cumplido')}


def cmd_acuerdo(a):
    comprobar_agente(a.agente)
    datos = leer_acuerdos()
    lista = datos.setdefault(a.agente, [])
    if any(x['texto'].lower() == a.texto.lower() and x['estado'] == 'activo' for x in lista):
        print('Ese acuerdo ya está en marcha.')
        return
    lista.append({'texto': a.texto, 'desde': HOY.isoformat(), 'estado': 'activo'})
    escribir_json(ACUERDOS, datos)
    if list(ACTAS.glob('*.json')):
        actualizar_acta(_contar_acuerdos)
    print(f'Acuerdo #{len(lista)} con {a.agente}: {a.texto}')


def cambiar_estado(a, estado):
    comprobar_agente(a.agente)
    datos = leer_acuerdos()
    lista = datos.get(a.agente, [])
    if not 1 <= a.numero <= len(lista):
        print(f'{a.agente} no tiene el acuerdo #{a.numero}.')
        sys.exit(1)
    x = lista[a.numero - 1]
    x['estado'] = 'cumplido' if estado == 'cumplido' else 'activo'
    x.setdefault('revisiones', []).append({'fecha': HOY.isoformat(), 'resultado': estado})
    if estado == 'no-cumplido' and sum(1 for r in x['revisiones'] if r['resultado'] == 'no-cumplido') >= 2:
        x['estado'] = 'no-cumplido'   # dos reuniones sin cumplirlo: Isa debería cambiar el acuerdo
    escribir_json(ACUERDOS, datos)
    if list(ACTAS.glob('*.json')):
        actualizar_acta(_contar_acuerdos)
    print(f'Acuerdo #{a.numero} de {a.agente}: {x["estado"]}.')


def cmd_acuerdos(a):
    activos = [(i, x) for i, x in enumerate(leer_acuerdos().get(a.agente, []), 1) if x['estado'] == 'activo']
    if not activos:
        print(f'{a.agente} no tiene acuerdos pendientes con Isa.')
        return
    print(f'Acuerdos de {a.agente} con Isa (cúmplelos en este trabajo):')
    for i, x in activos:
        print(f'  {i}. {x["texto"]}  (desde {x["desde"]})')


def cmd_historial(a):
    actas = [leer_json(f) for f in sorted(ACTAS.glob('*.json'))]
    if not actas:
        print('Todavía no hubo reuniones.')
        return
    ids = sorted({k for acta in actas for k in acta.get('agentes', {})})
    print('fecha       equipo  ' + '  '.join(f'{i[:12]:>12}' for i in ids))
    for acta in actas:
        notas = [acta['agentes'].get(i, {}).get('nota') for i in ids]
        print(f'{acta["fecha"]}  {acta.get("nota_equipo") or "—":>6}  ' + '  '.join(f'{n if n is not None else "—":>12}' for n in notas))


def main():
    ap = argparse.ArgumentParser(description='Reunión de equipo de Isa')
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('reunir', help='revisar el trabajo de todos y armar el acta y el informe visual')
    r.add_argument('--fecha', help='AAAA-MM-DD (por defecto hoy)')
    r.set_defaults(f=cmd_reunir)
    n = sub.add_parser('nota', help='comentario de Isa sobre un agente')
    n.add_argument('agente')
    n.add_argument('texto')
    n.set_defaults(f=cmd_nota)
    s = sub.add_parser('resumen', help='lo que Isa le dice al equipo')
    s.add_argument('texto')
    s.set_defaults(f=cmd_resumen)
    c = sub.add_parser('acuerdo', help='nuevo compromiso de un agente para la próxima reunión')
    c.add_argument('agente')
    c.add_argument('texto')
    c.set_defaults(f=cmd_acuerdo)
    for nombre in ('cumplido', 'no-cumplido'):
        e = sub.add_parser(nombre, help=f'marcar un acuerdo como {nombre}')
        e.add_argument('agente')
        e.add_argument('numero', type=int)
        e.set_defaults(f=lambda a, estado=nombre: cambiar_estado(a, estado))
    l = sub.add_parser('acuerdos', help='los acuerdos pendientes de un agente (lo lee antes de trabajar)')
    l.add_argument('agente')
    l.set_defaults(f=cmd_acuerdos)
    sub.add_parser('historial', help='notas de todas las reuniones').set_defaults(f=cmd_historial)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
