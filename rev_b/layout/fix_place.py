#!/usr/bin/env python3
"""Post-placement nudges (replayed by place.sh after the anneal): kipy fix_place.py IN OUT
Each entry: ref -> (chassis x, y of the footprint origin, KiCad rotation). Keep this list short: a nudge
is a placement fix the annealer could not find (each with its reason)."""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as P  # noqa: E402

FIX = {
    "R510": (164.0, 139.8, 0),      # seed 4: GF_PI pad 1.5 mm from C501's GND pad (HV to LV 2.5 mm)
    # soft ties at their connectors (grounding.md): DGND-AGND at J401 (B side), W24 ground at J201 (sending end)
    "R401": (257.2, 112.6, 90),
    "C401": (257.2, 116.0, 90),
    "R201": (262.6, 145.6, 90),
    "C201": (259.6, 160.2, 0),
}


import netclasses as N  # noqa: E402

EDGE = {"HV": 2.5 + 0.25, "MV": 1.25 + 0.25}


def cls(net):
    base = net.split("/")[-1]
    return "HV" if base in N.HV else "MV" if base in N.MV else None


def edge_push(b):
    """Move each footprint whose HV / MV pad sits closer to the outline than the edge rule inward,
    by the smallest amount (the anneal does not know the class rules)."""
    x0, y0, x1, y1 = (pcbnew.FromMM(v) for v in P.OUTLINE_BOARD)
    n = 0
    for f in b.GetFootprints():
        if f.GetReference()[0] in "JVH" or f.GetReference() in P.PINNED or f.GetReference() in P.PINNED_PIN1:
            continue
        dx = dy = 0
        for p in f.Pads():
            c = cls(p.GetNetname())
            if not c:
                continue
            m = pcbnew.FromMM(EDGE[c])
            bb = p.GetBoundingBox()
            dx = max(dx, x0 + m - bb.GetLeft()) if bb.GetLeft() < x0 + m else dx
            dx = min(dx, x1 - m - bb.GetRight()) if bb.GetRight() > x1 - m else dx
            dy = max(dy, y0 + m - bb.GetTop()) if bb.GetTop() < y0 + m else dy
            dy = min(dy, y1 - m - bb.GetBottom()) if bb.GetBottom() > y1 - m else dy
        if dx or dy:
            q = f.GetPosition()
            f.SetPosition(pcbnew.VECTOR2I(q.x + dx, q.y + dy))
            n += 1
            print(f"  edge push {f.GetReference()}: {pcbnew.ToMM(dx):+.2f}, {pcbnew.ToMM(dy):+.2f} mm (board frame)")
    return n


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for ref, (x, y, rot) in FIX.items():
        f = fp[ref]
        f.SetOrientationDegrees(rot)
        bx, by = P.to_board(x, y)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by)))
    n = edge_push(b)
    b.Save(sys.argv[2])
    print(f"fix_place: {len(FIX)} nudge(s), {n} edge push(es)")


if __name__ == "__main__":
    main()
