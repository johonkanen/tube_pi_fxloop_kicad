# Conversion plan: Phase inverter + FX loop (`poweri`)

Goal: redraw the Proteus schematic in KiCad 10 and rebuild the PCB from the Proteus Gerber X2
export, so that every pad, track, via and pour carries a net from the new schematic, and **prove
with scripted checks** that the KiCad design is electrically identical to the Proteus one. The
result is **rev A, the as-built baseline** for the redesign (see README.md).

This plan follows the generic playbook **`tools/p2k/CONVERSION_PLAYBOOK.md`** (read it first) and
lists only what is specific to this board. The finished reference is `~/dev/tube_psu_kicad`
(same proteus2kicad version, Phases 0-5 done): look at its `tools/`, `p2k_config.py`, PLAN.md and
STATUS.md for how each step was done.

**Order:** Run after the power amp pilot has finished Phase 1 (or at least Phase 0), and read its STATUS.md findings first: same 2010 / Proteus 7 export, same kinds of fly-lead pads.

## 1. Inventory (measured in Phase 0, 2026-11-20)

| Item | Value |
|---|---|
| Proteus project | `source/poweri.pdsprj` (values, devices, packages, pin names via `p2k.pdsprj`) |
| Schematic PDF | `source/schematic_pdf/pi_fx_loop.PDF`, 4 pages, **no title blocks** (sheet names from the content, `p2k_config.py` SHEETS) |
| CADCAM export | `source/cadcam/` (Gerber X2, metric `FSLAX45Y45`, one `SameCoordinates` id, no arcs), with the IPC-D-356A netlist |
| IPC netlist (the reference) | `source/cadcam/pi_fx_loop - CADCAM Netlist.IPC` |
| Copper layers | 2 (Top, Bottom); **no pours** (no `G36` regions, no `%LPC%`) |
| Drill | only `Drill TOP-BOT Plated` (261 plated hits), no NonPlated file; the 2010 Excellon `source/fab_2010/poweri - CADCAM Drill.TXT` (inch, 261 hits, same frame) for the Phase 4 `DRILL_EXCELLON` cross-check |
| Outline | 225.425 x 71.755 mm at (-123.825, -78.105) (Mechanical 1) |
| IPC records | 261, all THT: 247 component pads + 4 vias + 10 holes; 0 SMD |
| IPC refdes fields | 124 (+ the blank one of vias / holes) → **126 parts** (`RETURN` is three terminals) |
| Parts | 87 components (R 42, C 16, D 12, Q 11, U4/U5, SW4-SW6, relay SERIES/MIX) + 39 single-pad terminals |
| Nets (IPC) | 66; no `=POWER` nets; 5 N/C pads (U4-9, U5-9, SERIES/MIX 6-8) |
| Vias | 4 (0.508 mm drill, 1.27 mm pad; nets #00057, PWR-GND x2, SWLOOP) |
| Mounting holes | 10 (3.0 mm plated, 6.35 mm pad on both layers; positions in README.md "Mechanical baseline") |
| Technology | through-hole only |

Pre-check corrections: 66 nets (not 67); 14 blank-refdes records = **4 vias + 10 holes** (not
14 vias); 126 parts = 87 components + 39 terminals (the PDF shows all 126; the pre-check's
"89 parts / 37 fly-lead pads" counted `RETURN` once and `SERIES` as a pad: `SERIES` is the
8-pin relay `SERIES/MIX`).

## 2. Board-specific notes and expected pitfalls

- Built about 2010; the export in `source/cadcam/` matches the June 2010 fab Gerbers exactly. The schematic `poweri.DSN` was saved in October 2010, after the layout. The PDF is named `pi_fx_loop.PDF`, the project `poweri.pdsprj`, the CADCAM export `pi_fx_loop`.
- 2 noval sockets (U4 12AT7 FX loop driver, U5 12AX7 phase inverter, 9 pins; pin 9 N/C on both).
- Pages (no title blocks): 1 FX loop driver (U4, SERIES/MIX relay), 2 PI supply and FX
  switching (Q4 IRF820, 2N3906 drivers), 3 Phase inverter (U5), 4 FX send and return (J112
  JFET switches, SW4-SW6).
- The 39 terminals (single pad, Proteus TERMINAL): `+6`, `-6`, `A`, `C'`, `D'`, `CHASSIS`,
  `EQGND`, `EQOUT`, `FB`, `FX`, `FX'`, `MV0`, `MVW`, `MVX`, `PGND`, `PIPOWER`, `PIRETURN`,
  `PREPOWER`, `PRERETURN`, `PRE-H4`, `PRE-H5`, `RETURN1`-`RETURN3`, `SEND`, `SEND1`-`SEND3`,
  `SEND1W`-`SEND3W`, `SIGNALGND`, `SUKKA`, `SW1`-`SW3`, `V6+V7`, `V8+V9`, `VREF`.
  Truncated in the IPC: `PIPOWE`, `PIRETU`, `PREPOW`, `PRERET`, `CHASSI`, `SIGNAL`, `SERIES`
  (relay `SERIES/MIX`), `RETURN` (3 parts, keyed by coordinate). KiCad refdes map for `+`, `-`,
  `'`, `/` names (`p2k_config.py`).
- `J112` in the PDF is the device of the JFETs Q1-Q3, Q5-Q7 and `J04` belongs to the capacitor
  value `MMK J04 5MM` (C4, C6, C7, C32): neither is a part (the 2010 review's "net labels" is
  inaccurate, same conclusion: not parts).
- `A`, `C'`, `D'` are both terminals (page 2, at R28 / R27 / R29) and net labels (pages 2, 4);
  the terminals are **not** on the nets `A`, `C'`, `D'` (terminal refdes are not net names).
- The PDF writes the nets `send` and `nolla` in lower case; IPC: `SEND`, `NOLLA` (Proteus
  net names ignore case: use the IPC spelling).

## 3. Phases

As in the playbook, section 3. Board-specific done criteria:

| Phase | Done when |
|---|---|
| 0 Skeleton and inventory | `p2k_config.py` complete (sheet names from the PDF title blocks, truncated-refdes table, KiCad refdes map, net aliases, expected IPC counts, layers, drills, outline); `p2k ipc356 --check` and `p2k check_sources` pass; `reference/` cheat sheets written; `tools/check_all.sh` runs; PLAN.md section 1 corrected with the measured inventory |
| 1 Schematic | all 124 parts drawn; `compare_netlists` 0 wrong-net pins, every IPC net complete; ERC 0 errors (warnings explained) |
| 2 Footprints | every part fits the IPC pads within 0.05 mm (`check_footprints`); pin-order oddities reported |
| 3 PCB | copper 0 shorts / 0 orphans / 0 opens after zone fill; DRC 0 shorts, 0 unconnected, 0 parity; remaining DRC items listed and justified; `make_pcb.sh --check` reproducible |
| 4 Verification | `gerber_roundtrip --check` and `ipc356_diff` pass and are in `check_all.sh`; every new check negative-tested; preferably a different session/model |
| 5 Clean-up | only the user's choices (pad sizes, silk, refdes positions) |

When all phases are done: STATUS.md says so, and the amplifier master repo can add this repo as a
submodule (that step is done from the master repo, not here).

## 4. Effort

The playbook's estimates are for a ~270-part, 4-layer, 11-sheet board. This board has
124 parts on 4 sheets and 2 copper layers: scale accordingly.

## 5. Rules for this conversion

Several board conversions run **in parallel**, each in its own repo and session. To keep them
independent:

1. **Don't change the shared tools** in `tools/p2k` (proteus2kicad), and don't move the submodule
   pin (c5682dd). If a tool can't handle something on this board, write a board-local script in
   `tools/` (or a config key the tool already has) and record it in STATUS.md under
   "p2k candidates", with what the shared tool would need. The tool changes are made later, in one
   place, with the ac_psu regression.
2. **Don't touch other repositories.** In particular not `~/dev/tube_amplifier_kicad` (the
   amplifier master repo: it adds this repo as a submodule once the conversion is verified) and not
   `~/dev/ac_psu_kicad` (another session's work in progress). `~/dev/tube_psu_kicad` is the
   finished reference: read it, don't change it.
3. **Reproduce Proteus.** Problems in the original design are reported in STATUS.md
   ("Findings"), not fixed. The redesign happens later, from this baseline.
4. **Generate, don't hand-edit** (playbook section 1): every file in `kicad/`, `lib/` and
   `reference/` is written by a script and is reproducible.
5. **Temporary files in `build/tmp/`** (git-ignored). Never run the KiCad AppImage with
   `--version` (it starts the GUI and hangs); use `tools/p2k/bin/kipy` and `tools/p2k/bin/kicad-cli`.
6. **Commit and push at the end of every phase** (and at the end of a session), with
   STATUS.md and next_prompt.md updated in the same commit.
7. **Ask the user** where the playbook says to (pad sizes when DRC forces them, Phase 5 choices,
   anything that changes the design).

## 6. Session protocol

- Start every session by reading PLAN.md, STATUS.md and `tools/p2k/CONVERSION_PLAYBOOK.md`, then
  run `tools/check_all.sh` (from Phase 0 on) and compare with the last result in STATUS.md.
- One session per phase (Phase 1 transcription may take several, a few sheets each).
- End every session with: `tools/check_all.sh` passing for everything done so far, STATUS.md
  updated (phase state, last check output, findings, p2k candidates, decisions), next_prompt.md
  replaced with the prompt for the next session, commit and push.
