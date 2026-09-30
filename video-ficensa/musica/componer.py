"""Pista de fondo original para el video Ficensa (26 s).

Compás = 2.6 s (≈92.3 bpm) para que el video arranque justo en el compás 2
(2.6 s) y el cierre caiga en el compás 9 (20.8 s).
Progresión en Re mayor: D – A – Bm – G.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
DUR = 26.0
BAR = 2.6
BEAT = BAR / 4
N = int(SR * DUR)
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# Acordes (raíz MIDI + notas del acorde)
CHORDS = {
    "D": [50, 57, 62, 66, 69],
    "A": [45, 57, 61, 64, 69],
    "Bm": [47, 54, 59, 62, 66],
    "G": [43, 55, 59, 62, 67],
}
PROG = ["D", "A", "Bm", "G", "D", "A", "Bm", "G", "D", "D"]


def buf():
    return np.zeros((N, 2))


def place(dst, sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    dst[i : i + len(sig), 0] += sig * l * gain
    dst[i : i + len(sig), 1] += sig * r * gain


def env_adsr(n, a, d, s, r, sustain_len):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(int(sustain_len * SR) - a_n - d_n, 0)
    e = np.concatenate(
        [np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False), np.full(s_n, s), np.linspace(s, 0, r_n)]
    )
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))


def pad_note(f, length):
    n = int((length + 1.2) * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for det in (-0.12, 0.0, 0.12):  # voces desafinadas = pad cálido
        ff = f * 2 ** (det / 12)
        for h in range(1, 7):
            sig += np.sin(2 * np.pi * ff * h * t + h) / h**1.6
    return sig * env_adsr(n, 0.6, 0.4, 0.8, 1.2, length) * 0.05


def piano_note(f, length=2.4):
    n = int(length * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for h, amp in zip(range(1, 7), (1.0, 0.45, 0.25, 0.12, 0.06, 0.03)):
        sig += amp * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.6 + h * 0.9))
    atk = np.minimum(t / 0.004, 1)
    return sig * atk * 0.18


def pluck(f, length=0.6):
    n = int(length * SR)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return sig * np.exp(-t * 7) * np.minimum(t / 0.003, 1) * 0.09


def bass_note(f, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return sig * env_adsr(n, 0.01, 0.2, 0.7, 0.15, length) * 0.22


def kick():
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 0.5


def shaker():
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    sos = butter(4, 6000, "hp", fs=SR, output="sos")
    return sosfilt(sos, rng.standard_normal(n)) * np.exp(-t * 60) * 0.05


def swell(length):
    n = int(length * SR)
    t = np.arange(n) / SR
    sos = butter(2, [800, 6000], "bp", fs=SR, output="sos")
    return sosfilt(sos, rng.standard_normal(n)) * (t / length) ** 2.5 * 0.06


def reverb(x, secs=2.4, wet=0.28):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 3.2)
        ir /= np.sqrt(np.sum(ir**2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x * (1 - wet) + out * wet


pads, keys, arp, low, drums = buf(), buf(), buf(), buf(), buf()

for b, name in enumerate(PROG):
    t0 = b * BAR
    notes = CHORDS[name]
    last = b == len(PROG) - 1
    length = (DUR - t0) if last else BAR
    # Pad: todo el tema
    for k, n in enumerate(notes[1:]):
        place(pads, pad_note(midi(n), length), t0, pan=(k - 1.5) * 0.3)
    # Piano en el tiempo 1 (y un eco suave en el 3 fuera de la intro)
    for k, n in enumerate(notes[1:]):
        place(keys, piano_note(midi(n + 12), 3.5 if last else 2.4), t0 + k * 0.012, pan=0.15)
        if 1 <= b <= 7:
            place(keys, piano_note(midi(n + 12)) * 0.45, t0 + 2 * BEAT + k * 0.012, pan=0.15)
    # Arpegio en corcheas: compases 1–7 (video)
    if 1 <= b <= 7:
        pattern = [1, 2, 3, 4, 3, 2, 3, 4]
        for s, idx in enumerate(pattern):
            n = notes[idx] + 12
            vel = 1.0 if s % 2 == 0 else 0.7
            place(arp, pluck(midi(n)) * vel, t0 + s * BEAT / 2, pan=0.35 if s % 2 else -0.35)
    # Bajo: compases 1–7
    if 1 <= b <= 7:
        root = notes[0] - 12 if notes[0] > 45 else notes[0]
        place(low, bass_note(midi(root), 2 * BEAT * 0.95), t0)
        place(low, bass_note(midi(root), 2 * BEAT * 0.95), t0 + 2 * BEAT)
    # Bombo: compases 2–7 · shaker: compases 4–7 (escena 2)
    if 2 <= b <= 7:
        for beat in (0, 2):
            place(drums, kick(), t0 + beat * BEAT)
    if 4 <= b <= 7:
        for s in range(8):
            place(drums, shaker() * (1.0 if s % 2 else 0.5), t0 + s * BEAT / 2, pan=0.4)

# Subida hacia el cambio de escena (12.1 s) y hacia el cierre (20.8 s)
place(drums, swell(1.3), 12.1 - 1.3)
place(drums, swell(1.6), 20.8 - 1.6)

music = reverb(pads + keys + arp) + low + reverb(drums, 1.2, 0.15)

# Fundido de entrada y salida
t = np.arange(N) / SR
fade = np.minimum(t / 0.8, 1) * np.clip((DUR - t) / 2.5, 0, 1)
music *= fade[:, None]

music /= np.max(np.abs(music)) / 0.89  # pico ≈ -1 dBFS
wavfile.write("musica-fondo.wav", SR, (music * 32767).astype(np.int16))
print("ok", music.shape[0] / SR, "s")
