#!/usr/bin/env python3
"""Placement snapshot: kipy snapshot.py save BOARD JSON | apply BOARD JSON OUT
The chosen placement is kept as data (placement_snapshot.json, board frame: x, y, rotation, side per
reference), so the routed board can be rebuilt without re-running the anneal."""
import json
import sys

import pcbnew


def main():
    mode, board = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(board)
    if mode == "save":
        d = {}
        for f in b.GetFootprints():
            p = f.GetPosition()
            d[f.GetReference()] = [round(pcbnew.ToMM(p.x), 4), round(pcbnew.ToMM(p.y), 4),
                                   round(f.GetOrientationDegrees(), 3), "B" if f.IsFlipped() else "F"]
        json.dump(dict(sorted(d.items())), open(sys.argv[3], "w"), indent=0)
        print(f"saved {len(d)} footprints")
        return
    d = json.load(open(sys.argv[3]))
    n = 0
    for f in b.GetFootprints():
        r = f.GetReference()
        if r not in d or f.IsLocked():          # fixed parts (connectors, pinned) come from placement.py
            continue
        x, y, rot, side = d[r]
        if (side == "B") != f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(rot)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        n += 1
    b.Save(sys.argv[4])
    print(f"applied {n} footprints")


if __name__ == "__main__":
    main()
