#!/usr/bin/env python3
"""Silkscreen tidy: kipy silk_tidy.py IN OUT

- Values off the silkscreen (fab layer only), except the connectors, whose value carries the cable ID
  (e.g. "FX (W23-a)"): those stay on silk if they find room.
- Every reference on its side's silkscreen, upright (0 or 90 deg), 1.0 mm (JLC: 1.0 mm height, 0.15 mm
  line), placed at the first candidate position round the part's courtyard that clears every pad by
  0.2 mm, every other silk text and the footprints' own silk outlines, and the board edge by 0.3 mm;
  if none fits, 0.8 mm; if still none, the reference is left on the fab layer only (listed).
"""
import sys

import pcbnew

M = pcbnew.FromMM


def inflate(bb, d):
    return pcbnew.BOX2I(pcbnew.VECTOR2I(bb.GetLeft() - d, bb.GetTop() - d), pcbnew.VECTOR2I(bb.GetWidth() + 2 * d, bb.GetHeight() + 2 * d))


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    edge = b.GetBoardEdgesBoundingBox()
    inner = inflate(edge, -M(0.3))
    fps = list(b.GetFootprints())
    obst = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    for f in fps:
        side = pcbnew.B_SilkS if f.IsFlipped() else pcbnew.F_SilkS
        for p in f.Pads():
            for lay, cu in ((pcbnew.F_SilkS, pcbnew.F_Cu), (pcbnew.B_SilkS, pcbnew.B_Cu)):
                if p.IsOnLayer(cu):
                    obst[lay].append(inflate(p.GetBoundingBox(), M(0.2)))
        for g in f.GraphicalItems():
            if g.GetLayer() in obst and g.GetClass() != "PCB_TEXT":
                if g.GetClass() == "PCB_SHAPE" and g.GetShape() in (pcbnew.SHAPE_T_RECT, pcbnew.SHAPE_T_POLY):
                    for k in range(4):        # outline only: four thin boxes, so text may sit inside
                        bb = g.GetBoundingBox()
                        x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
                        w = M(0.2)
                        r = [(x0, y0, x1, y0 + w), (x0, y1 - w, x1, y1), (x0, y0, x0 + w, y1), (x1 - w, y0, x1, y1)][k]
                        obst[g.GetLayer()].append(pcbnew.BOX2I(pcbnew.VECTOR2I(r[0], r[1]), pcbnew.VECTOR2I(r[2] - r[0], r[3] - r[1])))
                else:
                    obst[g.GetLayer()].append(inflate(g.GetBoundingBox(), M(0.1)))
        for h in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            pass
    placed = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    hidden = []
    # big parts first (their refs have the most room), connectors' values last
    def area(f):
        cy = f.GetCourtyard(pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu)
        return cy.BBox().GetArea() if cy.OutlineCount() else 0
    # connectors first (their cable IDs matter at wiring), then the big parts
    order = sorted(fps, key=lambda f: (not f.GetReference().startswith("J"), -area(f)))
    for f in order:
        side = pcbnew.B_SilkS if f.IsFlipped() else pcbnew.F_SilkS
        fab = pcbnew.B_Fab if f.IsFlipped() else pcbnew.F_Fab
        val = f.Value()
        is_conn = f.GetReference().startswith("J")
        val.SetLayer(fab)
        texts = [(f.Reference(), f.GetReference())] + ([(val, "value")] if is_conn else [])
        cy = f.GetCourtyard(pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu)
        cb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        for txt, what in texts:
            ok = False
            sides = [side] + ([pcbnew.F_SilkS if side == pcbnew.B_SilkS else pcbnew.B_SilkS] if is_conn else [])
            for size, lay in [(sz, ly) for ly in sides for sz in (1.0, 0.8)]:
                side_ = lay
                txt.SetLayer(lay)
                txt.SetMirrored(lay == pcbnew.B_SilkS)
                txt.SetTextSize(pcbnew.VECTOR2I(M(size), M(size)))
                txt.SetTextThickness(M(0.15))
                txt.SetKeepUpright(True)
                cx, cyy = cb.GetCenter().x, cb.GetCenter().y
                hw, hh = cb.GetWidth() // 2, cb.GetHeight() // 2
                g = M(size * 0.7)
                cands = [(cx, cb.GetTop() - g, 0), (cx, cb.GetBottom() + g, 0), (cb.GetLeft() - g * 2, cyy, 90),
                         (cb.GetRight() + g * 2, cyy, 90), (cx, cyy, 0), (cx, cyy, 90),
                         (cb.GetLeft() + hw // 2, cb.GetTop() - g, 0), (cb.GetRight() - hw // 2, cb.GetBottom() + g, 0)]
                if is_conn:                   # inside the shroud / body outline, between and beside the pin rows
                    cands += [(cx + dx, cyy + dy, rot) for rot in (0, 90) for dx in (-hw // 2, 0, hw // 2)
                              for dy in (-hh // 2, 0, hh // 2)]
                for x, y, rot in cands:
                    txt.SetTextAngleDegrees(rot)
                    txt.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                    tb = txt.GetBoundingBox()
                    if not inner.Contains(tb):
                        continue
                    if any(o.Intersects(tb) for o in obst[side_]) or any(o.Intersects(tb) for o in placed[side_]):
                        continue
                    placed[side_].append(inflate(tb, M(0.15)))
                    ok = True
                    break
                if ok:
                    break
            if not ok:
                txt.SetLayer(fab)
                txt.SetMirrored(fab == pcbnew.B_Fab)
                txt.SetTextSize(pcbnew.VECTOR2I(M(0.8), M(0.8)))
                txt.SetTextThickness(M(0.12))
                txt.SetPosition(cb.GetCenter())
                hidden.append(f"{f.GetReference()}{'' if what != 'value' else ' value'}")
    b.Save(sys.argv[2])
    print(f"silk: {sum(len(v) for v in placed.values())} texts placed, {len(hidden)} left on fab only: {' '.join(hidden)}")


if __name__ == "__main__":
    main()
