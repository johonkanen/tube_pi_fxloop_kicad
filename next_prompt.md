# Next prompt

**The conversion is complete** (Phases 0-5 done 2026-11-20) and the **design fixes 2026-11-20** are done
(user decisions after the conversion; STATUS.md "Design fixes 2026-11-20"): relay SERIES_MIX on the Omron
G5V-2 pin numbers (Finding 15, `IPC_PIN_IDS`, copper unchanged), the three dangling
Proteus stubs removed (Finding 19, `REMOVED_TRACKS`), component values unchanged. `tools/check_all.sh`
prints ALL CHECKS PASSED (STATUS.md "Last check output"). The **shared-tool migration 2026-11-20** is done
(STATUS.md "Shared-tool migration 2026-11-20"): `tools/p2k` at proteus2kicad a9a286c, every board-local
workaround replaced by a shared tool / config key, re-baselines D-R / D-K2 / R1 only, strict opt-outs none.

## What remains

1. **Stop generating the board** - the user's call (Phase 5 decision: at the first manual layout change in
   KiCad, after the migration). Not done; nothing to do until the user says so. Then: remove the
   `make_pcb.sh --check` step from `tools/check_all.sh`, say so in STATUS.md (Phase 5 "Left open / when the
   board stops being generated"); check_board / assign_nets / DRC (`DRC_EXPECTED_WARNINGS`) / ipc356_diff /
   gerber_roundtrip (`DRILL_SMALLER` pad sets) keep working on the hand-edited board and show the intended
   differences (record them as deviations, e.g. `REMOVED_TRACKS` / `REMOVED_VIAS` or the deviation hooks).
2. The meta repo `tube_amplifier_kicad` bumps this submodule (coordinating session, after all boards).

Do not bump `tools/p2k` from this repo on your own; a later bump follows proteus2kicad's README "Changes
(upgrade notes)" and must leave `~/dev/proteus2kicad/tools/regress.sh <pin> tube_pi_fxloop_kicad` passing.

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
