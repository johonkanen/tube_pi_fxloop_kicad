"""Dynamics of the PI + power stage + feedback (simulation plan 2b, after the large-signal run):

  A. Recovery after loud bursts (blocking): a 300 ms, 100 Hz burst well into clipping on top
     of a small, continuous 1 kHz probe. Grid current charges the coupling capacitors, so the
     output tubes' grid bias shifts colder; the probe shows how much gain is lost and for how
     long, and whether it picks up crossover distortion while the bias recovers.
  B. A guitar-like drive signal: synthesized plucked notes (Karplus-Strong) as the PI input,
     at crunch and cranked levels. Envelope (sustain, compression), bias shift over the note,
     intermodulation, and WAV files for listening (out/, not committed).

Writes results/dynamics.md and results/dynamics_*.png.
"""
import os
import wave
from multiprocessing import Pool

os.environ.setdefault('OMP_NUM_THREADS', '1')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import nfb
import stage

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
K = dict(mode='grid2', pol=-1)
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6']
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
STEP = 5e-6           # 200 kHz sampling: audio band only (the HF stability runs use 0.5 us)

# 5 % THD onsets at 1 kHz from run_large_signal.py (results/large_signal.md)
ONSET = {(400.0, '100k'): 2.81, (400.0, 'none'): 0.95, (400.0, '47k'): 4.49, (200.0, '100k'): 1.14}
FBNET = {'100k': (dict(rf=100e3, cf=22e-12), True), '47k': (dict(rf=47e3, cf=47e-12), True),
         'none': ({}, False)}
NODES = ['out', 'gl1', 'gl3', 'pi_gx']


def simulate(va, fb, vin, tstop, stage_p=None, pi=None):
    net, on = FBNET[fb]
    vecs = ' '.join(f'v({n})' for n in NODES)
    an = dict(vin=vin, control=f"tran {STEP} {tstop} 0 {STEP}\nlinearize {vecs}\nwrdata {{dir}}/w.txt {vecs}")
    for opt in ('method=gear reltol=1e-4', 'method=gear reltol=1e-3 itl4=100', 'method=trap reltol=1e-3 itl4=100'):
        try:
            w = nfb.run(nfb.netlist(va, 0.0, 0.0, an, nfb=on, net=net, stage_p=stage_p, pi=pi, options=opt, **K), ['w'])['w']
        except RuntimeError:
            continue
        if w[-1, 0] >= tstop * 0.999 and np.all(np.isfinite(w)):
            t = w[:, 0]
            return t, {n: w[:, 1 + 2 * i] for i, n in enumerate(NODES)}
    raise RuntimeError('transient failed')


def movavg(x, n):
    """Centred moving average with edge-value padding (zero padding would drag the ends)."""
    k = np.ones(n) / n
    h = n // 2
    xp = np.pad(x, (h, n - 1 - h), mode='edge')
    return np.convolve(xp, k, mode='valid')


def bandpass_env(t, y, f0, bw):
    """Envelope of y around f0 (FFT brick-wall band-pass, then the analytic-signal magnitude)."""
    n = len(y)
    Y = np.fft.fft(y)
    f = np.fft.fftfreq(n, t[1] - t[0])
    H = (np.abs(np.abs(f) - f0) < bw / 2).astype(float)
    H[f < 0] = 0.0                       # analytic signal: positive frequencies only, doubled
    return np.abs(np.fft.ifft(Y * H * 2))


# ------------------------------------------------------------------ A. burst recovery
T0, T1, TEND = 0.15, 0.45, 1.45        # burst from T0 to T1, run to TEND
FB_BURST, FP = 100.0, 1000.0


