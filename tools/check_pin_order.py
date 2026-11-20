#!/usr/bin/env python3
"""Pin-order check: the UNMOVED KiCad base footprints with the Proteus renumbering, fitted onto
the IPC pads (playbook Phase 2, step 2). A small residual confirms that the Proteus pin ids sit on
the pads the renumbering says; a residual of a pad pitch or more means the ids are on other pads.

Inline and two-pad parts always fit (a 180 deg turn reverses the pad order), so for them the
orientation of the body marker decides: the fitted KiCad graphics (band, flat side, tab, '+',
pin-1 pad) are drawn over the Proteus silk with --render (reports/pin_order/<refdes>.png) and
were compared by eye (STATUS.md "Phase 2 - pin order").

For the noval sockets (U4, U5) the KiCad footprint (Valve:Valve_Noval_P) is a smaller circle
than the Proteus 21.0 mm pitch circle, so the residual is never small; the chirality test compares
the unmirrored fit (KiCad = standard noval numbering, clockwise seen from the pin side = solder
side of a top-mounted socket) with the mirrored one, fits an ideal standard noval on the Proteus
pitch circle (free rotation: the noval steps are 36 deg) and prints the sense of pins 1 -> 9.

The relay SERIES_MIX: since the design fixes 2026-11-20 (user decision, Finding 15) its IPC pin ids
are the physical Omron pins (p2k_config.py IPC_PIN_IDS, tools/ipc356.py), so the UNMOVED KiCad G5V-2
footprint without renumbering must fit unmirrored; the old Proteus-pole mapping (Omron pole 1 on the
Proteus pole, = the Phase 2 symbol) must still fit only mirrored (Finding 15: G5V-2(HI) is the mirror
image), which also proves that IPC_PIN_IDS is the physical and not the mirrored mapping.

Phase 5 (user decision 2026-11-20: the noval sockets are on the BOTTOM side, as the power amp
pilot's octal sockets): the project footprint tube_pi_fxloop:Valve_Noval_Belton_PCD21.00mm has the
standard noval numbering in its own view (fits the ideal standard noval unmirrored, not mirrored),
fits the IPC pads of U4 / U5 only mirrored (so check_footprints places it on the bottom),
reports/footprint_fit.csv has U4 / U5 on the bottom and every other part on top, and the board
(P2K_PCB overrides) has U4 / U5 on B.Cu and every other footprint on F.Cu (bottom_side_noval).

Adapted from the power amp pilot's tools/check_pin_order.py (octal -> noval, relay, SW-SPDT).

Usage: tools/p2k/bin/kipy tools/check_pin_order.py [--render]   (python3 works without --render;
       --render needs matplotlib, e.g. the system python3)
Exit 1 when a result differs from EXPECT (so a changed footprint or renumbering is noticed).
"""
import csv
import glob
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "p2k"))
os.chdir(ROOT)
from p2k import fpgeom, pcb, sexpr  # noqa: E402
from p2k.footprints import footprint_path  # noqa: E402

# refdes group -> (KiCad base footprint, renumbering of the base pads to the IPC pin ids of reference/)
# SERIES_MIX: the IPC ids are Omron ids (IPC_PIN_IDS). The Phase 2 symbol mapping (Omron pole 1 on the
# Proteus pole 1-8), expressed in today's Omron ids: Omron k -> the Omron id of the Proteus pad that
# mapping put k on (Proteus 1-8 = Omron 9 13 11 16 1 4 6 8).
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True
import p2k_config  # noqa: E402
_OMRON = p2k_config.IPC_PIN_IDS["SERIES_MIX"]
G5V2_POLE1 = {o: _OMRON[p] for o, p in {"8": "1", "4": "2", "6": "3", "1": "4", "16": "5", "13": "6",
                                         "11": "7", "9": "8"}.items()}
