#!/usr/bin/env python3
"""DRC exclusions of the PI + FX rev B board, each with its reason (STATUS "Layout, first pass" L3):

    tools/p2k/bin/kipy rev_b/layout/drc_exclusions.py     (edits rev_b/kicad/tube_pi_fxloop_revb.kicad_pro)

Only these violations are excluded; any other stays an error. Item ids change with every chain run,
so this runs after the board is copied into rev_b/kicad/. Pattern: tube_rear_io_kicad tools/drc_exclusions.py.
"""
import json
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RB = os.path.dirname(HERE)
PRO = os.path.join(RB, "kicad", "tube_pi_fxloop_revb.kicad_pro")
PCB = os.path.join(RB, "kicad", "tube_pi_fxloop_revb.kicad_pcb")
CLI = os.path.join(RB, "..", "tools", "p2k", "bin", "kicad-cli")

# (violation type, regex that every item description must match one of, reason)
RULES = [
    ("npth_inside_courtyard", [r"NPTH pad of H3", r"Footprint V2"],
     "rev A geometry (as built): standoff H3 sits at the edge of V2's socket outline; the socket body clears the standoff"),
    ("npth_inside_courtyard", [r"NPTH pad of H4", r"Footprint V1"],
     "rev A geometry (as built): standoff H4 sits at the edge of V1's socket outline; the socket body clears the standoff"),
]


def matches(v, pats):
    descs = [i["description"] for i in v["items"]]
    return len(descs) == len(pats) and all(any(re.search(p, d) for d in descs) for p in pats)


def main():
    pro = json.load(open(PRO))
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    ds["drc_exclusions"] = []
    json.dump(pro, open(PRO, "w"), indent=2)
    with tempfile.TemporaryDirectory() as td:
        rpt = os.path.join(td, "drc.json")
        subprocess.run([CLI, "pcb", "drc", "--severity-all", "--format", "json", "-o", rpt, PCB], capture_output=True)
        d = json.load(open(rpt))
    ex, n = [], 0
    for v in d["violations"]:
        for typ, pats, why in RULES:
            if v["type"] == typ and matches(v, pats):
                n += 1
                ids = [i["uuid"] for i in v["items"]]
                pts = [(round(i["pos"]["x"] * 1e6), round(i["pos"]["y"] * 1e6)) for i in v["items"]]
                for x, y in pts:
                    for a, b in ((ids[0], ids[-1]), (ids[-1], ids[0])):
                        ex.append([f"{typ}|{x}|{y}|{a}|{b}", why])
    ds["drc_exclusions"] = ex
    json.dump(pro, open(PRO, "w"), indent=2)
    print(f"{n} violations excluded ({len(ex)} keys)")


if __name__ == "__main__":
    main()
