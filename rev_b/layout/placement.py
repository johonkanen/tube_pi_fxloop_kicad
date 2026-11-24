"""PI + FX rev B: the one place for the board's mechanical figures, in the chassis frame.

Chassis frame (D748 top plate, interfaces.md 12.1): mm, x along the front from the left, y from the
front panel's inner face to the rear, seen from above; depth = mm below the top plate. The board
hangs 15 mm below the plate (board 15.0-16.6 mm), components down on F.Cu, sockets on B.Cu (the
plate side).

Board frame = rev A's KiCad frame (kicad/tube_pi_fxloop.kicad_pcb at the repo root), so the outline,
the ten holes and the two sockets are rev A's to the micrometre. mechanical/README.md (master repo):
chassis = mirror(board in the Proteus frame) + (154.87, 182.08); with KiCad's y-down board frame that
is a 180 degree turn:

    chassis_x = 154.87 - board_x        chassis_y = 182.08 - board_y

Every connector below is given by its pin 1 in chassis coordinates and its KiCad rotation; the
geometry script (sketch_geom.py) places the real footprint and reports every pin and courtyard
in chassis coordinates. Edit here, re-run sketch_geom.py and sketch_draw.py.
"""

OX, OY = 154.87, 182.08          # chassis = (OX - kx, OY - ky)


def to_board(cx, cy):
    return OX - cx, OY - cy


def to_chassis(kx, ky):
    return OX - kx, OY - ky


# ---- rev A, frozen (board frame) ------------------------------------------------------------
REVA_PCB = "kicad/tube_pi_fxloop.kicad_pcb"                     # repo root, read only
OUTLINE_BOARD = (-123.825, 6.35, 101.6, 78.105)                  # x0, y0, x1, y1 (board frame)
# chassis: x 53.270-278.695, y 103.975-175.730 (225.43 x 71.76)
HOLES_BOARD = {                                                  # rev A H1-H10, drill 3.0 plated in rev A
    "H1": (-119, 11), "H2": (97, 11), "H3": (-63, 14), "H4": (60, 14), "H5": (-94, 18.5),
    "H6": (29, 18.5), "H7": (-69, 41), "H8": (51, 41), "H9": (-119, 73), "H10": (97, 73),
}
HOLE_NO_CHASSIS = {"H1"}          # mechanical/README.md: 9 of 10 match; H1 has no plate hole (nearest 4 mm off)
HOLE_DRILL = 3.2                   # rev B: not plated, no net (grounding.md), M3 clearance
HOLE_KEEPOUT_LV = 3.75             # radius: M3 pan head 5.5 mm + 1 mm
HOLE_KEEPOUT_HV = 5.25             # radius: head + 2.5 mm (the screw / standoff is at chassis potential)
SOCKETS_BOARD = {                                                # rev A U4 / U5, B.Cu, rot 180, Belton PCD 21
    "U4": (45.956, 24.9445), "U5": (-76.5899, 25.2158),
}
SOCKET_FP = ("../lib/tube_pi_fxloop_revb.pretty", "Valve_Noval_Belton_PCD21.00mm")   # copy of rev A's
TUBES = {"U4": "V1 (FX: send follower pins 1-3, return stage pins 6-8)",
         "U5": "V2 (PI; units to be swapped at layout: input grid pin 7 west, second grid pin 2 east)"}

# ---- connectors and tabs leaving the board ---------------------------------------------------
# ref: (cable, mating, lib, footprint, side, kicad_rot, pin1 chassis (x, y), note)
STOCK = "@stock"                                                 # KiCad 10 stock footprint libraries
TABLIB = "../lib/tube_pi_fxloop_revb.pretty"
CONNECTORS = {
    "J102": ("W23", "rear I/O J101", STOCK + "/Connector_IDC.pretty", "IDC-Header_2x08_P2.54mm_Vertical",
             "F", 90, (183.89, 160.50), "long axis x, pin 1 east; moved 8 mm in from the rear edge for the heater pair"),
    "J302": ("W30", "front panel J4", STOCK + "/Connector_IDC.pretty", "IDC-Header_2x05_P2.54mm_Vertical",
             "F", 90, (208.50, 109.00), "CL; long axis x, pin 1 east, ribbon enters from the front"),
    "J303": ("W31", "front panel J5", STOCK + "/Connector_IDC.pretty", "IDC-Header_2x05_P2.54mm_Vertical",
             "F", 90, (230.50, 109.00), "CR"),
    "J304": ("W32", "front panel J6", STOCK + "/Connector_IDC.pretty", "IDC-Header_2x05_P2.54mm_Vertical",
             "F", 90, (252.50, 109.00), "LD"),
    "J401": ("W13", "control board J3", STOCK + "/Connector_IDC.pretty", "IDC-Header_2x07_P2.54mm_Vertical",
             "F", 0, (265.50, 124.84), "long axis y, pin 1 north, odd row east (J3 translated); ribbon from the east"),
    "J101": ("W22", "preamp J507", STOCK + "/Connector_Molex.pretty", "Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
             "F", 0, (136.00, 146.00), "shielded lead from below; 14 mm from V1 pin 2"),
    "J201": ("W24", "power amp J105", STOCK + "/Connector_Molex.pretty", "Molex_Mini-Fit_Jr_5566-06A_2x03_P4.20mm_Vertical",
             "F", 90, (271.50, 150.40), "east edge, harness down and east"),
    "J301": ("W25", "output transformer 8 ohm / COM", STOCK + "/Connector_Molex.pretty", "Molex_KK-396_A-41791-0002_1x02_P3.96mm_Vertical",
             "F", 90, (272.50, 138.46), "east edge, twisted pair from the OT lead hole"),
    "J501": ("W03-b", "HV supplies J103 (RAW_SS)", TABLIB, "Faston_Tab_4.8mm_x2_P15.00mm",
             "F", 90, (64.50, 116.00), "pad 1 BP_RAW, pad 2 GND = the board's star"),
    "J502": ("W07-b", "tube PSU HT tabs (piggy-back lead)", TABLIB, "Faston_Tab_6.3mm_x2_P12.70mm",
             "F", 90, (64.50, 143.50), "heater in, 1.5 A"),
    "J503": ("W08-a", "preamp J502 (x 290 / 303)", TABLIB, "Faston_Tab_6.3mm_x2_P12.70mm",
             "F", 0, (85.50, 169.00), "heater out to the preamp, 0.9 A"),
}

