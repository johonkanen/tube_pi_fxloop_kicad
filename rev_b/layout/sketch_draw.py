#!/usr/bin/env python3
"""Layout sketch, step 2: draw rev_b/docs/layout_sketch.png from placement.py and the geometry that
sketch_geom.py wrote (rev_b/build/layout/sketch_geom.json). Plain python3 + matplotlib.

    tools/p2k/bin/kipy rev_b/layout/sketch_geom.py && python3 rev_b/layout/sketch_draw.py

A: the chassis under the plate (plan, seen from above) with every cable that leaves the board.
B: the board (plan, seen from above = solder side; parts hang below): zones, connectors with pin 1,
   holes with keep-outs, the heater pair, the neighbours' edges.
C / D: sections (y against depth below the plate) at x 175 (W23) and x 247 (W32 entering J304).
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                     # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle             # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import placement as P  # noqa: E402

G = json.load(open(os.path.join(RB, "build", "layout", "sketch_geom.json")))
OUT = os.path.join(RB, "docs", "layout_sketch.png")

CABLE_COL = {"W23": "#1f77b4", "W30": "#2ca02c", "W31": "#2ca02c", "W32": "#2ca02c", "W13": "#9467bd",
             "W22": "#d62728", "W24": "#ff7f0e", "W25": "#8c564b", "W03": "#e41a1c", "W07": "#bcbd22",
             "W08": "#bcbd22", "ETH": "#7f7f7f"}
# plan routes (chassis x, y) and the length estimate (3D, drops and folds included), metres
ROUTES = [
    ("W23", [(175.0, 161.8), (175.0, 179.7)], "W23 0.08-0.09 m, 1 bend, 0 folds"),
    ("W30", [(393.0, 29.8), (390.0, 34.0), (390.0, 94.0), (203.4, 94.0), (203.4, 108.0)], "W30 CL 0.28 m"),
    ("W31", [(405.0, 29.8), (393.5, 36.0), (393.5, 96.5), (225.4, 96.5), (225.4, 108.0)], "W31 CR 0.26 m"),
    ("W32", [(417.0, 29.8), (397.0, 38.0), (397.0, 99.0), (247.4, 99.0), (247.4, 108.0)], "W32 LD 0.24 m"),
    ("W13", [(431.0, 90.8), (413.0, 90.8), (413.0, 117.2), (274.0, 117.2), (264.2, 117.2)], "W13 0.30 m, 2 folds"),
    ("W22", [(330.5, 84.0), (330.5, 106.0), (140.0, 106.0), (133.5, 140.0)], "W22 0.30 m shielded"),
    ("W24", [(269.0, 154.6), (292.0, 150.0)], "W24 ~0.15 m (J105 proposed)"),
    ("W25", [(415.5, 90.1), (405.0, 122.0), (280.0, 123.0), (272.5, 140.4)], "W25 ~0.3 m twisted"),
    ("W03", [(572.0, 32.0), (572.0, 24.0), (408.0, 24.0), (408.0, 101.0), (280.0, 136.0), (64.5, 123.5)], "W03 ~0.7 m raw HV"),
    ("W07", [(470.0, 24.0), (406.0, 24.0), (406.0, 102.0), (280.0, 138.0), (64.5, 149.8)], "W07 from the PSU HT tabs"),
    ("W08", [(79.0, 166.5), (120.0, 140.0), (280.0, 100.0), (296.5, 81.0)], "W08 ~0.38 m"),
]


def rect(ax, r, **kw):
    x0, y0, x1, y1 = r
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, **kw))


def board(ax, detail):
    ax.add_patch(Polygon(G["outline"], closed=True, fc="#f3f7ee", ec="k", lw=1.4, zorder=1))
    for h, (x, y) in G["holes"].items():
        ax.add_patch(Circle((x, y), P.HOLE_DRILL / 2, fc="w", ec="k", lw=0.8, zorder=5))
        if detail:
            ax.add_patch(Circle((x, y), P.HOLE_KEEPOUT_HV, fc="none", ec="#e41a1c", lw=0.5, ls=":", zorder=5))
            ax.add_patch(Circle((x, y), P.HOLE_KEEPOUT_LV, fc="none", ec="k", lw=0.5, ls="--", zorder=5))
            ax.text(x + 2.2, y - 3.5, h + (" (no plate hole)" if h in P.HOLE_NO_CHASSIS else ""), fontsize=5)
    for u, s in G["sockets"].items():
        cx, cy = s["centre"]
        ax.add_patch(Circle((cx, cy), 13.0, fc="#fff3d6", ec="#b8860b", lw=0.8, zorder=2))
        for p in s["pads"]:
            ax.add_patch(Circle((p["x"], p["y"]), p["d"] / 2, fc="#d4a017", ec="none", zorder=6))
            if detail:
                ax.text(p["x"], p["y"], p["num"], fontsize=3.5, ha="center", va="center", zorder=7)
        if detail:
            ax.text(cx, cy + 1.5, u, fontsize=7, ha="center", weight="bold", zorder=7)
            ax.text(cx, cy - 2.5, P.TUBES[u].split(" (")[0], fontsize=6, ha="center", zorder=7)


def connectors(ax, detail):
    for ref, c in G["connectors"].items():
        col = CABLE_COL.get(c["cable"][:3], "k")
        for poly in c["courtyard"]:
            ax.add_patch(Polygon(poly, closed=True, fc=col, alpha=0.18, ec=col, lw=0.8, zorder=8))
        for p in c["pads"]:
            ax.add_patch(Circle((p["x"], p["y"]), min(p["d"], 2.0) / 2, fc="#555", ec="none", zorder=9))
        p1 = [p for p in c["pads"] if p["num"] == "1"][0]
        ax.add_patch(Circle((p1["x"], p1["y"]), 1.0 if detail else 2.0, fc="r", ec="k", lw=0.3, zorder=10))
        if detail:
            xs = [q[0] for poly in c["courtyard"] for q in poly]
            ys = [q[1] for poly in c["courtyard"] for q in poly]
            ax.text(sum(xs) / len(xs), max(ys) + 0.8, f"{ref} {c['cable']}", fontsize=5.5, ha="center", zorder=11, weight="bold")


def neighbours(ax):
    rect(ax, P.PREAMP, fc="#eeeeee", ec="#666", lw=0.8)
    ax.text(194, 52, "Preamp (y 16.2-88.1)", ha="center", fontsize=7)
    rect(ax, P.POWER_AMP, fc="#eeeeee", ec="#666", lw=0.8)
    ax.text(400, 160, "Power amp (x 280.3-519.1, y 127.1-187.4)", ha="center", fontsize=7)
    rect(ax, P.CONTROL, fc="#eef2fa", ec="#666", lw=0.8)
    ax.text(489, 60, "Control board", ha="center", fontsize=7)
    ax.add_patch(Polygon(P.REAR_IO_MAIN, closed=True, fc="#f6eef6", ec="#666", lw=0.8))
    ax.text(240, 204, "Rear I/O (plan)", ha="center", fontsize=6)
    rect(ax, P.REAR_IO_JACKS, fc="#ead6ea", ec="#666", lw=0.5)
    rect(ax, (50, 10.7, 560, 12.3), fc="#999", ec="none")
    ax.text(60, 4, "front panel board (x 50-560, back face y 12.3)", fontsize=6)
    for ref, (x, z) in P.FRONT_J4_J6.items():
        rect(ax, (x - 3.7, 12.3, x + 6.2, P.FRONT_SOCKET_Y), fc="#2ca02c", alpha=0.3, ec="#2ca02c", lw=0.5)
        ax.text(x + 1.3, 31.5, ref, fontsize=5, ha="center")
    j3a, j3b = P.CONTROL_J3["pin1"], P.CONTROL_J3["pin14"]
    rect(ax, (j3b[0] - 3.7, j3b[1] - 5.6, j3a[0] + 3.7, j3a[1] + 5.6), fc="#9467bd", alpha=0.3, ec="#9467bd", lw=0.5)
    ax.text(j3a[0] + 5, j3a[1], "J3", fontsize=5)
    ax.add_patch(Circle(P.OT_HOLE, 7.5, fc="none", ec="k", lw=0.8))
    ax.add_patch(Circle(P.OT_HOLE, 15.0, fc="none", ec="k", lw=0.4, ls=":"))
    ax.text(P.OT_HOLE[0] + 9, P.OT_HOLE[1] - 2, "OT lead hole", fontsize=5)
    rect(ax, (P.PREAMP_J507[0] - 2.5, 80.6, P.PREAMP_J507[0] + 2.5, 87.4), fc="#d62728", alpha=0.4, ec="#d62728")
    ax.text(P.PREAMP_J507[0], 77, "J507", fontsize=5, ha="center")
    for (x, y) in P.PREAMP_J502:
        rect(ax, (x - 4, y - 4, x + 4, y + 4), fc="#bcbd22", alpha=0.4, ec="#bcbd22")
    ax.text(296, 74, "J502 htr", fontsize=5, ha="center")
    ax.plot([34.6, 444], [P.ETHERNET_Y, P.ETHERNET_Y], color=CABLE_COL["ETH"], lw=2.0, ls=(0, (6, 3)), alpha=0.6)
    ax.text(36, P.ETHERNET_Y + 1.5, "Ethernet patch cable on the floor (y ~96)", fontsize=5.5, color="#555")


def routes(ax, lw=1.4, labels=True):
    for w, pts, lab in ROUTES:
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=CABLE_COL[w], lw=lw, alpha=0.85, zorder=12)
        if labels:
            k = len(pts) // 2
            ax.text(pts[k][0], pts[k][1] + 1.5, lab, fontsize=5.5, color=CABLE_COL[w], zorder=13)


def zones(ax):
    for name, r, text in P.ZONES:
        rect(ax, r, fc="none", ec="#4a6", lw=0.8, ls="--", zorder=3)
        ax.text(r[0] + 1, r[1] + 1, name, fontsize=6.5, weight="bold", color="#2a5", zorder=3)
        ax.text(r[0] + 1, r[1] + 4.0, text, fontsize=4.2, color="#2a5", zorder=3, va="bottom")
    xs, ys = zip(*P.HEATER_ROUTE)
    ax.plot(xs, ys, color="#bcbd22", lw=2.5, alpha=0.8, zorder=4)
    ax.text(140, 174.2, "heater pair (broadside, rear strip y 172-174.5)", fontsize=5, color="#888800", zorder=4)


def keepouts(ax):
    x0, y0 = G["outline"][1][0], G["outline"][2][1]
    # rear edge: rear I/O
    ax.plot([160, 278.7], [179.7, 179.7], color="#a0a", lw=0.8, ls="--")
    ax.text(163, 180.6, "rear I/O W23 / W19 plugs y 179.7 (3.7 mm), jack board tails y 182.6 (6.6 mm): nothing past the rear edge, x 160-322", fontsize=5, color="#a0a")
    ax.plot([280.33, 280.33], [127.05, 187.4], color="#666", lw=0.8)
    ax.text(281, 186, "power amp\nx 280.33\n(1.64 mm)", fontsize=5, color="#444", va="top")
    ax.plot([45, 300], [88.08, 88.08], color="#666", lw=0.8)
    ax.text(46, 89, "preamp rear edge y 88.08 (gap 15.9 mm: W30-W32 on edge, W22, Ethernet on the floor)", fontsize=5, color="#444")
    # ribbon corridors on this board (no part taller than ~15 mm)
    rect(ax, (160.5, 166.7, 189.5, 175.7), fc="#1f77b4", alpha=0.10, ec="#1f77b4", lw=0.5, ls=":", zorder=3)
    ax.text(161, 167.4, "W23 corridor: parts <= 15 mm", fontsize=4.5, color="#1f77b4", zorder=3)
    rect(ax, (269.2, 107.0, 278.7, 127.0), fc="#9467bd", alpha=0.10, ec="#9467bd", lw=0.5, ls=":", zorder=3)
    ax.text(270, 128, "W13 corridor\n(no parts)", fontsize=4.5, color="#9467bd", zorder=3)
    del x0, y0


def section(ax, title, x_cut, items):
    ax.set_title(title, fontsize=8, loc="left")
    ax.add_patch(Rectangle((0, -2), 215, 2, fc="#888"))
    ax.text(2, -3, "top plate", fontsize=5)
    ax.axhline(P.FLOOR, color="#888", lw=1)
    ax.text(2, P.FLOOR + 3, "floor 82.5", fontsize=5)
    for kind, args in items:
        if kind == "rect":
            (y0, d0, y1, d1, fc, lab) = args
            ax.add_patch(Rectangle((y0, d0), y1 - y0, d1 - d0, fc=fc, ec="k", lw=0.5, alpha=0.6))
            if lab:
                ax.text((y0 + y1) / 2, d0 - 0.8, lab, fontsize=5, ha="center")
        elif kind == "line":
            pts, col, lab = args
            ys, ds = zip(*pts)
            ax.plot(ys, ds, color=col, lw=1.6)
            if lab:
                ax.text(pts[-1][0] + 1, pts[-1][1], lab, fontsize=5, color=col)
    ax.set_xlim(85, 212)
    ax.set_ylim(86, -6)
    ax.set_xlabel("chassis y (mm, front panel = 0)", fontsize=6)
    ax.set_ylabel("depth below the plate (mm)", fontsize=6)
    ax.tick_params(labelsize=5)
    ax.set_aspect("equal")
    del x_cut


def main():
    fig = plt.figure(figsize=(16.5, 23.0))
    axA = fig.add_axes([0.04, 0.665, 0.93, 0.32])
    axB = fig.add_axes([0.04, 0.27, 0.93, 0.38])
    axC = fig.add_axes([0.04, 0.025, 0.45, 0.22])
    axD = fig.add_axes([0.52, 0.025, 0.45, 0.22])

    axA.set_title("A. Under the plate, seen from above (D748 frame, mm): PI + FX rev B with every cable that leaves it "
                  "(red dot = pin 1)", fontsize=9, loc="left")
    neighbours(axA)
    board(axA, False)
    connectors(axA, False)
    routes(axA)
    axA.set_xlim(0, 600)
    axA.set_ylim(0, 212)
    axA.set_aspect("equal")
    axA.tick_params(labelsize=6)
    axA.grid(alpha=0.2)

    axB.set_title("B. PI + FX rev B, seen from above (solder side up; parts hang below, F.Cu faces the floor): zones, "
                  "connectors at their real footprints, pin 1 red; hole keep-outs LV dashed / HV dotted", fontsize=9, loc="left")
    neighbours(axB)
    board(axB, True)
    zones(axB)
    keepouts(axB)
    connectors(axB, True)
    for w, pts, lab in ROUTES:          # only the first leg off each connector of this board
        on = [q for q in pts if 53 <= q[0] <= 279 and 104 <= q[1] <= 176]
        if on and w not in ("W03", "W07", "W08", "W22", "W25", "W13"):
            xs, ys = zip(*pts[:2]) if pts[0] in on else zip(*pts[-2:])
            axB.plot(xs, ys, color=CABLE_COL[w], lw=1.0, alpha=0.8, zorder=12)
    for ref, c in G["connectors"].items():
        p1 = [p for p in c["pads"] if p["num"] == "1"][0]
        axB.annotate(f"pin 1 ({p1['x']:.2f}, {p1['y']:.2f})", (p1["x"], p1["y"]), xytext=(4, -9), textcoords="offset points",
                     fontsize=4.6, color="r", zorder=14)
    axB.set_xlim(45, 300)
    axB.set_ylim(85, 190)
    axB.set_aspect("equal")
    axB.tick_params(labelsize=6)
    axB.grid(alpha=0.25)

    d_b0, d_b1 = P.BOARD_DEPTH
    rio = P.REAR_IO_J101
    section(axC, "C. Section at x 175 (W23): PI + FX J102 -> rear I/O J101, straight 1:1, one bend", 175, [
        ("rect", (16.2, d_b0, 88.1, d_b1, "#ccc", "preamp")),
        ("rect", (103.98, d_b0, 175.73, d_b1, "#cfe8b8", "PI + FX board")),
        ("rect", (156.8, d_b1, 166.7, d_b1 + 9.0, "#1f77b4", "")),
        ("rect", (158.5, d_b1 + 9.0, 165.0, d_b1 + P.IDC_MATED, "#9ecae1", "J102 + socket")),
        ("rect", (103.98, d_b1, 175.73, d_b1 + P.TALLEST_PART, "none", "")),
        ("rect", (rio["board_face_y"], 8.0, rio["board_face_y"] + 1.6, 77.0, "#e8d0e8", "rear I/O main")),
        ("rect", (rio["plug_face_y"], rio["body_depth"][0], rio["board_face_y"], rio["body_depth"][1], "#c39bd3", "J101 + plug")),
        ("rect", (182.6, 25.0, 197.7, 60.0, "none", "jack board (x 191-219)")),
        ("line", ([(161.8, d_b1 + P.IDC_MATED + 0.5), (176.0, d_b1 + P.IDC_MATED + 0.5), (179.2, 38.5), (179.2, 47.4)],
                  CABLE_COL["W23"], "W23 (80 mm with slack)")),
        ("line", ([(103.98, d_b1 + P.TALLEST_PART), (175.73, d_b1 + P.TALLEST_PART)], "#999", "tallest parts 33 mm (depth 49.6)")),
    ])
    section(axD, "D. Section at x 247 (W32 into J304): on edge in the gap, one 45 deg fold up, into the socket from the front", 247, [
        ("rect", (16.2, d_b0, 88.1, d_b1, "#ccc", "preamp")),
        ("rect", (103.98, d_b0, 175.73, d_b1, "#cfe8b8", "PI + FX board")),
        ("rect", (105.3, d_b1, 115.2, d_b1 + 9.0, "#2ca02c", "")),
        ("rect", (107.0, d_b1 + 9.0, 113.5, d_b1 + P.IDC_MATED, "#a1d99b", "J304 + socket")),
        ("rect", (98.5, 38.0, 99.5, 50.7, "#2ca02c", "W30-W32 on edge (12.7 mm)")),
        ("line", ([(99.0, 38.0), (99.0, 35.2), (101.0, d_b1 + P.IDC_MATED + 0.6), (112.0, d_b1 + P.IDC_MATED + 0.6)], CABLE_COL["W32"], "")),
        ("rect", (P.ETHERNET_Y - 3, P.FLOOR - 6, P.ETHERNET_Y + 3, P.FLOOR, "#7f7f7f", "Ethernet")),
        ("line", ([(104.5, 55.0), (118.0, 55.0)], CABLE_COL["W22"], "W22 at depth >= 55")),
        ("line", ([(103.98, d_b1 + P.TALLEST_PART), (175.73, d_b1 + P.TALLEST_PART)], "#999", "")),
    ])
    for ax in (axA, axB, axC, axD):
        for t in ax.texts:
            t.set_clip_on(True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