def burst_case(args):
    key, va, fb, rel, cc = args[:5]
    pi_over = args[5] if len(args) > 5 else None
    on = ONSET[(va, fb)]
    pa = on * 10 ** (-20 / 20)           # probe 20 dB under the onset (clean)
    ba = on * 10 ** (rel / 20)
    tr = 2e-3
    vin = (f"Bin pi_src 0 V = {{{pa:.6g}*sin(2*pi*{FP}*time) + {ba:.6g}*sin(2*pi*{FB_BURST}*time)"
           f"*0.25*(1+tanh((time-{T0})/{tr}))*(1-tanh((time-{T1})/{tr}))}}")
    try:
        t, v = simulate(va, fb, vin, TEND, stage_p=dict(cc=cc), pi=pi_over)
    except RuntimeError as e:
        return key, dict(error=str(e))
    dt = t[1] - t[0]
    env = movavg(bandpass_env(t, v['out'], FP, 200.0), int(5e-3 / dt))
    ref = np.mean(env[(t > 0.10) & (t < 0.145)])
    edb = 20 * np.log10(np.maximum(env, 1e-9) / ref)
    after = (t > T1 + 0.01) & (t < TEND - 0.03)
    dip = float(np.min(edb[after]))
    bad = np.where(after & (np.abs(edb) > 1.0))[0]
    trec = float(t[bad[-1]] - T1) if len(bad) else 0.0
    nav = int(20e-3 / dt)
    bias = {n: movavg(v[n], nav) for n in ('gl1', 'gl3', 'pi_gx')}
    b0 = {n: np.mean(bias[n][(t > 0.10) & (t < 0.145)]) for n in bias}
    shift = {n: bias[n] - b0[n] for n in bias}
    worst_pt = 'gl1' if np.min(shift['gl1']) < np.min(shift['gl3']) else 'gl3'
    s = shift[worst_pt]
    smax = float(np.min(s[(t > T0) & (t < T1 + 0.05)]))
    rec = np.where(after & (np.abs(s) > 1.0))[0]
    tbias = float(t[rec[-1]] - T1) if len(rec) else 0.0
    pimax = float(np.min(shift['pi_gx'][(t > T0) & (t < T1 + 0.05)]))
    pirec = np.where(after & (np.abs(shift['pi_gx']) > 1.0))[0]
    tpi = float(t[pirec[-1]] - T1) if len(pirec) else 0.0
    # low-frequency thump at the speaker after the burst: content under 40 Hz
    Y = np.fft.rfft(v['out'])
    fr = np.fft.rfftfreq(len(t), dt)
    lf = np.fft.irfft(Y * (fr < 40.0), len(t))
    thump = float(np.max(np.abs(lf[after])))

    def probe_thd(ta, tb):
        m = (t >= ta) & (t < tb)
        y = v['out'][m] - np.mean(v['out'][m])
        Y = np.abs(np.fft.rfft(y * np.hanning(len(y))))
        f = np.fft.rfftfreq(len(y), dt)
        a = lambda k: np.sqrt(np.sum(Y[np.abs(f - k * FP) < 15] ** 2))
        return 100 * np.sqrt(sum(a(k) ** 2 for k in range(2, 8))) / a(1)
    return key, dict(t=t[::20], edb=edb[::20], shift=s[::20], pishift=shift['pi_gx'][::20],
                     dip=dip, trec=trec, smax=smax, tbias=tbias, pimax=pimax, tpi=tpi, thump=thump,
                     thd_pre=probe_thd(0.05, 0.145), thd_post=probe_thd(T1 + 0.01, T1 + 0.06),
                     vbias=float(nfb.bias_for(va)[0]))


# ------------------------------------------------------------------ B. guitar-like signal
FS = 48000


def karplus(freq, dur, fs=FS, decay=0.996, seed=1, pick=0.18):
    """Plucked string: noise burst in a delay line with an averaging low-pass (Karplus-Strong),
    plus a pickup-position comb. Returns a waveform normalised to 1 peak."""
    rng = np.random.default_rng(seed)
    n = int(fs * dur)
    L = int(round(fs / freq))
    buf = rng.uniform(-1, 1, L)
    buf = buf - buf.mean()
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % L]
        nxt = buf[(i + 1) % L]
        buf[i % L] = decay * 0.5 * (buf[i % L] + nxt)
    d = int(pick * L)                    # pickup position comb
    out = out - np.concatenate([np.zeros(d), out[:-d]])
    return out / np.max(np.abs(out))


def guitar_signals():
    dur = 2.0
    note = karplus(110.0, dur, seed=3)                                    # A2
    chord = np.zeros(int(FS * dur))
    for k, (f, sd) in enumerate(((82.41, 4), (123.47, 5), (164.81, 6))):  # E5 power chord
        off = int(FS * 0.015 * k)                                          # downstroke
        chord[off:] += karplus(f, dur, seed=sd)[:len(chord) - off]
    chord /= np.max(np.abs(chord))
    # a small attack fade so the first sample isn't a step
    for x in (note, chord):
        x[:48] *= np.linspace(0, 1, 48)
    return {'A2 note': note, 'E5 power chord': chord}


