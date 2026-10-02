#!/usr/bin/env python3
"""La Analista de redes de Isa: guarda las estadísticas de las publicaciones de Isabella
(Instagram y TikTok), las compara con su propio promedio y arma un informe visual con qué
funcionó, qué no y qué hacer la próxima semana. Sus consejos los leen los otros agentes.

No entra a Instagram ni a TikTok: los números salen de las capturas de pantalla que
Isabella deja en analista/capturas/ (la Analista las lee) o de lo que ella cuenta.

Uso (desde la carpeta del proyecto):
  python3 analista/redes.py pendientes                     # capturas sin leer y publicaciones sin números
  python3 analista/redes.py agregar --red instagram --tipo reel --fecha 2026-10-03 --hora 19:30 \\
      --tema "rutina de noche" --vistas 1800 --alcance 1500 --me-gusta 120 --comentarios 9 \\
      --guardados 30 --compartidos 12 --seguidores 8 --mensajes 3 --captura analista/capturas/x.png
  python3 analista/redes.py cuenta --red instagram --seguidores 1250 [--alcance 9000 --visitas-perfil 300]
  python3 analista/redes.py lista                          # lo guardado
  python3 analista/redes.py informe [--dias 30]            # informe visual + consejos para el equipo
  python3 analista/redes.py consejos <agente>              # lo que cada agente lee antes de trabajar

Si la publicación está en un plan del estratega (--plan y --id, o la encuentra sola por
fecha y red), también guarda vistas, mensajes y ventas en el plan: así el estratega y la
reunión del equipo aprenden de los resultados reales.
Solo usa la librería estándar de Python.
"""
import argparse
import datetime
import html
import importlib.util
import json
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
DATOS = AQUI / 'datos'
PUBLICACIONES = DATOS / 'publicaciones.json'
CUENTA = DATOS / 'cuenta.json'
CAPTURAS = AQUI / 'capturas'
INFORMES = AQUI / 'informes'
PLANES = RAIZ / 'planificador' / 'planes'
COMPARTIDO = Path('/mnt/project-files')

HOY = datetime.date.today()
REDES = ('instagram', 'tiktok', 'facebook', 'youtube')
TIPOS = ('reel', 'anuncio', 'educativo', 'carrusel', 'post', 'historia', 'en-vivo', 'video')
METRICAS = ('vistas', 'alcance', 'me_gusta', 'comentarios', 'guardados', 'compartidos',
            'seguidores', 'mensajes', 'ventas', 'visitas_perfil', 'duracion', 'seg_promedio', 'completo')
DIAS = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')
EXT_IMAGEN = ('.png', '.jpg', '.jpeg', '.heic', '.webp')
# Quién hace cada tipo de publicación (el mismo reparto que la reunión del equipo)
DUENO_TIPO = {'anuncio': 'creador-contenido', 'educativo': 'creador-educativo', 'carrusel': 'creador-educativo',
              'reel': 'guionista', 'historia': 'guionista', 'en-vivo': 'guionista'}
# Referencias aproximadas para cuentas que están empezando (solo para el semáforo)
REF_INTERACCION = (2.0, 5.0)     # % de la gente alcanzada que reacciona: bajo < 2, bien ≥ 5
REF_VALOR = (0.5, 1.5)           # guardados + compartidos por cada 100 vistas
REF_RETENCION = (35, 55)         # % del video que se ve en promedio


# ---------- utilidades ----------

def leer_json(archivo, defecto=None):
    try:
        return json.loads(Path(archivo).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def escribir_json(archivo, datos):
    Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    Path(archivo).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ruta_rel(p):
    try:
        return str(Path(p).resolve().relative_to(RAIZ))
    except ValueError:
        return str(p)


def cargar_planificar():
    try:
        spec = importlib.util.spec_from_file_location('planificar', RAIZ / 'planificador' / 'planificar.py')
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception:   # noqa: BLE001 — sin planificador, la Analista sigue sola
        return None


def fecha_valida(texto):
    try:
        return datetime.date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def publicaciones():
    datos = leer_json(PUBLICACIONES, [])
    return datos if isinstance(datos, list) else []


def div(a, b):
    return a / b if b else None


# ---------- guardar ----------

def planes():
    for f in sorted(PLANES.glob('*.json')):
        plan = leer_json(f)
        if isinstance(plan, dict) and plan.get('publicaciones'):
            yield f, plan


def buscar_en_plan(fecha, red, tipo):
    """La publicación del plan con la misma fecha y red (y tipo, si hay varias). Solo si queda una."""
    candidatas = []
    for f, plan in planes():
        for p in plan['publicaciones']:
            if p.get('fecha') != fecha:
                continue
            if red and p.get('red') and red not in str(p['red']).lower():
                continue
            candidatas.append((f, p))
    if len(candidatas) > 1:
        candidatas = [c for c in candidatas if c[1].get('tipo') == tipo]
    return candidatas[0] if len(candidatas) == 1 else None


def guardar_en_plan(archivo, id_, pub):
    planificar = cargar_planificar()
    if not planificar:
        return False
    a = argparse.Namespace(plan=str(archivo), id=str(id_), vistas=pub.get('vistas'),
                           mensajes=pub.get('mensajes'), ventas=pub.get('ventas'),
                           guardados=pub.get('guardados'), compartidos=pub.get('compartidos'))
    try:
        planificar.cmd_resultado(a)
        return True
    except SystemExit:
        return False


def archivar_captura(ruta, fecha):
    """Mueve la captura ya leída a capturas/leidas/ para no leerla dos veces."""
    origen = Path(ruta)
    if not origen.is_absolute():
        origen = (RAIZ / origen) if (RAIZ / origen).exists() else origen.resolve()
    if not origen.exists():
        return str(ruta)
    try:
        origen.resolve().relative_to(CAPTURAS.resolve())
    except ValueError:
        return ruta_rel(origen)   # está en otra carpeta: no se mueve
    if origen.parent.name == 'leidas':
        return ruta_rel(origen)
    destino = CAPTURAS / 'leidas' / f'{fecha}-{origen.name}'
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(origen), destino)
    return ruta_rel(destino)


