# Next prompt

**The conversion is complete** (Phases 0-5 done 2026-11-20) and the **design fixes 2026-11-20** are done
(user decisions after the conversion; STATUS.md "Design fixes 2026-11-20"): relay SERIES_MIX on the Omron
G5V-2 pin numbers (Finding 15, `IPC_PIN_IDS` / `tools/ipc356.py`, copper unchanged), the three dangling
Proteus stubs removed (Finding 19, `REMOVED_TRACKS`), component values unchanged. `tools/check_all.sh`
prints ALL CHECKS PASSED (STATUS.md "Last check output").

## What remains (in this order)

1. **Shared-tool migration** (done by the session consolidating `tools/p2k`, not here; do not bump the
   pin from this repo on your own). Board-local pieces to fold into the shared tools or re-check after the
   pin bump (STATUS.md "p2k candidates" 1-25), in particular:
   - 24: `IPC_PIN_IDS` + `tools/ipc356.py` (pin id renaming of the IPC file; `check_all.sh` calls the
     wrapper instead of `p2k ipc356 --check`);
   - 25: `tools/make_pcb.sh` `run()` chained with `&&` (the other board repos have the unfixed `run()`),
     `tools/check_no_dangling.py` (p2k drc does not enforce warnings);
   - 9 / 19 `tools/compare.py`, 20 `tools/check_drill_smaller.py`, 22 `tools/excellon_metric.py`, 23 the
     `bottom` footprint spec in `tools/gen_footprints.py`.
   After the pin bump: `tools/check_all.sh` must still print ALL CHECKS PASSED with the board byte-identical
   (`make_pcb.sh --check`); record any difference in STATUS.md.
2. **Then stop generating the board** (user decision 2026-11-20: after the migration): remove the
   `make_pcb.sh --check` step from `tools/check_all.sh`, say so in STATUS.md (Phase 5 "Left open / when the
   board stops being generated"); check_board / assign_nets / DRC / check_no_dangling / ipc356_diff /
   gerber_roundtrip / check_drill_smaller keep working on the hand-edited board and show the intended
   differences (record them as deviations).

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
