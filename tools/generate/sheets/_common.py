"""Helpers for the per-sheet transcription scripts (tools/sheets/sheetNN.py).

Copied from the power amp pilot (term, P) and adapted; mirrored symbols are p2k Sheet.place(mirror=).

The generic helpers come from p2k.sheetkit (grid g(), sheet(), left/right/up/down,
glabel_*/label_*, power_at, bus_group, flagged_power, vert2, horiz2, terminal); board helpers
below. Each sheet script starts with
    from _common import *  # noqa: F401,F403
"""
import csv
import os
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/generate/sheets/ -> tools
sys.path.insert(0, os.path.join(TOOLS, "p2k"))  # proteus2kicad
from p2k.sch_builder import Sheet  # noqa: E402,F401
from p2k.sheetkit import *  # noqa: E402,F401,F403

_PART_MAP = None


def part(ref):
    """Row of lib/part_map.csv for a KiCad refdes (keys refdes, sheet, lib_id, value, ...)."""
    global _PART_MAP
    if _PART_MAP is None:
        with open(os.path.join(os.path.dirname(TOOLS), "lib", "part_map.csv"), newline="", encoding="utf-8") as f:
            _PART_MAP = {r["refdes"]: r for r in csv.DictReader(l for l in f if not l.startswith("#"))}
    return _PART_MAP[ref]


def sh_value(ref):
    """Value of a refdes from lib/part_map.csv."""
    return part(ref)["value"]


def sym(ref):
    """Symbol name (lib_id without the library nickname) of a refdes from lib/part_map.csv."""
    return part(ref)["lib_id"].partition(":")[2]


def term(sh, ref, x, y, direction="up"):
    """Proteus TERMINAL / PIN part (connection point (x, y), circle pointing in `direction`, texts
    horizontal beside the circle, away from the wire) with the symbol and value of the part map."""
    return terminal(sh, ref, x, y, direction, symbol=sym(ref), value=sh_value(ref), justify="away")


# --- PDF coordinates ---------------------------------------------------------------------------------
# The Proteus PDF pages rendered at 200 dpi (build/tmp/pdf/hi-N.png) have 0.127 mm pixels, so
# 10 px = one 1.27 mm grid unit. P(px/10, py/10) puts a point of the render on the A3 KiCad sheet
# (same scale, shifted by OX/OY grid units), which keeps the layout close to the PDF.
OX, OY = 40, 30


def P(x, y):
    """Sheet point (mm, on the 1.27 mm grid) of PDF render position (x, y) in units of 10 px."""
    return (g(x + OX), g(y + OY))


# --- noval dual triodes (U4, U5) ----------------------------------------------------------------
def noval(sh, ref, a, b, heater, mirror_b=False):
    """Place the three units of a 12AX7 symbol: unit 1 = triode 2 (pins 6 A2, 7 G2, 8 K2) at `a`,
    unit 2 = triode 1 (pins 1 A1, 2 G1, 3 K1) at `b`, unit 3 = heater (4 H1, 5 H2, 9 HCT) at `heater`
    (points (x, y) in mm), with a no-connect flag on pin 9 (N/C in Proteus). mirror_b draws unit 2
    mirrored about the Y axis (grid and cathode on the right, as the Proteus symbol's right triode).
    Returns the three placed units (u1, u2, u3); wire the pins with u.pin(n)."""
    val = sh_value(ref)
    u1 = sh.place(sym(ref), ref, *a, unit=1, value=val)
    if mirror_b:
        bx, by = b
        u2 = sh.place(sym(ref), ref, bx, by, 0, mirror="y", unit=2, value=val,
                      ref_at=(round(bx + 3.81, 4), round(by - 7.62, 4), 0, "right"),
                      value_at=(round(bx + 3.81, 4), round(by - 5.715, 4), 0, "right"))
    else:
        u2 = sh.place(sym(ref), ref, *b, unit=2, value=val)
    u3 = sh.place(sym(ref), ref, *heater, unit=3, value=val)
    sh.no_connect(*u3.pin("9"))
    return u1, u2, u3


# --- two-pin parts from the part map, junctions ---------------------------------------------------
def pv(sh, ref, x, y, top, **kw):
    """Vertical two-pin part `ref` (symbol and value from the part map) centred on PDF position
    (x, y), pin `top` at the top. Returns (top_point, bottom_point)."""
    _, t, b = vert2(sh, sym(ref), ref, *P(x, y), sh_value(ref), top=top, **kw)
    return t, b


def ph(sh, ref, x, y, left, **kw):
    """Horizontal two-pin part `ref` centred on PDF position (x, y), pin `left` on the left.
    Returns (left_point, right_point)."""
    kw.setdefault("text", "above")
    if sym(ref).startswith("C"):      # capacitor plates are taller than a resistor body
        kw.setdefault("text_gap", 3.175)
    _, l, r = horiz2(sh, sym(ref), ref, *P(x, y), sh_value(ref), left=left, **kw)
    return l, r


