#!/usr/bin/env python3
"""Draw the five PI + FX loop rev B sheets (second-pass draft, 2026-11-23, interfaces.md IF-1.2).

Sources (tube_amplifier_kicad, read only, and this repo's rev_b/sim):
- PI and feedback: sim/pi_nfb (12AX7 LTP, ~2 mA CCS tail, equal 100k plates, feedback into the
  second grid; input 10n, second grid 22n; per-channel network Rf 100k || 22p, Cres 22n || 250k
  log pot, presence 1k + 50k rev-log + 22n, Rbot 4.7k); rev_b/sim/pi_nfb/run_open_load.py.
- FX loop: sim/fx_loop re-derived for rev B in rev_b/sim/fx_loop (fx_revb.py, run_fx_revb.py):
  the send cathode follower's grid is the >= 1 Mohm input buffer on the 140 kohm preamp output,
  rear send / return pots and the 0 / -20 dB pad (IF-1.1), JFET series-shunt mixer, return stage.
- PI-4 attenuator: five binary L-sections (1, 2, 4, 8, 16 dB, Z0 49.9k) on G6K-2 relays.
- Regulators: docs/preamp_regulator.md, rev B reference (STD4N80K5 DPAK, MMBTA42 on its pour =
  thermal foldback; no drain resistor on B+PI / B+FX); B+PI about 390 V, B+FX about 330 V. The raw
  feed has no fuse (interfaces.md 4.2, 8).
- Relays: Omron G6K-2F-Y 5 V (21.1 mA): coil + 1, - 8; pole 1 COM 3, NC 4, NO 2; pole 2 COM 6,
  NC 5, NO 7. Every function is on a NO contact; unpowered = 0 dB, no feedback network.
- Interfaces: docs/interfaces.md IF-1.2 (connector pinouts as the contract; W23 per section 10.1).

Footprints: every part gets one (KiCad stock libraries; the power tabs are local PLACEHOLDER
footprints, lib/tube_pi_fxloop_revb.pretty). draw_all.py writes lib/footprint_map.csv (read by
p2k's sch_builder) and bom/bom.csv (refs, value, footprint, candidate part).

Netlist-first drawing, as tube_preamp_kicad rev_b: every part on a grid, a wire stub and a label
on every pin (local label on one sheet, global label across sheets, power symbol for GND / GNDD /
+5V / +15V / -15V). GND = AGND (audio ground, the board's one solid ground: W03 return);
GNDD = the DGND island at the control ribbon, joined to GND by one soft tie (10R || 100n,
docs/grounding.md). Run from anywhere: python3 rev_b/tools/sheets/draw_all.py
Writes build/intended_nets.json (what was meant), checked against KiCad's netlist by verify.py.

Tube units (KiCad ECC83): unit 2 = pins 1/2/3, unit 1 = pins 6/7/8, unit 3 = heater 4/5/9.
  V1 (FX loop): unit 2 = send cathode follower, unit 1 = return stage
  V2 (PI):      unit 2 = input triode (grid 2), unit 1 = feedback triode (grid 7)
"""
import json
import math
import os
import sys

RB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("P2K_BOARD", RB)
sys.path.insert(0, os.path.join(RB, "..", "tools", "p2k"))
import p2k.sch_builder as sb  # noqa: E402
from p2k.sch_builder import Sheet, lib  # noqa: E402
from p2k.sexpr import find, find_all  # noqa: E402

POWER = {"GND", "GNDD", "+5V", "+15V", "-15V"}
GRID = 2.54
INTENDED = {}          # (ref, pin) -> net
PARTS = {}             # ref -> (symbol, value, footprint key or full name)

# Footprint keys (KiCad 10 stock libraries unless marked PLACEHOLDER). Package rules: 0603 logic and
# gate drive; 0805 low-voltage audio; 1206 where a node sits at 100-430 V (creepage) or for > 0.1 W;
# 2512 (200 V, 1 W) for plate loads and every resistor string across HV (no SMD resistor over 200 V);
# C0G for audio capacitors; film (THT) where an audio cap sees DC above 50 V.
FP = {
    "R0603": "Resistor_SMD:R_0603_1608Metric", "R0805": "Resistor_SMD:R_0805_2012Metric",
    "R1206": "Resistor_SMD:R_1206_3216Metric", "R2512": "Resistor_SMD:R_2512_6332Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric", "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "FILM5": "Capacitor_THT:C_Rect_L7.2mm_W4.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2",
    "FILM10": "Capacitor_THT:C_Rect_L13.0mm_W5.0mm_P10.00mm_FKS3_FKP3_MKS4",
    "FILM15": "Capacitor_THT:C_Rect_L18.0mm_W8.0mm_P15.00mm_FKS3_FKP3",
    "FILM27": "Capacitor_THT:C_Rect_L31.5mm_W17.0mm_P27.50mm_MKS4",
    "CPD8": "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", "CPD12": "Capacitor_THT:CP_Radial_D12.5mm_P5.00mm",
    "CPD16": "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm", "CPD18": "Capacitor_THT:CP_Radial_D18.0mm_P7.50mm", "CPE6": "Capacitor_SMD:CP_Elec_6.3x7.7",
    "CPE5": "Capacitor_SMD:CP_Elec_5x5.4",
    "SMA": "Diode_SMD:D_SMA", "SOD123": "Diode_SMD:D_SOD-123",
    "DPAK": "Package_TO_SOT_SMD:TO-252-2", "SOT89": "Package_TO_SOT_SMD:SOT-89-3",
    "SOT23": "Package_TO_SOT_SMD:SOT-23", "SOT23-6": "Package_TO_SOT_SMD:SOT-23-6",
    "SOIC18W": "Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm",
    "IDC2x5": "Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical",
    "IDC2x7": "Connector_IDC:IDC-Header_2x07_P2.54mm_Vertical",
    "IDC2x8": "Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical",
    "KK254x3": "Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
    "KK396x2": "Connector_Molex:Molex_KK-396_A-41791-0002_1x02_P3.96mm_Vertical",
    "MFJ2x3": "Connector_Molex:Molex_Mini-Fit_Jr_5566-06A_2x03_P4.20mm_Vertical",
    "TAB48": "tube_pi_fxloop_revb:PLACEHOLDER_Tab_x2_4.8mm_Legs_P5.00mm_D1.4mm",
    "TAB63": "tube_pi_fxloop_revb:PLACEHOLDER_Tab_x2_6.3mm_Legs_P5.00mm_D1.4mm",
}


def g(v):
    return round(round(v / 1.27) * 1.27, 2)


def at(c, r):
    return g(30.48 + c * 20.32), g(35.56 + r * 17.78)


