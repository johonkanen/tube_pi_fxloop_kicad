"""Rev B FX loop + PI-4 attenuator netlist (PI + FX board), from tube_amplifier_kicad
sim/fx_loop/fx.py (copied here as fx_ref.py) with the rev B changes:

- Input: the preamp rev B output is about 140 kohm (interfaces.md section 10, note 1), so the
  send cathode follower's grid IS the >= 1 Mohm input buffer: J_PRE_IN -> 2.2M to GND (DC
  reference) -> 100n -> 4.7k stopper -> V1a grid, 1M grid leak bootstrapped. No pad in front.
- Send (IF-1.1): CF output -> 4.7u -> 1k -> W23 SEND_SRC -> SEND LEVEL pot 100k log (rear I/O)
  -> wiper -> 1k -> SEND jack -> effects unit input (load + cable).
- Dry: CF output (after the 4.7u) -> Rd1 / Rd2 divider -> P (dry, pedal level) -> mixer.
- Return (IF-1.1): effects unit output -> RETURN LEVEL pot 100k (rear I/O, taper under test) ->
  wiper -> W23 RETURN_SIG -> Cr 220n -> Rp1 (pad series) -> W ; W -> Rp2 -> PAD_A ; the rear pad
  switch closes PAD_A to PAD_B = GND for -20 dB. W -> 1M to GND (defined when unplugged).
- Mixer: series-shunt NJFETs per branch as fx.py, branch resistors Rmx, Rm to GND, V1b grid.
- Return stage V1b: 100k plate, cathode 680R unbypassed + 820R / 100u (rev B: the dry level P is
  6 dB hotter than fx.py's, so the return-jack level for unity is between pedal and line), 0.47u out.
- PI-4 attenuator: five binary L-sections (1, 2, 4, 8, 16 dB) for Z0, terminated by Z0 at the
  PI input; the PI input is 10n + 1M (pi_nfb) here, as a load only.
- Ribbon W23: Ccpl from SEND_SRC to RETURN_SIG (coupling through the G-S-G ribbon).
- Noise: 1.6k resistors in series with each grid as the 12AX7's equivalent noise resistance
  (the tube models are noiseless), as in the preamp simulations.
"""
import math

BFX = 327.8   # B+FX regulator output (docs/preamp_regulator.md)
NJFET = '.model JSW NJF(vto=-1.5 beta=8m lambda=0.01 cgs=6p cgd=3p is=1e-14)'
import os
LIB = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'tubes.lib'))

D = dict(rsrc=140e3, cin_ext=45e-12,           # preamp source; cable (40 pF) + connector / PCB (5 pF)
         rk2=22e3, rd1=47e3, rd2=4.7e3,         # CF cathode R; dry divider
         send_pot=1.0, send_load=10e3, send_cab=300e-12,
         ret_pot=1.0, ret_taper='log', pad=False, rp1=100e3, rp2=11e3,
         rmx=100e3, rm=220e3, rku=680.0, rkb=820.0, z0=49.9e3, att=0, ccpl=0.0, pre_cap=5e-12,
         unit_gain=1.0, unit_rout=100.0)
ATT = (1, 2, 4, 8, 16)


def taper(x, kind):
    if kind == 'log':
        return (81.0 ** x - 1.0) / 80.0
    if kind == 'rlog':
        return 1.0 - (81.0 ** (1.0 - x) - 1.0) / 80.0
    return x


def pot(name, top, wiper, bot, total, x, kind):
    a = min(max(taper(x, kind), 1e-5), 1 - 1e-5)
    return [f'R{name}t {top} {wiper} {total * (1 - a)}', f'R{name}b {wiper} {bot} {total * a}']


def lpad(db, z0):
    a = 10 ** (-db / 20.0)
    return z0 * (1 - a), z0 * a / (1 - a)


