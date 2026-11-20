# tube_pi_fxloop_kicad

KiCad 10 migration of the phase inverter and all-tube effects loop board (`poweri`) of the tube amplifier, from Proteus. The schematic is redrawn from
the Proteus PDF and the PCB is rebuilt from the Gerber X2 export, so that every pad, track,
via and pour carries a net from the new schematic. The IPC-D-356A netlist of the CADCAM export
is the reference that every check compares against.

This is **rev A, the as-built baseline**. The redesign (ribbon cables, PCB-mount pots, the new
power section) starts from it. The amplifier project, its specification and the hardware state
are in [tube_amplifier_kicad](https://github.com/johonkanen/tube_amplifier_kicad), which includes
this repo as a submodule once the conversion is verified.

## Method

The shared [proteus2kicad](https://github.com/johonkanen/proteus2kicad) tools, a submodule in
`tools/p2k` (clone with `git clone --recurse-submodules`, or run `git submodule update --init`).
The phases and checks are in `tools/p2k/CONVERSION_PLAYBOOK.md`. Everything specific to this
board is in `p2k_config.py`.

## Status

Conversion plan: [PLAN.md](PLAN.md); progress: [STATUS.md](STATUS.md); prompt for the next agent session: [next_prompt.md](next_prompt.md).

Phase 0 (skeleton and inventory) done: `p2k_config.py` complete, `reference/` cheat sheets
written from the IPC netlist, `tools/check_all.sh` passes. Phase 1 (schematic, 4 sheets, 126 parts) is done and matches the IPC netlist. Phase 2 (footprints) is done: every part fits the IPC pads (`lib/tube_pi_fxloop.pretty`, `lib/footprint_map.csv`). User decisions 2026-11-20: the KiCad drills stay where they are smaller than Proteus (`DRILL_SMALLER`), and the noval sockets U4 / U5 are on the bottom side. Phase 3 (PCB): `kicad/tube_pi_fxloop.kicad_pcb` was generated from the schematic and the Proteus gerbers (now frozen in `tools/generate/`) with every pad, track and via on its IPC net (0 shorts / 0 orphans / 0 opens) and DRC clean (0 unaccepted errors, 0 unconnected, 0 parity) is done; the TO-92 pad 1 is round at the KiCad size 1.5 mm (user decision 2026-11-20), pin 1 marked by a silk dot. Phase 4 (independent verification, clean context) is done: the board's IPC-D-356 export equals the Proteus netlist (261 / 261 records, 66 nets 1:1), the gerber round trip finds only pad-shape differences (0 unexplained, drills 261 / 261, the June 2010 Excellon file 261 / 261), an independent reading of all four PDF pages agrees with the IPC netlist, and every new check is negative-tested. Phase 5 (clean-up) is done: the noval sockets U4 / U5 are on the bottom (solder) side with the standard noval numbering (footprint built mirrored, copper unchanged), references are placed by `p2k place_refdes` as the last `make_pcb.sh` step, and the rest (the TO-92 pin-1 dot, KiCad library graphics and pad sizes, sheet names, 1.6 mm) is kept as the user decided. **The conversion is complete** (`tools/check_all.sh`: ALL CHECKS PASSED). **Design fixes 2026-11-20** (user decisions after the conversion, STATUS.md "Design fixes 2026-11-20"): the relay SERIES_MIX uses the Omron G5V-2 pin numbers on symbol and footprint (KiCad's Relay:G5V-2 / Relay_DPDT_Omron_G5V-2 unchanged; the IPC pin ids are renamed by `p2k ipc356`, `IPC_PIN_IDS`; same copper and nets, Finding 15) and the three dangling Proteus copper stubs are removed (`REMOVED_TRACKS`, Finding 19); component values are unchanged as built. **Shared-tool migration 2026-11-20** (STATUS.md "Shared-tool migration 2026-11-20"): `tools/p2k` is at proteus2kicad a9a286c and every board-local workaround is replaced by a shared tool or config key (part map, ERC, sheets, netlist comparison, pin order, IPC pin renaming, DRC warning counts, drill pad sets, the 2010 Excellon read in inch, `p2k make_pcb`); the only generated-file changes are the accepted re-baselines D-R (cheat-sheet texts), D-K2 (5 capacitor text angles on sheets 1 and 3) and R1 (Excellon file name in the round-trip report). **Generation stopped 2026-11-20** (user decision; STATUS.md "Generation stopped 2026-11-20"): the board is no longer generated from the Proteus data (last generated commit 116d923); the committed KiCad files are the source. Open items are report-only design findings (STATUS.md "Findings").

Built in about 2010. The export in `source/cadcam/` matches the June 2010 fab Gerbers (`source/fab_2010/`) exactly: every hole and track. The schematic (`poweri.DSN`) was saved in October 2010, after the layout; all 126 board parts (87 components, 39 terminals) are in the PDF.

## Working on the board (since 2026-11-20)

The committed KiCad files are the source; edit them in KiCad (`kicad/tube_pi_fxloop.kicad_pro`):
schematic `kicad/*.kicad_sch`, board `kicad/tube_pi_fxloop.kicad_pcb`, symbols
`lib/tube_pi_fxloop.kicad_sym`, footprints `lib/tube_pi_fxloop.pretty/` (`lib/footprint_map.csv`,
`lib/part_map.csv` are records of rev A). **Do not run the generators** in `tools/generate/` (frozen
history; they would overwrite the hand edits; `make_pcb.sh` refuses without `--force-regenerate`).

After an edit run `tools/check_all.sh`. It checks the committed files against the Proteus truth
(`reference/`, `source/`: netlist, pads, copper, drills) and KiCad's rules (ERC, DRC with schematic
parity). A copper-neutral edit (silk, references) passes as it is. An intended change of the copper or
the netlist makes a check fail on purpose: record it as a deviation with a reason in `p2k_config.py`
(`REMOVED_TRACKS` / `REMOVED_VIAS`, the round-trip deviation hooks, `PHASE4_EXPECTED`, `DRC_ACCEPTED`,
`STRICT_CHECKS_OFF`) and in STATUS.md; never remove a check to make it pass.

