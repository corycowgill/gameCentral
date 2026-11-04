"""Renders the intro's audio sting to a WAV.

This is the offline twin of playSting() in hallucinated-intro.js: same riser,
same impact at the 2.30s lock, same shimmer chord. The JS version plays live in
a game; this one gets muxed into the exported mp4.

    python intro/tools/make-sting.py out.wav
"""
import struct
import sys
import numpy as np

SR = 44100
DURATION = 4.6
HIT = 2.30  # lock-in flash


def envelope(t, start, end, peak, floor=1e-4):
    """Exponential ramp from floor up to peak and back, as WebAudio does it."""
    env = np.full_like(t, floor)
    rise = (t >= start) & (t < end)
    k = (t[rise] - start) / (end - start)
    env[rise] = floor * (peak / floor) ** k
    return env


def main(path):
    t = np.arange(int(SR * DURATION)) / SR
    out = np.zeros_like(t)

    # --- riser: sawtooth sweeping 70Hz -> 880Hz into the lock ---
    sweep = (t < HIT)
    k = np.clip(t / HIT, 0, 1)
    freq = 70 * (880 / 70) ** k
    phase = 2 * np.pi * np.cumsum(freq) / SR
    saw = 2 * (phase / (2 * np.pi) % 1) - 1
    # one-pole lowpass that opens as the sweep climbs
    cutoff = 220 * (5200 / 220) ** k
    alpha = np.clip(2 * np.pi * cutoff / SR, 0, 1)
    filtered = np.zeros_like(saw)
    acc = 0.0
    for i in range(len(saw)):
        acc += alpha[i] * (saw[i] - acc)
        filtered[i] = acc
    rise_env = np.where(t < HIT, (t / HIT) ** 2.2 * 0.22, 0.0)
    rise_env *= np.clip((HIT - t) / 0.12, 0, 1)  # snap off at the hit
    out += filtered * rise_env * sweep

    # --- noise sweep riding the riser ---
    rng = np.random.default_rng(0x5EED)
    noise = rng.uniform(-1, 1, len(t))
    nacc = 0.0
    ncut = 400 * (7000 / 400) ** k
    nalpha = np.clip(2 * np.pi * ncut / SR, 0, 1)
    nfil = np.zeros_like(noise)
    for i in range(len(noise)):
        nacc += nalpha[i] * (noise[i] - nacc)
        nfil[i] = nacc
    band = noise - nfil  # crude highpass -> bandpass-ish hiss
    nenv = np.where(t < HIT, (t / HIT) ** 3 * 0.20, 0.0)
    nenv *= np.clip((HIT - t) / 0.10, 0, 1)
    out += band * nenv

    # --- impact: sub drop on the flash ---
    after = np.maximum(t - HIT, 0)
    sub_f = 150 * (42 / 150) ** np.clip(after / 0.5, 0, 1)
    sub_phase = 2 * np.pi * np.cumsum(np.where(t >= HIT, sub_f, 0)) / SR
    sub_env = np.where(t >= HIT, np.exp(-after * 3.2) * 0.85, 0.0)
    out += np.sin(sub_phase) * sub_env

    # transient click so the hit reads on small speakers
    click = np.where((t >= HIT) & (t < HIT + 0.02), rng.uniform(-1, 1, len(t)), 0.0)
    out += click * np.exp(-after * 160) * 0.3

    # --- shimmer chord over the reveal ---
    for i, f in enumerate([523.25, 784.0, 1046.5]):
        env = np.where(t >= HIT, np.exp(-after * 2.1) * (0.10 / (i + 1)), 0.0)
        env *= np.clip(after / 0.06, 0, 1)
        # triangle-ish via odd harmonics
        out += (np.sin(2 * np.pi * f * after) + 0.12 * np.sin(2 * np.pi * 3 * f * after)) * env

    # --- soft pad tail so the fade-out is not silent ---
    pad = np.where(t >= HIT, np.exp(-after * 0.9) * 0.05, 0.0)
    out += np.sin(2 * np.pi * 130.81 * after) * pad

    # fade the very end to zero to match the visual fade
    tail = np.clip((DURATION - t) / 0.45, 0, 1)
    out *= tail

    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * 0.89  # normalise with headroom

    pcm = (out * 32767).astype("<i2")
    data = pcm.tobytes()
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE")
        f.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, SR, SR * 2, 2, 16))
        f.write(b"data" + struct.pack("<I", len(data)))
        f.write(data)
    print("wrote %s (%.2fs, %d bytes)" % (path, DURATION, len(data)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sting.wav")
