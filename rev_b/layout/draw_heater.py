#!/usr/bin/env python3
"""Draw the heater pair (HTR1 / HTR2) on the PI + FX rev B board: kipy draw_heater.py IN OUT

12AX7 x2, 6.3 V parallel (pins 4+5 HTR1, pin 9 HTR2), 0.6 A own; 1.5 A through J502 -> J503 (0.9 A on
to the preamp). Floating (no reference on this board, interfaces.md 5). As the preamp rev B: a
broadside pair, HTR1 on F over HTR2 on B, along the rear strip (chassis y 174.0, behind the sockets'
heater pins and behind J102, which sits 8 mm in from the rear edge for it), 15 mm or more from every
grid pin. At each socket HTR1 (F) stubs to pins 4 and 5; HTR2 (B) leaves between pins 4 and 5 and runs
through the socket centre to pin 9. J502 -> J503: 2 mm tracks (1.5 A). No vias.
Coordinates: chassis frame (placement.py), converted to the board frame here.
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as P  # noqa: E402

Y_RUN = 174.0      # behind the standoff keep-outs (H4 / H3 at y 168.08, r 5.3) and 1.1 mm from the edge
W_RUN, W_STUB, W_TAB = 1.2, 0.8, 2.0


def mm(v):
    return pcbnew.FromMM(v)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    net = {n: fp["J502"].FindPadByNumber(p).GetNet() for n, p in (("HTR1", "1"), ("HTR2", "2"))}
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    def trk(n, pts, layer, w):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            a, c = P.to_board(x0, y0), P.to_board(x1, y1)
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
            t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net[n]); t.SetLocked(True); b.Add(t)

    def pad(ref, num, which=0):
        ps = sorted((p for p in fp[ref].Pads() if p.GetNumber() == num),
                    key=lambda p: P.to_chassis(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)))
        q = ps[which].GetPosition()
        return P.to_chassis(pcbnew.ToMM(q.x), pcbnew.ToMM(q.y))

    s = {v: {n: pad(v, n) for n in ("4", "5", "9")} for v in ("V1", "V2")}
    j2h1, j2h2 = pad("J502", "1", 1), pad("J502", "2", 1)        # east legs (x 64.5)
    j3h1a, j3h1b = sorted([pad("J503", "1", 0), pad("J503", "1", 1)], key=lambda p: p[1])  # y 164, 169
    j3h2a, j3h2b = sorted([pad("J503", "2", 0), pad("J503", "2", 1)], key=lambda p: p[1])
    x_end1 = s["V2"]["4"][0]
    x_end2 = (s["V2"]["4"][0] + s["V2"]["5"][0]) / 2
    # J502 -> J503 (pass-through) and onto the run
    trk("HTR1", [j2h1, (67.5, j2h1[1] + 3.0), (67.5, 160.5), (j3h1a[0], 160.5), j3h1a], F, W_TAB)
    trk("HTR1", [j3h1a, j3h1b], F, W_TAB)
    trk("HTR1", [j3h1b, (j3h1b[0], Y_RUN), (x_end1, Y_RUN)], F, W_RUN)
    trk("HTR2", [j2h2, (j3h2a[0], j3h2a[1] - 0.0)], B, W_TAB)
    # the two legs of each J502 tab are one pad number: join them in copper (the blade joins them anyway)
    trk("HTR1", [pad("J502", "1", 0), j2h1], F, W_TAB)
    trk("HTR2", [pad("J502", "2", 0), j2h2], B, W_TAB)
    trk("HTR2", [j3h2a, j3h2b], B, W_TAB)
    trk("HTR2", [j3h2b, (j3h2b[0], Y_RUN), (x_end2, Y_RUN)], B, W_RUN)
    for v in ("V1", "V2"):
        (x4, y4), (x5, y5), (x9, y9) = s[v]["4"], s[v]["5"], s[v]["9"]
        trk("HTR1", [(x4, Y_RUN), (x4, y4)], F, W_STUB)
        trk("HTR1", [(x5, Y_RUN), (x5, y5)], F, W_STUB)
        xc = (x4 + x5) / 2
        trk("HTR2", [(xc, Y_RUN), (xc, y4 - 4.0), (x9, y9 + 4.0), (x9, y9)], B, W_STUB)
    b.Save(sys.argv[2])
    print("heater pair drawn (rear strip, broadside)")


if __name__ == "__main__":
    main()
