#!/usr/bin/env python3
"""Sheet 1 - FX loop driver (PDF page 1): U4 12AT7. Triode 1 (pins 1-3) is the gain stage (anode
load R45 from G, grid from NOLLA via C32, cathode HYPPY2 with R13 / C8), its output goes via C31 to
MVX and R53; triode 2 (pins 6-8) is the cathode follower on F (grid bias R47-R49 / C28, input EQOUT
via R50 / C29) driving SEND through C30. Relay SERIES/MIX connects R26 (to NOLLA) to ground or SEND.

Differences to the PDF drawing (same nets): the two triodes of KiCad's ECC83 symbol are drawn side
by side and the heater unit below them; the relay is one symbol with both poles and the coil, Omron pin
numbers (design fixes 2026-11-20): the Proteus pole is Omron pole 2 (13 / 9 / 11), the unused pole 1
(4 / 6 / 8) carries no-connect flags; turned so that the common contact faces R26."""
from _common import *  # noqa: F401,F403

sh = sheet("01_fx_loop_driver.kicad_sch")

XA, XB, YG = 95, 111, 49    # anode columns of pin 6 / pin 1, grid row
GND = 113                   # PWR-GND row
u1, u2, u3 = noval(sh, "U4", P(XA, YG), P(XB, YG), P(103, 68), mirror_b=True)

# triode 2 (6, 7, 8): anode on F, grid bias, EQOUT input
sh.glabel("F", *P(XA, 20), 90)
sh.wire(P(XA, 20), u1.pin(6))
r48t, r48b = pv(sh, "R48", 73, 40, top=2)
sh.wire(r48t, P(73, 31), P(XA, 31))
sh.junction(*P(XA, 31))
term(sh, "EQOUT", *P(25, YG), "left")
r50l, r50r = ph(sh, "R50", 34, YG, left=2)
c29l, c29r = ph(sh, "C29", 47, YG, left=1)
sh.wire(P(25, YG), r50l)
sh.wire(r50r, c29l)
sh.wire(c29r, u1.pin(7))
r49t, r49b = pv(sh, "R49", 63, 62, top=2)
sh.wire(P(63, YG), r49t)
c28t, c28b = pv(sh, "C28", 63, 88, top="+")
sh.wire(r49b, c28t)
r47t, r47b = pv(sh, "R47", 73, 88, top=2)
sh.wire(r48b, r47t)
sh.wire(P(63, 71), P(73, 71))
junctions(sh, P(63, YG), P(63, 71), P(73, 71))
sh.wire(c28b, P(63, GND))
sh.wire(r47b, P(73, GND))

# cathode 8: R46 to ground, C30 to SEND
sh.wire(u1.pin(8), P(93, 59), P(85, 59), P(85, 98))
r46t, r46b = pv(sh, "R46", 85, 104, top=2)
sh.wire(P(85, 98), r46t)
sh.wire(r46b, P(85, GND))
c30l, c30r = ph(sh, "C30", 99, 98, left=1)
sh.wire(P(85, 98), c30l)
sh.junction(*P(85, 98))

# triode 1 (1, 2, 3): anode load from G, C31 to MVX / R53, grid from NOLLA via C32, R54
sh.glabel("G", *P(XB, 20), 90)
r45t, r45b = pv(sh, "R45", XB, 28, top=2)
sh.wire(P(XB, 20), r45t)
sh.wire(r45b, u2.pin(1))
c31l, c31r = ph(sh, "C31", 125, 39, left=1)
sh.wire(P(XB, 39), c31l)
sh.junction(*P(XB, 39))
XR = 171                    # column of MVX, R53, R26 and the relay's common contact
term(sh, "MVX", *P(XR, 29), "up")
r53t, r53b = pv(sh, "R53", XR, 52, top=2)
sh.wire(P(XR, 29), r53t)
sh.wire(c31r, P(XR, 39))
sh.junction(*P(XR, 39))
r26t, r26b = pv(sh, "R26", XR, 72, top=2)
sh.wire(r53b, r26t)
sh.wire(P(XR, 61), P(179, 61))
sh.glabel("NOLLA", *P(179, 61), 0)
c32l, c32r = ph(sh, "C32", 145, YG, left=1)
sh.wire(u2.pin(2), c32l)
sh.wire(c32r, P(161, YG), P(161, 61), P(XR, 61))
sh.junction(*P(XR, 61))
r54t, r54b = pv(sh, "R54", 137, 66, top=2)
sh.wire(P(137, YG), r54t)
sh.junction(*P(137, YG))
sh.wire(r54b, P(137, GND))

