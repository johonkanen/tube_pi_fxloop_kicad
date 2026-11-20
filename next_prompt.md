# Next prompt

Ready-to-paste prompt for the next agent session (model: Opus). Replaced at the end of every session.

```
Convert the Proteus board in /home/jari/dev/tube_pi_fxloop_kicad to KiCad 10: Phase 3 (PCB).
Phases 0-2 are done: 4 sheets (126/126 parts, compare 0 wrong-net pins, 71/71 nets, ERC 0 / 0),
footprints (126/126 parts fit the IPC pads, worst 0.001 mm, reports/footprint_fit.csv), pin order
checked (tools/check_pin_order.py).

Read, in this order: PLAN.md, STATUS.md (Phase 2: footprint table, "Pad size / drill differences vs
Proteus" (open user decision), pin order; Findings 15-18; p2k candidates), tools/p2k/CONVERSION_PLAYBOOK.md
(section 3 "Phase 3" and section 5), tools/p2k/README.md (build_pcb, gerber_to_tracks, assign_nets,
check_board, drc, PCB_RULES, DRC_ACCEPTED). Run tools/check_all.sh first and compare with STATUS.md
"Last check output".

Model: the power amp pilot ~/dev/tube_power_amp_kicad (READ ONLY): tools/make_pcb.sh (build_pcb,
gerber_to_tracks, assign_nets; --check rebuilds in build/tmp and compares byte for byte),
tools/measure_gaps.py, p2k_config.py PCB_RULES / PCB_THICKNESS / DRC_ACCEPTED, STATUS.md "Phase 3".
The finished reference ~/dev/tube_psu_kicad (READ ONLY).

Board specifics: 2 copper layers, no pours (no pours_to_zones), 4 vias (0.508 / 1.27 mm: #00057,
PWR-GND x2, SWLOOP), 10 plated 3.0 mm mounting holes (HOLE_FOOTPRINT is set; six of them sit around
U4 / U5), 5 N/C pads (U4-9, U5-9, SERIES_MIX 6-8 -> unconnected-(...) nets), outline 225.425 x 71.755 mm.

Do:
1. tools/make_pcb.sh (as the pilot's, plus the vias) -> kicad/tube_pi_fxloop.kicad_pcb; --check in
   check_all.sh. Design rules measured on the Proteus copper (measure_gaps) -> PCB_RULES, PCB_THICKNESS
   (1.6 unless the sources say otherwise).
2. check_board, assign_nets --check (0 shorts / 0 orphans / 0 opens), p2k drc (0 shorts, 0 unconnected,
   0 parity); remaining DRC types in DRC_ACCEPTED with reasons (expect courtyard overlaps: the 21 mm
   noval courtyards, 100N rows 6.35 mm apart).
3. Pad sizes: FOOTPRINT_PAD_SIZES = "kicad" stays unless DRC forces a change; report the smallest gaps
   with the KiCad pads (the 2 W resistors have pads 2.4 vs Proteus 2.286). The drill differences (relay
   0.7 vs 1.143, C2 1.0 vs 1.143, MMK caps 0.75 vs 0.762) are the user's decision for Phase 4: do not
   decide them, keep them listed.
4. Negative tests (track moved, pad net edited, footprint moved, a via removed) and record them.

Rules (PLAN.md section 5): don't change tools/p2k or its pin (board-local workarounds, noted in STATUS.md
"p2k candidates"); use tools/compare.py, not p2k compare_netlists; don't touch other repos; report design
findings, don't fix them; keep the Proteus pads, ids and sides; temporary files in build/tmp; never run
the KiCad AppImage with --version (use tools/p2k/bin/kipy and tools/p2k/bin/kicad-cli). No symbol may use
the no_connect pin type (check_all.sh greps). At the end: STATUS.md updated (steps, rules, DRC items,
check output, findings, p2k candidates, decisions), next_prompt.md replaced with the Phase 4 prompt
(independent verification, preferably another model / clean context), commit and push (git push origin
main). If something needs a user decision, stop, record it in STATUS.md, commit and push, and report it.
```
