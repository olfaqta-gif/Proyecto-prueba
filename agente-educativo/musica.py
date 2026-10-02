"""Música para los videos educativos: cada video saca su propia canción.

Se elige (o se sortea con la variación) un ambiente, un tono, una velocidad, una progresión
de acordes y un patrón de arpegio y batería. Los efectos (whoosh, pops, tics, sellos,
campanitas) caen en los momentos que marca la línea de tiempo de generar.py y van afinados
en el tono de la canción. Los instrumentos son los de agente-contenido/sonido.py.

    suave      lo-fi con piano eléctrico, batería con swing y vinilo (76-90 bpm)
    fresco     pop con plucks en arpegio y chasquidos (100-114 bpm)
    energia    house: bombo en cada tiempo, bajo a contratiempo y acordes cortados (120-126 bpm)
    brillante  pop brillante: acordes anchos que "respiran", campanitas y medio tiempo (140-150 bpm)
"""
import random
import zlib

import numpy as np

import sonido
from sonido import filt, note, t_

AMBIENTES = {'suave': (76, 90), 'fresco': (100, 114), 'energia': (120, 126), 'brillante': (140, 150)}
POR_TIPO = {'tips': ['fresco', 'brillante', 'energia', 'suave'], 'mito': ['energia', 'fresco', 'brillante'],
            'pasos': ['suave', 'fresco', 'brillante'], 'dato': ['suave', 'brillante', 'fresco']}
NOMBRES = ['Do', 'Do#', 'Re', 'Mib', 'Mi', 'Fa', 'Fa#', 'Sol', 'Lab', 'La', 'Sib', 'Si']
# Progresiones de 4 acordes (semitonos desde la tónica). Las de 4 notas suenan más "jazz".
PROGRESIONES = [
    [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]],          # I V vi IV
    [[9, 12, 16], [5, 9, 12], [0, 4, 7], [7, 11, 14]],          # vi IV I V
    [[0, 4, 7], [9, 12, 16], [5, 9, 12], [7, 11, 14]],          # I vi IV V
    [[5, 9, 12], [0, 4, 7], [7, 11, 14], [9, 12, 16]],          # IV I V vi
    [[2, 5, 9, 12], [7, 11, 14, 17], [0, 4, 7, 11], [9, 12, 16, 19]],   # ii7 V7 Imaj7 vi7
    [[0, 4, 7, 11], [5, 9, 12, 16], [4, 7, 11, 14], [9, 12, 16, 19]],   # Imaj7 IVmaj7 iii7 vi7
]
ARPEGIOS = [[0, 1, 2, 3, 2, 1, 0, 2], [0, 2, 1, 3, 0, 2, 1, 3], [0, 1, 2, 1, 3, 2, 1, 2], [3, 2, 1, 0, 1, 2, 3, 2]]
ESCALA = [0, 2, 4, 5, 7, 9, 11]


def elegir(F, T, variacion=0):
    """Decide la canción de este video. Mismo guion + misma variación = misma canción."""
    pedido = (F.get('musica') or {}).get('ambiente')
    semilla = zlib.crc32((F['tipo'] + str(F['gancho']['titulo'])).encode()) + variacion * 104729
    r = random.Random(semilla)
    ambiente = pedido if pedido in AMBIENTES else r.choice(POR_TIPO[F['tipo']])
    lo, hi = AMBIENTES[ambiente]
    raiz = r.randrange(52, 64)                     # Mi3 … Re#4
    prog = r.randrange(len(PROGRESIONES)) if ambiente == 'suave' else r.randrange(4)
    return {'ambiente': ambiente, 'raiz': raiz, 'tono': NOMBRES[raiz % 12] + ' mayor', 'bpm': r.randint(lo, hi),
            'progresion': prog, 'arpegio': r.randrange(len(ARPEGIOS)), 'patron': r.randrange(3), 'semilla': semilla}


def generar(T, F, salida):
    sonido.RECETAS['edu'] = receta
    return sonido.generar(T, salida, 'edu', F)


