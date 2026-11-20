"""proteus2kicad configuration of the poweri board (tools in tools/p2k, see its README).

Plain Python; every value here is specific to this board. Coordinates in mm, IPC frame (Y up).
Phase 0 (2026-11-20): sheets, IPC fix-ups, expected counts, layers, drills, outline.
"""

PROJECT = "tube_pi_fxloop"  # KiCad project / library name

# Sources (relative to the repo root). The CADCAM export with Gerber X2 attributes.
CADCAM = "source/cadcam"
IPC = "source/cadcam/pi_fx_loop - CADCAM Netlist.IPC"

# --- Schematic skeleton (make_skeleton) ----------------------------------------------

# (Proteus page, sheet name, file). The 2010 PDF pages have no title block (as on the power
# amp board), so the names describe the page content (STATUS.md "Phase 0", Decisions);
# rename here before make_skeleton if wanted.
SHEETS = [
    (1, "FX loop driver", "01_fx_loop_driver.kicad_sch"),       # U4 12AT7, SERIES/MIX relay, EQOUT/EQGND, MVX
    (2, "PI supply and FX switching", "02_pi_supply_fx_switching.kicad_sch"),  # Q4 IRF820 regulator, Q8/Q10/Q20/Q90, SW1-3, FX
    (3, "Phase inverter", "03_phase_inverter.kicad_sch"),       # U5 12AX7, V6+V7 / V8+V9 outputs, MVW/MV0, FB
    (4, "FX send and return", "04_fx_send_return.kicad_sch"),   # J112 JFET switches Q1-Q3/Q5-Q7, SEND1-3, RETURN1-3, SW4-6
]
SCH_TITLE = "Tube phase inverter and FX loop"
SCH_COMPANY = "Tube amplifier"
SCH_REV = "rev A (as built)"
SCH_COMMENT = "Redrawn from Proteus poweri"
SCH_NOTE = ("Tube phase inverter and FX loop rev A - redrawn from Proteus poweri (2010).\n"
            "One sheet per Proteus PDF page. Net names follow the IPC-D-356A netlist "
            "(reference/pins_by_net.md).")

# --- IPC-D-356A fix-ups (ipc356) -----------------------------------------------------

# Truncated refdes (IPC 6-char field) -> full Proteus refdes, from the schematic PDF.
# RETURN is three terminals (page 4), keyed by their pad coordinate (um): RETURN1 on the
# SW4-2 / R19-1 net, RETURN2 on SW6-2 / R21-1, RETURN3 on SW5-2 / R23-1.
# EQOUT, EQGND, SEND1W..SEND3W, PRE-H4 / PRE-H5 are complete (6 characters or fewer).
TRUNCATED_REFDES = {
    "PIPOWE": "PIPOWER",
    "PIRETU": "PIRETURN",
    "PREPOW": "PREPOWER",
    "PRERET": "PRERETURN",
    "CHASSI": "CHASSIS",
    "SIGNAL": "SIGNALGND",
    "SERIES": "SERIES/MIX",            # G5V-2(HI) relay, 8 pins
    ("RETURN", 0, -57150): "RETURN1",
    ("RETURN", 9525, -57150): "RETURN2",
    ("RETURN", 19050, -57150): "RETURN3",
}
# Expected net per restored refdes. ipc356 looks the key up by the KiCad refdes (p2k
# candidate 2). SERIES_MIX has several nets and is not listed.
TRUNCATED_NETS = {
    "PIPOWER": "#00028",     # Q4-2, R9-1, R66... (PI supply output)
    "PIRETURN": "PWR-GND",
    "PREPOWER": "F",
    "PRERETURN": "PWR-GND",
    "CHASSIS": "PWR-GND",
    "SIGNALGND": "PWR-GND",
    "RETURN1": "#00078",     # SW4-2
    "RETURN2": "#00079",     # SW6-2
    "RETURN3": "#00080",     # SW5-2
}

# Full Proteus refdes -> KiCad refdes (KiCad references: letter first, then letters, digits,
# '_'; no spaces, '+', '-', '.', '/', "'"). Every script that compares against the IPC goes
# through this table (ipc356_pads.json carries it). Convention as tube_psu / the power amp
# pilot: leading + -> P, leading - -> N, other + - / . space -> _, ' -> _PRIME.
KICAD_REFDES = {
    "+6": "P6",
    "-6": "N6",
    "PRE-H4": "PRE_H4",
    "PRE-H5": "PRE_H5",
    "V6+V7": "V6_V7",
    "V8+V9": "V8_V9",
    "C'": "C_PRIME",
    "D'": "D_PRIME",
    "FX'": "FX_PRIME",
    "SERIES/MIX": "SERIES_MIX",
}