# cathode 3 = HYPPY2 (local label, twice as in the PDF), R13 / C8 to ground
sh.wire(u2.pin(3), P(113, 59), P(121, 59))
sh.label("HYPPY2", *P(121, 59), 0)
c8t, c8b = pv(sh, "C8", 121, 124, top="-")
r13t, r13b = pv(sh, "R13", 133, 124, top=2)
sh.wire(c8t, P(121, GND))
sh.wire(r13t, P(133, GND))
sh.wire(c8b, P(121, 137), P(141, 137))
sh.wire(r13b, P(133, 137))
sh.junction(*P(133, 137))
sh.label("HYPPY2", *P(141, 137), 0)

# relay SERIES/MIX, Omron pin numbers (design fixes 2026-11-20, Finding 15): the used pole is pole 2
# (COM 13, NO 9, NC 11; Proteus 2 / 1 / 3), the coil 16 / 1 (Proteus 4 / 5), pole 1 (4 / 6 / 8) N/C.
# Rotated 180 and placed one column right of XR + 8 so that COM2 sits under R26 and NO2 / NC2 where
# the Proteus pole was drawn; the coil column then holds the coil wires and D1 one column further.
k = sh.place(sym("SERIES_MIX"), "SERIES_MIX", *P(XR + 8, 88), 180, value=sh_value("SERIES_MIX"),
             ref_at=(P(150, 0)[0], P(0, 86)[1], 0, "right"), value_at=(P(150, 0)[0], P(0, 88)[1], 0, "right"))
sh.wire(r26b, k.pin("13"))
sh.wire(c30r, P(169, 98), k.pin("9"))
sh.wire(k.pin("11"), P(173, GND))
for n in ("4", "6", "8"):
    sh.no_connect(*k.pin(n))
d1k, d1a = pv(sh, "D1", 195, 88, top="K")
sh.wire(k.pin("16"), P(187, 80), P(201, 80))
sh.wire(P(195, 80), d1k)
sh.glabel("SWLOOP", *P(201, 80), 0)
sh.wire(k.pin("1"), P(187, 96), P(201, 96))
sh.wire(d1a, P(195, 96))
sh.glabel("PWRH4", *P(201, 96), 0)
junctions(sh, P(195, 80), P(195, 96))
sh.wire(P(115, 98), P(115, 104))
sh.junction(*P(115, 98))
sh.glabel("SEND", *P(115, 104), 270)

# ground row
term(sh, "EQGND", *P(45, GND), "left")
sh.wire(P(45, GND), P(173, GND))
sh.wire(P(85, GND), P(85, 120))
sh.glabel("PWR-GND", *P(85, 120), 270)
junctions(sh, P(63, GND), P(73, GND), P(85, GND), P(121, GND), P(133, GND), P(137, GND))

# heaters
for net, pin, y, ref in (("PWRH4", u3.pin(4), 81, "PRE_H4"), ("PWRH5", u3.pin(5), 87, "PRE_H5")):
    yy = P(0, y)[1]
    sh.glabel(net, *P(95, y), 180)
    term(sh, ref, *P(119, y), "right")
    sh.wire(P(95, y), P(119, y))
    sh.wire(pin, (pin[0], yy))
    sh.junction(pin[0], yy)

sh.text("R47 = 50-100k (Proteus hand note; value 33k)", *P(45, 122))
sh.text("PDF labels 'send' / 'nolla' = nets SEND / NOLLA (Proteus net names are case-insensitive).", *P(45, 145))
sh.text("Terminals PRE-H4 / PRE-H5 = PRE_H4 / PRE_H5; relay SERIES/MIX = SERIES_MIX, Omron pins (Proteus 1-8 = 9 13 11 16 1 4 6 8; pole 1 not connected).", *P(45, 148))
sh.text("U4: KiCad ECC83 symbol in three units (heater U4C below); pin 9 (HCT) is not connected. Value 12AT7.", *P(45, 151))
sh.save()
print("sheet01: written")
