import numpy as np
from scipy.signal import butter, lfilter
import wave

SR = 44100
BEAT = 0.88                 # one GIF beat = 8 frames x 110 ms
BAR = BEAT * 4
BARS = 8
LEN = BAR * BARS
TAIL = 4.0
rng = np.random.default_rng(7)

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def buf(): return np.zeros(int((LEN + TAIL) * SR))
def lp(x, fc, order=2): b, a = butter(order, fc / (SR / 2), 'low'); return lfilter(b, a, x)
def hp(x, fc, order=2): b, a = butter(order, fc / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)

def add(dst, sig, t):
    i = int(t * SR)
    n = min(len(sig), len(dst) - i)
    if n > 0:
        dst[i:i + n] += sig[:n]

# swing: 16th grid with the off 16ths pushed late
def t16(bar, step, swing=0.58):
    pair = step // 2
    off = step % 2
    six = BEAT / 4
    return bar * BAR + pair * 2 * six + (off * 2 * six * swing)

# ---------------- instruments
def rhodes(f, dur=2.6, vel=0.5):
    t = np.arange(int(dur * SR)) / SR
    idx = 1.6 * np.exp(-t * 5) + 0.25
    mod = np.sin(2 * np.pi * f * t) * idx
    car = np.sin(2 * np.pi * f * t + mod)
    tine = np.sin(2 * np.pi * f * 4.01 * t) * np.exp(-t * 18) * 0.15
    env = (1 - np.exp(-t * 300)) * np.exp(-t / 1.6)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.2 * t)
    return (car + tine) * env * trem * vel

def bass(f, dur=0.9, vel=0.6):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    env = (1 - np.exp(-t * 200)) * np.exp(-t / 0.45)
    return np.tanh(s * 1.4) * env * vel

def kick(vel=1.0):
    t = np.arange(int(0.45 * SR)) / SR
    f = 48 + 75 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / 0.16)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.15
    return (s + click) * vel

def snare(vel=0.7):
    t = np.arange(int(0.3 * SR)) / SR
    n = bp(rng.standard_normal(len(t)), 900, 5200) * np.exp(-t / 0.09)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05) * 0.6
    return lp(n * 1.4 + tone, 5000) * vel

def hat(vel=0.25, open_=False):
    t = np.arange(int((0.25 if open_ else 0.06) * SR)) / SR
    n = hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / (0.08 if open_ else 0.018))
    return n * vel

def pluck(f, vel=0.3):
    t = np.arange(int(1.4 * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)
    env = (1 - np.exp(-t * 400)) * np.exp(-t / 0.5)
    return s * env * vel

# ---------------- arrangement
CHORDS = [  # (bass midi, chord voicing)
    (50, [53, 57, 60, 64]),      # Dm9
    (43, [53, 59, 64, 69]),      # G13
    (48, [52, 55, 59, 62]),      # Cmaj9
    (45, [55, 60, 64, 71]),      # Am9
]
MEL = [
    [(1.5, 76), (2.5, 74), (3.0, 72)],
    [(1.0, 71), (2.0, 74), (3.5, 76)],
    [(1.5, 79), (2.5, 76), (3.5, 74)],
    [(1.0, 72), (2.0, 71), (3.0, 69), (3.75, 67)],
]

keys, bs, drums, mel = buf(), buf(), buf(), buf()
for bar in range(BARS):
    root, ch = CHORDS[bar % 4]
    t0 = bar * BAR
    for k, m in enumerate(ch):                       # strummed chord on 1
        add(keys, rhodes(mtof(m), vel=0.22), t0 + 0.012 * k + 0.01)
    for k, m in enumerate(ch[1:]):                   # soft push on the "and" of 2
        add(keys, rhodes(mtof(m), dur=1.2, vel=0.11), t16(bar, 6) + 0.01 * k)
    add(bs, bass(mtof(root), dur=1.6, vel=0.55), t0)
    add(bs, bass(mtof(root + 7), dur=0.5, vel=0.35), t16(bar, 10))
    add(bs, bass(mtof(root + 12 if bar % 2 else root), dur=0.4, vel=0.3), t16(bar, 14))
    # drums
    for st in (0, 7, 10):
        add(drums, kick(1.0 if st == 0 else 0.75), t16(bar, st))
    for st in (4, 12):
        add(drums, snare(0.75), t16(bar, st) + 0.012)
    if bar % 2 == 1:
        add(drums, snare(0.18), t16(bar, 15))
    for st in range(0, 16, 2):
        add(drums, hat(0.22 if st % 4 == 0 else 0.13), t16(bar, st))
    add(drums, hat(0.08), t16(bar, 11))
    if bar % 4 == 3:
        add(drums, hat(0.14, open_=True), t16(bar, 14))
    # melody: first half quiet, second half a touch louder
    for (bt, m) in MEL[bar % 4]:
        add(mel, pluck(mtof(m), vel=0.16 if bar < 4 else 0.22), t0 + (bt - 1) * BEAT + 0.01)

keys = lp(keys, 2400); mel = lp(mel, 3200)
bs = lp(bs, 380); drums = lp(drums, 6500)

# sidechain-ish pump from the kick grid
pump = np.ones_like(drums)
for bar in range(BARS):
    for st in (0, 7, 10):
        i = int(t16(bar, st) * SR)
        n = int(0.25 * SR)
        seg = 1 - 0.35 * np.exp(-np.arange(n) / SR / 0.08)
        pump[i:i + n] = np.minimum(pump[i:i + n], seg[:len(pump[i:i + n])])

mix = (keys * pump * 1.0 + mel * pump * 0.9 + bs * 0.9 + drums * 0.85)

# vinyl: hiss + crackle
L = len(mix)
hiss = lp(hp(rng.standard_normal(L), 1500), 9000) * 0.006
crackle = np.zeros(L)
pos = rng.integers(0, L, 900)
crackle[pos] = rng.standard_normal(900) * 0.25
crackle = hp(crackle, 1200) * 0.5
mix = mix + hiss + crackle
mix = lp(mix, 7500)

# fold the tail back onto the start for a seamless loop
n = int(LEN * SR)
loop = mix[:n].copy()
loop[:len(mix) - n] += mix[n:]
loop = np.tanh(loop * 1.3) / np.tanh(1.3)
loop /= np.max(np.abs(loop)) * 1.12

# tiny stereo: delay one side 9 ms for width
d = int(0.009 * SR)
left = loop
right = np.roll(loop, d) * 0.96 + loop * 0.04
st = np.stack([left, right], 1)
pcm = (st * 32767).astype(np.int16)
with wave.open('stonepark_lofi.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('seconds', n / SR)