def receta(m, T, F):
    cfg = T['musica']
    rng = np.random.default_rng(cfg['semilla'] % 2 ** 32)
    place, music, sfx, N, D = m.place, m.music, m.sfx, m.N, m.D
    R = cfg['raiz']
    prog = [[R + x for x in ch] for ch in PROGRESIONES[cfg['progresion']]]
    arp = ARPEGIOS[cfg['arpegio']]
    BEAT = 60 / cfg['bpm']
    bar = 4 * BEAT
    drop = T['drop']
    o = drop - int(drop / bar) * bar                # un compás empieza justo en el "drop"
    fin = D - 1.4

    def acorde(t):
        return prog[int(np.floor((t - o) / bar)) % 4]

    def escala(grado, octava=0):
        return R + 12 * (octava + grado // 7) + ESCALA[grado % 7]

    def compases(desde, hasta):
        k = int(np.floor((desde - o) / bar))
        while o + k * bar < hasta:
            yield o + k * bar
            k += 1

    golpes = []
    amb = cfg['ambiente']
    pat = cfg['patron']

    # ---------- armonía ----------
    if amb == 'suave':
        place(music, m.vinilo(D), 0, 0.45)
        for st in compases(0, fin):
            ch = acorde(st + 0.01)
            ini = max(st, 0)
            dur = st + bar - ini + 0.4
            for j, n in enumerate(ch):
                place(music, m.epiano(note(n + 12), dur), ini + j * 0.025, 0.085, pan=(j - 1.5) * 0.15, send=0.4)
            if st >= drop - 0.01:
                tt = t_(2 * BEAT)
                for h in (0, 2 * BEAT):
                    bass = np.sin(2 * np.pi * note(ch[0] - 12) * tt) * np.minimum(tt * 200, 1) * np.exp(-tt * 1.2)
                    place(music, bass, st + h, 0.3)
            if pat != 1 and st >= drop:
                place(music, m.epiano(note(ch[-1] + 24), 1.0), st + 2.5 * BEAT, 0.05, pan=0.4, send=0.6)
    else:
        for st in compases(0, fin):
            ch = acorde(st + 0.01)
            ini = max(st, 0)
            dur = min(st + bar, fin) - ini + 0.3
            if dur <= 0.3:
                continue
            tt = t_(dur)
            antes = st < drop - 0.01
            if amb == 'energia' and not antes:     # acordes cortados (stabs) a contratiempo
                for h in ([0.5, 1.5, 2.5, 3.5] if pat == 0 else [0.5, 1.25, 2.5, 3.0, 3.75]):
                    s = sum(m.supersaw(note(n + 12), 0.22, 3, 0.1) for n in ch)
                    tt2 = t_(0.22)
                    place(music, filt(s, 'lowpass', 3000) * np.exp(-tt2 * 9), st + h * BEAT, 0.06, send=0.3)
            else:
                pad = sum(m.supersaw(note(n + 12), dur, 4, 0.12) for n in ch)
                corte = 900 if antes else (2600 if amb == 'brillante' else 1600)
                place(music, filt(pad, 'lowpass', corte) * np.minimum(tt / 0.08, 1) * np.minimum((dur - tt) / 0.3, 1),
                      ini, 0.07 if amb == 'brillante' else 0.05, send=0.45)

    # ---------- arpegio ----------
    if amb in ('fresco', 'brillante'):
        paso = BEAT / (4 if amb == 'fresco' else 2)
        k = 0
        t = o - int(o / paso) * paso
        while t < fin:
            ch = acorde(t)
            notas = (ch + [ch[0] + 12])[:4] if len(ch) < 4 else ch[:4]
            n = notas[arp[k % 8] % len(notas)] + (12 if amb == 'fresco' else 24)
            if amb == 'fresco':
                place(music, m.pluck(note(n), 0.3, 2400 if t < drop else 4200), t, 0.15, pan=0.35 * np.sin(k), send=0.3)
            else:
                place(music, m.bell(note(n), 0.9), t, 0.05, pan=0.4 * np.sin(k * 0.7), send=0.5)
            k += 1
            t += paso

    # ---------- batería y bajo (desde el drop) ----------
    for st in compases(drop, fin):
        ch = acorde(st + 0.01)
        if amb == 'suave':
            SW = 0.58
            for at in (st, st + 1.5 * BEAT + (SW - 0.5) * BEAT) + ((st + 2.5 * BEAT,) if pat == 2 else ()):
                if at < fin:
                    place(music, filt(m.kick(0.4, 110, 45), 'lowpass', 2500), at, 0.65)
                    golpes.append(at)
            for h in (1, 3):
                if st + h * BEAT < fin:
                    place(music, m.snare_lofi(), st + h * BEAT, 0.4, send=0.25)
            for e in range(8):
                at = st + (e // 2) * BEAT + (SW * BEAT if e % 2 else 0)
                if at < fin:
                    place(music, filt(m.hat(), 'lowpass', 9000), at, 0.08 if e % 2 else 0.1, pan=0.25)
        elif amb == 'fresco':
            for b in range(4):
                at = st + b * BEAT
                if at >= fin:
                    break
                if pat == 0 or b % 2 == 0:
                    place(music, m.kick(0.35, 150, 50), at, 0.6)
                    golpes.append(at)
                if b % 2 == 1:
                    place(music, m.snap(), at, 0.3, pan=-0.2, send=0.3)
                    place(music, m.clap(), at, 0.16, send=0.2)
                place(music, m.hat(), at + BEAT / 2, 0.12, pan=0.3)
                if pat == 2:
                    place(music, m.hat(), at + BEAT / 4 * 3, 0.06, pan=-0.3)
                tt = t_(BEAT * 0.9)
                place(music, np.sin(2 * np.pi * note(ch[0] - 24) * tt) * np.exp(-tt * 3) * np.minimum(tt * 300, 1), at + BEAT / 2, 0.3)
        elif amb == 'energia':
            for b in range(4):
                at = st + b * BEAT
                if at >= fin:
                    break
                place(music, m.kick(0.4, 140, 45), at, 0.72)
                golpes.append(at)
                if b % 2 == 1:
                    place(music, m.clap(), at, 0.3, send=0.25)
                place(music, m.hat(open_=True), at + BEAT / 2, 0.12, pan=0.25)
                if pat != 0:
                    place(music, m.hat(), at + BEAT / 4, 0.05, pan=-0.25)
                tt = t_(BEAT / 2)
                bass = np.sin(2 * np.pi * note(ch[0] - 24) * tt) + 0.35 * m.supersaw(note(ch[0] - 24), BEAT / 2, 2)
                place(music, filt(bass, 'lowpass', 900) * np.minimum(tt * 300, 1) * np.exp(-tt * 5), at + BEAT / 2, 0.26)
        else:  # brillante, medio tiempo: bombo en 1 y "3 y medio", caja en 3
            for at, cosa in ((st, 'k'), (st + 1.5 * BEAT, 'k' if pat else None), (st + 2 * BEAT, 's'), (st + 3.5 * BEAT, 'k')):
                if cosa and at < fin:
                    if cosa == 'k':
                        place(music, m.kick(0.45, 130, 42), at, 0.7)
                        golpes.append(at)
                    else:
                        place(music, m.clap(), at, 0.38, send=0.35)
                        place(music, m.snare_lofi(), at, 0.25)
            for e in range(8):
                at = st + e * BEAT / 2
                if at < fin:
                    place(music, m.hat(), at, 0.07 if e % 2 else 0.1, pan=0.3)
            tt = t_(bar)
            bass = np.sin(2 * np.pi * note(ch[0] - 24) * tt) * np.minimum(tt * 100, 1) * np.minimum((bar - tt) * 20, 1)
            place(music, bass, st, 0.22)

    # ---------- efectos en los tiempos de la animación ----------
    if amb in ('energia', 'brillante') and drop > 1.2:
        place(sfx, m.riser(drop - 0.6), 0.6, 0.18, send=0.4)
    place(sfx, m.impact(1.2, deep=amb != 'suave'), drop, 0.4, send=0.4)
    for e in T['eventos']:
        at, que = e[0], e[1]
        if que == 'intro':
            place(sfx, m.shimmer(escala(0, 2) + 12, gap=0.05), 0.02, 0.07, send=0.6)
        elif que == 'pop':
            place(sfx, m.pop(rng.uniform(520, 900)), at, 0.32, pan=rng.uniform(-.3, .3))
        elif que == 'palabras':
            n, paso = e[2], e[3]
            for k in range(n):
                f = note(escala(k % 5, 2))
                place(sfx, m.pop(f * 0.5), at + k * paso, 0.12, pan=((k % 3) - 1) * 0.3)
        elif que == 'golpe':
            place(sfx, m.impact(0.8, deep=False), at, 0.42, send=0.35)
        elif que == 'tic':
            place(sfx, m.tick(), at, 0.22, pan=rng.uniform(-.3, .3))
        elif que == 'whoosh':
            place(sfx, m.whoosh(0.5, True, 400, 7000), at, 0.2, pan=rng.uniform(-.4, .4), send=0.3)
        elif que == 'ding':
            place(sfx, m.bell(note(escala(rng.choice([0, 2, 4]), 3)), 1.6), at, 0.11, pan=0.2, send=0.6)
        elif que == 'cuenta':                      # tics que se aceleran mientras sube el número
            for k in range(14):
                frac = 1 - (1 - k / 14) ** 1.6
                place(sfx, m.tick(), at + frac * 1.25, 0.12 + 0.01 * k)
            place(sfx, m.bell(note(escala(4, 3)), 1.8), at + 1.3, 0.13, send=0.6)
        elif que == 'sello':
            place(sfx, m.impact(1.0, deep=True), at, 0.55, send=0.3)
            place(sfx, m.clap(), at, 0.3)
        elif que == 'giro':
            place(sfx, m.whoosh(0.7, True, 300, 6000), at, 0.25, send=0.4)
        elif que == 'bien':
            for k, g in enumerate((0, 2, 4, 7)):
                place(sfx, m.bell(note(escala(g, 3)), 1.6), at + k * 0.07, 0.1, send=0.6)
        elif que == 'boton':
            for g in (0, 2, 4, 7):
                place(sfx, m.bell(note(escala(g, 3)), 2.2), at, 0.09, send=0.6)
        elif que == 'final':
            tt = t_(2.6)
            final = sum(m.supersaw(note(n + 12), 2.6, 4, 0.1) for n in prog[0]) if amb != 'suave' else \
                sum(m.epiano(note(n + 12), 2.6) for n in prog[0])
            place(music, filt(final, 'lowpass', 2400) * np.exp(-tt * 1.0) * np.minimum(tt * 40, 1), at, 0.1, send=0.7)
    prof = {'suave': 0.3, 'fresco': 0.45, 'energia': 0.6, 'brillante': 0.65}[amb]
    return sonido.ducking(N, golpes, prof)