from gen_footprints import PROJECT  # noqa: E402
CHECKS = [
    ("Q4", "Package_TO_SOT_THT:TO-220-3_Vertical", {}),
    ("Q8 Q10 Q20 Q90", "Package_TO_SOT_THT:TO-92_Inline_Wide", {}),
    ("Q1 Q2 Q3 Q5 Q6 Q7", "Package_TO_SOT_THT:TO-92_Inline_Wide", {}),
    ("D2 D7 D8 D9 D10 D11 D12", "Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal", {"1": "K", "2": "A"}),
    ("D1 D3 D4 D5 D6", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", {"1": "K", "2": "A"}),
    ("C8 C28", "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm", {"1": "+", "2": "-"}),
    ("C1 C36 C37", "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm", {"1": "2", "2": "1"}),
    ("SERIES_MIX", "Relay_THT:Relay_DPDT_Omron_G5V-2", {}),
    ("SERIES_MIX ", "Relay_THT:Relay_DPDT_Omron_G5V-2", G5V2_POLE1),
    ("U4 U5", "Valve:Valve_Noval_P", {}),
]
# expected best fit per group: (mirror, residual upper bound mm)
EXPECT = {
    "Q4": (False, 0.01),
    "Q8 Q10 Q20 Q90": (False, 0.51),       # TO-92_Inline_Wide is P2.54, Proteus P2.032: 0.508 at the outer pads
    "Q1 Q2 Q3 Q5 Q6 Q7": (False, 0.51),
    "D2 D7 D8 D9 D10 D11 D12": (False, 0.01),
    "D1 D3 D4 D5 D6": (False, 0.01),
    "C8 C28": (False, 0.03),               # P2.50 vs P2.54
    "C1 C36 C37": (False, 0.01),           # pad 2 = + = KiCad pad 1
    "SERIES_MIX": (False, 0.01),           # Omron ids (IPC_PIN_IDS) on the unmoved KiCad G5V-2: unmirrored
    "SERIES_MIX ": (True, 0.01),           # the Phase 2 Proteus-pole mapping (pole 1) fits only MIRRORED
    "U4 U5": (True, 3.0),                  # KiCad Noval_P is a smaller circle; only the MIRRORED one is near
}
NOVAL = "tube_pi_fxloop:Valve_Noval_Belton_PCD21.00mm"
NOVALS = ["U4", "U5"]
NOVAL_PCD = 21.0      # Proteus 9-PIN BELTON NOVAL pitch circle (U4 / U5: r = 10.499-10.503 mm)


def base_pads(fpid, ren):
    pads = fpgeom.load_footprint(footprint_path(fpid))
    out = []
    for p in pads:
        if p["num"] == "":
            continue   # unnumbered pads (centre holes)
        q = dict(p)
        q["num"] = ren.get(p["num"], p["num"])
        out.append(q)
    return out


def ideal_noval(r=NOVAL_PCD / 2):
    """Standard noval numbering in KiCad's top view (Y up): 10 positions 36 deg apart, pins 1-9
    counter-clockwise seen from the top, i.e. clockwise seen from the pin / solder side of a
    top-mounted socket; the gap (10th position) between 9 and 1."""
    return [{"num": str(k + 1), "x": r * math.cos(math.radians(-36 + 36 * k)),
             "y": r * math.sin(math.radians(-36 + 36 * k)), "w": 4.318, "h": 4.318, "rot": 0.0, "drill": 1.727,
             "kind": "thru_hole", "shape": "circle"} for k in range(9)]


def free_fit(fp, ipc_pads, mirror):
    """Rigid fit WITHOUT the 45 deg rotation snap of fpgeom.fit (the noval steps are 36 deg):
    least-squares rotation, max residual (mm)."""
    m = -1.0 if mirror else 1.0
    q = {p["pin"]: (p["x_mm"], p["y_mm"]) for p in ipc_pads}
    pairs = [((m * f["x"], f["y"]), q[f["num"]]) for f in fp]
    n = len(pairs)
    pcx, pcy = sum(a[0] for a, _ in pairs) / n, sum(a[1] for a, _ in pairs) / n
    qcx, qcy = sum(b[0] for _, b in pairs) / n, sum(b[1] for _, b in pairs) / n
    s = c = 0.0
    for (px, py), (qx, qy) in pairs:
        px, py, qx, qy = px - pcx, py - pcy, qx - qcx, qy - qcy
        c += px * qx + py * qy
        s += px * qy - py * qx
    a = math.atan2(s, c)
    ca, sa = math.cos(a), math.sin(a)
    res = [math.hypot(qcx + ca * (px - pcx) - sa * (py - pcy) - qx, qcy + sa * (px - pcx) + ca * (py - pcy) - qy)
           for (px, py), (qx, qy) in pairs]
    return max(res), math.degrees(a)


def turn_direction(ipc_pads):
    """'clockwise' / 'counter-clockwise': the sense of pins 1 -> 9 around the socket centre, seen
    from the top (component) side, IPC frame Y up."""
    pts = {int(p["pin"]): (p["x_mm"], p["y_mm"]) for p in ipc_pads}
    cx = sum(x for x, _ in pts.values()) / len(pts)
    cy = sum(y for _, y in pts.values()) / len(pts)
    tot = 0.0
    for k in range(1, 9):
        a0 = math.atan2(pts[k][1] - cy, pts[k][0] - cx)
        a1 = math.atan2(pts[k + 1][1] - cy, pts[k + 1][0] - cx)
        tot += (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return "counter-clockwise" if tot > 0 else "clockwise"


def graphics(fpid):
    """F.SilkS / F.Fab polylines of a footprint (footprint frame, Y up)."""
    node = sexpr.load(footprint_path(fpid))
    lines = []

    def xy(n):
        return float(n[1]), -float(n[2])
    for g in node:
        if not isinstance(g, list) or not g or str(g[0]) not in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
            continue
        layer = sexpr.find(g, "layer")
        if layer is None or layer[1] not in ("F.SilkS", "F.Fab"):
            continue
        kind = str(g[0])
        if kind == "fp_line":
            lines.append([xy(sexpr.find(g, "start")), xy(sexpr.find(g, "end"))])
        elif kind == "fp_rect":
            (x0, y0), (x1, y1) = xy(sexpr.find(g, "start")), xy(sexpr.find(g, "end"))
            lines.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
        elif kind == "fp_circle":
            (cx, cy), (ex, ey) = xy(sexpr.find(g, "center")), xy(sexpr.find(g, "end"))
            r = math.hypot(ex - cx, ey - cy)
            lines.append([(cx + r * math.cos(t / 20 * math.pi), cy + r * math.sin(t / 20 * math.pi)) for t in range(41)])
        elif kind == "fp_arc":
            a, m, b = xy(sexpr.find(g, "start")), xy(sexpr.find(g, "mid")), xy(sexpr.find(g, "end"))
            lines.append(_arc(a, m, b))
        else:
            pts = [xy(p) for p in sexpr.find(g, "pts")[1:]]
            lines.append(pts + pts[:1])
    return lines


def _arc(a, m, b):
    ax, ay = a
    bx, by = m
    cx, cy = b
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [a, m, b]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    t0, tm, t1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (a, m, b))

    def ccw(s, e):
        return (e - s) % (2 * math.pi)
    if ccw(t0, tm) <= ccw(t0, t1):
        span = ccw(t0, t1)
    else:
        span = -ccw(t1, t0)
    return [(ux + r * math.cos(t0 + span * k / 24), uy + r * math.sin(t0 + span * k / 24)) for k in range(25)]


def to_board(fr, x, y):
    a = math.radians(fr["angle"])
    x = -x if fr["mirror"] else x
    return fr["tx"] + math.cos(a) * x - math.sin(a) * y, fr["ty"] + math.sin(a) * x + math.cos(a) * y


def render(ref, fpid, fr, ipc_pads, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    from p2k import gerber
    silk = gerber.parse(glob.glob("source/cadcam/*Top Silk Screen.GBR")[0]).of(gerber.Draw)
    xs = [p["x_mm"] for p in ipc_pads]
    ys = [p["y_mm"] for p in ipc_pads]
    m = 16 if len(ipc_pads) >= 8 else 8
    box = (min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m)
    fig, ax = plt.subplots(figsize=(6, 6))
    for d in silk:
        if box[0] <= d.x1 <= box[1] and box[2] <= d.y1 <= box[3]:
            ax.plot([d.x1, d.x2], [d.y1, d.y2], color="k", lw=1.0)
    for p in ipc_pads:
        ax.add_patch(Circle((p["x_mm"], p["y_mm"]), p["pad_w"] / 2, color="orange", alpha=0.6))
        ax.text(p["x_mm"], p["y_mm"], p["pin"], ha="center", va="center", fontsize=9, color="b")
    for line in graphics(fpid):
        pts = [to_board(fr, x, y) for x, y in line]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="r", lw=0.8)
    for num, f, q, _ in fr["pads"]:
        bx, by = to_board(fr, f["x"], f["y"])
        ax.add_patch(Circle((bx, by), 0.35, color="r"))
        if f is fr["pads"][0][1] or num in ("1", "K", "+"):
            ax.text(bx + 0.6, by + 0.6, f"KiCad {num}", fontsize=7, color="r")
    ax.set_title(f"{ref}: black = Proteus silk, orange = IPC pads (pin ids)\n"
                 f"red = unmoved {fpid.split(':')[1]} fitted ({'mirrored, ' if fr['mirror'] else ''}"
                 f"{fr['angle']:g} deg, res {fr['max_res']:.3f} mm)", fontsize=7)
    ax.set_aspect("equal")
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[3])
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)


