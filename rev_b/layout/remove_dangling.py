#!/usr/bin/env python3
"""Delete the tracks / vias kicad-cli DRC flags as dangling (track_dangling, via_dangling), repeated until
none: kipy remove_dangling.py IN OUT   (the DRC decides, not pcbnew's connectivity: kicad_krt_traps.md)"""
import json
import os
import subprocess
import sys
import tempfile

import pcbnew

CLI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "p2k", "bin", "kicad-cli")


def flagged(path):
    with tempfile.TemporaryDirectory() as td:
        rpt = os.path.join(td, "d.json")
        subprocess.run([CLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", rpt, path], capture_output=True)
        d = json.load(open(rpt))
    return {i["uuid"] for v in d["violations"] if v["type"] in ("track_dangling", "via_dangling") for i in v["items"]}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    if src != dst:
        b = pcbnew.LoadBoard(src)
        b.Save(dst)
    total = 0
    for _ in range(5):
        ids = flagged(dst)
        if not ids:
            break
        b = pcbnew.LoadBoard(dst)
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in ids:
                b.Delete(t)
                total += 1
        zs = b.Zones()
        pcbnew.ZONE_FILLER(b).Fill(zs)
        b.Save(dst)
    print(f"removed {total} dangling tracks / vias")


if __name__ == "__main__":
    main()