class Drawer:
    def __init__(self, fname, mode, globals_=frozenset()):
        self.fname, self.mode, self.globals = fname, mode, globals_
        self.nets = set()
        self.sheet_no = int(fname[:2])
        self.count = {}
        self.refmap = {}
        self.sh = Sheet(os.path.join(RB, "kicad", fname)).clear() if mode == "draw" else None
        if self.sh is not None:
            self.sh.pwr = self.sheet_no * 100

    def auto_ref(self, ref, sym):
        if ref.startswith(("V", "#")):
            return ref
        multi = sym in ("DG412xY", "ECC83")
        if multi and ref in self.refmap:
            return self.refmap[ref]
        pre = ref[0]
        self.count[pre] = self.count.get(pre, 0) + 1
        new = f"{pre}{self.sheet_no * 100 + self.count[pre]}"
        self.refmap[ref] = new
        return new

    def part(self, sym, ref, c, r, nets, value=None, rot=0, unit=1, stub=GRID, fp=None):
        ref = self.auto_ref(ref, sym)
        if not ref.startswith("#") and (ref not in PARTS or fp):
            PARTS[ref] = (sym, value, fp if fp else (PARTS.get(ref, (0, 0, None))[2]))
        for n in nets.values():
            if n and n != "NC":
                self.nets.add(n)
        if self.mode != "draw":
            return ref
        for pin, net in nets.items():
            if net and net != "NC" and not ref.startswith("#"):
                INTENDED[(ref, str(pin))] = net
        x, y = at(c, r)
        p = self.sh.place(sym, ref, x, y, rot=rot, unit=unit, value=value)
        dirs = {}
        for sub in find_all(lib()[sym], "symbol"):
            u = int(sub[1].rsplit("_", 2)[-2])
            if u not in (0, unit):
                continue
            for pn in find_all(sub, "pin"):
                dirs[str(find(pn, "number")[1])] = float(find(pn, "at")[3])
        for pin, net in nets.items():
            if not net:
                continue
            x0, y0 = p.pin(pin)
            if net == "NC":
                self.sh.no_connect(x0, y0)
                continue
            out = (dirs[str(pin)] + 180 + rot) % 360
            a = math.radians(out)
            x1, y1 = g(x0 + math.cos(a) * stub), g(y0 - math.sin(a) * stub)
            self.sh.wire((x0, y0), (x1, y1))
            lrot = int(round(out / 90.0)) * 90 % 360
            if net in POWER:
                self.sh.power(net, x1, y1, rot=0)
            elif net in self.globals:
                self.sh.glabel(net, x1, y1, rot=lrot)
            else:
                self.sh.label(net, x1, y1, rot=lrot)
        return ref

    def text(self, s, c, r, size=1.27):
        if self.mode == "draw":
            self.sh.text(s, *at(c, r), size=size)

    def save(self):
        if self.mode == "draw":
            self.sh.save()


# ------------------------------------------------------------------ helpers
def R(d, c, r, a, b, v, rot=90, fp=None):
    return d.part("R", "R", c, r, {1: a, 2: b}, value=v, rot=rot, fp=fp or ("R0603" if d.sheet_no == 4 else "R0805"))


def C(d, c, r, a, b, v, rot=90, fp=None):
    return d.part("C", "C", c, r, {1: a, 2: b}, value=v, rot=rot, fp=fp or "C0603")


def CP(d, c, r, plus, minus, v, rot=0, fp=None):
    return d.part("C_Polarized", "C", c, r, {1: plus, 2: minus}, value=v, rot=rot, fp=fp)


def softtie(d, c, r, a, b, note):
    """Soft tie (docs/grounding.md): 10R || 100n."""
    R(d, c, r, a, b, "10R", fp="R0603")
    C(d, c + 1, r, a, b, "100n")
    d.text(note, c, r - 0.6)


def jfet_series(d, c, r, a, b, drv, tag):
    """Series NJFET (MMBFJ113, on = gate 0 V, off = -15 V). Edge filter 100k / 10n, then 1M to
    the gate so the gate floats with the channel when on (rev_b/sim/fx_loop: a gate held at AC
    ground by the 10n forward-biases on the negative peaks and distorts)."""
    d.part("MMBFJ113", "Q", c, r, {1: a, 2: b, 3: f"GJ_{tag}"}, value="MMBFJ113")
    R(d, c - 1, r - 0.5, drv, f"GC_{tag}", "100k", rot=0, fp="R0603")
    C(d, c - 1, r + 0.6, f"GC_{tag}", "GND", "10n", rot=270)
    R(d, c - 0.2, r + 1.2, f"GC_{tag}", f"GJ_{tag}", "1M", fp="R0603")


def jfet_shunt(d, c, r, a, drv, tag):
    """Shunt NJFET to GND (on = gate 0 V through 100k / 10n)."""
    d.part("MMBFJ113", "Q", c, r, {1: a, 2: "GND", 3: f"GJ_{tag}"}, value="MMBFJ113")
    R(d, c - 1, r - 0.5, drv, f"GJ_{tag}", "100k", rot=0, fp="R0603")
    C(d, c - 1, r + 0.6, f"GJ_{tag}", "GND", "10n", rot=270)


def relay(d, c, r, drive, poles):
    """Omron G6K-2F-Y, 5 V coil (decided 2026-11-22, shared with the preamp; 21.1 mA, 237 ohm).
    Datasheet, top view: coil + 1 (to +5V), - 8 (to the ULN2803A sink); pole 1 COM 3, NC 4, NO 2;
    pole 2 COM 6, NC 5, NO 7. The first pass had NO / NC swapped (read from KiCad's G6K-2 drawing);
    the local G6K-2F-Y symbol is redrawn to the datasheet. Every function uses the NO contacts, so an
    unpowered relay is the safe state (attenuator section out = 0 dB; feedback network open)."""
    nets = {1: "+5V", 8: drive}
    for p in (2, 3, 4, 5, 6, 7):
        nets[p] = poles.get(p, "NC")
    return d.part("G6K-2F-Y", "K", c, r, nets, value="G6K-2F-Y 5VDC")


