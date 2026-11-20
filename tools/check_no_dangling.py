#!/usr/bin/env python3
"""No dangling track or via in the DRC report (reports/drc.json, written by `p2k drc`; P2K_REPORTS
overrides the directory).

Design fixes 2026-11-20 (user decision, Finding 19): the three dangling Proteus stubs are not built
(p2k_config.py REMOVED_TRACKS). `p2k drc` does not enforce warnings, and gerber_roundtrip passes when a
stub is on both sides, so a stub that comes back (its entry dropped and the board regenerated) would
only change a warning count. This step fails on any track_dangling / via_dangling item.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rep = os.path.join(os.environ.get("P2K_REPORTS") or os.path.join(ROOT, "reports"), "drc.json")
v = [x for x in json.load(open(rep))["violations"] if x["type"] in ("track_dangling", "via_dangling")]
for x in v:
    it = x["items"][0]
    print(f"check_no_dangling: {x['type']}: {it['description']} at ({it['pos']['x']}, {it['pos']['y']})")
print(f"check_no_dangling: {len(v)} dangling tracks / vias in {os.path.relpath(rep, ROOT)}")
print("check_no_dangling: " + ("OK" if not v else "FAILED"))
sys.exit(1 if v else 0)