def bottom_side_noval(ipc):
    """Phase 5: the noval footprint is the standard noval and U4 / U5 are on the bottom side. Free
    rotation fits (free_fit): the noval steps are 36 deg, fpgeom.fit snaps to 45 deg."""
    bad = []
    fp = [p for p in fpgeom.load_footprint(footprint_path(NOVAL)) if p["num"]]
    target = [dict(p, pin=p["num"], x_mm=p["x"], y_mm=p["y"]) for p in ideal_noval()]   # as IPC pads
    ideal = {m: free_fit(fp, target, m)[0] for m in (False, True)}
    on_ipc = {m: max(free_fit(fp, ipc[r], m)[0] for r in NOVALS) for m in (False, True)}
    name = NOVAL.split(":")[1]
    print(f"{'(footprint)':16s} {name + ' vs ideal noval':44s} {ideal[False]:7.3f}{'':11s} "
          f"{ideal[True]:7.3f}{'':11s}  {'unmirrored' if ideal[False] < ideal[True] else 'mirrored'}")
    print(f"{'U4 U5':16s} {name + ' (project)':44s} {on_ipc[False]:7.3f}{'':11s} "
          f"{on_ipc[True]:7.3f}{'':11s}  {'mirrored = bottom side' if on_ipc[True] < on_ipc[False] else 'unmirrored'}")
    if not (ideal[False] < 0.01 < 1.0 < ideal[True]):
        bad.append(f"{name}: expected the standard noval numbering in the footprint's own view")
    if not (on_ipc[True] < 0.01 and on_ipc[False] > 1.0):
        bad.append(f"{name}: expected to fit the IPC pads only mirrored (bottom side)")
    with open("reports/footprint_fit.csv") as f:
        rows = list(csv.DictReader(l for l in f if not l.startswith("# ")))
    wrong = [r["refdes"] for r in rows if (r["side"] == "bottom") != (r["refdes"] in NOVALS)]
    if wrong:
        bad.append(f"reports/footprint_fit.csv: wrong side for {wrong} (bottom = exactly {NOVALS})")
    layers = {}
    BOARD = os.path.relpath(pcb.board_file())   # kicad/tube_pi_fxloop.kicad_pcb (P2K_PCB overrides)
    for node in sexpr.find_all(sexpr.load(BOARD), "footprint"):
        ref = next((p[2] for p in sexpr.find_all(node, "property") if p[1] == "Reference"), "")
        layers[ref] = sexpr.find(node, "layer")[1]
    wrong = sorted(r for r, l in layers.items() if l != ("B.Cu" if r in NOVALS else "F.Cu"))
    if wrong or not set(NOVALS) <= set(layers):
        bad.append(f"{BOARD}: wrong layer for {wrong or NOVALS} (B.Cu = exactly {NOVALS})")
    else:
        print(f"{'':16s} footprint_fit.csv and board: U4 U5 bottom (B.Cu), the other {len(layers) - 2} footprints top")
    return bad