# ------------------------------------------------------------------ sheet 01
def sheet01(d):
    d.text("01 FX loop (one 12AX7, V1). The send cathode follower's grid is the >= 1 Mohm input buffer on the 140 kohm "
           "preamp output (interfaces.md note 1); dry and wet both pass the return stage (FX-1). Values: rev_b/sim/fx_loop "
           "(fx_revb.py).", 0, -1.0, 2)
    # INTERFACE: J101 = W22-b (mirror of preamp J507: 1 OUT, 2 GND, 3 GND / shield; solid at this receiving end)
    d.part("Conn_01x03", "J", 0, 1, {1: "PRE_IN", 2: "GND", 3: "GND"}, value="PRE IN (W22-b)", fp="KK254x3")
    # INTERFACE: J102 = W23-a, IF-1.2 pinout (interfaces.md 10.1, 2026-11-22): 2x8, odd pins GND, no power;
    # 2 SEND_SRC, 4 GND, 6 RSVD1, 8 PAD_A, 10 PAD_B (= GND), 12 RSVD2, 14 GND, 16 RETURN_SIG.
    d.part("Conn_02x08_Odd_Even", "J", 0, 7, {1: "GND", 2: "SEND_SRC", 3: "GND", 4: "GND", 5: "GND", 6: "NC",
                                              7: "GND", 8: "PAD_A", 9: "GND", 10: "GND", 11: "GND", 12: "NC",
                                              13: "GND", 14: "GND", 15: "GND", 16: "RETURN_SIG"}, value="FX (W23-a)",
           fp="IDC2x8")
    d.text("J102 (IF-1.2): 2 SEND_SRC, 8 PAD_A, 10 PAD_B = GND (the rear switch grounds PAD_A), 16 RETURN_SIG "
           "(far end from SEND_SRC, 2.2M bleed here); 6 / 12 RSVD1 / RSVD2 not connected. Place at the rear edge, x 170-190 "
           "(the rear I/O jack board stands behind x 191-219).", 0, 9.3)
    # input network and send cathode follower (V1 pins 1-3)
    R(d, 1.5, 2.2, "PRE_IN", "GND", "2.2M")
    C(d, 2.5, 1, "PRE_IN", "CI", "100n/250V film", rot=0, fp="FILM5")
    R(d, 3.5, 1, "CI", "G1A", "4.7k", rot=0)
    R(d, 4.5, 2.2, "G1A", "SB", "1M")
    d.part("ECC83", "V1", 6, 1, {1: "BFX1", 2: "G1A", 3: "K1A"}, value="12AX7", unit=2)
    R(d, 6, 3, "K1A", "SB", "1.5k")
    R(d, 6, 4.5, "SB", "GND", "22k 0.5W", fp="R1206")
    CP(d, 7.5, 2.2, "K1A", "CFO", "4.7u/160V", fp="CPD8")
    R(d, 8.5, 3, "CFO", "GND", "1M")
    R(d, 9, 1, "CFO", "SEND_SRC", "1k", rot=0)
    R(d, 9, 4.5, "CFO", "NP", "47k", rot=0)
    R(d, 10, 5.7, "NP", "GND", "4.7k")
    d.text("SEND_SRC: full preamp level (-2 dB) to the SEND LEVEL pot on the rear I/O board", 8.5, 0.3)
    # return input and the pad (resistors here, switch contact on the ribbon)
    C(d, 2.5, 7, "RETURN_SIG", "RC", "220n/100V film", rot=0, fp="FILM5")
    R(d, 3.5, 7, "RC", "NW", "100k", rot=0)
    R(d, 4.5, 8.2, "NW", "GND", "1M")
    R(d, 5.5, 8.2, "NW", "PD", "11k")
    d.part("MMBFJ113", "Q", 5.8, 9.8, {1: "PD", 2: "GND", 3: "G_PAD"}, value="MMBFJ113")
    R(d, 3, 10.5, "PAD_A", "-15V", "1M")
    C(d, 2, 10.5, "PAD_A", "GND", "100n")
    R(d, 4, 9.6, "PAD_A", "G_PAD", "100k", rot=0)
    C(d, 4.2, 11, "G_PAD", "GND", "10n")
    d.text("Pad (IF-1.2): rear switch open (or W23 unplugged) = PAD_A at -15 V = JFET off = 0 dB; closed = PAD_A at GND "
           "= JFET on = 11k shunt = -20 dB. Only the DC line PAD_A crosses the ribbon; 1M to -15 V and 100n at J102.", 2, 12.2)
    # mixer: series-shunt JFETs per branch (sim/fx_loop Q11), 100k branch resistors, 220k to GND
    jfet_series(d, 13, 2, "NP", "DMX", "JDRV_DS", "DS")
    jfet_shunt(d, 15, 3.5, "DMX", "JDRV_DH", "DH")
    R(d, 16, 4.8, "DMX", "GND", "1M")
    R(d, 17, 2, "DMX", "M", "100k", rot=0)
    jfet_series(d, 13, 7, "NW", "WMX", "JDRV_WS", "WS")
    jfet_shunt(d, 15, 8.5, "WMX", "JDRV_WH", "WH")
    R(d, 16, 9.8, "WMX", "GND", "1M")
    R(d, 17, 7, "WMX", "M", "100k", rot=0)
    d.text("Dry branch (bypass, parallel)", 12, 0.6)
    d.text("Wet branch (series, parallel)", 12, 5.6)
    R(d, 18.5, 5.2, "M", "GND", "220k")
    # return stage (V1 pins 6-8)
    R(d, 19.5, 4, "M", "G1B", "1k", rot=0)
    d.part("ECC83", "V1", 21, 4, {6: "P1B", 7: "G1B", 8: "K1B"}, value="12AX7", unit=1)
    R(d, 21, 2.5, "BFX2", "P1B", "100k", fp="R2512")
    R(d, 21, 6, "K1B", "KB", "680")
    R(d, 21, 7.5, "KB", "GND", "820")
    CP(d, 22, 7.5, "KB", "GND", "100u/25V", fp="CPE6")
    C(d, 23, 4, "P1B", "ATT_IN", "470n/400V film", rot=0, fp="FILM15")
    R(d, 24, 5.2, "ATT_IN", "GND", "1M")
    d.text("Return stage: 680R unbypassed sets the bypass gain preamp -> PI input to -3.8 dB (20 V peak in = 13 V at the PI, "
           "under the 18 V limit of PI-4)", 18, 9.5)
    # Second pass (IF-1.2, interfaces.md 10.1): RETURN_SIG bleed at J102, so the ribbon side of the 220n never floats
    # with W23 unplugged (the grid side is held by the 1M on NW and the 220k on M). 2.2M keeps the pad-on load >= 100k
    # (1M would give 99k); the return law moves < 0.1 dB
    # (rev_b/sim/fx_loop, rret_bleed). The SEND_SRC side is bled by the 1M on CFO through the 1k.
    R(d, 1.5, 8.2, "RETURN_SIG", "GND", "2.2M")


# ------------------------------------------------------------------ sheet 02
ATT = ((1, "5.36k", "412k"), (2, "10.2k", "191k"), (4, "18.2k", "84.5k"), (8, "30.1k", "33.2k"), (16, "42.2k", "7.87k"))


