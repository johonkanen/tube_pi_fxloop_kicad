#!/usr/bin/env python3
"""Build lib/tube_pi_fxloop_revb.kicad_sym from KiCad's standard symbol libraries: the symbols the
rev B sheets use, flattened (KiCad's derived 'extends' symbols resolved, since a schematic's
lib_symbols needs them whole); the G6K-2F-Y redrawn to the Omron datasheet; and the placeholder
footprints in lib/tube_pi_fxloop_revb.pretty (the power tabs: no KiCad stock part)."""
import copy
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "..", "tools", "p2k"))
from p2k.sexpr import Sym, find, find_all, load, save  # noqa: E402

KICAD = os.environ.get("KICAD_SYMBOLS", "/mnt/c/Program Files/KiCad/10.0/share/kicad/symbols")
WANT = [
    ("Device", "R"), ("Device", "C"), ("Device", "C_Polarized"), ("Device", "D"), ("Device", "D_Zener"),
    ("Transistor_FET", "Q_NMOS_GDS"), ("Transistor_FET_Other", "DN2540N8-G"), ("Transistor_BJT", "MMBTA42"),
    ("Valve", "ECC83"), ("Transistor_FET", "MMBFJ113"),
    ("Interface_Expansion", "MCP23S17x-x-SS"), ("Transistor_Array", "ULN2803A"),
    ("Analog_Switch", "DG412xY"), ("74xGxx", "74LVC1G11"),
    ("Connector_Generic", "Conn_02x07_Odd_Even"), ("Connector_Generic", "Conn_02x08_Odd_Even"),
    ("Connector_Generic", "Conn_02x05_Odd_Even"), ("Connector_Generic", "Conn_01x05"),
    ("Connector_Generic", "Conn_01x02"), ("Connector_Generic", "Conn_01x03"),
    ("power", "GND"), ("power", "GNDD"), ("power", "+5V"), ("power", "+15V"), ("power", "-15V"), ("power", "PWR_FLAG"),
]
_cache = {}


def library(name):
    if name not in _cache:
        _cache[name] = {s[1]: s for s in find_all(load(os.path.join(KICAD, name + ".kicad_sym")), "symbol")}
    return _cache[name]


def flat(libname, name):
    s = copy.deepcopy(library(libname)[name])
    ext = find(s, "extends")
    if not ext:
        return s
    base = flat(libname, ext[1])
    out = copy.deepcopy(base)
    out[1] = name
    for sub in find_all(out, "symbol"):
        sub[1] = sub[1].replace(ext[1] + "_", name + "_", 1)
    props = {p[1]: p for p in find_all(s, "property")}
    for i, c in enumerate(out):
        if isinstance(c, list) and c and c[0] == "property" and c[1] in props:
            out[i] = props.pop(c[1])
    for p in props.values():
        out.insert(2, p)
    return out


def g6k_2f_y():
    """Relay:G6K-2 redrawn for the Omron G6K-2F-Y datasheet (top view): coil + 1, - 8; pole 1 COM 3,
    NC 4, NO 2; pole 2 COM 6, NC 5, NO 7. KiCad's G6K-2 draws the resting arms on pins 2 and 7 (the
    NO contacts by the datasheet); here the two arms are mirrored onto 4 and 5, so the drawing shows
    the unpowered state truthfully. Pin numbers and positions are unchanged; footprint set."""
    s = flat("Relay", "G6K-2")
    s[1] = "G6K-2F-Y"
    for sub in find_all(s, "symbol"):
        sub[1] = sub[1].replace("G6K-2_", "G6K-2F-Y_", 1)
        for pl in find_all(sub, "polyline"):
            pts = find(pl, "pts")
            xy = [(float(p[1]), float(p[2])) for p in find_all(pts, "xy")]
            if xy == [(0.0, -2.54), (-1.905, 3.81)]:
                find_all(pts, "xy")[1][1] = 1.905
            elif xy == [(10.16, -2.54), (8.255, 3.81)]:
                find_all(pts, "xy")[1][1] = 12.065
    for p in find_all(s, "property"):
        if p[1] == "Footprint":
            p[2] = "Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y"
        elif p[1] == "Value":
            p[2] = "G6K-2F-Y"
    return s


def tab_footprint(width, gap):
    """PLACEHOLDER (no KiCad stock part): two PCB blade tabs (interfaces.md 4.1: 2 legs on 5.00 mm,
    1.4 mm drill), pad 1 = tab 1, pad 2 = tab 2, tabs `gap` mm apart. Replace with the chosen tab's
    drawing (BTC-3 class) before layout."""
    name = f"PLACEHOLDER_Tab_x2_{width}mm_Legs_P5.00mm_D1.4mm"
    L = [f'(footprint "{name}"', '\t(version 20241229)', '\t(generator "make_lib")', '\t(layer "F.Cu")',
         f'\t(descr "PLACEHOLDER: 2x {width} mm PCB blade tab, 2 legs on 5.00 mm, 1.4 mm drill, {gap} mm apart. '
         'Replace with the chosen part before layout.")', '\t(attr through_hole)',
         '\t(property "Reference" "REF**" (at 0 -4 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         f'\t(property "Value" "{name}" (at 0 4 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
         '\t(fp_text user "PLACEHOLDER" (at 0 6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    for n, x in ((1, -gap / 2), (2, gap / 2)):
        L.append(f'\t(fp_rect (start {x - width / 2 - 0.5:.2f} -1.2) (end {x + width / 2 + 0.5:.2f} 1.2) '
                 '(stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS"))')
        for dx in (-2.5, 2.5):
            L.append(f'\t(pad "{n}" thru_hole circle (at {x + dx:.2f} 0) (size 2.6 2.6) (drill 1.4) '
                     '(layers "*.Cu" "*.Mask"))')
    L.append(')')
    return name, "\n".join(L) + "\n"


def main():
    pretty = os.path.join(HERE, "lib", "tube_pi_fxloop_revb.pretty")
    os.makedirs(pretty, exist_ok=True)
    for w, gap in ((4.8, 10.0), (6.3, 12.0)):
        name, text = tab_footprint(w, gap)
        open(os.path.join(pretty, name + ".kicad_mod"), "w").write(text)
    lib = [Sym("kicad_symbol_lib"), [Sym("version"), 20251024], [Sym("generator"), "make_lib"],
           [Sym("generator_version"), "10.0"]]
    for libname, name in WANT:
        lib.append(flat(libname, name))
    lib.append(g6k_2f_y())
    save(os.path.join(HERE, "lib", "tube_pi_fxloop_revb.kicad_sym"), lib)
    for libname, name in WANT:
        s = flat(libname, name)
        pins = []
        for sub in find_all(s, "symbol"):
            for p in find_all(sub, "pin"):
                num, nm = find(p, "number"), find(p, "name")
                pins.append(f"{num[1]}={nm[1]}" if num and nm else "?")
        print(f"{name}: " + " ".join(pins))


if __name__ == "__main__":
    main()
