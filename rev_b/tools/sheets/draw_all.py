#!/usr/bin/env python3
"""Draw the five PI + FX loop rev B sheets (first draft).

Sources (tube_amplifier_kicad, read only, and this repo's rev_b/sim):
- PI and feedback: sim/pi_nfb (12AX7 LTP, ~2 mA CCS tail, equal 100k plates, feedback into the
  second grid; input 10n, second grid 22n; per-channel network Rf 100k || 22p, Cres 22n || 250k
  log pot, presence 1k + 50k rev-log + 22n, Rbot 4.7k); rev_b/sim/pi_nfb/run_open_load.py.
- FX loop: sim/fx_loop re-derived for rev B in rev_b/sim/fx_loop (fx_revb.py, run_fx_revb.py):
  the send cathode follower's grid is the >= 1 Mohm input buffer on the 140 kohm preamp output,
  rear send / return pots and the 0 / -20 dB pad (IF-1.1), JFET series-shunt mixer, return stage.
- PI-4 attenuator: five binary L-sections (1, 2, 4, 8, 16 dB, Z0 49.9k) on G6K-2 relays.
- Regulators: docs/preamp_regulator.md (B+PI about 390 V, B+FX about 330 V).
- Interfaces: docs/interfaces.md IF-1 / IF-1.1 (connector pinouts as the contract).

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
from p2k.sch_builder import Sheet, lib  # noqa: E402
from p2k.sexpr import find, find_all  # noqa: E402

POWER = {"GND", "GNDD", "+5V", "+15V", "-15V"}
GRID = 2.54
INTENDED = {}          # (ref, pin) -> net


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

    def part(self, sym, ref, c, r, nets, value=None, rot=0, unit=1, stub=GRID):
        ref = self.auto_ref(ref, sym)
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
def R(d, c, r, a, b, v, rot=90):
    return d.part("R", "R", c, r, {1: a, 2: b}, value=v, rot=rot)


def C(d, c, r, a, b, v, rot=90):
    return d.part("C", "C", c, r, {1: a, 2: b}, value=v, rot=rot)


def CP(d, c, r, plus, minus, v, rot=0):
    return d.part("C_Polarized", "C", c, r, {1: plus, 2: minus}, value=v, rot=rot)


def softtie(d, c, r, a, b, note):
    """Soft tie (docs/grounding.md): 10R || 100n."""
    R(d, c, r, a, b, "10R")
    C(d, c + 1, r, a, b, "100n")
    d.text(note, c, r - 0.6)


def jfet_series(d, c, r, a, b, drv, tag):
    """Series NJFET (MMBFJ113, on = gate 0 V, off = -15 V). Edge filter 100k / 10n, then 1M to
    the gate so the gate floats with the channel when on (rev_b/sim/fx_loop: a gate held at AC
    ground by the 10n forward-biases on the negative peaks and distorts)."""
    d.part("MMBFJ113", "Q", c, r, {1: a, 2: b, 3: f"GJ_{tag}"}, value="MMBFJ113")
    R(d, c - 1, r - 0.5, drv, f"GC_{tag}", "100k", rot=0)
    C(d, c - 1, r + 0.6, f"GC_{tag}", "GND", "10n", rot=270)
    R(d, c - 0.2, r + 1.2, f"GC_{tag}", f"GJ_{tag}", "1M")


def jfet_shunt(d, c, r, a, drv, tag):
    """Shunt NJFET to GND (on = gate 0 V through 100k / 10n)."""
    d.part("MMBFJ113", "Q", c, r, {1: a, 2: "GND", 3: f"GJ_{tag}"}, value="MMBFJ113")
    R(d, c - 1, r - 0.5, drv, f"GJ_{tag}", "100k", rot=0)
    C(d, c - 1, r + 0.6, f"GJ_{tag}", "GND", "10n", rot=270)


def relay(d, c, r, drive, poles):
    """G6K-2 (SMD, 5 V coil, family decided, part number OPEN with the preamp): coil 1 to +5V,
    8 to the ULN2803A sink. Pole 1: COM 3, NC 2, NO 4. Pole 2: COM 6, NC 7, NO 5 (KiCad stock
    G6K-2; confirm NC / NO against the Omron datasheet, interfaces.md 7.1 note)."""
    nets = {1: "+5V", 8: drive}
    for p in (2, 3, 4, 5, 6, 7):
        nets[p] = poles.get(p, "NC")
    return d.part("G6K-2", "K", c, r, nets, value="G6K-2F-Y 5VDC")


# ------------------------------------------------------------------ sheet 01
def sheet01(d):
    d.text("01 FX loop (one 12AX7, V1). The send cathode follower's grid is the >= 1 Mohm input buffer on the 140 kohm "
           "preamp output (interfaces.md note 1); dry and wet both pass the return stage (FX-1). Values: rev_b/sim/fx_loop "
           "(fx_revb.py).", 0, -1.0, 2)
    # INTERFACE: J101 = W22-b (mirror of preamp J507: 1 OUT, 2 GND, 3 GND / shield; solid at this receiving end)
    d.part("Conn_01x03", "J", 0, 1, {1: "PRE_IN", 2: "GND", 3: "GND"}, value="PRE IN (W22-b)")
    # INTERFACE: J102 = W23-a, IF-1.1 pinout (2x8, odd pins GND, no power)
    d.part("Conn_02x08_Odd_Even", "J", 0, 7, {1: "GND", 2: "SEND_SRC", 3: "GND", 4: "GND", 5: "GND", 6: "RETURN_SIG",
                                              7: "GND", 8: "GND", 9: "GND", 10: "PAD_A", 11: "GND", 12: "GND",
                                              13: "GND", 14: "NC", 15: "GND", 16: "NC"}, value="FX (W23-a)")
    d.text("J102 pin 12 PAD_B = GND (the pad switch grounds PAD_A); pins 14 / 16 RSVD1 / RSVD2 not connected", 0, 9.3)
    # input network and send cathode follower (V1 pins 1-3)
    R(d, 1.5, 2.2, "PRE_IN", "GND", "2.2M")
    C(d, 2.5, 1, "PRE_IN", "CI", "100n/250V film", rot=0)
    R(d, 3.5, 1, "CI", "G1A", "4.7k", rot=0)
    R(d, 4.5, 2.2, "G1A", "SB", "1M")
    d.part("ECC83", "V1", 6, 1, {1: "BFX1", 2: "G1A", 3: "K1A"}, value="12AX7", unit=2)
    R(d, 6, 3, "K1A", "SB", "1.5k")
    R(d, 6, 4.5, "SB", "GND", "22k 0.5W")
    CP(d, 7.5, 2.2, "K1A", "CFO", "4.7u/160V")
    R(d, 8.5, 3, "CFO", "GND", "1M")
    R(d, 9, 1, "CFO", "SEND_SRC", "1k", rot=0)
    R(d, 9, 4.5, "CFO", "NP", "47k", rot=0)
    R(d, 10, 5.7, "NP", "GND", "4.7k")
    d.text("SEND_SRC: full preamp level (-2 dB) to the SEND LEVEL pot on the rear I/O board", 8.5, 0.3)
    # return input and the pad (resistors here, switch contact on the ribbon)
    C(d, 2.5, 7, "RETURN_SIG", "RC", "220n/100V film", rot=0)
    R(d, 3.5, 7, "RC", "NW", "100k", rot=0)
    R(d, 4.5, 8.2, "NW", "GND", "1M")
    R(d, 5.5, 8.2, "NW", "PD", "11k")
    d.part("MMBFJ113", "Q", 5.8, 9.8, {1: "PD", 2: "GND", 3: "G_PAD"}, value="MMBFJ113")
    R(d, 3, 10.5, "PAD_A", "-15V", "1M")
    C(d, 2, 10.5, "PAD_A", "GND", "100n")
    R(d, 4, 9.6, "PAD_A", "G_PAD", "100k", rot=0)
    C(d, 4.2, 11, "G_PAD", "GND", "10n")
    d.text("Pad: rear switch open (or W23 unplugged) = PAD_A at -15 V = JFET off = 0 dB; closed = PAD_A at GND = JFET on = "
           "11k shunt = -20 dB. No audio node crosses the ribbon on PAD_A (rev B proposal, STATUS.md).", 2, 12.2)
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
    R(d, 21, 2.5, "BFX2", "P1B", "100k")
    R(d, 21, 6, "K1B", "KB", "680")
    R(d, 21, 7.5, "KB", "GND", "820")
    CP(d, 22, 7.5, "KB", "GND", "100u/25V")
    C(d, 23, 4, "P1B", "ATT_IN", "470n/400V film", rot=0)
    R(d, 24, 5.2, "ATT_IN", "GND", "1M")
    d.text("Return stage: 680R unbypassed sets the bypass gain preamp -> PI input to -3.8 dB (20 V peak in = 13 V at the PI, "
           "under the 18 V limit of PI-4)", 18, 9.5)


# ------------------------------------------------------------------ sheet 02
ATT = ((1, "5.36k", "412k"), (2, "10.2k", "191k"), (4, "18.2k", "84.5k"), (8, "30.1k", "33.2k"), (16, "42.2k", "7.87k"))


def sheet02(d):
    d.text("02 PI-4 attenuator (five binary L-sections for Z0 = 49.9k, relay energised = section in; 0-18 dB used of 0-31) "
           "and the phase inverter: 12AX7 LTP, DN2540 CCS tail about 2 mA, equal 100k plates, feedback into the second "
           "grid (sim/pi_nfb). Plate DC goes out on W24; the coupling caps are on the power amp (interfaces.md 10).", 0, -1.0, 2)
    # INTERFACE: J201 = W24-a (1 GND, 2 DRV_A, 3 GND, 4 DRV_B, 5 GND), Lock-3.96, >= 600 V wire
    d.part("Conn_01x05", "J", 24, 8, {1: "GND_DRV", 2: "DRV_A", 3: "GND_DRV", 4: "DRV_B", 5: "GND_DRV"},
           value="DRIVE (W24-a)")
    softtie(d, 22, 10.5, "GND_DRV", "GND", "W24 ground: soft tie at the sending end (grounding.md)")
    node = "ATT_IN"
    for i, (db, rs, rp) in enumerate(ATT):
        nxt = "ATT_OUT" if i == len(ATT) - 1 else f"ATT{i + 1}"
        c0 = 1 + i * 3.2
        d.text(f"{db} dB", c0, 0.4)
        R(d, c0, 1, node, nxt, rs, rot=0)
        relay(d, c0 + 0.6, 3.2, f"RLY_ATT{db}_N", {3: node, 2: nxt, 6: nxt, 5: f"ATP{db}"})
        R(d, c0 + 2, 5.5, f"ATP{db}", "GND", rp)
        node = nxt
    R(d, 17, 2.2, "ATT_OUT", "GND", "49.9k")
    # PI
    C(d, 18, 1, "ATT_OUT", "PIX", "10n/630V film", rot=0)
    R(d, 19.5, 2.2, "PIX", "PTOP", "1M")
    R(d, 19.5, 1, "PIX", "G2A", "1k", rot=0)
    d.part("ECC83", "V2", 21, 1.5, {1: "DRV_A", 2: "G2A", 3: "PK"}, value="12AX7", unit=2)
    R(d, 21, 0, "BPI_P", "DRV_A", "100k 1W")
    d.part("ECC83", "V2", 21, 6, {6: "DRV_B", 7: "G2B", 8: "PK"}, value="12AX7", unit=1)
    R(d, 21, 4.5, "BPI_P", "DRV_B", "100k 1W")
    R(d, 19.5, 6, "G2BX", "G2B", "1k", rot=0)
    R(d, 18.5, 7.3, "G2BX", "PTOP", "1M")
    C(d, 17.5, 6, "FB_NODE", "G2BX", "22n/630V film", rot=0)
    d.text("Second-grid cap 22n (pi_nfb); open-load LF margin: rev_b/sim/pi_nfb/results/open_load.md", 15, 8.2)
    R(d, 22.5, 3.2, "PK", "PTOP", "1k")
    d.part("Q_NMOS_Depletion", "Q", 22.5, 5, {"D": "PTOP", "G": "QG", "S": "QS"}, value="DN2540N8")
    R(d, 21.5, 6.6, "QG", "GND", "100")
    R(d, 23.5, 6.6, "QS", "GND", "1k (select, ~2 mA)")
    d.text("CCS: DN2540 with a source resistor (Vgs(off) spread 1.5-3.5 V: select or trim Rs for 2.0 mA); tail top about 20 V", 18, 9.2)


# ------------------------------------------------------------------ sheet 03
CH = (("CL", "clean"), ("CR", "crunch"), ("LD", "lead"))


def sheet03(d):
    d.text("03 Feedback: one network per channel (PI-3, sim/pi_nfb): relay at the 8 ohm end -> Rf 100k || Cf 22p -> Cres 22n || "
           "resonance pot (front panel, W30-W32) -> network node -> NJFET T-switch -> common feedback node (second grid's cap); "
           "presence 1k + pot + 22n from the network node. Rbot 4.7k stays on the common node (no network = no feedback, "
           "grid still returned).", 0, -1.0, 2)
    # INTERFACE: J301 = W25-b (1 FB_8R, 2 FB_RTN), Lock-3.96, twisted pair
    d.part("Conn_01x02", "J", 0, 6, {1: "FB_8R", 2: "FB_RTN"}, value="FB (W25-b)")
    R(d, 1.5, 7.5, "FB_RTN", "GND", "0R")
    d.text("FB_RTN: the OT secondary COM, referenced here only (grounding.md); 0R link (10R || 100n footprint option)", 0, 9)
    for i, (t, name) in enumerate(CH):
        r0 = 0.5 + i * 4.5
        d.text(f"{name}", 2, r0 - 0.3)
        # INTERFACE: J302-J304 = W30-b..W32-b (interfaces.md 11.2)
        d.part("Conn_02x05_Odd_Even", "J", 11, r0 + 2, {1: "GND", 2: f"FX_{t}", 3: "GND", 4: f"FN_{t}", 5: "GND",
                                                        6: f"PRA_{t}", 7: "GND", 8: f"PRW_{t}", 9: "GND", 10: "GND"},
               value=f"PRES/RES {t} (W{30 + i}-b)")
        relay(d, 3, r0 + 1.5, f"RLY_FB_{t}_N", {3: "FB_8R", 4: f"SPK_{t}", 6: "FB_8R", 5: f"SPK_{t}"})
        R(d, 5, r0 + 2.7, f"SPK_{t}", "GND", "1M")
        R(d, 6, r0 + 0.5, f"SPK_{t}", f"FX_{t}", "100k 0.5W", rot=0)
        C(d, 6, r0 + 1.5, f"SPK_{t}", f"FX_{t}", "22p/200V C0G (PI-6)", rot=0)
        C(d, 8, r0 + 1, f"FX_{t}", f"FN_{t}", "22n/100V film", rot=0)
        R(d, 8, r0 + 2.5, f"FN_{t}", f"PRA_{t}", "1k", rot=0)
        C(d, 9.5, r0 + 3.5, f"PRW_{t}", "GND", "22n/100V film")
        jfet_series(d, 15, r0 + 1, f"FN_{t}", f"T_{t}", f"JDRV_FBS_{t}", f"S1{t}")
        jfet_series(d, 18, r0 + 1, f"T_{t}", "FB_NODE", f"JDRV_FBS_{t}", f"S2{t}")
        jfet_shunt(d, 16.5, r0 + 3, f"T_{t}", f"JDRV_FBH_{t}", f"H{t}")
    R(d, 21, 5, "FB_NODE", "GND", "4.7k")
    R(d, 22, 4, "FB_NODE", "STP", "DNP (step R)", rot=0)
    C(d, 23, 5.2, "STP", "GND", "DNP (step C)")
    d.text("PI-6: step network footprint (DNP) on the common node; Cf per channel; Zobel belongs at the OT secondary", 20, 7)


# ------------------------------------------------------------------ sheet 04
def sheet04(d):
    d.text("04 Switch control: MCP23S17 (map interfaces.md 7.2) -> 3x DG412 (JFET gates 0 / -15 V), ULN2803A relay sinks. "
           "Mixer branch enable = FX_x AND FX_UNMUTE AND MUTE_ALL_N (74LVC1G11). Reset, card absent, ribbon unplugged or "
           "-15 V missing: both FX branches shunted (muted), feedback JFETs shunted, relays off. GNDD = DGND island.", 0, -1.0, 2)
    # INTERFACE: J401 = W13-b, template 2x7 (interfaces.md 6.1)
    d.part("Conn_02x07_Odd_Even", "J", 0, 2, {1: "+5V", 2: "GNDD", 3: "+15V", 4: "GNDD", 5: "-15V", 6: "GNDD",
                                              7: "SPI_SCK", 8: "GNDD", 9: "SPI_MOSI", 10: "SPI_MISO",
                                              11: "SPI_CS_N", 12: "MUTE_ALL_N", 13: "RESET_N", 14: "GNDD"},
           value="CONTROL (W13-b)")
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
           value="74LVC1G11")
    d.part("74LVC1G11", "U", 10, 4, {1: "FX_WET", 3: "FX_UNMUTE", 6: "MUTE_ALL_N", 4: "WET_EN", 2: "GNDD", 5: "+5V"},
           value="74LVC1G11")
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
    d.part("ULN2803A", "U", 6, 11, nets, value="ULN2803A")
    C(d, 8, 13, "+5V", "GNDD", "10u/16V")


# ------------------------------------------------------------------ sheet 05
def regulator(d, c0, r0, tag, out, zeners, rs, note):
    """docs/preamp_regulator.md: LND150 CCS -> zener string -> 1M / 2.2u filter (soft start) ->
    HV MOSFET source follower, foldback current limit (NPN), 47u + 100n + 470k bleed."""
    d.text(note, c0, r0 - 0.6)
    d.part("Q_NMOS_Depletion", "Q", c0 + 1, r0, {"D": "BP_RAW", "G": f"ZT_{tag}", "S": f"CS_{tag}"}, value="LND150")
    R(d, c0 + 2, r0 + 1, f"CS_{tag}", f"ZT_{tag}", "330")
    for i, zv in enumerate(zeners):
        top = f"ZT_{tag}" if i == 0 else f"Z{i}_{tag}"
        bot = "GND" if i == len(zeners) - 1 else f"Z{i + 1}_{tag}"
        d.part("D_Zener", "D", c0 + 2, r0 + 2.2 + i * 1.1, {1: top, 2: bot}, value=zv, rot=90)
    R(d, c0 + 3.5, r0 + 1, f"ZT_{tag}", f"GF_{tag}", "1M 500V", rot=0)
    C(d, c0 + 4.5, r0 + 2.2, f"GF_{tag}", "GND", "2.2u/630V film")
    R(d, c0 + 5.5, r0 + 1, f"GF_{tag}", f"GP_{tag}", "10k", rot=0)
    d.part("D", "D", c0 + 4.5, r0 - 0.3, {1: "BP_RAW", 2: f"GF_{tag}"}, value="1N4007")
    d.part("Q_NMOS", "Q", c0 + 7, r0 + 1, {"D": "BP_RAW", "G": f"GP_{tag}", "S": f"SRC_{tag}"}, value="STF4N80K5 (insulated)")
    d.part("D_Zener", "D", c0 + 6.5, r0 + 3, {1: f"GP_{tag}", 2: f"SRC_{tag}"}, value="15V", rot=90)
    R(d, c0 + 8, r0 + 2, f"SRC_{tag}", out, rs, rot=0)
    d.part("Q_NPN", "Q", c0 + 8.5, r0 + 4, {"B": f"QB_{tag}", "C": f"GP_{tag}", "E": out}, value="MMBTA42")
    R(d, c0 + 7.5, r0 + 5.2, f"SRC_{tag}", f"QB_{tag}", "1k", rot=0)
    R(d, c0 + 9.5, r0 + 5.2, f"QB_{tag}", out, "10k", rot=0)
    R(d, c0 + 8.5, r0 + 6.2, "BP_RAW", f"QB_{tag}", "820k 500V", rot=0)
    CP(d, c0 + 10, r0 + 2.2, out, "GND", "47u/450V")
    C(d, c0 + 11, r0 + 2.2, out, "GND", "100n/630V")
    R(d, c0 + 12, r0 + 2.2, out, "GND", "470k 0.5W")


def sheet05(d):
    d.text("05 Supply: raw HV tab (RAW_SS through the HV supplies' 100 mA fuse), B+PI and B+FX regulators (preamp_regulator.md), "
           "RC decoupling per triode, heater tabs (in from the PSU, out to the preamp; floating, no reference on this board).",
           0, -1.0, 2)
    # INTERFACE: J501 = W03-b (BP_RAW, GND) 4.8 mm tabs; J502 = W07-b heaters in, J503 = W08-a heaters out, 6.3 mm tabs
    d.part("Conn_01x02", "J", 0, 1, {1: "BP_RAW", 2: "GND"}, value="RAW HV (W03-b, 4.8 mm tabs)")
    d.part("Conn_01x02", "J", 0, 9, {1: "HTR1", 2: "HTR2"}, value="HEATER IN (W07-b, 6.3 mm tabs)")
    d.part("Conn_01x02", "J", 0, 11, {1: "HTR1", 2: "HTR2"}, value="HEATER OUT (W08-a, 6.3 mm tabs)")
    d.part("PWR_FLAG", "#FLG501", 1, 2.5, {1: "BP_RAW"}, value="PWR_FLAG")
    d.part("PWR_FLAG", "#FLG502", 1, 10, {1: "HTR1"}, value="PWR_FLAG")
    d.part("PWR_FLAG", "#FLG503", 1.6, 10, {1: "HTR2"}, value="PWR_FLAG")
    regulator(d, 2, 1, "PI", "BPI", ("130V 5W 2%", "130V 5W 2%", "130V 5W 2%"), "20R",
              "B+PI about 388 V (3x 130 V), limit 25 mA, foldback 8 mA")
    regulator(d, 2, 7.5, "FX", "BFX", ("150V 5W 2%", "180V 5W 2%"), "16R",
              "B+FX about 328 V (150 V + 180 V), limit 27 mA, foldback 10 mA")
    R(d, 17, 1, "BPI", "BPI_P", "2.2k", rot=0)
    CP(d, 18, 2.2, "BPI_P", "GND", "22u/450V")
    R(d, 17, 7.5, "BFX", "BFX1", "10k", rot=0)
    CP(d, 18, 8.7, "BFX1", "GND", "22u/450V")
    R(d, 17, 10.5, "BFX", "BFX2", "10k", rot=0)
    CP(d, 18, 11.7, "BFX2", "GND", "22u/450V")
    d.text("Separate RC per FX triode (sim/fx_loop fix: shared decoupling leaked the dry into series mode at -64 dB)", 16, 6.5)
    for i, v in enumerate(("V1", "V2")):
        d.part("ECC83", v, 3 + i * 2, 13.5, {4: "HTR1", 5: "HTR1", 9: "HTR2"}, value="12AX7", unit=3)
    d.text("Heaters 6.3 V parallel (pins 4+5 / 9). 0.6 A here + 0.9 A passed to the preamp = 1.5 A through J502", 2, 15)


SHEETS = [("01_fx_loop.kicad_sch", sheet01), ("02_pi.kicad_sch", sheet02), ("03_feedback.kicad_sch", sheet03),
          ("04_control.kicad_sch", sheet04), ("05_supply.kicad_sch", sheet05)]


def main():
    seen = {}
    for f, fn in SHEETS:
        d = Drawer(f, "collect")
        fn(d)
        for n in d.nets:
            seen.setdefault(n, set()).add(f)
    glob = frozenset(n for n, fs in seen.items() if len(fs) > 1 and n not in POWER)
    for f, fn in SHEETS:
        d = Drawer(f, "draw", glob)
        fn(d)
        d.save()
    single = sorted(n for n, fs in seen.items() if len(fs) == 1)
    os.makedirs(os.path.join(RB, "build"), exist_ok=True)
    json.dump({f"{r}:{p}": n for (r, p), n in sorted(INTENDED.items())},
              open(os.path.join(RB, "build", "intended_nets.json"), "w"), indent=0)
    parts = len({r for r, _ in INTENDED})
    print(f"nets: {len(seen)}, global: {len(glob)}, parts with nets: {parts}")


if __name__ == "__main__":
    main()
