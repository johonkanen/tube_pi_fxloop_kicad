#!/bin/bash
# fab_outputs.sh : gerbers (4 layers, paste, silk, mask, outline), Excellon drill (PTH / NPTH) with maps,
# placement files (top = component side F, bottom = plate side B) and the BOM into rev_b/fab/;
# the zip, the placement files and the BOM are committed, the loose gerber/ folder is not.
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"; R="$L/.."; CLI="$R/../tools/p2k/bin/kicad-cli"; B="$R/kicad/tube_pi_fxloop_revb.kicad_pcb"; F="$R/fab"
rm -rf "$F"; mkdir -p "$F/gerber"
# plot from current zone fills: refill and save the board first (stale fills plot stale copper)
"$R/../tools/p2k/bin/kipy" ~/.claude/skills/kicad-agentic-routing/scripts/fill_zones.py "$B" "$B" >/dev/null 2>&1
$CLI pcb drc --severity-error --format json -o "$F/drc_unrefilled.json" "$B" >/dev/null 2>&1 || true
python3 -c "import json,sys; d=json.load(open('$F/drc_unrefilled.json')); n=len([v for v in d['violations'] if not v.get('excluded')]); u=len(d['unconnected_items']); print('DRC without refill:', n, 'errors,', u, 'unconnected'); sys.exit(1 if n or u else 0)"
rm -f "$F/drc_unrefilled.json"
$CLI pcb export gerbers -o "$F/gerber/" -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts "$B" >/dev/null
$CLI pcb export drill -o "$F/gerber/" --format excellon --excellon-separate-th --generate-map --map-format gerberx2 "$B" >/dev/null
$CLI pcb export pos -o "$F/tube_pi_fxloop_revb-pos-top.csv" --side front --format csv --units mm "$B" >/dev/null
$CLI pcb export pos -o "$F/tube_pi_fxloop_revb-pos-bottom.csv" --side back --format csv --units mm "$B" >/dev/null
cp "$R/bom/bom.csv" "$F/"
( cd "$F" && zip -qr tube_pi_fxloop_revb-gerbers.zip gerber )
ls -la "$F"
