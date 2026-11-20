# Status: Phase inverter + FX loop (`poweri`)

Plan: [PLAN.md](PLAN.md). Playbook: `tools/p2k/CONVERSION_PLAYBOOK.md`.

| Phase | State |
|---|---|
| 0 Skeleton and inventory | **done** 2026-11-20 (Opus 5.5) |
| 1 Schematic | **done** 2026-11-20 (preparation Opus 5.5, transcription Fable 5.2) |
| 2 Footprints | not started; next (next_prompt.md) |
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

## Last check output

`tools/check_all.sh` (2026-11-20, end of Phase 1):

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
== Part map up to date
make_part_map: lib/part_map.csv up to date, 126 parts; per sheet 1:24 2:46 3:24 4:32
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
sheets: 4 scripts reproduce kicad/0?_*.kicad_sch
== Netlist comparison vs IPC
compare: parts 126/126 present, 0 missing, 0 extra; pins compared 247, wrong-net pins 0; IPC nets touched 71, complete 71
compare: per sheet (drawn/total) 1:24/24 2:46/46 3:24/24 4:32/32
compare: OK
== No symbol pin of type no_connect

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
