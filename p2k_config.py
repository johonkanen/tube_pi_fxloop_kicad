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

# --- ERC (p2k erc; was the board-local tools/erc.sh) ------------------------------------

# ERC warning types that fail: footprint_link_issues (a Footprint field that names a missing library /
# footprint, e.g. without kicad/fp-lib-table: check_footprints does not resolve it, p2k candidate 15) and
# no_connect_connected (a pin with a no-connect flag that is wired: a netlist error, Phase 4).
ERC_FATAL_WARNINGS = {"no_connect_connected", "footprint_link_issues"}

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
    "PIPOWER": "#00028",     # Q4-2 (drain), R9-2 (PI supply input)
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

# Pin ids renamed after parsing the IPC file (p2k ipc356; STATUS.md "Design fixes 2026-11-20", p2k
# candidate 24, was the board-local wrapper tools/ipc356.py). {KiCad refdes: {Proteus
# pin id: KiCad pin id}}; every IPC pad of the refdes must be listed, the targets unique.
# SERIES_MIX (user decision 2026-11-20, Finding 15): the Proteus package G5V-2(HI) numbers the pads
# 1-8 and is the mirror image of the Omron G5V-2 seen from the top; a top-mounted G5V-2 puts Omron
# 9 (NO2) on Proteus pad 1, 13 (COM2) on 2, 11 (NC2) on 3, the coil 16 / 1 on 4 / 5 and pole 1
# (4 COM1, 6 NC1, 8 NO1) on the N/C pads 6-8. With the physical Omron ids the symbol and footprint
# are KiCad's Relay:G5V-2 / Relay_THT:Relay_DPDT_Omron_G5V-2 unchanged; the copper and every net
# stay as built (the used pole is pole 2, the coil is not polarised).
IPC_PIN_IDS = {
    "SERIES_MIX": {"1": "9", "2": "13", "3": "11", "4": "16", "5": "1", "6": "4", "7": "6", "8": "8"},
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
    "nc_pads": 5,         # U4-9, U5-9 (heater centre tap), SERIES/MIX Proteus 6-8 (Omron 4, 6, 8)
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

# --- Footprints (Phase 2, tools/generate/gen_footprints.py, frozen) ------------------------------------

# Pad sizes: "kicad" (KiCad library pad sizes and drills, pad centres on the Proteus positions;
# the IPC-built footprints - noval socket, SW-SPDT, 100n Xicon, Solen, fly-lead terminal - have
# the Proteus pads). Changing it, or Proteus pads / drills per footprint, is a user decision
# (STATUS.md "Phase 2", pad / drill differences; Phase 3 DRC, Phase 4 drill checks).
FOOTPRINT_PAD_SIZES = "kicad"
# Every part of lib/part_map.csv has IPC pads: no off-board parts.
OFF_BOARD_PARTS = {}
# footprints.run also writes / checks kicad/fp-lib-table (the project library, default descr).
FP_LIB_TABLE = True

# --- PCB (Phase 3, build_pcb) ----------------------------------------------------------

# The 10 IPC 'hole' records: plated 3.0 mm holes with a 6.35 mm pad on both layers, no net.
HOLE_FOOTPRINT = "tube_pi_fxloop:MountingHole_3.0mm_PTH_Pad6.35mm"
HOLE_VALUE = "MountingHole_3.0mm"
# Board thickness: 1.6 mm, the 2010 standard; the 2010 fab READ-ME (source/fab_2010) gives no
# stack-up. The 2026 export's READ-ME lists Proteus 8's default 2-layer stack (2 x 0.036 Cu +
# 1.483 FR4 = 1.555 mm, + 2 x 0.01 resist), written when the design was re-saved, not the 2010 order.
PCB_THICKNESS = 1.6
# Design rules from the Proteus copper as built (STATUS.md "Phase 3", measured with the former
# tools/measure_gaps.py = `kipy -m p2k.measure_gaps`), mm.
PCB_RULES = dict(
    min_track=0.5,        # thinnest conductor draw 0.508 (20 mil)
    min_via=1.2,          # the 4 Proteus vias: 1.27 mm pad / 0.508 mm drill
    min_annular=0.1,      # vias 0.381; smallest footprint ring 0.35 (KiCad relay pads 1.4 / 0.7)
    min_drill=0.5,        # smallest drill 0.508 (vias); pads >= 0.70 (KiCad relay)
    clearance=0.4,        # smallest different-net gap 0.421 (pad-track, Q3-1 / PWR-GND); pad-pad and track-track 0.508
    hole_clearance=0.25,  # drill to other-net copper: >= 0.4 gap + annular ring
    hole_to_hole=1.0,     # smallest drill-to-drill 1.270 (Proteus, TO-92), 1.232 with the KiCad 0.8 drills
    edge_clearance=1.0,   # copper to outline >= 1.143
    track=0.508,          # Default netclass
    via=1.27,             # Default netclass = the Proteus vias
    via_drill=0.508,
)
# DRC error types that remain by design (p2k drc; STATUS.md "Phase 3" / "Phase 5", remaining DRC items).
DRC_ACCEPTED = {
    "courtyards_overlap": "KiCad courtyards vs the Proteus placement (40 pairs, parts exactly at the "
                          "Proteus positions, all on the top side): the 100N rows C3/C5/C9 6.35 mm apart; "
                          "the TO-92 rows (Q1/Q2, Q3/Q5, Q6/Q7) with each other and R11 R16 R18, Q20 / "
                          "R270, SEND2W SEND3W; resistors / film caps / terminals packed closer than the "
                          "KiCad courtyards (R19-R24, R66, RETURN1-3, C4 C7 with D9 R50, C30 with R24 "
                          "R26, ...). The noval sockets U4 / U5 are on the bottom side since Phase 5 (user "
                          "2026-11-20): their courtyards (B.CrtYd) no longer meet the top-side parts",
    "pth_inside_courtyard": "Proteus placement: H3 / H4 in the U5 / U4 courtyard (the mounting holes "
                            "around the sockets, Finding 17), C8's pads in U4's, V8_V9 pad 1 in U5's (a "
                            "THT pad is on both sides, so the bottom-side socket courtyards still contain "
                            "them), R24-1 and R26-1 inside the large C30 Solen box courtyard",
}

# The DRC warning counts that must match exactly (p2k drc): no dangling track or via, so a removed stub
# that comes back fails (was the board-local tools/check_no_dangling.py; design fixes 2026-11-20).
DRC_EXPECTED_WARNINGS = {"track_dangling": 0, "via_dangling": 0}

# Recorded copper deviations (p2k.pcb removed_track; user decision 2026-11-20, Finding 19, reverses
# Phase 5 decision 3): the three dangling stubs of the 2010 routing are not built. {(layer, x1, y1,
# x2, y2): reason}, IPC frame (Y up); gerber_to_tracks fails unless every entry matches exactly one
# Conductor draw, gerber_roundtrip drops them from the Proteus copper.
REMOVED_TRACKS = {
    ("B.Cu", 84.455, -42.545, 84.455, -43.815): "SWLOOP stub 1.27 mm at D8-K, lying on the D8-K -> D9-K "
                                                 "track (redundant), free end touches nothing",
    ("F.Cu", -20.0025, -43.18, -19.3675, -43.18): "Net-(Q90-B) stub 0.635 mm from a track junction, free "
                                                   "end touches nothing",
    ("F.Cu", -60.325, -67.945, -58.42, -67.945): "H stub 1.905 mm from R67-2, free end touches nothing",
}

# --- Phase 4 checks (p2k.gerber_roundtrip, p2k.ipc356_diff) ---------------------------

# KiCad footprint drills smaller than the Proteus drill, accepted by the user (2026-11-20,
# STATUS.md "Decisions"): the KiCad drills and pads stay. 18 holes (reports/footprint_pads.csv).
# The pad-set form (reason, pads): both Phase 4 tools require the smaller drills of each pair to be exactly
# these pads (was the board-local tools/check_drill_smaller.py).
DRILL_SMALLER = {
    (1.143, 0.7): ("SERIES_MIX (all 8 pads): KiCad G5V-2 land pattern, 0.70 mm drill / 1.4 mm pad kept "
                   "(Proteus 1.143 = 45 mil); user decision 2026-11-20", {"SERIES_MIX"}),
    (1.143, 1.0): ("C2: KiCad C_Rect 1.0 mm drill kept (Proteus 1.143 = 45 mil); user decision 2026-11-20",
                   {"C2"}),
    (0.762, 0.75): ("C4 C6 C7 C32: KiCad C_Rect_L7.2mm_W5.0mm_P5.00mm 0.75 mm drill kept (Proteus 0.762 = "
                    "30 mil); user decision 2026-11-20", {"C4", "C6", "C7", "C32"}),
}
# The June 2010 fab Excellon drill file (inch, read natively by gerber_roundtrip; decision R1, was converted
# to metric by the board-local tools/excellon_metric.py): cross-checked 1:1 with the 2026 X2 drill gerber.
DRILL_EXCELLON = "source/fab_2010/poweri - CADCAM Drill.TXT"

# --- Pin order (p2k check_pin_order; was tools/check_pin_order.py, STATUS.md "Phase 2 - pin order") ----

# The frozen footprint generator (RULES / PROJECT for spec= / rule= / PIN_ORDER_MAX_MOVE), moved to
# tools/generate/ when generation stopped (2026-11-20); imported, never run.
FOOTPRINT_SCRIPT = "tools/generate/gen_footprints.py"

# The UNMOVED KiCad base footprints with the Proteus renumbering, fitted onto the IPC pads: a small
# residual on the expected side confirms that the Proteus pin ids sit on the pads the renumbering
# says. Inline and two-pad parts fit both ways round: `polarity` (the pin id on the marked base pad 1)
# and the --render overlays decide (reports/pin_order/<refdes>.png, compared by eye in Phase 2).
# Relay SERIES_MIX: its IPC pin ids are the physical Omron pins (IPC_PIN_IDS), so the unmoved KiCad
# G5V-2 must fit unmirrored; the Phase 2 Proteus-pole mapping (Omron pole 1 on the Proteus pole 1-8),
# expressed in today's Omron ids (Omron k -> the Omron id of the Proteus pad that mapping put k on),
# must fit only mirrored (Finding 15: G5V-2(HI) is the mirror image of the Omron G5V-2 seen from the top),
# which also proves that IPC_PIN_IDS is the physical and not the mirrored mapping.
G5V2_POLE1 = {o: IPC_PIN_IDS["SERIES_MIX"][p] for o, p in {"8": "1", "4": "2", "6": "3", "1": "4", "16": "5",
                                                            "13": "6", "11": "7", "9": "8"}.items()}
# Noval sockets U4 / U5: Proteus 9-PIN BELTON NOVAL on a 21.0 mm pitch circle; the standard noval
# (pins 1-9 counter-clockwise seen from the top, 36 deg steps, the gap between 9 and 1) as an ideal
# socket. KiCad Valve:Valve_Noval_P is a smaller circle, so only its mirror state is checked. The noval
# steps are 36 deg: free_angle (no 45 deg snap). Phase 5 (user decision 2026-11-20): the sockets are on
# the BOTTOM side: the project footprint has the standard numbering in its own view and fits the IPC
# pads only mirrored; PIN_ORDER_BOTTOM checks reports/footprint_fit.csv and the board.
_NOVAL = dict(n=9, pcd=21.0, step=36, start=-36, pad=4.318, drill=1.727)
PIN_ORDER = [
    dict(refs="Q4", footprint="Package_TO_SOT_THT:TO-220-3_Vertical", mirror=False, res=0.01),
    # TO-92_Inline_Wide is P2.54, Proteus P2.032: 0.508 at the outer pads
    dict(refs="Q8 Q10 Q20 Q90", spec="TO-92_Inline_P2.03mm", mirror=False, res=0.51, polarity="1"),
    dict(refs="Q1 Q2 Q3 Q5 Q6 Q7", spec="TO-92_Inline_P2.03mm", mirror=False, res=0.51, polarity="1"),
    dict(refs="D2 D7 D8 D9 D10 D11 D12", spec="D_DO-35_SOD27_P10.16mm_Horizontal_AK", mirror=False, res=0.01,
         polarity="K"),
    dict(refs="D1 D3 D4 D5 D6", spec="D_DO-41_SOD81_P10.16mm_Horizontal_AK", mirror=False, res=0.01, polarity="K"),
    dict(refs="C8 C28", spec="CP_Radial_D5.0mm_P2.54mm_PM", mirror=False, res=0.03, polarity="+"),   # P2.50 vs P2.54
    dict(refs="C1 C36 C37", spec="CP_Radial_D16.0mm_P7.50mm_21", mirror=False, res=0.01, polarity="2"),  # + = pin 2
    dict(refs="SERIES_MIX", footprint="Relay_THT:Relay_DPDT_Omron_G5V-2", mirror=False, res=0.01,
         note="Omron ids (IPC_PIN_IDS) on the unmoved KiCad G5V-2"),
    dict(name="SERIES_MIX pole 1", refs="SERIES_MIX", footprint="Relay_THT:Relay_DPDT_Omron_G5V-2",
         renumber=G5V2_POLE1, mirror=True, res=0.01, render=False,
         note="the Phase 2 Proteus-pole mapping fits only mirrored"),
    dict(refs="U4 U5", footprint="Valve:Valve_Noval_P", mirror=True, res=3.0,
         note="KiCad Noval_P is a smaller circle; only the mirrored one is near"),
    dict(name="U4 U5 ideal noval", refs="U4 U5", ideal=_NOVAL, free_angle=True, mirror=True, res=0.01, other=1.0,
         note="ideal standard noval, PCD 21.00 mm"),
    dict(name="U4 U5 sense", refs="U4 U5", turn="clockwise",
         note="noval standard: counter-clockwise from the top"),
    # SW-SPDT (built from the IPC pads, no KiCad base): 1 (NO) and 2 (NC) 5.08 mm apart, 3 (COM) the
    # offset hole 5.12 mm from both
    dict(refs="SW4 SW5 SW6", distances={"1-2": 5.08, "1-3": 5.12, "2-3": 5.12}),
    dict(name="noval footprint vs ideal", footprint="tube_pi_fxloop:Valve_Noval_Belton_PCD21.00mm", on_ideal=_NOVAL,
         free_angle=True, mirror=False, res=0.01, other=1.0, note="standard noval numbering in its own view"),
    dict(name="noval footprint on IPC", refs="U4 U5", footprint="tube_pi_fxloop:Valve_Noval_Belton_PCD21.00mm",
         free_angle=True, mirror=True, res=0.01, other=1.0, note="fits only mirrored = bottom side"),
]
PIN_ORDER_BOTTOM = {"U4", "U5"}