def cmd_agregar(a):
    fecha = a.fecha or HOY.isoformat()
    if not fecha_valida(fecha):
        sys.exit(f'La fecha "{fecha}" no se entiende: usa AAAA-MM-DD.')
    red = a.red.lower()
    nueva = {'red': red, 'tipo': a.tipo, 'fecha': fecha}
    for campo in ('hora', 'tema', 'enlace', 'producto', 'nota'):
        if getattr(a, campo):
            nueva[campo] = getattr(a, campo)
    for m in METRICAS:
        v = getattr(a, m)
        if v is not None:
            nueva[m] = v
    lista = publicaciones()
    # Si ya existe (misma red, fecha y tema), se actualizan sus números
    existente = next((p for p in lista if p['red'] == red and p['fecha'] == fecha and
                      (p.get('tema') or '').lower() == (a.tema or '').lower() and p.get('tipo') == a.tipo), None)
    if existente:
        existente.update(nueva)
        pub = existente
    else:
        pub = dict(nueva, id=max((p.get('id', 0) for p in lista), default=0) + 1)
        lista.append(pub)
    if a.captura:
        pub.setdefault('capturas', [])
        for c in a.captura:
            ruta = archivar_captura(c, fecha)
            if ruta not in pub['capturas']:
                pub['capturas'].append(ruta)
    # Conectar con el plan del estratega
    enlace = None
    if a.plan and a.id:
        enlace = (Path(a.plan), a.id)
    elif pub.get('plan') and pub.get('plan_id'):
        enlace = (RAIZ / pub['plan'], pub['plan_id'])
    elif not a.sin_plan:
        encontrada = buscar_en_plan(fecha, red, a.tipo)
        if encontrada:
            enlace = (encontrada[0], encontrada[1].get('id'))
            pub.setdefault('tipo_plan', encontrada[1].get('tipo'))
            pub.setdefault('pilar', encontrada[1].get('pilar'))
    en_plan = False
    if enlace:
        pub['plan'], pub['plan_id'] = ruta_rel(enlace[0]), enlace[1]
        en_plan = guardar_en_plan(enlace[0], enlace[1], pub)
    escribir_json(PUBLICACIONES, lista)
    print(f'Guardada la publicación #{pub["id"]} ({red}, {pub["tipo"]}, {fecha}).')
    if en_plan:
        print(f'También quedó en el plan ({pub["plan"]}, publicación {pub["plan_id"]}): el estratega y la reunión la usan.')
    faltan = [m for m in ('vistas', 'alcance', 'me_gusta', 'guardados', 'compartidos') if m not in pub]
    if faltan:
        print('Faltan (si la captura los muestra, agrégalos): ' + ', '.join(faltan))


def cmd_cuenta(a):
    fecha = a.fecha or HOY.isoformat()
    datos = leer_json(CUENTA, [])
    datos = [d for d in datos if not (d['red'] == a.red and d['fecha'] == fecha)]
    fila = {'red': a.red, 'fecha': fecha, 'seguidores': a.seguidores}
    for campo in ('alcance', 'visitas_perfil', 'interacciones'):
        if getattr(a, campo) is not None:
            fila[campo] = getattr(a, campo)
    datos.append(fila)
    datos.sort(key=lambda d: (d['red'], d['fecha']))
    escribir_json(CUENTA, datos)
    previas = [d for d in datos if d['red'] == a.red and d['fecha'] < fecha]
    extra = f' ({a.seguidores - previas[-1]["seguidores"]:+d} desde el {previas[-1]["fecha"]})' if previas else ''
    print(f'Cuenta de {a.red} el {fecha}: {a.seguidores} seguidores{extra}.')


def cmd_pendientes(a):
    nuevas = sorted(f for f in CAPTURAS.glob('*') if f.suffix.lower() in EXT_IMAGEN) if CAPTURAS.is_dir() else []
    print(f'Capturas sin leer: {len(nuevas)}')
    for f in nuevas:
        print(f'  {ruta_rel(f)}')
    guardadas = {(p.get('plan'), str(p.get('plan_id'))) for p in publicaciones()}
    sin_numeros = []
    for f, plan in planes():
        for p in plan['publicaciones']:
            pasada = (p.get('fecha') or '9') <= HOY.isoformat()
            if pasada and p.get('estado') in ('hecho', 'publicado') and not p.get('resultados') \
                    and (ruta_rel(f), str(p.get('id'))) not in guardadas:
                sin_numeros.append(f'  {p.get("fecha")} · {p.get("tipo")} · {p.get("red", "")} · {p.get("idea", "")[:60]}  (plan {ruta_rel(f)}, id {p.get("id")})')
    print(f'Publicaciones del plan ya hechas y sin números: {len(sin_numeros)}')
    print('\n'.join(sin_numeros))
    ultimo = sorted(INFORMES.glob('*.json'))
    if ultimo:
        dias = max(0, (HOY - datetime.date.fromisoformat(ultimo[-1].stem[:10])).days)
        print(f'Último informe: hace {dias} días' + (' (toca uno nuevo)' if dias >= 7 else ''))
    else:
        print('Todavía no hay informes.')


def cmd_lista(a):
    lista = publicaciones()
    if not lista:
        print('Todavía no hay publicaciones guardadas.')
        return
    for p in sorted(lista, key=lambda p: (p['fecha'], p.get('hora') or '')):
        m = calcular(p)
        print(f'#{p["id"]:>3} {p["fecha"]} {p.get("hora", ""):>5} {p["red"]:<9} {p["tipo"]:<9} '
              f'{p.get("vistas", "—")!s:>7} vistas · interacción {fmt_pct(m["interaccion"])} · '
              f'{(p.get("tema") or "")[:40]}')


# ---------- análisis ----------

