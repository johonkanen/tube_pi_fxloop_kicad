#!/usr/bin/env bash
# Phase 3: rebuild kicad/tube_pi_fxloop.kicad_pcb (p2k make_pcb, default PCB_STEPS: build_pcb,
# gerber_to_tracks, assign_nets, place_refdes; no pours). --check: rebuild into build/tmp and compare.
# Kept as a one-liner because the p2k regression harness calls tools/make_pcb.sh.
exec tools/p2k/bin/p2k make_pcb "$@"
