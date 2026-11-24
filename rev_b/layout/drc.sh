#!/bin/bash
# drc.sh BOARD [TYPE] : kicad-cli DRC (zones refilled, schematic parity) graded against rev_b/kicad's own rules
# -> BOARD.drc.json, summary by type; TYPE lists the violations of one type.
set -euo pipefail
B=$1; L="$(cd "$(dirname "$0")" && pwd)"; CLI="$L/../../tools/p2k/bin/kicad-cli"; P="$L/../kicad/tube_pi_fxloop_revb"
for x in pro dru; do cp "$P.kicad_$x" "${B%.kicad_pcb}.kicad_$x"; done
$CLI pcb drc --refill-zones --format json --severity-error -o "${B%.kicad_pcb}.drc.json" "$B" >/dev/null 2>&1 || true
python3 - "${B%.kicad_pcb}.drc.json" "${2:-}" <<'PY'
import json,sys,collections
d=json.load(open(sys.argv[1])); c=collections.Counter(v["type"] for v in d["violations"])
print("violations:", dict(c), "| unconnected:", len(d.get("unconnected_items",[])))
if sys.argv[2]:
    for v in d["violations"] + [dict(u, type="unconnected") for u in d.get("unconnected_items", [])]:
        if sys.argv[2] in v["type"]: print(" ", v["description"][:60], "|", " / ".join(i["description"][:80] for i in v["items"]))
PY