def calcular(p):
    """Las medidas que importan de una publicación."""
    vistas, alcance = p.get('vistas') or 0, p.get('alcance') or 0
    base = alcance or vistas
    reacciones = sum(p.get(k) or 0 for k in ('me_gusta', 'comentarios', 'guardados', 'compartidos'))
    valor = (p.get('guardados') or 0) + (p.get('compartidos') or 0)
    retencion = p.get('completo')
    if retencion is None and p.get('seg_promedio') and p.get('duracion'):
        retencion = min(100, 100 * p['seg_promedio'] / p['duracion'])
    return {
        'vistas': vistas or None,
        'interaccion': 100 * div(reacciones, base) if base else None,
        'valor': 100 * div(valor, vistas or alcance) if (vistas or alcance) else None,
        'conversacion': (p.get('comentarios') or 0) + (p.get('mensajes') or 0),
        'seguidores_100': 100 * div(p.get('seguidores') or 0, base) if base else None,
        'negocio': (p.get('mensajes') or 0) + 3 * (p.get('ventas') or 0),
        'retencion': retencion,
    }


PESOS = {'vistas': 0.25, 'interaccion': 0.25, 'valor': 0.2, 'negocio': 0.2, 'seguidores_100': 0.1}


def puntajes(pubs):
    """Puntaje 0-100 de cada publicación comparada con la mediana de Isabella (50 = su normal)."""
    medidas = [calcular(p) for p in pubs]
    medianas = {}
    for k in PESOS:
        valores = [m[k] for m in medidas if m[k] is not None]
        medianas[k] = statistics.median(valores) if valores else None
    salida = []
    for p, m in zip(pubs, medidas):
        total = peso = 0
        detalle = {}
        for k, w in PESOS.items():
            if m[k] is None or not medianas[k]:
                continue
            razon = min(3.0, m[k] / medianas[k])      # 1 = igual que su normal, 3 = el triple o más
            detalle[k] = razon
            total += w * razon
            peso += w
        salida.append({'pub': p, 'medidas': m, 'razon': detalle,
                       'puntaje': round(min(100, 50 * total / peso)) if peso else None})
    return salida, medianas


def franja(hora):
    try:
        h = int(str(hora)[:2])
    except ValueError:
        return ''
    return 'mañana' if 6 <= h < 12 else 'tarde' if 12 <= h < 18 else 'noche' if h >= 18 else 'madrugada'


def duracion_rango(seg):
    if not seg:
        return ''
    return 'hasta 15 s' if seg <= 15 else '16 a 30 s' if seg <= 30 else '31 a 60 s' if seg <= 60 else 'más de 1 min'


def agrupar(evaluadas, campo):
    grupos = defaultdict(list)
    for e in evaluadas:
        p = e['pub']
        valor = {
            'tipo': p.get('tipo'), 'red': p.get('red'), 'pilar': p.get('pilar'),
            'dia': DIAS[fecha_valida(p['fecha']).weekday()] if fecha_valida(p['fecha']) else '',
            'franja': franja(p.get('hora') or ''), 'duracion': duracion_rango(p.get('duracion')),
        }[campo]
        if valor and e['puntaje'] is not None:
            grupos[valor].append(e)
    filas = [{'valor': k, 'publicaciones': len(v), 'puntaje': round(statistics.mean(e['puntaje'] for e in v)),
              'vistas': round(statistics.mean(e['medidas']['vistas'] or 0 for e in v))}
             for k, v in grupos.items()]
    return sorted(filas, key=lambda f: -f['puntaje'])


def semaforo(valor, ref):
    if valor is None:
        return None
    return 'bien' if valor >= ref[1] else 'aviso' if valor >= ref[0] else 'mal'


def por_que(e, medianas):
    """En palabras simples: qué la hizo subir o bajar frente a su normal."""
    nombres = {'vistas': 'vistas', 'interaccion': 'gente que reaccionó', 'valor': 'guardados y compartidos',
               'negocio': 'mensajes y ventas', 'seguidores_100': 'seguidores nuevos'}
    altos = [nombres[k] for k, r in sorted(e['razon'].items(), key=lambda x: -x[1]) if r >= 1.3]
    bajos = [nombres[k] for k, r in sorted(e['razon'].items(), key=lambda x: x[1]) if r <= 0.7]
    partes = []
    if altos:
        partes.append(' y '.join('más ' + x for x in altos[:2]) + ' que lo normal')
    if bajos:
        partes.append(' y '.join('menos ' + x for x in bajos[:2]) + ' que lo normal')
    return '; '.join(partes) or 'parecida a lo normal'


def frecuencia(pubs, dias):
    fechas = sorted({p['fecha'] for p in pubs})
    semanas = max(1, dias / 7)
    huecos = []
    for a, b in zip(fechas, fechas[1:]):
        d = (fecha_valida(b) - fecha_valida(a)).days
        if d > 4:
            huecos.append((a, b, d))
    return round(len(pubs) / semanas, 1), huecos


def crecimiento():
    datos = leer_json(CUENTA, []) or []
    salida = []
    for red in sorted({d['red'] for d in datos}):
        filas = [d for d in datos if d['red'] == red]
        primera, ultima = filas[0], filas[-1]
        dias = (fecha_valida(ultima['fecha']) - fecha_valida(primera['fecha'])).days
        salida.append({'red': red, 'seguidores': ultima['seguidores'], 'desde': primera['fecha'],
                       'cambio': ultima['seguidores'] - primera['seguidores'], 'dias': dias,
                       'historial': [(d['fecha'], d['seguidores']) for d in filas]})
    return salida


