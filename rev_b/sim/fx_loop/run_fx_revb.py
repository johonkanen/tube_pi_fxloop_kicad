#!/usr/bin/env python3
"""Rev B FX loop levels with the rear send / return pots and the 0 / -20 dB pad (IF-1.1,
SPECIFICATION FX-3), the >= 1 Mohm input on the 140 kohm preamp output (interfaces.md note 1),
send-to-return coupling on the W23 ribbon, noise with the return pot low, and the PI-4
attenuator steps. Circuit: fx_revb.py. Writes results/fx_revb.md. About a minute.
"""
import os
from multiprocessing import Pool

import numpy as np

import fx_revb as F
from simrun import run

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, 'results')


def db(x):
    return 20 * np.log10(np.maximum(np.abs(np.asarray(x, dtype=float)), 1e-15))


def ac(mode, nodes, **kw):
    net, out = F.netlist(mode, **kw)
    real = [n if n != 'out' else out for n in nodes]
    _, f, _, o = run(net, 'ac dec 30 5 100k\nwrdata a.txt ' + ' '.join(f'vm({n})' for n in real))
    if 'a.txt' not in f:
        raise RuntimeError(o[-2000:])
    a = f['a.txt']
    return a[:, 0], {n: a[:, 1 + 2 * i] for i, n in enumerate(nodes)}


def at(f, y, fr):
    return float(np.interp(np.log(fr), np.log(f), y))


# ---------------------------------------------------------------- jobs
def j_bypass(_):
    f, y = ac('bypass', ['out', 'inp', 'pre', 'ssrc', 'np', 'm'], src='ac')
    g = db(y['out'])
    g1k = at(f, g, 1e3)
    lo = f[np.argmax(g > g1k - 3)]
    hi = f[len(g) - 1 - np.argmax(g[::-1] > g1k - 3)]
    # input impedance: I = (Vpre - Vinp) / Rsrc (magnitudes from the AC run, phase ignored -> use complex run)
    net, _ = F.netlist('bypass')
    _, ff, _, _ = run(net, 'ac dec 30 5 100k\nwrdata z.txt vr(inp) vi(inp)')
    z = ff['z.txt']
    vin = z[:, 1] + 1j * z[:, 3]
    zin = vin / ((1 - vin) / F.D['rsrc'])
    return 'bypass', dict(g1k=g1k, lo=lo, hi=hi, g20k=at(f, g, 2e4) - g1k, g20=at(f, g, 20) - g1k,
                          inp1k=at(f, db(y['inp']), 1e3), inp20k=at(f, db(y['inp']), 2e4),
                          ssrc=at(f, db(y['ssrc']), 1e3), p=at(f, db(y['np']), 1e3), m=at(f, db(y['m']), 1e3),
                          zin1k=abs(np.interp(1e3, z[:, 0], zin.real) + 1j * np.interp(1e3, z[:, 0], zin.imag)),
                          zin10k=abs(np.interp(1e4, z[:, 0], zin.real) + 1j * np.interp(1e4, z[:, 0], zin.imag)))


def j_sendlaw(args):
    x, load = args
    f, y = ac('bypass', ['sj'], send_pot=x, send_load=load)
    return ('sendlaw', x, load), at(f, db(y['sj']), 1e3)


def j_retlaw(args):
    x, taper, pad = args
    f, y = ac('series', ['out'], ret_pot=x, ret_taper=taper, pad=pad, ret_src='ac', src='off')
    return ('retlaw', x, taper, pad), at(f, db(y['out']), 1e3)


def j_tran_send(args):
    amp, load = args
    net, out = F.netlist('bypass', src='sin', amp=amp, send_pot=1.0, send_load=load)
    v, _, thd, o = run(net, 'tran 5u 80m 0 5u\nfourier 1k v(sj)\nfourier 1k v(ssrc)\nfourier 1k v(%s)\n'
                       'meas tran sjpp PP v(sj) from=60m to=80m\nmeas tran outpp PP v(%s) from=60m to=80m\n'
                       'meas tran ppp PP v(np) from=60m to=80m' % (out, out))
    return ('send', amp, load), dict(sj=v.get('sjpp', 0) / 2, out=v.get('outpp', 0) / 2, p=v.get('ppp', 0) / 2,
                                     thd=thd if len(thd) == 3 else [float('nan')] * 3)


def j_tran_ret(args):
    amp, pad = args
    net, out = F.netlist('series', src='off', ret_src='sin', ret_amp=amp, pad=pad)
    v, _, thd, o = run(net, 'tran 5u 80m 0 5u\nfourier 1k v(%s)\nmeas tran outpp PP v(%s) from=60m to=80m\n'
                       'meas tran nwpp PP v(nw) from=60m to=80m\nmeas tran mpp PP v(m) from=60m to=80m' % (out, out))
    return ('ret', amp, pad), dict(out=v.get('outpp', 0) / 2, nw=v.get('nwpp', 0) / 2, m=v.get('mpp', 0) / 2,
                                   thd=thd[0] if thd else float('nan'))


