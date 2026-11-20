# Status: Phase inverter + FX loop (`poweri`)

Plan: [PLAN.md](PLAN.md). Playbook: `tools/p2k/CONVERSION_PLAYBOOK.md`.

| Phase | State |
|---|---|
| 0 Skeleton and inventory | **done** 2026-11-20 (Opus 5.5) |
| 1 Schematic | not started; next: preparation (next_prompt.md) |
| 2 Footprints | not started |
| 3 PCB | not started |
| 4 Verification | not started |
| 5 Clean-up | not started |

## Phase 0 – done (Opus 5.5, 2026-11-20)

- **Inventory measured** (PLAN.md section 1 corrected): 66 nets, 261 IPC records, all THT
  (247 component pads + 4 vias + 10 plated 3.0 mm mounting holes), 0 SMD, 5 N/C pads, 0 free
  pads, **no pours** (no `G36` / `%LPC%`), no arcs, 2 copper layers, outline 225.425 x 71.755 mm
  at (-123.825, -78.105). 124 IPC refdes fields → **126 parts** = 87 components + 39 terminals.
  Corrections to the pre-check: 66 nets (not 67); the 14 blank-refdes records are 4 vias
  (0.508 mm drill, 1.27 mm pad) + 10 holes (not 14 vias); `RETURN` is three terminals
  (RETURN1-3); `SERIES` is not a fly-lead pad but the 8-pin relay `SERIES/MIX` (G5V-2(HI));
  the PDF shows all 126 parts (not 89); `PIPOWE`/`PIRETU`/`PREPOW`/`PRERET`/`CHASSI`/`SIGNAL`
  are truncations of PIPOWER, PIRETURN, PREPOWER, PRERETURN, CHASSIS, SIGNALGND.
- **PDF:** 4 pages, rendered with `pdftoppm -r 200 -png source/schematic_pdf/pi_fx_loop.PDF
  build/tmp/pdf/hi` (`hi-1..4.png`, git-ignored; re-render in later sessions). As on the power
  amp board the 2010 pages have **no title block**; the SHEETS names describe the content:
  1 **FX loop driver** (U4 12AT7, relay SERIES/MIX, EQOUT/EQGND, MVX, PRE-H4/H5; 24 parts),
  2 **PI supply and FX switching** (Q4 IRF820 source follower, zeners D3-D6, RC filter
  R66/R67/C36/C37/C1 to the nets F/G/H, 2N3906 drivers Q8/Q10/Q20/Q90, SW1-SW3/FX diode OR to
  SWLOOP; 46 parts), 3 **Phase inverter** (U5 12AX7 long-tail pair, V6+V7 / V8+V9 outputs,
  MVW/MV0, FB; 24 parts), 4 **FX send and return** (J112 JFET shunt switches Q1-Q3, Q5-Q7,
  SEND*, RETURN1-3, SW4-SW6; 32 parts). Every IPC refdes is in the PDF text layer (checked with
  `pdftotext`); `A`, `C'`, `D'` appear on pages 2 and 4 because they are net labels as well
  (the terminals are on page 2).
- **`p2k_config.py`** complete for Phase 0: SHEETS, `TRUNCATED_REFDES` (+ `TRUNCATED_NETS`),
  `KICAD_REFDES`, `NET_ALIASES` (empty), blank-refdes drills, `EXPECTED_IPC`, `COPPER`, drills,
  outline. Tables:

  | IPC field | Full Proteus refdes | Net (check) |
  |---|---|---|
  | `PIPOWE` | PIPOWER | `#00028` (Q4-2, R9-2) |
  | `PIRETU` | PIRETURN | `PWR-GND` |
  | `PREPOW` | PREPOWER | `F` |
  | `PRERET` | PRERETURN | `PWR-GND` |
  | `CHASSI` | CHASSIS | `PWR-GND` |
  | `SIGNAL` | SIGNALGND | `PWR-GND` |
  | `SERIES` | SERIES/MIX (relay, 8 pins) | several (not in TRUNCATED_NETS) |
  | `RETURN` @ (0.000, -57.150) | RETURN1 | `#00078` (SW4-2) |
  | `RETURN` @ (9.525, -57.150) | RETURN2 | `#00079` (SW6-2) |
  | `RETURN` @ (19.050, -57.150) | RETURN3 | `#00080` (SW5-2) |

  `EQOUT`, `EQGND`, `SEND1W`-`SEND3W`, `PRE-H4`, `PRE-H5` are complete (PDF agrees).

  | Proteus refdes | KiCad refdes |
  |---|---|
  | `+6` / `-6` | `P6` / `N6` |
  | `PRE-H4` / `PRE-H5` | `PRE_H4` / `PRE_H5` |
  | `V6+V7` / `V8+V9` | `V6_V7` / `V8_V9` |
  | `C'` / `D'` / `FX'` | `C_PRIME` / `D_PRIME` / `FX_PRIME` |
  | `SERIES/MIX` | `SERIES_MIX` |

  The single-letter terminal `A` stays `A` (a valid KiCad reference; refdes without a trailing
  number are accepted, power amp / tube_psu precedent); `C'` and `D'` become `C_PRIME` /
  `D_PRIME` by the `'` rule, so no reference is a bare `C` or `D`. Refdes without a trailing
  number (VREF, FB, SUKKA, ...) and `MV0` stay as they are.
  Net names: no `=POWER` nets. Named nets (IPC spelling): `PWR-GND`, `F`, `G`, `H`, `PWRH4`,
  `PWRH5`, `HYPPY2`, `SEND`, `NOLLA`, `SWLOOP`, `A`, `C'`, `D'`; the rest are Proteus auto-names.
  The PDF writes `send` and `nolla` in lower case: label them `SEND` / `NOLLA`.
