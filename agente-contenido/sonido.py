"""Música y efectos sintetizados para la plantilla de anuncio (sin samples ni licencias).

Lee la misma línea de tiempo que la plantilla HTML (plantilla/tiempos.json), así que
cada whoosh, pop e impacto cae justo en su animación aunque se muevan los tiempos.

Uso directo:  python3 sonido.py salida.wav
Desde generar.py:  sonido.generar(tiempos, 'audio.wav')
"""
import json
import sys
from pathlib import Path

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


def generar(T, salida):
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

    # ---------- música: 100 bpm, el golpe cae en el flash (gancho -> producto) ----------
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

    duck = np.ones(N)  # la música "respira" con cada bombo
    for bt in drum_times:
        i = int(bt * SR)
        seg = 1 - 0.55 * np.exp(-t_(0.3) * 14)
        duck[i:i + len(seg)] = np.minimum(duck[i:i + len(seg)], seg[: N - i])

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


if __name__ == '__main__':
    tiempos = json.loads((Path(__file__).parent / 'plantilla' / 'tiempos.json').read_text())
    print(generar(tiempos, sys.argv[1] if len(sys.argv) > 1 else 'audio.wav'))
