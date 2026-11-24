#!/usr/bin/env python3
"""Layout sketch, step 1 (needs pcbnew: run with tools/p2k/bin/kipy from the repo root):
place the real footprints of placement.py in the board frame and write every pad and courtyard
in chassis coordinates to rev_b/build/layout/sketch_geom.json, plus a table of pin positions
(pin 1, pin 2, last pin) on stdout. sketch_draw.py draws from the JSON.

    tools/p2k/bin/kipy rev_b/layout/sketch_geom.py
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
RB = os.path.dirname(HERE)
ROOT = os.path.dirname(RB)
sys.path.insert(0, HERE)
import placement as P  # noqa: E402

STOCK = os.path.join(open(f"/tmp/p2k_kicad_mount.{os.getuid()}").read().strip(), "share", "kicad", "footprints") \
    if os.path.exists(f"/tmp/p2k_kicad_mount.{os.getuid()}") else os.path.join(os.environ["KICAD_MOUNT"], "share", "kicad", "footprints")


def mm(v):
    return pcbnew.ToMM(v)


def libpath(lib):
    if lib.startswith(P.STOCK):
        return STOCK + lib[len(P.STOCK):]
    return os.path.normpath(os.path.join(RB, "kicad", lib))


def courtyard(fp, side):
    layer = pcbnew.F_CrtYd if side == "F" else pcbnew.B_CrtYd
    poly = fp.GetCourtyard(pcbnew.F_Cu if side == "F" else pcbnew.B_Cu)
    if poly.OutlineCount() == 0:
        bb = fp.GetBoundingBox(False)
        pts = [(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())]
    else:
        polys = []
        for k in range(poly.OutlineCount()):
            o = poly.Outline(k)
            polys.append([P.to_chassis(mm(o.CPoint(i).x), mm(o.CPoint(i).y)) for i in range(o.PointCount())])
        return polys
    del layer
    return [[P.to_chassis(mm(x), mm(y)) for x, y in pts]]


def pads(fp):
    out = []
    for p in fp.Pads():
        x, y = P.to_chassis(mm(p.GetPosition().x), mm(p.GetPosition().y))
        out.append({"num": p.GetNumber(), "x": round(x, 3), "y": round(y, 3), "d": round(mm(max(p.GetSize().x, p.GetSize().y)), 2)})
    return out


def place(lib, name, side, rot, pin1_chassis=None, at_board=None):
    fp = pcbnew.FootprintLoad(libpath(lib), name)
    if fp is None:
        raise SystemExit(f"footprint not found: {lib}/{name}")
    board = pcbnew.BOARD()
    board.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    if side == "B":
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    if at_board is not None:
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(at_board[0]), pcbnew.FromMM(at_board[1])))
    else:
        p1 = [p for p in fp.Pads() if p.GetNumber() == "1"][0].GetPosition()
        tx, ty = P.to_board(*pin1_chassis)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(tx) - p1.x, pcbnew.FromMM(ty) - p1.y))
    return fp, board


def main():
    out = {"outline": None, "holes": {}, "sockets": {}, "connectors": {}}
    x0, y0, x1, y1 = P.OUTLINE_BOARD
    out["outline"] = [P.to_chassis(x, y) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    for h, (bx, by) in P.HOLES_BOARD.items():
        out["holes"][h] = P.to_chassis(bx, by)
    for u, at in P.SOCKETS_BOARD.items():
        fp, _b = place(*P.SOCKET_FP, "B", 180, at_board=at)
        out["sockets"][u] = {"centre": P.to_chassis(*at), "pads": pads(fp), "courtyard": courtyard(fp, "B")}
    print("| Ref | Cable | pin 1 (chassis) | pin 2 | last pin | courtyard x | courtyard y |")
    print("|---|---|---|---|---|---|---|")
    for ref, (cable, mate, lib, name, side, rot, pin1, note) in P.CONNECTORS.items():
        fp, _b = place(lib, name, side, rot, pin1_chassis=pin1)
        pp = pads(fp)
        cy = courtyard(fp, side)
        xs = [p[0] for poly in cy for p in poly]
        ys = [p[1] for poly in cy for p in poly]
        out["connectors"][ref] = {"cable": cable, "mate": mate, "footprint": name, "side": side, "rot": rot,
                                  "pads": pp, "courtyard": cy, "note": note}
        nums = [p for p in pp]
        first = [p for p in nums if p["num"] == "1"]
        second = [p for p in nums if p["num"] == "2"]
        last = nums[-1]
        print(f"| {ref} | {cable} | ({first[0]['x']:.2f}, {first[0]['y']:.2f}) | ({second[0]['x']:.2f}, {second[0]['y']:.2f}) | "
              f"{last['num']} ({last['x']:.2f}, {last['y']:.2f}) | {min(xs):.2f}-{max(xs):.2f} | {min(ys):.2f}-{max(ys):.2f} |")
    os.makedirs(os.path.join(RB, "build", "layout"), exist_ok=True)
    with open(os.path.join(RB, "build", "layout", "sketch_geom.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
