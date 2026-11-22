"""Preamp B+ linear regulator: netlist generator and ngspice tests (docs/preamp_regulator.md).

Topology (one block per output, identical except for the zener string and the limit resistors):

  raw 430 V ──┬──────────────────────────────┬──── drain  M2 (HV N-MOSFET, pass device)
              │                              │
          M1 depletion CCS (LND150 class)    │   gate ── Rg 10k ── gf ──┬── Rf 1M ── zt
              │ Rset                         │                       Cf 2.2u
              zt ── zener string ── 0        │   source ── Rs ──┬── out ── Cout ── loads
                                             │   Q1 (current limit with foldback):
                                             │     collector to gate, emitter to out,
                                             │     base: R1 from source, R2 to out, R3 from raw
  Dgs: 15 V zener gate-source.  Rbleed across the output.  Ddis from gf to raw: discharges Cf
  (otherwise left at ~390 V after power-off) into the raw rail's bleeders.

The reference is a CCS-fed zener string filtered by Rf·Cf (corner well below 1 Hz), so the
zener noise and the raw-rail ripple are both removed before the gate, and Rf·Cf also gives a
soft start of several seconds. M2 is a source follower: no feedback loop, so no stability
problem with any output capacitance. Vout = Vzener - Vgs(M2) - I·Rs.
"""
import os
import re
import subprocess
import tempfile

MODELS = """
* depletion-mode CCS device, LND150 class (500 V; Idss 1-3 mA; Vgs(off) -1..-3 V)
.model LND NMOS(level=1 vto=-1.8 kp=2.5m lambda=0.002 cgso=1n cgdo=0.2n)
* pass device, 800 V class N-MOSFET (e.g. STP4N80K5, IRFBG20 class): VDMOS with body diode
.model PASS VDMOS(vto=3.5 kp=1.0 rd=2 rs=0.05 lambda=0.001 cgdmax=60p cgdmin=4p cgs=450p cjo=60p is=1e-12 rb=0.5)
* current-limit transistor
.model QL NPN(is=1e-14 bf=200 vaf=100 cjc=4p cje=8p)
* Cf discharge diode, 1N4007 class (1000 V)
.model DDIS D(is=5n rs=0.05 n=1.8 cjo=15p bv=1000)
* gate-source protection zener 15 V
.model DGS D(bv=15 ibv=5m rs=5 cjo=50p)
"""


DEFAULTS = dict(
    vraw=430.0,
    zeners=(130.0, 130.0, 130.0),  # zener string (sets Vout = sum - Vgs - I*Rs)
    rz=400.0,                      # dynamic impedance per zener (high-voltage zeners at ~2 mA)
    en_z=10e-6,                    # zener noise density per zener, V/rtHz (avalanche, pessimistic)
    rset=330.0,                    # CCS current set resistor (about 2 mA with LND)
    rf=1e6, cf=2.2e-6,             # reference filter / soft start
    rg=10e3,                       # gate stopper
    rs=20.0, r1=1e3, r2=10e3, r3=820e3,   # current limit with foldback
    cout=47e-6, esr=0.5, cfilm=0.1e-6, rbleed=470e3,
    iload=0.015,                   # nominal load current (A), resistive load at Vout
    rdrain=0.0,                    # optional drain resistor (raw to M2's drain): takes part of the drop
    temp=27.0,                     # circuit temperature (C); run_thermal_foldback.py sweeps it
)


def zener_models(zeners, rz):
    return ''.join(f'.model DZ{i} D(bv={vz} ibv=1m rs={rz} cjo=20p)\n' for i, vz in enumerate(zeners))


