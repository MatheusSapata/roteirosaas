"""synth_music.py plan.json out.wav

Procedural score for the film (no music API available): nylon-guitar bossa comping
(additive plucked strings), a soft pad, shaker, rim, warm bass and a soft kick.
Everything is placed on a bar grid given in plan.json:
  {"bpm": 100, "t0": -1.1, "duration": 29.0, "sections": [[startBar, "name"], ...],
   "dips": [[t, dur, depth_db], ...], "final": t}
Sections: "intro" (guitar only), "build" (guitar+pad+shaker), "groove" (+bass, kick, rim),
"lift" (groove, brighter voicings, fuller pad), "outro" (guitar+pad), "end" (final chord).
"""
import json, sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
plan = json.load(open(sys.argv[1]))
BPM, T0, DUR = plan["bpm"], plan["t0"], plan["duration"]
BEAT = 60.0 / BPM
BAR = 4 * BEAT
N = int((DUR + 3.0) * SR)
rng = np.random.default_rng(7)

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)

def pluck(freq, dur=2.6, vel=1.0, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    p = 0.18  # pluck position
    for h in range(1, 16):
        f = freq * h * (1 + 0.0004 * h * h)
        if f > 9000: break
        a = abs(np.sin(np.pi * h * p)) / h ** 1.15 * (bright ** (h - 1) if bright < 1 else 1)
        d = 1.6 + 0.55 * h ** 1.25
        out += a * np.exp(-d * t) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
    att = np.minimum(1, t / 0.004)
    noise = rng.standard_normal(min(n, int(0.02 * SR))) * np.exp(-np.arange(min(n, int(0.02 * SR))) / (0.004 * SR))
    out[:len(noise)] += 0.08 * bp(noise, 1500, 6000)
    out *= att * vel
    # nylon body: soften highs, a little low-mid warmth
    out = lp(out, 4200)
    return out

def add(buf, x, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= buf.shape[1] or i + len(x) <= 0: return
    a, b = max(0, i), min(buf.shape[1], i + len(x))
    seg = x[a - i:b - i] * gain
    buf[0, a:b] += seg * np.sqrt(0.5 * (1 - pan))
    buf[1, a:b] += seg * np.sqrt(0.5 * (1 + pan))

# Harmony (MIDI). D major bossa: Dmaj7 | Bm7 | Em7 | A13 ; lift: Gmaj7 | F#m7 | Em7 | A7sus4
CHORDS = {
    'Dmaj7': ([50], [61, 66, 69, 73]), 'Bm7': ([47], [57, 62, 66, 69]), 'Em7': ([52], [62, 67, 71, 74]),
    'A13': ([45], [55, 61, 66, 67]), 'Gmaj7': ([43], [59, 62, 66, 71]), 'F#m7': ([42], [57, 61, 64, 69]),
    'A7sus4': ([45], [55, 62, 64, 67]), 'Dmaj9': ([38, 50], [61, 64, 66, 69, 73]),
}
MAIN = ['Dmaj7', 'Bm7', 'Em7', 'A13']
LIFT = ['Gmaj7', 'F#m7', 'Em7', 'A7sus4']

sections = sorted(plan["sections"])
def section_at(bar):
    s = sections[0][1]
    for b0, name in sections:
        if bar >= b0: s = name
    return s

gtr = np.zeros((2, N)); pad = np.zeros((2, N)); perc = np.zeros((2, N)); bass = np.zeros((2, N))
# bossa comping pattern in 16ths over one bar: chord hits
COMP = [0, 3, 6, 10, 12]  # syncopated
nbars = int(np.ceil((DUR - T0) / BAR)) + 1
lift_i = 0; main_i = 0
final_t = plan.get("final")
for k in range(nbars):
    tb = T0 + k * BAR
    if tb > DUR: break
    name = section_at(k)
    if final_t is not None and tb >= final_t - 0.01: break
    if name == 'end': break
    if name == 'lift': ch = LIFT[lift_i % 4]; lift_i += 1
    else: ch = MAIN[main_i % 4]; main_i += 1
    roots, voic = CHORDS[ch]
    bright = 1.0 if name == 'lift' else 0.92
    # thumb bass on 1 and 3 (guitar), alternating fifth
    for bi, beat in enumerate([0, 2]):
        r = roots[0] + (7 if bi == 1 else 0)
        add(gtr, pluck(mtof(r), 2.2, 0.55), tb + beat * BEAT + 0.004, 1.0, -0.15)
    # chord comping
    for j, s16 in enumerate(COMP):
        tt = tb + s16 * BEAT / 4
        if name == 'intro' and j in (1, 3): continue
        vel = [0.5, 0.36, 0.42, 0.34, 0.4][j]
        for v, m in enumerate(voic):
            add(gtr, pluck(mtof(m + (12 if name == 'lift' and v == len(voic) - 1 else 0)), 1.4, vel * 0.42, bright), tt + v * 0.006, 1.0, 0.12)
    # pad
    if name in ('build', 'groove', 'lift', 'outro'):
        n = int(BAR * SR) + int(0.6 * SR); t = np.arange(n) / SR
        env = np.minimum(1, t / 0.5) * np.minimum(1, (n / SR - t) / 0.6)
        x = np.zeros(n)
        for m in voic:
            f = mtof(m)
            x += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 1) + 0.15 * np.sin(2 * np.pi * f * 1.003 * t)
        x = lp(x, 1800 if name != 'lift' else 2600) * env
        add(pad, x, tb - 0.05, 0.05 if name == 'build' else (0.075 if name == 'lift' else 0.06))
    # shaker
    if name in ('build', 'groove', 'lift'):
        for s16 in range(16):
            tt = tb + s16 * BEAT / 4
            ln = int(0.07 * SR); env = np.exp(-np.arange(ln) / (0.018 * SR))
            x = hp(rng.standard_normal(ln), 6500) * env
            acc = 1.0 if s16 % 4 == 2 else (0.7 if s16 % 2 == 0 else 0.45)
            add(perc, x, tt, 0.05 * acc * (0.7 if name == 'build' else 1.0), 0.35)
    # rim + kick + bass
    if name in ('groove', 'lift'):
        for s16 in [3, 6, 10, 13]:
            ln = int(0.05 * SR); env = np.exp(-np.arange(ln) / (0.006 * SR))
            x = bp(rng.standard_normal(ln), 1200, 3500) * env
            add(perc, x, tb + s16 * BEAT / 4, 0.09, -0.3)
        for beat in [0, 2]:
            ln = int(0.25 * SR); t = np.arange(ln) / SR
            f = 45 + 55 * np.exp(-t / 0.03)
            x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
            add(perc, x, tb + beat * BEAT, 0.32)
        for beat, off in [(0, 0), (1.5, 7), (2, 7), (3.5, 0)]:
            ln = int(0.5 * SR); t = np.arange(ln) / SR
            f = mtof(roots[0] - 12 + off)
            x = (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.35) * np.minimum(1, t / 0.01)
            add(bass, np.tanh(1.5 * x), tb + beat * BEAT, 0.22)

# final chord
if final_t is not None:
    roots, voic = CHORDS['Dmaj9']
    for v, m in enumerate(roots + voic):
        add(gtr, pluck(mtof(m), 3.5, 0.5, 1.0), final_t + v * 0.022, 0.75, -0.2 + 0.08 * v)
    n = int(3.2 * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * mtof(m) * t) for m in voic) * np.minimum(1, t / 0.2) * np.exp(-t / 1.4)
    add(pad, lp(x, 2400), final_t, 0.05)

