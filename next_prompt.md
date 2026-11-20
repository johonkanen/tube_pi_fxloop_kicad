# Next prompt

**The conversion is complete** (Phases 0-5 done 2026-11-20; STATUS.md). There is no next conversion
session. `tools/check_all.sh` prints ALL CHECKS PASSED (STATUS.md "Last check output").

The board `kicad/tube_pi_fxloop.kicad_pcb` is still **generated** by `tools/make_pcb.sh`. Stopping
generation is the user's call at the first hand edit of the layout in KiCad; then remove the
`make_pcb.sh --check` step from `tools/check_all.sh` and record it in STATUS.md (STATUS.md "Phase 5",
"Left open / when the board stops being generated"). The amplifier master repo can add this repo as a
submodule (done from the master repo, not here).

## What remains open (report only, no conversion work)

Design findings about the original Proteus design (STATUS.md "Findings about the original design";
the conversion reproduces Proteus, these are for the redesign):

- 1: terminals `A`, `C'`, `D'` are not on the nets `A`, `C'`, `D'`.
- 2: one ground net `PWR-GND` joins the power returns and the signal ground.
- 5 / 14: page 1 hand note "R47 = 50-100k" (value 33k); a stray junction dot on page 2.
- 8 / 21: U4 device `12AX7` with value `12AT7`; C8 / C28 value `22u` with device `HITEMP10U50V`.
- 9 / 10 / 15: Proteus pin numbering oddities (C1 / C36 / C37 `+` = pin 2; relay G5V-2(HI) the mirror
  image of the Omron pinout; SW-SPDT own ids) - for the redesign's symbol / footprint pairs.
- 12 / 13: FX switch driver topology (PNP emitter on ground; SW4-SW6 short the 1M return resistors).
- 16 / 17: noval sockets: mirrored numbering (resolved by the bottom-side mounting, user 2026-11-20) and
  the 21.0 mm pitch circle with three mounting holes per socket - confirm on the real amplifier before
  the redesign reuses the footprint.
- 18: the 2010 drills were larger than the KiCad library drills kept (`DRILL_SMALLER`, user decision).
- 19: three dangling Proteus copper stubs, kept as drawn (user decision).
- 20: the 0.421 mm Proteus clearance at the TO-92 rows (redesign rules).
- 22: heaters in series across pins 4 / 5 (about 12.6 V per valve between PWRH4 and PWRH5).

Accepted DRC items (STATUS.md "Phase 5"): 40 courtyards_overlap and 7 pth_inside_courtyard (Proteus
placement vs KiCad courtyards), 55 silk warnings from the KiCad library graphics, 3 track_dangling
(Finding 19).

Shared-tool work for later, in one place with the ac_psu regression: STATUS.md "p2k candidates" 1-23.
