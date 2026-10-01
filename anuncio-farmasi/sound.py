"""Diseño de sonido sintetizado para el anuncio (26 s), sincronizado con anuncio.src.html.

Genera audio.wav: base musical (100 bpm, el pulso cae en 3.6 s = "LA CREÓ.")
más efectos (whoosh, impactos, pops, destellos) en los tiempos de cada animación.
"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
D = 26.0
N = int(SR * D)
rng = np.random.default_rng(7)

music = np.zeros((N, 2))
sfx = np.zeros((N, 2))
verb_send = np.zeros((N, 2))


def t_(dur):
    return np.arange(int(SR * dur)) / SR


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


def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x)


def sweep(x, f0, f1, kind='bandpass', bw=0.6):
    """Filtro con frecuencia variable en el tiempo (por bloques)."""
    out = np.zeros_like(x)
    blk = 512
    nb = int(np.ceil(len(x) / blk))
    zi = None
    for b in range(nb):
        f = f0 * (f1 / f0) ** (b / max(nb - 1, 1))
        if kind == 'bandpass':
            sos = butter(2, [f * (1 - bw / 2), min(f * (1 + bw / 2), SR / 2 - 100)], 'bandpass', fs=SR, output='sos')
        else:
            sos = butter(2, min(f, SR / 2 - 100), kind, fs=SR, output='sos')
        if zi is None or zi.shape[0] != sos.shape[0]:
            zi = np.zeros((sos.shape[0], 2))
        out[b * blk:(b + 1) * blk], zi = sosfilt(sos, x[b * blk:(b + 1) * blk], zi=zi)
    return out


def note(n):  # midi -> Hz
    return 440 * 2 ** ((n - 69) / 12)


# ---------------- instrumentos ----------------
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


def bell(freq, dur=1.6, bright=1.0):
    t = t_(dur)
    s = (np.sin(2 * np.pi * freq * t) + .5 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
         + .25 * bright * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 12))
    return s * np.exp(-t * 3.2) * np.minimum(t * 400, 1)


# ---------------- efectos ----------------
def whoosh(dur=0.6, up=True, f0=300, f1=6000):
    t = t_(dur)
    n = rng.standard_normal(len(t))
    s = sweep(n, f0, f1) if up else sweep(n, f1, f0)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return s * env


def riser(dur=2.6):
    t = t_(dur)
    n = sweep(rng.standard_normal(len(t)), 200, 9000, bw=0.5)
    f = 180 * (8 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    env = (t / dur) ** 2.2
    return (n + tone) * env


def impact(dur=1.8, deep=True):
    t = t_(dur)
    f = 28 + 90 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    crack = filt(rng.standard_normal(len(t)), 'lowpass', 2500) * np.exp(-t * 14)
    s = boom * (1.3 if deep else .8) + crack * .7
    return np.tanh(s * 1.6)


def pop(freq=700):
    t = t_(0.14)
    f = freq * (1 + 0.9 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32)


def tick(freq=2400):
    t = t_(0.05)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 110)


def shimmer(base=88, steps=(0, 7, 12, 16, 19, 24), gap=0.045):
    out = np.zeros(int(SR * (gap * len(steps) + 1.6)))
    for k, s in enumerate(steps):
        b = bell(note(base + s), 1.4) * (0.9 - k * 0.08)
        i = int(k * gap * SR)
        out[i:i + len(b)] += b
    return out


# ---------------- música ----------------
BEAT = 0.6           # 100 bpm
START = 3.6          # el drop cae en "LA CREÓ."
CHORDS = [  # (inicio, notas midi)
    (0.0, [57, 60, 64]),     # Am (intro)
    (3.6, [57, 60, 64]),     # Am
    (8.4, [53, 57, 60]),     # F
    (13.2, [60, 64, 67]),    # C
    (18.0, [55, 59, 62]),    # G
    (22.8, [60, 64, 67]),    # C (resuelve, final luminoso)
]
ENDS = [c[0] for c in CHORDS[1:]] + [D]

# pad
for (st, notes), en in zip(CHORDS, ENDS):
    dur = en - st + 0.4
    t = t_(dur)
    p = sum(supersaw(note(n), dur) for n in notes + [notes[0] + 12])
    p = filt(p, 'lowpass', 900 if st < START else 2200)
    att = 2.5 if st == 0 else 0.15
    env = np.minimum(t / att, 1) * np.minimum((dur - t) / 0.4, 1)
    place(music, p * env, st, gain=0.11 if st < START else 0.085, send=0.5)

# bajo en corcheas + batería, con pausa de tensión 16.4–18.0
drum_times = np.arange(START, 24.6, BEAT)
for bt in drum_times:
    if 16.4 <= bt < 18.0:
        continue
    k = round((bt - START) / BEAT)
    place(music, kick(), bt, 0.72)
    if k % 2 == 1:
        place(music, clap(), bt, 0.35, send=0.25)
    place(music, hat(open_=(k % 4 == 3)), bt + BEAT / 2, 0.16, pan=0.3)
    root = [n for s, n in [(c[0], c[1][0]) for c in CHORDS] if s <= bt + 1e-6][-1]
    for h in (0, BEAT / 2):
        t = t_(BEAT / 2)
        b = (np.sin(2 * np.pi * note(root - 24) * t) + 0.3 * supersaw(note(root - 24), BEAT / 2, 2))
        b = b * np.minimum(t * 300, 1) * np.exp(-t * 4) * np.minimum((t[-1] - t) * 200, 1)
        place(music, b, bt + h, 0.22)
# hats suaves durante la pausa para mantener tensión
for bt in np.arange(16.4, 18.0, BEAT / 2):
    place(music, hat(), bt, 0.12, pan=-0.3)

# sidechain: la música "respira" con cada bombo
duck = np.ones(N)
for bt in drum_times:
    if 16.4 <= bt < 18.0:
        continue
    i = int(bt * SR)
    t = t_(0.3)
    seg = 1 - 0.55 * np.exp(-t * 14)
    duck[i:i + len(seg)] = np.minimum(duck[i:i + len(seg)], seg[: N - i])

# ---------------- efectos sincronizados con la animación ----------------
# S1: líneas que suben
for at in (0.1, 0.2, 0.9, 1.6):
    place(sfx, whoosh(0.45, True, 400, 3500), at - 0.08, 0.10, pan=rng.uniform(-.3, .3), send=0.3)
place(sfx, riser(2.5), 1.1, 0.30, send=0.4)
# S2: LA / CREÓ.
place(sfx, impact(), 3.6, 0.85, send=0.5)
place(sfx, impact(1.4, deep=False), 3.85, 0.6, send=0.5)
place(sfx, shimmer(84), 3.6, 0.10, pan=0.2, send=0.6)
place(sfx, whoosh(0.5, True, 800, 9000), 4.35, 0.14, pan=0.5)        # barra dorada
place(sfx, whoosh(0.5, True, 400, 3000), 4.75, 0.08, send=0.3)
# S3: transición + productos
place(sfx, whoosh(0.7, False), 5.85, 0.20, send=0.4)
for at, pitch in ((6.7, 88), (8.25, 91), (9.65, 93), (11.05, 96)):
    place(sfx, pop(620), at, 0.55)
    place(sfx, shimmer(pitch), at + 0.05, 0.19, pan=0.25, send=0.6)
for at in (7.85, 9.25, 10.65):
    place(sfx, whoosh(0.4, True, 600, 7000), at, 0.12, pan=-0.4)
# S4: Tu negocio / horarios / reglas
place(sfx, whoosh(0.7, False), 12.0, 0.20, send=0.4)
for at in (12.6, 13.3, 14.0):
    place(sfx, impact(0.7, deep=False), at, 0.45)
    place(sfx, pop(420), at, 0.25)
place(sfx, whoosh(0.4, True, 400, 3000), 14.75, 0.08)
# S5: tensión -> "Genera ingresos extra."
place(sfx, whoosh(0.7, False), 16.2, 0.20, send=0.4)
place(sfx, riser(1.4), 16.5, 0.25, send=0.4)
place(sfx, impact(), 17.9, 0.8, send=0.5)
place(sfx, shimmer(96, steps=(0, 4, 7, 12, 16, 19, 24, 28), gap=0.035), 17.95, 0.13, send=0.6)
for k, at in enumerate((18.5, 18.7, 18.9, 19.1)):
    place(sfx, tick(2000 + k * 300), at, 0.22, pan=(-.4, .4)[k % 2])
# S6: CTA
place(sfx, whoosh(0.8, False), 19.8, 0.22, send=0.4)
place(sfx, impact(), 20.2, 0.75, send=0.55)
for k, at in enumerate((21.2, 21.35, 21.5, 21.65)):
    place(sfx, pop(560 * 2 ** (k * 4 / 12)), at, 0.48, pan=-0.45 + k * 0.3)
for n in (84, 88, 91, 96):                                            # chime del botón
    place(sfx, bell(note(n), 2.2), 22.1, 0.10, send=0.6)
place(sfx, shimmer(91), 22.4, 0.09, send=0.6)
# acorde final sostenido
t = t_(3.0)
final = sum(supersaw(note(n), 3.0) for n in (60, 64, 67, 72))
place(music, filt(final, 'lowpass', 2500) * np.exp(-t * 1.0) * np.minimum(t * 50, 1), 24.6, 0.12, send=0.7)

# ---------------- mezcla ----------------
ir_t = t_(2.2)
ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 3.0)[:, None]
ir[:, 0] = filt(ir[:, 0], 'lowpass', 6000)
ir[:, 1] = filt(ir[:, 1], 'lowpass', 6000)
verb = np.stack([fftconvolve(verb_send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
verb /= np.max(np.abs(verb)) + 1e-9

mix = music * duck[:, None] + sfx + verb * 0.18
mix = filt(mix.T, 'highpass', 28).T
fade = np.ones(N)
fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR)) ** 2
mix *= fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / 0.95
wavfile.write('audio.wav', SR, (mix * 32767).astype(np.int16))
print('audio.wav', mix.shape[0] / SR, 's')
