#!/bin/bash
# Placement: rev_b/kicad board from tools/make_pcb.py (fixed parts placed, the rest parked) ->
# KiCadRoutingTools place_simple with groups.json / intent.json (make_groups.py) -> build/placed.kicad_pcb.
# Deterministic for a given seed. Pattern: tube_preamp_kicad rev_b/layout/place.sh.
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"; B="$L/build"; KRT=~/dev/KiCadRoutingTools; PY="$KRT/.venv/bin/python -X utf8"
SEED=${SEED:-7}; P=tube_pi_fxloop_revb
mkdir -p "$B"
cp "$L/../kicad/$P."{kicad_pcb,kicad_pro,kicad_dru} "$B/"
LOCK=$(python3 -c "
import sys; sys.path.insert(0, '$L'); import placement as P
print(' '.join(['V1', 'V2'] + list(P.CONNECTORS) + list(P.PINNED) + list(P.PINNED_PIN1) + [h for h in P.HOLES_BOARD if h not in P.HOLE_DROPPED]))")
cd "$KRT"
$PY py_placer/place_pose.py "$B/$P.kicad_pcb" "$B/locked.kicad_pcb" lock $LOCK >/dev/null
$PY py_tools/check_floorplan.py "$B/locked.kicad_pcb" --emit-intent "$B/emitted_intent.json" >/dev/null || true
python3 "$L/make_groups.py" "$B/emitted_intent.json"
$PY py_placer/place_simple.py "$B/locked.kicad_pcb" "$B/placed.kicad_pcb" --groups "$L/groups.json" \
    --intent "$L/intent.json" --seed "$SEED" --halo-coef ${HALO:-0.5} --json "$B/placed.json" ${PLACE_ARGS:-} | grep -v "^  " | tail -5