def consejos(evaluadas, medianas, grupos, frec, huecos, crec, dias):
    """Recomendaciones concretas, cada una para quien la tiene que cumplir."""
    c = []

    def agregar(para, texto, porque):
        c.append({'para': para, 'texto': texto, 'porque': porque})

    n = len(evaluadas)
    if n < 3:
        agregar('isabella', 'Seguir mandando las capturas de cada publicación',
                f'Con {n} {"publicación" if n == 1 else "publicaciones"} todavía no se pueden sacar conclusiones; desde 5 ya se ven patrones.')
        return c
    for campo, quien, como in (('tipo', 'estratega-contenido', 'tipo de publicación'),
                               ('franja', 'estratega-contenido', 'horario'),
                               ('dia', 'estratega-contenido', 'día')):
        filas = [f for f in grupos[campo] if f['publicaciones'] >= 2]
        if len(filas) >= 2 and filas[0]['puntaje'] - filas[-1]['puntaje'] >= 12:
            mejor, peor = filas[0], filas[-1]
            agregar(quien, f'Poner más publicaciones en {como} «{mejor["valor"]}» y menos en «{peor["valor"]}»',
                    f'«{mejor["valor"]}» saca {mejor["puntaje"]} puntos de promedio ({mejor["publicaciones"]} publicaciones) '
                    f'y «{peor["valor"]}» {peor["puntaje"]} ({peor["publicaciones"]}).')
            if campo == 'tipo':
                bueno, malo = DUENO_TIPO.get(mejor['valor']), DUENO_TIPO.get(peor['valor'])
                if bueno:
                    agregar(bueno, f'Lo tuyo ({mejor["valor"]}) es lo que mejor funciona: repite lo de las mejores',
                            f'{mejor["puntaje"]} puntos de promedio, el más alto')
                if malo and malo != bueno:
                    agregar(malo, f'Lo tuyo ({peor["valor"]}) es lo que menos funciona: cambia el gancho y el formato',
                            f'{peor["puntaje"]} puntos de promedio, el más bajo')
    ret = [e['medidas']['retencion'] for e in evaluadas if e['medidas']['retencion'] is not None]
    if len(ret) >= 3 and statistics.mean(ret) < REF_RETENCION[0]:
        for quien in ('guionista', 'creador-contenido', 'creador-educativo'):
            agregar(quien, 'Gancho más fuerte en los primeros 2 segundos y videos más cortos',
                    f'La gente ve en promedio el {statistics.mean(ret):.0f}% de los videos; lo bueno empieza en {REF_RETENCION[1]}%.')
    inter = [e['medidas']['interaccion'] for e in evaluadas if e['medidas']['interaccion'] is not None]
    if inter and statistics.mean(inter) < REF_INTERACCION[0]:
        agregar('guionista', 'Terminar cada video con una pregunta para que comenten',
                f'Solo reacciona el {statistics.mean(inter):.1f}% de la gente que ve (lo normal es 2 a 5%).')
    valor = [e['medidas']['valor'] for e in evaluadas if e['medidas']['valor'] is not None]
    if valor and statistics.mean(valor) < REF_VALOR[0]:
        agregar('creador-educativo', 'Más contenido útil para guardar (tips, pasos, listas) con "guárdalo" al final',
                f'Por cada 100 vistas hay {statistics.mean(valor):.1f} guardados o compartidos; lo bueno es más de {REF_VALOR[1]}.')
    vistas_altas = [e for e in evaluadas if (e['razon'].get('vistas') or 0) >= 1.3]
    sin_negocio = [e for e in vistas_altas if not e['pub'].get('mensajes') and not e['pub'].get('ventas')]
    if len(sin_negocio) >= 2:
        agregar('creador-contenido', 'Cerrar con un llamado claro: "escríbeme INFO" o el enlace en la bio',
                f'{len(sin_negocio)} publicaciones con muchas vistas no trajeron ningún mensaje ni venta.')
    if frec < 3:
        agregar('estratega-contenido', 'Planear al menos 3 publicaciones por semana, repartidas',
                f'En los últimos {dias} días hubo {frec} por semana.')
    if huecos:
        a, b, d = max(huecos, key=lambda h: h[2])
        agregar('isabella', 'Publicar sin dejar semanas vacías (aunque sea una historia)',
                f'Entre el {a} y el {b} pasaron {d} días sin publicar; las redes muestran menos a las cuentas que desaparecen.')
    for g in crec:
        if g['dias'] >= 7 and g['cambio'] <= 0:
            agregar('estratega-contenido', f'Sumar contenido para gente nueva en {g["red"]} (tendencias, colaboraciones, respuestas a comentarios)',
                    f'Los seguidores no crecieron en {g["dias"]} días ({g["cambio"]:+d}).')
    mejores = sorted((e for e in evaluadas if e['puntaje'] is not None), key=lambda e: -e['puntaje'])[:2]
    for e in mejores:
        p = e['pub']
        agregar('estratega-contenido', f'Repetir la idea de «{p.get("tema") or p["tipo"]}» con otro producto o ángulo',
                f'Fue de lo mejor: {e["puntaje"]} puntos ({por_que(e, medianas)}).')
    return c


def analizar(dias, hasta=None):
    hasta = hasta or HOY
    desde = hasta - datetime.timedelta(days=dias)
    todas = [p for p in publicaciones() if fecha_valida(p['fecha'])]
    periodo = [p for p in todas if desde < fecha_valida(p['fecha']) <= hasta]
    anterior = [p for p in todas if desde - datetime.timedelta(days=dias) < fecha_valida(p['fecha']) <= desde]
    evaluadas, medianas = puntajes(periodo)
    eval_ant, med_ant = puntajes(anterior)
    grupos = {c: agrupar(evaluadas, c) for c in ('tipo', 'red', 'dia', 'franja', 'duracion', 'pilar')}
    frec, huecos = frecuencia(periodo, dias)
    crec = crecimiento()

    def prom(lista, k):
        valores = [e['medidas'][k] for e in lista if e['medidas'][k] is not None]
        return round(statistics.mean(valores), 2) if valores else None

    resumen = {k: prom(evaluadas, k) for k in ('vistas', 'interaccion', 'valor', 'retencion', 'seguidores_100')}
    resumen_ant = {k: prom(eval_ant, k) for k in resumen}
    totales = {k: sum(p.get(k) or 0 for p in periodo) for k in ('vistas', 'mensajes', 'ventas', 'seguidores', 'guardados', 'compartidos')}
    ordenadas = sorted((e for e in evaluadas if e['puntaje'] is not None), key=lambda e: -e['puntaje'])
    top = [dict(fila(e), porque=por_que(e, medianas)) for e in ordenadas[:3]]
    flojas = [dict(fila(e), porque=por_que(e, medianas)) for e in ordenadas[-3:][::-1]] if len(ordenadas) > 3 else []
    return {
        'fecha': hasta.isoformat(), 'dias': dias, 'desde': (desde + datetime.timedelta(days=1)).isoformat(),
        'publicaciones': len(periodo), 'publicaciones_antes': len(anterior), 'por_semana': frec,
        'totales': totales, 'resumen': resumen, 'resumen_antes': resumen_ant,
        'semaforo': {'interaccion': semaforo(resumen['interaccion'], REF_INTERACCION),
                     'valor': semaforo(resumen['valor'], REF_VALOR),
                     'retencion': semaforo(resumen['retencion'], REF_RETENCION)},
        'grupos': grupos, 'mejores': top, 'flojas': flojas,
        'todas': [fila(e) for e in sorted(evaluadas, key=lambda e: e['pub']['fecha'])],
        'crecimiento': crec,
        'consejos': consejos(evaluadas, medianas, grupos, frec, huecos, crec, dias),
    }