def netlist(test, p, vout_guess=None):
    q = dict(DEFAULTS, **p)
    vout = vout_guess if vout_guess else sum(q['zeners']) - 4.0
    rload = vout / q['iload'] if q['iload'] > 0 else 1e9
    L = [f'* preamp regulator test={test}', MODELS, zener_models(q['zeners'], q['rz']), f'.temp {q["temp"]}']
    # raw rail
    if test == 'startup':
        L.append(f'Vraw raw 0 PWL(0 0 0.5 {q["vraw"]})')
    elif test == 'line':
        L.append(f'Vraw raw 0 DC {q["vraw"]}')
    else:
        L.append(f'Vraw raw 0 DC {q["vraw"]} AC 1')
    # CCS + zener string with a noise source
    L += ['Mccs raw zt cs cs LND', f'Rset cs zt {q["rset"]}']
    prev = 'zt'
    for i in range(len(q['zeners'])):
        L.append(f'Dz{i} z{i} {prev} DZ{i}')   # cathode at the higher node
        prev = f'z{i}'
    # zener noise: thermal noise of a resistor sized to give en_z*sqrt(nz), via a VCVS in series
    rn = (q['en_z'] ** 2 * len(q['zeners'])) / (4 * 1.380649e-23 * 300.15)
    L += [f'Enz {prev} 0 nz 0 1', f'Rnz nz 0 {rn:.4g}']
    # filter, gate, pass device, limit
    L += [f'Rf zt gf {q["rf"]}', f'Cf gf 0 {q["cf"]}', f'Rg gf g {q["rg"]}',
          'Ddis gf raw DDIS',   # discharges Cf into the raw rail at power-off
          'Mpass raw g s PASS', 'Dgs s g DGS',
          f'Rs s out {q["rs"]}',
          'Q1 g b out QL', f'R1 s b {q["r1"]}', f'R2 b out {q["r2"]}', f'R3 raw b {q["r3"]}',
          f'Cout out co {q["cout"]}', f'Resr co 0 {q["esr"]}', f'Cfilm out 0 {q["cfilm"]}',
          f'Rbleed out 0 {q["rbleed"]}',
          'Bpm pm 0 V = {V(dr,s)*I(Vid)}']   # M2's own dissipation
    # measure pass device current with a 0 V source in the drain
    drn = f'Rdrn rd dr {q["rdrain"]}' if q['rdrain'] > 0 else 'Vdr rd dr 0'
    L = [x.replace('Mpass raw g s PASS', f'Vid raw rd 0\n{drn}\nMpass dr g s PASS') for x in L]
    if test == 'ac':
        L += [f'Rload out 0 {rload}', '.control', 'op', 'print v(out) v(zt) v(g) v(s) i(Vid)',
              'ac dec 20 1 1meg',
              'wrdata psrr.txt vdb(out)',
              'meas ac p100 FIND vdb(out) AT=100', 'meas ac p1k FIND vdb(out) AT=1k',
              'meas ac p20k FIND vdb(out) AT=20k', 'meas ac p140k FIND vdb(out) AT=140k',
              '.endc', '.end']
    elif test == 'zout':
        L += [f'Rload out 0 {rload}', 'Iac out 0 DC 0 AC 1', '.control', 'ac dec 20 1 1meg',
              'wrdata zout.txt vm(out)',
              'meas ac z100 FIND vm(out) AT=100', 'meas ac z1k FIND vm(out) AT=1k',
              'meas ac z20k FIND vm(out) AT=20k', '.endc', '.end']
    elif test == 'noise':
        L += [f'Rload out 0 {rload}', '.control', 'noise v(out) Vraw dec 20 20 20k', 'setplot noise2',
              'print onoise_total', '.endc', '.end']
    elif test == 'load':
        # DC load regulation and current limit: sweep a load current source
        L += ['Iload out 0 DC 0', '.control', 'dc Iload 0 0.05 0.0005', 'wrdata load.txt v(out)',
              '.endc', '.end']
    elif test == 'line':
        L += [f'Rload out 0 {rload}', '.control', f'dc Vraw 300 450 1', 'wrdata line.txt v(out)', '.endc', '.end']
    elif test == 'startup':
        L += [f'Rload out 0 {rload}', '.options method=gear', '.control', 'tran 1m 20 0 2m',
              'wrdata startup.txt v(out) v(raw) v(pm)',
              'meas tran pmax MAX v(pm)', 'meas tran vfinal FIND v(out) AT=19.9',
              f'meas tran t90 WHEN v(out)={0.9 * vout} RISE=1', '.endc', '.end']
    elif test == 'short':
        L += [f'Rload out 0 {rload}', 'Sshort out 0 ctl 0 SSH', '.model SSH SW(vt=0.5 ron=0.5 roff=1e9)',
              'Vctl ctl 0 PWL(0 0 30 0 30.001 1 40 1 40.001 0)',
              '.options method=gear', '.control', 'tran 2m 60 0 2m',
              'wrdata short.txt v(out) i(Vid) v(pm)',
              'meas tran ishort AVG i(Vid) from=35 to=40', 'meas tran pshort AVG v(pm) from=35 to=40',
              'meas tran ppeak MAX v(pm) from=29 to=41', 'meas tran vrec FIND v(out) AT=59.9',
              'meas tran vbefore FIND v(out) AT=29.9', '.endc', '.end']
    elif test == 'step':
        il = q['iload']
        L += [f'Rload out 0 {rload * 2}',
              f'Istep out 0 PWL(0 0 25 0 25.0001 {il / 2} 26 {il / 2} 26.0001 0)',
              '.options method=gear', '.control', 'tran 0.1m 27 0 0.5m',
              'meas tran vpre FIND v(out) AT=24.99', 'meas tran vmin MIN v(out) from=25 to=26',
              'meas tran vstep FIND v(out) AT=25.99', '.endc', '.end']
    return '\n'.join(L) + '\n'


def run(test, p, workdir):
    with tempfile.NamedTemporaryFile('w', suffix='.cir', delete=False, dir=workdir) as f:
        f.write(netlist(test, p))
        path = f.name
    try:
        r = subprocess.run(['ngspice', '-b', os.path.basename(path)], capture_output=True, text=True,
                           timeout=900, cwd=workdir)
    finally:
        os.unlink(path)
    out = r.stdout + r.stderr
    vals = dict((k.lower(), float(v)) for k, v in re.findall(r'^(\w+)\s*=\s*([-+0-9.eE]+)', out, re.M))
    return vals, out