- **`p2k ipc356`** wrote `reference/` (`ipc356_pads.{json,csv}`, `pin_nets_by_component.md`,
  `pins_by_net.md`); `--check` passes. **`p2k check_sources`** passes: 247 ComponentPad +
  10 OtherPad + 4 ViaPad flashes per copper layer and 261 plated drill flashes match the IPC 1:1,
  one SameCoordinates id, outline. Negative tests (all fail as they should, restored → pass):
  holes 11; RETURN2 expected net #00080; RETURN2 key 1 um off (unkeyed truncated refdes);
  `VIA_DRILLS` 0.6 (vias become free pads); `HOLES_PLATED = False` (check_sources: drill flashes
  without IPC record); an unused `TRUNCATED_REFDES` entry; outline height 71.5.
- **`tools/check_all.sh`**: KiCad environment, IPC self-check, X2 vs IPC (as the pilot), plus
  `PYTHONDONTWRITEBYTECODE=1` and removing `__pycache__` (p2k candidate 3).
- Notes for the later phases:
  - Phase 1: terminal refdes are not net names: the terminals `A`, `C'`, `D'` (page 2, at the
    R28 / R27 / R29 inputs of the 2N3906 drivers) are on #00033, #00032, #00036, **not** on the
    nets `A`, `C'`, `D'` (driver collectors → JFET gates, labels on pages 2 and 4). Do not label
    the terminals. Nets that cross pages: `PWR-GND` (all), `F`/`G` (1, 2), `H` (2, 3),
    `PWRH4`/`PWRH5` (1, 3), `SEND` and `NOLLA` (1, 4), `SWLOOP` (1, 2), `A`/`C'`/`D'` (2, 4) →
    global labels.
  - Phase 1: C1, C36, C37 have the value `22µF 450V` (PDF): expect the pilot's Latin-1 `µ`
    problem in `p2k.pdsprj` (power amp p2k candidate 1).
  - Phase 1: two tube types (U4 12AT7, U5 12AX7, 9-pin, pin 9 N/C) and the heaters on PWRH4 /
    PWRH5 (pins 4 / 5, parallel 6.3 V; +6 on PWRH5, -6 on PWRH4); decide the multi-unit
    handling up front (pilot candidate 8). U5 pins 3 and 8 are one net (#00057, long-tail
    cathodes; one of the 4 vias, at (-79.375, -24.765), is on it).
  - Pad / drill families: small R/C/D 1.778/0.762, 2N3906/J112 1.524/0.762, D1/D3-D6, Q4,
    2 W resistors 2.286/1.016, film / electrolytic C and the relay 2.54/1.143, terminals and
    SW4-SW6 3.048/1.524, noval 4.318/1.727, Q4 2.032 square/1.016.
  - Phase 4: the 2010 Excellon `source/fab_2010/poweri - CADCAM Drill.TXT` (inch, 261 hits,
    same frame: the via at (-79.375, -24.765) is `X-031250Y-009750`) can serve as
    `DRILL_EXCELLON`.

## Last check output

`tools/check_all.sh` (2026-11-20, end of Phase 0):

```
== KiCad environment
pcbnew 10.0.7
== IPC-D-356A parser self-check
ipc356: nets=66, records=261, refdes_raw=125, tht_records=261, smd_records=0, smd_top=0, smd_bottom=0, nc_pads=5, vias=4, free_pads=0, holes=10, parts=126
ipc356: OK
== Gerber X2 export vs IPC (pads, vias, holes, drills, outline)
  8 gerbers, one SameCoordinates id
  Top Copper: Draw:Conductor 277, Draw:Profile 4, Flash:ComponentPad 247, Flash:OtherPad,Unknown 10, Flash:ViaPad 4
  Bottom Copper: Draw:Conductor 238, Draw:Profile 4, Flash:ComponentPad 247, Flash:OtherPad,Unknown 10, Flash:ViaPad 4
  drills: 261 plated, 0 non-plated
  outline 225.4 x 71.8 mm at (-123.83, -78.11)
check_sources: OK

ALL CHECKS PASSED
```

