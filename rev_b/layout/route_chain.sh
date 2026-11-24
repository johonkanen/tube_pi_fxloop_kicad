#!/bin/bash
# Routing chain (kicad-agentic-routing pattern; tube_preamp_kicad rev_b/layout/route_chain.sh):
# build/placed.kicad_pcb (place.sh) -> build/route/NN_*.kicad_pcb -> build/routed.kicad_pcb.
# One KRT step per net group (routing.json, from make_routing.py); each step's nets locked before the next.
#   ./route_chain.sh [FROM [LAST]]   (step numbers; resumes from build/route/<FROM-1>_*.kicad_pcb)
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"; R="$L/build/route"; S=~/.claude/skills/kicad-agentic-routing/scripts
REPO="$(cd "$L/../.." && pwd)"; P=tube_pi_fxloop_revb; KP="$REPO/tools/p2k/bin/kipy"
export ROUTING_CONFIG="$L/routing.json" KICAD_PYTHON="$KP"
FROM=${1:-0}; LAST=${2:-99}
mkdir -p "$R"
prev() { ls "$R"/$(printf %02d $(( $1 - 1 )))_*.kicad_pcb 2>/dev/null | head -1 || true; }
sib() { for x in pro dru; do cp "$L/../kicad/$P.kicad_$x" "${1%.kicad_pcb}.kicad_$x"; done; }
step() {   # step N NAME GROUP [route.py opts]
    local n=$1 name=$2 grp=$3; shift 3
    [ "$n" -lt "$FROM" ] || [ "$n" -gt "$LAST" ] && return 0
    local in; in=$(prev "$n")
    local out="$R/$(printf %02d "$n")_$name.kicad_pcb"
    echo "== $n $name ($grp)"
    python3 -I "$S/route_step.py" "$in" "$out" "$grp" "$@" || true
    [ -f "$out" ] || cp "$in" "$out"
    sib "$out"
    source "$S/kenv.sh"; kpy "$S/lock_tracks.py" "$out" lock "$grp" >/dev/null
}
if [ "$FROM" -le 0 ] && [ "$LAST" -ge 0 ]; then
    echo "== 0 prep: heater pair, drain pours"
    rm -f "$R"/[0-9][0-9]_*
    out="$R/00_prep.kicad_pcb"; sib "$out"
    $KP "$L/draw_heater.py" "$L/build/placed.kicad_pcb" "$out" 2>&1 | grep -v "memory leak"
    $KP "$L/draw_pours.py" "$out" "$out" 2>&1 | grep -v "memory leak"
fi
step 1 hv hv --via-cost 100
step 2 mv mv --via-cost 100
step 3 hiz hiz --via-cost 60
step 4 audio audio
step 5 coil coil
step 6 gate gate --grid-step 0.05
step 7 logic logic --grid-step 0.05
step 8 supply supply --grid-step 0.05 --power-nets "+5V" "+15V" "-15V" "GNDD" --power-nets-widths 0.5 0.4 0.4 0.5
step 9 leftover hv,mv,hiz,audio,coil,gate,logic,supply --max-iterations 20000000 --layer-costs 1 1
# GND pours on F and B (KRT route_planes), then repair islands, HIZ cuts, refill (finalize.py)
if [ 10 -ge "$FROM" ] && [ 10 -le "$LAST" ]; then
    echo "== 10 gnd pours"
    in=$(prev 10); out="$R/10_gnd.kicad_pcb"; sib "$out"
    ( cd ~/dev/KiCadRoutingTools && .venv/bin/python -X utf8 py_router/route_planes.py "$in" "$out" \
        --nets GND GND --plane-layers F.Cu B.Cu --stitch-vias --stitch-pitch 8 --via-size 0.8 --via-drill 0.3 \
        --escalation board --no-fix-drc-settings > "${out%.kicad_pcb}.log" 2>&1 ) || { tail -20 "${out%.kicad_pcb}.log"; exit 1; }
    grep -E "^(Total|Planes|.*islands?|.*unconnected)" "${out%.kicad_pcb}.log" | tail -6 || true
fi
if [ 11 -ge "$FROM" ] && [ 11 -le "$LAST" ]; then
    echo "== 11 gnd repair + finalize"
    in=$(prev 11); out="$R/11_final.kicad_pcb"; sib "$out"
    ( cd ~/dev/KiCadRoutingTools && .venv/bin/python -X utf8 py_router/repair_planes.py "$in" --output "$out" \
        --nets GND GND --plane-layers F.Cu B.Cu --via-size 0.8 --via-drill 0.3 --escalation board --no-fix-drc-settings \
        > "${out%.kicad_pcb}.log" 2>&1 ) || { tail -20 "${out%.kicad_pcb}.log"; cp "$in" "$out"; }
    $KP "$L/finalize.py" "$out" "$out" 2>&1 | grep -v "memory leak"
    cp "$out" "$L/build/routed.kicad_pcb"; sib "$L/build/routed.kicad_pcb"
fi
