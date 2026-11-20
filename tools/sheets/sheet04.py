#!/usr/bin/env python3
"""Sheet 4 - FX send and return (PDF page 4): three send channels (wiper terminal SENDnW - 5k -
J112 shunt - 2k2 - J112 shunt - terminal SENDn; gates on C' / A / D' from the drivers of sheet 2),
the SEND terminal, and three return inputs RETURN1-3 (1M / 100k to NOLLA, SW4-SW6 switch the 1M
out: common on the divider node, NC on the terminal, NO on NOLLA).

Layout as the PDF, with the ground row and the gate rows of channel 2 moved down a little."""
from _common import *  # noqa: F401,F403

sh = sheet("04_fx_send_return.kicad_sch")

GND = 117
send_channel(sh, 25, 65, "R11", "R12", "Q1", "Q2", "C'", ("SEND1W", 11, 55, "up"), ("SEND1", 43, 57, "up"),
             xg=51, yg=91, yl=126, gnd=GND)
send_channel(sh, 73, 91, "R16", "R17", "Q3", "Q5", "A", ("SEND2W", 57, 57, "up"), ("SEND2", 89, 81, "up"),
             xg=105, yg=123, yl=130, gnd=GND)
send_channel(sh, 117, 71, "R18", "R14", "Q6", "Q7", "D'", ("SEND3W", 103, 57, "up"), ("SEND3", 143, 71, "right"),
             xg=145, yg=99, yl=110, gnd=GND)

# ground row
sh.glabel("PWR-GND", *P(9, 108), 90)
sh.wire(P(9, 108), P(9, GND), P(133, GND))
term(sh, "SIGNALGND", *P(19, 127), "down")
sh.wire(P(19, GND), P(19, 127))
junctions(sh, *(P(x, GND) for x in (19, 25, 41, 73, 89, 117)))

# SEND terminal
term(sh, "SEND", *P(103, 27), "up")
sh.wire(P(103, 27), P(103, 43), P(108, 43))
sh.glabel("SEND", *P(108, 43), 0)

# returns
XR, XBUS = 175, 217
for y, ret, r1, sw, r2 in ((25, "RETURN1", "R19", "SW4", "R20"), (47, "RETURN2", "R21", "SW6", "R22"),
                           (69, "RETURN3", "R23", "SW5", "R24")):
    return_block(sh, XR, y, ret, r1, sw, r2, XBUS)
sh.wire(P(XBUS, 13), P(XBUS, 81), P(207, 81))
sh.glabel("NOLLA", *P(207, 81), 180)
junctions(sh, *(P(XBUS, y) for y in (25, 35, 47, 57, 69)))

sh.text("PDF labels 'send' / 'nolla' = nets SEND / NOLLA. Gate nets C', A, D' come from the 2N3906 drivers (sheet 2);", *P(11, 140))
sh.text("the terminals named A, C', D' (sheet 2) are the driver inputs and are not on these nets.", *P(11, 143))
sh.save()
print("sheet04: written")