def j_noise(args):
    mode, x, pad = args
    net, out = F.netlist(mode, src='off', ret_src='ac', ret_pot=x, pad=pad)
    net = net.replace('Vret rj0 0 DC 0 AC 1', 'Vret rj0 0 DC 0 AC 1')
    _, _, _, o = run(net, f'noise v({out}) vret dec 20 20 20k\nsetplot noise2\nprint onoise_total')
    import re
    m = re.search(r'onoise_total\s*=\s*([-+0-9.eE]+)', o)
    return ('noise', mode, x, pad), float(m.group(1)) if m else float('nan')


def j_cpl(args):
    xs, xr, c = args
    # leak: unit disconnected (gain 0), coupling only; wanted: unit unity, no coupling
    f, y0 = ac('series', ['out'], send_pot=xs, ret_pot=xr, unit_gain=0.0, ccpl=c)
    f, y1 = ac('series', ['out'], send_pot=xs, ret_pot=xr, unit_gain=1.0, ccpl=0.0)
    r = db(y0['out']) - db(y1['out'])
    return ('cpl', xs, xr, c), (at(f, r, 1e3), at(f, r, 1e4))


def j_att(step):
    f, y = ac('bypass', ['out'], att=step)
    return ('att', step), at(f, db(y['out']), 1e3)


def main():
    os.makedirs(RES, exist_ok=True)
    jobs = [(j_bypass, None)]
    jobs += [(j_sendlaw, (x, ld)) for x in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0) for ld in (10e3, 1e6)]
    jobs += [(j_retlaw, (x, t, pad)) for x in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
             for t in ('log', 'lin') for pad in (False, True)]
    jobs += [(j_tran_send, (a, ld)) for a in (9, 17, 20) for ld in (10e3, 1e6)]
    jobs += [(j_tran_ret, (a, pad)) for a in (0.5, 1.0, 2.0, 3.0, 4.0, 6.0) for pad in (False,)]
    jobs += [(j_tran_ret, (a, True)) for a in (5.0, 10.0, 20.0, 30.0)]
    jobs += [(j_noise, ('series', x, pad)) for x in (0.05, 0.2, 0.5, 1.0) for pad in (False, True)]
    jobs += [(j_noise, ('bypass', 1.0, False))]
    jobs += [(j_cpl, (xs, xr, c)) for xs, xr in ((0.4, 1.0), (0.7, 0.6), (1.0, 0.4), (0.5, 0.8)) for c in (0.01e-12, 0.1e-12, 0.3e-12, 1e-12)]
    jobs += [(j_att, s) for s in range(0, 19)]
    with Pool(min(30, os.cpu_count() or 4)) as p:
        res = dict(p.starmap(lambda_run, jobs))
    write(res)


def lambda_run(fn, a):
    return fn(a)


