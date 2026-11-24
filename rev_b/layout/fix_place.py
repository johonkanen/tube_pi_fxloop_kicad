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
    # B+FX zener string: no room left on F in the regulator corner (the anneal had them between the J501 / J502
    # receptacles); on B under C504's body, clear of the B drain pour (HV on the plate side: 13.4 mm to the plate)
    "D506": (80.0, 133.5, 0, "B"),
    "D507": (90.0, 133.5, 0, "B"),
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


import math  # noqa: E402

FIXED = None


def need(a, b):
    ca, cb = cls(a.GetNetname()), cls(b.GetNetname())
    if a.GetNetname() == b.GetNetname() or "unconnected" in a.GetNetname() + b.GetNetname():
        return 0.0
    s = {ca, cb}
    if s == {"HV", None}:
        return 2.5
    if s == {"HV", "MV"} or s == {"MV", None}:
        return 1.25
    if s in ({"HV"}, {"MV"}):
        return 0.6
    return 0.0


def class_push(b, margin=0.25):
    """Pads of two different parts closer than their class rule (HV-LV 2.5, HV-MV / MV-LV 1.25, HV-HV
    0.6 mm): move the movable part (not fixed; the low-voltage one first) away by the deficit. The anneal
    and its legaliser know courtyards, not the class rules."""
    fixed = set(P.CONNECTORS) | set(P.PINNED) | set(P.PINNED_PIN1)
    pads = [(f, p) for f in b.GetFootprints() if not f.GetReference().startswith("H") for p in f.Pads() if p.GetNetname()]
    moves = {}
    for i, (fa, a) in enumerate(pads):
        for fb, q in pads[i + 1:]:
            if fa is fb:
                continue
            r = need(a, q)
            if not r:
                continue
            if a.IsOnLayer(pcbnew.F_Cu) != q.IsOnLayer(pcbnew.F_Cu) and a.IsOnLayer(pcbnew.B_Cu) != q.IsOnLayer(pcbnew.B_Cu):
                continue
            pa, pq = a.GetPosition(), q.GetPosition()
            d = math.hypot(pa.x - pq.x, pa.y - pq.y)
            if d > pcbnew.FromMM(r + 6):
                continue
            ra = max(a.GetSize().x, a.GetSize().y) / 2
            rq = max(q.GetSize().x, q.GetSize().y) / 2
            gap = pcbnew.ToMM(d - ra - rq)
            if gap >= r:
                continue
            # move the one that is movable; prefer the part whose pad is not the HV one
            cand = [(fq, pa_, pq_) for fq, pa_, pq_ in ((fb, pa, pq), (fa, pq, pa))
                    if fq.GetReference() not in fixed and fq.GetReference()[0] not in "JVH"]
            if not cand:
                continue
            f, src, dst = cand[0]
            ux, uy = (dst.x - src.x) / max(d, 1), (dst.y - src.y) / max(d, 1)
            k = pcbnew.FromMM(r - gap + margin)
            mx, my = moves.get(f.GetReference(), (0, 0))
            moves[f.GetReference()] = (mx + ux * k, my + uy * k)
    # HV / MV pads round the standoff holes (HV 3.65 mm, MV 2.4 mm from the hole edge, r 1.6)
    for h, (hx, hy) in P.HOLES_BOARD.items():
        if h in P.HOLE_DROPPED:
            continue
        c = pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy))
        for f, p in pads:
            k_ = cls(p.GetNetname())
            if not k_ or f.GetReference() in fixed or f.GetReference()[0] in "JVH":
                continue
            r = (3.65 if k_ == "HV" else 2.4) + 1.6 + margin
            q = p.GetPosition()
            d = math.hypot(q.x - c.x, q.y - c.y)
            gap = pcbnew.ToMM(d - max(p.GetSize().x, p.GetSize().y) / 2)
            if gap < r:
                ux, uy = (q.x - c.x) / max(d, 1), (q.y - c.y) / max(d, 1)
                k = pcbnew.FromMM(r - gap)
                mx, my = moves.get(f.GetReference(), (0, 0))
                moves[f.GetReference()] = (mx + ux * k, my + uy * k)
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for ref, (mx, my) in moves.items():
        q = fp[ref].GetPosition()
        fp[ref].SetPosition(pcbnew.VECTOR2I(int(q.x + mx), int(q.y + my)))
        print(f"  class push {ref}: {pcbnew.ToMM(int(mx)):+.2f}, {pcbnew.ToMM(int(my)):+.2f} mm")
    return len(moves)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    for ref, (x, y, rot, *side) in FIX.items():
        f = fp[ref]
        if side and (side[0] == "B") != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(rot)
        bx, by = P.to_board(x, y)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(bx), pcbnew.FromMM(by)))
    n = edge_push(b)
    if "--push" in sys.argv:
        n += class_push(b)
    b.Save(sys.argv[2])
    print(f"fix_place: {len(FIX)} nudge(s), {n} edge push(es)")


if __name__ == "__main__":
    main()
