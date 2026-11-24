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
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
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
        x0, y0, x1, y1 = P.rect_board(*P.POUR_F[q])
        y = y0 + 1.5
        while y < y1 - 1.0:
            x = x0 + 1.5
            while x < x1 - 1.0:
                ok = not (abs(x - tx) < CUT + 1.0 and abs(y - ty) < CUT + 1.0)
                for p in pads:
                    if not ok:
                        break
                    bb = p.GetBoundingBox()
                    same = p.GetNetCode() == net.GetNetCode()
                    m = 0.4 if same and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else (0.8 if same else 2.0)
                    ok = not (pcbnew.ToMM(bb.GetLeft()) - m < x < pcbnew.ToMM(bb.GetRight()) + m and
                              pcbnew.ToMM(bb.GetTop()) - m < y < pcbnew.ToMM(bb.GetBottom()) + m)
                if ok:
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(1.0)); v.SetDrill(mm(0.5))
                    v.SetNet(net); v.SetLocked(True); b.Add(v); n += 1
                x += 2.0
            y += 2.0
    zones = b.Zones()
    pcbnew.ZONE_FILLER(b).Fill(zones)
    b.Save(sys.argv[2])
    print(f"BP_RAW drain pours F/B x2, {n} stitching vias")


if __name__ == "__main__":
    main()
