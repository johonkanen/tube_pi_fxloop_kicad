#!/usr/bin/env python3
"""Regulator drain pours (BP_RAW) on F and B with the foldback transistor's cut-out on F, stitched:
kipy draw_pours.py IN OUT

preamp_regulator.md rev B / sim/preamp_supply: the STD4N80K5's tab (drain = BP_RAW) on a copper pour,
the MMBTA42 that sets the current limit on the same pour (thermal foldback: thermally coupled,
electrically separate). Here: the tab on an F pour (placement.POUR_F), the MMBTA42 in a cut-out of
it, a larger B pour under the whole regulator (placement.POUR_B), stitched by vias inside the F
pour. One pair of pours per regulator (each pass device has its own, as the thermal simulation
assumes).
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as P  # noqa: E402

CUT = 2.9          # half size of the MMBTA42's cut-out in the F pour (mm)
FOLD = {"Q505": "Q506", "Q502": "Q503"}


def mm(v):
    return pcbnew.FromMM(v)


def zone(b, net, layer, rect_c, hole=None, prio=10, name=""):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(net); z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetMinThickness(mm(0.3)); z.SetLocalClearance(mm(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name)
    o = z.Outline(); o.NewOutline()
    x0, y0, x1, y1 = P.rect_board(*rect_c)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(x), mm(y))
    if hole:
        o.NewHole()
        hx0, hy0, hx1, hy1 = hole
        for x, y in ((hx0, hy0), (hx0, hy1), (hx1, hy1), (hx1, hy0)):
            o.Append(mm(x), mm(y), 0, 0)
    b.Add(z)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fp = {f.GetReference(): f for f in b.GetFootprints()}
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    n = 0
    for q, t in FOLD.items():
        net = fp[q].FindPadByNumber("2").GetNet()
        c = fp[t].GetPosition()
        tx, ty = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y)
        zone(b, net, pcbnew.F_Cu, P.POUR_F[q], (tx - CUT, ty - CUT, tx + CUT, ty + CUT), name=f"{q} drain F")
        zone(b, net, pcbnew.B_Cu, P.POUR_B[q], name=f"{q} drain B")
        # thermal vias in the tab pad (0.3 mm, 1.2 mm pitch): F pour -> tab -> B pour; filled and capped
        # (IPC-4761 type VII) on the fab order, or accept some solder wicking
        tab = fp[q].FindPadByNumber("2")
        tb = tab.GetBoundingBox()
        tx0, ty0, tx1, ty1 = (pcbnew.ToMM(v) for v in (tb.GetLeft(), tb.GetTop(), tb.GetRight(), tb.GetBottom()))
        yy = ty0 + 1.0
        while yy < ty1 - 0.8:
            xx = tx0 + 1.0
            while xx < tx1 - 0.8:
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(xx), mm(yy))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
                v.SetNet(net); v.SetLocked(True); b.Add(v); n += 1
                xx += 1.2
            yy += 1.2
    zones = b.Zones()
    pcbnew.ZONE_FILLER(b).Fill(zones)
    b.Save(sys.argv[2])
    print(f"BP_RAW drain pours F/B x2, {n} thermal vias in the tabs")


if __name__ == "__main__":
    main()