# No Proteus power nets (no "=POWER" names). The named nets keep their IPC spelling; the PDF
# writes "send" and "nolla" in lower case (Proteus net names ignore case): IPC "SEND", "NOLLA".
NET_ALIASES = {}

# Blank-refdes records: 4 vias (0.508 mm drill, 1.27 mm pad: #00057, 2x PWR-GND, SWLOOP),
# no free pads; the 10 records without a net are the plated 3.0 mm mounting holes
# (6.35 mm pad on both layers).
VIA_DRILLS = (0.508,)
FREE_PAD_DRILLS = ()
HOLE_DRILLS = (3.0,)
HOLES_PLATED = True

# Expected counts in the Proteus file (PLAN.md section 1).
EXPECTED_IPC = {
    "nets": 66,           # NNAME declarations
    "records": 261,       # 247 component pads + 4 vias + 10 holes
    "refdes_raw": 125,    # 124 distinct refdes fields + the blank one of vias / holes
    "tht_records": 261,
    "smd_records": 0,
    "smd_top": 0,
    "smd_bottom": 0,
    "nc_pads": 5,         # U4-9, U5-9 (heater centre tap), SERIES/MIX 6-8
    "vias": 4,
    "free_pads": 0,
    "holes": 10,
    "parts": 126,         # 87 components + 39 terminals (RETURN -> RETURN1..3)
}

# --- Gerbers (check_sources, later the PCB tools) ------------------------------------

# Proteus copper gerber name -> KiCad copper layer, User layer for the pour outlines
# (there are no pours on this board: no G36 regions, no %LPC%).
COPPER = [
    ("Top Copper", "F.Cu", "User.1"),
    ("Bottom Copper", "B.Cu", "User.2"),
]
DRILL_PLATED = "Drill TOP-BOT Plated"
DRILL_NONPLATED = None    # no NonPlated drill file: the mounting holes are plated
OUTLINE = "Mechanical 1"
OUTLINE_RECT = (-123.825, -78.105, 225.425, 71.755)  # x, y, width, height

# --- Footprints (Phase 2, tools/gen_footprints.py) ------------------------------------

# Pad sizes: "kicad" (KiCad library pad sizes and drills, pad centres on the Proteus positions;
# the IPC-built footprints - noval socket, SW-SPDT, 100n Xicon, Solen, fly-lead terminal - have
# the Proteus pads). Changing it, or Proteus pads / drills per footprint, is a user decision
# (STATUS.md "Phase 2", pad / drill differences; Phase 3 DRC, Phase 4 drill checks).
FOOTPRINT_PAD_SIZES = "kicad"
# Every part of lib/part_map.csv has IPC pads: no off-board parts.
OFF_BOARD_PARTS = {}

# --- PCB (Phase 3, build_pcb) ----------------------------------------------------------

# The 10 IPC 'hole' records: plated 3.0 mm holes with a 6.35 mm pad on both layers, no net.
HOLE_FOOTPRINT = "tube_pi_fxloop:MountingHole_3.0mm_PTH_Pad6.35mm"
HOLE_VALUE = "MountingHole_3.0mm"

# --- Phase 4 checks (p2k.gerber_roundtrip, p2k.ipc356_diff) ---------------------------

# KiCad footprint drills smaller than the Proteus drill, accepted by the user (2026-11-20,
# STATUS.md "Decisions"): the KiCad drills and pads stay. 18 holes (reports/footprint_pads.csv).
DRILL_SMALLER = {
    (1.143, 0.7): "SERIES_MIX (all 8 pads): KiCad G5V-2 land pattern, 0.70 mm drill / 1.4 mm pad kept "
                  "(Proteus 1.143 = 45 mil); user decision 2026-11-20",
    (1.143, 1.0): "C2: KiCad C_Rect 1.0 mm drill kept (Proteus 1.143 = 45 mil); user decision 2026-11-20",
    (0.762, 0.75): "C4 C6 C7 C32: KiCad C_Rect_L7.2mm_W5.0mm_P5.00mm 0.75 mm drill kept (Proteus 0.762 = "
                   "30 mil); user decision 2026-11-20",
}