def sheet02(d):
    d.text("02 PI-4 attenuator (five binary L-sections for Z0 = 49.9k, relay energised = section in (NO contacts), unpowered = "
           "0 dB; 0-18 dB used of 0-31) "
           "and the phase inverter: 12AX7 LTP, DN2540 CCS tail about 2 mA, equal 100k plates, feedback into the second "
           "grid (sim/pi_nfb). Plate DC goes out on W24; the coupling caps are on the power amp (interfaces.md 10).", 0, -1.0, 2)
    # INTERFACE: J201 = W24-a, Molex Mini-Fit Jr (user V5, 2026-11-23; interfaces.md IF-1.3), pin order unchanged:
    # 1 GND, 2 DRV_A, 3 GND, 4 DRV_B, 5 GND; the 2x3 part (5566-06A) with position 6 unused. Rows: 1-2-3 / 4-5-6, so each
    # drive pin has only GND pins beside it (DRV_A: 1, 3, 5; DRV_B: 1, 5); >= 600 V wire.
    d.part("Conn_02x03_Top_Bottom", "J", 24, 8, {1: "GND_DRV", 2: "DRV_A", 3: "GND_DRV", 4: "DRV_B", 5: "GND_DRV", 6: "NC"},
           value="DRIVE (W24-a, Mini-Fit Jr)", fp="MFJ2x3")
    softtie(d, 22, 10.5, "GND_DRV", "GND", "W24 ground: soft tie at the sending end (grounding.md)")
    node = "ATT_IN"
    for i, (db, rs, rp) in enumerate(ATT):
        nxt = "ATT_OUT" if i == len(ATT) - 1 else f"ATT{i + 1}"
        c0 = 1 + i * 3.2
        d.text(f"{db} dB", c0, 0.4)
        R(d, c0, 1, node, nxt, rs, rot=0)
        # pole 1 (COM 3 / NC 4) shorts the series R while unpowered; pole 2 (COM 6 / NO 7) connects the shunt when on
        relay(d, c0 + 0.6, 3.2, f"RLY_ATT{db}_N", {3: node, 4: nxt, 6: nxt, 7: f"ATP{db}"})
        R(d, c0 + 2, 5.5, f"ATP{db}", "GND", rp)
        node = nxt
    R(d, 17, 2.2, "ATT_OUT", "GND", "49.9k")
    # PI
    C(d, 18, 1, "ATT_OUT", "PIX", "10n/630V film", rot=0, fp="FILM10")
    R(d, 19.5, 2.2, "PIX", "PI_REF", "1M")
    R(d, 19.5, 1, "PIX", "G2A", "1k", rot=0)
    d.part("ECC83", "V2", 21, 1.5, {1: "DRV_A", 2: "G2A", 3: "PK"}, value="12AX7", unit=2)
    R(d, 21, 0, "BPI_P", "DRV_A", "100k 1W", fp="R2512")
    d.part("ECC83", "V2", 21, 6, {6: "DRV_B", 7: "G2B", 8: "PK"}, value="12AX7", unit=1)
    R(d, 21, 4.5, "BPI_P", "DRV_B", "100k 1W", fp="R2512")
    R(d, 19.5, 6, "G2BX", "G2B", "1k", rot=0)
    R(d, 18.5, 7.3, "G2BX", "PI_REF", "1M")
    C(d, 17.5, 6, "FB_NODE", "G2BX", "22n/630V film", rot=0, fp="FILM10")
    d.text("Second-grid cap 22n (pi_nfb, unchanged by V1). Power tubes (on the power amp): grid leak 91k, coupling cap 220n "
           "film >= 630 V per tube (user V1, 2026-11-23; docs/output_stage_stability.md).", 15, 8.2)
    R(d, 22.5, 3.2, "PK", "PTOP", "1k")
    d.part("DN2540N8-G", "Q", 22.5, 5, {2: "PTOP", 1: "QG", 3: "QS"}, value="DN2540N8")
    R(d, 21.5, 6.6, "QG", "GND", "100")
    R(d, 23.5, 6.6, "QS", "GND", "1k (select, ~2 mA)")
    d.text("CCS: DN2540 with a source resistor (Vgs(off) spread 1.5-3.5 V: select or trim Rs for 2.0 mA); tail top about 21 V", 18, 9.2)
    # Third pass: the PI grid leaks return to a fixed, decoupled reference (PI_REF about 22 V), not to the CCS tail top:
    # with the leaks on the tail top an overdrive burst pumps the PI's common mode up (+39 V after +13 dB, +108 V after
    # +20 dB, not back after 1 s; docs/output_stage_stability.md section 5); with PI_REF the PI grid moves +1.2 / +2.8 V
    # and is back within 11 ms (rev_b/sim/pi_burst/results/leak_ref.md). 2 x 820k 2512 (182 V each) from B+PI decoupled.
    R(d, 16, 10.5, "BPI_P", "PIR_M", "820k", fp="R2512")
    R(d, 16, 12, "PIR_M", "PI_REF", "820k", fp="R2512")
    R(d, 17.2, 13.2, "PI_REF", "GND", "100k")
    CP(d, 18.2, 13.2, "PI_REF", "GND", "10u/50V", fp="CPE5")
    d.text("PI_REF: grid-leak reference, 386 V x 100k / 1.74M = 22 V, 10u (corner 0.17 Hz)", 15, 14.6)


# ------------------------------------------------------------------ sheet 03
CH = (("CL", "clean"), ("CR", "crunch"), ("LD", "lead"))


def sheet03(d):
    d.text("03 Feedback: one network per channel (PI-3, sim/pi_nfb): relay (G6K-2F-Y, NO contacts) at the 8 ohm end -> Rf 100k || Cf 22p -> Cres 22n || "
           "resonance pot (front panel, W30-W32) -> network node -> NJFET T-switch -> common feedback node (second grid's cap); "
           "presence 1k + pot + 22n from the network node. Rbot 4.7k stays on the common node (no network = no feedback, "
           "grid still returned).", 0, -1.0, 2)
    # INTERFACE: J301 = W25-b (1 FB_8R, 2 FB_RTN), Lock-3.96, twisted pair
    d.part("Conn_01x02", "J", 0, 6, {1: "FB_8R", 2: "FB_RTN"}, value="FB (W25-b)", fp="KK396x2")
    R(d, 1.5, 7.5, "FB_RTN", "GND", "0R")
    d.text("FB_RTN: the OT secondary COM, referenced here only (grounding.md); 0R link (10R || 100n footprint option)", 0, 9)
    for i, (t, name) in enumerate(CH):
        r0 = 0.5 + i * 4.5
        d.text(f"{name}", 2, r0 - 0.3)
        # INTERFACE: J302-J304 = W30-b..W32-b (interfaces.md 11.2)
        d.part("Conn_02x05_Odd_Even", "J", 11, r0 + 2, {1: "GND", 2: f"FX_{t}", 3: "GND", 4: f"FN_{t}", 5: "GND",
                                                        6: f"PRA_{t}", 7: "GND", 8: f"PRW_{t}", 9: "GND", 10: "GND"},
               value=f"PRES/RES {t} (W{30 + i}-b)", fp="IDC2x5")
        # both poles in parallel on the NO contacts (COM 3 / NO 2, COM 6 / NO 7): unpowered = network open
        relay(d, 3, r0 + 1.5, f"RLY_FB_{t}_N", {3: "FB_8R", 2: f"SPK_{t}", 6: "FB_8R", 7: f"SPK_{t}"})
        R(d, 5, r0 + 2.7, f"SPK_{t}", "GND", "1M")
        R(d, 6, r0 + 0.5, f"SPK_{t}", f"FX_{t}", "100k 0.5W", rot=0, fp="R1206")
        C(d, 6, r0 + 1.5, f"SPK_{t}", f"FX_{t}", "22p/200V C0G (PI-6)", rot=0, fp="C1206")
        C(d, 8, r0 + 1, f"FX_{t}", f"FN_{t}", "22n C0G 50V", rot=0, fp="C1206")
        R(d, 8, r0 + 2.5, f"FN_{t}", f"PRA_{t}", "1k", rot=0)
        C(d, 9.5, r0 + 3.5, f"PRW_{t}", "GND", "22n C0G 50V", fp="C1206")
        jfet_series(d, 15, r0 + 1, f"FN_{t}", f"T_{t}", f"JDRV_FBS_{t}", f"S1{t}")
        jfet_series(d, 18, r0 + 1, f"T_{t}", "FB_NODE", f"JDRV_FBS_{t}", f"S2{t}")
        jfet_shunt(d, 16.5, r0 + 3, f"T_{t}", f"JDRV_FBH_{t}", f"H{t}")
    R(d, 21, 5, "FB_NODE", "GND", "4.7k")
    R(d, 22, 4, "FB_NODE", "STP", "DNP (step R)", rot=0)   # footprint only; the Rf 47k + step option is dropped (V1)
    C(d, 23, 5.2, "STP", "GND", "DNP (step C)", fp="C0805")
    d.text("Rf >= 68k on every channel (user V1, 2026-11-23; drawn 100k || 22p each). PI-6 step network: DNP footprint only "
           "(the Rf 47k + step option is dropped); Zobel belongs at the OT secondary", 20, 7)
    d.text("Layout: J302 / J303 / J304 (W30 / W31 / W32) at x 200-279, on the downward face near the front edge, in CL / CR / LD "
           "order (interfaces.md 12.3), away from J101 and the FX return", 20, 8)


