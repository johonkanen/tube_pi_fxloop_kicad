"""All-tube FX loop netlist (simulation plan, section 2c). One 12AX7 (the PI / FX board has two
noval sockets: the PI and the loop).

  preamp out (source, Rsrc) -- 0.47u -- Ra 47k --+-- Rb 10k -- GND            (-15 dB: line level)
                                                +-- 0.1u -- grid of V1a (send cathode follower,
                                                            1M grid leak to the bootstrap node)
  V1a cathode -- 4.7u -- L (line-level send node) -- R2 4.7k -- P (pedal level) -- R3 1.5k -- GND
  send jack: L or P (rear-panel level switch) through 100R.
  dry = P (pedal level, about -27.5 dB from the preamp output).

  return jack -- [line pad -12 dB: 7.5k / 2.5k, 10k input] -- W (pedal-level wet)
  mixer: D=P -- Jd (series NJFET) --+-- Rd 47k --+-- M ;  W -- Jw --+-- Rw 47k --+-- M
                                    Jhd (shunt)                   Jhw (shunt)
         M -- Rm to GND ;  M -- grid of V1b (return gain stage, cathode bypassed)
  Separate RC decoupling (10k / 22u) for each triode from B+FX.
  V1b plate -- 0.1u -- ret (to the automatic attenuator / drive control / PI: 1M || 50p)

Dry and wet both pass through the return stage, so they are always in phase with each other, and
the polarity doesn't change between bypass, series and parallel. Loop modes per channel (control
card): bypass = Jd on, Jw off; series = Jd off, Jw on; parallel = both on.
"""

BFX = 327.8   # B+FX regulator output (docs/preamp_regulator.md)

UNITS = {
    'unity line': dict(gain=1.0, rout=100, delay=0),
    'unity pedal': dict(gain=1.0, rout=1e3, delay=0),
    'invert': dict(gain=-1.0, rout=100, delay=0),
    'delay 1 ms': dict(gain=1.0, rout=100, delay=1e-3),
    'delay 3 ms': dict(gain=1.0, rout=100, delay=3e-3),
    'none': None,
}
SEND_LOADS = {'line': 10e3, 'pedal': 500e3}

NJFET = '.model JSW NJF(vto=-1.5 beta=8m lambda=0.01 cgs=6p cgd=3p is=1e-14)'


def netlist(mode='bypass', level='pedal', unit='unity pedal', tube='12AX7_DZ', rsrc=1e3,
            rm=100e3, src='ac', amp=1.0, ret_src=None, ret_amp=0.0, cable=1e-9):
    jd_on = mode in ('bypass', 'parallel')
    jw_on = mode in ('series', 'parallel')
    u = UNITS[unit]
    L = ['* FX loop', '.include "/home/jari/dev/tube_amplifier_kicad/sim/models/tubes.lib"', NJFET,
         f'Vb bx 0 {BFX}', 'Rbd bx b1 10k', 'Cbd b1 0 22u',     # send stage decoupling
         'Rbd2 bx b2 10k', 'Cbd2 b2 0 22u']                      # return stage decoupling (separate)
    # preamp output source
    if src == 'ac':
        L.append('Vpre pre 0 DC 0 AC 1')
    else:
        L.append(f'Vpre pre 0 SIN(0 {amp} 1k)')
    L += [f'Rsrc pre pre2 {rsrc}', 'Cin pre2 d1 0.47u', 'Ra d1 dd 47k', 'Rb dd 0 10k',
          'Cc2 dd sg 0.1u', 'Rgl sg sb 1Meg',
          f'X1 b1 sg sk {tube}', 'Rk1 sk sb 1.5k', 'Rk2 sb 0 47k',
          'Cs sk nl 4.7u', 'R2 nl np 4.7k', 'R3 np 0 1.5k']
    # send jack
    sel = 'nl' if level == 'line' else 'np'
    L += [f'Rsout {sel} sj 100', f'Ccab sj 0 {cable}', f'Rsl sj 0 {SEND_LOADS[level]}']
    # effects unit: input = send jack, output -> return jack
    if ret_src is not None:
        L.append(f'Vret rj0 0 SIN(0 {ret_amp} 1k)')
        L.append('Rro rj0 rj 100')
    elif u is None:
        L.append('Rnoret rj 0 1')
    elif u['delay'] > 0:
        L += ['Ebuf ua 0 sj 0 1', 'Rt1 ua ub 50', f'T1 ub 0 uc 0 Z0=50 TD={u["delay"]}', 'Rt2 uc 0 50',
              f'Eu ue 0 uc 0 {2 * u["gain"]}', f'Ruo ue rj {u["rout"]}']
    else:
        L += [f'Eu ue 0 sj 0 {u["gain"]}', f'Ruo ue rj {u["rout"]}']
    # return pad
    if level == 'line':
        L += ['Rpad1 rj nw0 7.5k', 'Rpad2 nw0 0 2.5k']
    else:
        L += ['Rpad1 rj nw0 1', 'Rpad2 nw0 0 1Meg']
    # mixer: series-shunt NJFET switches per branch (gate 0 V = on, -15 V = off). When a branch is
    # off, its series JFET is off and its shunt JFET grounds the branch, so every branch always loads
    # M the same way: each path has the same gain alone or in parallel, and isolation improves.
    def branch(tag, src_node, on):
        return [f'Vg{tag} g{tag} 0 {0 if on else -15}', f'Rg{tag} g{tag} g{tag}j 1Meg',
                f'J{tag} {src_node} g{tag}j {tag}mx JSW',
                f'Vh{tag} h{tag} 0 {-15 if on else 0}', f'Rh{tag} h{tag} h{tag}j 1Meg',
                f'Jh{tag} {tag}mx h{tag}j 0 JSW',
                f'R{tag}l {tag}mx 0 1Meg', f'R{tag} {tag}mx m 47k']
    L += branch('d', 'np', jd_on) + branch('w', 'nw0', jw_on) + [f'Rm m 0 {rm}']
    # return gain stage
    L += [f'X2 rp m rk {tube}', 'Rk rk 0 1.5k', 'Ck rk 0 100u', 'Rp b2 rp 100k',
          'Cout rp ret 0.1u', 'Rload ret 0 1Meg', 'Cload ret 0 50p']
    return '\n'.join(L)
