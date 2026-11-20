#!/usr/bin/env python3
"""Sheet 3 - Phase inverter (PDF page 3): U5 12AX7 long-tail pair. Anode loads R1 / R2 from H to the
outputs V8+V9 / V6+V7, input via MVW / R6 to grid 7, tail R3 / R4 / R8 with the MV0 node, feedback
FB via R7 / C3, second grid via C5 / R5; heaters on PWRH4 (-6) / PWRH5 (+6).

Differences to the PDF drawing (same nets): KiCad's ECC83 symbol is three units, so the two triodes
are drawn side by side (anode columns 16 grid units apart instead of 8) and the heater unit stands
to the right of the tube with the PWRH4 / PWRH5 rows; pin 9 carries a no-connect flag."""
from _common import *  # noqa: F401,F403

sh = sheet("03_phase_inverter.kicad_sch")

XA, XB = 93, 109            # anode columns: pin 6 (R1) and pin 1 (R2)
YG = 61                     # grid row
u1, u2, u3 = noval(sh, "U5", P(XA, YG), P(XB, YG), P(139, 62), mirror_b=True)

# anode loads from H
for ref, x, pin, yout, out in (("R1", XA, u1.pin(6), 35, "V8_V9"), ("R2", XB, u2.pin(1), 49, "V6_V7")):
    t, b = pv(sh, ref, x, 28, top=2)
    sh.wire(t, P(x, 18))
    sh.glabel("H", *P(x, 18), 90)
    sh.wire(b, pin)
    term(sh, out, *P(155, yout), "right")
    sh.wire(P(x, yout), P(155, yout))
    sh.junction(*P(x, yout))

# input: MVW, R6 to grid 7, R15 to the MV0 node
r6l, r6r = ph(sh, "R6", 78, YG, left=1)
sh.wire(r6r, u1.pin(7))
term(sh, "MVW", *P(65, 53), "up")
sh.wire(P(65, 53), P(65, YG), r6l)
r15t, r15b = pv(sh, "R15", 65, 74, top=2)
sh.wire(P(65, YG), r15t)
sh.junction(*P(65, YG))
sh.wire(r15b, P(65, 87), P(81, 87), P(81, 97))

# cathodes 8 + 3 (#00057) and the tail
sh.wire(u1.pin(8), P(91, 73), P(111, 73), u2.pin(3))
r3t, r3b = pv(sh, "R3", 101, 90, top=1)
sh.wire(P(101, 73), r3t)
sh.junction(*P(101, 73))
term(sh, "MV0", *P(71, 97), "left")
r5t, r5b = pv(sh, "R5", 117, 88, top=1)
sh.wire(P(71, 97), P(117, 97), r5b)
sh.wire(r3b, P(101, 97))
r4t, r4b = pv(sh, "R4", 101, 104, top=1)
sh.wire(P(101, 97), r4t)
junctions(sh, P(81, 97), P(101, 97))

# grid 2: R5, C5
sh.wire(u2.pin(2), P(125, YG))
sh.wire(P(117, YG), r5t)
sh.junction(*P(117, YG))
c5t, c5b = pv(sh, "C5", 125, 101, top=2)
sh.wire(P(125, YG), c5t)

# #00062 row: C9, R4, R8, C5, C3
c9t, c9b = pv(sh, "C9", 71, 117, top=2)
c3l, c3r = ph(sh, "C3", 137, 111, left=2)
sh.wire(c9t, P(71, 111), c3l)
sh.wire(r4b, P(101, 111))
sh.wire(c5b, P(125, 111))
r8t, r8b = pv(sh, "R8", 101, 118, top=1)
sh.wire(P(101, 111), r8t)
junctions(sh, P(101, 111), P(125, 111))
r7l, r7r = ph(sh, "R7", 166, 111, left=2)
sh.wire(c3r, r7l)
term(sh, "FB", *P(179, 111), "right")
sh.wire(r7r, P(179, 111))

# ground
r10l, r10r = ph(sh, "R10", 78, 129, left=1)
sh.wire(c9b, P(71, 129), r10l)
sh.wire(r8b, P(101, 135))
sh.wire(r10r, P(101, 129))
sh.glabel("PWR-GND", *P(93, 125), 180)
term(sh, "PGND", *P(127, 125), "right")
sh.wire(P(93, 125), P(127, 125))
term(sh, "SUKKA", *P(89, 135), "left")
term(sh, "CHASSIS", *P(139, 135), "right")
sh.wire(P(89, 135), P(139, 135))
junctions(sh, P(101, 125), P(101, 129), P(101, 135))

# heaters
p4, p5 = u3.pin(4), u3.pin(5)
for net, pin, y, ref, xt in (("PWRH4", p4, 77, "N6", 155), ("PWRH5", p5, 83, "P6", 149)):
    sh.glabel(net, *P(127, y), 180)
    term(sh, ref, *P(xt, y), "right")
    sh.wire(P(127, y), P(xt, y))
    sh.wire(pin, (pin[0], P(0, y)[1]))
    sh.junction(pin[0], P(0, y)[1])

sh.text("Terminal -6 = N6 (PWRH4), +6 = P6 (PWRH5), V8+V9 = V8_V9, V6+V7 = V6_V7.", *P(60, 145))
sh.text("U5: KiCad ECC83 in three units (triodes side by side, heater U5C at the right); pin 9 (HCT) is not connected.", *P(60, 148))
sh.save()
print("sheet03: written")