def fila(e):
    p, m = e['pub'], e['medidas']
    return {'id': p.get('id'), 'fecha': p['fecha'], 'hora': p.get('hora', ''), 'red': p['red'], 'tipo': p['tipo'],
            'tema': p.get('tema', ''), 'puntaje': e['puntaje'], 'vistas': p.get('vistas'),
            'interaccion': m['interaccion'], 'valor': m['valor'], 'retencion': m['retencion'],
            'mensajes': p.get('mensajes'), 'ventas': p.get('ventas'), 'seguidores': p.get('seguidores'),
            'captura': (p.get('capturas') or [None])[0]}


# ---------- informe visual ----------

def fmt_pct(v, dec=1):
    return '—' if v is None else f'{v:.{dec}f}%'


def fmt_dec(v):
    return '—' if v is None else f'{v:.1f}'


def fmt_num(v):
    if v is None:
        return '—'
    return f'{v / 1000:.1f} mil' if v >= 10000 else f'{v:,.0f}'.replace(',', '.')


ICONO = {'bien': '✓', 'aviso': '!', 'mal': '✕'}
PALABRA = {'bien': 'Muy bien', 'aviso': 'Normal', 'mal': 'Bajo'}


def tarjeta_kpi(titulo, valor, antes, estado, ayuda, formato=fmt_pct):
    cambio = ''
    if valor is not None and antes is not None:
        sube = valor >= antes
        cambio = f'<span class="tend {"sube" if sube else "baja"}">{"▲" if sube else "▼"} antes {formato(antes)}</span>'
    chip = f'<span class="estado {estado}">{ICONO[estado]} {PALABRA[estado]}</span>' if estado else ''
    return (f'<div class="kpi"><span>{html.escape(titulo)}</span><b>{formato(valor)}</b>{cambio}{chip}'
            f'<small>{html.escape(ayuda)}</small></div>')


def barras(filas, unidad='puntos'):
    if not filas:
        return '<p class="vacio">Todavía no hay suficientes publicaciones.</p>'
    return '<div class="barras">' + ''.join(
        f'<div class="fila-barra" data-tip="{html.escape(str(f["valor"]))}: {f["puntaje"]} {unidad} · {f["publicaciones"]} publicaciones · '
        f'{fmt_num(f["vistas"])} vistas de promedio"><span class="nom">{html.escape(str(f["valor"]))}</span>'
        f'<span class="pista"><i style="width:{min(100, f["puntaje"]):.0f}%"></i><em></em></span>'
        f'<span class="val">{f["puntaje"]} <small>· {f["publicaciones"]} pub.</small></span></div>'
        for f in filas) + '</div>'


def incrustar(ruta):
    """La captura como imagen dentro del informe (así se ve aunque se mueva el archivo)."""
    import base64
    if not ruta:
        return ''
    f = RAIZ / ruta
    if not f.exists() or f.stat().st_size > 2_500_000 or f.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
        return ''
    tipo = 'png' if f.suffix.lower() == '.png' else 'webp' if f.suffix.lower() == '.webp' else 'jpeg'
    return f'data:image/{tipo};base64,' + base64.b64encode(f.read_bytes()).decode()


def tarjeta_pub(f, clase):
    img = incrustar(f.get('captura'))
    foto = f'<img src="{img}" alt="" loading="lazy">' if img else f'<div class="sin-foto">{html.escape(f["red"][:2].upper())}</div>'
    return (f'<article class="pub {clase}">{foto}<div><b>{html.escape(f.get("tema") or f["tipo"])}</b>'
            f'<small>{f["fecha"]} · {html.escape(f["red"])} · {html.escape(f["tipo"])}</small>'
            f'<p>{fmt_num(f["vistas"])} vistas · reacciona {fmt_pct(f["interaccion"])} · {f.get("mensajes") or 0} mensajes</p>'
            f'<p class="porque">{html.escape(f["porque"])}</p></div><span class="nota">{f["puntaje"]}</span></article>')


NOMBRES = {'isabella': 'Isabella', 'estratega-contenido': 'Estratega', 'guionista': 'Guionista',
           'creador-contenido': 'Creador de anuncios', 'creador-educativo': 'Profe'}