def netlist(mode='bypass', src='ac', amp=1.0, ret_src=None, ret_amp=0.0, tube='12AX7_DZ', **kw):
    p = dict(D, **kw)
    jd_on = mode in ('bypass', 'parallel')
    jw_on = mode in ('series', 'parallel')
    L = ['* rev B FX loop', f'.include "{LIB}"', NJFET,
         f'Vb bx 0 {BFX}', 'Rbd bx b1 10k', 'Cbd b1 0 22u', 'Rbd2 bx b2 10k', 'Cbd2 b2 0 22u']
    L.append('Vpre pre 0 DC 0 AC 1' if src == 'ac' else
             ('Vpre pre 0 DC 0' if src == 'off' else f'Vpre pre 0 SIN(0 {amp} 1k)'))
    # preamp output (Thevenin) and the input network
    L += [f'Rsrc pre inp {p["rsrc"]}', f'Ccab inp 0 {p["cin_ext"]}', 'Rin inp 0 2.2Meg',
          'Cin inp ci 100n', 'Rstp ci gx 4.7k', 'Rn1 gx sg 1.6k',
          'Rgl gx sb 1Meg', f'X1 b1 sg sk {tube}', 'Rk1 sk sb 1.5k', f'Rk2 sb 0 {p["rk2"]}',
          'Cs sk cfo 4.7u', 'Rcfo cfo 0 1Meg']
    # send: 1k -> SEND_SRC -> pot (rear) -> 1k -> jack
    L += ['Rsend cfo ssrc 1k'] + pot('sp', 'ssrc', 'sw', '0', 100e3, p['send_pot'], 'log')
    L += ['Rsj sw sj 1k', f'Csj sj 0 {p["send_cab"]}', f'Rsl sj 0 {p["send_load"]}']
    # dry tap
    L += [f'Rd1 cfo np {p["rd1"]}', f'Rd2 np 0 {p["rd2"]}']
    # effects unit / return source
    if ret_src is not None:
        L += [f'Vret rj0 0 SIN(0 {ret_amp} 1k)' if ret_src == 'sin' else 'Vret rj0 0 DC 0 AC 1', 'Rro rj0 rj 100']
    elif ret_src is None and mode == 'bypass' and p.get('noret'):
        L += ['Rnoret rj 0 100']
    else:
        L += [f'Eu ue 0 sj 0 {p["unit_gain"]}', f'Ruo ue rj {p["unit_rout"]}']
    L += pot('rp', 'rj', 'rsig', '0', 100e3, p['ret_pot'], p['ret_taper'])
    if p['ccpl']:
        L.append(f'Ccpl ssrc rsig {p["ccpl"]}')
    L += ['Crsig rsig 0 20p',                         # ribbon conductor to its neighbours (grounds)
          'Cr rsig rc 220n', f'Rp1 rc nw {p["rp1"]}', 'Rnwl nw 0 1Meg', 'Cw nw 0 5p']
    if p['pad']:
        L.append(f'Rp2 nw 0 {p["rp2"]}')

    def branch(tag, src_node, on):
        # series JFET: 100k / 10n edge filter, then 1M to the gate, so the gate floats with the
        # channel (a gate held at AC ground by the 10n forward-biases on the negative peaks)
        return [f'Vg{tag} g{tag} 0 {0 if on else -15}', f'Rg{tag} g{tag} g{tag}c 100k', f'Cg{tag} g{tag}c 0 10n',
                f'Rgg{tag} g{tag}c g{tag}j 1Meg',
                f'J{tag} {src_node} g{tag}j {tag}mx JSW',
                f'Vh{tag} h{tag} 0 {-15 if on else 0}', f'Rh{tag} h{tag} h{tag}j 100k', f'Ch{tag} h{tag}j 0 10n',
                f'Jh{tag} {tag}mx h{tag}j 0 JSW', f'R{tag}l {tag}mx 0 1Meg', f'R{tag} {tag}mx m {p["rmx"]}']
    L += branch('d', 'np', jd_on) + branch('w', 'nw', jw_on) + [f'Rm m 0 {p["rm"]}']
    L += ['Rn2 m mg 1.6k', f'X2 rp mg rk {tube}', f'Rku rk rkb {p["rku"]}', f'Rkb rkb 0 {p["rkb"]}', 'Ck rkb 0 100u', 'Rp b2 rp 100k',
          'Cout rp a0 0.47u', 'Rbl a0 0 1Meg']
    # PI-4 attenuator: L-sections, a section is in when its bit is set
    node = 'a0'
    for i, db in enumerate(ATT):
        nxt = f'a{i + 1}'
        rs, rp_ = lpad(db, p['z0'])
        if p['att'] & (1 << i):
            L += [f'Ras{i} {node} {nxt} {rs:.1f}', f'Rap{i} {nxt} 0 {rp_:.1f}']
        else:
            L += [f'Ras{i} {node} {nxt} 0.05']
        node = nxt
    L += [f'Rz0 {node} 0 {p["z0"]}', f'Cpi {node} pig 10n', 'Rpig pig 0 1Meg', 'Cpig pig 0 5p']
    L.append(f'.options method=gear reltol=1e-4')
    return '\n'.join(L), node
