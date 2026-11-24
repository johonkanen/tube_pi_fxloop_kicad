#!/usr/bin/env python3
"""Mechanical checks of the laid-out board against the neighbours: kipy mech_check.py BOARD
- every courtyard inside the outline (nothing overhangs: rear edge over x 160-278.7 for the rear I/O,
  east edge for the power amp at 1.64 mm, front edge for the gap);
- every connector's pin 1 at the agreed chassis position (placement.CONNECTORS = interfaces.md 12.5);
- part heights in the ribbon corridors (W23: <= 15 mm below the board; W13: nothing);
- HV copper to the standoffs and edges is in the DRC rules (not repeated here).
Heights are by footprint class (seated height, mm, from the parts' data / STATUS)."""
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as P  # noqa: E402

HEIGHT = [(r"CP_Radial_D18", 33.0), (r"CP_Radial_D16", 26.5), (r"CP_Radial_D8", 12.0), (r"C_Rect_L31.5", 29.0),
          (r"C_Rect_L18", 15.5), (r"C_Rect_L13", 12.0), (r"C_Rect_L7.2", 9.0), (r"Mini-Fit", 9.6), (r"IDC-Header", 9.1),
          (r"KK-396", 12.5), (r"KK-254", 8.0), (r"Faston", 8.0), (r"Relay_DPDT_Omron_G6K", 5.2), (r"CP_Elec_6.3x7.7", 7.9),
          (r"CP_Elec_5x5.4", 5.6), (r"TO-252", 2.4), (r"SOIC", 1.8), (r"SSOP", 2.0), (r"MountingHole", 0.0), (r"", 1.5)]


def height(f):
    n = str(f.GetFPID().GetLibItemName())
    return next(h for p, h in HEIGHT if re.search(p, n))


def cbox(f):
    cy = f.GetCourtyard(pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu)
    bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
    xs = [P.to_chassis(pcbnew.ToMM(x), 0)[0] for x in (bb.GetLeft(), bb.GetRight())]
    ys = [P.to_chassis(0, pcbnew.ToMM(y))[1] for y in (bb.GetTop(), bb.GetBottom())]
    return min(xs), min(ys), max(xs), max(ys)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    ox0, oy0 = P.to_chassis(P.OUTLINE_BOARD[2], P.OUTLINE_BOARD[3])
    ox1, oy1 = P.to_chassis(P.OUTLINE_BOARD[0], P.OUTLINE_BOARD[1])
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    worst = {"west": 99, "front": 99, "east": 99, "rear": 99}
    out = []
    for r, f in fps.items():
        if f.IsFlipped() and r.startswith("V"):
            continue
        x0, y0, x1, y1 = cbox(f)
        for k, v in (("west", x0 - ox0), ("front", y0 - oy0), ("east", ox1 - x1), ("rear", oy1 - y1)):
            worst[k] = min(worst[k], v)
            if v < 0:
                out.append(f"OVERHANG {r} {k} {v:.2f} mm")
    print(f"outline chassis x {ox0:.2f}-{ox1:.2f}, y {oy0:.2f}-{oy1:.2f}; smallest courtyard margin (negative = overhang): "
          + ", ".join(f"{k} {v:.2f}" for k, v in worst.items()))
    for ref, (cable, mate, _l, _n, _s, _r, pin1, _note) in P.CONNECTORS.items():
        p = fps[ref].FindPadByNumber("1").GetPosition()
        x, y = P.to_chassis(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
        print(f"{ref} {cable}: pin 1 ({x:.2f}, {y:.2f}) agreed ({pin1[0]:.2f}, {pin1[1]:.2f}) off {abs(x - pin1[0]) + abs(y - pin1[1]):.3f} mm")
    for name, (cx0, cy0, cx1, cy1), hmax in (("W23 corridor", (160.0, 166.8, 190.0, 175.7), 15.0),
                                            ("W13 corridor", (269.2, 107.0, 278.7, 127.0), 0.0),
                                            ("front of J302-J304", (192.0, 104.0, 259.0, 105.2), 0.0)):
        hit = []
        for r, f in fps.items():
            if f.IsFlipped() or r in ("J102", "J401") or r.startswith("H"):
                continue
            x0, y0, x1, y1 = cbox(f)
            if x0 < cx1 and x1 > cx0 and y0 < cy1 and y1 > cy0 and height(f) > hmax:
                hit.append(f"{r} ({height(f)} mm)")
        print(f"{name}: parts taller than {hmax} mm: {', '.join(hit) or 'none'}")
    tall = sorted(((height(f), r) for r, f in fps.items() if not f.IsFlipped()), reverse=True)[:6]
    print("tallest below the board:", ", ".join(f"{r} {h} mm (to {16.6 + h:.1f} mm below the plate)" for h, r in tall))
    bside = [r for r, f in fps.items() if f.IsFlipped() and not r.startswith("V")]
    print(f"parts on B (plate side): {len(bside)} (0603, <= 1 mm; 13.4 mm to the plate)")
    for o in out:
        print(o)


if __name__ == "__main__":
    main()