def grafico_seguidores(crec):
    if not crec or all(len(g['historial']) < 2 for g in crec):
        return '<p class="vacio">Cuando Isabella mande una captura de su perfil cada semana, aquí se ve cómo crecen sus seguidores.</p>'
    salida = ''
    for g in crec:
        h = g['historial']
        if len(h) < 2:
            continue
        valores = [v for _, v in h]
        lo, hi = min(valores), max(valores)
        rango = (hi - lo) or 1
        ancho, alto = 1000, 190
        puntos = [(30 + i * (ancho - 60) / (len(h) - 1), alto - 25 - (v - lo) * (alto - 50) / rango) for i, (_, v) in enumerate(h)]
        linea = ' '.join(f'{x:.1f},{y:.1f}' for x, y in puntos)
        marcas = ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="marca" data-tip="{d}: {v} seguidores"/>'
                         for (x, y), (d, v) in zip(puntos, h))
        salida += (f'<h4>{html.escape(g["red"].title())}: {g["seguidores"]} seguidores '
                   f'<span class="tend {"sube" if g["cambio"] > 0 else "baja"}">{g["cambio"]:+d} en {g["dias"]} días</span></h4>'
                   f'<svg viewBox="0 0 {ancho} {alto}" class="grafico" role="img" aria-label="Seguidores de {html.escape(g["red"])}">'
                   f'<line x1="30" x2="{ancho - 30}" y1="{alto - 25}" y2="{alto - 25}" class="guia"/>'
                   f'<polyline points="{linea}" class="linea"/>{marcas}'
                   f'<text x="30" y="{alto - 6}" class="eje">{h[0][0]}</text>'
                   f'<text x="{ancho - 30}" y="{alto - 6}" class="eje" text-anchor="end">{h[-1][0]}</text></svg>')
    return salida


def informe_html(r):
    res, ant, sem = r['resumen'], r['resumen_antes'], r['semaforo']
    kpis = ''.join([
        tarjeta_kpi('Publicaciones', r['publicaciones'], r['publicaciones_antes'] or None, None,
                    f'{r["por_semana"]} por semana', formato=lambda v: '—' if v is None else str(v)),
        tarjeta_kpi('Vistas promedio', res['vistas'], ant['vistas'], None, 'Cuánta gente ve cada publicación', formato=fmt_num),
        tarjeta_kpi('Reacciona', res['interaccion'], ant['interaccion'], sem['interaccion'],
                    'De cada 100 que la ven, cuántos dan me gusta, comentan, guardan o comparten'),
        tarjeta_kpi('Guardan o comparten', res['valor'], ant['valor'], sem['valor'],
                    'Por cada 100 vistas: lo que más le gusta a Instagram y TikTok', formato=fmt_dec),
        tarjeta_kpi('Ven del video', res['retencion'], ant['retencion'], sem['retencion'],
                    'Qué parte del video ven en promedio', formato=lambda v: fmt_pct(v, 0)),
    ])
    tot = r['totales']
    totales = (f'<p class="totales">En estos {r["dias"]} días: <b>{fmt_num(tot["vistas"])}</b> vistas, '
               f'<b>{tot["seguidores"]}</b> seguidores nuevos, <b>{tot["mensajes"]}</b> mensajes y <b>{tot["ventas"]}</b> ventas.</p>')
    mejores = ''.join(tarjeta_pub(f, 'top') for f in r['mejores']) or '<p class="vacio">Todavía no hay publicaciones.</p>'
    flojas = ''.join(tarjeta_pub(f, 'floja') for f in r['flojas']) or '<p class="vacio">Con más publicaciones aparecen aquí las que menos funcionaron.</p>'
    por_quien = defaultdict(list)
    for c in r['consejos']:
        por_quien[c['para']].append(c)
    consejos_html = ''.join(
        f'<div class="consejo"><h3>Para {html.escape(NOMBRES.get(q, q))}</h3><ol>' +
        ''.join(f'<li><b>{html.escape(c["texto"])}</b><small>{html.escape(c["porque"])}</small></li>' for c in lista) + '</ol></div>'
        for q, lista in por_quien.items()) or '<p class="vacio">Sin consejos todavía.</p>'
    filas = ''.join(
        f'<tr><td>{f["fecha"]}</td><td>{html.escape(f["red"])}</td><td>{html.escape(f["tipo"])}</td><td>{html.escape(f.get("tema") or "")}</td>'
        f'<td class="n">{fmt_num(f["vistas"])}</td><td class="n">{fmt_pct(f["interaccion"])}</td><td class="n">{fmt_dec(f["valor"])}</td>'
        f'<td class="n">{f.get("mensajes") or 0}</td><td class="n"><b>{"—" if f["puntaje"] is None else f["puntaje"]}</b></td></tr>'
        for f in r['todas'])
    grupos = r['grupos']
    bloques = ''.join(
        f'<div class="caja"><h3>{t}</h3>{barras(grupos[c])}</div>'
        for c, t in (('tipo', 'Por tipo de publicación'), ('red', 'Por red'), ('dia', 'Por día'),
                     ('franja', 'Por horario (mañana 6-12 h, tarde 12-18 h, noche 18-24 h)'), ('duracion', 'Por duración del video'), ('pilar', 'Por pilar del plan'))
        if grupos[c])
    return PLANTILLA.format(
        fecha=r['fecha'], desde=r['desde'], dias=r['dias'], kpis=kpis, totales=totales, mejores=mejores,
        flojas=flojas, consejos=consejos_html, bloques=bloques or '<p class="vacio">Todavía no hay suficientes publicaciones.</p>',
        seguidores=grafico_seguidores(r['crecimiento']), filas=filas or '<tr><td colspan="9">Sin publicaciones</td></tr>',
        ref_i=f'{REF_INTERACCION[0]:g} a {REF_INTERACCION[1]:g}%', ref_v=f'{REF_VALOR[0]:g} a {REF_VALOR[1]:g}',
        ref_r=f'{REF_RETENCION[0]} a {REF_RETENCION[1]}%')


