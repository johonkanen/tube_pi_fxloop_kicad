#!/usr/bin/env bash
# Run every verification step. Exit status is non-zero if any step fails.
# Each phase adds its steps here (playbook principle 5, PLAN.md section 3).
# The tools are the proteus2kicad submodule in tools/p2k; board values in p2k_config.py.
set -u
cd "$(dirname "$0")/.."
[ -x tools/p2k/bin/p2k ] || { echo "tools/p2k missing: git submodule update --init"; exit 1; }
fail=0
mkdir -p build/tmp
log=build/tmp/check_all.log; : > "$log"
step() {
    echo "== $1" | tee -a "$log"; shift
    "$@" 2>&1 | tee -a "$log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "!! FAILED: $*" | tee -a "$log"; fail=1; }
}

# Phase 0: environment and sources
step "KiCad environment" tools/p2k/bin/kipy -c "import pcbnew; v = pcbnew.GetBuildVersion(); print('pcbnew', v); assert v.startswith('10.0.7'), v"
# p2k ipc356 renames the relay SERIES_MIX pin ids to the Omron ids (IPC_PIN_IDS)
step "IPC-D-356A parser self-check" tools/p2k/bin/p2k ipc356 --check
step "Gerber X2 export vs IPC (pads, vias, holes, drills, outline)" tools/p2k/bin/p2k check_sources
# Phase 1: schematic
step "Part map up to date" python3 tools/make_part_map.py --check
step "Symbol library up to date" python3 tools/gen_symbols.py --check
step "Symbol pin sets vs IPC" tools/p2k/bin/p2k check_symbols
step "ERC" tools/p2k/bin/p2k erc
step "Sheet scripts reproduce kicad/*.kicad_sch" tools/p2k/bin/p2k sheets --check
step "Netlist comparison vs IPC" tools/p2k/bin/p2k compare_netlists
# Phase 2: footprints
step "Footprint library, map and fp-lib-table up to date" python3 tools/gen_footprints.py --check
step "Footprints vs IPC pad geometry" tools/p2k/bin/kipy -m p2k.check_footprints --pcbnew
step "Pin order vs unmoved KiCad base footprints" tools/p2k/bin/p2k check_pin_order
# Phase 3: PCB (build_pcb, gerber_to_tracks with the 4 vias, assign_nets; no pours)
step "PCB rebuilt from schematic + gerbers, up to date" tools/make_pcb.sh --check
step "Board pads, holes, vias vs IPC (position, size, nets 1:1)" tools/p2k/bin/kipy -m p2k.check_board
step "Board copper connectivity (KiCad geometry)" tools/p2k/bin/kipy -m p2k.assign_nets --check
# DRC_EXPECTED_WARNINGS: 0 track_dangling / via_dangling (the removed Proteus stubs, REMOVED_TRACKS)
step "DRC with schematic parity" tools/p2k/bin/p2k drc
# Phase 4: independent verification (kicad-cli IPC-D-356 export and gerber plot of the board vs Proteus).
# DRILL_SMALLER (p2k_config.py, pad sets) accepts exactly the 18 decided holes of the three drill pairs.
step "IPC-D-356 from the board vs Proteus (pads, vias, holes, nets)" tools/p2k/bin/p2k ipc356_diff
step "Gerber round trip vs Proteus (copper XOR, coverage, drills, 2010 Excellon)" tools/p2k/bin/p2k gerber_roundtrip --check

echo
pending=$(grep -c "PENDING USER DECISION" "$log")
if [ $fail -ne 0 ]; then echo "SOME CHECKS FAILED"
elif [ "$pending" -ne 0 ]; then echo "ALL CHECKS PASSED, EXCEPT $pending PENDING USER DECISION(S):"; grep "PENDING USER DECISION" "$log" | sed 's/^/  /'
else echo "ALL CHECKS PASSED"; fi
exit $fail
