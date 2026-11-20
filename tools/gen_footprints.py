#!/usr/bin/env python3
"""Footprint assignment and the project footprint library of the PI / FX loop board (stdlib only).

Writes (through the shared generator tools/p2k/p2k/footprints.py)
  lib/footprint_map.csv        refdes -> footprint for all 126 parts of lib/part_map.csv
  lib/tube_pi_fxloop.pretty/   project footprints: derived from KiCad library footprints (pads
                               renumbered to the Proteus ids, pad centres moved onto the Proteus
                               positions) or built from the IPC-D-356A pads where KiCad has nothing
  kicad/fp-lib-table           registers the project library (p2k_config.py FP_LIB_TABLE = True)

Usage: python3 tools/gen_footprints.py [--check]      (needs the KiCad AppImage mount)

Adapted from the power amp pilot (~/dev/tube_power_amp_kicad tools/gen_footprints.py): the
shared 2010 packages (RES40, 2 W metal film, 22N XICON, DO41, TO92, C-120-60 terminal, plated
mounting hole) use the same footprint names and specs.

This file holds what is decided for this board: RULES (symbol + IPC pad pattern -> footprint)
and PROJECT (the project footprint specs); the rule syntax and the spec keys are documented in
tools/p2k/p2k/footprints.py. Pad numbers always equal the IPC pin ids.

Pad sizes: p2k_config.py FOOTPRINT_PAD_SIZES = "kicad" (KiCad library pads and drills; the
footprints built from the IPC pads have the Proteus pads). tools/p2k check_footprints verifies
every footprint against the IPC pads (residual < 0.05 mm per pad) and reports the pad size /
drill differences (STATUS.md "Phase 2").
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "p2k"))  # proteus2kicad
from p2k import footprints  # noqa: E402

P = "tube_pi_fxloop:"

# (symbol, conditions, footprint, note). Conditions: n = pad count, tht, span (mm, +-0.02),
# pad = (w, h) of the IPC pads, drill, package / device (lib/part_map.csv columns), refdes.
# One rule per Proteus package (2010 package name in the note).
RULES = [
    # --- resistors
    ("R", dict(package="RES40", span=10.16, pad=(1.778, 1.778), drill=0.762),
     "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", "RES40: 1/4 W axial, P10.16"),
    ("R", dict(package="2W METAL FILM RESISTOR", span=19.05, pad=(2.286, 2.286), drill=1.016),
     P + "R_Axial_DIN0414_L11.9mm_D4.5mm_P19.05mm_Horizontal", "2W METAL FILM RESISTOR: 2 W axial, P19.05"),
    # --- film capacitors
    ("C", dict(package="22N XICON", span=9.70, pad=(2.54, 2.54), drill=1.143),
     P + "C_Rect_L13.0mm_W6.0mm_P9.70mm", "22N XICON: film box 13 x 6 mm, P9.70"),
    ("C", dict(package="47N XICON", span=15.0, pad=(2.54, 2.54), drill=1.143),
     "Capacitor_THT:C_Rect_L18.0mm_W6.0mm_P15.00mm_FKS3_FKP3", "47N XICON: film box 18 x 6 mm, P15.00"),
    ("C", dict(package="100N XICON", span=20.0, pad=(2.54, 2.54), drill=1.143),
     P + "C_Rect_L23.1mm_W6.0mm_P20.00mm", "100N XICON: film box 23.1 x 6 mm, P20.00"),
    ("C", dict(package="MMK J04", span=5.0, pad=(1.778, 1.778), drill=0.762),
     "Capacitor_THT:C_Rect_L7.2mm_W5.0mm_P5.00mm", "MMK J04: film box 7.2 x 5 mm, P5.00"),
    ("C", dict(package="SOLEN 1U", span=30.48, pad=(2.54, 2.54), drill=1.143),
     P + "C_Axial_L26.7mm_D15.2mm_P30.48mm_Horizontal", "SOLEN 1U: axial film 26.7 x 15.2 mm, P30.48"),
    # --- electrolytics
    ("C_Polarized", dict(package="ELEC-RAD10", span=2.54, pad=(2.032, 2.032), drill=0.762),
     P + "CP_Radial_D5.0mm_P2.54mm_PM", "ELEC-RAD10: 5 mm radial electrolytic, P2.54, pads +/-"),
    ("C_Polarized_21", dict(package="ELEC D16 R7.5", span=7.5, pad=(2.54, 2.54), drill=1.143),
     P + "CP_Radial_D16.0mm_P7.50mm_21", "ELEC D16 R7.5: 16 mm radial electrolytic, P7.50, pad 2 = +"),
    # --- diodes
    ("D", dict(package="DO35", span=10.16), P + "D_DO-35_SOD27_P10.16mm_Horizontal_AK", "DO35: pads A/K"),
    ("D", dict(package="DO41", span=10.16), P + "D_DO-41_SOD81_P10.16mm_Horizontal_AK", "DO41: pads A/K"),
    ("D_Zener", dict(package="DO41", span=10.16), P + "D_DO-41_SOD81_P10.16mm_Horizontal_AK", "DO41: pads A/K"),
    # --- transistors
    ("2N3906", dict(package="TO92", span=4.064), P + "TO-92_Inline_P2.03mm", "TO92: inline, 1=E 2=B 3=C, P2.032"),
    ("J112", dict(package="TO92", span=4.064), P + "TO-92_Inline_P2.03mm", "TO92: inline, 1=D 2=S 3=G, P2.032"),
    ("IRF820", dict(package="TO220", span=5.08), "Package_TO_SOT_THT:TO-220-3_Vertical",
     "TO220: vertical, 1=G 2=D 3=S, P2.54"),
    # --- tubes, relay, switches
    ("12AX7", dict(package="9-PIN BELTON NOVAL", n=9, pad=(4.318, 4.318), drill=1.727),
     P + "Valve_Noval_Belton_PCD21.00mm",
     "9-PIN BELTON NOVAL: noval socket, Proteus pads and pin ids, standard noval numbering, bottom side"),
    ("G5V-2", dict(package="G5V-2(HI)", n=8, pad=(2.54, 2.54), drill=1.143),
     "Relay_THT:Relay_DPDT_Omron_G5V-2", "G5V-2(HI): Omron G5V-2, Omron pin numbers (IPC_PIN_IDS)"),
    ("SW_SPDT", dict(package="SPDT HOLES", n=3, pad=(3.048, 3.048), drill=1.524),
     P + "SW_SPDT_3Holes_Proteus", "SPDT HOLES: three solder holes for a wired switch, NO=1 NC=2 COM=3"),
    # --- terminals (fly leads)
    ("PIN", dict(package="C-120-60", n=1, pad=(3.048, 3.048), drill=1.524),
     P + "FlyLead_Pad_D3.048mm_Drill1.524mm", "C-120-60: fly-lead terminal pad"),
]

# Body outlines read from the Proteus Top Assembly gerber (board coordinates, IPC frame, mm) of
# the `ipc` refdes: U4's socket square (26.4 x 25.4 mm) and SW4's rectangle (8.1 x 7.5 mm).
U4_BODY = [(32.734, -37.649), (59.179, -37.649), (59.179, -12.241), (32.734, -12.241)]
SW4_BODY = [(-25.654, -66.929), (-17.526, -66.929), (-17.526, -59.436), (-25.654, -59.436)]

# Relay SERIES_MIX: the Proteus package G5V-2(HI) numbers its pads 1-8 and is the mirror image of the
# Omron G5V-2 seen from the top (STATUS.md Finding 15). Since the design fixes 2026-11-20 (user
# decision) the IPC pin ids of SERIES_MIX are renamed to the physical Omron pins (p2k_config.py
# IPC_PIN_IDS, tools/ipc356.py: Proteus 1-8 = Omron 9 13 11 16 1 4 6 8), so the relay uses KiCad's
# Relay_THT:Relay_DPDT_Omron_G5V-2 unchanged (pads 1.4 / drill 0.7, DRILL_SMALLER). Until then a
# project copy renumbered to the Proteus ids (Relay_DPDT_Omron_G5V-2_Proteus) was used; same copper.

# TO-92 pad 1 (user decision 2026-11-20, option (a); STATUS.md "Phase 3"): KiCad's TO-92 has a
# square 1.5 mm pad 1 whose corners come 0.12 mm close to diagonal Proteus tracks (Q1, Q3, Q6, Q20);
# the Proteus TO92 pads are all round. Pad 1 becomes a circle at the KiCad size 1.5 mm (spec key
# `pads`, which also requires the base pad 1 to be a rect). With three round pads the symmetric TO-92
# outline no longer shows pin 1, so a filled dot is added on F.SilkS and F.Fab beside pad 1 at the
# flat side (outside the body, 0.6 mm off the pad, inside the courtyard): spec key `pin1_dot`
# (x, y in the KiCad frame, Y down, radius in mm).
PIN1_DOT = (-0.45, 1.35, 0.2)   # x, y (KiCad frame, Y down), radius in mm

# Project footprints (spec keys: see p2k.footprints). `ipc` = refdes whose IPC pads give the
# pad centres. All parts are THT and on the top side (Proteus Top Assembly), except the noval
# sockets U4 / U5 (bottom side, user decision 2026-11-20).
PROJECT = {
    # --- shared with the power amp pilot (same names and specs)
    "R_Axial_DIN0414_L11.9mm_D4.5mm_P19.05mm_Horizontal": dict(
        base="Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P20.32mm_Horizontal", ipc="R45",
        descr="2 W axial metal film resistor DIN0414, Proteus pads 19.05 mm apart"),
    # 22n Xicon film: Proteus silk 12.8 x 6.0 mm, pads 9.70 mm apart
    "C_Rect_L13.0mm_W6.0mm_P9.70mm": dict(
        base="Capacitor_THT:C_Rect_L13.0mm_W6.0mm_P10.00mm_FKS3_FKP3_MKS4", ipc="C2",
        descr="Film capacitor box 13 x 6 mm (22n Xicon), Proteus pads 9.70 mm apart"),
    # DO-41 / DO-35: KiCad pad 1 = cathode (band)
    "D_DO-41_SOD81_P10.16mm_Horizontal_AK": dict(
        base="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", renumber={"1": "K", "2": "A"}, ipc="D1",
        descr="DO-41 diode P10.16, pads K (KiCad pad 1, band) / A"),
    "D_DO-35_SOD27_P10.16mm_Horizontal_AK": dict(
        base="Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal", renumber={"1": "K", "2": "A"}, ipc="D2",
        descr="DO-35 diode P10.16, pads K (KiCad pad 1, band) / A"),
    # TO-92 at the Proteus 2.032 mm (80 mil) pitch: KiCad has 1.27 (Inline) and 2.54 (Inline_Wide)
    # pads / pin1_dot: the round TO-92 pad 1 and its silk dot (see PIN1_DOT above)
    "TO-92_Inline_P2.03mm": dict(
        base="Package_TO_SOT_THT:TO-92_Inline_Wide", ipc="Q8",
        pads={"1": dict(shape="circle", expect_shape="rect")}, pin1_dot=PIN1_DOT,
        descr="TO-92 inline, pads 1-3 2.032 mm apart (Proteus TO92)"),
    "FlyLead_Pad_D3.048mm_Drill1.524mm": dict(
        ipc="EQOUT", descr="Fly-lead terminal (Proteus C-120-60): one 3.048 mm pad, drill 1.524"),
    # --- this board
    # 100n Xicon film: Proteus silk 23.1 x 6.0 mm at P20.00 in rows 6.35 mm apart (C5 / C3 / C9).
    # KiCad has no P20.00 box; the nearest (L24 W7 P22.5, L26.5 W6 P22.5) would overlap the
    # neighbouring rows or the board's parts more than Proteus: built from the IPC pads.
    "C_Rect_L23.1mm_W6.0mm_P20.00mm": dict(
        ipc="C5", body=(23.1, 6.0),
        descr="Film capacitor box 23.1 x 6.0 mm (100n Xicon, Proteus 100N XICON), pads 20.00 mm apart"),
    # Solen 1 uF film (axial): Proteus box 26.67 x 15.24 mm, pads 30.48 mm apart; KiCad's axial
    # capacitors stop at D10.5 (P27.5): built from the IPC pads
    "C_Axial_L26.7mm_D15.2mm_P30.48mm_Horizontal": dict(
        ipc="C30", body=(26.67, 15.24),
        descr="Axial film capacitor 26.7 x 15.2 mm (Solen 1 uF, Proteus SOLEN 1U), pads 30.48 mm apart"),
    # electrolytics: KiCad pad 1 (square, '+' silk) = Proteus pin '+' (C8, C28) or pin 2 (C1, C36, C37)
    "CP_Radial_D5.0mm_P2.54mm_PM": dict(
        base="Capacitor_THT:CP_Radial_D5.0mm_P2.50mm", renumber={"1": "+", "2": "-"}, ipc="C8",
        descr="5 mm radial electrolytic, pads + (KiCad pad 1) / -, Proteus pads 2.54 mm apart"),
    "CP_Radial_D16.0mm_P7.50mm_21": dict(
        base="Capacitor_THT:CP_Radial_D16.0mm_P7.50mm", renumber={"1": "2", "2": "1"}, ipc="C1",
        descr="16 mm radial electrolytic P7.50, pads 2 = + (KiCad pad 1) / 1 = - (Proteus ELEC D16 R7.5)"),
    # Noval socket built from the IPC pads: Proteus 9-PIN BELTON NOVAL has a 21.0 mm pitch circle
    # (10 positions 36 deg apart, gap between 9 and 1), 4.318 / 1.727 pads, no centre hole; KiCad
    # Valve:Valve_Noval_P is the standard 11.9 mm-class circle. Pad ids = the IPC pin ids. Body =
    # the Proteus assembly square. The sockets are mounted on the BOTTOM (solder) side (user
    # decision 2026-11-20, STATUS.md Findings 16 / 17, Phase 5): the footprint is built mirrored
    # (`bottom`, board-local key, see build_library below), so in the footprint's own view pins
    # 1 -> 9 run in the standard noval direction (counter-clockwise seen from the component side)
    # and check_footprints places U4 / U5 on B (graphics, courtyard on the B layers; pad positions,
    # drills and nets unchanged). No 3D model (KiCad has no noval socket model).
    "Valve_Noval_Belton_PCD21.00mm": dict(
        ipc="U4", body_poly=U4_BODY, bottom=True,
        descr="Noval tube socket (Proteus 9-PIN BELTON NOVAL), standard noval numbering, mounted on the "
              "solder side: 9 pads 4.318 mm / drill 1.727 on a 21.0 mm pitch circle, pad 9 without a net, "
              "body = the Proteus assembly outline"),
    # SW-SPDT: three solder holes (two 5.08 mm apart, the third 2.54 / 4.445 mm off), for a
    # panel switch wired to the board; KiCad has no such pattern: built from the IPC pads
    "SW_SPDT_3Holes_Proteus": dict(
        ipc="SW4", body_poly=SW4_BODY,
        descr="SPDT switch connection, three 3.048 mm pads / drill 1.524 (Proteus SPDT HOLES): "
              "1 NO, 2 NC, 3 COM; body = the Proteus assembly outline"),
    # Board-only (no symbol; placed by p2k.build_pcb at the 10 IPC 'hole' records)
    "MountingHole_3.0mm_PTH_Pad6.35mm": dict(
        board_only=True, pad=(6.35, 3.0), plated=True,
        descr="Plated 3.0 mm mounting hole with a 6.35 mm pad on both layers, no net"),
}

if __name__ == "__main__":
    sys.exit(footprints.run(RULES, PROJECT))
