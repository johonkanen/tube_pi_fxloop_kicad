#!/usr/bin/env python3
"""Build lib/tube_pi_fxloop_revb.kicad_sym from KiCad's standard symbol libraries: the symbols the
rev B sheets use, flattened (KiCad's derived 'extends' symbols resolved, since a schematic's
lib_symbols needs them whole); the G6K-2F-Y redrawn to the Omron datasheet; and the local
footprints in lib/tube_pi_fxloop_revb.pretty (the power tabs: no KiCad stock part; rev A's noval socket)."""
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
    ("Connector_Generic", "Conn_02x05_Odd_Even"), ("Connector_Generic", "Conn_01x05"), ("Connector_Generic", "Conn_02x03_Top_Bottom"),
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


def faston(width, n, pitch):
    """PCB blade (Faston) tabs, as the preamp rev B's make_footprints.py (tube_preamp_kicad rev_b,
    same footprint, same name): n tabs of the given width side by side along x at `pitch`, one pad
    number per tab (both legs), legs on 5.00 mm along the blade, 1.4 mm drill, 2.8 mm pads
    (interfaces.md 4.1); the courtyard leaves room for an insulated push-on receptacle."""
    def rect(x0, y0, x1, y1, layer, w):
        pts = ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0))
        return "".join(f'\t(fp_line (start {a:.3f} {b:.3f}) (end {c:.3f} {d:.3f})\n'
                       f'\t\t(stroke (width {w}) (type solid)) (layer "{layer}"))\n' for a, b, c, d in pts)
    name = f"Faston_Tab_{width}mm_x{n}_P{pitch:.2f}mm"
    s = (f'(footprint "{name}"\n\t(version 20241229)\n\t(generator "make_lib")\n\t(layer "F.Cu")\n'
         f'\t(descr "PCB blade (Faston) tab {width} mm, 2 legs on 5.00 mm, 1.4 mm drill (interfaces.md 4.1); {n} tab(s)")\n'
         '\t(tags "faston quick connect blade tab")\n'
         '\t(property "Reference" "REF**" (at 0.000 -7.200 0) (layer "F.SilkS")\n\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
         f'\t(property "Value" "{name}" (at 0.000 7.500 0) (layer "F.Fab")\n\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
         '\t(attr through_hole)\n')
    for i in range(n):
        x = i * pitch
        s += rect(x - 0.4, -width / 2, x + 0.4, width / 2, "F.Fab", 0.1)
        s += rect(x - 4.1, -5.85, x + 4.1, 5.85, "F.SilkS", 0.12)
        s += rect(x - 4.25, -6.0, x + 4.25, 6.0, "F.CrtYd", 0.05)
        for y in (-2.5, 2.5):
            s += (f'\t(pad "{i + 1}" thru_hole circle (at {x:.3f} {y:.3f}) (size 2.8 2.8) (drill 1.4)\n'
                  '\t\t(layers "*.Cu" "*.Mask"))\n')
    s += '\t(fp_text user "1" (at -3.0 0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n)\n'
    return name, s


BELTON = os.path.join(HERE, "..", "lib", "tube_pi_fxloop.pretty", "Valve_Noval_Belton_PCD21.00mm.kicad_mod")


def main():
    pretty = os.path.join(HERE, "lib", "tube_pi_fxloop_revb.pretty")
    os.makedirs(pretty, exist_ok=True)
    for f in os.listdir(pretty):
        if f.startswith("PLACEHOLDER_"):
            os.remove(os.path.join(pretty, f))
    for w, pitch in ((4.8, 15.0), (6.3, 12.7)):
        name, text = faston(w, 2, pitch)
        open(os.path.join(pretty, name + ".kicad_mod"), "w").write(text)
    # rev A's noval socket (matches the chassis holes), copied unchanged from the frozen rev A library
    open(os.path.join(pretty, "Valve_Noval_Belton_PCD21.00mm.kicad_mod"), "w").write(open(BELTON).read())
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