def main():
    do_render = "--render" in sys.argv[1:]
    ipc = fpgeom.ipc_pads_by_refdes()
    bad = []
    # the renumbering checked here must be the one the derived project footprints use
    for refs, fpid, ren in CHECKS:
        for name, spec in PROJECT.items():
            if spec.get("base") == fpid and spec.get("renumber", {}) != ren and refs != "SERIES_MIX ":
                bad.append(f"{refs}: renumbering {ren} differs from gen_footprints {name} {spec.get('renumber', {})}")
    print(f"{'parts':16s} {'KiCad base (unmoved)':44s} {'unmirrored':>18s} {'mirrored':>18s}  best")
    for refs, fpid, ren in CHECKS:
        fp = base_pads(fpid, ren)
        worst = {False: (0.0, None), True: (0.0, None)}
        for ref in refs.split():
            for mir in (False, True):
                r = fpgeom.fit(fp, ipc[ref], mir)
                if r["missing"] or r["extra"] or r["count_diff"]:
                    bad.append(f"{ref}: pad numbers differ from {fpid}: {r['missing']} {r['extra']} {r['count_diff']}")
                if worst[mir][1] is None or r["max_res"] > worst[mir][0]:
                    worst[mir] = (r["max_res"], r)
            if do_render:
                os.makedirs("reports/pin_order", exist_ok=True)
                best = min((fpgeom.fit(fp, ipc[ref], m) for m in (False, True)), key=lambda r: r["max_res"])
                render(ref, fpid, best, ipc[ref], f"reports/pin_order/{ref}.png")
        u, m = worst[False], worst[True]
        best = u[0] <= m[0]
        best_mir = not best
        cell = lambda w: f"{w[0]:7.3f} @{w[1]['angle']:5g}"  # noqa: E731
        print(f"{refs:16s} {fpid:44s} {cell(u):>18s} {cell(m):>18s}  {'mirrored' if best_mir else 'unmirrored'}")
        want_mir, lim = EXPECT[refs]
        res = m[0] if best_mir else u[0]
        if best_mir != want_mir or res > lim:
            bad.append(f"{refs}: best fit {'mirrored' if best_mir else 'unmirrored'} {res:.3f} mm, expected "
                       f"{'mirrored' if want_mir else 'unmirrored'} <= {lim}")
    # ideal standard noval on the Proteus pitch circle (free rotation)
    nov = {mir: max(free_fit(ideal_noval(), ipc[r], mir)[0] for r in ("U4", "U5")) for mir in (False, True)}
    print(f"{'U4 U5':16s} {'ideal standard noval, PCD 21.00 mm (free rot.)':44s} {nov[False]:7.3f}{'':11s} "
          f"{nov[True]:7.3f}{'':11s}  {'mirrored' if nov[True] < nov[False] else 'unmirrored'}")
    if not (nov[True] < 0.01 and nov[False] > 1.0):
        bad.append("ideal noval: expected only the mirrored standard noval to fit")
    for r in ("U4", "U5"):
        d = turn_direction(ipc[r])
        print(f"{r}: pins 1 -> 9 run {d} seen from the top side (noval standard: counter-clockwise from the top)")
        if d != "clockwise":
            bad.append(f"{r}: pins 1 -> 9 expected clockwise seen from the top (as recorded)")
    # SW-SPDT (built from the IPC pads, no KiCad base): COM = 3 is the offset hole, NO = 1 / NC = 2
    # the two holes 5.08 mm apart (positions as recorded; nets checked by the netlist comparison)
    for r in ("SW4", "SW5", "SW6"):
        q = {p["pin"]: (p["x_mm"], p["y_mm"]) for p in ipc[r]}
        d12 = math.dist(q["1"], q["2"])
        d13, d23 = math.dist(q["1"], q["3"]), math.dist(q["2"], q["3"])
        if abs(d12 - 5.08) > 0.01 or abs(d13 - d23) > 0.01 or abs(d13 - 5.12) > 0.01:
            bad.append(f"{r}: hole pattern differs (1-2 {d12:.3f}, 1-3 {d13:.3f}, 2-3 {d23:.3f} mm)")
    print("SW4 SW5 SW6: 1 (NO) and 2 (NC) 5.08 mm apart, 3 (COM) the offset hole 5.12 mm from both")
    bad += bottom_side_noval(ipc)
    for b in bad:
        print("check_pin_order: ERROR " + b)
    print("check_pin_order: " + ("FAILED" if bad else "OK (results as recorded in STATUS.md)"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
