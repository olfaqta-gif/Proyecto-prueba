"""Música corporativa y efectos sincronizados para el showcase (sintetizados, sin licencias).

Lee la línea de tiempo que exporta la animación (eventos.json) y coloca cada efecto donde
ocurre: whoosh en cada cambio de pantalla, clic en cada toque, teclas al escribir, obturador
en las fotos, campanitas en los tips y en cada validación, y un golpe con brillo en el logo.

    python3 musica.py eventos.json audio.wav
"""
import json
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 108
BEAT = 60 / BPM
rnd = np.random.default_rng(7)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x)


def add(buf, sig, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    sig = sig[:len(buf) - i]
    buf[i:i + len(sig)] += sig * gain


def env(n, a=.005, r=.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)


def tono(f, dur, a=.005, r=.2, harm=(1, .3, .1)):
    t = np.arange(int(dur * SR)) / SR
    s = sum(h * np.sin(2 * np.pi * f * (k + 1) * t) for k, h in enumerate(harm))
    return s * env(len(t), a, r)


def ruido(dur):
    return rnd.standard_normal(int(dur * SR))


# ---------- Instrumentos ----------
def pad(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for m in notas:
        for d in (-.08, 0, .08):
            f = hz(m + d)
            s += 2 * ((t * f) % 1) - 1
    s = filt(s / (len(notas) * 3), 'low', 1400)
    a = np.minimum(1, t / .6) * np.minimum(1, (dur - t) / .5).clip(0)
    return s * a


def pluck(m, dur=.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t + .8 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 12))
    return s * env(len(t), .002, .16)


def bajo(m, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.tanh(1.6 * np.sin(2 * np.pi * hz(m) * t))
    return filt(s, 'low', 500) * np.minimum(1, t / .01) * np.exp(-t / (dur * .8))


def bombo():
    t = np.arange(int(.35 * SR)) / SR
    f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def palmas():
    s = filt(ruido(.22), 'band', [900, 3500]) * env(int(.22 * SR), .001, .07)
    return s * .9


def hat(abierto=False):
    d = .25 if abierto else .06
    return filt(ruido(d), 'high', 7000) * env(int(d * SR), .001, d / 3)


# ---------- Efectos ----------
def whoosh(dur=.55, f0=300, f1=4000, g=1.0):
    """Ruido que pasa de grave a agudo y vuelve (mezcla de bandas), con forma de campana."""
    n = int(dur * SR)
    x = ruido(dur)
    bandas = np.geomspace(f0, f1, 5)
    k = np.linspace(0, 1, n)
    pos = np.sin(np.pi * np.clip(k / .7, 0, 1) / 2) * (1 - np.clip((k - .7) / .3, 0, 1) * .6) * (len(bandas) - 1)
    out = np.zeros(n)
    for i, f in enumerate(bandas):
        w = np.clip(1 - np.abs(pos - i), 0, 1)
        out += filt(x, 'band', [f * .6, min(f * 1.6, 20000)]) * w
    e = np.sin(np.pi * k) ** 1.5
    return out * e * g / np.abs(out).max() * .9


def clic():
    s = tono(2400, .05, .0005, .012, (1,)) * .6
    s[:int(.02 * SR)] += filt(ruido(.02), 'high', 3000) * env(int(.02 * SR), .0005, .004) * .4
    return s


def tecla():
    return filt(ruido(.03), 'band', [1800, 6000]) * env(int(.03 * SR), .0005, .006)


def pop():
    t = np.arange(int(.12 * SR)) / SR
    f = 900 * np.exp(-t * 18) + 380
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), .001, .04)


def campana(notas, sep=.07, r=.45):
    s = np.zeros(int((sep * len(notas) + r * 3) * SR))
    for i, m in enumerate(notas):
        add(s, tono(hz(m), r * 3, .002, r, (1, .25, .08, .05)), i * sep)
    return s


def obturador():
    a = filt(ruido(.05), 'band', [1500, 8000]) * env(int(.05 * SR), .0005, .01)
    s = np.zeros(int(.2 * SR))
    add(s, a, 0)
    add(s, a * .8, .07)
    return s * 1.2