mix = gtr * 0.9 + pad + perc + bass
# reverb: synthetic room
ir_n = int(1.9 * SR); ir_t = np.arange(ir_n) / SR
ir = rng.standard_normal((2, ir_n)) * np.exp(-ir_t / 0.45)
ir = np.stack([lp(ir[0], 5000), lp(ir[1], 5000)])
wet = np.stack([fftconvolve(mix[c], ir[c])[:N] for c in range(2)])
wet = hp(wet, 250)
mix = mix + 0.12 * wet / np.max(np.abs(wet) + 1e-9) * np.max(np.abs(mix))
# dips (clear the sound before big moves)
env = np.ones(N)
for t, d, db in plan.get("dips", []):
    a, b = int(t * SR), int((t + d) * SR)
    g = 10 ** (-db / 20)
    ramp = int(0.08 * SR)
    env[max(0, a - ramp):a] = np.minimum(env[max(0, a - ramp):a], np.linspace(1, g, a - max(0, a - ramp)))
    env[a:b] = np.minimum(env[a:b], g)
    rb = min(N, b + int(0.05 * SR))
    env[b:rb] = np.minimum(env[b:rb], np.linspace(g, 1, rb - b))
mix *= env
mix = mix[:, :int(DUR * SR)]
fade = int(0.8 * SR)
mix[:, -fade:] *= np.linspace(1, 0, fade) ** 1.5
mix = np.tanh(1.2 * mix / (np.max(np.abs(mix)) + 1e-9)) * 0.8
import wave
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix.T, -1, 1) * 32767).astype('<i2').tobytes()); w.close()
print('wrote', sys.argv[2], mix.shape[1] / SR, 's')
