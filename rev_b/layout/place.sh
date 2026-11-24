#!/bin/bash
# Placement: rev_b/kicad board from tools/make_pcb.py (fixed parts placed, the rest parked) ->
# KiCadRoutingTools place_simple with groups.json / intent.json (make_groups.py) -> build/placed.kicad_pcb.
# Deterministic for a given seed. Pattern: tube_preamp_kicad rev_b/layout/place.sh.
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"; B="$L/build"; KRT=~/dev/KiCadRoutingTools; PY="$KRT/.venv/bin/python -X utf8"
SEED=${SEED:-4}; HALO=${HALO:-0.3}; P=tube_pi_fxloop_revb   # default seed: see STATUS "Layout, first pass"
mkdir -p "$B"
cp "$L/../kicad/$P."{kicad_pcb,kicad_pro,kicad_dru} "$B/"
LOCK=$(python3 -c "
import sys; sys.path.insert(0, '$L'); import placement as P
print(' '.join(['V1', 'V2'] + list(P.CONNECTORS) + list(P.PINNED) + list(P.PINNED_PIN1) + [h for h in P.HOLES_BOARD if h not in P.HOLE_DROPPED]))")
cd "$KRT"
$PY py_placer/place_pose.py "$B/$P.kicad_pcb" "$B/locked.kicad_pcb" lock $LOCK >/dev/null
$PY py_tools/check_floorplan.py "$B/locked.kicad_pcb" --emit-intent "$B/emitted_intent.json" >/dev/null || true
python3 "$L/make_groups.py" "$B/emitted_intent.json"
if [ -z "${ANNEAL:-}" ] && [ -z "${SEEDS:-}" ]; then   # default: the committed placement snapshot (no anneal)
    "$L/../../tools/p2k/bin/kipy" "$L/snapshot.py" apply "$B/locked.kicad_pcb" "$L/placement_snapshot.json" "$B/placed.kicad_pcb" 2>&1 | grep -v "memory leak\|^$"
elif [ -n "${SEEDS:-}" ]; then      # several seeds in parallel; keep the one with the fewest illegal parts, then the lowest cost
    $PY py_placer/place_simple.py "$B/locked.kicad_pcb" "$B/placed_{seed}.kicad_pcb" --groups "$L/groups.json" \
        --intent "$L/intent.json" --seeds "$SEEDS" --jobs 8 --halo-coef ${HALO:-0.5} --json "$B/placed_{seed}.json" ${PLACE_ARGS:-} \
        | grep -v "^  " | tail -3
    best=$(python3 - "$B" "$SEEDS" <<'PY'
import json, sys
r = []
for s in sys.argv[2].split(","):
    try:
        d = json.load(open(f"{sys.argv[1]}/placed_{s}.json"))
        r.append((len(d["illegal"]), d["final"]["cost"], s))
        print(f"seed {s}: illegal {len(d['illegal'])}, cost {d['final']['cost']:.0f}, crossings {d['final']['crossings']}", file=sys.stderr)
    except (OSError, KeyError, ValueError):
        pass
print(min(r)[2])
PY
)
    echo "best seed $best"; cp "$B/placed_$best.kicad_pcb" "$B/placed.kicad_pcb"; cp "$B/placed_$best.json" "$B/placed.json"
else
    $PY py_placer/place_simple.py "$B/locked.kicad_pcb" "$B/placed.kicad_pcb" --groups "$L/groups.json" \
        --intent "$L/intent.json" --seed "$SEED" --halo-coef ${HALO:-0.5} --json "$B/placed.json" ${PLACE_ARGS:-} | grep -v "^  " | tail -5
fi
"$L/../../tools/p2k/bin/kipy" "$L/fix_place.py" "$B/placed.kicad_pcb" "$B/placed.kicad_pcb" 2>&1 | grep -v "memory leak\|^$"
# re-legalise after the nudges (moves only what a nudge made illegal)
cd "$KRT" && $PY py_placer/place_simple.py "$B/placed.kicad_pcb" "$B/placed.kicad_pcb" --groups "$L/groups.json" --intent "$L/intent.json" \
    --seed "$SEED" --halo-coef "$HALO" --legalise-only --json "$B/placed_legal.json" | grep -o '"illegal": \[[^]]*\]' | head -1