# ------------------------------------------------------------------ sheet 04
def sheet04(d):
    d.text("04 Switch control: MCP23S17 (map interfaces.md 7.2) -> 3x DG412 (JFET gates 0 / -15 V), ULN2803A relay sinks. "
           "Mixer branch enable = FX_x AND FX_UNMUTE AND MUTE_ALL_N (74LVC1G11). Reset, card absent, ribbon unplugged or "
           "-15 V missing: both FX branches shunted (muted), feedback JFETs shunted, relays off. GNDD = DGND island.", 0, -1.0, 2)
    # INTERFACE: J401 = W13-b, template 2x7 (interfaces.md 6.1)
    d.part("Conn_02x07_Odd_Even", "J", 0, 2, {1: "+5V", 2: "GNDD", 3: "+15V", 4: "GNDD", 5: "-15V", 6: "GNDD",
                                              7: "SPI_SCK", 8: "GNDD", 9: "SPI_MOSI", 10: "SPI_MISO",
                                              11: "SPI_CS_N", 12: "MUTE_ALL_N", 13: "RESET_N", 14: "GNDD"},
           value="CONTROL (W13-b)", fp="IDC2x7")
    for i, n in enumerate(("+5V", "+15V", "-15V", "GNDD")):
        d.part("PWR_FLAG", f"#FLG40{i}", 2, 4 + i * 0.6, {1: n}, value="PWR_FLAG")
    softtie(d, 0, 7, "GNDD", "GND", "DGND - AGND soft tie at the header (grounding.md)")
    d.part("PWR_FLAG", "#FLG404", 2, 8, {1: "GND"}, value="PWR_FLAG")
    R(d, 3, 1, "RESET_N", "+5V", "10k")
    R(d, 3, 3, "MUTE_ALL_N", "GNDD", "100k")
    gp = {21: "FX_DRY", 22: "FX_WET", 23: "FX_UNMUTE", 24: "FB_RLY_CL", 25: "FB_RLY_CR", 26: "FB_RLY_LD",
          27: "FB_J_CL", 28: "FB_J_CR", 1: "FB_J_LD", 2: "ATT_1DB", 3: "ATT_2DB", 4: "ATT_4DB", 5: "ATT_8DB",
          6: "ATT_16DB", 7: "NC", 8: "NC"}
    nets = dict(gp)
    nets.update({9: "+5V", 10: "GNDD", 11: "SPI_CS_N", 12: "SPI_SCK", 13: "SPI_MOSI", 14: "SPI_MISO",
                 15: "GNDD", 16: "GNDD", 17: "GNDD", 18: "RESET_N", 19: "NC", 20: "NC"})
    d.part("MCP23S17x-x-SS", "U", 6, 3, nets, value="MCP23S17-E/SS")
    C(d, 6, 0, "+5V", "GNDD", "100n", rot=0)
    used = sorted(n for n in gp.values() if n != "NC")
    for k, n in enumerate(used):
        R(d, 9 + (k % 7) * 1.6, 8.5 + (k // 7) * 1.4, n, "GNDD", "100k")
    # branch enables
    d.part("74LVC1G11", "U", 10, 1, {1: "FX_DRY", 3: "FX_UNMUTE", 6: "MUTE_ALL_N", 4: "DRY_EN", 2: "GNDD", 5: "+5V"},
           value="74LVC1G11", fp="SOT23-6")
    d.part("74LVC1G11", "U", 10, 4, {1: "FX_WET", 3: "FX_UNMUTE", 6: "MUTE_ALL_N", 4: "WET_EN", 2: "GNDD", 5: "+5V"},
           value="74LVC1G11", fp="SOT23-6")
    C(d, 11.5, 0, "+5V", "GNDD", "100n", rot=0)
    C(d, 11.5, 3, "+5V", "GNDD", "100n", rot=0)
    # DG412: series gates pulled to -15 V (off), switched to GND (on) when IN high;
    #        shunt gates pulled to GND (on), switched to -15 V (off) when IN high.
    sw = [("DRY_EN", "JDRV_DS", "GND"), ("DRY_EN", "JDRV_DH", "-15V"), ("WET_EN", "JDRV_WS", "GND"), ("WET_EN", "JDRV_WH", "-15V"),
          ("FB_J_CL", "JDRV_FBS_CL", "GND"), ("FB_J_CL", "JDRV_FBH_CL", "-15V"), ("FB_J_CR", "JDRV_FBS_CR", "GND"),
          ("FB_J_CR", "JDRV_FBH_CR", "-15V"), ("FB_J_LD", "JDRV_FBS_LD", "GND"), ("FB_J_LD", "JDRV_FBH_LD", "-15V"),
          (None, None, None), (None, None, None)]
    pins = [(1, 2, 3), (8, 7, 6), (9, 10, 11), (16, 15, 14)]
    for j in range(3):
        key = f"U_dg{j}"
        for u in range(4):
            inp, dpin, spin = pins[u]
            ex, drv, src = sw[j * 4 + u]
            if ex is None:
                nets = {inp: "GNDD", dpin: "NC", spin: "NC"}
            else:
                nets = {inp: ex, dpin: drv, spin: src}
            d.part("DG412xY", key, 14 + u * 2.2, 1.5 + j * 3.6, nets, value="DG412DY", unit=u + 1)
        d.part("DG412xY", key, 23, 1.5 + j * 3.6, {4: "-15V", 5: "GNDD", 12: "+5V", 13: "+15V"}, value="DG412DY", unit=5)
        C(d, 24.5, 1 + j * 3.6, "+15V", "GNDD", "100n")
        C(d, 25.5, 1 + j * 3.6, "-15V", "GNDD", "100n")
    for k, (_, drv, src) in enumerate(s for s in sw if s[0]):
        R(d, 14 + k * 1.2, 12.5, drv, "-15V" if src == "GND" else "GND", "100k")
    d.text("Gate pulls: series (JDRV_*S*) 100k to -15 V = off; shunt (JDRV_*H*) 100k to GND = on", 14, 11.6)
    rl = ["FB_RLY_CL", "FB_RLY_CR", "FB_RLY_LD", "ATT_1DB", "ATT_2DB", "ATT_4DB", "ATT_8DB", "ATT_16DB"]
    out = ["RLY_FB_CL_N", "RLY_FB_CR_N", "RLY_FB_LD_N", "RLY_ATT1_N", "RLY_ATT2_N", "RLY_ATT4_N", "RLY_ATT8_N", "RLY_ATT16_N"]
    nets = {i + 1: rl[i] for i in range(8)}
    nets.update({18 - i: out[i] for i in range(8)})
    nets.update({9: "GNDD", 10: "+5V"})
    d.part("ULN2803A", "U", 6, 11, nets, value="ULN2803A", fp="SOIC18W")
    C(d, 8, 13, "+5V", "GNDD", "10u/16V", fp="C0805")
    d.text("Relay coils: G6K-2F-Y 5 V, 21.1 mA each; +5 V about 25 mA at 0 dB (one feedback relay), about 115 mA at the 15 dB "
           "step (4 attenuator relays + 1 feedback relay). ULN2803A clamp diodes to +5V (pin 10).", 0, 14.3)


# ------------------------------------------------------------------ sheet 05
def regulator(d, c0, r0, tag, out, zeners, rs, note):
    """docs/preamp_regulator.md, rev B reference (SMD with thermal foldback): LND150 CCS -> zener
    string -> Rf / Cf filter (soft start) -> STD4N80K5 (DPAK, on a copper pour) source follower,
    foldback current limit by an MMBTA42 placed ON the pass device's pour (thermally coupled,
    electrically separate: thermal foldback), 47u + 100n + bleed. No drain resistor: B+PI and B+FX
    pass at 70 C without one (preamp_regulator.md; rev_b/sim/preamp_supply with this board's loads).
    HV resistor strings split so no SMD resistor sees more than 200 V: Rf 3 x 330k (390 V at
    start-up), R3 3 x 270k (430 V at start-up / into a short), bleed 3 x 150k (388 V)."""
    d.text(note, c0, r0 - 0.6)
    d.part("DN2540N8-G", "Q", c0 + 1, r0, {2: "BP_RAW", 1: f"ZT_{tag}", 3: f"CS_{tag}"}, value="LND150N8", fp="SOT89")
    R(d, c0 + 2, r0 + 1, f"CS_{tag}", f"ZT_{tag}", "330", fp="R1206")
    for i, zv in enumerate(zeners):
        top = f"ZT_{tag}" if i == 0 else f"Z{i}_{tag}"
        bot = "GND" if i == len(zeners) - 1 else f"Z{i + 1}_{tag}"
        d.part("D_Zener", "D", c0 + 2, r0 + 2.2 + i * 1.1, {1: top, 2: bot}, value=zv, rot=90, fp="SMA")
    R(d, c0 + 3.5, r0 + 1, f"ZT_{tag}", f"RF1_{tag}", "330k", rot=0, fp="R2512")
    C(d, c0 + 4.5, r0 + 2.2, f"GF_{tag}", "GND", "2.2u/630V film", fp="FILM27")
    R(d, c0 + 5.5, r0 + 1, f"GF_{tag}", f"GP_{tag}", "10k", rot=0, fp="R1206")
    d.part("D", "D", c0 + 4.5, r0 - 0.3, {1: "BP_RAW", 2: f"GF_{tag}"}, value="1N4007 (M7)", fp="SMA")
    d.part("Q_NMOS_GDS", "Q", c0 + 7, r0 + 1, {2: "BP_RAW", 1: f"GP_{tag}", 3: f"SRC_{tag}"}, value="STD4N80K5",
           fp="DPAK")
    d.part("D_Zener", "D", c0 + 6.5, r0 + 3, {1: f"GP_{tag}", 2: f"SRC_{tag}"}, value="15V", rot=90, fp="SOD123")
    R(d, c0 + 8, r0 + 2, f"SRC_{tag}", out, rs, rot=0, fp="R1206")
    d.part("MMBTA42", "Q", c0 + 8.5, r0 + 4, {1: f"QB_{tag}", 3: f"GP_{tag}", 2: out}, value="MMBTA42")
    R(d, c0 + 7.5, r0 + 5.2, f"SRC_{tag}", f"QB_{tag}", "1k", rot=0, fp="R1206")
    R(d, c0 + 9.5, r0 + 5.2, f"QB_{tag}", out, "10k", rot=0, fp="R1206")
    R(d, c0 + 8.5, r0 + 6.2, "BP_RAW", f"FBA_{tag}", "270k", rot=0, fp="R2512")
    CP(d, c0 + 10, r0 + 2.2, out, "GND", "47u/500V", fp="CPD18")
    C(d, c0 + 11, r0 + 2.2, out, "GND", "100n/630V", fp="FILM10")
    R(d, c0 + 12, r0 + 2.2, out, f"BL1_{tag}", "150k", fp="R2512")
    # the rest of the split HV strings (drawn after, so the refs above keep their order)
    R(d, c0 + 3.5, r0 + 0.2, f"RF1_{tag}", f"RF2_{tag}", "330k", rot=0, fp="R2512")
    R(d, c0 + 4.5, r0 + 0.8, f"RF2_{tag}", f"GF_{tag}", "330k", rot=0, fp="R2512")
    R(d, c0 + 10.5, r0 + 6.2, f"FBA_{tag}", f"FBB_{tag}", "270k", rot=0, fp="R2512")
    R(d, c0 + 12, r0 + 6.2, f"FBB_{tag}", f"QB_{tag}", "270k", rot=0, fp="R2512")
    R(d, c0 + 12, r0 + 3.6, f"BL1_{tag}", f"BL2_{tag}", "150k", fp="R2512")
    R(d, c0 + 12, r0 + 5.0, f"BL2_{tag}", "GND", "150k", fp="R2512")
    d.text(f"Q (MMBTA42) on the STD4N80K5's copper pour (thermal foldback); 2.2u film: Rf 3 x 330k", c0 + 6, r0 + 7)


def sheet05(d):
    d.text("05 Supply: raw HV tab (RAW_SS, no fuse: protected by the regulators' foldback, the tube PSU's short-circuit "
           "protection and the control board's trip request, interfaces.md 8), B+PI and B+FX regulators (preamp_regulator.md "
           "rev B reference), RC decoupling per triode, heater tabs (in from the PSU, out to the preamp; floating, no "
           "reference on this board).", 0, -1.0, 2)
    # INTERFACE: J501 = W03-b (BP_RAW, GND) 4.8 mm tabs; J502 = W07-b heaters in, J503 = W08-a heaters out, 6.3 mm tabs
    d.part("Conn_01x02", "J", 0, 1, {1: "BP_RAW", 2: "GND"}, value="RAW HV (W03-b, 4.8 mm tabs)", fp="TAB48")
    d.part("Conn_01x02", "J", 0, 9, {1: "HTR1", 2: "HTR2"}, value="HEATER IN (W07-b, 6.3 mm tabs)", fp="TAB63")
    d.part("Conn_01x02", "J", 0, 11, {1: "HTR1", 2: "HTR2"}, value="HEATER OUT (W08-a, 6.3 mm tabs)", fp="TAB63")
    d.part("PWR_FLAG", "#FLG501", 1, 2.5, {1: "BP_RAW"}, value="PWR_FLAG")
    d.part("PWR_FLAG", "#FLG502", 1, 10, {1: "HTR1"}, value="PWR_FLAG")
    d.part("PWR_FLAG", "#FLG503", 1.6, 10, {1: "HTR2"}, value="PWR_FLAG")
    regulator(d, 2, 1, "PI", "BPI", ("130V", "130V", "130V"), "20R",
              "B+PI about 388 V (3x 130 V), limit 25 mA (19.5 mA with Q at 70 C), short 8 mA cold, about 0.6 W steady")
    regulator(d, 2, 9.5, "FX", "BFX", ("150V", "180V"), "16R",
              "B+FX about 328 V (150 V + 180 V), limit 27 mA (20 mA with Q at 70 C), short 10 mA cold, about 0.6 W steady")
    R(d, 17, 1, "BPI", "BPI_P", "2.2k", rot=0, fp="R1206")
    CP(d, 18, 2.2, "BPI_P", "GND", "22u/500V", fp="CPD16")
    R(d, 17, 9.5, "BFX", "BFX1", "10k", rot=0, fp="R1206")
    CP(d, 18, 10.7, "BFX1", "GND", "22u/500V", fp="CPD16")
    R(d, 17, 12.5, "BFX", "BFX2", "10k", rot=0, fp="R1206")
    CP(d, 18, 13.7, "BFX2", "GND", "22u/500V", fp="CPD16")
    d.text("Separate RC per FX triode (sim/fx_loop fix: shared decoupling leaked the dry into series mode at -64 dB)", 16, 8.7)
    for i, v in enumerate(("V1", "V2")):
        d.part("ECC83", v, 3 + i * 2, 18, {4: "HTR1", 5: "HTR1", 9: "HTR2"}, value="12AX7", unit=3)
    d.text("Heaters 6.3 V parallel (pins 4+5 / 9). 0.6 A here + 0.9 A passed to the preamp = 1.5 A through J502", 2, 19.5)


SHEETS = [("01_fx_loop.kicad_sch", sheet01), ("02_pi.kicad_sch", sheet02), ("03_feedback.kicad_sch", sheet03),
          ("04_control.kicad_sch", sheet04), ("05_supply.kicad_sch", sheet05)]


# ------------------------------------------------------------------ footprints and BOM
# Candidate parts: LCSC numbers are the ones the preamp rev B BOM checked on 2026-11-22 (same part,
# tube_preamp_kicad rev_b/bom); others are an MPN or a specification only. Resistors default to
# UNI-ROYAL thick film 1 % (MPN generated from the value); thin film / MELF preferred for cathode and
# plate resistors if sourced.
KNOWN = {
    ("100k", "R0603"): ("0603WAF1003T5E", "C25803"), ("10k", "R0603"): ("0603WAF1002T5E", "C25804"),
    ("10R", "R0603"): ("0603WAF100JT5E", "C22859"), ("100k", "R0805"): ("0805W8F1003T5E", "C149504"),
    ("1M", "R0805"): ("0805W8F1004T5E", "C17514"), ("220k", "R0805"): ("0805W8F2203T5E", "C17556"),
    ("270k", "R2512"): ("CL2512FN270KB", "C48392179"), ("100k", "R2512"): ("FRC2512F1003TS", "C2934045"),
    ("330", "R1206"): ("FRC1206F3300TS", "C2933675"), ("10k", "R1206"): ("1206W4F1002T5E", "C17902"),
    ("1k", "R1206"): ("1206W4F1001T5E", "C4410"),
    ("10n", "C0603"): ("0603B103K500NT", "C57112"), ("100n", "C0603"): ("CC0603KRX7R9BB104", "C14663"),
    ("22n C0G 50V", "C1206"): ("C1206N223K050T", "C105982"),
    ("100n/630V", "FILM10"): ("CBB21-630V104JP10", "C2888191"),
    ("22n/630V film", "FILM10"): ("MPE223J2JB050C030ZR", "C53224144"),
    ("470n/400V film", "FILM15"): ("CBB21-400V474JP15", "C2888194"),
    # B+ electrolytics 500 V (user, 2026-11-23: a shorted pass device puts the raw rail, up to 480 V, on B+):
    # Nichicon UCY (105 C, 12000 h), DigiKey / RS stock; not at LCSC (hand-solder). 47u second source Rubycon
    # 500LXW47MEFR18X25 (18 x 25, 12000 h).
    ("47u/500V", "CPD18"): ("Nichicon UCY2H470MHD6 (18 x 31.5, P7.5; alt. Rubycon 500LXW47MEFR18X25)", ""),
    ("22u/500V", "CPD16"): ("Nichicon UCY2H220MHD6 (16 x 25, P7.5)", ""),
    ("130V", "SMA"): ("1SMA5952B", "C48578686"), ("150V", "SMA"): ("1SMA5953B", ""), ("180V", "SMA"): ("1SMA5955B", ""),
    ("15V", "SOD123"): ("BZT52C15", "C2891782"), ("1N4007 (M7)", "SMA"): ("M7", "C7420350"),
    ("MMBFJ113", None): ("MMBFJ113", "C891686"), ("LND150N8", "SOT89"): ("LND150N8-G", "C629123"),
    ("STD4N80K5", "DPAK"): ("STD4N80K5", "C472540"), ("MMBTA42", None): ("MMBTA42", "C20069138"),
    ("DN2540N8", None): ("DN2540N8-G", ""),
    ("MCP23S17-E/SS", None): ("MCP23S17-E/SS", "C148009"), ("DG412DY", None): ("DG412DY-T1-E3", "C553989"),
    ("ULN2803A", "SOIC18W"): ("ULN2803ADWR", ""), ("74LVC1G11", "SOT23-6"): ("74LVC1G11GV,125", ""),
    ("G6K-2F-Y 5VDC", None): ("G6K-2F-Y-TR DC5", "C47190"),
    ("DRIVE (W24-a, Mini-Fit Jr)", "MFJ2x3"): ("Molex 39-28-1063 class (5566-06A; confirm the order code), receptacle 39-01-2060", ""),
    ("CONTROL (W13-b)", "IDC2x7"): ("HY2541WV-N-2x7P", "C17179454"),
    ("PRE IN (W22-b)", "KK254x3"): ("Molex 22272031", "C471416"),
    ("RAW HV (W03-b, 4.8 mm tabs)", "TAB48"): ("2x BTC-3-PCB484608T", "C20626099"),
    ("HEATER IN (W07-b, 6.3 mm tabs)", "TAB63"): ("2x BTC-3-PCB485005D", "C20626100"),
    ("HEATER OUT (W08-a, 6.3 mm tabs)", "TAB63"): ("2x BTC-3-PCB485005D", "C20626100"),
}
NOTES = {
    "FILM5": "film >= 100 V (PET / PP)", "FILM10": "film 630 V", "FILM15": "film >= 400 V", "FILM27": "PP film 630 V (preamp_regulator.md)",
    "CPD8": "105 C electrolytic", "CPE6": "105 C electrolytic", "CPE5": "105 C electrolytic", "CPD12": "105 C electrolytic", "CPD16": "105 C, 12000 h, not at LCSC: hand-solder", "CPD18": "105 C, 12000 h, not at LCSC: hand-solder",
    "R2512": "2512, 1 W, 200 V", "TAB48": "PLACEHOLDER footprint", "TAB63": "PLACEHOLDER footprint",
    "MFJ2x3": "W24: Mini-Fit Jr 600 V (V5); 2x3 with position 6 unused, same mapping on the power amp",
}
SYM_NOTES = {
    "ECC83": "noval PCB socket on the solder side (rev A part; rev A footprint tube_pi_fxloop:Valve_Noval_Belton_PCD21.00mm "
             "matches the chassis holes, use it at layout); tubes not on the BOM",
    "ULN2803A": "check the 70 C design temperature against the bought part's rating (ENV-2)",
    "G6K-2F-Y": "coil + 1 / - 8; NC 4 / 5, NO 2 / 7 (Omron datasheet)",
    "Q_NMOS_GDS": "DPAK on a copper pour; Q MMBTA42 on the same pour (thermal foldback)",
}
MULT = {"R": 1, "k": 1e3, "M": 1e6}


def rcode(v):
    """'4.7k' -> '4701' (E96 4-digit code); '10R' -> '10R0'; '0R' -> '0000'."""
    t = v.split()[0]
    if t in ("0R", "0"):
        return "0000"
    num, m = (t[:-1], MULT[t[-1]]) if t[-1] in MULT else (t, 1)
    ohm = float(num) * m
    if ohm < 100:
        return None
    e = int(math.floor(math.log10(ohm))) - 2
    return f"{int(round(ohm / 10 ** e)):03d}{e}"


def candidate(sym, value, key):
    v = (value or "").strip()
    for k in ((v, key), (v, None)):
        if k in KNOWN:
            return KNOWN[k]
    if sym == "R" and not v.startswith("DNP"):
        fam = {"R0603": "0603WAF{}T5E", "R0805": "0805W8F{}T5E", "R1206": "1206W4F{}T5E", "R2512": "25121WF{}T4E"}[key]
        code = rcode(v)
        return (fam.format(code) if code else f"{key[1:]} {v.split()[0]} 1 % thick film"), ""
    return "", ""


def footprint_of(ref):
    sym, value, key = PARTS[ref]
    if key:
        return FP.get(key, key)
    prop = [p for p in find_all(lib()[sym], "property") if p[1] == "Footprint"]
    return prop[0][2] if prop else ""


def write_fp_and_bom():
    rows = sorted(PARTS, key=lambda r: (r[0], int("".join(ch for ch in r[1:] if ch.isdigit()) or 0)))
    path = os.path.join(RB, "lib", "footprint_map.csv")
    with open(path, "w") as f:
        f.write("# generated by tools/sheets/draw_all.py: refdes -> footprint (read by p2k sch_builder)\n")
        f.write("refdes,footprint\n")
        for r in rows:
            f.write(f"{r},{footprint_of(r)}\n")
    groups = {}
    for r in rows:
        sym, value, key = PARTS[r]
        mpn, lcsc = candidate(sym, value, key)
        k = (value or sym, footprint_of(r), mpn, lcsc, NOTES.get(key, "") or SYM_NOTES.get(sym, ""))
        groups.setdefault(k, []).append(r)
    os.makedirs(os.path.join(RB, "bom"), exist_ok=True)
    import csv
    with open(os.path.join(RB, "bom", "bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Qty", "Refs", "Value", "Footprint", "Candidate MPN", "LCSC", "DNP", "Note"])
        for (value, fp, mpn, lcsc, note), refs in sorted(groups.items(), key=lambda kv: kv[1][0][0] + kv[1][0][1:].zfill(4)):
            w.writerow([len(refs), " ".join(refs), value, fp, mpn, lcsc, "yes" if value.startswith("DNP") else "", note])
    return len(rows), len(groups)


def main():
    seen = {}
    for f, fn in SHEETS:
        d = Drawer(f, "collect")
        fn(d)
        for n in d.nets:
            seen.setdefault(n, set()).add(f)
    glob = frozenset(n for n, fs in seen.items() if len(fs) > 1 and n not in POWER)
    nparts, nlines = write_fp_and_bom()
    sb._FOOTPRINTS = None              # re-read the footprint map just written
    for f, fn in SHEETS:
        d = Drawer(f, "draw", glob)
        fn(d)
        d.save()
    single = sorted(n for n, fs in seen.items() if len(fs) == 1)
    os.makedirs(os.path.join(RB, "build"), exist_ok=True)
    json.dump({f"{r}:{p}": n for (r, p), n in sorted(INTENDED.items())},
              open(os.path.join(RB, "build", "intended_nets.json"), "w"), indent=0)
    parts = len({r for r, _ in INTENDED})
    print(f"nets: {len(seen)}, global: {len(glob)}, parts with nets: {parts}, footprints: {nparts}, BOM lines: {nlines}")


if __name__ == "__main__":
    main()
