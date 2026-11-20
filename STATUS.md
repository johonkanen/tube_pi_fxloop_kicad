# Status: Phase inverter + FX loop (`poweri`)

Plan: [PLAN.md](PLAN.md). Playbook: `tools/p2k/CONVERSION_PLAYBOOK.md`.

| Phase | State |
|---|---|
| 0 Skeleton and inventory | **done** 2026-11-20 (Opus 5.5) |
| 1 Schematic | **done** 2026-11-20 (preparation Opus 5.5, transcription Fable 5.2) |
| 2 Footprints | **done** 2026-11-20 (Opus 5.5); drills decided by the user 2026-11-20 (KiCad drills kept, `DRILL_SMALLER`) |
| 3 PCB | **done** 2026-11-20 (Opus 5.5); TO-92 pad 1 round decided by the user 2026-11-20 (option (a)) |
| 4 Verification | **done** 2026-11-20 (Fable 5.2, clean context): `ipc356_diff`, `gerber_roundtrip --check` (with the 2010 Excellon) pass; the board is unchanged |
| 5 Clean-up | **done** 2026-11-20 (Opus 5.5, clean context): U4 / U5 on the bottom side (standard noval numbering), `place_refdes` in `make_pcb.sh`; the rest kept as the user decided. **The conversion is complete.** |
| Design fixes | **done** 2026-11-20 (Opus 5.5, user decisions after the conversion): relay SERIES_MIX on Omron pin numbers (Finding 15), the three dangling Proteus stubs removed (`REMOVED_TRACKS`, Finding 19); values unchanged |
| Shared-tool migration | **done** 2026-11-20 (Opus 5.5): p2k a9a286c, every board-local workaround replaced by a shared tool / key; re-baselines D-R, D-K2, R1 only; strict opt-outs none; the board is still generated (stopping is the user's call) |

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

## Phase 1 preparation – done (Opus 5.5, 2026-11-20)

New in this repo (all generated, `--check` in check_all.sh); copied from the power amp pilot
(`~/dev/tube_power_amp_kicad`, read only) and adapted:

- **`tools/make_part_map.py` → `lib/part_map.csv`**: 126 parts, per sheet 1:24 2:46 3:24 4:32
  (= Phase 0). Columns `refdes` (KiCad), `sheet` (PDF page), `lib_id`, `value`, `device`,
  `package`, `proteus_refdes` (the 10 renamed refdes). No off-board parts (every PDF part has pads).
  - value = schematic value from ROOT.DSN (`p2k.pdsprj.dsn_values`, full refdes set).
    **C1, C36, C37**: `22µF 450V` (Latin-1 µ, dsn_values → None): value from the PDF
    (`LATIN1_PARTS`); the script fails if dsn_values starts reading it. The CSV is UTF-8.
  - device / package from ROOT.LYT with a **board-local `lyt_parts()`** (p2k candidate 5:
    `p2k.pdsprj.lyt_parts` drops the one-character refdes `A` and fails with "two layout records
    for -6"). It also decodes Latin-1, so C1/C36/C37 get their device `22µF 450V` / package
    `ELEC D16 R7.5` without a hand-made override.
  - sheet = PDF page from the text layer; `PAGE_OVERRIDES`: `A`, `C'`, `D'` → 2 (the terminals;
    pages 2 and 4 also carry the net labels of the same names).
  - lib_id from the Proteus device (`SYMBOL_BY_DEVICE`): 22N / 47N / 100N XICON, MMK J04 5MM,
    1UF SOLEN FAST → C; HITEMP10U50V → C_Polarized; 22µF 450V → C_Polarized_21; MINRES100K,
    METALFILM1K, RES → R; 1N4148, 1N4001 → D; BZV85C12, 1M180ZS5, 1N4764A → D_Zener; 2N3906; J112;
    IRF820; 12AX7 (U4 and U5); SW-SPDT → SW_SPDT; G5V-2(HI) → G5V-2; TERMINAL → PIN. The script
    fails on a device without symbol and on unused SYMBOL_BY_DEVICE / PAGE_OVERRIDES /
    LATIN1_PARTS entries.
- **`tools/gen_symbols.py` → `lib/tube_pi_fxloop.kicad_sym`** (13 symbols, all from the KiCad 10
  standard library; no power symbols because the IPC has no `=POWER` nets):

  | Symbol | From | Pins (= IPC ids) |
  |---|---|---|
  | R, C | Device | 1, 2 |
  | C_Polarized | Device:C_Polarized | `+` `-` (C8, C28) |
  | C_Polarized_21 | Device:C_Polarized | **2 = `+`, 1 = `-`** (C1, C36, C37: Proteus package `ELEC D16 R7.5`) |
  | D, D_Zener | Device | `A` `K` |
  | 2N3906 | Transistor_BJT:2N3906 (Q_PNP_EBC) | 1=E 2=B 3=C |
  | J112 | Device:Q_NJFET_DSG (KiCad has no THT J112) | 1=D 2=S 3=G |
  | IRF820 | Transistor_FET:IRF740 (BUZ11 body, TO-220 G D S) | 1=G 2=D 3=S |
  | 12AX7 | Valve:ECC83, **3 units**, every pin `passive`, Proteus pin names | unit 1: 6=A2 7=G2 8=K2; unit 2: 1=A1 2=G1 3=K1; unit 3 (heater): 4=H1 5=H2 9=HCT |
  | SW_SPDT | Switch:SW_SPDT, renumbered 1→2, 2→3, 3→1 | 1=NO 2=NC (blade rests on it) 3=COM |
  | G5V-2 | Relay:G5V-2, renumbered (Omron 8/4/6/1/16/13/11/9 → 1..8) | 1=AC1 (NO) 2=COM1 3=NC1 4=DC1 5=DC2 (coil) 6=COM2 7=NC2 8=AC2 (NO) |
  | PIN | Connector:TestPoint | 1 (the 39 terminals) |

- **Proteus pinouts vs KiCad and the IPC nets** (ROOT.DSN read by hand: the device `$PINSHORT` /
  `$PINDEFAULT` records and the `*PINOUT` package tables; `dsn_pinouts` sees only the latter):
  - **2N3906** `$PINSHORT` E=1 B=2 C=3 (no *PINOUT: symbol numbers = pads) = KiCad 2N3906 and the
    TO-92 datasheet (E B C). Nets agree: Q8/Q10/Q20/Q90 emitter (1) on PWR-GND, base (2) via
    R25/R29/R27/R28, collector (3) on #00047 / D' / C' / A.
  - **J112** `$PINSHORT` D=1 S=2 G=3 = the J112 TO-92 datasheet (D S G) = KiCad Q_NJFET_DSG. Nets:
    drain on the send node (#00068 ...), source on PWR-GND, gate on C' / A / D' (shunt switches).
    (The P-channel JFET block in ROOT.DSN is the unused library device 2N5460, not J112.)
  - **IRF820** `*PINOUT TO220` G=1 D=2 S=3 = TO-220 datasheet = KiCad IRF740/BUZ11. Nets: gate on
    the zener string / R9 / C2 (#00029), drain on PIPOWER (#00028), source on H (Finding 4).
  - **12AX7 / 12AT7** `*PINOUT 9-PIN BELTON NOVAL` A1=1 G1=2 K1=3 H1=4 H2=5 A2=6 G2=7 K2=8 HCT=9 =
    the noval standard = KiCad ECC83 numbering. (The device symbol's own `$PINDEFAULT` numbers
    A2=1 A1=6 H1=5 H2=4 ... are overridden by the package table; the PDF shows the package
    numbers.) Nets agree (U5: anodes 1/6 via R2/R1 to H, cathodes 3+8 = #00057, grids 2/7;
    U4: triode 1 = anode 1 via R45 to G, grid 2 from NOLLA via C32, cathode 3 = HYPPY2;
    triode 2 = cathode follower, anode 6 on F, grid 7, cathode 8 via R46 and C30 to SEND).
    Phase 2 still checks the socket pad order against an ideal noval circle (pilot's octal was
    mirrored).
  - **G5V-2(HI)** `*PINOUT` AC1=1 COM1=2 NC1=3 DC1=4 DC2=5 COM2=6 NC2=7 AC2=8. AC = normally open:
    the PDF draws pole 1's blade (COM1, R26) resting on the contact wired to PWR-GND (pin 3 = NC1)
    and the other contact on send (pin 1). Coil 4/5 on SWLOOP / PWRH4 with D1 (K on SWLOOP).
    The Proteus package numbers 1-8 are not the Omron numbers (1, 4, 6, 8, 9, 11, 13, 16):
    Phase 2 must map them by position.
  - **SW-SPDT** `*PINOUT SPDT HOLES` NO=1 NC=2 COM=3. Nets: COM (3) on the R19/R20 node, NC (2)
    on RETURNx, NO (1) on NOLLA. KiCad SW_SPDT has the common on pin 2: renumbered.
  - Diodes / zeners A, K; HITEMP10U50V +, -; **22µF 450V: + = 2, - = 1** (package table), all
    three on the positive rail with pin 2 (H, F, G) as the PDF shows. TERMINAL 1.
  - **No pinout differences that change a net.** Differences to KiCad are numbering only
    (SW_SPDT, G5V-2, C_Polarized_21) and the Proteus pin names on the valve.
- **Valve unit / heater decision (pilot candidate 8), made up front:** keep KiCad's ECC83 split
  into **3 units** (two triodes + heater). Each tube places all three units (`_common.noval()`):
  unit 2 (pins 1-3, drawn on the right of the Proteus symbol) and unit 1 (pins 6-8, left)
  side by side where the PDF draws the tube, unit 3 (heater) directly below them with pins 4 / 5
  to the PWRH4 / PWRH5 wiring as the PDF draws it, and a **no-connect flag on pin 9** (HCT is N/C
  in Proteus). KiCad draws the envelope for each unit (unit 0 graphics), so the heater unit is a
  separate small tube outline. Same choice as the pilot (consistent libraries for the redesign);
  a one-unit Proteus-like symbol was rejected because it departs from the KiCad library. All valve
  pins are `passive` (pilot candidate 9). Pin 9 stays `passive` (not `no_connect` type as the
  pilot's EL34 pin 6): the redesign may use the centre tap; the explicit flag mirrors Proteus' N/C.
- **`p2k make_skeleton`** → `kicad/` (tube_pi_fxloop.kicad_pro, sym-lib-table, root sheet with
  `01 FX loop driver`, `02 PI supply and FX switching`, `03 Phase inverter`,
  `04 FX send and return`, empty sub-sheets). **`tools/erc.sh`** (as the pilot).
  **`tools/sheets/_common.py`**: `part()`, `sh_value()`, `sym()`, `term()` (terminal with the part
  map's symbol / value and readable text justification), `P()` (PDF render position → sheet),
  `place_mirrored()` (pilot) and **`noval(sh, ref, a, b, heater)`** (three units + pin 9 flag).
- **`tools/check_all.sh`**: + part map, symbol library, symbol pins vs IPC, ERC, netlist
  comparison (`--allow-missing` until the 4 sheets are drawn).
- **Smoke test** (scratch copy in build/tmp/smoke, deleted afterwards; the repo's sheets are
  empty): U4 (3 units via `noval()`), R45, relay SERIES_MIX with flags on 6-8, R26, D1, C30,
  terminals PRE_H4 / A / SEND, Q90 mirrored, R28, SW4, local labels, global labels SEND, NOLLA,
  PWRH4, PWRH5, PWR-GND, SWLOOP, F, G, A across sheets 1 / 2 / 4 → compare 12 parts, 36 pins,
  0 wrong-net pins, the N/C pins as `unconnected-(…)`; ERC 0 errors (9 isolated-label warnings,
  expected for a partial drawing). Renders: relay pole 1 rests on pin 3 (NC1) as the PDF,
  Q90 mirrored with the base on the right as the PDF. **Negative tests** (all fail as they should):
  no flag on U4-9 → ERC `pin_not_connected` error; U4-9 wired to PWRH4 → compare "N/C mismatch";
  `send` (lower case) on sheet 1 → compare "IPC net SEND split over KiCad nets [SEND …] [send …]";
  a global label `A` on the terminal A → compare "KiCad net A merges IPC nets [#00033 …] [A …]";
  part map edited / symbol pin renumbered / a SYMBOL_BY_DEVICE entry changed → `--check` /
  check_symbols fail. Restored → all pass.
- `TRUNCATED_NETS` (pilot candidate 11): every key is the KiCad refdes (none of the restored
  refdes is renamed; SERIES_MIX is not listed); Phase 0's negative test (RETURN2 → wrong net)
  showed the entries are checked.

### Transcription rules (for the sheet sessions)

- **Symbols and values**: only `tube_pi_fxloop:` symbols, exactly the `lib_id` and `value` of
  `lib/part_map.csv` per refdes (`_common.sym(ref)`, `sh_value(ref)`; C1/C36/C37 value
  `22µF 450V`, U4 value `12AT7` on the `12AX7` symbol). Refdes = the `refdes` column: `P6` (`+6`),
  `N6` (`-6`), `PRE_H4`, `PRE_H5`, `V6_V7`, `V8_V9`, `C_PRIME` (`C'`), `D_PRIME` (`D'`),
  `FX_PRIME` (`FX'`), `SERIES_MIX` (`SERIES/MIX`); `A` stays `A`. Terminals with `_common.term()`
  (never `sheetkit.terminal`: wrong value "PIN").
- **Net names = IPC names** (`reference/pins_by_net.md`), whatever the PDF writes. The named nets
  (no `=POWER` nets, so no power symbols; PWR-GND is a global label too):

  | Net | Sheets | Label | Pins |
  |---|---|---|---|
  | `PWR-GND` | 1 2 3 4 | global | 34 pins (all grounds, terminals PIRETURN PRERETURN CHASSIS SIGNALGND EQGND PGND SUKKA) |
  | `F` | 1 2 | global | R66-2 U4-6 R48-2 PREPOWER C36-2 |
  | `G` | 1 2 | global | R45-2 R66-1 R67-1 C37-2 |
  | `H` | 2 3 | global | R67-2 R1-2 R2-2 Q4-3 D3-A C1-2 (sheet 3 draws two H labels) |
  | `PWRH4` | 1 3 | global | N6 U5-4 U4-4 PRE_H4 SERIES_MIX-5 D1-A |
  | `PWRH5` | 1 3 | global | P6 U5-5 U4-5 PRE_H5 |
  | `SEND` | 1 4 | global; **the PDF writes `send`: label it `SEND`** | C30-2 SERIES_MIX-1 SEND |
  | `NOLLA` | 1 4 | global; **the PDF writes `nolla`: label it `NOLLA`** | C32-2 R53-1 R20-1 R22-1 R24-1 R26-2 SW4/5/6-1 |
  | `SWLOOP` | 1 2 | global | SERIES_MIX-4 D1-K D2-K D7-K D8-K D9-K |
  | `A` | 2 4 | global | Q3-3 Q5-3 Q90-3 R270-1 D12-K C4-2 |
  | `C'` | 2 4 | global | Q1-3 Q2-3 Q20-3 R110-1 D10-K C7-2 |
  | `D'` | 2 4 | global | Q6-3 Q7-3 Q10-3 R100-1 D11-K C6-2 |
  | `HYPPY2` | 1 | local | R13-1 C8-+ U4-3 (the PDF uses two HYPPY2 labels on sheet 1) |

  All other nets are Proteus auto-names (`#000xx`): plain wires. **No auto-named net crosses a
  sheet**, there are **no single-pin nets**.
- **Terminal refdes are not net names** (Finding 1): the terminals `A`, `C'`, `D'` (sheet 2, at
  R28 / R27 / R29) are on #00033 / #00032 / #00036, **not** on the nets `A`, `C'`, `D'`:
  never put a label on them (a global label `A` there merges two IPC nets: negative test above).
  Likewise `SEND` (terminal, sheet 4) is on the net SEND by its wire to the `send` label, not
  by its name; `PREPOWER` is on F, `PIPOWER` on #00028, `-6` on PWRH4, `+6` on PWRH5 (wires).
- **N/C pins** (5): U4-9 and U5-9 (`noval()` puts the flag), SERIES_MIX 6, 7, 8 (pole 2):
  **no-connect flag** on each (`sh.no_connect(*k.pin("6"))`); without the flag ERC reports
  `pin_not_connected`, a wire on them fails compare ("N/C mismatch").
- **Valves U4 (sheet 1) and U5 (sheet 3)**: `u1, u2, u3 = noval(sh, ref, a, b, heater)`;
  unit 2 = pins 1 A1, 2 G1, 3 K1 (the PDF's right triode), unit 1 = 6 A2, 7 G2, 8 K2 (left),
  unit 3 = heater 4 / 5 (+ flagged 9) below the tube. Missing a unit → compare "missing pin".
  U5 pins 3 and 8 are one net (#00057, to R3).
- **Transistors**: 2N3906 (Q8, Q10, Q20, Q90) and J112 (Q1-Q3, Q5-Q7) as the PDF draws them; where
  the PDF has the base / gate on the right, use `_common.place_mirrored(..., axis="y")` and pass
  `ref_at` / `value_at` (the default texts overlap the mirrored body). Q4 IRF820: gate pin 1
  (bottom in the PDF), drain 2 = PIPOWER side, source 3 = H side.
- **Relay SERIES_MIX** (sheet 1): one symbol (`G5V-2`, both poles and the coil in one unit);
  pin 1 → SEND, 2 → R26, 3 → PWR-GND, 4 → SWLOOP (with D1-K), 5 → PWRH4 (with D1-A), flags on
  6-8. **SW4-SW6** (sheet 4): 1 = NO → NOLLA, 2 = NC → RETURNx, 3 = COM → R19/R21/R23-1 node.
- **Grid 1.27 mm**: symbols, wires and labels on the grid (`g(n)`); `_common.P(x, y)` maps a
  position of `build/tmp/pdf/hi-N.png` (10 px units) to the sheet, which keeps the layout close
  to the PDF (A3 sheets; the 2020 x 1420 px pages fit with the default offset). Use the
  `p2k.sheetkit` helpers (`vert2`, `horiz2`, `glabel_*`, `label_*`, …); repeated blocks (the
  three JFET send channels on sheet 4, the three RETURN switch blocks, the four diode-OR inputs
  on sheet 2) as helpers in `tools/sheets/_common.py`.
- One script per sheet, `tools/sheets/sheetNN.py` (NN = PDF page), rebuilding `kicad/NN_*.kicad_sch`
  from scratch; render with `tools/p2k/bin/p2k render_sheet kicad/NN_*.kicad_sch` and compare
  with `build/tmp/pdf/hi-N.png`.
- After each sheet: `tools/p2k/bin/p2k compare_netlists --allow-missing --sheet N` and
  `tools/erc.sh`, then `tools/check_all.sh`. Target per sheet: 0 missing on that sheet, 0 compare
  errors, 0 ERC errors (warnings explained here; isolated global labels are expected until the
  other sheet of the net is drawn). After the last sheet: drop `--allow-missing` in check_all.sh.
- **Suggested order**: 3 Phase inverter (24 parts: U5, H / PWRH4 / PWRH5 / PWR-GND) →
  1 FX loop driver (24: U4, relay, F / G / SEND / NOLLA / SWLOOP / HYPPY2) → 4 FX send and
  return (32: J112 channels, SW4-SW6, A / C' / D') → 2 PI supply and FX switching (46, the
  largest; closes F, G, H, SWLOOP, A, C', D').

## Phase 1 transcription – done (Fable 5.2, 2026-11-20)

One script per sheet (`tools/sheets/sheet03.py`, `sheet01.py`, `sheet04.py`, `sheet02.py`, drawn in
that order), each rebuilding its `kicad/NN_*.kicad_sch` from scratch; two runs are byte-identical
(`tools/check_sheets.sh`, now a step of check_all.sh). Renders in `reports/render/NN_*.png`, compared
with the PDF pages by eye.

| Sheet | Parts | compare (`--sheet N`, when drawn) | ERC (when drawn) |
|---|---|---|---|
| 3 Phase inverter | 24/24 | 0 missing, 45 pins, 0 wrong-net | 0 errors, 0 warnings |
| 1 FX loop driver | 24/24 | 0 missing, 101 pins (cumulative), 0 wrong-net | 0 errors, 1 warning (global label `G` on one pin until sheet 2) |
| 4 FX send and return | 32/32 | 0 missing, 163 pins (cumulative), 0 wrong-net | 3 `pin_not_driven` errors on the J112 gates (Q1, Q3, Q6) + the `G` warning: **interim only**, the gate nets A / C' / D' had no driver until sheet 2 was drawn |
| 2 PI supply and FX switching | 46/46 | 0 missing, 0 wrong-net | 0 errors, 0 warnings |
| **Total** | **126/126** | 247 pins compared, 0 wrong-net; nets 71 touched / 71 complete (66 IPC nets + the 5 N/C pads) | **0 errors, 0 warnings** |

`tools/check_all.sh` now runs the comparison **without** `--allow-missing` (through
`tools/compare.py`, p2k candidate 9), plus the sheet reproducibility check and a grep that no symbol
pin has the type `no_connect`.

**N/C pins and pin types (coordinator's reminder).** KiCad 10 keeps a pin of type `no_connect` in a
net of its own even when a wire is drawn on it, so compare_netlists could not see a wired N/C pad.
**No symbol in `lib/tube_pi_fxloop.kicad_sym` uses the `no_connect` pin type**: 39 pins are
`passive`, 3 are `input` (2N3906 base, J112 gate, IRF820 gate); check_all.sh greps for it. All five
N/C pads (U4-9, U5-9, SERIES_MIX 6, 7, 8) are `passive` pins with a no-connect **flag**
(1 flag on sheet 3, 4 on sheet 1). Negative test 2 below shows a wire on such a pin is caught.

Negative tests (each on the finished schematic; restored afterwards → all checks pass):

1. Global label `A` on the terminal `A` (sheet 2) → compare exit 1: "KiCad net A merges IPC nets
   [A: C4-2 D12-K Q3-3 Q5-3 Q90-3 R270-1] [#00033: A-1 R28-2]", 2 wrong-net pins.
2. SERIES_MIX pin 6 wired to PWRH4 (flag removed) → compare exit 1: "N/C mismatch: SERIES_MIX-6 is
   N/C in IPC but on KiCad net PWRH4".
3. No flag on SERIES_MIX pin 6 → ERC 1 error `pin_not_connected` (compare alone still passes: the
   pin is unconnected either way).
4. `send` (lower case) global label on sheet 4 → compare exit 1: "IPC net SEND split over KiCad nets
   [SEND: C30-2 SERIES_MIX-1] [send: SEND-1]".

How the sheets were drawn:

- **Coordinates from the PDF** (`_common.P(x, y)`, render position in 10 px units → A3 sheet on the
  1.27 mm grid). Sheets 2 and 4 follow the PDF closely; differences (same nets, noted on the sheets):
  - **Valves (sheets 1, 3):** KiCad's ECC83 is three units. The two triodes stand side by side
    (anode columns 16 grid units apart instead of 8), unit 2 (pins 1-3) **mirrored** so its grid and
    cathode are on the right as in the Proteus symbol (`noval(..., mirror_b=True)`); the heater unit
    is below the tube (U4) or to its right (U5) with the PWRH4 / PWRH5 rows and the heater terminals.
  - **Relay SERIES_MIX (sheet 1):** one symbol with both poles and the coil, rotated 180° so the
    common contact (2) faces R26; contacts 1 (SEND) / 3 (PWR-GND) below, coil 4 / 5 with D1 at the
    right, flags on 6-8. The PDF draws the contacts and the coil as separate graphics.
  - **Q4 (sheet 2):** rotated 90° and mirrored (gate down, source left on H, drain right on PIPOWER)
    as in the PDF: `_common.place_rot90_mirrored()`; the pin positions are asserted in the script.
  - Sheet 2: the rows of the nets A / D' / C' are 6 grid units apart (PDF: D' and C' 2 apart);
    sheet 4: ground row and the channel-2 gate row a little lower, RETURN blocks 16 units to the right.
  - The PDF's stray junction dot on the ground row of page 2 (at x = 950 px, nothing attached) is
    not drawn.
- New helpers in `tools/sheets/_common.py`: `pv()` / `ph()` (vertical / horizontal two-pin part with
  symbol and value from the part map; capacitor texts clear of the plates), `junctions()`,
  `q_right()` (2N3906 / J112 mirrored, base / gate on the right), `send_channel()`,
  `return_block()` (sheet 4), `diode_input()` (sheet 2), `place_rot90_mirrored()`,
  `noval(mirror_b=)`.
- Labels: global `PWR-GND`, `F`, `G`, `H`, `PWRH4`, `PWRH5`, `SEND`, `NOLLA`, `SWLOOP`, `A`, `C'`,
  `D'`; local `HYPPY2` (twice on sheet 1). No label on the terminals A, C', D' (sheet 2).
- ERC warnings at the end: none.

## Phase 2 – done (Opus 5.5, 2026-11-20)

New in this repo (all generated, in check_all.sh); the pilot's Phase 2 pieces
(`~/dev/tube_power_amp_kicad`, read only) reused and adapted:

- **`p2k_config.py`**: `FOOTPRINT_PAD_SIZES = "kicad"` (the default, explicit), `OFF_BOARD_PARTS = {}`
  (every part has pads), `HOLE_FOOTPRINT = tube_pi_fxloop:MountingHole_3.0mm_PTH_Pad6.35mm` /
  `HOLE_VALUE` (for Phase 3 `build_pcb`).
- **`tools/gen_footprints.py`** (RULES + PROJECT, `p2k.footprints.run`) → `lib/footprint_map.csv`
  (126 rows), `lib/tube_pi_fxloop.pretty/` (15 files: 14 footprints used by symbols + the mounting hole)
  and **`kicad/fp-lib-table`** (written and `--check`ed by the board script, pilot candidate 12). One rule
  per Proteus package, matched on `package` + span + pad size + drill. The shared 2010 packages keep the
  pilot's footprint names and specs (DIN0414 P19.05, C_Rect L13 W6 P9.70, DO-41 `_AK`, TO-92 P2.03,
  fly-lead pad, mounting hole).
- Sheet scripts re-run: the 130 placed symbol units (126 parts + the 4 extra valve units of U4 / U5)
  carry their footprint; the diff of `kicad/0?_*.kicad_sch` is the Footprint lines only. ERC 0 / 0 with
  the project fp-lib-table, compare unchanged (126/126, 0 wrong-net pins, 71/71 nets).
- **`tools/erc.sh`** now also fails on `footprint_link_issues` warnings (a Footprint field naming a
  library / footprint the project cannot resolve): without `kicad/fp-lib-table` ERC gives 90 such
  warnings (0 errors), which the old script let pass.
- **`tools/check_pin_order.py`** (pilot's board script, p2k candidate 13 there): fits the **unmoved**
  KiCad base footprints with the Proteus renumbering onto the IPC pads, both unmirrored and mirrored;
  noval: KiCad `Valve:Valve_Noval_P`, an ideal standard noval on the Proteus 21.0 mm circle with a free
  rotation (the fit of `fpgeom` snaps to 45°, the noval steps are 36°) and the sense of pins 1 → 9;
  relay with both mappings; SW-SPDT hole pattern. The renumberings checked must equal those of the
  derived footprints in `gen_footprints.PROJECT` (the relay's is imported from it). `--render` (system
  python3, matplotlib) writes `reports/pin_order/<ref>.png`.
- **`tools/check_all.sh`**: + footprint library / map / fp-lib-table up to date
  (`gen_footprints.py --check`), footprints vs IPC pads (`kipy -m p2k.check_footprints --pcbnew`),
  pin order (`kipy tools/check_pin_order.py`).

### Footprints and fit

| Parts | Proteus package (2010) | Footprint | How | Pads IPC → footprint (mm, pad / drill) | Fit |
|---|---|---|---|---|---|
| 34 R (R3-R8, R10-R26, R47, R49, R50, R53, R54, R27-R29, R100, R110, R270) | RES40 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | KiCad, unchanged | 1.778/0.762 → 1.6/0.8 | 0.000 |
| R1 R2 R9 R45 R46 R48 R66 R67 | 2W METAL FILM RESISTOR | `R_Axial_DIN0414_L11.9mm_D4.5mm_P19.05mm_Horizontal` | pilot spec: derived from `..._P20.32mm` | 2.286/1.016 → **2.4**/1.2 | 0.000 |
| C2 | 22N XICON | `C_Rect_L13.0mm_W6.0mm_P9.70mm` | pilot spec: derived from `C_Rect_L13.0mm_W6.0mm_P10.00mm_FKS3_FKP3_MKS4` | 2.54/1.143 → 2.0/**1.0** | 0.000 |
| C31 | 47N XICON | `Capacitor_THT:C_Rect_L18.0mm_W6.0mm_P15.00mm_FKS3_FKP3` | KiCad, unchanged (Proteus silk 18.0 x 6.0 mm) | 2.54/1.143 → 2.4/1.2 | 0.000 |
| C3 C5 C9 C29 | 100N XICON | `C_Rect_L23.1mm_W6.0mm_P20.00mm` | **built from the IPC pads** (C5), body 23.1 x 6.0 mm = Proteus silk; KiCad has no P20.00 box, the nearest (L24 W7 / L26.5 W6, P22.5) are wider or longer than the Proteus rows 6.35 mm apart | 2.54/1.143 (Proteus) | 0.000 |
| C4 C6 C7 C32 | MMK J04 | `Capacitor_THT:C_Rect_L7.2mm_W5.0mm_P5.00mm` | KiCad, unchanged (Proteus silk 7.2 x 5.2 mm) | 1.778/0.762 → 1.5/**0.75** | 0.000 |
| C30 | SOLEN 1U | `C_Axial_L26.7mm_D15.2mm_P30.48mm_Horizontal` | **built from the IPC pads**, body 26.67 x 15.24 mm = Proteus silk box (KiCad axial capacitors stop at D10.5 / P27.5) | 2.54/1.143 (Proteus) | 0.000 |
| C8 C28 | ELEC-RAD10 | `CP_Radial_D5.0mm_P2.54mm_PM` | derived from `CP_Radial_D5.0mm_P2.50mm`, pads 1 → `+`, 2 → `-`, moved to P2.54 (Proteus circle D5) | 2.032/0.762 → 1.6/0.8 | 0.000 |
| C1 C36 C37 | ELEC D16 R7.5 | `CP_Radial_D16.0mm_P7.50mm_21` | derived from `CP_Radial_D16.0mm_P7.50mm`, pads **1 → `2`, 2 → `1`** (KiCad pad 1 = `+` = Proteus pin 2, Finding 9) | 2.54/1.143 → 2.4/1.2 | 0.000 |
| D2 D7-D12 | DO35 | `D_DO-35_SOD27_P10.16mm_Horizontal_AK` | derived, pads 1 → `K` (band), 2 → `A` | 1.778/0.762 → 1.6/0.8 | 0.000 |
| D1 D3-D6 | DO41 | `D_DO-41_SOD81_P10.16mm_Horizontal_AK` | pilot spec, pads 1 → `K`, 2 → `A` | 2.286/1.016 → 2.2/1.1 | 0.000 |
| Q8 Q10 Q20 Q90 (2N3906, E B C), Q1-Q3 Q5-Q7 (J112, D S G) | TO92 | `TO-92_Inline_P2.03mm` | pilot spec: derived from `TO-92_Inline_Wide` at P2.032; pad numbers = Proteus ids 1-3 | 1.524/0.762 → 1.5/0.8 | 0.000 |
| Q4 | TO220 | `Package_TO_SOT_THT:TO-220-3_Vertical` | KiCad, unchanged (1=G 2=D 3=S; KiCad pad 1 rectangular) | 2.032/1.016 → 1.905x2.0/1.1 | 0.000 |
| U4 U5 | 9-PIN BELTON NOVAL | `Valve_Noval_Belton_PCD21.00mm` | **built from the IPC pads** (U4): Proteus pitch circle **21.0 mm** (10 positions 36° apart), KiCad `Valve_Noval_P` is a smaller circle (mirrored fit 2.97 mm off); no centre hole; body = the Proteus Top Assembly square 26.4 x 25.4 mm | 4.318/1.727 (Proteus) | 0.001 |
| SERIES_MIX | G5V-2(HI) | `Relay_DPDT_Omron_G5V-2_Proteus` | derived from `Relay_THT:Relay_DPDT_Omron_G5V-2`, renumbered by **physical position** (Omron 9 → 1, 13 → 2, 11 → 3, 16 → 4, 1 → 5, 4 → 6, 6 → 7, 8 → 8; Finding 15) | 2.54/1.143 → 1.4/**0.7** | 0.000 |
| SW4 SW5 SW6 | SPDT HOLES | `SW_SPDT_3Holes_Proteus` | **built from the IPC pads** (SW4), body = Proteus assembly rectangle 8.1 x 7.5 mm | 3.048/1.524 (Proteus) | 0.000 |
| 39 terminals | C-120-60 | `FlyLead_Pad_D3.048mm_Drill1.524mm` | pilot spec, built from the IPC pad (EQOUT) | 3.048/1.524 (Proteus) | 0.000 |
| H1-H10 (Phase 3) | mounting holes | `MountingHole_3.0mm_PTH_Pad6.35mm` | board-only, plated, pad number 1, no net | 6.35/3.0 (Proteus) | – |

`check_footprints`: 126/126 parts, 247 pads, worst residual 0.001 mm; `--pcbnew` placement worst 0.001
mm; every part on the top side (60 at 0°, 37 at 270°, 21 at 90°, 8 at 180°); `reports/footprint_fit.csv`
(placement for Phase 3) and `reports/footprint_pads.csv` written.

### Pad size / drill differences vs Proteus (drills decided by the user 2026-11-20: KiCad drills kept, `DRILL_SMALLER`)

With `FOOTPRINT_PAD_SIZES = "kicad"` the KiCad library pads and drills replace the Proteus ones on the
footprints taken or derived from KiCad (the IPC-built ones keep the Proteus pads). **Not decided here**;
Phase 3 DRC shows whether a pad size matters, Phase 4 (`ipc356_diff`, `gerber_roundtrip`) fails on every
KiCad drill smaller than Proteus unless `DRILL_SMALLER` records it or the footprint gets the Proteus
drill (`ipc_sizes`, or a `refdes` rule). The power amp kept its smaller KiCad drills (C1-C6,
`DRILL_SMALLER`); that is no precedent here.

| Refdes | Footprint | Pad Proteus → KiCad | Drill Proteus → KiCad | Note |
|---|---|---|---|---|
| **SERIES_MIX** | Relay_DPDT_Omron_G5V-2_Proteus | 2.54 → **1.4** | 1.143 → **0.70** (-0.443) | largest difference: KiCad's G5V-2 land pattern (all 8 pads) |
| **C2** | C_Rect_L13.0mm_W6.0mm_P9.70mm | 2.54 → 2.0 | 1.143 → **1.00** (-0.143) | same as the pilot's C1-C4 |
| **C4 C6 C7 C32** | C_Rect_L7.2mm_W5.0mm_P5.00mm | 1.778 → 1.5 | 0.762 → **0.75** (-0.012) | small; Phase 4 tools match drills within 0.005 mm, so it counts |
| R1 R2 R9 R45 R46 R48 R66 R67 | R_Axial_DIN0414 P19.05 | 2.286 → **2.4** (+0.057 per side) | 1.016 → 1.2 | the only **larger** pads (clearance), as on the pilot (no DRC problem there) |
| Q4 | TO-220-3_Vertical | 2.032 → 1.905 x 2.0 (pad 1 rect.) | 1.016 → 1.1 | |
| all other KiCad / derived | – | smaller | larger or equal | R 1.6/0.8, D 1.6/0.8 and 2.2/1.1, TO-92 1.5/0.8, C8/C28 1.6/0.8, C1/C36/C37 and C31 2.4/1.2 |
| C3 C5 C9 C29, C30, U4 U5, SW4-SW6, terminals | IPC-built | Proteus | Proteus | no difference |

Drills smaller than Proteus: **6 parts, 18 holes** (SERIES_MIX 8, C2 2, C4 / C6 / C7 / C32 8; per pad in
`reports/footprint_pads.csv`, `fp_drill` < `ipc_drill`).
Options per footprint: (a) keep the KiCad drill → `DRILL_SMALLER = {(1.143, 0.7): ..., (1.143, 1.0): ...,
(0.762, 0.75): ...}` in Phase 4; (b) Proteus drill (`ipc_sizes=True` on the spec, which also takes the
Proteus pad size). For the relay a 1.143 mm hole in KiCad's 1.4 mm pad would leave a 0.13 mm ring, so
(b) means the Proteus 2.54 mm pads as well.

### Pin order (`tools/check_pin_order.py`, renders in `reports/pin_order/`)

| Parts | Unmoved KiCad base (renumbering) | Unmirrored | Mirrored | Result (body marker from the render) |
|---|---|---|---|---|
| Q4 | TO-220-3_Vertical | 0.000 @ 90° | 0.000 @ 270° | KiCad tab line on −x = Proteus hatched tab on −x: **1=G 2=D 3=S as KiCad** |
| Q8 Q10 Q20 Q90 | TO-92_Inline_Wide | 0.508 @ 90° (P2.54 vs 2.032) | 0.508 | KiCad flat side = Proteus flat side on all four: **1=E 2=B 3=C (EBC) as KiCad** |
| Q1-Q3 Q5-Q7 | TO-92_Inline_Wide | 0.508 @ 270° | 0.508 | flat sides agree on all six: **1=D 2=S 3=G** (J112 datasheet D S G) |
| D2 D7-D12 | D_DO-35 (1 → K) | 0.000 | 0.000 | KiCad band at K = Proteus band at K on all seven |
| D1 D3-D6 | D_DO-41 (1 → K) | 0.000 | 0.000 | same, all five |
| C8 C28 | CP_Radial_D5.0mm_P2.50mm (1 → +) | 0.020 | 0.020 | KiCad `+` / square pad at Proteus `+`, Proteus `+` mark beside it |
| **C1 C36 C37** | CP_Radial_D16.0mm_P7.50mm (1 → `2`, 2 → `1`) | 0.000 | 0.000 | KiCad `+` and square pad on **pad 2** = Proteus `+` mark beside pad 2: **+ = pad 2 confirmed** |
| **SERIES_MIX** (symbol mapping, Omron pole 1: 8/4/6/1/16/13/11/9 → 1..8) | Relay_DPDT_Omron_G5V-2 | **7.620** | **0.000** | only the **mirrored** Omron footprint matches (Finding 15) |
| SERIES_MIX (physical mapping 9/13/11/16/1/4/6/8 → 1..8, the footprint) | Relay_DPDT_Omron_G5V-2 | **0.000** | 7.620 | KiCad pin-1 mark at Proteus pad 5 |
| **U4 U5** | Valve:Valve_Noval_P | 17.630 | **2.972** | only the mirrored KiCad noval is near (smaller circle); ideal standard noval on the 21.0 mm circle (free rotation): unmirrored **19.318**, mirrored **0.007** |
| SW4-SW6 | – (IPC-built) | – | – | 1 (NO) and 2 (NC) 5.08 mm apart, 3 (COM) the offset hole 5.12 mm from both; nets checked by compare (COM on the R19/R21/R23 node, NC on RETURNx, NO on NOLLA) |

Two-pad and inline parts fit either way (a 180° turn reverses the order); the body markers decide and
agree with KiCad on every part (renders looked at for all 31 rendered parts). **The noval sockets are
mirrored like the pilot's octal**: pins 1 → 9 run **clockwise seen from the top** (1 at −144°, 2 at 180°,
… 9 at −72°, gap at −108°); the noval standard (KiCad) runs clockwise seen from the pin / solder side of
a top-mounted socket, i.e. counter-clockwise from the top (Finding 16). The footprint keeps the Proteus
ids and the top side (reproduces Proteus; the copper is identical either way).

Negative tests (each restored afterwards; check_all.sh passes):

1. Noval pad 4 moved 0.1 mm in the library file → `gen_footprints --check` exit 1 ("out of date"),
   check_footprints FAILED (U4 / U5 residual 0.089 mm).
2. TO-92 pads 2 / 3 swapped in the library file → `--check` exit 1, check_footprints FAILED (all ten TO-92
   parts, 2.032 mm).
3. A map entry changed (R13 → the DIN0414 footprint) → `--check` exit 1 ("out of date:
   lib/footprint_map.csv"), check_footprints "R13: schematic footprint … != lib/footprint_map.csv … (re-run
   the sheet scripts)". A stale sheet (R3's Footprint field edited) → check_footprints FAILED (map
   mismatch + residual 4.445) and check_sheets.sh fails.
4. `kicad/fp-lib-table` removed → `--check` exit 1; ERC 90 `footprint_link_issues` warnings, now exit 1
   (erc.sh change above). A misspelled KiCad footprint name in a sheet → ERC 1 `footprint_link_issues`, exit 1.
5. Pin-order expectation of the relay's physical mapping set to mirrored → check_pin_order FAILED.
6. `G5V2_RENUMBER` with pads 2 / 3 swapped in gen_footprints → **check_footprints still OK** (the shared
   `derive()` moves the pads onto the IPC positions by number whatever the base fit was: p2k candidate 14),
   check_pin_order FAILED (5.080 mm).
7. C1/C36/C37 renumbering 1 → `1`, 2 → `2` in gen_footprints → check_footprints OK (same reason),
   check_pin_order FAILED ("renumbering … differs from gen_footprints").
8. Noval sense expected counter-clockwise → check_pin_order FAILED for U4 and U5.

## Phase 3 – PCB – done (Opus 5.5, 2026-11-20)

`kicad/tube_pi_fxloop.kicad_pcb` is generated: `tools/make_pcb.sh` runs the shared tools (about 3 s)
and two runs give a byte-identical board; `tools/make_pcb.sh --check` (in `check_all.sh`) rebuilds it
in `build/tmp/make_pcb_check` (with a copy of the `.kicad_pro`) and compares the board,
`reports/pour_nets.json` (empty: no pours) and the stage A/B part of `reports/assign_nets.txt`. Do not
hand-edit the board while it is generated. `build_pcb` writes the design rules into
`kicad/tube_pi_fxloop.kicad_pro` (committed with the board).

**Everything passes: `check_all.sh` "ALL CHECKS PASSED", DRC 0 unaccepted errors.** The first board had
9 `clearance` errors at the square KiCad pad 1 of the TO-92 footprint; the user chose option (a), a round
pad 1 at the KiCad size 1.5 mm (section "TO-92 pad 1" below; Decisions), applied in the Phase 3 finish
session. `tools/drc_pending.py` (the interim wrapper) is removed; `check_all.sh` runs `p2k drc` directly.

### Steps (tools/make_pcb.sh; the pilot's without its Phase 5 place_refdes step)

| Step | Tool | Result |
|---|---|---|
| 3a | `p2k.build_pcb` | 126 footprints with nets and symbol links at `reports/footprint_fit.csv` (none excluded); 2 Cu layers (Top / Bottom Copper → F.Cu / B.Cu; User.1/2 reserved for pours, none); outline 225.425 × 71.755 mm (4 Mechanical 1 segments); **H1-H10** = `tube_pi_fxloop:MountingHole_3.0mm_PTH_Pad6.35mm` at the IPC hole records (plated, no net); thickness 1.6 mm; rules below. Board nets: 66 IPC nets + the 5 `unconnected-(…)` N/C pins (U4-9, U5-9, SERIES_MIX 6-8) = 71. |
| 3b | `p2k.gerber_to_tracks` | 515 tracks (F.Cu 277 / B.Cu 238), **4 vias** (1.27 / 0.508 mm, from the ViaPad flashes + drills; IPC 4), 0 pours, 8 profile draws skipped; every pad flash (247 per layer) lands on a footprint pad, every OtherPad flash on a mounting-hole pad, every drill on a pad / via hole. |
| 3c | `p2k.assign_nets` | stage A = stage B (no pours): **81 groups (66 nets + 10 holes + 5 N/C pads), 0 shorts, 0 orphans, 0 opens**; 519/519 tracks and vias got their net. |
| check | `p2k.check_board` | 247 pads within 0.001 mm and on the IPC nets (66 IPC nets 1:1), 10 mounting holes (size, plating, no net), 4 vias (position, size, net), 515 tracks, 0 zones, every copper item has a net. |
| check | `p2k.assign_nets --check` | KiCad geometry: 81 groups, 0 shorts, 0 orphans, 0 opens, 0 items with a foreign net. |
| check | `p2k drc` | **0 shorts, 0 unconnected, 0 parity, 0 unaccepted errors** (252 items, accepted types below); smallest TO-92 pad-track gap 0.432 mm. |

### Design rules (p2k_config.py `PCB_RULES`, `PCB_THICKNESS`)

Measured on the Proteus copper (`tools/measure_gaps.py`, the pilot's / tube_psu's copy, read-only,
assign_nets stage B geometry = Proteus pad flashes + tracks + vias): smallest different-net gap
**0.421 mm** (pad–track: Q3-1 / the PWR-GND track beside it; TO-92 rows), pad–pad 0.508 (C8 + / −,
P2.54 with 2.032 pads), track–track 0.508, pad–via 0.766, track–via 0.907; copper to outline ≥ 1.143 mm;
drill to drill ≥ 1.270 mm (TO-92, 1.232 with the KiCad 0.8 drills); conductors 0.508 – 1.778 mm (thinnest
0.508 = 20 mil); vias 1.27 / 0.508 mm.
Rules: clearance **0.4** (also the netclass clearance), min track 0.5, min via 1.2, min annular 0.1, min
drill 0.5 (the vias), hole clearance 0.25, hole-to-hole 1.0, copper-to-edge 1.0; Default netclass track
0.508, via 1.27 / 0.508 (= the Proteus vias).
Thickness **1.6 mm**: the 2010 fab READ-ME has no stack-up; the 2026 export's READ-ME lists Proteus 8's
default 2-layer stack (1.555 mm + resist), added when the design was re-saved – not the 2010 order (as
the pilot; agent's choice, change `PCB_THICKNESS` if the board measures otherwise).

### KiCad pad sizes: one conflict, the TO-92 pad 1 (decided: option (a), round pad 1)

The first DRC with the Phase 2 footprints (KiCad pad sizes) has 0 shorts, 0 hole-clearance and 0
solder-mask-bridge errors, but **9 clearance errors, all at pad 1 of the TO-92 parts Q1, Q3, Q6, Q20**.
The KiCad TO-92 footprint (`TO-92_Inline_P2.03mm`, derived from `TO-92_Inline_Wide`) has a **square**
1.5 × 1.5 mm pad 1; the Proteus TO92 pads are all **round** 1.524 mm. The square's corner reaches
0.31 mm farther than the Proteus circle towards a diagonal track:

| Pad | Track | KiCad gap | Proteus gap |
|---|---|---|---|
| Q3-1 (Net-(Q3-D)) | F.Cu PWR-GND, 45° from Q3-2 | **0.122** (and 0.393 to two more) | 0.421 |
| Q6-1 (Net-(Q6-D)) | F.Cu PWR-GND, 45° from Q6-2 | **0.122** (and 0.393 to two B.Cu tracks) | 0.421 |
| Q1-1 (Net-(Q1-D)) | B.Cu PWR-GND, 45° from Q1-2 | **0.123** | 0.421 |
| Q20-1 (PWR-GND) | B.Cu Net-(Q20-B), 45° from Q20-2 | **0.122** (and 0.392) | 0.421 |

The pad size is not the problem (1.5 < 1.524), the shape is. The pilot uses the same footprint (Q2 /
Q3) without a conflict: no diagonal track passes its pad-1 corners. Options (tried on scratch copies in
`build/tmp/padexp`, DRC rerun):

- **(a) Round pad 1** (KiCad size 1.5 mm, circle like pads 2 / 3; pin 1 then marked by the silk only):
  all 9 errors gone, smallest TO-92 gap **0.433 mm** (better than Proteus 0.421). Needs a board-local
  pad-shape override after `derive()` in `tools/gen_footprints.py` (the shared tool keeps the base pad
  shapes; p2k candidate 16).
- **(b) Proteus pads** (1.524 mm round, drill 0.762): all 9 errors gone, gaps = Proteus (0.421). Note
  `ipc_sizes=True` alone keeps the square shape (it only sets size and drill), so this also needs the
  shape override, or the TO-92 footprint built from the IPC pads (`from_ipc` with a body, losing the
  KiCad graphics / 3D model).
- **(c) Keep the square pad** and accept 0.12 mm: `p2k drc` accepts by violation type only, so
  `DRC_ACCEPTED["clearance"]` would hide every future clearance error – not recommended.

Agent's recommendation: (a). **User decision 2026-11-20: (a).** Applied (Phase 3 finish):

- `tools/gen_footprints.py` wraps `footprints.derive()` (board-local, p2k candidate 16): for
  `TO-92_Inline_P2.03mm` it checks that the base has exactly one `rect` pad 1 (fails otherwise, so a
  changed KiCad base is noticed) and makes it a `circle`; size 1.5 mm and drill 0.8 stay (KiCad). All ten
  TO-92 parts (Q1-Q3, Q5-Q7, Q8, Q10, Q20, Q90) use the footprint.
- **Pin 1 marking.** KiCad's TO-92 outline (silk and fab: flat side plus arc) is symmetric about pad 2,
  and the square pad was the only pin-1 mark. With three round pads that mark is gone, so the wrapper adds
  a **filled dot (radius 0.2 mm, about 0.5 mm across with the line) on F.SilkS and on F.Fab** at (-0.45, 1.35) in the footprint frame: left of pad 1
  on the flat side, outside the body outline, 0.6 mm from the pad copper, inside the courtyard. It moves
  with the footprint (the TO-92 rows have both orientations). The dot overlaps 4 neighbour reference texts
  (R16 / Q3, R27 / Q90, R18 / Q6, R11 / Q1: silk_overlap 134 → 138 warnings; reference positions are
  Phase 5); it touches no copper (silk_over_copper unchanged 55).
- Footprint fit and pin order rechecked: `check_footprints` 126/126, worst residual 0.001 mm (pad centres
  unchanged); `check_pin_order` unchanged (it fits the unmoved KiCad base footprints).
- `tools/make_pcb.sh`: board rebuilt, byte-identical on a second run; DRC **0 clearance errors**; smallest
  different-net gap at a TO-92 pad **0.432 mm** (pcbnew geometry, pad circle to track edge; Q1-2, Q3-1,
  Q5-3, Q6-1, Q6-3, Q7-3), above the 0.4 rule and the Proteus 0.421.

(Original note:) a pad change forced by DRC is the user's. The
other KiCad pads: the 2 W resistors (2.4 vs Proteus 2.286 mm) are nowhere near the clearance – smallest
gap **1.171 mm** (R48-2 / F.Cu PWR-GND track; Proteus 1.228); no other pair below 0.433 mm apart from
the TO-92 pad 1 (DRC at 0.6 mm clearance on a scratch copy: 73 pairs < 0.6, all Proteus-tight spots).
Drills are decided (KiCad drills kept, `DRILL_SMALLER`); DRC does not involve them.

### Remaining DRC items (`DRC_ACCEPTED`)

| Type | Count | Why it stays |
|---|---|---|
| shorting_items / unconnected / schematic parity | 0 / 0 / 0 | – |
| clearance (error) | 0 | (9 before the TO-92 pad 1 became round, above) |
| courtyards_overlap (error) | 47 | Proteus placement vs KiCad courtyards, parts exactly at the Proteus positions: U4 / U5 noval courtyards (21 mm circle) with H3 H4 H7 H8, C8, R54, V8_V9; the 100N rows C3 / C5 / C9 (6.35 mm apart); the TO-92 rows Q1/Q2, Q3/Q5, Q6/Q7 and their neighbours R11, R16, R18, R270, SEND2W, SEND3W; tight resistor / film-cap / terminal rows (R19-R24, R66, RETURN1-3, A / D_PRIME with R28, FX_PRIME/R25, VREF/R100, C4 / C7 with D9 and R50, C30 with R24 / R26, C37 with R67 / SW4, C2/R9, C28/R48, C29/C6, C32/R53, R1/V8_V9). Accepted. |
| pth_inside_courtyard (error) | 7 | H3 / H4 in the U5 / U4 courtyard (Finding 17), C8 + / − in U4's, V8_V9-1 in U5's, R24-1 and R26-1 in the C30 Solen box. Accepted. |
| track_dangling (warning) | 3 | Proteus copper stubs (Finding 19). |
| silk_overlap / silk_over_copper (warning) | 138 / 55 | KiCad footprint silk and default reference positions on the Proteus placement (Phase 5); 4 of the overlaps are the TO-92 pin-1 dots under neighbour references. |
| silk_edge_clearance (warning) | 2 | reference texts of H1 / H2 at the board edge (Phase 5). |

Several courtyard items (U4 / U5 with top-side parts) go away when the sockets move to the bottom side
in Phase 5 (user decision 2026-11-20); then the counts in `DRC_ACCEPTED`'s reason need updating.

### Negative tests (all restored with tools/make_pcb.sh; board byte-identical afterwards)

| Change | make_pcb --check | check_board | assign_nets --check | drc |
|---|---|---|---|---|
| a SWLOOP track (F.Cu, at SERIES_MIX-4) moved 3 mm | not up to date | OK (tracks not position-checked) | **1 open** (SWLOOP: D2/D7-D9 vs D1/SERIES_MIX-4) | **1 unconnected** |
| the SWLOOP via at (30.48, 50.8) deleted | not up to date | **"IPC via (30.48, -50.8) SWLOOP: no board via"** | **1 open** (same groups) | **1 unconnected** |
| pad R13-1 net edited in the file (HYPPY2 → PWR-GND) | not up to date | **IPC net HYPPY2 spans two KiCad nets** (+ 3 pad net errors) | **IPC net HYPPY2 spans two KiCad nets** | **1 short, 1 unconnected, 1 parity** |
| footprint R13 moved 0.2 mm | not up to date | **R13-1/-2 0.200 mm from the IPC pad** | OK | OK (gaps still ≥ 0.4) |
| a segment's net edited in the file (SWLOOP → PWR-GND) | not up to date | OK | OK | OK – pcbnew / kicad-cli re-derive track nets from the pads on load (the pilot's pitfall); only the byte compare catches it |
| `DRC_ACCEPTED` without `pth_inside_courtyard` | – | – | – | `drc_pending.py` **FAILED** (7 unaccepted errors besides the 9 pending; run before the pad decision) |
| Phase 3 finish: the round pad 1 left out in `gen_footprints.py` (the old square pad), library not regenerated | – | – | – | `gen_footprints --check` **out of date** (TO-92 footprint) → SOME CHECKS FAILED |
| same, library regenerated and board rebuilt (`make_pcb.sh`) | up to date | OK | OK | `p2k drc` **FAILED: 9 clearance** (the same 9: Q1, Q3, Q6, Q20 pad 1, 0.122 mm) → SOME CHECKS FAILED |

After the Phase 3 finish tests `gen_footprints.py` was restored and the board rebuilt: byte-identical to
the board before the tests, ALL CHECKS PASSED. Every board change is caught by at least the byte compare; geometry and net errors by the independent
checks as well.

## Phase 4 – independent verification – done (Fable 5.2, clean context, 2026-11-20)

Start: `tools/check_all.sh` = the Phase 3 "Last check output" byte for byte (ALL CHECKS PASSED). New in
this repo: `tools/excellon_metric.py` → `reference/fab_2010_drill_metric.drl`, `DRILL_EXCELLON` in
`p2k_config.py`, `tools/check_drill_smaller.py`, `reports/roundtrip/` (report + overlay PNGs), four new
steps in `tools/check_all.sh`; `tools/erc.sh` fails on `no_connect_connected` (and takes an optional
schematic / report argument for scratch copies); `tools/compare.py` fails on an `unconnected-(…)` net
with more than one pin. **The conversion itself is unchanged**: `kicad/`, `lib/` and the Phase 0-3
reports are byte-identical to the Phase 3 commit (`git status`: no change under `kicad/` or `lib/`).
No user decision is needed.

### Results

| Check | Result |
|---|---|
| `p2k ipc356_diff` (kicad-cli IPC-D-356 export of the board vs the Proteus IPC) | Proteus 261 records, KiCad 261, **261 matched** (247 pads incl. the 5 N/C pads, 4 vias, 10 plated holes), worst position offset 0.002 mm (limit 0.05); **66 Proteus nets mapped 1:1**, 0 mismatches; side / THT / plating equal. Drills: KiCad larger (reported) 116× 0.762→0.8, 13× 1.016→1.1, 16× 1.016→1.2, 8× 1.143→1.2; **KiCad smaller, accepted by `DRILL_SMALLER`: 8× 0.762→0.75, 8× 1.143→0.7, 2× 1.143→1.0 = 18 holes**; the rest equal. OK |
| `p2k gerber_roundtrip --check` (KiCad gerbers + drills vs the Proteus gerbers) | F.Cu: XOR 94.27 mm², beyond 0.05 mm only-Proteus 53.53 / only-KiCad 6.39 mm², **218 clusters, all "pad shape", 0 other**; B.Cu: 97.05 mm², 54.15 / 7.29, **213 pad shape, 0 other**; coverage both ways **0 draws / flashes off the other copper** (F.Cu: Proteus 281 draws incl. the 4 outline draws / 261 flashes, KiCad 277 / 261; B.Cu: 242 / 261 and 238 / 261); plated drills **261 / 261 matched** within 0.05 mm, 0 mismatches, the same 18 accepted smaller holes; **Excellon cross-check 261 / 261 holes, 0 mismatches**. OK |
| 2010 Excellon (`DRILL_EXCELLON`) | `source/fab_2010/poweri - CADCAM Drill.TXT` (inch, 7 tools) → `reference/fab_2010_drill_metric.drl` by `tools/excellon_metric.py` (the pilot's script, only the file name differs; `--check` in check_all.sh). 4× 0.508, 124× 0.762, 29× 1.016, 28× 1.143, 48× 1.524, 18× 1.7272, 10× 2.9997 (= 3.0) = 261: **the June 2010 fab drill file and the 2026 X2 drill gerber are the same holes** |
| `tools/check_drill_smaller.py` (board-local, new) | own IPC parser + the board through pcbnew: 261 records / 261 board holes, every record has one plated hole at its position; the pads with a smaller board drill are **exactly** SERIES_MIX 1-8, C2 1-2, C4 / C6 / C7 / C32 1-2 (18); `DRILL_SMALLER` has exactly the three decided pairs. OK |

Pad-shape clusters per footprint (F.Cu; B.Cu alike): only-Proteus copper (KiCad pad smaller): relay
SERIES_MIX 24.99 mm² (KiCad 1.4 mm pads against Proteus 2.54), RES40 resistors 14.14, MMK caps 3.60, C2
3.14, C8 / C28 2.73, DO-35 1.86, Q4 1.60, C1 / C36 / C37 0.66, C31 0.48; **only-KiCad copper**: DO-41 2.98 mm²
(square 2.2 mm cathode pad against the round 2.286), C1 / C36 / C37 1.26 (rounded-square + pad), 2 W
resistors 0.92 (2.4 vs 2.286 mm), DO-35 0.88 (square cathode pad). The TO-92 parts (round 1.5 vs 1.524)
and the footprints with Proteus pads (terminals, noval sockets, SW4-SW6, 100N Xicon, Solen, mounting
holes) show **no cluster at all**. DRC is clean with the added copper (Phase 3).

### Independent recomputation (scratch scripts in `build/tmp/indep`, no p2k code)

- **Schematic netlist vs IPC:** own parser of the IPC file (317 records, NNAME table, truncated-refdes
  table by hand) against `kicad-cli sch export netlist`: **71 pin sets = 71 pin sets** (66 nets + the 5
  N/C pads), compared as sets of (refdes, pin); every named IPC net has the same name in KiCad (`HYPPY2`
  is the sheet-local `/01 FX loop driver/HYPPY2`); no single-pin net.
- **Board vs IPC:** pcbnew: 136 footprints all on F.Cu, 257 pads; the 247 component pads within 0.0011 mm
  of their IPC record, all PTH, nets 1:1 (66), the 5 N/C pads on `unconnected-(…)` nets; H1-H10 at the 10
  IPC hole records (3.0 / 6.35, PTH, no net, no symbol link); 4 vias at the 4 IPC via records (1.27 / 0.508;
  `#00057` = `Net-(U5A-K2)`, 2× PWR-GND, SWLOOP); 515 tracks (F.Cu 0.508 ×244, 1.27 ×10, 1.524 ×23; B.Cu
  0.508 ×181, 1.016 ×5, 1.27 ×15, 1.524 ×30, 1.778 ×7), none without a net; 0 zones; only the 4 outline
  segments as board graphics; 2 copper layers, 1.6 mm.

### PDF vs IPC, read independently (all four pages, every wire)

The PDF was rendered again (220 dpi, crops of the dense areas) and read without the sheet scripts or
the Phase 1 notes, then compared with `reference/pins_by_net.md`. **No disagreement on any page**
(connections, junction dots, crossings without a dot, labels, polarities):

- **Page 1 (relay, densest part):** lower pole: moving contact → R26 (`#00018`: R26-1, SERIES_MIX-2);
  upper fixed contact ← the R54 / ground column with a dot at the contact row (SERIES_MIX-3 on PWR-GND);
  lower fixed contact ← C30-2 with the `send` label (SEND: C30-2, SERIES_MIX-1); the SEND row crosses
  the R54 column **without** a dot. The lever is drawn on the ground contact (rest position = R26
  grounded, consistent with pad 3 = NC). Upper pole: three open stubs (pads 6-8 N/C). Coil: left end +
  D1 cathode (bar on the left) + `SWLOOP`; right end + D1 anode + `PWRH4` (SERIES_MIX-4 / -5, D1-K / -A).
  Valve: 7 ← C29 / R49; 8 → C30-1 / R46; 6 → F with R48; 1 → R45 / C31; 2 → C32-1 / R54; 3 → HYPPY2;
  4 → PRE-H4 / PWRH4; 5 → PRE-H5 / PWRH5 (the PRE-H5 wire crosses the PRE-H4 row without a dot); 9 open.
  C28 / C8: the hollow (+) plate on the divider node / on HYPPY2, the hatched plate on ground.
- **Page 2:** F / G / H chain, Q4 (the symbol's body diode points from the H side to the PIPOWER side:
  source on H, drain on PIPOWER), D3 anode on H, zener string D6-D5-D4 cathodes up; the three gate rows:
  dots at C4 / D12 / R270+Q90 (A), C6 / D11 / R100+Q10 (D'), C7+D10 / R110+Q20 (C'), every other
  crossing of the C6, C7, D12, D11, R110, R100 columns and of the Q10 / Q90 emitter columns with the
  rows and the R27 / R29 wires is **without** a dot; D10-D12 anodes joined to the Q8 collector; all four
  2N3906 drawn PNP with the emitter on the PWR-GND row; SWLOOP bus: D2 at the corner, dots at D7, D8, D9.
- **Page 3:** cathodes 3 and 8 joined by the box around the heater rows (no dot where the PWRH4 / PWRH5
  rows cross it); MV0 node R3 / R4 / R5 / R15; tail node R4 / R8 / C9 / C5 / C3; ground column PGND / R10 /
  SUKKA / CHASSIS.
- **Page 4 (J112 switches, SW4-SW6):** per channel SENDnW → 5k → node (drain of the first J112, 2k2) →
  2k2 → node (drain of the second J112, SENDn terminal); both sources on the PWR-GND row (dots at each
  source, no dot where the gate wires of Q2, Q3, Q5 cross the row or where Q1's / Q6's gate wire crosses
  the next source column); gates in pairs to C' (Q1, Q2), A (Q3, Q5), D' (Q6, Q7). SW4-SW6: contact 2 ←
  the RETURNn terminal (around the 1M), contact 1 → the NOLLA column (dots at each 100k and each contact
  1 branch), pin 3 on the 1M / 100k node. `send` and `nolla` are lower case in the PDF (IPC `SEND`,
  `NOLLA`), as recorded.
- Values: every refdes and value of `lib/part_map.csv` is on its PDF page (pdftotext), value counts
  per page agree.

Resistor pin numbers are not printed in the PDF, so pin 1 / 2 of the resistors and unpolarised
capacitors cannot be read from it (the IPC decides; every resistor on page 4 has pin 2 on the left).

### No-connect pins (the pilot's blind spot) and one more, closed here

- The pilot's case does not exist here: **no symbol pin has the type `no_connect`** (grep step in
  check_all.sh; netlist: the five pins are `passive+no_connect`, i.e. passive pins with a flag), and a
  flagged pin wired to another net is caught by the comparison (Phase 1 negative test 2).
- **New blind spot found:** two flagged N/C pins **wired to each other** (scratch copy
  `build/tmp/neg/sch_nc`: a wire between SERIES_MIX pins 7 and 8, flags kept). KiCad puts both pins in
  one net `unconnected-(SERIES_MIX-Pad7)`; `compare_netlists` treats every pin of an `unconnected-(…)`
  net as a singleton and reports **"compare: OK", 0 wrong-net pins** (old `tools/compare.py`). ERC only
  warns (`no_connect_connected`), which the old `tools/erc.sh` let pass. So relay pole 2 (or U4-9 /
  U5-9 with a neighbour) wired together in the schematic was invisible to every Phase 1 check.
  It is **not** the case in the schematic (the independent pin-set comparison above: 71 = 71 sets, the 5
  N/C pins alone), and it is now closed twice, board-locally: `tools/compare.py` fails on an
  `unconnected-(…)` net with more than one pin, `tools/erc.sh` fails on `no_connect_connected`
  (p2k candidate 19).
- Board: the 5 N/C pads carry their own `unconnected-(…)` net; nearest track copper 1.59 mm (relay
  6-8), 4.08 mm (U4-9), 3.20 mm (U5-9) away; `assign_nets` has them as 5 single-pad groups.

### Review of the scripts

Read in full: `p2k_config.py`, `tools/check_all.sh`, `make_pcb.sh`, `erc.sh`, `check_sheets.sh`,
`compare.py`, `gen_footprints.py`. Read in part: `gen_symbols.py` (pin types), `sheets/sheet01.py` and
`_common.py` (relay, valve, no-connect flags), `measure_gaps.py` (re-run). **Not read line by line:**
`make_part_map.py`, `check_pin_order.py`, `sheets/sheet02-04.py` – their results were checked from the
outside instead (the independent netlist and board comparisons, the PDF reading, the part values
against the PDF text).

Blind spots found (all closed board-locally or recorded):

1. **`DRILL_SMALLER` is matched by diameter pair, not by pad** (both shared tools): a board whose R13-1
   drill is 0.75 mm (Proteus 0.762: the MMK pair) passes `ipc356_diff` and `gerber_roundtrip --check`,
   only the count in the output changes (8× → 9×); a relay pad drilled 1.2 mm instead of 0.7 passes too
   (larger is always accepted). "Exactly these 18 and nothing else" was therefore not enforced. Closed
   by `tools/check_drill_smaller.py` (step in check_all.sh; p2k candidate 20).
2. **Joined N/C pins** (above; p2k candidate 19).
3. **Pad size changes are invisible to both Phase 4 checks** (a KiCad pad grown or shrunk is a "pad
   shape" cluster / an info line; negative tests `pad_grown`, `pad_shrunk`): as designed
   (`FOOTPRINT_PAD_SIZES = "kicad"`), caught by `gen_footprints --check`, the `make_pcb --check` byte
   compare and, where it matters, DRC. Stays true only while the board is generated (p2k candidate 21).
4. Solder resist, silk and assembly gerbers are not compared with Proteus by any check (the KiCad
   footprints bring their own); intended, Phase 5 material.
5. Comment only: `p2k_config.py` `TRUNCATED_NETS` said "PIPOWER … Q4-2, R9-1, R66 (PI supply output)";
   the net `#00028` is PIPOWER-1, Q4-2 (drain), R9-2 – the supply **input**. Comment corrected, value
   unchanged.

Spot checks on the saved board (pcbnew, read-only): polarity marks – the rounded-square KiCad pad 1 is
the `+` pad of C8 / C28 (HYPPY2, `#00011`) and pad 2 of C1 / C36 / C37 (H / F / G), the K pad of every diode
(D1-K SWLOOP, D3-K gate node, D2-K SWLOOP, D12-K A); Q4 pad 1 (rect) = gate; relay pin-1 mark on Proteus
pad 5 (Finding 15); TO-92 pads all round 1.5 / 0.8 (decision (a)); U4 / U5 on F.Cu, rotation 0, pads 1-9
round 4.318 / 1.727 (not moved, as instructed); SW4 pads 1 / 2 / 3 = NOLLA / RETURN1 net / node.

Earlier findings (numbers as in "Findings"):

| # | Verdict | Checked how |
|---|---|---|
| 1 | **confirmed** | PDF page 2: terminals A / C' / D' at R28 / R27 / R29, the labels A / C' / D' on the collector rows; IPC `#00033` = A-1, R28-2 against net `A` = C4-2 D12-K Q3-3 Q5-3 Q90-3 R270-1 |
| 2 | confirmed | IPC PWR-GND: 34 pins incl. PIRETURN, PRERETURN, SIGNALGND, EQGND, PGND, SUKKA, CHASSIS |
| 3 | confirmed | PDF page 1 (above); IPC N/C on SERIES 6-8 |
| 4 | confirmed | PDF: body diode direction of the Q4 symbol (source = H side); nets as stated |
| 5, 14 | confirmed | hand note "R47 = 50-100k" on page 1; the dot on page 2's ground row above C7 has no wire (C7's wire joins the row one dot further right) |
| 6 | confirmed | pdftotext: `J112` ×6 on page 4, `MMK J04 5MM` ×4 |
| 7 | confirmed | Mechanical 1: `%TF.FileFunction,NonPlated,1,2,NPTH*%`; both resist files `FilePolarity,Negative` |
| 8 | confirmed | part map: U4 value 12AT7, device 12AX7 |
| 9 | confirmed | PDF page 2 prints pin 2 at the hollow plate of C1 / C36 / C37 (on H / F / G), pin 1 at the hatched plate (ground) |
| 10, 15 | confirmed, and independently: by pad pitch the relay pads 4 / 5 are the coil end (7.62 mm to 2 / 6, then 5.08, 5.08), so pads 2 / 6 sit on the Omron COM positions (4 / 13), 3 / 7 on NC (6 / 11), 1 / 8 on NO (8 / 9) **in either mirror state**: SEND on a NO contact, PWR-GND on an NC contact, as the PDF draws it. The mirror only swaps the poles and coil ends (check_pin_order, scripted, not re-derived) |
| 11 | **confirmed** | the independent reading above: 0 disagreements |
| 12 | confirmed | PDF: PNP symbols, emitters on the PWR-GND row, collectors on the gate rows, pull-ups to VREF |
| 13 | nets confirmed; **refined**: the PDF draws all three levers on contact 1 (the NOLLA side), while Proteus names contact 2 `NC`. Which position is "rest" cannot be decided from the PDF (an interactive Proteus switch is drawn in its saved state); for a panel toggle it does not matter. Contact 2 = RETURN terminal (1M bypassed), contact 1 = NOLLA (100k bypassed) holds either way |
| 16, 17 | confirmed | IPC pads of U4: 10.5 mm from the centre (PCD 21.0), pad 1 at −144°, 2 at 180°, 3 at 144° (Y up) = clockwise from the top; holes at the listed positions. Mounting side: the user's statement (not verifiable here) |
| 18 | confirmed | the drill tables above (IPC, drill gerber, 2010 Excellon all 1.143 / 0.762) |
| 19 | confirmed | DRC: 3 `track_dangling` (H 1.905 mm at (-60.325, 67.945), Net-(Q90-B) 0.635 mm, the B.Cu SWLOOP stub); the round trip has no uncovered draw, i.e. the stubs are Proteus copper |
| 20 | confirmed | `tools/measure_gaps.py 0.45` re-run: pad–track 0.4209 mm at Q3-1 / PWR-GND, 17 pairs below 0.45, copper–outline 1.143, drill–drill 1.270 |
| Phase 3 "pcbnew re-derives track nets on load" | consistent: `ipc356_diff` sees pads, vias and holes only; tracks are checked by the round trip and `assign_nets --check` |

Nothing refuted. New: Findings 21, 22.

### Negative tests (scratch boards in `build/tmp/neg/<case>`, written with pcbnew from the committed board, run with `P2K_PCB` / `P2K_REPORTS`; the repo board untouched: md5 of the board and the `.kicad_pro` equal before and after)

| Change | ipc356_diff | gerber_roundtrip --check | check_drill_smaller |
|---|---|---|---|
| none (control) | OK | OK | OK |
| an F.Cu SWLOOP track (at SERIES_MIX-4) moved 3 mm | OK (pads only) | **fails**: 2 other clusters (5.3 mm² only Proteus, 3.0 only KiCad), 2 uncovered draws | OK |
| the same track moved 0.2 mm sideways | OK | **fails**: 2 other clusters (3.6 / 0.77 mm²) | OK |
| the same track deleted | OK | **fails**: 1 other cluster, 1 uncovered Proteus draw | OK |
| the same track 0.508 → 0.3 mm wide | OK | **fails**: 1 other cluster 3.6 mm² | OK |
| a new 5 mm F.Cu track in free space | OK | **fails**: 1 other cluster, 1 KiCad draw off the Proteus copper | OK |
| the SWLOOP via deleted | **fails**: "Proteus via at (30.48, -50.8): no KiCad record" | **fails**: 2 other clusters (via pads), 1 drill | **fails** |
| the SWLOOP via moved 0.3 mm | **fails** | **fails**: 5 other clusters, drills | **fails** |
| the SWLOOP via drill 0.508 → 0.4 | **fails**: "drill Proteus 0.508, KiCad 0.3988 is smaller" | **fails** | **fails** |
| pad R13-1 net → PWR-GND | **fails**: "Proteus net HYPPY2 spans KiCad nets", "KiCad net PWR-GND spans Proteus nets" | OK (same copper) | OK |
| N/C pad SERIES_MIX-6 → net SEND | **fails**: "pad SERIES_MIX-6: N/C in Proteus, KiCad net SEND" | OK | OK |
| N/C pad U4-9 → net PWRH4 | **fails**: "pad U4-9: N/C in Proteus, KiCad net PWRH4" | OK | OK |
| footprint R13 shifted 0.1 mm | **fails**: R13-1 / -2 0.099 mm away | **fails**: 4 drill mismatches (the copper XOR calls it pad shape) | **fails** |
| R13-1 drill 0.8 → 0.7 mm | **fails**: "drill Proteus 0.762, KiCad 0.7010 is smaller" | **fails** | **fails** |
| **R13-1 drill 0.8 → 0.75 mm** (a `DRILL_SMALLER` pair on another pad) | **OK – not caught** | **OK – not caught** (count 9× 0.762→0.75) | **fails**: "R13-1: board drill 0.75 < Proteus 0.762, not a decided hole" |
| SERIES_MIX-1 drill 0.7 → 0.6 mm | **fails** | **fails** | **fails** |
| **SERIES_MIX-1 drill 0.7 → 1.2 mm** (a decided hole no longer smaller) | OK (larger is accepted) | OK | **fails**: "expected a board drill smaller than Proteus (1.143, 0.7), it is not" |
| H1 made NPTH | **fails**: "plated Proteus True, KiCad False" | **fails**: plated drill missing, non-plated extra | **fails** |
| H1 deleted | **fails**: "Proteus hole … nearest KiCad record 62 mm away" | **fails** on the drill (the missing 6.35 mm ring is classed pad shape, as on the pilot) | **fails** |
| U4 flipped to the bottom with pcbnew `Flip` (pads mirrored) | **fails**: U4 pads 17-21 mm off | **fails**: drills | **fails** |
| terminal EQOUT pad 3.048 → 2.2 mm; R13-1 pad 1.6 → 2.6 mm | OK | OK (pad shape) | OK – review item 3: only the byte compare / gen_footprints / DRC see pad sizes |

Config and source variants (scratch board roots `build/tmp/neg/cfg_<case>` with a copy of
`p2k_config.py`, run with `P2K_BOARD`):

| Change | Result |
|---|---|
| `DRILL_SMALLER = {}` | ipc356_diff **fails** with exactly 18 errors (C32, C2, SERIES_MIX 1-8, C4, C6, C7), roundtrip **fails** "18 drill mismatches", check_drill_smaller **fails** (pairs differ) – nothing else hides behind the acceptance |
| the pair (1.143, 1.0) removed | both tools **fail** on exactly C2-1, C2-2; check_drill_smaller **fails** |
| an extra pair (0.762, 0.7) added | ipc356_diff OK (nothing uses it) – check_drill_smaller **fails** (pairs differ) |
| `STACKED_VIAS = 1` | both tools **fail**: "0 stacked duplicate … STACKED_VIAS = 1" |
| Excellon: one hole 0.1 mm off | roundtrip **fails**: 2 Excellon errors |
| Excellon: tool T03 0.762 → 0.8 | roundtrip **fails**: 124 Excellon errors |
| `DRILL_EXCELLON` = the inch file itself | roundtrip **fails**: 522 Excellon errors (0.02 "mm" holes at inch coordinates: the shared reader ignores `INCH`, as on the pilot) |
| `reference/fab_2010_drill_metric.drl` edited by 1 µm | `excellon_metric.py --check` **not up to date** (restored) |
| a symbol pin of type `no_connect` (scratch copy of the library) | the grep step **fails** |
| scratch schematic: wire between SERIES_MIX pins 7 and 8 | old compare.py **OK (not caught)**; new compare.py **fails** ("net unconnected-(SERIES_MIX-Pad7) joins 2 pins"); `erc.sh` **fails** (1 `no_connect_connected`) |

Every change is caught by at least one check now in `check_all.sh`, except a pure pad-size change
(review item 3). Tracks are seen only by the round trip, nets only by `ipc356_diff`, "which pad has
the smaller drill" only by `check_drill_smaller`.

## Phase 5 – clean-up – done (Opus 5.5, clean context, 2026-11-20)

Verified state first: `tools/check_all.sh` printed exactly the Phase 4 "Last check output" (ALL CHECKS
PASSED). The user's answers (Decisions, "User decisions for Phase 5") were recorded before any change.
Model: the power amp pilot `~/dev/tube_power_amp_kicad` (read only), its Phase 5.

### User decisions (2026-11-20, through the coordinating session)

1. U4 / U5 on the bottom side with the standard noval numbering, footprint built mirrored – **done** (below).
2. `p2k place_refdes` as a `make_pcb.sh` step – **done** (below).
3. The three dangling Proteus stubs (Finding 19) – **kept as drawn**, no `REMOVED_TRACKS`; the 3
   `track_dangling` warnings stay. **Reversed by the user 2026-11-20 after the conversion: removed**
   ("Design fixes 2026-11-20").
4. TO-92 pin-1 dot (`PIN1_DOT`) – **kept**.
5. Body graphics (KiCad library), KiCad pad sizes, sheet names, KiCad refdes of the signed names, 1.6 mm
   – **kept**, nothing changed.
6. The board **stays generated** (`tools/make_pcb.sh`); see "When the board stops being generated".

### Noval sockets on the bottom side (decision 1)

- `tools/gen_footprints.py`: the spec `Valve_Noval_Belton_PCD21.00mm` gets the board-local key
  `bottom=True`; a wrapper around `footprints.build_library` (the pilot's, unchanged) marks the IPC pads
  of the spec's `ipc` part (U4) as bottom side, so the shared `from_ipc` builds the footprint
  **mirrored** (the shared tool mirrors only bottom SMD parts; THT pads are `both` in the IPC file;
  p2k candidate 23). Footprint name, pad numbers (= IPC pin ids), pad sizes, drills unchanged; the pad x
  coordinates and the body (Proteus Top Assembly square, mirrored with the pads) are mirrored. In the
  footprint's own view pins 1 → 9 now run in the **standard noval direction** (counter-clockwise seen
  from the component side = clockwise seen from the pins). No 3D model (none before; KiCad has no noval
  socket model).
- `p2k.check_footprints` finds the pattern fits **only mirrored** and writes U4 / U5 as `bottom`
  (orientation 180) into `reports/footprint_fit.csv`; `build_pcb` flips them: footprint layer B.Cu, silk
  / Fab / courtyard on B.SilkS / B.Fab / B.CrtYd, reference on B.SilkS. (A plain pcbnew `Flip` of the old
  top footprint would mirror the pads: Phase 4 negative test, and test 3 below.)
- Copper unchanged: every pad lands on the same IPC pad (check_footprints worst 0.001 mm, check_board,
  assign_nets, **ipc356_diff 261/261, 66 nets 1:1; gerber_roundtrip and check_drill_smaller: output
  identical to Phase 4**, `reports/roundtrip/` unchanged).
- `tools/check_pin_order.py` keeps the Phase 2 facts (unmoved KiCad `Valve_Noval_P` and the ideal noval
  fit the Proteus ids only mirrored) and adds `bottom_side_noval()` (the pilot's `bottom_side_octal()`
  with free-rotation fits, the noval steps are 36°): (a) project footprint vs an ideal standard noval in
  the footprint frame: unmirrored **0.006**, mirrored 19.318 → standard numbering; (b) project footprint
  vs the IPC pads of U4 / U5: unmirrored 19.314, mirrored **0.001** → bottom side; (c)
  `reports/footprint_fit.csv`: bottom = exactly U4, U5; (d) the board (`pcb.board_file()`, `P2K_PCB`
  overrides): U4 / U5 on B.Cu, the other 134 footprints on F.Cu.

### References (decision 2)

`tools/make_pcb.sh` step 4 `kipy -m p2k.place_refdes` (defaults, no `REFDES_PLACEMENT`), also in the
`--check` rebuild: **68 kept, 67 moved, 1 moved with 0.8 mm text, 0 on the Fab layer**; a second run on
the finished board keeps all 136 and leaves it byte-identical. No remaining silk warning involves a
reference (the 4 overlaps of the TO-92 pin-1 dots with neighbour references are gone too).

### DRC before / after Phase 5 (accepted error types in `p2k_config.py` `DRC_ACCEPTED`, reasons updated)

| Type | Phase 4 | sockets on B only | Phase 5 (sockets + place_refdes) |
|---|---|---|---|
| shorts / unconnected / parity / clearance / hole clearance / mask bridge | 0 | 0 | 0 |
| courtyards_overlap (error, accepted) | 47 | 40 | **40**, all between top-side parts (100N rows, TO-92 rows with R11 / R16 / R18, Q20 / R270, resistor / terminal rows, C30 with R24 / R26, ...); the U4 / U5 courtyards (B.CrtYd) no longer meet any part |
| pth_inside_courtyard (error, accepted) | 7 | 7 | **7**: H3 / H4 and V8_V9-1 in the B-side U5 / U4 courtyards, C8 + / − in U4's (a THT pad is on both sides; Finding 17), R24-1 / R26-1 in C30's |
| silk_overlap (warning) | 138 | 120 | **28**: KiCad library silk of neighbouring parts (TO-92 outlines over R11 / R16 / R18 / R270 boxes, C3 / C5 / C9 rows, R19-R24 boxes, C4 / C7 / R50, C29 / C6, SW4 / C37) and D3's library "K" text over Q4 |
| silk_over_copper (warning) | 55 | 55 | **27**: 2 W resistor (DIN0414) silk over their own / neighbour pads (R1 R2 R9 R45 R46 R48 R66 R67), 9 × socket body silk on B.SilkS over C8, H3 / H4 / H7, V8_V9 pads |
| track_dangling (warning) | 3 | 3 | **3** (Finding 19, kept: decision 3) |
| silk_edge_clearance (warning) | 2 | 2 | **0** |
| total | 252 | 227 | **105** |

The remaining 55 silk warnings are KiCad library footprint graphics and the Proteus socket body on the
Proteus placement (decision 5: library graphics kept). `p2k drc` fails only on unaccepted errors; the
warning counts are not enforced – a board change is caught by the `make_pcb --check` byte compare.

### Negative tests (all restored; `check_all.sh` afterwards: ALL CHECKS PASSED)

Scratch boards in `build/tmp/neg5/<case>` (pcbnew from the generated board, run with `P2K_PCB` /
`P2K_REPORTS`; the repo board untouched, md5 equal before and after).

| Change | Caught by |
|---|---|
| none (control scratch board) | all OK (check_pin_order, check_board, ipc356_diff, check_drill_smaller, roundtrip) |
| `bottom=True` removed from the noval spec | `gen_footprints --check` out of date; after regenerating: check_footprints OK (fits unmirrored, top) but **check_pin_order FAILED** (no standard numbering, not mirrored-only, footprint_fit.csv sides) and **make_pcb --check** not up to date |
| socket back on top: scratch board, U4 flipped to F (pcbnew `Flip`) | **check_pin_order** "wrong layer for ['U4']"; **check_board** U4 pads 6.5-21 mm off; **ipc356_diff** FAILED; **roundtrip** FAILED (2 drill mismatches) |
| socket on B with mirrored ids: scratch board, U4 pads mirrored in the footprint frame (stays B.Cu) | check_pin_order OK (it checks the library, the fit file and the layer); **check_board**, **ipc356_diff**, **roundtrip** FAILED (U4 pads 6.5-21 mm off the IPC pads) |
| footprint with mirrored ids in the library (pad x negated in the `.kicad_mod`) | **gen_footprints --check** out of date; **check_pin_order FAILED** (not the standard numbering, fits unmirrored, sides); check_footprints OK (it fits either way) |
| another part on B: scratch board, R13 flipped | **check_pin_order** "wrong layer for ['R13']"; check_board, ipc356_diff, roundtrip FAILED |
| `place_refdes` line removed from make_pcb.sh | **make_pcb --check** not up to date |
| place_refdes run again on the generated board | 136 kept, file byte-identical (idempotent) |

### Left open / when the board stops being generated

- Everything in "Findings about the original design" is report-only (the conversion reproduces
  Proteus); nothing there needs a decision for the conversion.
- Per the playbook (section 3, Phase 5) and decision 6: the board stops being generated at the **first
  manual layout change in KiCad – the user's call**, not done here. Until then `tools/make_pcb.sh` stays
  the only way to change the board. When the user edits the board by hand: remove the
  `make_pcb.sh --check` step from `tools/check_all.sh` and say so here; check_board / assign_nets / DRC /
  ipc356_diff / gerber_roundtrip / check_drill_smaller keep working on the edited board and show the
  intended differences (record them as deviations).
- Courtyard / silk items above (library graphics on the Proteus placement), as decided.

## Design fixes 2026-11-20 (Opus 5.5, after the conversion)

User decisions: "Decisions", "User decisions 2026-11-20, after the conversion" (recorded before the work).
Verified state first: `tools/check_all.sh` printed the Phase 5 "Last check output" (ALL CHECKS PASSED).
Everything is done in the generators and config; the board, schematic, libraries and reports are
regenerated (`tools/make_pcb.sh`, sheet scripts, `gen_symbols`, `gen_footprints`, `tools/ipc356.py`).
`tools/p2k` and its pin are unchanged.

### Which findings are fixed

| Finding | Action |
|---|---|
| 15 relay G5V-2(HI) mirrored / Proteus pin ids | **fixed**: Omron pin numbers on symbol and footprint (below) |
| 19 three dangling Proteus stubs | **fixed**: removed with `REMOVED_TRACKS` (below) |
| 5, 8, 21 values (R47 33k vs hand note, U4 12AT7 on the 12AX7 device, C8 / C28 22u) | **unchanged** (user: values stay) |
| 14 stray junction dot, page 1 hand note | nothing to fix in KiCad: the redrawn sheets have no stray dot; the hand note stays as a text (it belongs to Finding 5) |
| 16 noval numbering | already fixed in Phase 5 (bottom side, standard numbering) |
| 9 C1 / C36 / C37 `+` = pin 2, 10 SW-SPDT ids | left: pin numbering only, the footprints carry the same ids and mark `+`; changing them is a redesign choice (not asked) |
| 1, 2, 3, 4, 12, 13, 17, 18, 20, 22 | design / topology facts or already decided (18: `DRILL_SMALLER`); changing them changes the circuit or the copper - for the redesign, not a clean-up |

### Relay SERIES_MIX on Omron pin numbers (Finding 15)

- `p2k_config.py` **`IPC_PIN_IDS`** (board-local key) `{"SERIES_MIX": {Proteus pin: Omron pin}}`: 1 → 9
  (NO2, SEND), 2 → 13 (COM2, #00018 = R26), 3 → 11 (NC2, PWR-GND), 4 → 16 (coil, SWLOOP), 5 → 1 (coil,
  PWRH4), 6 → 4, 7 → 6, 8 → 8 (pole 1, N/C). That is the physical mapping of a top-mounted G5V-2 found in
  Phase 2 (the former `G5V2_RENUMBER`, inverted).
- **`tools/ipc356.py`** (new): `p2k ipc356` with the renaming applied after the shared parser (wraps
  `ipc356.parse`); fails unless every IPC pad of a listed refdes is renamed, the targets are unique and the
  refdes exists. `reference/` is regenerated with it, so `ipc356_pads.json` and the cheat sheets carry the
  Omron ids and every check reading them (check_symbols, compare, check_footprints, check_pin_order,
  check_board, assign_nets, ipc356_diff, gerber_roundtrip) compares against the Omron ids; positions and
  nets stay Proteus'. `check_all.sh` runs `tools/ipc356.py --check` instead of `p2k ipc356 --check`
  (p2k candidate 24).
- `tools/gen_symbols.py`: KiCad `Relay:G5V-2` **unchanged** (no renumbering; KiCad's symbol has no pin
  names, the numbers are the Omron ones). `tools/sheets/sheet01.py`: the Proteus pole is drawn as Omron
  **pole 2** (COM 13 under R26, NO 9 to C30 / SEND, NC 11 to ground), the coil 16 on SWLOOP and 1 on
  PWRH4 with D1 (K on SWLOOP, A on PWRH4) one column right; pole 1 (4 / 6 / 8) has the no-connect flags.
  Relay placed one 10.16 mm column right so the contacts keep their Proteus positions
  (`reports/render/01_fx_loop_driver.png`).
- `tools/gen_footprints.py`: the rule maps G5V-2(HI) to KiCad's **`Relay_THT:Relay_DPDT_Omron_G5V-2`
  unchanged**; the project footprint `Relay_DPDT_Omron_G5V-2_Proteus` (renumbered copy) is gone (17
  footprints, 13 project). Same pads 1.4 / 0.7, same placement (check_footprints: top, 0°, same origin,
  residual 0.000).
- `tools/check_pin_order.py`: the unmoved KiCad G5V-2 with the Omron ids of `reference/` fits
  **unmirrored 0.000** (mirrored 7.62); the Phase 2 Proteus-pole mapping (Omron pole 1 on Proteus 1-8,
  expressed in today's ids) still fits **only mirrored** - proves `IPC_PIN_IDS` is the physical and not
  the mirrored mapping. `tools/check_drill_smaller.py`: the 8 relay holes by their Omron pad numbers.
- Copper: unchanged (ipc356_diff 261 / 261, 66 nets 1:1, 0 mismatches; check_board 0.001 mm; round trip
  areas unchanged for the relay; only the pad names in the reports changed).

### Dangling stubs removed (Finding 19)

- `p2k_config.py` **`REMOVED_TRACKS`** (shared p2k key, IPC frame): B.Cu SWLOOP (84.455, −42.545)–(84.455,
  −43.815), F.Cu Net-(Q90-B) (−20.0025, −43.18)–(−19.3675, −43.18), F.Cu H (−60.325, −67.945)–(−58.42,
  −67.945) (R67-2). gerber_to_tracks: 515 → **512 tracks** ("removed as recorded: 3 tracks"); assign_nets
  81 groups, 0 shorts / orphans / opens (unchanged).
- Round trip: "Proteus objects not compared (recorded deviations): 3 Conductor draws (REMOVED_TRACKS)";
  F.Cu only-KiCad 6.39 → 6.41 mm² = one new 0.073 mm² "pad shape" cluster at the R67-2 corner that the
  H stub used to cover (the same 2 W pad corner as R46-2's); everything else equal.
- DRC: track_dangling 3 → **0** (total 105 → 102: 40 + 7 accepted errors, 28 silk_overlap, 27
  silk_over_copper warnings).
- New check **`tools/check_no_dangling.py`** (check_all step after DRC): fails on any `track_dangling` /
  `via_dangling` in `reports/drc.json`. Needed because `p2k drc` does not enforce warnings and the round
  trip passes when a stub is on both sides (negative test 1b).
- `tools/make_pcb.sh` fix: the steps of `run()` are chained with `&&`. `run` is called inside `||` in
  `--check` mode, where `set -e` is off, so a failing gerber_to_tracks (e.g. a `REMOVED_TRACKS` entry
  without a draw) was followed by assign_nets on a trackless board and its ERROR line was filtered out;
  the step still failed (board not byte-identical) but for the wrong visible reason. Now it prints
  `gerber_to_tracks: ERROR REMOVED_TRACKS: … missing …` and `make_pcb: FAILED`. The other board repos'
  `make_pcb.sh` have the same `run()` (not changed here; p2k candidate 25).

### Negative tests (config / sheet edited temporarily or scratch boards in `build/tmp/neg6/<case>`; all restored, md5 of the board, sheets and `reference/ipc356_pads.json` equal afterwards; `check_all.sh` afterwards: ALL CHECKS PASSED)

| Change | Caught by |
|---|---|
| 1a `REMOVED_TRACKS` entry of the H stub deleted (board not regenerated) | **make_pcb --check** (board / assign_nets not up to date), **gerber_roundtrip** FAILED (1 unexplained cluster, 1 Proteus draw without KiCad copper) |
| 1b same, board regenerated in place | `check_all`: **check_no_dangling** FAILED (`track_dangling: Track [H] on F.Cu, length 1.9050 mm`); every other step passes (stub on both sides) - the reason for the new step |
| 2a non-existent track listed (`("F.Cu", 1, 1, 2, 1)`) | **make_pcb --check**: `gerber_to_tracks: ERROR REMOVED_TRACKS: 4 listed, found 3 draws (missing …)`, `make_pcb: FAILED` |
| 2b real stub with a wrong end point (−58.40 for −58.42) | same: `3 listed, found 2 draws (missing …)` |
| 3a relay pins on the wrong net in the schematic (wires to 9 and 11 swapped in sheet01.py) | **compare**: 3 wrong-net pins, `KiCad net PWR-GND merges IPC nets [PWR-GND …] [SEND …]`, 1 error |
| 3b `IPC_PIN_IDS` = the mirrored mapping (Omron pole 1 on the Proteus pole) | **ipc356 --check** stale; after regenerating `reference/`: **compare** 8 wrong-net pins, **check_pin_order** (KiCad G5V-2 fits mirrored), **check_board**, **ipc356_diff** FAILED |
| 3c `IPC_PIN_IDS` with a pin missing | **tools/ipc356.py**: `IPC pins [1..8], listed [1..7]` |
| 3d scratch board: SERIES_MIX pad 9 on PWR-GND | **check_board** `SERIES_MIX-9: net PWR-GND, IPC net SEND`, **ipc356_diff** FAILED, **assign_nets --check** (SEND spans two KiCad nets) |
| 3e scratch board: pad numbers 9 / 11 swapped (copper nets kept) | **check_board** (5.08 mm from the IPC pad, wrong nets), **ipc356_diff** FAILED |

### Left open

- Generation stops later (user decision 4): after the shared-tool migration; then remove the
  `make_pcb.sh --check` step from `check_all.sh` (Phase 5 "Left open").
- `IPC_PIN_IDS` / `tools/ipc356.py`, `tools/check_no_dangling.py` and the `make_pcb.sh` `&&` fix were
  board-local: replaced in the shared-tool migration 2026-11-20 (p2k candidates 24, 25).

## Shared-tool migration 2026-11-20 (Opus 5.5)

Task: `tools/p2k/docs/CANDIDATES.md` section 7.3 (PF), coordinating-session prompt. Every board-local
p2k workaround is replaced by the shared tool / config key of proteus2kicad **a9a286c** (all p2k code is in
2fb1563 = batch Z; later commits are docs only). Proven per commit from a clean clone with
`~/dev/proteus2kicad/tools/regress.sh a9a286c tube_pi_fxloop_kicad` (clone, regenerate every generated
file, `check_all.sh`, clean `git status`): **PASS** after each commit.

### Commits

1. **Bump** `tools/p2k` c5682dd → a9a286c (`da63c7d`). `p2k ipc356` (still through the old
   `tools/ipc356.py`) re-baselines exactly 2 lines of `reference/pin_nets_by_component.md`: `Net aliases:
   none.` and the `Index:` line naming `MV0 N6 P6` (was `MV`, `N`, `P`) - **decision D-R** (batch R report
   texts). No strict exception needed: the D-Z default set (`no_connect_pin_type`, `nc_joined`,
   `net_names`, `derive_max_move`, `hole_refdes`, `track_nets`, `roundtrip_counts`) passes; the new
   strict lines print to stdout only.
2. **Migration** (`81e19cd`): board-local tools deleted, shared keys added; every generated file
   byte-identical except the two accepted re-baselines below (D-K2, R1).
3. No design change is listed for this board in CANDIDATES.md 7.3, so there is no third commit (this
   record is docs only).

Regression (`regress.sh a9a286c tube_pi_fxloop_kicad`): `da63c7d` PASS (63 s); `81e19cd` PASS (70 s). A
first try of commit 2 failed the clean-tree step: the R1 line of `reports/roundtrip/roundtrip.txt` had been
reverted by the negative-test restore (`git checkout reports/`) before the commit; regenerated and amended
before pushing, then PASS.

### Board-local → shared

| Deleted / replaced | Shared tool / key now |
|---|---|
| `tools/make_part_map.py` readers (`_strings`, `lyt_parts`, `LATIN1_PARTS`) | data only: `part_map.run(SPEC)` with `LATIN1=True`, `CHECK_UNUSED_DEVICES=True`, `COMMENT` = the committed first line; `lib/part_map.csv` identical |
| `gen_symbols.py` `pin_types()` | `from_std(..., pin_types={"*": PAS})` (valve) |
| sheets `_common.py` `place_mirrored()`, `place_rot90_mirrored()` (sheet02 Q4) | `Sheet.place(..., mirror="x" / "y")` (Q4: `place(..., 90, mirror="y")`) |
| sheets `term()` body | `sheetkit.terminal(sh, ref, x, y, d, symbol=sym(ref), value=sh_value(ref), justify="away")` |
| sheets `ph()` capacitor `ref_at` / `value_at` | `place(..., text="above", text_gap=3.175)` - **D-K2** re-baseline |
| `tools/check_sheets.sh` | `p2k sheets --check` |
| `tools/compare.py` (type-safe sort key, joined N/C nets) | `p2k compare_netlists` (C1 fixed; strict `nc_joined`, `net_names` on by default) |
| check_all step `grep "(pin no_connect"` | strict `no_connect_pin_type` (check_symbols, default on) |
| `tools/erc.sh` | `p2k erc`, `ERC_FATAL_WARNINGS = {"no_connect_connected", "footprint_link_issues"}` |
| check_all `PYTHONDONTWRITEBYTECODE` / `rm -rf __pycache__` | `board.config()` executes the config source (G1) |
| `gen_footprints.py` `fp_lib_table()` | `FP_LIB_TABLE = True` (p2k_config.py; default descr = the committed one) |
| `gen_footprints.py` `build_library` wrapper (`bottom`) | spec key `bottom=True` |
| `gen_footprints.py` `derive` wrapper (`ROUND_PAD1`, `_dot`) | spec keys `pads={"1": dict(shape="circle", expect_shape="rect")}`, `pin1_dot=PIN1_DOT` |
| `tools/check_pin_order.py` | `p2k check_pin_order`, `PIN_ORDER` (15 entries: `spec=` + `polarity` for the derived groups, `G5V2_POLE1` computed in `p2k_config.py` from `IPC_PIN_IDS`, Valve_Noval_P mirrored, ideal noval / footprint vs ideal / footprint on IPC with `free_angle` and `other=1.0`, `turn="clockwise"`, SW4-SW6 `distances`), `PIN_ORDER_BOTTOM = {"U4", "U5"}`; every residual and angle as the board script printed |
| `tools/ipc356.py` | `p2k ipc356 [--check]` with the shared `IPC_PIN_IDS` (same key and values; `reference/` identical) |
| `tools/check_no_dangling.py` | `DRC_EXPECTED_WARNINGS = {"track_dangling": 0, "via_dangling": 0}` (p2k drc) |
| `tools/check_drill_smaller.py` | `DRILL_SMALLER` pad sets: SERIES_MIX; C2; C4 / C6 / C7 / C32 (ipc356_diff and gerber_roundtrip) |
| `tools/excellon_metric.py` + `reference/fab_2010_drill_metric.drl` | `DRILL_EXCELLON = "source/fab_2010/poweri - CADCAM Drill.TXT"` (inch, read natively) - **R1** re-baseline |
| `tools/make_pcb.sh` (`run()` chained with `&&`) | one-liner `exec tools/p2k/bin/p2k make_pcb "$@"` (default `PCB_STEPS`; kept as a file because the regression harness calls it) |
| `tools/measure_gaps.py` | `tools/p2k/bin/kipy -m p2k.measure_gaps` |

Kept in the board repo: `tools/check_all.sh`, `tools/make_part_map.py` (SPEC), `tools/gen_symbols.py`,
`tools/sheets/*` (sheet scripts and board helpers `part`, `sym`, `sh_value`, `term`, `P`, `noval`, `pv`,
`ph`, `q_right`, `send_channel`, `return_block`, `diode_input`), `tools/gen_footprints.py` (RULES,
PROJECT), `tools/make_pcb.sh` (one line). **Strict opt-outs: none** (`STRICT_CHECKS` / `STRICT_CHECKS_OFF`
absent).

### Accepted re-baselines

- **D-R** (commit 1): `reference/pin_nets_by_component.md`, 2 lines (above).
- **D-K2** (commit 2): `kicad/01_fx_loop_driver.kicad_sch` (8 lines: C29, C30, C31, C32 Reference /
  Value angle 0 → 270) and `kicad/03_phase_inverter.kicad_sch` (2 lines: C3, 0 → 90). The old `ph()`
  passed angle 0 on a rotated capacitor, so KiCad drew the texts vertical over the plates; the shared
  `text_gap` passes the angle that draws them horizontal. Positions unchanged. Rendered both sheets
  (`p2k render_sheet`, `build/tmp/dk2/`): the five capacitor texts are horizontal above the part. ERC,
  compare, every netlist check unchanged.
- **R1** (commit 2): `reports/roundtrip/roundtrip.txt`, 1 line: `== excellon (fab_2010_drill_metric.drl):
  …` → `== excellon (poweri - CADCAM Drill.TXT): …` (file name only; 261 / 261 holes matched, same tool
  table).

### Negative tests (config / footprint script edited temporarily, all restored; md5 of the board, `reference/*` and `lib/tube_pi_fxloop.pretty/*` equal afterwards)

| Change | Caught by |
|---|---|
| relay `PIN_ORDER` entry expected `mirror=True` | **check_pin_order** `SERIES_MIX: unmirrored 0.000, expected mirrored <= 0.01` |
| C1 renumbering `{"1": "1", "2": "2"}` in gen_footprints | **check_pin_order** `C1 C36 C37: the marked base pad 1 is pin '1', expected '2'` (polarity) |
| noval `turn="counter-clockwise"` | **check_pin_order** U4 / U5 `pins 1 -> 9 run clockwise, expected counter-clockwise` |
| `bottom=True` removed from the noval spec (library regenerated) | **check_pin_order** footprint vs ideal (fits mirrored) and footprint on IPC (fits unmirrored) |
| `DRILL_SMALLER` (0.762, 0.75) without C32 | **ipc356_diff** and **gerber_roundtrip** `C32-1 / C32-2: KiCad drill smaller, not in the entry's pad set` |
| `IPC_PIN_IDS` SERIES_MIX pin 8 → "6" (duplicate target) | **p2k ipc356** `target pin ids not unique` |
| `IPC_PIN_IDS` SERIES_MIX pin 8 dropped | config import fails (`G5V2_POLE1` KeyError '8'), so every tool stops |
| `REMOVED_TRACKS` H-stub entry dropped, board regenerated in place | **p2k drc** `1 track_dangling warnings, DRC_EXPECTED_WARNINGS 0` |

### p2k candidates (section "p2k candidates" below) after the migration

| # | Status |
|---|---|
| 1 | solved in p2k a9a286c (I3 / I4, D-R re-baseline) |
| 2 | not migrated: open in p2k (I1 `truncated_nets_keys`); no effect here, every `TRUNCATED_NETS` key is a KiCad refdes |
| 3 | solved in p2k a9a286c (G1; the check_all bytecode lines are gone) |
| 4 | not migrated: deferred in p2k (I2); not needed here |
| 5 | solved in p2k a9a286c (P1 / P2: `LATIN1=True`; the local reader is gone) |
| 6 | solved in p2k a9a286c (P4 reader); nothing to migrate: the pinouts were read once by hand and are recorded in `gen_symbols.py` |
| 7, 10 | solved in p2k a9a286c (K1 `place(mirror=)`) |
| 8, 12 | solved in p2k a9a286c (G3 playbook notes; nothing board-local) |
| 9 | solved in p2k a9a286c (C1; `tools/compare.py` deleted) |
| 11 | solved in p2k a9a286c (K2 `text_gap`; D-K2 re-baseline) |
| 13 | solved in p2k a9a286c (F1 `FP_LIB_TABLE`, F11 `check_pin_order` with `free_angle`, `turn`) |
| 14 | solved in p2k a9a286c (F3 `max_move`, strict `derive_max_move` on by default: limits printed, all pass) |
| 15 | solved in p2k a9a286c (E1 `ERC_FATAL_WARNINGS`, CF3 check_footprints resolves the fp-lib-table with `FP_LIB_TABLE`) |
| 16 | solved in p2k a9a286c (F4 `pads`, `pin1_dot`) |
| 17 | solved in p2k a9a286c (B7 `DRC_ACCEPTED_ITEMS`, B9 `PENDING`); not used here (no pending items) |
| 18 | solved in p2k a9a286c (B11 `p2k.measure_gaps`; `tools/measure_gaps.py` deleted) |
| 19 | solved in p2k a9a286c (C2 strict `nc_joined` default; `no_connect_connected` fatal in `ERC_FATAL_WARNINGS`) |
| 20 | solved in p2k a9a286c (R3 `DRILL_SMALLER` pad sets) |
| 21 | not migrated: R5 `roundtrip_pad_match` is opt-in (off by default per D-Z until the pad sizes are a decided design); the byte compare covers it while the board is generated |
| 22 | solved in p2k a9a286c (R1 inch Excellon, C5 `P2K_SCHEMATIC`) |
| 23 | solved in p2k a9a286c (F2 spec `bottom`, B8 `DRC_EXPECTED_WARNINGS`) |
| 24 | solved in p2k a9a286c (I6 `IPC_PIN_IDS` in `p2k ipc356`) |
| 25 | solved in p2k a9a286c (B12 `p2k make_pcb` stops at the first failing step; B8 replaces `check_no_dangling.py`) |

### Left open

- **Stop generating the board** (Phase 5 "Left open", user decision 4): the board is still generated
  (`make_pcb.sh --check` in `check_all.sh`); when to stop is the user's call. Then remove that step, say so
  here, and record hand edits as deviations (check_board / assign_nets / DRC / ipc356_diff /
  gerber_roundtrip keep working on the edited board).
- The meta repo `tube_amplifier_kicad` bumps its submodule after all boards are migrated (coordinating
  session).

## Last check output

`tools/check_all.sh` (2026-11-20, after the shared-tool migration, p2k a9a286c; every step runs a shared
tool, `make_pcb.sh` = `p2k make_pcb`):

```
== KiCad environment
pcbnew 10.0.7
== IPC-D-356A parser self-check
ipc356: nets=66, records=261, refdes_raw=125, tht_records=261, smd_records=0, smd_top=0, smd_bottom=0, nc_pads=5, vias=4, free_pads=0, holes=10, parts=126
ipc356: OK
ipc356: pin ids renamed (IPC_PIN_IDS): SERIES_MIX 1->9 2->13 3->11 4->16 5->1 6->4 7->6 8->8
== Gerber X2 export vs IPC (pads, vias, holes, drills, outline)
  8 gerbers, one SameCoordinates id
  Top Copper: Draw:Conductor 277, Draw:Profile 4, Flash:ComponentPad 247, Flash:OtherPad,Unknown 10, Flash:ViaPad 4
  Bottom Copper: Draw:Conductor 238, Draw:Profile 4, Flash:ComponentPad 247, Flash:OtherPad,Unknown 10, Flash:ViaPad 4
  drills: 261 plated, 0 non-plated
  outline 225.4 x 71.8 mm at (-123.83, -78.11)
check_sources: OK
== Part map up to date
make_part_map: lib/part_map.csv up to date, 126 parts (126 on the board); per sheet 1:24 2:46 3:24 4:32
== Symbol library up to date
gen_symbols: lib/tube_pi_fxloop.kicad_sym up to date (13 symbols)
== Symbol pin sets vs IPC
  12AX7                  2  pins  9  U4 U5
  2N3906                 4  pins  3  Q8 Q10 Q20 Q90
  C                     11  pins  2  C29 C30 C31 C32 C2 C4 C6 C7 ...
  C_Polarized            2  pins  2  C8 C28
  C_Polarized_21         3  pins  2  C1 C36 C37
  D                      8  pins  2  D1 D2 D7 D8 D9 D10 D11 D12
  D_Zener                4  pins  2  D3 D4 D5 D6
  G5V-2                  1  pins  8  SERIES_MIX
  IRF820                 1  pins  3  Q4
  J112                   6  pins  3  Q1 Q2 Q3 Q5 Q6 Q7
  PIN                   39  pins  1  EQGND EQOUT MVX PRE_H4 PRE_H5 A C_PRIME D_PRIME ...
  R                     42  pins  2  R13 R26 R45 R46 R47 R48 R49 R50 ...
  SW_SPDT                3  pins  3  SW4 SW5 SW6
symbols: 13 part types, 126 refdes, 0 power symbols
symbols: OK
== ERC
erc: 0 errors, 0 warnings (reports/erc.rpt)
== Sheet scripts reproduce kicad/*.kicad_sch
sheets: 4 sheet scripts, kicad/*.kicad_sch up to date
== Netlist comparison vs IPC
compare: parts 126/126 present, 0 missing, 0 extra; pins compared 247, wrong-net pins 0; IPC nets touched 66, complete 66 (+ 5 N/C / no-net pins)
compare: per sheet (drawn/total) 1:24/24 2:46/46 3:24/24 4:32/32
compare: OK
== Footprint library, map and fp-lib-table up to date
footprints: R_Axial_DIN0414_L11.9mm_D4.5mm_P19.05mm_Horizontal: fit on R45 unmirrored, largest pad move 0.635 mm (pad 2), limit 10.160 mm
footprints: C_Rect_L13.0mm_W6.0mm_P9.70mm: fit on C2 unmirrored, largest pad move 0.150 mm (pad 2), limit 5.000 mm
footprints: D_DO-41_SOD81_P10.16mm_Horizontal_AK: fit on D1 unmirrored, largest pad move 0.000 mm (pad A), limit 5.080 mm
footprints: D_DO-35_SOD27_P10.16mm_Horizontal_AK: fit on D2 unmirrored, largest pad move 0.000 mm (pad A), limit 5.080 mm
footprints: TO-92_Inline_P2.03mm: fit on Q8 unmirrored, largest pad move 0.508 mm (pad 3), limit 1.270 mm
footprints: CP_Radial_D5.0mm_P2.54mm_PM: fit on C8 unmirrored, largest pad move 0.020 mm (pad +), limit 1.250 mm
footprints: CP_Radial_D16.0mm_P7.50mm_21: fit on C1 unmirrored, largest pad move 0.000 mm (pad 1), limit 3.750 mm
gen_footprints: 126 parts, 17 footprints (13 project), up to date
== Footprints vs IPC pad geometry
check_footprints: pcbnew placement of 126 parts, worst pad offset 0.001 mm
check_footprints: note: U4: THT pad pattern fits only mirrored -> bottom side
check_footprints: note: U5: THT pad pattern fits only mirrored -> bottom side
check_footprints: 126/126 parts fitted, 247 pads, 17 footprints, worst residual 0.001 mm (limit 0.05)
check_footprints: OK
== Pin order vs unmoved KiCad base footprints
check                    base (unmoved)                                     unmirrored         mirrored  result
Q4                       TO-220-3_Vertical                               0.000 @    90    0.000 @   270  unmirrored 0.000
Q8 Q10 Q20 Q90           polarity: base pad 1 (marked) = pin '1' (expected '1')
Q8 Q10 Q20 Q90           TO-92_Inline_Wide                               0.508 @    90    0.508 @   270  unmirrored 0.508
Q1 Q2 Q3 Q5 Q6 Q7        polarity: base pad 1 (marked) = pin '1' (expected '1')
Q1 Q2 Q3 Q5 Q6 Q7        TO-92_Inline_Wide                               0.508 @   270    0.508 @    90  unmirrored 0.508
D2 D7 D8 D9 D10 D11 D12  polarity: base pad 1 (marked) = pin 'K' (expected 'K')
D2 D7 D8 D9 D10 D11 D12  D_DO-35_SOD27_P10.16mm_Horizontal               0.000 @     0    0.000 @   180  unmirrored 0.000
D1 D3 D4 D5 D6           polarity: base pad 1 (marked) = pin 'K' (expected 'K')
D1 D3 D4 D5 D6           D_DO-41_SOD81_P10.16mm_Horizontal               0.000 @    90    0.000 @   270  unmirrored 0.000
C8 C28                   polarity: base pad 1 (marked) = pin '+' (expected '+')
C8 C28                   CP_Radial_D5.0mm_P2.50mm                        0.020 @   180    0.020 @     0  unmirrored 0.020
C1 C36 C37               polarity: base pad 1 (marked) = pin '2' (expected '2')
C1 C36 C37               CP_Radial_D16.0mm_P7.50mm                       0.000 @   270    0.000 @    90  unmirrored 0.000
SERIES_MIX               Relay_DPDT_Omron_G5V-2                          0.000 @     0    7.620 @     0  unmirrored 0.000  (Omron ids (IPC_PIN_IDS) on the unmoved KiCad G5V-2)
SERIES_MIX pole 1        Relay_DPDT_Omron_G5V-2                          7.620 @     0    0.000 @     0  mirrored 0.000  (the Phase 2 Proteus-pole mapping fits only mirrored)
U4 U5                    Valve_Noval_P                                  17.630 @ 150.3    2.972 @     0  mirrored 2.972  (KiCad Noval_P is a smaller circle; only the mirrored one is near)
U4 U5 ideal noval        ideal n=9 PCD 21 mm                            19.318 @   144    0.007 @     0  mirrored 0.007  (ideal standard noval, PCD 21.00 mm)
U4 U5 sense              U4: pins 1 -> 9 run clockwise seen from the top (expected clockwise)
U4 U5 sense              U5: pins 1 -> 9 run clockwise seen from the top (expected clockwise)
SW4 SW5 SW6              SW4: distances 1-2 5.080, 1-3 5.120, 2-3 5.120 mm
SW4 SW5 SW6              SW5: distances 1-2 5.080, 1-3 5.120, 2-3 5.120 mm
SW4 SW5 SW6              SW6: distances 1-2 5.080, 1-3 5.120, 2-3 5.120 mm
noval footprint vs ideal Valve_Noval_Belton_PCD21.00mm                   0.006 @     0   19.318 @   216  unmirrored 0.006  (standard noval numbering in its own view)
noval footprint on IPC   Valve_Noval_Belton_PCD21.00mm                  19.314 @   144    0.001 @     0  mirrored 0.001  (fits only mirrored = bottom side)
bottom                   footprint_fit.csv and kicad/tube_pi_fxloop.kicad_pcb: U4 U5 bottom (B.Cu), the other 134 footprints top
check_pin_order: OK (15 checks as recorded)
== PCB rebuilt from schematic + gerbers, up to date
build_pcb: 126 footprints placed (0 excluded from board), 10 mounting holes, 71 nets, 4 outline segments
gerber_to_tracks: 512 tracks, 4 vias (IPC 4), 0 pour outlines on User.1-4; removed as recorded: 3 tracks (REMOVED_TRACKS), 0 vias (REMOVED_VIAS)
assign_nets: stage A (no pours): 81 groups, 0 shorts, 0 orphans, 0 opens
assign_nets: stage B (with pours): 81 groups, 0 shorts, 0 orphans, 0 opens
place_refdes: 68 kept, 67 moved, 1 moved, 0.8 mm text (sizes 1.0, 0.8 mm)
make_pcb: board rebuilt from scratch, byte-identical
== Board pads, holes, vias vs IPC (position, size, nets 1:1)
check_board: 136 footprints, 247 pads, worst pad offset 0.001 mm (limit 0.05), 66 IPC nets mapped 1:1, 10 mounting holes
check_board: 512 tracks, 4 vias, 0 zones
check_board: 516 track / via nets in the board file = their copper group's net (track_nets)
check_board: OK
== Board copper connectivity (KiCad geometry)
assign_nets: after zone fill: 81 groups, 0 shorts, 0 orphans, 0 opens, 0 items with a foreign net
assign_nets: OK (report reports/assign_nets.txt)
== DRC with schematic parity
drc: 102 violations, 0 shorts, 0 unconnected, 0 parity issues (reports/drc.json)
drc:     40 error    courtyards_overlap  accepted: KiCad courtyards vs the Proteus placement (40 pairs, parts exactly at the Proteus positions, all on the top side): the 100N rows C3/C5/C9 6.35 mm apart; the TO-92 rows (Q1/Q2, Q3/Q5, Q6/Q7) with each other and R11 R16 R18, Q20 / R270, SEND2W SEND3W; resistors / film caps / terminals packed closer than the KiCad courtyards (R19-R24, R66, RETURN1-3, C4 C7 with D9 R50, C30 with R24 R26, ...). The noval sockets U4 / U5 are on the bottom side since Phase 5 (user 2026-11-20): their courtyards (B.CrtYd) no longer meet the top-side parts
drc:      7 error    pth_inside_courtyard  accepted: Proteus placement: H3 / H4 in the U5 / U4 courtyard (the mounting holes around the sockets, Finding 17), C8's pads in U4's, V8_V9 pad 1 in U5's (a THT pad is on both sides, so the bottom-side socket courtyards still contain them), R24-1 and R26-1 inside the large C30 Solen box courtyard
drc:     28 warning  silk_overlap
drc:     27 warning  silk_over_copper
drc: warning counts as expected (DRC_EXPECTED_WARNINGS): 0 track_dangling, 0 via_dangling
drc: OK
== IPC-D-356 from the board vs Proteus (pads, vias, holes, nets)
ipc356_diff: Proteus 261 records, KiCad 261; matched 261 (247 pads incl. 5 N/C, 4 vias, 10 holes), worst position offset 0.002 mm (limit 0.05)
ipc356_diff: 66 Proteus nets mapped 1:1 onto KiCad nets, 0 mismatches
ipc356_diff: KiCad drill larger (footprint kept): 116x 0.762->0.8, 13x 1.016->1.1, 16x 1.016->1.199, 8x 1.143->1.199
ipc356_diff: KiCad drill smaller, accepted (DRILL_SMALLER): 8x 0.762->0.749, 8x 1.143->0.701, 2x 1.143->1.001
ipc356_diff: pads with another size in KiCad (info): C 22, D 24, Q 33, R 84, SERIES_MIX 8
ipc356_diff: 5 unconnected-(...) nets, one record each (nc_joined)
ipc356_diff: OK
== Gerber round trip vs Proteus (copper XOR, coverage, drills, 2010 Excellon)
roundtrip: F.Cu   XOR   94.31 mm^2, beyond 0.05 mm: only Proteus  53.53, only KiCad   6.41 mm^2; clusters >= 0.01 mm^2: 218 pad shape; draws/flashes off the other copper: 0 Proteus, 0 KiCad
roundtrip: B.Cu   XOR   97.05 mm^2, beyond 0.05 mm: only Proteus  54.15, only KiCad   7.29 mm^2; clusters >= 0.01 mm^2: 213 pad shape; draws/flashes off the other copper: 0 Proteus, 0 KiCad
roundtrip: Proteus objects not compared (recorded deviations, all layers): 3 Conductor draws (REMOVED_TRACKS)
roundtrip: drills 0 mismatches; KiCad drill smaller, accepted (DRILL_SMALLER): 8x 0.762->0.75, 8x 1.143->0.7, 2x 1.143->1.0; report reports/roundtrip/roundtrip.txt, overlays reports/roundtrip/*.png
roundtrip: counts (roundtrip_counts): KiCad track draws / flashes per layer F.Cu 275 / 261, B.Cu 237 / 261: tracks as gerber_to_tracks builds them, flashes = Proteus
roundtrip: OK

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
8. **U4's Proteus device is `12AX7` with the value `12AT7`** (layout record: value 12AT7, device
   12AX7): the board is built for a 12AT7 (PDF, value), the Proteus simulation model would be a
   12AX7. Same noval pinout, no effect on the nets; the KiCad part uses the `12AX7` symbol with
   the value 12AT7 (reproduced).
9. **C1, C36, C37 (`22µF 450V`, package `ELEC D16 R7.5`) have pin ids 1 / 2 with `+` = 2**, unlike
   the other electrolytics (C8, C28: pin ids `+` / `-`). Polarity in the nets is right (pin 2 on
   H / F / G). Phase 2: the footprint pad numbers are 1 / 2 with pad 2 = `+`.
10. **Relay G5V-2(HI) and SW-SPDT use Proteus' own pin numbers** (relay 1-8 in package order with
   AC = normally open, not the Omron 1/4/6/8/9/11/13/16; switch NO=1 NC=2 COM=3). Numbering only;
   Phase 2 checks the pad positions.

11. **Phase 1 transcription: every PDF connection agrees with the IPC netlist** (247 pins, 0
   wrong-net pins, no net alias needed). The PDF values equal the part map. No pin is drawn
   unconnected except U4-9, U5-9 and relay pole 2 (pins 6-8).
12. **The FX switch drivers are PNP transistors with the emitter on ground** (sheet 2): Q8, Q10, Q20,
   Q90 (2N3906) have the emitter on PWR-GND and the collector on the gate nets (pull-ups R100 / R110 /
   R270 100k to the VREF terminal, 10k base resistors from the terminals A / C' / D'). That only
   works with **VREF and the control inputs negative** against PWR-GND (presumably the power amp board's
   negative VREF, not verified here; it would also give the J112 gates their pinch-off voltage): a control input
   pulled negative turns its driver on and lifts the gate net to ground (JFET on, send shunted).
   Q8 (input FX') lifts all three gate nets through D10-D12. Consistent as drawn; reproduced.
   Worth knowing for the redesign and for simulation (the polarity is not visible from this board
   alone).
13. **SW4-SW6 short the 1M series resistor of a return input** (sheet 4): common on the R19/R20 node,
   NC contact on the RETURN terminal (1M bypassed in the rest position), NO contact on NOLLA (node
   shorted to NOLLA, i.e. the 100k bypassed and the 1M left in series). Reproduced as drawn.
14. **A stray junction dot** on page 2's ground row (no wire attached), and the page 1 hand note
   (Finding 5): drawing leftovers only.

15. **The Proteus relay package G5V-2(HI) is the mirror image of the Omron G5V-2 seen from the top**
   (Phase 2 pin-order check): with the Omron mapping of the symbol (AC1 = 8, COM1 = 4, NC1 = 6, coil 1 / 16,
   pole 2 = 9 / 13 / 11) the KiCad G5V-2 footprint fits only mirrored (0.000 mm; unmirrored 7.62 mm), most
   likely the datasheet's bottom view drawn as the top. A G5V-2 inserted from the top lands with its
   **pole 2 on the Proteus pole-1 pads** and its coil ends swapped: Proteus pad 1 (AC1, SEND) gets Omron 9
   (NO2), 2 (COM1, R26) gets 13 (COM2), 3 (NC1, PWR-GND) gets 11 (NC2), 4 / 5 (coil) get 16 / 1, and the N/C
   pads 6-8 get pole 1 (4 / 6 / 8). **Electrically the same** (the poles are identical, the G5V-2 coil is
   not polarised and D1 sits across it either way), so the board works; only the pole and pin names
   differ. The footprint uses the physical mapping (KiCad pin-1 mark at Proteus pad 5); the symbol keeps
   Proteus' names. Worth correcting in the redesign's symbol / footprint pair.
   **Fixed 2026-11-20 (user decision, "Design fixes 2026-11-20"): symbol and footprint use the Omron pin
   numbers** (KiCad Relay:G5V-2 / Relay_THT:Relay_DPDT_Omron_G5V-2 unchanged; the IPC pin ids of
   SERIES_MIX renamed, `IPC_PIN_IDS`): Proteus 1-8 = Omron 9 13 11 16 1 4 6 8; the schematic now shows
   that pole 2 is the used pole. Every pin on its net, copper unchanged.
16. **The noval sockets U4 / U5 are numbered mirrored** (as the pilot's octal, power amp Finding 10): pins
   1 → 9 run clockwise seen from the top (1 at −144°, 2 at 180°, … 9 at −72°, gap at −108°); the noval
   standard runs clockwise seen from the pin side. Only the mirrored ideal noval fits (0.007 mm vs 19.3 mm).
   The numbering is right for a socket **mounted on the solder (bottom) side** (its pin side then faces
   the board, seen through it from the top), or a chassis socket wired by position. On the power amp
   the user confirmed (2026-11-20) that the octal sockets are on the solder side; the same is likely
   here, but not confirmed for U4 / U5. A PCB socket mounted tube-up on the top side would
   put tube pin k on Proteus pad 10 − k (gap aligned): heater 4 / 5 on pads 6 / 5, anode 1 on the N/C pad 9,
   i.e. wrong. **Confirm the mounting on the real amplifier** before the redesign reuses the footprint.
   Copper reproduced as is. **User 2026-11-20: U4 / U5 are on the bottom (solder) side** (Decisions);
   done in Phase 5: the footprint is built mirrored and placed on B, standard noval numbering in its own
   view.
17. **The "9-PIN BELTON NOVAL" pattern has a 21.0 mm pitch circle** (4.318 mm pads, 1.727 mm drill, no
   centre hole), not the 11.9 mm-class circle of a PCB noval socket, and each socket has three plated
   3.0 mm holes around it at about 17-18 mm from its centre (U4: H at (60, -14), (29, -18.5), (51, -41);
   U5 likewise, IPC frame): the socket is probably not a standard PCB-mount noval but one held by its own
   screws (on the solder side, Finding 16). Footprint built from the IPC pads; the holes stay board-only mounting
   holes (Phase 3). Relevant for the redesign.
18. **Drill sizes of the 2010 library are larger than the KiCad library's for the relay and small film
   caps** (SERIES_MIX 1.143 vs KiCad 0.7 mm, C2 1.143 vs 1.0, MMK caps 0.762 vs 0.75): the 2010 board was
   drilled with the larger holes. **User 2026-11-20: the KiCad drills stay** (`DRILL_SMALLER`, Decisions).

19. **Three dangling copper stubs in the Proteus layout** (Phase 3 DRC `track_dangling` warnings; KiCad
   frame, y down, IPC y = −y): a 1.27 mm B.Cu SWLOOP segment from D8-K to (84.455, 43.815), lying on top of
   the D8-K → D9-K track (redundant); a 0.635 mm F.Cu Net-(Q90-B) stub from the junction at (-20.003, 43.18)
   to (-19.368, 43.18); a 1.905 mm F.Cu H stub from R67-2 to (-58.42, 67.945). The free ends touch nothing
   (checked against every pad and track end). No net effect; leftovers of the 2010 routing. Reproduced
   (`REMOVED_TRACKS` could drop them in Phase 5 if wanted). **User 2026-11-20: kept as drawn.**
   **Fixed 2026-11-20 (user decision after the conversion, reverses the Phase 5 one): removed** with
   `REMOVED_TRACKS` ("Design fixes 2026-11-20"); DRC track_dangling 3 -> 0.
20. **The Proteus clearance is tight at the TO-92 rows**: 0.421 mm between a TO-92 pad and the 45° tracks
   that leave the neighbouring pad (Q1, Q3, Q6, Q20), the smallest gap on the board (otherwise ≥ 0.508).
   Fine for the 2010 board; relevant for the redesign's rules.

21. **C8 / C28: value `22u`, Proteus device `HITEMP10U50V`** (Phase 4; like Finding 8): the schematic
   value is 22 µF, the library device a 10 µF / 50 V part (package ELEC-RAD10, 2.54 mm pitch, 5 mm can).
   The value is reproduced; which capacitor is fitted is for the BOM of the redesign (C28 sits on the
   R47 / R48 / R49 divider node, C8 on the U4 cathode: low voltages).
22. **The heaters run in series across pins 4 / 5** (Phase 4, PDF pages 1 and 3): U4 and U5 have pin 4
   on PWRH4 (terminals `-6`, `PRE-H4`) and pin 5 on PWRH5 (`+6`, `PRE-H5`); pin 9 (the heater centre
   tap) is the N/C pad. So each valve needs about 12.6 V between PWRH4 and PWRH5 (the terminal names
   suggest −6 / +6 V), and the relay coil with D1 hangs between PWRH4 and SWLOOP. Consistent as drawn;
   worth knowing for the redesign (a 6.3 V parallel heater connection would need pin 9).

## p2k candidates

(Shared-tool limitations met on this board, with the board-local workaround used. Status after the
shared-tool migration: table in "Shared-tool migration 2026-11-20".)

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
5. **`p2k.pdsprj.lyt_parts` (`_strings`) drops one-character strings and Latin-1 bytes.** The
   terminal refdes `A` is a one-character run, so its layout record has no refdes token, the
   backward search finds the previous part (`-6`) and the function raises "two layout records for
   -6". The µ in `22µF 450V` also splits the C1/C36/C37 records. Workaround: a board-local copy
   `lyt_parts()` in `tools/make_part_map.py` with a `_strings()` that keeps runs of one character
   and decodes 0xA0-0xFF as Latin-1 (all 126 records found; net tokens carry a trailing 0xFF
   padding that is stripped). The shared tool would need: `_strings(min_len=1)` plus Latin-1 in
   `lyt_parts` (and `dsn_values`' `pstr`, pilot candidate 1).
6. **Pilot candidate 4 confirmed: `dsn_pinouts` does not read the device `$PINSHORT` /
   `$PINDEFAULT` records**, and they need care: the pin name is often a single character (B, C,
   E, D, G, S, A, K), so a `strings -n 2` scan loses it; the number after the name is the
   **symbol** pin number, which a `*PINOUT` table of the package overrides (12AX7: `$PINDEFAULT`
   A2=1 A1=6 H1=5 ..., package A1=1 A2=6 H1=4 ...). Read by hand here (bytes after each
   `$PIN*` marker). The shared tool would need: a `$PIN*` reader grouped by the following
   `{*DEVICE}` block, with the device name (the string before the block) and the package table
   applied when there is one.
7. **`sch_builder.Sheet.place` has no mirror and `place_mirrored()` keeps the default text
   positions** (pilot candidate 6): the mirrored Q90 of the smoke test had its refdes / value over
   the body; pass `ref_at` / `value_at`. The shared tool would need: mirror-aware field placement.
8. **No KiCad THT symbols for J112 and IRF820**: generic `Device:Q_NJFET_DSG` and
   `Transistor_FET:IRF740` (same TO-220 G D S) renamed. Not a tool limitation; noted for the
   symbol list of later boards (the preamp has J112s too?).

9. **`compare_netlists` crashes on refdes pairs like `SEND` / `SEND1`** (found when sheet 4 was
   drawn): `natkey()` returns mixed str / int lists and `pinkey()` appends `"-"` and the pin, so
   `['SEND', '-', 1]` against `['SEND', 1, '', '-', 1]` compares `'-'` with `1` →
   `TypeError: '<' not supported between instances of 'int' and 'str'` in `sorted(common, key=pinkey)`.
   Any board with a number-less refdes that is the prefix of a numbered one hits it. Workaround:
   `tools/compare.py` replaces `natkey` / `pinkey` with keys of `(kind, int, str)` tuples and calls
   the tool's `main()` (same arguments and output); check_all.sh uses it. The shared tool would
   need: the same type-safe key.
10. **`place_mirrored()` covers rotation 0 only** (and is itself a board-local helper, candidate 7):
   Q4 needed rotation 90 + mirror → board-local `place_rot90_mirrored()`. The shared
   `Sheet.place` would need `mirror=` with correct pin points for every rotation, and mirror-aware
   field placement (multi-pin symbols at rotation 90 / 270 also keep the library field offsets, so
   SW4-SW6 and the rotated relay needed `ref_at` / `value_at`).
11. `sch_builder.place` puts the texts of a horizontal two-pin part with `text="above"` 3.81 / 2.03 mm
   above the centre: fine for resistors, the value overlaps the plates of a horizontal capacitor.
   Workaround: `_common.ph()` passes `ref_at` / `value_at` for capacitors. Cosmetic.
12. A sheet drawn before the sheet that drives its nets shows interim ERC errors (`pin_not_driven`
   on the J112 gates until the drivers of sheet 2 exist). Not a tool problem; noted so the
   per-sheet target "0 ERC errors" is read as "none that the missing sheets do not explain". An
   order drivers-first (2 before 4) avoids it.

13. Pilot candidates 12 (`footprints.run` does not write `kicad/fp-lib-table`; board-local
   `fp_lib_table()` in `tools/gen_footprints.py`) and 13 (no shared pin-order check; board-local
   `tools/check_pin_order.py`, adapted) apply here too. New for the pin-order tool: a **free-rotation fit**
   (`fpgeom._solve` snaps the angle to 45°, so a 9-pin noval with 36° steps cannot be tested with an ideal
   pattern in an arbitrary orientation; `free_fit()` in check_pin_order.py), the **sense of a circular
   pin sequence** (`turn_direction()`), and a check that the renumbering tested equals the one in the
   footprint spec.
14. **`footprints.derive()` accepts any base fit.** It fits the renumbered base onto the IPC pads, takes the
   best mirror state and moves every pad onto its IPC position **without a residual limit**, so a wrong
   renumbering (two pads swapped, + / - reversed) produces a footprint that check_footprints passes
   (negative tests 6 and 7: only check_pin_order caught them). The pitch corrections it is meant for move
   pads by < 1 mm (here at most 1.27 mm: DIN0414 P20.32 → P19.05). The shared tool would need: a
   `max_move` per spec (default e.g. half the smallest pad pitch) and an error when a pad moves farther,
   and a report of the mirror state chosen (a mirrored-only base fit is a pin-order finding).
15. `check_footprints` does not resolve a Footprint field against the project fp-lib-table (it reads the
   map and the library files), so a missing `kicad/fp-lib-table` passes it; ERC reports it only as a
   `footprint_link_issues` **warning**. Board-local: `tools/erc.sh` fails on those warnings.

16. **No pad-shape override in `footprints.derive()`**: `ipc_sizes=True` takes the Proteus pad size and drill
   but keeps the base pad's shape (the square pad 1 of KiCad's TO-92 becomes a 1.524 mm square, still
   wider than the round Proteus pad). This board's TO-92 conflict (Phase 3) needs a shape change: the
   shared tool would need a `pad_shape` (`{pin: "circle"}` or `"ipc"` = the IPC shape) per spec. Until
   then a board-local edit of the derived footprint in `tools/gen_footprints.py`: done in the Phase 3
   finish (a wrapper around `footprints.derive` makes the TO-92 pad 1 a circle and adds a pin-1 dot on
   silk and fab, since the KiCad TO-92 outline is symmetric). Shared tool: a `pad_shape` key plus a
   pin-1 marker option for footprints whose only pin-1 mark is the pad shape.
17. **`p2k drc` accepts by violation type only.** A single pending item (9 clearance errors at known
   pads) cannot be accepted without accepting every clearance error. Board-local:
   `tools/drc_pending.py` (passes only when exactly those 9 TO-92 pad-1 clearance errors are the
   unaccepted errors; prints PENDING USER DECISION; `check_all.sh` counts them as the pilot's does). The
   shared tool would need item-level acceptance (`{type: {item pattern: reason}}`) or an expected
   count per type. (`drc_pending.py` was removed in the Phase 3 finish once the pad was decided; the
   limitation stays.)
18. **`measure_gaps.py` measures the Proteus geometry only** (the pilot's / tube_psu's copy). The gaps with
   the KiCad pads were measured with kicad-cli DRC at a raised clearance on a scratch copy (0.6 and 1.5 mm,
   `build/tmp/padexp`). A KiCad-geometry mode (assign_nets' `--check` items) would make that a tool step.
   Pilot candidate 12 / place_refdes: make_pcb.sh leaves out `place_refdes` here (reference positions are
   Phase 5).

19. **`compare_netlists` treats every pin of an `unconnected-(…)` net as a singleton** (`k_group`), so
   N/C pins wired to each other (one KiCad net `unconnected-(X-PadN)` with two or more nodes) pass as
   separate N/C pins; ERC gives only the warning `no_connect_connected` (Phase 4 negative test). Board-
   local: `tools/compare.py` fails on such a net with more than one node, `tools/erc.sh` fails on the
   warning. The shared tool would need: a pin is unconnected only if its net has one node (and the
   playbook: erc.sh fails on `no_connect_connected`, pilot candidate 19).
20. **`DRILL_SMALLER` accepts by diameter pair, not by pad or count** (`ipc356_diff`, `gerber_roundtrip`):
   any other pad with a listed pair is accepted, and a decided hole that is no longer smaller is not
   noticed. Board-local: `tools/check_drill_smaller.py` (exact pad set per pair, own IPC parser). The
   shared tool would need: `{(proteus, kicad): (reason, count)}` or a refdes list per pair, checked
   exactly.
21. **Pad sizes are outside both Phase 4 checks** (pilot candidate 21): a changed KiCad pad is a "pad
   shape" cluster in the round trip and an info line in `ipc356_diff`; a deleted mounting hole's ring
   is "pad shape" too (the drill catches it). Fine while the board is generated (byte compare); after
   the first manual edit a per-footprint expected pad-shape area (or pad sizes vs the library) would be
   needed.
22. `gerber_roundtrip.parse_excellon` is metric-only and ignores the `INCH` header (pilot candidate):
   board-local `tools/excellon_metric.py` (a copy of the pilot's; the two differ only in the source file
   name – a shared `--excellon-inch` reader would remove both). `compare_netlists` has `--schematic` /
   `--netlist` but ignores `P2K_SCHEMATIC` (the PCB tools honour `P2K_PCB`): a scratch-copy run needs the
   argument.

23. **`footprints.from_ipc` mirrors only bottom SMD parts** (pilot candidate 24): a THT part mounted on
   the bottom side (here the noval sockets U4 / U5, Phase 5) has IPC side `both`, so the shared tool builds
   it unmirrored. Board-local: `bottom=True` spec key + a `build_library` wrapper in
   `tools/gen_footprints.py` (the pilot's code); `tools/check_pin_order.py` `bottom_side_noval()` checks
   the result. The shared tool would need a `bottom` spec key (or a side override per refdes). Also as
   on the pilot (candidate 25): `p2k drc` does not enforce warning counts; only the byte compare sees a
   new silk warning while the board is generated.
24. **No pin id renaming for the IPC file** (design fixes 2026-11-20): the relay SERIES_MIX should carry the
   Omron pin numbers while the Proteus IPC numbers it 1-8. Board-local: `IPC_PIN_IDS` in `p2k_config.py` and
   `tools/ipc356.py` (wraps `ipc356.parse`, renames after parsing, checks completeness / uniqueness), so
   `reference/` carries the KiCad ids. The shared tool would need the key in `ipc356` itself (with the
   Proteus pin kept in an extra field such as `pin_proteus`, which `FIELDS` does not allow today).
25. **`make_pcb.sh --check` hides a failing step** (the pilot's script, copied to every board repo): `run` is
   called inside `run >log || {...}`, where `set -e` does not apply, so after a failing gerber_to_tracks the
   later steps run on and the filtered output never shows the ERROR (the step still fails, as "not up to
   date"). Fixed here by chaining the steps with `&&`; the other board repos have the same `run()`. Also:
   `p2k drc` does not enforce warnings, so a dangling track coming back is only a count; board-local
   `tools/check_no_dangling.py`.

## Decisions

- Sheet names (no title blocks in the PDF): FX loop driver / PI supply and FX switching /
  Phase inverter / FX send and return, chosen by the agent from the content; the user can
  rename them (only `p2k_config.py`, before `make_skeleton`).
- KiCad refdes for the names with signs / quote / slash: table above (agent's choice, same
  convention as tube_psu and the power amp pilot: + → P / _, - → N / _, ' → _PRIME, / → _).
  The terminal `A` keeps its name.
- Phase 1 preparation (agent's choices, no user decision needed): all 39 terminals use one
  symbol `PIN` (Connector:TestPoint, as tube_psu / the pilot); U4/U5 keep KiCad's three ECC83
  units (heater separate, pin 9 flagged; see the valve decision above); valve pins passive;
  J112 / IRF820 from generic / same-pinout KiCad symbols; PWR-GND as a global label (no power
  symbols, IPC has no =POWER net); named nets in IPC spelling (`SEND`, `NOLLA` upper case).
- Phase 1 transcription (agent's choices, no user decision needed): valve triodes side by side with
  unit 2 mirrored, heater unit beside / below the tube; relay as one symbol rotated 180°; Q4 rotated
  and mirrored as the PDF; `SEND` drawn as wires plus a global label where the PDF has one; A3 sheets
  with the PDF geometry on the 1.27 mm grid; renders committed in `reports/render/`.
- **Open for the user: nothing blocking.** (Sheet names and the KiCad refdes of the signed names can
  still be changed in `p2k_config.py` / by re-running the generators.)
- Phase 2 (agent's choices, no user decision needed): one rule per Proteus package; the pilot's specs and
  names for the shared 2010 packages; 100N XICON, SOLEN 1U, the noval socket, SW-SPDT and the terminals
  built from the IPC pads (Proteus pads) with the Proteus silk / assembly outline as body; 47N XICON and
  MMK J04 from unchanged KiCad boxes that match the Proteus silk; the relay footprint renumbered by
  physical position (Finding 15), the symbol unchanged; `tools/erc.sh` fails on footprint link issues.
- **User decisions 2026-11-20** (given through the coordinating session):
  1. **The noval sockets U4 / U5 are mounted on the bottom (solder) side** (Findings 16, 17). As on the
     power amp, moving the socket footprints to B with the standard noval numbering is **Phase 5** work
     (not done in Phase 3; the copper is identical either way).
  2. **Drills: the KiCad drills stay everywhere** (and the KiCad pads with them): relay SERIES_MIX 0.70
     vs Proteus 1.143 mm (all 8 pads, KiCad 1.4 mm pads kept), C2 1.0 vs 1.143, C4 / C6 / C7 / C32 0.75
     vs 0.762. Recorded as `DRILL_SMALLER` in `p2k_config.py` (reason "user decision 2026-11-20") so
     that Phase 4's `ipc356_diff` / `gerber_roundtrip` accept exactly these pairs.
  3. **Pad sizes**: `FOOTPRINT_PAD_SIZES = "kicad"` stays; only if the Phase 3 DRC forces a change, stop
     and ask (unchanged rule).
- Phase 3 (agent's choices, no user decision needed): design rules from the Proteus copper (clearance 0.4
  mm from the measured 0.421, edge 1.0, min drill 0.5 for the 0.508 vias, netclass via = the Proteus via);
  thickness 1.6 mm (as the pilot); `make_pcb.sh` without `place_refdes` (Phase 5); `DRC_ACCEPTED` for
  courtyards_overlap and pth_inside_courtyard (Proteus placement).
- ~~OPEN FOR THE USER (blocked Phase 3): TO-92 pad 1.~~ Decided, see the user decision below. The KiCad TO-92 footprint's square pad 1 is 0.122
  mm from Proteus tracks on Q1, Q3, Q6, Q20 (9 DRC clearance errors; Proteus gap 0.421 with its round
  pads). Options (Phase 3 "KiCad pad sizes"): **(a)** round pad 1 at the KiCad size 1.5 mm (gap 0.433;
  agent's recommendation), **(b)** the Proteus pads 1.524 round / drill 0.762 (gap 0.421), **(c)** keep the
  square pad and accept 0.12 mm (not recommended). (a) and (b) change the footprint shared by all ten TO-92
  parts (Q1-Q3, Q5-Q7, Q8, Q10, Q20, Q90); the pilot uses the same footprint without a conflict.
- **User decision 2026-11-20 (given through the coordinating session): TO-92 pad 1 = option (a), a ROUND
  pad at the KiCad size 1.5 mm on all TO-92 parts** (Q1-Q3, Q5-Q7, Q8, Q10, Q20, Q90), instead of KiCad's
  square pin-1 pad; drill 0.8 (KiCad) unchanged. Applied board-locally in `tools/gen_footprints.py`
  (Phase 3 "KiCad pad sizes"); DRC 0 clearance errors, smallest TO-92 gap 0.432 mm.
- Phase 3 finish (agent's choice, no user decision needed): pin 1 of the TO-92 parts is marked by a
  filled dot on F.SilkS and F.Fab beside pad 1 on the flat side (the KiCad TO-92 outline is symmetric,
  the square pad was the only mark). The user can drop or move it (`PIN1_DOT` in `tools/gen_footprints.py`).
- Phase 4 (agent's choices, no user decision needed): the 2010 Excellon file converted by a board-local
  copy of the pilot's `tools/excellon_metric.py` and set as `DRILL_EXCELLON`; `reports/roundtrip/`
  committed (reproducible: two runs byte-identical); three board-local hardenings of the checks, none of
  which changes the conversion: `tools/check_drill_smaller.py` (the 18 decided holes by pad),
  `tools/compare.py` (no `unconnected-(…)` net with more than one pin), `tools/erc.sh` (fails on
  `no_connect_connected`). U4 / U5 were not moved (Phase 5). **Open for the user: nothing blocking**;
  Phase 5 needs the user's choices (next_prompt.md).
- **User decisions for Phase 5, 2026-11-20** (given through the coordinating session, recorded before
  the Phase 5 work):
  1. **U4 / U5 on the bottom (solder) side with the standard noval numbering** (already decided above):
     the footprint is **built mirrored**, as the power amp pilot did for its octal sockets (a plain pcbnew
     `Flip` mirrors the pads and fails the checks, Phase 4 negative test).
  2. **Yes, `p2k place_refdes` as a `make_pcb.sh` step** (as the pilot).
  3. **The three dangling Proteus copper stubs (Finding 19) stay as drawn**; no `REMOVED_TRACKS`.
  4. **The TO-92 pin-1 dot (`PIN1_DOT`) stays** as it is.
  5. **Kept**: footprint body graphics (KiCad library graphics), KiCad pad sizes, the sheet names, the
     KiCad refdes of the signed names, board thickness 1.6 mm.
  6. **The board stays generated** (`tools/make_pcb.sh`); stopping generation is the user's call at the
     first hand edit of the layout.
- Phase 5 (agent's choices, no user decision needed): the pilot's `bottom` spec key and `build_library`
  wrapper copied unchanged; `check_pin_order` checks the bottom side with free-rotation fits (noval 36°
  steps); `place_refdes` with its defaults (no `REFDES_PLACEMENT`); `DRC_ACCEPTED` reasons and counts
  updated (40 courtyards_overlap, 7 pth_inside_courtyard). **Open for the user: nothing blocking.** The
  conversion is complete; the first hand edit of the board (which ends generation) is the user's call.
- **User decisions 2026-11-20, after the conversion** (given through the coordinating session; recorded
  before the work, done in "Design fixes 2026-11-20"):
  1. **Fix the design findings in the KiCad design, but leave the component values as they are**
     (Findings 5, 8, 21 unchanged: R47 33k, U4 value 12AT7 on the 12AX7 symbol, C8 / C28 22u). The
     boards will be redesigned; the aim is a clean starting point.
  2. **Finding 15: relabel the relay SERIES_MIX symbol / footprint pin names to Omron's** (electrically
     identical, no copper change). Every pin stays on its net; compare / check_board / ipc356_diff must
     still pass.
  3. **Finding 19: REMOVE the three dangling Proteus stubs** (SWLOOP, Net-(Q90-B), H at R67-2) with the
     p2k key `REMOVED_TRACKS`. **This reverses Phase 5 decision 3.** The checks accept recorded removals.
  4. **Generation stops later** (after the shared-tool migration); the board stays generated for now.
- Design fixes 2026-11-20 (agent's choices, no user decision needed): the relay renaming is done on the
  IPC side (`IPC_PIN_IDS`, `tools/ipc356.py`) so that symbol and footprint are KiCad's unchanged; the
  sheet draws the used pole as Omron pole 2; findings other than 15 / 19 are left (table in "Design
  fixes 2026-11-20"); new board-local `tools/check_no_dangling.py`; `make_pcb.sh` steps chained with `&&`.
  **Open for the user: nothing blocking** (which further findings, if any, to change is redesign work).