def junctions(sh, *pts):
    for p in pts:
        sh.junction(*p)


# --- transistors with the base / gate on the right (2N3906, J112 as the PDF draws them) ----------
def q_right(sh, ref, x, y, axis="y"):
    """Transistor `ref` centred on PDF position (x, y), mirrored about the Y axis (base / gate on the
    right), texts right of the body above / below the base lead. Returns the placed symbol."""
    px, py = P(x, y)
    return sh.place(sym(ref), ref, px, py, 0, mirror=axis, value=sh_value(ref),
                    ref_at=(round(px + 1.27, 4), round(py - 3.81, 4), 0, "right"),
                    value_at=(round(px + 1.27, 4), round(py + 3.81, 4), 0, "right"))


# --- sheet 4: JFET send channel, RETURN switch block -------------------------------------------------
def send_channel(sh, x0, y, rw, rs, qa, qb, gate, wiper, send, xg, yg, yl, gnd):
    """One FX send channel: wiper terminal - rw - node 1 (drain of qa) - rs - node 2 (drain of qb,
    send terminal); both J112 sources on the ground row `gnd`, both gates on the global net `gate`
    (label at (xg, yl), the gate of qa joins the gate column at row yg). x0 = column of node 1,
    y = resistor row; wiper / send = (refdes, x, y, direction) of the terminals (PDF positions)."""
    l1, r1 = ph(sh, rw, x0 - 7, y, left=2)
    l2, r2 = ph(sh, rs, x0 + 7, y, left=2)
    sh.wire(r1, l2)
    x1 = x0 + 16
    wref, wx, wy, wdir = wiper
    term(sh, wref, *P(wx, wy), wdir)
    sh.wire(P(wx, wy), P(wx, y), l1)
    sref, sx, sy, sdir = send
    term(sh, sref, *P(sx, sy), sdir)
    sh.wire(r2, P(x1, y)) if (sx, sy) == (x1, y) else sh.wire(r2, P(sx, y), P(sx, sy))
    a = q_right(sh, qa, x0 + 2, y + 16)
    b = q_right(sh, qb, x1 + 2, y + 16)
    sh.wire(P(x0, y), a.pin(1))
    sh.wire(P(x1, y), b.pin(1))
    sh.junction(*P(x0, y))
    if sx != x1 or sdir != "up":
        sh.junction(*P(x1, y))
    sh.wire(a.pin(2), P(x0, gnd))
    sh.wire(b.pin(2), P(x1, gnd))
    sh.wire(a.pin(3), P(x0 + 12, y + 16), P(x0 + 12, yg), P(xg, yg))
    sh.wire(b.pin(3), P(xg, y + 16), P(xg, yl))
    sh.junction(*P(xg, yg))
    sh.glabel(gate, *P(xg, yl), 270)


def return_block(sh, x, y, ret, r_ret, sw, r_nolla, xbus):
    """One FX return input: terminal `ret` at PDF position (x, y) - r_ret - node (switch common,
    pin 3) - r_nolla - NOLLA bus column xbus; the switch's NC contact (pin 2) on the terminal, the NO
    contact (pin 1) on the bus."""
    term(sh, ret, *P(x, y), "left")
    l1, r1 = ph(sh, r_ret, x + 17, y, left=2)
    l2, r2 = ph(sh, r_nolla, x + 33, y, left=2)
    sh.wire(P(x, y), l1)
    sh.wire(r1, l2)
    sh.wire(r2, P(xbus, y))
    sx, sy = P(x + 26, y - 4)
    s = sh.place(sym(sw), sw, sx, sy, 90, value=sh_value(sw),
                 ref_at=(round(sx + 3.81, 4), round(sy - 6.35, 4), 270, "left"),
                 value_at=(round(sx + 3.81, 4), round(sy - 4.445, 4), 270, "left"))
    assert s.pin(3) == P(x + 26, y), s.pins
    sh.wire(s.pin(2), (s.pin(2)[0], P(0, y - 12)[1]), P(x + 10, y - 12), P(x + 10, y))
    sh.wire(s.pin(1), (s.pin(1)[0], P(0, y - 12)[1]), P(xbus, y - 12))
    junctions(sh, P(x + 10, y), P(x + 26, y))


def diode_input(sh, y, d, t, xbus):
    """Sheet 2: one input of the diode OR onto the bus column xbus (cathode on the bus, terminal on
    the anode)."""
    k, a = ph(sh, d, xbus + 5, y, left="K")
    sh.wire(P(xbus, y), k)
    term(sh, t, *P(xbus + 18, y), "right")
    sh.wire(a, P(xbus + 18, y))

