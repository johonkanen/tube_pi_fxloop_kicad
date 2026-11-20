#!/usr/bin/env bash
# FROZEN HISTORY (user decision 2026-11-20, STATUS.md "Generation stopped 2026-11-20"): the board is no
# longer generated. kicad/tube_pi_fxloop.kicad_pcb is the source and is edited in KiCad; running this
# overwrites every hand edit with a rebuild from the schematic and the Proteus gerbers.
#
# It was: rebuild kicad/tube_pi_fxloop.kicad_pcb (p2k make_pcb, default PCB_STEPS: build_pcb,
# gerber_to_tracks, assign_nets, place_refdes; no pours); --check rebuilt into build/tmp and compared.
#   tools/generate/make_pcb.sh --force-regenerate [--check]
set -u
cd "$(dirname "$0")/../.."
force=0; args=()
for a in "$@"; do
    if [ "$a" = "--force-regenerate" ]; then force=1; else args+=("$a"); fi
done
if [ $force -ne 1 ]; then
    echo "make_pcb.sh: refused. The board is no longer generated (user decision 2026-11-20);" >&2
    echo "  kicad/tube_pi_fxloop.kicad_pcb is the source, edit it in KiCad. A rebuild would discard" >&2
    echo "  every hand edit. Only with --force-regenerate (and only if you mean it)." >&2
    exit 2
fi
exec tools/p2k/bin/p2k make_pcb ${args[@]+"${args[@]}"}