# ---- neighbours (chassis frame) --------------------------------------------------------------
PREAMP = (3.37, 16.18, 386.16, 88.08)          # chassis_view.kicad_pcb User.1
POWER_AMP = (280.33, 127.05, 519.09, 187.375)
CONTROL = (426.0, 30.0, 552.0, 122.0)          # interfaces.md 12.1
REAR_IO_MAIN = [(160, 179.7), (276, 179.7), (276, 195.7), (322, 195.7), (322, 210), (160, 210)]  # plan, 12.1
REAR_IO_JACKS = (191.0, 182.6, 219.0, 197.7)   # jack board tails to y 182.6 (rear I/O L5)
REAR_IO_J101 = {"pins_x": (166.11, 183.89), "pin1": (183.89, 41.23), "rows_depth": (41.23, 43.77),
                "plug_face_y": 179.7, "board_face_y": 197.7, "body_depth": (37.6, 47.4)}
OT_HOLE = (415.5, 90.1)
FRONT_J4_J6 = {"J4": (391.73, 49.08), "J5": (403.73, 49.08), "J6": (415.73, 49.08)}   # pin 1 (x, depth), long axis vertical
FRONT_BACK_FACE_Y = 12.3                        # front panel board's back face; mated sockets to y 29.8
FRONT_SOCKET_Y = 29.8
CONTROL_J3 = {"pin1": (432.28, 98.40), "pin14": (429.74, 83.16), "odd_row": "east"}
PREAMP_J507 = (330.5, 84.0)                     # x 328-333, y 84 (preamp README)
PREAMP_J502 = ((290.0, 81.0), (303.0, 81.0))    # heater tabs
PREAMP_J501 = ((357.0, 81.0), (372.0, 81.0))
HV_J103 = (572.0, 32.0)                          # RAW_SS to the PI + FX, HV supplies front edge
ETHERNET_Y = 96.0                                # shielded patch cable on the chassis floor

# ---- heights (depth below the plate) ---------------------------------------------------------
BOARD_DEPTH = (15.0, 16.6)
TALLEST_PART = 33.0                              # 47 uF / 500 V seated -> depth 49.6
IDC_MATED = 18.0                                 # shrouded header + IDC socket below the board
FLOOR = 82.5

# ---- block zones (chassis rectangles x0, y0, x1, y1) -----------------------------------------
ZONES = [
    ("REG", (54.0, 104.5, 120.0, 140.0), "B+PI / B+FX regulators: DPAK pours >= 6 cm2 each (2 oz, both layers),\nMMBTA42 on each pour, HV strings, 47u x2, 2.2u/630V x2; J501 raw tab = star"),
    ("FX-RET", (67.0, 140.0, 98.0, 166.0), "return stage (V1 pins 6-8),\npad JFET, mixer JFETs"),
    ("FX-SEND", (122.0, 138.0, 158.0, 166.0), "send follower (V1 pins 1-3),\ninput J101, dry divider"),
    ("ATT", (120.0, 104.5, 190.0, 138.0), "PI-4 attenuator: 5x G6K-2F-Y,\nL-sections; RETURN_SIG input"),
    ("FX-IO", (158.0, 138.0, 192.0, 166.0), "J102 W23: send out,\nreturn in, bleeds"),
    ("PI", (192.0, 138.0, 262.0, 176.0), "PI (V2): CCS DN2540, PI_REF 22 V,\nplate loads 2512, B+PI decoupling"),
    ("FB", (192.0, 115.5, 240.0, 138.0), "3 feedback networks, relays at the\n8 ohm end, T-switches at the node"),
    ("DGND", (240.0, 115.5, 279.0, 132.0), "DGND island: MCP23S17, ULN2803A,\nDG412 x3, LVC1G11 x2, soft tie"),
]
HEATER_ROUTE = [(64.5, 156.2), (66.0, 173.0), (233.0, 173.0), (231.5, 167.0)]   # broadside pair along the rear strip