def pwl_line(x, amp, fs_out=24000):
    xs = x[::FS // fs_out] * amp
    ts = np.arange(len(xs)) / fs_out
    pts = ' '.join(f"{a:.6g} {b:.5g}" for a, b in zip(ts, xs))
    # split into continuation lines
    words = pts.split(' ')
    lines, cur = [], []
    for i in range(0, len(words), 2):
        cur.append(words[i] + ' ' + words[i + 1])
        if len(cur) == 40:
            lines.append('+ ' + ' '.join(cur))
            cur = []
    if cur:
        lines.append('+ ' + ' '.join(cur))
    return "Vin pi_src 0 dc 0 PWL(\n" + '\n'.join(lines) + "\n+ )"


def write_wav(path, y, fs=FS):
    y = y / (np.max(np.abs(y)) + 1e-12) * 0.89
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes((y * 32767).astype('<i2').tobytes())


def guitar_case(args):
    key, sname, x, va, fb, rel = args
    amp = ONSET[(va, fb)] * 10 ** (rel / 20)
    try:
        t, v = simulate(va, fb, pwl_line(x, amp), 2.0)
    except RuntimeError as e:
        return key, dict(error=str(e))
    dt = t[1] - t[0]
    y = v['out']
    tw = np.arange(0, 2.0, 1 / FS)
    yo = np.interp(tw, t, y)
    xi = x[:len(tw)] * amp
    fname = f"guitar_{sname.split()[0]}_{int(va)}V_{fb}_{'+' if rel >= 0 else ''}{rel}dB.wav"
    write_wav(os.path.join(OUT, fname), yo)
    nwin = int(0.02 * FS)
    env_in = 20 * np.log10(np.sqrt(movavg(xi ** 2, nwin)) + 1e-9)
    env_out = 20 * np.log10(np.sqrt(movavg(yo ** 2, nwin)) + 1e-9)

    def fall10(e):
        i0 = int(np.argmax(e[:int(0.3 * FS)]))
        below = np.where(e[i0:] < e[i0] - 10)[0]
        return (below[0] / FS) if len(below) else float('nan')
    m = (tw > 0.05) & (tw < 1.5)
    rng_in = float(np.max(env_in[m]) - np.min(env_in[m]))
    rng_out = float(np.max(env_out[m]) - np.min(env_out[m]))
    nav = int(20e-3 / dt)
    b1, b3 = movavg(v['gl1'], nav), movavg(v['gl3'], nav)
    b0 = float(nfb.bias_for(va)[0])
    shift = np.minimum(b1, b3) - b0
    # inharmonic / intermodulation energy in 0.3-0.8 s: energy not within 4 Hz of a harmonic
    seg = (tw >= 0.3) & (tw < 0.8)
    Y = np.abs(np.fft.rfft(yo[seg] * np.hanning(seg.sum()))) ** 2
    f = np.fft.rfftfreq(seg.sum(), 1 / FS)
    fund = (110.0,) if sname.startswith('A2') else (82.41, 123.47, 164.81)
    harm = np.zeros_like(f, dtype=bool)
    for f0 in fund:
        for k in range(1, int(8000 / f0) + 1):
            harm |= np.abs(f - k * f0) < 4
    band = f < 8000
    inh = 10 * np.log10(np.sum(Y[band & ~harm]) / np.sum(Y[band & harm]))
    return key, dict(t=tw[::48], ein=env_in[::48], eout=env_out[::48], tb=t[::200], shift=shift[::200],
                     fall_in=fall10(env_in), fall_out=fall10(env_out), rng_in=rng_in, rng_out=rng_out,
                     smax=float(np.min(shift)), send=float(np.mean(shift[(t > 1.8)])), inh=inh,
                     wav=fname, amp=amp)


def style(ax):
    ax.grid(True, which='major', color=GRID, lw=0.8)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)


