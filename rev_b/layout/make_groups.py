#!/usr/bin/env python3
"""Placement groups and floorplan intent for KiCadRoutingTools' place_simple (PI + FX rev B).

Writes rev_b/layout/groups.json and rev_b/layout/intent.json from the emitted intent (argv[1]) plus
the zones and keep-outs below. Zones are written in the chassis frame and converted to the board
frame (placement.rect_board). Pattern: tube_preamp_kicad rev_b/layout/make_groups.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import placement as P  # noqa: E402


def rng(p, a, b):
    return [f"{p}{i}" for i in range(a, b + 1)]


# name, refs, chassis zone (x0, y0, x1, y1), near, why
G = [
    ("reg_fx", "Q504 R515 D506 D507 R516 R523 R524 C504 R517 D508 Q505 D509 R518 Q506 R519 R520 R521 R525 R526 C505 C506 "
               "R522 R527 R528".split(), (54.0, 104.0, 125.0, 162.0), ["reg_pi"],
     "B+FX regulator (raw from J501): LND150 CCS, zener string, Rf string + 2.2u film, DPAK on its pour, foldback, 47u, bleed"),
    ("reg_pi", "Q501 R501 D501 D502 D503 R502 R509 R510 C501 R503 D504 Q502 D505 R504 Q503 R505 R506 R507 R511 R512 C502 "
               "C503 R508 R513 R514".split(), (120.0, 104.0, 186.0, 143.0), ["reg_fx"],
     "B+PI regulator: as B+FX; its output runs east to the PI's decoupling"),
    ("dec_fx", "R530 C508 R531 C509".split(), (60.0, 140.0, 160.0, 171.0), ["ret", "send"],
     "per-triode RC decoupling of B+FX (V1 plates)"),
    ("send", rng("R", 101, 109) + ["C101", "C102"], (112.0, 140.0, 165.0, 171.0), ["fxio", "mixer"],
     "input network (J101), send cathode follower V1 pins 1-3, SEND_SRC, dry divider"),
    ("fxio", "R131 C103 R110 R111 R112 Q101 R113 R114 C104 C105".split(), (140.0, 140.0, 195.0, 171.0), ["mixer", "send"],
     "return input at J102: bleed, 220n, pad (JFET on PAD_A)"),
    ("mixer", rng("Q", 102, 105) + rng("R", 115, 126) + rng("C", 106, 109), (60.0, 140.0, 170.0, 171.0), ["ret", "fxio", "send"],
     "series-shunt JFET mixer, 220k, the 1k stopper at V1 pin 7"),
    ("ret", "R127 R128 R129 C110 C111 R130".split(), (60.0, 140.0, 125.0, 171.0), ["mixer", "att"],
     "return stage V1 pins 6-8: plate load, cathode, 470n to the attenuator"),
    ("att", rng("K", 201, 205) + rng("R", 202, 212), (140.0, 104.0, 217.0, 171.0), ["fxio", "pi"],
     "PI-4 attenuator: five relays and L-sections, ATT_IN from the return stage to ATT_OUT at the PI"),
    ("pi", "C202 R213 R214 R215 R216 R217 R218 R219 Q201 R220 R221 C203 R222 R223 R224 C204 R529 C507 C201 R201".split(),
     (190.0, 125.0, 266.0, 175.6), ["att", "fb"], "PI: 10n in, grid stoppers, CCS, plate loads, PI_REF, B+PI decoupling, W24 soft tie"),
    ("fb", rng("K", 301, 303) + rng("R", 301, 327) + rng("C", 301, 319) + rng("Q", 301, 309), (175.0, 110.0, 262.0, 145.0),
     ["pi"], "three feedback networks between J302-J304 and the second grid; relays near J301"),
    ("ctl", rng("U", 401, 407) + rng("C", 401, 411) + rng("R", 401, 427), (200.0, 110.0, 278.6, 150.0), ["fb"],
     "DGND island at J401: expander, DG412 x3, LVC1G11 x2, ULN2803A, soft tie"),
]
SMALL = []
TALL = {"C501", "C502", "C504", "C505", "C507", "C508", "C509", "C102", "C111", "C202", "C203", "C503", "C506",
        "C101", "C103"}


def main():
    intent = json.load(open(sys.argv[1]))
    groups = [{"name": n, "role": "core", "refs": r, "near": near, "side": "F", "why": w} for n, r, _z, near, w in G]
    json.dump({"schema": 1, "board": "rev_b/kicad/tube_pi_fxloop_revb.kicad_pcb", "groups": groups},
              open(os.path.join(HERE, "groups.json"), "w"), indent=1)
    intent["blocks"] = [{"name": n, "refs": r, "zone": list(P.rect_board(*z)), "side": "F", "note": w}
                        for n, r, z, _near, w in G]
    allrefs = [r for _, refs, _, _, _ in G for r in refs]
    global SMALL
    SMALL = [r for r in allrefs if r[0] in "RCQD" and r not in TALL and not r.startswith(("Q50", "Q20"))]
    ko = []
    for h, (bx, by) in P.HOLES_BOARD.items():
        if h not in P.HOLE_DROPPED:
            ko.append({"name": f"{h} standoff", "circle": [bx, by, 4.2], "sides": ["F", "B"], "allow": [h],
                       "why": "M3 head and HV clearance to the standoff"})
    for u, (bx, by) in P.SOCKETS_BOARD.items():
        ko.append({"name": f"{u} socket pads", "circle": [bx, by, 13.6], "sides": ["F"], "why": "noval socket pad ring",
                   "allow": SMALL})
    # heater pair along the rear strip (draw_heater.py): both layers
    hx0, hy0, hx1, hy1 = P.rect_board(58.0, 171.0, 236.0, 175.8)
    ko.append({"name": "heater pair", "rect": [hx0, hy0, hx1, hy1], "sides": ["F", "B"], "why": "broadside heater pair"})
    ko.append({"name": "heater J502-J503", "rect": list(P.rect_board(58.0, 158.5, 89.0, 176.0)), "sides": ["F", "B"],
               "allow": ["J503"], "why": "heater pass-through (draw_heater.py)"})
    ko.append({"name": "heater J502 leg", "rect": list(P.rect_board(65.5, 142.0, 69.6, 162.0)), "sides": ["F"],
               "why": "heater pass-through (draw_heater.py)"})
    # ribbon corridors (layout sketch): W13 rises inside x 269.2-278.7, y 107-127; W23 passes under y 166.7-175.7
    ko.append({"name": "W13 corridor", "rect": list(P.rect_board(269.0, 104.0, 278.6, 128.0)), "sides": ["F"],
               "allow": ["J401"], "why": "W13 ribbon rises here (interfaces.md 12.5)"})
    ko.append({"name": "W23 corridor", "rect": list(P.rect_board(160.0, 166.5, 190.0, 175.8)), "sides": ["F"],
               "allow": [r for r in allrefs if r not in TALL], "why": "W23 ribbon at depth 34.6: parts <= 15 mm"})
    # in front of J302-J304: the sockets are entered from the front edge
    ko.append({"name": "front of J302-J304", "rect": list(P.rect_board(192.0, 103.9, 259.0, 105.4)), "sides": ["F"],
               "why": "W30-W32 enter from the front"})
    # regulator F pours (draw_pours.py): only the pass device and its foldback transistor
    for name, refs, r in POURS_F:
        ko.append({"name": name, "rect": list(P.rect_board(*r)), "sides": ["F"], "allow": refs, "why": "BP_RAW drain pour (F)"})
    intent["keepouts"] = ko
    json.dump(intent, open(os.path.join(HERE, "intent.json"), "w"), indent=1)
    print(len(allrefs), "parts in", len(G), "groups")


# F-side drain pours (chassis): DPAK tab + the MMBTA42 in its cut-out (draw_pours.py draws the same)
POURS_F = [("Q505 pour F", ["Q505", "Q506"], P.POUR_F["Q505"]), ("Q502 pour F", ["Q502", "Q503"], P.POUR_F["Q502"])]

if __name__ == "__main__":
    main()
