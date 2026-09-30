"""Efectos de sonido sintetizados para cada escena (tiempos locales del clip, 10 s cada uno).

Reemplazan el audio original de los clips (que traía música mezclada).
Genera sfx-escena1.wav y sfx-escena2.wav.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
DUR = 10.0
N = int(SR * DUR)
rng = np.random.default_rng(11)


def T(n):
    return np.arange(n) / SR


def noise(n):
    return rng.standard_normal(n)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bp", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lp", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "hp", fs=SR, output="sos"), x)


class Track:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= N:
            return
        sig = sig[: N - i]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.x[i : i + len(sig), 0] += sig * l * gain
        self.x[i : i + len(sig), 1] += sig * r * gain


# ---------------- Sonidos ----------------
def footstep(hard=True):
    n = int(0.12 * SR)
    t = T(n)
    heel = lp(noise(n), 2500 if hard else 1200) * np.exp(-t * 60)
    thump = np.sin(2 * np.pi * 90 * t) * np.exp(-t * 40)
    return (heel * 0.5 + thump * 0.6) * 0.5


def tap():
    n = int(0.05 * SR)
    t = T(n)
    return (hp(noise(n), 2000) * np.exp(-t * 180) * 0.4 + np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 90) * 0.25)


def beep(freqs=(880, 1320), step=0.09):
    out = []
    for f in freqs:
        n = int(step * SR)
        t = T(n)
        env = np.minimum(t / 0.004, 1) * np.exp(-t * 18)
        out.append((np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)) * env * 0.3)
    return np.concatenate(out)


def printer(length=0.75):
    n = int(length * SR)
    t = T(n)
    motor = np.sign(np.sin(2 * np.pi * 118 * t)) * 0.08 + np.sin(2 * np.pi * 236 * t) * 0.05
    stutter = 0.6 + 0.4 * (np.sin(2 * np.pi * 28 * t) > 0)
    paper = bp(noise(n), 1500, 5000) * 0.12
    env = np.minimum(t / 0.03, 1) * np.minimum((length - t) / 0.05, 1)
    return lp(motor * stutter + paper * stutter, 6000) * env


def whoosh(length=0.6, lo=300, hi=3000, rise=True):
    n = int(length * SR)
    t = T(n)
    x = noise(n)
    # barrido de filtro por bloques
    out = np.zeros(n)
    blocks = 24
    for b in range(blocks):
        a, z = b * n // blocks, (b + 1) * n // blocks
        p = b / (blocks - 1)
        c = lo * (hi / lo) ** (p if rise else 1 - p)
        out[a:z] = bp(x, c * 0.7, min(c * 1.4, SR / 2 - 100))[a:z]
    env = np.sin(np.pi * t / length) ** 2
    return out * env * 0.35


def shimmer(length=1.2, count=40, lo=2500, hi=7000):
    n = int(length * SR)
    t = T(n)
    out = np.zeros(n)
    for _ in range(count):
        st = rng.uniform(0, length * 0.7)
        f = rng.uniform(lo, hi)
        i = int(st * SR)
        tt = t[: n - i]
        out[i:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * rng.uniform(8, 20)) * rng.uniform(0.3, 1)
    return out * 0.03


def pop(f=900, drop=0.6):
    n = int(0.09 * SR)
    t = T(n)
    ff = f * (drop + (1 - drop) * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 45) * 0.3


def bell(f, length=1.4):
    n = int(length * SR)
    t = T(n)
    parts = [(1, 1.0, 3.0), (2.01, 0.4, 5.0), (3.02, 0.2, 8.0), (4.7, 0.1, 12.0)]
    return sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in parts) * np.minimum(t / 0.003, 1) * 0.18


def key_click():
    n = int(0.03 * SR)
    t = T(n)
    return bp(noise(n), 1500, 6000) * np.exp(-t * 250) * 0.25


def door_slide(length=1.1):
    n = int(length * SR)
    t = T(n)
    rumble = lp(noise(n), 250) * 0.5
    air = bp(noise(n), 400, 1800) * 0.25
    env = np.sin(np.pi * t / length) ** 1.5
    return (rumble + air) * env * 0.5


def room_tone(length):
    n = int(length * SR)
    t = T(n)
    x = lp(noise(n), 500) * 0.02 + bp(noise(n), 200, 1200) * 0.008
    env = np.minimum(t / 0.3, 1) * np.minimum((length - t) / 0.3, 1)
    return x * env


def reverb(x, secs=0.9, wet=0.18):
    n = int(secs * SR)
    ir = noise(n) * np.exp(-T(n) * 6)
    ir /= np.sqrt(np.sum(ir**2))
    out = np.stack([fftconvolve(x[:, c], ir)[: len(x)] for c in range(2)], 1)
    return x * (1 - wet) + out * wet


def export(track, name):
    x = reverb(track.x)
    x /= max(np.max(np.abs(x)) / 0.89, 1e-9)
    wavfile.write(name, SR, (x * 32767).astype(np.int16))
    print(name, "ok")


# ================= ESCENA 1 =================
a = Track()
a.add(room_tone(2.3), 0.0, 1.0)
for k, st in enumerate(np.arange(0.1, 1.6, 0.48)):  # entra caminando
    a.add(footstep(), st, 0.8, pan=-0.2 + 0.1 * k)
a.add(tap(), 1.75, 1.0, 0.3)  # toca la pantalla del kiosko
a.add(beep(), 1.85, 0.9, 0.3)
a.add(whoosh(0.7, 400, 4000, True), 1.9, 1.0)  # ola azul de transición
a.add(printer(0.8), 2.25, 1.0, 0.2)  # sale el ticket
a.add(whoosh(0.8, 2500, 500, False), 3.0, 0.7)  # aparece el holograma
a.add(shimmer(1.0, 25), 3.2, 1.0)
a.add(whoosh(0.6, 300, 2500, True), 4.1, 0.8)  # panel CRM
a.add(shimmer(0.8, 15, 3000, 8000), 4.4, 0.8)
for k, st in enumerate([5.0, 5.35, 5.7]):  # elementos y checks
    a.add(pop(700 + 150 * k), st, 0.8, pan=0.3)
for k, st in enumerate([6.0, 6.2, 6.4]):  # tarjetas de oportunidad
    a.add(pop(1000 + 120 * k, 0.8), st, 0.7, pan=-0.2)
a.add(room_tone(2.6), 7.4, 1.0)
a.add(bell(1046.5), 7.55, 0.9)  # notificación "Venta sugerida"
a.add(bell(1568.0), 7.7, 0.7)
for st in np.arange(8.5, 9.8, 0.11) + rng.uniform(-0.03, 0.03, len(np.arange(8.5, 9.8, 0.11))):
    a.add(key_click(), st, 0.8, pan=-0.3)  # teclea
export(a, "sfx-escena1.wav")

# ================= ESCENA 2 =================
b = Track()
b.add(room_tone(4.4), 0.0, 0.8)
b.add(tap(), 0.25, 1.0, -0.2)  # toca la mesa de cristal
b.add(whoosh(0.55, 500, 3500, True), 0.4, 0.8)  # sube el panel de beneficios
b.add(shimmer(0.7, 15), 0.6, 0.7)
b.add(tap(), 1.45, 0.9, 0.3)  # el cliente señala
b.add(pop(1100, 0.8), 2.1, 0.5)
b.add(whoosh(0.6, 3000, 400, False), 4.35, 0.8)  # cambio a la tarjeta
b.add(pop(800), 4.6, 0.6)
for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):  # "Aprobada"
    b.add(bell(f, 1.6), 5.05 + k * 0.09, 0.7)
b.add(shimmer(1.4, 60, 3000, 9000), 5.2, 1.3)  # partículas
b.add(door_slide(1.2), 6.3, 0.9)  # puerta automática
b.add(room_tone(2.0), 6.4, 0.6)
for k, st in enumerate(np.arange(6.6, 8.2, 0.5)):  # sale caminando
    b.add(footstep(False), st, 0.6 - 0.05 * k, pan=0.1)
b.add(whoosh(1.0, 300, 2000, True), 7.7, 0.5)  # entrada del logo
b.add(shimmer(1.2, 30, 3000, 8000), 8.4, 0.8)
export(b, "sfx-escena2.wav")