def main():
    pool = Pool(30)
    md = ["# Burst recovery and a guitar-like drive signal", "",
          "Generated by `run_dynamics.py` (ngspice transient, 5 µs step). Circuit as in `run_nfb.py`:",
          "12AX7 long-tailed pair, 4x EL34 with fixed bias sources (0.1 µF / 220k / 5.6k grid stopper",
          "per tube unless stated), 1650TA, representative 8 Ω speaker, feedback into the PI's second",
          "grid. Levels are relative to each case's 5 % THD onset at 1 kHz (results/large_signal.md).",
          "The bias sources are ideal and fixed: the real bias loop (cathode shunts, control card) is",
          "far slower than these events.", ""]

    # ---------------------------------------------------------------- A
    BC = [('base +12', 400.0, '100k', 12, 0.1e-6), ('base +20', 400.0, '100k', 20, 0.1e-6),
          ('cc47 +20', 400.0, '100k', 20, 47e-9), ('cc22 +20', 400.0, '100k', 20, 22e-9),
          ('cc22 +12', 400.0, '100k', 12, 22e-9),
          ('nofb +20', 400.0, 'none', 20, 0.1e-6), ('fb47 +20', 400.0, '47k', 20, 0.1e-6),
          ('200V +20', 200.0, '100k', 20, 0.1e-6), ('200V cc22 +20', 200.0, '100k', 20, 22e-9)]
    LBL = {'base +12': 'Rf 100k, 0.1 µF, +12 dB', 'base +20': 'Rf 100k, 0.1 µF, +20 dB',
           'cc47 +20': 'Rf 100k, 47 nF, +20 dB', 'cc22 +20': 'Rf 100k, 22 nF, +20 dB',
           'cc22 +12': 'Rf 100k, 22 nF, +12 dB',
           'nofb +20': 'No feedback, 0.1 µF, +20 dB', 'fb47 +20': 'Rf 47k, 0.1 µF, +20 dB',
           '200V +20': '200 V, Rf 100k, 0.1 µF, +20 dB', '200V cc22 +20': '200 V, Rf 100k, 22 nF, +20 dB'}
    res = dict(pool.map(burst_case, [(k, va, fb, rel, cc) for k, va, fb, rel, cc in BC]))
    md += ["## A. Recovery after a loud burst", "",
           f"A {int((T1-T0)*1e3)} ms burst at {FB_BURST:.0f} Hz (level as stated, relative to the onset) on top of",
           "a continuous 1 kHz probe 20 dB under the onset. Probe gain is the 1 kHz content of the",
           "speaker voltage relative to before the burst. Grid bias shift is the 20 ms average at the",
           "power tube grid (after the coupling capacitor), worst tube, relative to idle.", "",
           "| Case | Idle bias | Power grid shift (worst) | Back within 1 V | PI input grid shift | Back within 1 V | Probe gain dip | Probe back within 1 dB | Probe THD before / just after | LF thump at the speaker |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for k, *_r in BC:
        r = res[k]
        if 'error' in r:
            md.append(f"| {LBL[k]} | failed | | | | | | | | |")
            continue
        md.append(f"| {LBL[k]} | {r['vbias']:.1f} V | {r['smax']:+.1f} V | {r['tbias']*1e3:.0f} ms | "
                  f"{r['pimax']:+.1f} V | {r['tpi']*1e3:.0f} ms | "
                  f"{r['dip']:+.1f} dB | {r['trec']*1e3:.0f} ms | {r['thd_pre']:.1f} / {r['thd_post']:.1f} % | {r['thump']:.1f} V pk |")
    md += [""]
    fig, axs = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for (k, c) in zip(('base +12', 'base +20', 'cc22 +20', 'nofb +20', '200V +20'), CAT):
        r = res[k]
        if 'error' in r:
            continue
        axs[0].plot(r['t'] * 1e3, r['shift'], color=c, lw=2, label=LBL[k])
        axs[1].plot(r['t'] * 1e3, r['edb'], color=c, lw=2, label=LBL[k])
    for ax in axs:
        style(ax)
        ax.axvspan(T0 * 1e3, T1 * 1e3, color=GRID, alpha=0.5, lw=0)
    axs[0].set_ylabel('Power tube grid bias shift (V)', fontsize=9, color=INK2)
    axs[1].set_ylabel('1 kHz probe gain (dB)', fontsize=9, color=INK2)
    axs[1].set_ylim(-25, 15)
    axs[1].set_xlabel('ms (shaded: the burst)', fontsize=9, color=INK2)
    axs[0].legend(fontsize=8, frameon=False, loc='lower right')
    axs[0].set_title('Blocking: grid bias shift and probe gain around a 300 ms burst', fontsize=11, color=INK, loc='left')
    fig.tight_layout()
    fig.savefig(os.path.join(RES, 'dynamics_burst.png'), dpi=130)
    plt.close(fig)
    md += ["![Burst recovery](dynamics_burst.png)", ""]

    # ---------------------------------------------------------------- B
    sigs = guitar_signals()
    GC = []
    for sname, x in sigs.items():
        for va, fb, rel in ((400.0, '100k', 6), (400.0, '100k', 18), (200.0, '100k', 18), (400.0, 'none', 18)):
            GC.append(((sname, va, fb, rel), sname, x, va, fb, rel))
    gres = dict(pool.map(guitar_case, GC))
    md += ["## B. Guitar-like drive signal", "",
           "Synthesized plucked strings (Karplus-Strong with a pickup-position comb), 2 s: an A2 note",
           "(110 Hz) and an E5 power chord (E2 + B2 + E3, 15 ms downstroke). Peak level at the PI input",
           "relative to the 1 kHz onset; the pluck's peak is a short transient, so +6 dB only clips the",
           "attack, +18 dB keeps the stage clipped through most of the note. 'Fall 10 dB' is the time",
           "from the envelope peak to 10 dB below it (longer = more sustain). 'Range' is the envelope",
           "range over 0.05-1.5 s (smaller = more compression). Inharmonic energy: everything within",
           "8 kHz that is not within 4 Hz of a harmonic of the played notes, 0.3-0.8 s (IM products).", "",
           "| Signal | V_ANODE | Feedback | Level | Fall 10 dB: in / out | Range: in / out | Bias shift max / at 1.8 s | Inharmonic energy | WAV (out/) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for key, sname, x, va, fb, rel in GC:
        r = gres[key]
        if 'error' in r:
            md.append(f"| {sname} | {va:.0f} V | {fb} | {rel:+d} dB | failed | | | | |")
            continue
        md.append(f"| {sname} | {va:.0f} V | {fb} | {rel:+d} dB | {r['fall_in']:.2f} / {r['fall_out']:.2f} s | "
                  f"{r['rng_in']:.0f} / {r['rng_out']:.0f} dB | {r['smax']:+.1f} / {r['send']:+.1f} V | "
                  f"{r['inh']:.0f} dB | `{r['wav']}` |")
    md += ["", "The WAV files are the speaker-terminal voltage, normalised. They have no cabinet or",
           "microphone in them: convolve with a cabinet impulse response before judging them by ear.", ""]
    for sname in sigs:
        x = sigs[sname]
        write_wav(os.path.join(OUT, f"guitar_{sname.split()[0]}_input.wav"), x)

    fig, axs = plt.subplots(2, 2, figsize=(13, 7), sharex=True)
    for j, sname in enumerate(sigs):
        ax = axs[0, j]
        style(ax)
        first = True
        for (va, fb, rel), c in zip(((400.0, '100k', 6), (400.0, '100k', 18), (200.0, '100k', 18), (400.0, 'none', 18)), CAT):
            r = gres[(sname, va, fb, rel)]
            if 'error' in r:
                continue
            if first:
                ax.plot(r['t'], r['ein'] - np.max(r['ein']), color=INK2, lw=1.5, ls='--', label='input (shape)')
                first = False
            ax.plot(r['t'], r['eout'] - np.max(r['eout']), color=c, lw=2,
                    label=f"{va:.0f} V, {'no feedback' if fb == 'none' else 'Rf ' + fb}, {rel:+d} dB")
            axs[1, j].plot(r['tb'], r['shift'], color=c, lw=2)
        ax.set_ylim(-40, 3)
        ax.set_title(f"{sname}: envelope relative to its peak", fontsize=10, color=INK, loc='left')
        ax.set_ylabel('dB', fontsize=9, color=INK2)
        style(axs[1, j])
        axs[1, j].set_ylabel('Grid bias shift (V)', fontsize=9, color=INK2)
        axs[1, j].set_xlabel('s', fontsize=9, color=INK2)
        ax.legend(fontsize=7, frameon=False, loc='lower left')
    fig.tight_layout()
    fig.savefig(os.path.join(RES, 'dynamics_guitar.png'), dpi=130)
    plt.close(fig)
    md += ["![Guitar-like signal](dynamics_guitar.png)", ""]

    pool.close()
    with open(os.path.join(RES, 'dynamics.md'), 'w') as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == '__main__':
    main()