def write(R):
    b = R['bypass']
    L = ['# Rev B FX loop: levels, headroom, noise, coupling, PI-4 steps', '',
         'Generated by `run_fx_revb.py` (circuit `fx_revb.py`); do not edit. 12AX7 Dempwolf model (RSD-1),',
         'generic NJFET switch, preamp output modelled as a 140 kohm source (interfaces.md note 1) with 45 pF',
         '(W22 cable 40 pF + connector / PCB 5 pF) on the line. "Preamp" levels are the open-circuit level of',
         'that source. Loop output = the PI grid side of the PI input cap (10n, 1M), after the PI-4 attenuator.', '',
         '## Bypass path and input', '',
         f'- Preamp to PI input, attenuator at 0 dB: **{b["g1k"]:+.2f} dB** at 1 kHz; -3 dB at {b["lo"]:.0f} Hz and '
         f'{b["hi"] / 1e3:.1f} kHz; {b["g20"]:+.1f} dB at 20 Hz, {b["g20k"]:+.1f} dB at 20 kHz.',
         f'- At the PI + FX input: {b["inp1k"]:+.2f} dB at 1 kHz (the 2.2M + follower load on 140k), {b["inp20k"]:+.2f} dB at 20 kHz '
         f'(140k into 45 pF + the follower).',
         f'- Input impedance: {b["zin1k"] / 1e6:.2f} Mohm at 1 kHz, {b["zin10k"] / 1e3:.0f} kohm at 10 kHz (the 45 pF of cable and PCB dominate above a few kHz).',
         f'- SEND_SRC {b["ssrc"]:+.1f} dB re the preamp (pot at full, 10k load on the jack), dry node P {b["p"]:+.1f} dB, mixer node M {b["m"]:+.1f} dB.',
         '', '## Send level against the SEND LEVEL pot (100k log), at the jack', '',
         '| Rotation | 10k load (dB re preamp) | 1M load | Jack level at 10 V / 17 V peak preamp (1M load) |', '|---|---|---|---|']
    for x in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        a, c = R[('sendlaw', x, 10e3)], R[('sendlaw', x, 1e6)]
        L.append(f'| {x:.1f} | {a:+.1f} | {c:+.1f} | {10 * 10 ** (c / 20):.2f} / {17 * 10 ** (c / 20):.2f} V |')
    L += ['', 'Pedal nominal is about 0.45 V peak (-10 dBV), line +4 dBu = 1.74 V peak.', '',
          '## Return path against the RETURN LEVEL pot (series mode, return jack to loop output)', '',
          'Unity loop = the bypass gain above: a return-jack level gives the same loop output as the dry path when the',
          'value in this table equals the bypass gain plus the dB by which the jack level is below the preamp level.', '',
          '| Rotation | log, pad 0 dB | log, pad -20 dB | linear, pad 0 dB | linear, pad -20 dB |', '|---|---|---|---|---|']
    for x in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        L.append(f'| {x:.1f} | ' + ' | '.join(f'{R[("retlaw", x, t, p)]:+.1f}' for t in ('log', 'lin') for p in (False, True)) + ' |')
    full = R[('retlaw', 1.0, 'log', False)]
    unity = 10 ** ((b['g1k'] - full) / 20) * 10
    L += ['', f'Return-jack level for unity loop gain at 10 V peak preamp, pot full, pad off: **{unity:.2f} V peak**; with the pad: '
          f'{10 ** ((b["g1k"] - R[("retlaw", 1.0, "log", True)]) / 20) * 10:.1f} V peak.', '',
          '## Headroom', '', 'Send, SEND LEVEL pot at full (worst case), bypass mode:', '',
          '| Preamp (V pk) | Jack load | Jack (V pk) | Jack THD | SEND_SRC THD | Dry node P (V pk) | Loop output (V pk) | Loop THD |',
          '|---|---|---|---|---|---|---|---|']
    for a in (9, 17, 20):
        for ld in (10e3, 1e6):
            r = R[('send', a, ld)]
            L.append(f'| {a} | {"10k" if ld < 1e5 else "1M"} | {r["sj"]:.2f} | {r["thd"][0]:.2f} % | {r["thd"][1]:.2f} % | {r["p"]:.2f} | {r["out"]:.2f} | {r["thd"][2]:.2f} % |')
    L += ['', 'Return, series mode, RETURN LEVEL pot at full (worst case), 1 kHz at the return jack:', '',
          '| Return jack (V pk) | Pad | W node (V pk, JFET switch) | M node (V pk) | Loop output (V pk) | THD |', '|---|---|---|---|---|---|']
    for k in sorted(k for k in R if k[0] == 'ret'):
        r = R[k]
        L.append(f'| {k[1]} | {"-20 dB" if k[2] else "0 dB"} | {r["nw"]:.2f} | {r["m"]:.2f} | {r["out"]:.2f} | {r["thd"]:.2f} % |')
    nom = 10 ** (b['g1k'] / 20) * 10 / np.sqrt(2)
    L += ['', '## Noise at the loop output (20 Hz-20 kHz, resistor noise + 1.6k per grid for the tubes)', '',
          f'Against the nominal loop output (10 V peak preamp in bypass: {nom:.2f} V rms):', '',
          '| Mode | RETURN pot | Pad | Output noise (µV rms) | Signal / noise (dB) |', '|---|---|---|---|---|']
    for k in sorted(k for k in R if k[0] == 'noise'):
        n = R[k]
        L.append(f'| {k[1]} | {k[2]:.2f} | {"-20 dB" if k[3] else "0 dB"} | {n * 1e6:.1f} | {db(nom / n):.0f} |')
    L += ['', '## Send-to-return coupling on W23 (series mode, dry leak around the effects unit)', '',
          'Leak = loop output with the effects unit silent and a capacitance from SEND_SRC to RETURN_SIG, relative to',
          'the wanted output with a unity effects unit and no coupling, at the same pot settings.', '',
          '| SEND pot | RETURN pot | Ccpl | Leak at 1 kHz | Leak at 10 kHz |', '|---|---|---|---|---|']
    for k in sorted(k for k in R if k[0] == 'cpl'):
        a, c = R[k]
        L.append(f'| {k[1]:.1f} | {k[2]:.1f} | {k[3] * 1e12:.2f} pF | {a:.0f} dB | {c:.0f} dB |')
    L += ['', '## PI-4 attenuator (five L-sections, Z0 49.9k, terminated at the PI input)', '',
          '| Step (dB) | Loop output re step 0 (dB) | Error (dB) |', '|---|---|---|']
    g0 = R[('att', 0)]
    for s in range(19):
        g = R[('att', s)] - g0
        L.append(f'| {s} | {g:+.2f} | {g + s:+.2f} |')
    open(os.path.join(RES, 'fx_revb.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
