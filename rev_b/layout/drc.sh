#!/bin/bash
# drc.sh BOARD [TYPE] : kicad-cli DRC (zones refilled, schematic parity, every severity) graded against
# rev_b/kicad's own rules -> BOARD.drc.json. Summary: errors and warnings by type, silkscreen counted
# apart, excluded items counted apart; TYPE lists the items of one type.
set -euo pipefail
B=$1; L="$(cd "$(dirname "$0")" && pwd)"; CLI="$L/../../tools/p2k/bin/kicad-cli"; P="$L/../kicad/tube_pi_fxloop_revb"
for x in pro dru; do cp "$P.kicad_$x" "${B%.kicad_pcb}.kicad_$x" 2>/dev/null || true; done
$CLI pcb drc --refill-zones --schematic-parity --severity-all --severity-exclusions --format json -o "${B%.kicad_pcb}.drc.json" "$B" >/dev/null 2>&1 || true
python3 - "${B%.kicad_pcb}.drc.json" "${2:-}" <<'PY'
import json,sys,collections
d=json.load(open(sys.argv[1]))
ex=[v for v in d["violations"] if v.get("excluded")]
vs=[v for v in d["violations"] if not v.get("excluded")]
silk=[v for v in vs if v["type"].startswith("silk")]
rest=[v for v in vs if not v["type"].startswith("silk")]
c=collections.Counter((v["severity"], v["type"]) for v in rest)
print("errors/warnings:", dict(c) or 0, "| silkscreen:", len(silk), "| excluded:", len(ex),
      "| unconnected:", len(d.get("unconnected_items",[])), "| parity:", len(d.get("schematic_parity",[])))
if sys.argv[2]:
    for v in d["violations"] + [dict(u, type="unconnected") for u in d.get("unconnected_items", [])] + [dict(u, type="parity:"+u["type"]) for u in d.get("schematic_parity", [])]:
        if sys.argv[2] in v["type"]: print(" ", v["description"][:70], "|", " / ".join(i["description"][:80] for i in v.get("items", [])))
PY
