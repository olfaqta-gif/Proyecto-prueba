"""Música y efectos sintetizados para los anuncios (sin samples ni licencias).

Cada estilo tiene su propia receta y lee la misma línea de tiempo que su plantilla HTML
(plantilla/estilos/<estilo>/tiempos.json), así que cada whoosh, pop e impacto cae justo
en su animación aunque se muevan los tiempos.

    clasico   100 bpm, electrónica con "drop" cuando aparece el producto
    favorito  118 bpm, pop alegre con plucks y chasquidos (tipo TikTok)
    razones   84 bpm, lo-fi relajado con piano eléctrico y vinilo

Uso directo:  python3 sonido.py <estilo> salida.wav
Desde generar.py:  sonido.generar(tiempos, 'audio.wav', estilo, ficha)
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000


def t_(dur):
    return np.arange(int(SR * dur)) / SR


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x)


def sweep(x, f0, f1, bw=0.6):
    """Pasabanda que barre de f0 a f1 (por bloques)."""
    out = np.zeros_like(x)
    blk = 512
    nb = int(np.ceil(len(x) / blk))
    zi = np.zeros((2, 2))
    for b in range(nb):
        f = f0 * (f1 / f0) ** (b / max(nb - 1, 1))
        sos = butter(2, [f * (1 - bw / 2), min(f * (1 + bw / 2), SR / 2 - 100)], 'bandpass', fs=SR, output='sos')
        out[b * blk:(b + 1) * blk], zi = sosfilt(sos, x[b * blk:(b + 1) * blk], zi=zi)
    return out


def note(n):  # midi -> Hz
    return 440 * 2 ** ((n - 69) / 12)


def generar(T, salida, estilo='clasico', F=None):
    rng = np.random.default_rng(7)
    D = T['duracion']
    N = int(SR * D)
    music = np.zeros((N, 2))
    sfx = np.zeros((N, 2))
    verb_send = np.zeros((N, 2))

    def place(bus, sig, at, gain=1.0, pan=0.0, send=0.0):
        i = int(at * SR)
        if i >= N:
            return
        sig = sig[: N - i]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        st = np.stack([sig * l, sig * r], axis=1) * gain * 1.41
        bus[i:i + len(sig)] += st
        if send:
            verb_send[i:i + len(sig)] += st * send

    # ---------- instrumentos ----------
    def kick(dur=0.45, f0=130, f1=42):
        t = t_(dur)
        f = f1 + (f0 - f1) * np.exp(-t * 28)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
        s[:200] += rng.standard_normal(200) * np.linspace(.5, 0, 200)
        return s

    def clap():
        t = t_(0.25)
        n = filt(rng.standard_normal(len(t)), 'bandpass', [900, 5000])
        env = np.zeros(len(t))
        for k, o in enumerate([0, .011, .022]):
            i = int(o * SR)
            env[i:] = np.maximum(env[i:], np.exp(-t[: len(t) - i] * (60 if k < 2 else 16)))
        return n * env

    def hat(open_=False):
        t = t_(0.18 if open_ else 0.05)
        return filt(rng.standard_normal(len(t)), 'highpass', 7500) * np.exp(-t * (18 if open_ else 80))

    def supersaw(freq, dur, voices=5, det=0.12):
        t = t_(dur)
        s = np.zeros(len(t))
        for v in range(voices):
            f = freq * 2 ** ((v - (voices - 1) / 2) * det / 12)
            s += 2 * ((t * f + rng.random()) % 1) - 1
        return s / voices

    def bell(freq, dur=1.6):
        t = t_(dur)
        s = (np.sin(2 * np.pi * freq * t) + .5 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
             + .25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 12))
        return s * np.exp(-t * 3.2) * np.minimum(t * 400, 1)

    # ---------- efectos ----------
    def whoosh(dur=0.6, up=True, f0=300, f1=6000):
        t = t_(dur)
        n = rng.standard_normal(len(t))
        s = sweep(n, f0, f1) if up else sweep(n, f1, f0)
        return s * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2

    def riser(dur=2.0):
        t = t_(dur)
        n = sweep(rng.standard_normal(len(t)), 200, 9000, bw=0.5)
        tone = np.sin(2 * np.pi * np.cumsum(180 * (8 ** (t / dur))) / SR) * 0.35
        return (n + tone) * (t / dur) ** 2.2

    def impact(dur=1.8, deep=True):
        t = t_(dur)
        f = 28 + 90 * np.exp(-t * 9)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
        crack = filt(rng.standard_normal(len(t)), 'lowpass', 2500) * np.exp(-t * 14)
        return np.tanh((boom * (1.3 if deep else .8) + crack * .7) * 1.6)

    def pop(freq=700):
        t = t_(0.14)
        f = freq * (1 + 0.9 * np.exp(-t * 60))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32)

    def shimmer(base=88, steps=(0, 7, 12, 16, 19, 24), gap=0.045):
        out = np.zeros(int(SR * (gap * len(steps) + 1.6)))
        for k, s in enumerate(steps):
            b = bell(note(base + s), 1.4) * (0.9 - k * 0.08)
            i = int(k * gap * SR)
            out[i:i + len(b)] += b
        return out

    def pluck(freq, dur=0.35, brillo=3500):
        t = t_(dur)
        s = supersaw(freq, dur, 3, 0.06) + 0.5 * np.sin(2 * np.pi * freq * 2 * t)
        return filt(s, 'lowpass', brillo) * np.exp(-t * 11) * np.minimum(t * 800, 1)

    def snap():
        t = t_(0.12)
        return filt(rng.standard_normal(len(t)), 'bandpass', [1800, 6000]) * np.exp(-t * 55)

    def epiano(freq, dur=2.0):
        """Piano eléctrico suave (tipo Rhodes) con trémolo."""
        t = t_(dur)
        s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 3)
             + 0.12 * np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 6))
        trem = 1 - 0.18 * (1 + np.sin(2 * np.pi * 4.5 * t)) / 2
        return s * trem * np.exp(-t * 1.1) * np.minimum(t * 300, 1) * np.minimum((dur - t) * 20, 1)

    def snare_lofi():
        t = t_(0.3)
        n = filt(rng.standard_normal(len(t)), 'bandpass', [1200, 5000]) * np.exp(-t * 18)
        tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
        return filt(n * 0.8 + tone * 0.5, 'lowpass', 4000)

    def vinilo(dur):
        n = len(t_(dur))
        hiss = filt(rng.standard_normal(n), 'bandpass', [800, 6000]) * 0.04
        pops = np.zeros(n)
        idx = rng.integers(0, n, int(dur * 9))
        pops[idx] = rng.uniform(-1, 1, len(idx))
        return hiss + filt(pops, 'highpass', 1500) * 0.6

    def tick():
        t = t_(0.05)
        return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120)

    m = SimpleNamespace(**{k: v for k, v in locals().items() if callable(v)},
                        rng=rng, music=music, sfx=sfx, N=N, D=D)
    duck = RECETAS[estilo](m, T, F or {})

    # ---------- mezcla ----------
    ir_t = t_(2.2)
    ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 3.0)[:, None]
    for ch in range(2):
        ir[:, ch] = filt(ir[:, ch], 'lowpass', 6000)
    verb = np.stack([fftconvolve(verb_send[:, ch], ir[:, ch])[:N] for ch in range(2)], axis=1)
    verb /= np.max(np.abs(verb)) + 1e-9
    mix = music * duck[:, None] + sfx + verb * 0.18
    mix = filt(mix.T, 'highpass', 28).T
    fade = np.ones(N)
    fade[-int(1.0 * SR):] = np.linspace(1, 0, int(1.0 * SR)) ** 2
    mix *= fade[:, None]
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    mix /= np.max(np.abs(mix)) / 0.95
    wavfile.write(salida, SR, (mix * 32767).astype(np.int16))
    return salida




def clasico(m, T, F):
    """100 bpm, el golpe cae en el flash (gancho -> producto)."""
    place, music, sfx, rng, N, D = m.place, m.music, m.sfx, m.rng, m.N, m.D
    kick, clap, hat, supersaw, bell = m.kick, m.clap, m.hat, m.supersaw, m.bell
    whoosh, riser, impact, pop, shimmer = m.whoosh, m.riser, m.impact, m.pop, m.shimmer
    BEAT = 0.6
    DROP = T['flash']
    g, p, b, c = T['gancho'], T['producto'], T['beneficios'], T['cierre']
    chords = [(0.0, [57, 60, 64]), (DROP, [57, 60, 64]), (b['entra'], [53, 57, 60]),
              (c['entra'] - 1.8, [55, 59, 62]), (c['entra'], [60, 64, 67])]
    ends = [x[0] for x in chords[1:]] + [D]
    for (st, notes), en in zip(chords, ends):
        dur = en - st + 0.4
        t = t_(dur)
        pad = sum(supersaw(note(n), dur) for n in notes + [notes[0] + 12])
        pad = filt(pad, 'lowpass', 900 if st < DROP else 2200)
        att = 1.8 if st == 0 else 0.15
        env = np.minimum(t / att, 1) * np.minimum((dur - t) / 0.4, 1)
        place(music, pad * env, st, gain=0.11 if st < DROP else 0.085, send=0.5)

    drum_end = D - 1.4
    drum_times = np.arange(DROP, drum_end, BEAT)
    for bt in drum_times:
        k = round((bt - DROP) / BEAT)
        place(music, kick(), bt, 0.72)
        if k % 2 == 1:
            place(music, clap(), bt, 0.35, send=0.25)
        place(music, hat(open_=(k % 4 == 3)), bt + BEAT / 2, 0.16, pan=0.3)
        root = [n[0] for s, n in chords if s <= bt + 1e-6][-1]
        for h in (0, BEAT / 2):
            t = t_(BEAT / 2)
            bass = np.sin(2 * np.pi * note(root - 24) * t) + 0.3 * supersaw(note(root - 24), BEAT / 2, 2)
            bass = bass * np.minimum(t * 300, 1) * np.exp(-t * 4) * np.minimum((t[-1] - t) * 200, 1)
            place(music, bass, bt + h, 0.22)

    duck = ducking(N, drum_times)

    # ---------- efectos en los tiempos de cada animación ----------
    for at in (g['kicker'], g['linea1'], g['linea2']):
        place(sfx, whoosh(0.45, True, 400, 3500), at - 0.08, 0.10, pan=rng.uniform(-.3, .3), send=0.3)
    place(sfx, riser(DROP - 0.6), 0.6, 0.28, send=0.4)
    place(sfx, impact(), DROP, 0.85, send=0.5)
    place(sfx, shimmer(84), DROP, 0.10, pan=0.2, send=0.6)
    place(sfx, pop(620), p['halo'], 0.55)
    place(sfx, shimmer(91), p['halo'] + 0.05, 0.19, pan=0.25, send=0.6)
    place(sfx, whoosh(0.4, True, 600, 7000), p['nombre'] - 0.05, 0.12, pan=-0.4)
    place(sfx, pop(880), p['dato'], 0.3, pan=0.3)
    place(sfx, whoosh(0.7, False), b['entra'] - 0.25, 0.20, send=0.4)
    for k, key in enumerate(('b1', 'b2', 'b3')):
        place(sfx, impact(0.7, deep=False), b[key], 0.40)
        place(sfx, pop(420 * 2 ** (k * 4 / 12)), b[key], 0.28)
    place(sfx, whoosh(0.8, False), c['entra'] - 0.4, 0.22, send=0.4)
    place(sfx, impact(), c['marca'], 0.75, send=0.55)
    place(sfx, pop(700), c['mini'], 0.45)
    for n in (84, 88, 91, 96):                     # campanita del botón
        place(sfx, bell(note(n), 2.2), c['boton'], 0.10, send=0.6)
    place(sfx, shimmer(91), c['aviso'], 0.08, send=0.6)
    t = t_(2.6)                                    # acorde final sostenido
    final = sum(supersaw(note(n), 2.6) for n in (60, 64, 67, 72))
    place(music, filt(final, 'lowpass', 2500) * np.exp(-t * 1.0) * np.minimum(t * 50, 1), drum_end, 0.12, send=0.7)

    return duck


def ducking(N, golpes, prof=0.55):
    """La música "respira" con cada bombo."""
    duck = np.ones(N)
    for bt in golpes:
        i = int(bt * SR)
        seg = 1 - prof * np.exp(-t_(0.3) * 14)
        duck[i:i + len(seg)] = np.minimum(duck[i:i + len(seg)], seg[: N - i])
    return duck


def favorito(m, T, F):
    """118 bpm, pop alegre: plucks en arpegio desde el primer cuadro, el ritmo entra con la respuesta."""
    place, music, sfx, rng, N, D = m.place, m.music, m.sfx, m.rng, m.N, m.D
    BEAT = 60 / T.get('bpm', 118)
    g, p, b, c = T['gancho'], T['producto'], T['beneficios'], T['cierre']
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]      # C G Am F
    bar = 4 * BEAT
    fin = D - 1.3
    # arpegio de plucks en semicorcheas
    k = 0
    t = 0.0
    while t < fin:
        ch = chords[int(t / bar) % 4]
        n = (ch + [ch[0] + 12])[[0, 1, 2, 3, 2, 1, 0, 2][k % 8]] + 12
        place(music, m.pluck(note(n), 0.3, 2500 if t < g['linea2'] else 4200), t, 0.16, pan=0.35 * np.sin(k), send=0.3)
        k += 1
        t += BEAT / 4
    # acordes suaves de fondo
    for i in range(int(fin / bar) + 1):
        st = i * bar
        dur = min(bar, fin - st) + 0.3
        if dur <= 0.3:
            break
        tt = t_(dur)
        pad = sum(m.supersaw(note(n), dur, 4, 0.1) for n in chords[i % 4])
        place(music, filt(pad, 'lowpass', 1600) * np.minimum(tt / 0.05, 1) * np.minimum((dur - tt) / 0.3, 1), st, 0.05, send=0.4)
    # ritmo: entra con la respuesta del gancho
    golpes = np.arange(g['linea2'], fin, BEAT)
    for i, bt in enumerate(golpes):
        place(music, m.kick(0.35, 150, 50), bt, 0.62)
        if i % 2 == 1:
            place(music, m.snap(), bt, 0.32, pan=-0.2, send=0.3)
            place(music, m.clap(), bt, 0.18, send=0.2)
        place(music, m.hat(), bt + BEAT / 2, 0.13, pan=0.3)
        root = chords[int(bt / bar) % 4][0] - 24
        tt = t_(BEAT * 0.9)
        place(music, np.sin(2 * np.pi * note(root) * tt) * np.exp(-tt * 3) * np.minimum(tt * 300, 1), bt + BEAT / 2, 0.3)
    # efectos
    palabras = len(str((F.get('gancho') or {}).get('linea1', '')).split())
    for i in range(palabras):
        place(sfx, m.pop(500 + 90 * (i % 5)), g['linea1'] + i * g.get('paso', 0.14), 0.32, pan=((i % 3) - 1) * 0.3)
    place(sfx, m.impact(0.9, deep=False), g['linea2'], 0.5, send=0.4)
    for at in (p['entra'], b['entra'], c['entra']):
        place(sfx, m.whoosh(0.5, True, 500, 8000), at - 0.15, 0.22, send=0.3)
    place(sfx, m.pop(660), p['tarjeta'] + 0.1, 0.4)
    place(sfx, m.pop(990), p['sticker'], 0.38, pan=0.4)
    place(sfx, m.shimmer(91), p['sticker'], 0.12, send=0.6)
    for i, key in enumerate(('b1', 'b2', 'b3')):
        place(sfx, m.whoosh(0.35, True, 800, 7000), b[key] - 0.08, 0.2, pan=-0.5 if i % 2 == 0 else 0.5)
        place(sfx, m.pop(520 * 2 ** (i * 4 / 12)), b[key] + 0.2, 0.3)
    place(sfx, m.pop(780), b['mini'], 0.3)
    place(sfx, m.impact(1.2), c['marca'], 0.55, send=0.5)
    for n in (84, 88, 91, 96):
        place(sfx, m.bell(note(n), 2.2), c['boton'], 0.1, send=0.6)
    place(sfx, m.shimmer(96), c['aviso'], 0.08, send=0.6)
    tt = t_(2.4)
    final = sum(m.pluck(note(n), 2.4, 3000) for n in (72, 76, 79, 84))
    place(music, final, fin, 0.2, send=0.7)
    return ducking(N, golpes, 0.45)


def razones(m, T, F):
    """84 bpm, lo-fi: piano eléctrico, batería con swing y vinilo; un "tic" y una campanita en cada número."""
    place, music, sfx, rng, N, D = m.place, m.music, m.sfx, m.rng, m.N, m.D
    BEAT = 60 / T.get('bpm', 84)
    SW = 0.58                                      # swing de las corcheas
    g, p, r, c = T['gancho'], T['producto'], T['razon'], T['cierre']
    chords = [[50, 53, 57, 60, 64], [43, 53, 57, 59, 64], [48, 52, 55, 59, 62], [45, 52, 55, 60, 64]]  # Dm9 G13 Cmaj9 Am7
    bar = 4 * BEAT
    fin = D - 1.0
    place(music, m.vinilo(D), 0, 0.5)
    for i in range(int(D / bar) + 1):
        st = i * bar
        if st >= fin:
            break
        ch = chords[i % 4]
        for j, n in enumerate(ch[1:]):              # acorde levemente arpegiado
            place(music, m.epiano(note(n + 12), bar + 0.4), st + j * 0.025, 0.09, pan=(j - 1.5) * 0.15, send=0.4)
        place(music, m.epiano(note(ch[3] + 24), 1.0), st + 2.5 * BEAT, 0.05, pan=0.4, send=0.6)
        tt = t_(2 * BEAT)
        for h in (0, 2 * BEAT):
            bass = np.sin(2 * np.pi * note(ch[0] - 12) * tt) * np.minimum(tt * 200, 1) * np.exp(-tt * 1.2)
            place(music, bass, st + h, 0.3)
    golpes = []
    for i in range(int(fin / bar) + 1):
        st = i * bar
        for at in (st, st + 1.5 * BEAT + (SW - 0.5) * BEAT):
            if g['numero'] - 0.01 <= at < fin:
                place(music, filt(m.kick(0.4, 110, 45), 'lowpass', 2500), at, 0.7)
                golpes.append(at)
        for h in (1, 3):
            if g['numero'] <= st + h * BEAT < fin:
                place(music, m.snare_lofi(), st + h * BEAT, 0.42, send=0.25)
        for e in range(8):
            at = st + (e // 2) * BEAT + (SW * BEAT if e % 2 else 0)
            if g['numero'] <= at < fin:
                place(music, filt(m.hat(), 'lowpass', 9000), at, 0.08 if e % 2 else 0.11, pan=0.25)
    # efectos
    place(sfx, m.impact(1.6), g['numero'], 0.45, send=0.45)
    for at in (g['linea1'], g['linea2']):
        place(sfx, m.whoosh(0.4, True, 400, 4000), at - 0.05, 0.1)
    place(sfx, m.whoosh(0.55, False), p['entra'] - 0.1, 0.2, send=0.3)
    place(sfx, m.pop(600), p['foto'], 0.35)
    n_razones = len((F.get('beneficios') or {}).get('lista') or []) or 3
    for i, key in enumerate(('r1', 'r2', 'r3')[:n_razones]):
        place(sfx, m.whoosh(0.5, True, 300, 6000), r[key] - 0.12, 0.18, pan=-0.3, send=0.3)
        place(sfx, m.tick(), r[key] + 0.15, 0.25)
        place(sfx, m.bell(note(84 + [0, 4, 7][i]), 1.8), r[key] + 0.15, 0.13, send=0.6)
    place(sfx, m.whoosh(0.7, False), c['entra'] - 0.2, 0.2, send=0.4)
    place(sfx, m.impact(1.2, deep=False), c['marca'], 0.45, send=0.5)
    place(sfx, m.pop(700), c['foto'], 0.35)
    for n in (79, 84, 88):
        place(sfx, m.bell(note(n), 2.2), c['boton'], 0.1, send=0.6)
    for j, n in enumerate((62, 65, 69, 72, 76)):  # acorde final
        place(music, m.epiano(note(n), 3.0), fin - 0.6 + j * 0.04, 0.09, send=0.6)
    return ducking(N, golpes, 0.35)


RECETAS = {'clasico': clasico, 'favorito': favorito, 'razones': razones}


if __name__ == '__main__':
    estilo = sys.argv[1] if len(sys.argv) > 1 else 'clasico'
    tiempos = json.loads((Path(__file__).parent / 'plantilla' / 'estilos' / estilo / 'tiempos.json').read_text())
    print(generar(tiempos, sys.argv[2] if len(sys.argv) > 2 else 'audio.wav', estilo))
