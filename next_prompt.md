# Next prompt

**The conversion is complete** (Phases 0-5 done 2026-11-20), the **design fixes 2026-11-20** and the
**shared-tool migration 2026-11-20** are done, and **generation stopped 2026-11-20** (user decision;
STATUS.md "Generation stopped 2026-11-20"): the board is no longer generated from the Proteus data (last
generated commit 116d923). The committed KiCad files (`kicad/`, `lib/`) are the source, edited in KiCad -
the clean starting point for the redesign. The generators are frozen history in `tools/generate/` (do not
run them; `make_pcb.sh` refuses without `--force-regenerate`). `tools/check_all.sh` (13 steps, no
regeneration) prints ALL CHECKS PASSED (STATUS.md "Last check output").

## Working on the board

Edit in KiCad, then run `tools/check_all.sh`. Copper-neutral edits pass. An intended change of copper or
netlist fails a check on purpose: record it as a deviation with a reason in `p2k_config.py`
(`REMOVED_TRACKS` / `REMOVED_VIAS`, round-trip deviation hooks `in_area` / `added` / `extra_vias`,
`PHASE4_EXPECTED`, `DRC_ACCEPTED`, `STRICT_CHECKS_OFF`) and in STATUS.md - never by removing a check.

## What remains

1. The redesign (ribbon cables, PCB-mount pots, the new power section) - the user's plan, from this board.
2. The meta repo `tube_amplifier_kicad` bumps this submodule (coordinating session).
3. proteus2kicad's `tools/regress.sh` regenerates board files with the board's own scripts; for this board
   pin it at 116d923 (last generated commit) or add a check-only mode in proteus2kicad (not done here).

Do not bump `tools/p2k` from this repo on your own; a later bump follows proteus2kicad's README "Changes
(upgrade notes)" and must leave `tools/check_all.sh` passing (and `~/dev/proteus2kicad/tools/regress.sh <pin> tube_pi_fxloop_kicad@116d923`).

## Report-only design findings (for the redesign; STATUS.md "Findings about the original design")

- 1: terminals `A`, `C'`, `D'` are not on the nets `A`, `C'`, `D'`.
- 2: one ground net `PWR-GND` joins the power returns and the signal ground.
- 5 / 8 / 21: values kept as built (user): R47 33k (hand note "50-100k"), U4 device `12AX7` with value
  `12AT7`, C8 / C28 `22u` with device `HITEMP10U50V`.
- 9 / 10: C1 / C36 / C37 `+` = pin 2; SW-SPDT own ids (NO=1 NC=2 COM=3).
- 12 / 13: FX switch driver topology (PNP emitter on ground; SW4-SW6 short the 1M return resistors).
- 17: the 21.0 mm noval pitch circle with three mounting holes per socket - confirm on the real amplifier.
- 18: the 2010 drills were larger than the KiCad drills kept (`DRILL_SMALLER`, user decision).
- 20: the 0.421 mm Proteus clearance at the TO-92 rows (redesign rules).
- 22: heaters in series across pins 4 / 5 (about 12.6 V per valve between PWRH4 and PWRH5).
- Fixed: 15 (relay Omron pins), 16 (noval sockets on the bottom side, Phase 5), 19 (stubs removed).

Accepted DRC items (STATUS.md "Phase 5", "Design fixes 2026-11-20"): 40 courtyards_overlap and 7
pth_inside_courtyard (Proteus placement vs KiCad courtyards), 55 silk warnings from the KiCad library
graphics; no track_dangling any more.