PLANTILLA = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Redes de Isabella · {fecha}</title>
<style>
:root{{--fondo:#eef3fb;--superficie:#ffffff;--tinta:#0f1b33;--suave:#4f6285;--tenue:#7f8fa9;--pista:#e3eaf6;--borde:#dbe4f3;--acento:#2f6bff;
  --bien:#14996b;--aviso:#b26f00;--mal:#d0453b;--barra:#2f6bff;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--fondo:#081226;--superficie:#0f1e3a;--tinta:#e8f0ff;--suave:#a9b9d8;--tenue:#7f90b3;--pista:#1c2e52;--borde:#1f335a;--acento:#5b94ff;
  --bien:#3fd39b;--aviso:#f2b64c;--mal:#ff7b70;--barra:#5b94ff;color-scheme:dark}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--fondo);color:var(--tinta);font:15px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}}
.pagina{{max-width:1180px;margin:0 auto;padding:28px 16px 60px}}
.caja{{background:var(--superficie);border:1px solid var(--borde);border-radius:20px;padding:20px}}
.titulo small{{text-transform:uppercase;letter-spacing:.14em;color:var(--acento);font-weight:700;font-size:12px}}
.titulo h1{{margin:6px 0 4px;font-size:30px;line-height:1.15}} .titulo p{{margin:0;color:var(--suave)}}
.totales{{margin:14px 0 0;font-size:16px}}
.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:16px}}
.kpi{{background:var(--superficie);border:1px solid var(--borde);border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:2px}}
.kpi>span{{font-size:12px;color:var(--tenue);text-transform:uppercase;letter-spacing:.06em}} .kpi b{{font-size:26px}}
.kpi small{{color:var(--suave);font-size:12px;margin-top:4px}}
.tend{{display:inline-block;font-size:12px;font-weight:600;padding:1px 8px;border-radius:99px;background:var(--pista);color:var(--suave);width:max-content}}
.tend.sube{{color:var(--bien)}} .tend.baja{{color:var(--mal)}}
.estado{{display:inline-block;font-size:12px;font-weight:700;padding:1px 8px;border-radius:99px;background:var(--pista);width:max-content;margin-top:4px}}
.estado.bien{{color:var(--bien)}} .estado.aviso{{color:var(--aviso)}} .estado.mal{{color:var(--mal)}}
h2.sec{{margin:36px 0 12px;font-size:21px}} h2.sec small{{display:block;font-size:13px;color:var(--suave);font-weight:400}}
h3{{margin:0 0 12px;font-size:16px}} h4{{margin:12px 0 4px;font-size:14px}}
.dos{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} .rejilla{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:16px}}
.pub{{display:grid;grid-template-columns:64px 1fr auto;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--borde)}}
.pub:last-child{{border-bottom:0}} .pub img,.sin-foto{{width:64px;height:84px;border-radius:10px;object-fit:cover;object-position:top;border:1px solid var(--borde);background:var(--pista)}}
.sin-foto{{display:grid;place-items:center;color:var(--tenue);font-weight:700}}
.pub b{{display:block}} .pub small{{color:var(--tenue)}} .pub p{{margin:2px 0 0;font-size:13px;color:var(--suave)}} .pub .porque{{color:var(--tinta)}}
.pub .nota{{font-size:22px;font-weight:800;min-width:52px;text-align:center;border-radius:12px;padding:6px;background:var(--pista)}}
.pub.top .nota{{color:var(--bien)}} .pub.floja .nota{{color:var(--mal)}}
.consejos{{display:grid;align-items:start;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr));gap:16px}}
.consejo{{background:var(--superficie);border:1px solid var(--borde);border-left:5px solid var(--acento);border-radius:16px;padding:16px}}
.consejo ol{{margin:0;padding-left:20px}} .consejo li{{margin-bottom:8px}} .consejo small{{display:block;color:var(--suave)}}
.barras{{display:flex;flex-direction:column;gap:10px}} .fila-barra{{display:grid;grid-template-columns:96px 1fr 76px;gap:10px;align-items:center;font-size:14px}}
.fila-barra .pista{{position:relative;height:14px;background:var(--pista);border-radius:4px;overflow:hidden}}
.fila-barra .pista i{{display:block;height:100%;border-radius:0 4px 4px 0;background:var(--barra)}}
.fila-barra .pista em{{position:absolute;left:50%;top:-2px;bottom:-2px;border-left:2px dashed var(--tenue)}}
.fila-barra small{{color:var(--suave)}} .nom{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}} .val{{text-align:right}}
.grafico{{width:100%;height:auto}} .guia{{stroke:var(--borde)}} .eje{{fill:var(--tenue);font-size:14px}}
.linea{{fill:none;stroke:var(--barra);stroke-width:2}} .marca{{fill:var(--barra);stroke:var(--superficie);stroke-width:2}}
.vacio,.pie{{color:var(--suave);font-size:14px}}
.tabla-scroll{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;color:var(--tenue);font-size:12px;text-transform:uppercase;letter-spacing:.06em}} th,td{{padding:8px 6px;border-bottom:1px solid var(--borde)}} .n{{text-align:right}}
#tip{{position:fixed;pointer-events:none;background:var(--tinta);color:var(--superficie);font-size:13px;padding:6px 10px;border-radius:8px;max-width:320px;opacity:0;transition:opacity .12s;z-index:9}}
@media (max-width:900px){{.kpis{{grid-template-columns:1fr 1fr}} .dos{{grid-template-columns:1fr}} .fila-barra{{grid-template-columns:90px 1fr 76px}} .titulo h1{{font-size:24px}}}}
</style></head><body><div class="pagina">
<header class="caja titulo"><small>La Analista de redes de Isa</small><h1>Cómo le fue a Isabella en redes</h1>
<p>Del {desde} al {fecha} ({dias} días), comparado con los {dias} días anteriores.</p>{totales}</header>
<div class="kpis">{kpis}</div>
<h2 class="sec">Qué hacer la próxima semana<small>Cada agente lee sus consejos antes de trabajar.</small></h2>
<div class="consejos">{consejos}</div>
<div class="dos">
  <div><h2 class="sec">Lo que mejor funcionó<small>Puntaje: 50 es lo normal de Isabella, 100 es el doble o más.</small></h2><div class="caja">{mejores}</div></div>
  <div><h2 class="sec">Lo que menos funcionó<small>Para aprender, no para preocuparse.</small></h2><div class="caja">{flojas}</div></div>
