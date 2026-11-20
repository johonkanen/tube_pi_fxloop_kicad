#!/usr/bin/env python3
"""Sheet 2 - PI supply and FX switching (PDF page 2).
Top: the supply. PIPOWER -> Q4 IRF820 source follower (gate on the zener string D6 / D5 / D4 = 380 V
with R9 and C2, D3 gate clamp) -> H -> R67 -> G -> R66 -> F = PREPOWER, with C1 / C37 / C36.
Bottom right: the 2N3906 drivers Q90 / Q10 / Q20 (inputs: terminals A / D' / C' via R28 / R29 / R27,
collectors = nets A / D' / C' to the JFET gates of sheet 4, pull-ups R270 / R100 / R110 to VREF,
C4 / C6 / C7 to ground) and Q8 (FX' via R25) pulling the three nets through D12 / D11 / D10.
Bottom left: diode OR of SW1-SW3 and FX onto SWLOOP (relay coil, sheet 1).

The terminals A, C', D' are NOT on the nets A, C', D' (Proteus terminals do not name nets): no
label on them. Layout as the PDF; the rows of A / D' / C' are spread a little."""
from _common import *  # noqa: F401,F403

sh = sheet("02_pi_supply_fx_switching.kicad_sch")

RAIL, GND = 15, 63

# --- supply chain F - R66 - G - R67 - H ------------------------------------------------------------
term(sh, "PREPOWER", *P(5, RAIL), "left")
r66l, r66r = ph(sh, "R66", 28, RAIL, left=2)
r67l, r67r = ph(sh, "R67", 44, RAIL, left=1)
sh.wire(P(5, RAIL), r66l)
sh.wire(r66r, r67l)
for net, x, c, yc in (("F", 19, "C36", 27), ("G", 37, "C37", 27), ("H", 51, "C1", 47)):
    sh.glabel(net, *P(x, 6), 90)
    t, b = pv(sh, c, x, yc, top=2)
    sh.wire(P(x, 6), t)
    sh.wire(b, P(x, GND))
    junctions(sh, P(x, RAIL), P(x, GND))

# --- Q4 source follower: gate down, source (3) left on H, drain (2) right on PIPOWER ---------------
qx, qy = P(105, 17)
q4 = sh.place(sym("Q4"), "Q4", qx, qy, 90, mirror="y", value=sh_value("Q4"),
              ref_at=(qx, round(qy - 10.16, 4), 270, None), value_at=(qx, round(qy - 8.255, 4), 270, None))
assert q4.pin(1) == P(105, 21) and q4.pin(2) == P(109, 15) and q4.pin(3) == P(101, 15), q4.pins
sh.wire(r67r, q4.pin(3))
term(sh, "PIPOWER", *P(127, RAIL), "right")
sh.wire(q4.pin(2), P(127, RAIL))
r9t, r9b = pv(sh, "R9", 117, 26, top=2)
sh.wire(P(117, RAIL), r9t)
d3a, d3k = pv(sh, "D3", 91, 26, top="A")
sh.wire(P(91, RAIL), d3a)
junctions(sh, P(91, RAIL), P(117, RAIL))
# gate node #00029: D3 cathode, R9, C2, zener string
sh.wire(d3k, P(91, 35), P(117, 35))
sh.wire(q4.pin(1), P(105, 35))
c2t, c2b = pv(sh, "C2", 105, 47, top=2)
sh.wire(P(105, 35), c2t)
sh.wire(c2b, P(105, GND))
prev = r9b
for ref, y in (("D6", 40), ("D5", 48), ("D4", 56)):
    k, a = pv(sh, ref, 117, y, top="K")
    sh.wire(prev, k)
    prev = a
sh.wire(prev, P(117, GND))
junctions(sh, P(105, 35), P(117, 35))

# --- ground row ---------------------------------------------------------------------------------------
term(sh, "PRERETURN", *P(5, GND), "left")
term(sh, "PIRETURN", *P(139, GND), "right")
sh.wire(P(5, GND), P(139, GND))
sh.wire(P(19, GND), P(19, 70))
sh.glabel("PWR-GND", *P(19, 70), 270)
junctions(sh, P(105, GND), P(117, GND))

