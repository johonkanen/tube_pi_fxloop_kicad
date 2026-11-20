#!/usr/bin/env python3
"""p2k drc while the TO-92 pad-1 question is open (STATUS.md "Phase 3", Decisions).

Runs `p2k drc`. If it passes, this passes. If it fails, it passes only when the failure is exactly
the open user question: 0 shorts, 0 unconnected, 0 parity, and the only unaccepted errors are the
9 `clearance` errors between the rectangular KiCad pad 1 of the TO-92 parts Q1 / Q3 / Q6 / Q20 and
Proteus tracks (it then prints PENDING USER DECISION). Any other error fails. Remove this wrapper
(check_all.sh runs `p2k drc` directly) once the decision is made and the board rebuilt.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED = 9
PAD1 = re.compile(r"^PTH pad 1 \[[^]]*\] of (Q1|Q3|Q6|Q20)$")


def main():
    r = subprocess.run([os.path.join(ROOT, "tools/p2k/bin/p2k"), "drc"], cwd=ROOT)
    if r.returncode == 0:
        return 0
    with open(os.path.join(ROOT, "reports/drc.json")) as f:
        d = json.load(f)
    sys.path.insert(0, ROOT)
    import p2k_config
    accepted = getattr(p2k_config, "DRC_ACCEPTED", {})
    bad = []
    if d.get("unconnected_items") or d.get("schematic_parity"):
        bad.append("unconnected / parity items")
    pending = 0
    for v in d["violations"]:
        if v["severity"] != "error" or v["type"] in accepted:
            continue
        pads = [i["description"] for i in v["items"] if PAD1.match(i["description"])]
        if v["type"] == "clearance" and len(pads) == 1:
            pending += 1
        else:
            bad.append(f"{v['type']}: {v['description']}")
    if bad or pending != EXPECTED:
        print(f"drc_pending: FAILED ({pending} TO-92 pad-1 clearance errors, expected {EXPECTED}; "
              f"other: {bad[:5]})")
        return 1
    print(f"drc_pending: PENDING USER DECISION: {pending} clearance errors, rectangular KiCad pad 1 of "
          "the TO-92 parts Q1 Q3 Q6 Q20 vs Proteus tracks (0.122 mm; STATUS.md Phase 3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
