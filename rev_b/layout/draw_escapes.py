#!/usr/bin/env python3
"""Scripted escapes where the router boxes itself in: kipy draw_escapes.py IN OUT

The MCP23S17's GPA0-GPA2 (pins 21-23: FX_DRY, FX_WET, FX_UNMUTE) sit in the middle of its west row,
facing the ULN2803A 3 mm away; every routing order left one of them without an exit. Each gets a short
stub west and a via (0.6 / 0.3 mm), staggered (pin 22's via one step further out, its stub passing
between the other two), so the router continues from the vias on the inner layers. Locked.
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as P  # noqa: E402

ESC = {"21": 1.85, "22": 2.85, "23": 1.85}     # via distance west of the pad centre (chassis mm)


def mm(v):
    return pcbnew.FromMM(v)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    u = {f.GetReference(): f for f in b.GetFootprints()}["U401"]
    for num, dx in ESC.items():
        p = u.FindPadByNumber(num)
        x, y = P.to_chassis(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y))
        vx, vy = P.to_board(x - dx, y)
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(p.GetPosition()); t.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
        t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(p.GetNet()); t.SetLocked(True); b.Add(t)
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetNet(p.GetNet()); v.SetLocked(True); b.Add(v)
    b.Save(sys.argv[2])
    print("expander GPA0-GPA2 escapes drawn")


if __name__ == "__main__":
    main()