## Findings about the original design

(Report here; don't fix.)

1. **Terminals `A`, `C'`, `D'` are not on the nets `A`, `C'`, `D'`** (see the Phase 1 note):
   the terminals are the driver inputs (R28 / R27 / R29), the nets of the same names are the
   driver outputs to the JFET gates. Proteus terminals do not join nets by refdes. Consistent
   with the design (a control input named after its channel), reproduced as is.
2. **One ground net**: `PWR-GND` joins the power returns (PIRETURN, PRERETURN), the signal
   ground (SIGNALGND, EQGND, PGND), SUKKA and CHASSIS: there is no separate signal ground on
   this board.
3. **Relay SERIES/MIX (G5V-2, DPDT) uses one pole**: pins 6-8 are N/C in the IPC (the PDF
   draws the second changeover unconnected); coil on PWRH4 (heater supply) with flyback diode
   D1, switched by SWLOOP.
4. **Q4 IRF820 is a source-follower regulator**: pin 1 (gate) on #00029 with the zener string
   D4 180 V + D5 + D6 100 V (380 V) and R9 from pin 2; pin 2 on PIPOWER (supply input), pin 3 on
   H, D3 (BZV85C12) gate clamp between pins 1 and 3. Consistent with the TO-220 G D S = 1 2 3
   pinout (drain = PIPOWER, source = H). Phase 1/2 still confirm the Proteus pinout. The board
   receives the PI supply on PIPOWER and feeds the preamp via the RC chain H → R67 → G → R66 → F
   = PREPOWER.
5. Page 1 carries a hand note **"R47 = 50-100k"** while R47's value is 33k: a value range left
   open in 2010 (schematic value 33k is reproduced).
6. `J112` / `J04` in the PDF: `J112` is the device value of the JFETs Q1-Q3, Q5-Q7, `J04` part
   of the capacitor value `MMK J04 5MM`. Not parts; the earlier "net labels" note was inaccurate.
7. Export quirks (as on the power amp board, no effect): Mechanical 1's X2 FileFunction is
   `NonPlated,1,2,NPTH` although it holds only the profile; the solder resist files are negative
   polarity.

## p2k candidates

(Shared-tool limitations met on this board, with the board-local workaround used.)

1. `p2k ipc356` prints "Net aliases: ." in `pin_nets_by_component.md` when `NET_ALIASES` is
   empty and groups the index by the letter prefix (`MV0` under `MV`, `P6` / `N6` under `P` /
   `N`) (cosmetic; same as the pilot's candidate 2).
2. **`TRUNCATED_NETS` is looked up by the KiCad refdes** (`p["refdes"]` after `KICAD_REFDES`),
   and keys that match no refdes are silently ignored. A key with the Proteus spelling (e.g.
   `"P.I.GND"` when the KiCad refdes is `PI_GND`) is never checked. Here every key is a KiCad
   refdes (none of the restored names is renamed). The shared tool would need: accept either
   spelling and fail on keys that match no part. (Worth checking the pilot's `P.I.GND` entry.)
3. **Stale bytecode of `p2k_config.py`.** The config is imported, so Python caches it in
   `__pycache__/p2k_config.*.pyc` validated by mtime (1 s) and size: an edit within the same
   second that keeps the size (e.g. `"holes": 10` → `11` by a script) is ignored. Seen in the
   negative tests. Workaround: `check_all.sh` sets `PYTHONDONTWRITEBYTECODE=1` and removes
   `__pycache__`. The shared tool would need: load the config with `sys.dont_write_bytecode`
   or by exec of the source.
4. Truncated refdes with several nets (the relay `SERIES/MIX`) cannot be given an expected net
   in `TRUNCATED_NETS` (one net per refdes). Not needed here; a `{pin: net}` form would cover it.

## Decisions

- Sheet names (no title blocks in the PDF): FX loop driver / PI supply and FX switching /
  Phase inverter / FX send and return, chosen by the agent from the content; the user can
  rename them (only `p2k_config.py`, before `make_skeleton`).
- KiCad refdes for the names with signs / quote / slash: table above (agent's choice, same
  convention as tube_psu and the power amp pilot: + → P / _, - → N / _, ' → _PRIME, / → _).
  The terminal `A` keeps its name.