def impacto():
    t = np.arange(int(1.6 * SR)) / SR
    f = 40 + 80 * np.exp(-t * 8)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3)
    brillo = filt(ruido(1.6), 'high', 6000) * np.exp(-t * 2.5) * .25
    return boom + brillo


# ---------- Canción ----------
TONICA = 62  # Re
PROG = [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]]  # I V vi IV


def generar(info, salida):
    dur = info['duracion']
    M = info['marcas']
    n = int((dur + .5) * SR)
    mus = np.zeros(n)
    drums = np.zeros(n)
    sfx = np.zeros(n)
    bar = BEAT * 4
    inicio_ritmo = M['inicioPasos']
    fin_ritmo = M['fin'] + 4.6
    nb = int(dur / bar) + 1
    for b in range(nb):
        t0 = b * bar
        ch = [TONICA + x for x in PROG[b % 4]]
        add(mus, pad([c - 12 for c in ch] + [ch[0]], bar + .6), t0, .32)
        # Arpegio en corcheas
        pat = [0, 1, 2, 1, 2, 0, 1, 2]
        for k in range(8):
            if t0 < 2.9 and k % 2:
                continue
            add(mus, pluck(ch[pat[k]] + 12), t0 + k * BEAT / 2, .16)
        if inicio_ritmo - .1 <= t0 < fin_ritmo:
            for k in range(8):
                add(mus, bajo(ch[0] - 24, BEAT / 2), t0 + k * BEAT / 2, .28)
            for k in range(4):
                add(drums, bombo(), t0 + k * BEAT, .9)
                if k % 2:
                    add(drums, palmas(), t0 + k * BEAT, .35)
            for k in range(8):
                add(drums, hat(k == 7), t0 + k * BEAT / 2, .16 if k % 2 else .09)
    # Bombo "respira" con cada golpe (sidechain sencillo)
    sc = np.ones(n)
    for b in range(nb * 4):
        t0 = b * BEAT
        if inicio_ritmo <= t0 < fin_ritmo:
            i = int(t0 * SR)
            m = int(.25 * SR)
            sc[i:i + m] = np.minimum(sc[i:i + m], 1 - .45 * np.exp(-np.arange(min(m, n - i)) / SR / .08))
    mus *= sc

    # Efectos en la línea de tiempo
    for e in info['eventos']:
        t, tipo = e['t'], e['tipo']
        if tipo == 'swoosh':
            add(sfx, whoosh(.55, 500, 5000), t - .2, .22)
        elif tipo == 'barrido':
            add(sfx, whoosh(1.1, 200, 6000), t - .1, .45)
        elif tipo == 'tap':
            add(sfx, clic(), t, .5)
        elif tipo == 'tecla':
            add(sfx, tecla(), t, .22)
        elif tipo == 'pop':
            add(sfx, pop(), t, .35)
        elif tipo == 'tip':
            add(sfx, campana([TONICA + 24, TONICA + 31], .08, .35), t, .14)
        elif tipo in ('ok', 'notif'):
            add(sfx, campana([TONICA + 19, TONICA + 26], .1, .3), t, .16)
        elif tipo == 'exito':
            add(sfx, campana([TONICA + 12, TONICA + 16, TONICA + 19, TONICA + 24], .07, .5), t, .2)
        elif tipo == 'shutter':
            add(sfx, obturador(), t, .45)
        elif tipo == 'confeti':
            add(sfx, whoosh(1.2, 2000, 9000), t, .18)
            add(sfx, campana([TONICA + 24, TONICA + 28, TONICA + 31, TONICA + 36], .06, .6), t + .05, .16)
        elif tipo == 'logo':
            add(sfx, impacto(), t, .55)

    mix = mus + drums * .8 + sfx
    # Entrada y salida suaves
    tt = np.arange(n) / SR
    mix *= np.minimum(1, tt / .15) * np.clip((dur - tt) / 2.0, 0, 1)
    mix = filt(mix, 'high', 30)
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    mix *= .89 / max(1e-9, np.abs(mix).max())
    est = np.stack([mix, np.roll(mix, int(.012 * SR)) * .97 + mix * .03], 1)[:int(dur * SR)]
    wavfile.write(salida, SR, (est * 32767).astype(np.int16))


if __name__ == '__main__':
    generar(json.load(open(sys.argv[1])), sys.argv[2])
