#!/usr/bin/env python3
"""Feedback-path check (pattern: tube_preamp_kicad rev_b/layout/coupling_check.py): kipy coupling_check.py BOARD [MM]

Lists where an aggressor net (the PI plates on W24, the return stage plate, the speaker-level feedback
lines, SEND_SRC, the logic / gate / coil lines) runs within MM (default 2.0) of a victim (the input, the
FX return, the mixer, the attenuator, the PI grids) on the same or an adjacent copper layer, as
parallel length and closest gap per net pair. A PI plate or a speaker line next to the input or the PI
grid closes a loop around the power section; SEND_SRC next to RETURN_SIG is the W23 dry leak.
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netclasses as N  # noqa: E402

AGG = ["DRV_A", "DRV_B", "P1B", "SPK_CL", "SPK_CR", "SPK_LD", "FB_8R", "SEND_SRC", "CFO", "K1A"] + N.LOGIC + N.COIL
VIC = ["PRE_IN", "CI", "G1A", "SB", "RETURN_SIG", "RC", "NW", "DMX", "WMX", "M", "G1B", "ATT_IN", "ATT1", "ATT2", "ATT3",
       "ATT4", "ATT_OUT", "PIX", "G2A"]
ADJ = {pcbnew.F_Cu: {pcbnew.F_Cu, pcbnew.In1_Cu}, pcbnew.In1_Cu: {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu},
       pcbnew.In2_Cu: {pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}, pcbnew.B_Cu: {pcbnew.In2_Cu, pcbnew.B_Cu}}


def short(n):
    return n.split("/")[-1]


def seg_dist(a0, a1, b0, b1):
    def pd(p, s0, s1):
        dx, dy = s1[0] - s0[0], s1[1] - s0[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((p[0] - s0[0]) * dx + (p[1] - s0[1]) * dy) / L))
        return math.hypot(p[0] - s0[0] - t * dx, p[1] - s0[1] - t * dy)
    return min(pd(a0, b0, b1), pd(a1, b0, b1), pd(b0, a0, a1), pd(b1, a0, a1))


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    lim = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    segs = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        s = (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y))
        e = (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
        segs.append((short(t.GetNetname()), t.GetLayer(), s, e, pcbnew.ToMM(t.GetWidth()) / 2, pcbnew.ToMM(t.GetLength())))
    agg = [x for x in segs if x[0] in AGG]
    vic = [x for x in segs if x[0] in VIC]
    res = {}
    for a in agg:
        for v in vic:
            if v[1] not in ADJ[a[1]]:
                continue
            g = seg_dist(a[2], a[3], v[2], v[3]) - a[4] - v[4]
            if g < lim:
                k = (a[0], v[0], "same" if a[1] == v[1] else "adjacent")
                L, G = res.get(k, (0.0, 99.0))
                res[k] = (L + min(a[5], v[5]), min(G, g))
    print(f"aggressor -> victim within {lim} mm (same or adjacent layer; length ~ overlap of the shorter segments)")
    for (an, vn, lay), (L, G) in sorted(res.items(), key=lambda kv: -kv[1][0]):
        print(f"  {an:12s} -> {vn:11s} {lay:8s} {L:6.1f} mm, closest {G:4.2f} mm")
    if not res:
        print("  none")


if __name__ == "__main__":
    main()