</div>
<h2 class="sec">Qué funciona mejor<small>Puntaje promedio; la raya punteada es lo normal de Isabella (50).</small></h2>
<div class="rejilla">{bloques}</div>
<h2 class="sec">Seguidores</h2><div class="caja">{seguidores}</div>
<h2 class="sec">Todas las publicaciones</h2>
<div class="caja tabla-scroll"><table><thead><tr><th>Fecha</th><th>Red</th><th>Tipo</th><th>Tema</th><th class="n">Vistas</th><th class="n">Reacciona</th><th class="n">Guardan+comp. /100</th><th class="n">Mensajes</th><th class="n">Puntaje</th></tr></thead><tbody>{filas}</tbody></table></div>
<p class="pie">Referencias aproximadas para cuentas que empiezan: reacciona {ref_i} es lo normal; guardan o comparten {ref_v} por cada 100 vistas; ven del video {ref_r}.
Los números salen de las capturas de Instagram y TikTok que mandó Isabella.</p>
</div><div id="tip"></div>
<script>
const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el=>{{
  el.addEventListener('mousemove',e=>{{tip.textContent=el.dataset.tip;tip.style.opacity=1;tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+14)+'px';}});
  el.addEventListener('mouseleave',()=>tip.style.opacity=0);
}});
</script></body></html>'''


def cmd_informe(a):
    hasta = fecha_valida(a.hasta) if a.hasta else HOY
    r = analizar(a.dias, hasta)
    INFORMES.mkdir(parents=True, exist_ok=True)
    base = INFORMES / r['fecha']
    escribir_json(base.with_suffix('.json'), r)
    base.with_suffix('.html').write_text(informe_html(r), encoding='utf-8')
    if COMPARTIDO.is_dir():
        destino = COMPARTIDO / 'redes'
        destino.mkdir(exist_ok=True)
        shutil.copy(base.with_suffix('.html'), destino / f'{r["fecha"]}.html')
    res = r['resumen']
    print(f'Informe del {r["desde"]} al {r["fecha"]}: {r["publicaciones"]} publicaciones ({r["por_semana"]} por semana).')
    print(f'Vistas promedio {fmt_num(res["vistas"])} · reacciona {fmt_pct(res["interaccion"])} · '
          f'guardan o comparten {fmt_dec(res["valor"])} por 100 vistas · '
          f'ven el {fmt_pct(res["retencion"], 0)} del video')
    for f in r['mejores']:
        print(f'  MEJOR  {f["puntaje"]:>3} · {f["fecha"]} {f["red"]} {f["tipo"]} «{f["tema"]}»: {f["porque"]}')
    for f in r['flojas']:
        print(f'  FLOJA  {f["puntaje"]:>3} · {f["fecha"]} {f["red"]} {f["tipo"]} «{f["tema"]}»: {f["porque"]}')
    for c in r['consejos']:
        print(f'  CONSEJO para {c["para"]}: {c["texto"]} — {c["porque"]}')
    print(f'\nInforme visual: {ruta_rel(base.with_suffix(".html"))}')


def ultimo_informe():
    archivos = sorted(INFORMES.glob('*.json'))
    return leer_json(archivos[-1]) if archivos else None


def cmd_consejos(a):
    r = ultimo_informe()
    if not r:
        print('La Analista todavía no tiene informes de redes.')
        return
    mios = [c for c in r.get('consejos', []) if c['para'] == a.agente]
    if not mios:
        print(f'La Analista no tiene consejos nuevos para {a.agente} (informe del {r["fecha"]}).')
        return
    print(f'Consejos de la Analista de redes para {a.agente} (informe del {r["fecha"]}, úsalos en este trabajo):')
    for i, c in enumerate(mios, 1):
        print(f'  {i}. {c["texto"]} ({c["porque"]})')


def main():
    ap = argparse.ArgumentParser(description='La Analista de redes de Isa')
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('agregar', help='guardar los números de una publicación')
    g.add_argument('--red', required=True, choices=REDES)
    g.add_argument('--tipo', required=True, choices=TIPOS)
    g.add_argument('--fecha', help='AAAA-MM-DD (cuándo se publicó)')
    g.add_argument('--hora', help='HH:MM')
    g.add_argument('--tema', help='de qué trataba, en pocas palabras')
    g.add_argument('--producto')
    g.add_argument('--enlace')
    g.add_argument('--nota', help='algo que contó Isabella')
    for m in METRICAS:
        g.add_argument('--' + m.replace('_', '-'), dest=m, type=float if m in ('seg_promedio', 'completo', 'duracion') else int,
                       help={'seg_promedio': 'segundos que lo ven en promedio', 'completo': '% que lo vio completo',
                             'duracion': 'segundos que dura el video', 'seguidores': 'seguidores que ganó con esta publicación'}.get(m))
    g.add_argument('--captura', nargs='*', help='las capturas de donde salen los números')
    g.add_argument('--plan', help='plan del estratega (si no, la busca por fecha y red)')
    g.add_argument('--id', help='id de la publicación en el plan')
    g.add_argument('--sin-plan', action='store_true', help='no buscarla en los planes')
    g.set_defaults(f=cmd_agregar)
    c = sub.add_parser('cuenta', help='seguidores y datos del perfil en una fecha')
    c.add_argument('--red', required=True, choices=REDES)
    c.add_argument('--seguidores', required=True, type=int)
    c.add_argument('--fecha')
    c.add_argument('--alcance', type=int)
    c.add_argument('--visitas-perfil', dest='visitas_perfil', type=int)
    c.add_argument('--interacciones', type=int)
    c.set_defaults(f=cmd_cuenta)
    sub.add_parser('pendientes', help='capturas sin leer y publicaciones sin números').set_defaults(f=cmd_pendientes)
    sub.add_parser('lista', help='todo lo guardado').set_defaults(f=cmd_lista)
    i = sub.add_parser('informe', help='informe visual y consejos para el equipo')
    i.add_argument('--dias', type=int, default=30)
    i.add_argument('--hasta', help='AAAA-MM-DD (por defecto hoy)')
    i.set_defaults(f=cmd_informe)
    k = sub.add_parser('consejos', help='lo que un agente lee antes de trabajar')
    k.add_argument('agente')
    k.set_defaults(f=cmd_consejos)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