# --- gate nets A / D' / C': rows, capacitors to ground, pull-ups to VREF, drivers --------------------
YA, YD, YC = 89, 95, 101
VREF, GND2 = 77, 137
for net, y, x0, x1 in (("A", YA, 66, 147), ("D'", YD, 62, 129), ("C'", YC, 68, 119)):
    sh.glabel(net, *P(x0, y), 180)
    sh.wire(P(x0, y), P(x1, y))
c4t, c4b = pv(sh, "C4", 73, 77, top=1)
sh.wire(c4t, P(73, GND))
sh.wire(c4b, P(73, YA))
c6t, c6b = pv(sh, "C6", 85, 71, top=1)
sh.wire(c6t, P(85, GND))
sh.wire(c6b, P(85, 77), P(89, 77), P(89, YD))
c7t, c7b = pv(sh, "C7", 95, 85, top=1)
sh.wire(c7t, P(95, 75), P(101, 75), P(101, GND))
sh.wire(c7b, P(95, YC))
junctions(sh, P(73, GND), P(85, GND), P(101, GND), P(73, YA), P(89, YD), P(95, YC))

term(sh, "VREF", *P(111, VREF), "left")
sh.wire(P(111, VREF), P(147, VREF))
for r, q, x, yrow, yq, rb, t, yt in (("R270", "Q90", 147, YA, 99, "R28", "A", 95),
                                     ("R100", "Q10", 129, YD, 109, "R29", "D_PRIME", 109),
                                     ("R110", "Q20", 119, YC, 125, "R27", "C_PRIME", 125)):
    rt, rbot = pv(sh, r, x, 84, top=2)
    sh.wire(rt, P(x, VREF))
    tr = q_right(sh, q, x + 2, yq)
    sh.wire(rbot, tr.pin(3))
    sh.junction(*P(x, yrow))
    sh.wire(tr.pin(1), P(x, GND2))
    xr = 136 if q == "Q20" else 162
    l, rr = ph(sh, rb, xr, yt, left=1)
    sh.wire(tr.pin(2), P(x + 8, yq), P(x + 8, yt), l) if yt != yq else sh.wire(tr.pin(2), l)
    term(sh, t, *P(175, yt), "right")          # terminal: no label (not the net of the same name)
    sh.wire(rr, P(175, yt))
junctions(sh, P(119, VREF), P(129, VREF))

# Q8 (FX') pulls A / D' / C' through D12 / D11 / D10
for d, x, yrow in (("D12", 83, YA), ("D10", 95, YC), ("D11", 109, YD)):
    k, a = pv(sh, d, x, 108, top="K")
    sh.wire(k, P(x, yrow))
    sh.wire(a, P(x, 117))
    if d != "D10":
        sh.junction(*P(x, yrow))
sh.wire(P(83, 117), P(109, 117))
q8 = sh.place(sym("Q8"), "Q8", *P(93, 125), 0, value=sh_value("Q8"))
sh.wire(P(95, 117), q8.pin(3))
sh.junction(*P(95, 117))
sh.wire(q8.pin(1), P(95, GND2))
term(sh, "FX_PRIME", *P(55, 125), "left")
r25l, r25r = ph(sh, "R25", 78, 125, left=2)
sh.wire(P(55, 125), r25l)
sh.wire(r25r, q8.pin(2))
sh.glabel("PWR-GND", *P(86, GND2), 180)
sh.wire(P(86, GND2), P(147, GND2))
junctions(sh, P(95, GND2), P(119, GND2), P(129, GND2))

# --- diode OR onto SWLOOP ---------------------------------------------------------------------------------
XB = 15
for y, d, t in ((95, "D2", "SW1"), (107, "D7", "SW2"), (119, "D8", "SW3"), (131, "D9", "FX")):
    diode_input(sh, y, d, t, XB)
sh.wire(P(XB, 95), P(XB, 131), P(9, 131))
sh.glabel("SWLOOP", *P(9, 131), 180)
junctions(sh, P(XB, 107), P(XB, 119), P(XB, 131))

sh.text("Terminals C' = C_PRIME, D' = D_PRIME, FX' = FX_PRIME. The terminals A, C', D' are the driver inputs:", *P(5, 145))
sh.text("they are not on the nets A, C', D' (driver collectors, to the J112 gates on sheet 4).", *P(5, 148))
sh.save()
print("sheet02: written")
