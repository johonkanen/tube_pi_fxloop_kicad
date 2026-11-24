#!/bin/bash
# Routing chain (kicad-agentic-routing pattern; tube_preamp_kicad rev_b/layout/route_chain.sh):
# build/placed.kicad_pcb (place.sh) -> build/route/NN_*.kicad_pcb -> build/routed.kicad_pcb.
# One KRT step per net group (routing.json, from make_routing.py); each step's nets locked before the next.
#   ./route_chain.sh [FROM [LAST]]   (step numbers; resumes from build/route/<FROM-1>_*.kicad_pcb)
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"; R="${RDIR:-$L/build/route}"; PLACED="${PLACED:-$L/build/placed.kicad_pcb}"; S=~/.claude/skills/kicad-agentic-routing/scripts
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
    source "$S/kenv.sh"
    for g in ${grp//,/ }; do kpy "$S/lock_tracks.py" "$out" lock "$g" >/dev/null || true; done
}
unlock() {   # unlock N GROUP...: unlock the given groups on the previous step's board (in place)
    local in; in=$(prev "$1"); shift
    [ -n "$in" ] || return 0
    $KP "$L/unlock_groups.py" "$in" "$@" 2>&1 | grep -v "memory leak\|^$"
}
if [ "$FROM" -le 0 ] && [ "$LAST" -ge 0 ]; then
    echo "== 0 prep: heater pair, drain pours"
    rm -f "$R"/[0-9][0-9]_*
    out="$R/00_prep.kicad_pcb"; sib "$out"
    $KP "$L/draw_heater.py" "$PLACED" "$out" 2>&1 | grep -v "memory leak"
    $KP "$L/draw_pours.py" "$out" "$out" 2>&1 | grep -v "memory leak"
    $KP "$L/draw_escapes.py" "$out" "$out" 2>&1 | grep -v "memory leak"
fi
step 1 hv hv --via-cost 100 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1 4 4 1.5
step 2 mv mv --via-cost 100 --layers F.Cu B.Cu --layer-costs 1 1.5
step 3 hiz hiz --via-cost 60
step 4 audio audio
step 5 supply supply --grid-step 0.05 --power-nets "+5V" "+15V" "-15V" "GNDD" --power-nets-widths 0.5 0.4 0.4 0.5
step 6 logic logic --grid-step 0.05 --ordering original
step 7 coil coil
step 8 gate gate --grid-step 0.05
# leftovers: the logic and gate nets unlocked so KRT may rip and re-route them around the last opens
if [ 9 -ge "$FROM" ] && [ 9 -le "$LAST" ]; then unlock 9 logic gate coil supply audio; fi
KICAD_RIP_PREEXISTING=1 step 9 leftover logic,gate,coil,supply,hiz,audio --max-iterations 20000000 --layer-costs 1 1 1 1 --grid-step 0.05
step 10 leftover_hv hv,mv --max-iterations 20000000 --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1 3 3 1
# GND pours on F and B (KRT route_planes), then repair islands, HIZ cuts, refill (finalize.py)
if [ 11 -ge "$FROM" ] && [ 11 -le "$LAST" ]; then
    echo "== 11 gnd pours"
    in=$(prev 11); out="$R/11_gnd.kicad_pcb"; sib "$out"
    ( cd ~/dev/KiCadRoutingTools && .venv/bin/python -X utf8 py_router/route_planes.py "$in" "$out" \
        --nets GND GND --plane-layers F.Cu B.Cu --stitch-vias --stitch-pitch 8 --via-size 0.8 --via-drill 0.3 \
        --escalation board --no-fix-drc-settings > "${out%.kicad_pcb}.log" 2>&1 ) || { tail -20 "${out%.kicad_pcb}.log"; exit 1; }
    grep -E "^(Total|Planes|.*islands?|.*unconnected)" "${out%.kicad_pcb}.log" | tail -6 || true
fi
if [ 12 -ge "$FROM" ] && [ 12 -le "$LAST" ]; then
    echo "== 12 gnd repair + finalize"
    in=$(prev 12); out="$R/12_final.kicad_pcb"; sib "$out"
    ( cd ~/dev/KiCadRoutingTools && .venv/bin/python -X utf8 py_router/repair_planes.py "$in" --output "$out" \
        --nets GND GND --plane-layers F.Cu B.Cu --via-size 0.8 --via-drill 0.3 --escalation board --no-fix-drc-settings \
        > "${out%.kicad_pcb}.log" 2>&1 ) || { tail -20 "${out%.kicad_pcb}.log"; cp "$in" "$out"; }
    $KP "$L/finalize.py" "$out" "$out" 2>&1 | grep -v "memory leak"
fi
# GND pads the pours could not reach (parts walled in on B): tracks, then a refill
step 13 gnd_tracks GND --power-nets GND --power-nets-widths 0.4 --max-iterations 5000000
if [ 13 -ge "$FROM" ] && [ 13 -le "$LAST" ]; then
    out="$R/13_gnd_tracks.kicad_pcb"
    source "$S/kenv.sh"; kpy "$S/fill_zones.py" "$out" "$out" >/dev/null 2>&1 || true
    cp "$out" "$R/../routed.kicad_pcb"; sib "$R/../routed.kicad_pcb"
fi
