"""synth_sfx.py outdir : procedural SFX kit (no SFX API permission). 48 kHz mono wavs, peak -3 dBFS.
click.wav (cursor press), key1..key6.wav (keyboard ticks), whoosh.wav (camera snap/whip),
pop.wav (notification), tap.wav (soft UI tick), land.wav (logo landing)."""
import os, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(11)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def save(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (-3 / 20)
    w = wave.open(os.path.join(out, name), 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close()
def t(d): return np.arange(int(d * SR)) / SR

# click: trackpad-like, dry
tt = t(0.09)
x = bp(rng.standard_normal(len(tt)), 1800, 7000) * np.exp(-tt / 0.0035)
x += 0.6 * np.sin(2 * np.pi * 140 * tt) * np.exp(-tt / 0.012)
x += 0.25 * bp(rng.standard_normal(len(tt)), 900, 2500) * np.exp(-(tt - 0.035).clip(0) / 0.004) * (tt > 0.035)
save('click.wav', x)
# key ticks (6 variants)
for k in range(6):
    tt = t(0.06)
    f0 = 2200 + 400 * k
    x = bp(rng.standard_normal(len(tt)), f0, f0 * 2.4) * np.exp(-tt / (0.0025 + 0.0004 * k))
    x += 0.35 * np.sin(2 * np.pi * (180 + 15 * k) * tt) * np.exp(-tt / 0.008)
    save(f'key{k + 1}.wav', x)
# whoosh: band-swept noise
tt = t(0.6)
n = rng.standard_normal(len(tt))
env = np.where(tt < 0.32, (tt / 0.32) ** 2, np.exp(-(tt - 0.32) / 0.07))
lo = hp(n, 300); hi = hp(n, 2200)
mixw = np.clip(tt / 0.32, 0, 1)
x = lp((1 - mixw) * lo + mixw * hi, 7000) * env
save('whoosh.wav', x)
# pop / notification: rounded two-tone
tt = t(0.45)
x = (np.sin(2 * np.pi * 987.8 * tt) + 0.5 * np.sin(2 * np.pi * 1318.5 * tt) * (tt > 0.07)) * np.exp(-tt / 0.12) * np.minimum(1, tt / 0.004)
x += 0.4 * np.sin(2 * np.pi * 1975.5 * tt) * np.exp(-tt / 0.05)
save('pop.wav', x)
# tap: soft UI tick
tt = t(0.05)
x = bp(rng.standard_normal(len(tt)), 3000, 9000) * np.exp(-tt / 0.002) + 0.3 * np.sin(2 * np.pi * 600 * tt) * np.exp(-tt / 0.006)
save('tap.wav', x)
# land: low soft boom + airy shimmer
tt = t(1.6)
f = 52 + 40 * np.exp(-tt / 0.05)
x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.35)
sh = hp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt / 0.5) * np.minimum(1, tt / 0.03) * 0.12
x += sh
save('land.wav', x)
print('sfx ->', out, sorted(os.listdir(out)))