## Source

poweri.DSN/.LYT (Proteus 7, 2010), opened and saved in Proteus 8.12 as `poweri.pdsprj`. Exported 2026-11-19 from Proteus 8.12 SP2: schematic PDF, Gerber X2 CADCAM (metric)
with the IPC-D-356A netlist.

## Mechanical baseline

From the export (the fit reference for the redesign; the KiCad file is
`mechanical/pi_fxloop_poweri.kicad_pcb` in tube_amplifier_kicad):

```
outline: 225.43 x 71.76 mm, lower-left corner at (-123.825, -78.105) in the Proteus frame
copper layers: 2; components: 124; mounting holes: 10
mounting holes (relative to the lower-left outline corner, mm):
  H1: x  183.825  y   64.105  drill 3.00 plated
  H2: x  152.825  y   59.605  drill 3.00 plated
  H3: x  174.825  y   37.105  drill 3.00 plated
  H4: x  220.825  y   67.105  drill 3.00 plated
  H5: x  220.825  y    5.105  drill 3.00 plated
  H6: x   54.825  y   37.105  drill 3.00 plated
  H7: x   29.825  y   59.605  drill 3.00 plated
  H8: x   60.825  y   64.105  drill 3.00 plated
  H9: x    4.825  y   67.105  drill 3.00 plated
  H10: x    4.825  y    5.105  drill 3.00 plated
```

## Layout

```
source/         Proteus exports (read-only)
  cadcam/         Gerber X2 export with the IPC-D-356A netlist (the reference)
  schematic_pdf/  schematic PDF to redraw from
  *.pdsprj        Proteus project (schematic values, devices, packages, pin names)
  fab_2010/       the RS-274X Gerbers the boards were made from (June 2010)
tools/p2k/       proteus2kicad (submodule)
reference/      tables derived from the IPC netlist (generated by p2k ipc356; IPC_PIN_IDS renames
                  the relay SERIES_MIX pins to the Omron numbers)
tools/check_all.sh  every verification step (against the Proteus truth and KiCad rules)
tools/generate/  the frozen generators of rev A (history, do not run; see its README)
kicad/, lib/     the KiCad design (the source since 2026-11-20)
p2k_config.py   board configuration for the tools
```
