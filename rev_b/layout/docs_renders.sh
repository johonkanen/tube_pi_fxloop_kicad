#!/bin/bash
# docs_renders.sh BOARD : the review renders in rev_b/docs/ (2D per side and inner layers, 3D both sides)
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"; D="$L/../docs"; B=$1; CLI="$L/../../tools/p2k/bin/kicad-cli"
"$L/render.sh" "$B" "$D/layout_top.png" "F.Cu,F.SilkS,F.Fab,Edge.Cuts" 300
"$L/render.sh" "$B" "$D/layout_bottom.png" "B.Cu,B.SilkS,B.Fab,Edge.Cuts" 300
"$L/render.sh" "$B" "$D/layout_inner.png" "In1.Cu,In2.Cu,Edge.Cuts" 300
"$L/render.sh" "$B" "$D/layout_all_copper.png" "F.Cu,In1.Cu,In2.Cu,B.Cu,Edge.Cuts" 300
$CLI pcb render --side top --quality basic -w 2400 -h 900 --background opaque -o "$D/layout_3d_top.png" "$B" >/dev/null 2>&1 || true
$CLI pcb render --side bottom --quality basic -w 2400 -h 900 --background opaque -o "$D/layout_3d_bottom.png" "$B" >/dev/null 2>&1 || true
$CLI pcb render --rotate '-55,0,20' --perspective --quality basic -w 2400 -h 1200 --background opaque -o "$D/layout_3d_iso.png" "$B" >/dev/null 2>&1 || true
ls -la "$D"/layout_*.png
