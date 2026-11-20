# Next prompt

Ready-to-paste prompt for the next agent session. Replaced at the end of every session.

```
Convert the Proteus board in /home/jari/dev/tube_pi_fxloop_kicad to KiCad 10: Phase 1 preparation
(part map, symbols, skeleton, checks); no sheet transcription yet.

Read, in this order: PLAN.md, STATUS.md (Phase 0 notes, findings, p2k candidates, decisions),
tools/p2k/CONVERSION_PLAYBOOK.md (section 3 "Phase 1" and section 5), tools/p2k/README.md.
Run tools/check_all.sh first and compare with STATUS.md "Last check output".
Render the PDF: pdftoppm -r 200 -png source/schematic_pdf/pi_fx_loop.PDF build/tmp/pdf/hi

The power amp pilot ~/dev/tube_power_amp_kicad (same 2010 Proteus 7 export, Phase 1 done) has the
reusable pieces; READ ONLY, copy and adapt into this repo, never change it:
- tools/make_part_map.py -> lib/part_map.csv (dsn_values / lyt_parts with the FULL refdes set,
  PAGE_OVERRIDES, SYMBOL_BY_DEVICE, LATIN1_PARTS for values with a Latin-1 'µ': here C1, C36,
  C37 "22µF 450V"; OFF_BOARD if any part of the PDF has no pads - Phase 0 found none);
- tools/gen_symbols.py -> lib/tube_pi_fxloop.kicad_sym (KiCad std symbols renumbered to the IPC
  pin ids; valve pins set to passive: pilot candidate 9);
- tools/erc.sh, tools/sheets/_common.py (term() for terminals with the part-map symbol/value,
  place_mirrored() for mirrored transistors), and its STATUS.md "Transcription rules" as the model
  for this board's rules;
- its STATUS.md "p2k candidates" (pdsprj Latin-1, dsn_pinouts misses $PINSHORT records: read the
  Proteus device pinouts from ROOT.DSN by hand; sheetkit.terminal; multi-unit valve symbols).
The finished reference ~/dev/tube_psu_kicad (read only) has the same tools.

This board: 126 parts on 4 pages (24 / 46 / 24 / 32): R 42, C 16 (incl. electrolytics C8, C28,
C1, C36, C37), D 12 (1N4148, 1N4001, zeners), Q4 IRF820, Q8/Q10/Q20/Q90 2N3906, Q1-Q3/Q5-Q7
J112, U4 12AT7 + U5 12AX7 (9-pin, pin 9 N/C), SW4-SW6 SW-SPDT, relay SERIES_MIX (G5V-2(HI),
pins 6-8 N/C), 39 terminals (KiCad refdes per p2k_config.py KICAD_REFDES).
Do: part map; Proteus pinouts of IRF820, 2N3906, J112, G5V-2, SW-SPDT, the noval tubes checked
against the KiCad symbols and the IPC nets (report differences as findings); decide the valve
multi-unit / heater handling up front (pilot candidate 8); gen_symbols; check_symbols;
p2k make_skeleton (sheet names from p2k_config.py SHEETS); erc.sh; check_all.sh with part map,
symbols, check_symbols, ERC and compare_netlists --allow-missing; a smoke test (a few parts, a
terminal, a global label, an N/C pin) with negative tests, then remove it; transcription rules in
STATUS.md (named nets in IPC spelling: send/nolla -> SEND/NOLLA; terminals A, C', D' are not on
the nets A, C', D'; cross-page nets as global labels; grid 1.27 mm; suggested sheet order).

Rules (PLAN.md section 5): don't change tools/p2k or its pin (board-local workarounds, noted in
STATUS.md "p2k candidates"); don't touch other repos; report design findings, don't fix them;
temporary files in build/tmp; never run the KiCad AppImage with --version (use tools/p2k/bin/kipy
and tools/p2k/bin/kicad-cli). At the end: STATUS.md updated (result, check output, findings),
next_prompt.md replaced with the transcription prompt, commit and push (git push origin main).
```
