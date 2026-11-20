# Next prompt

Ready-to-paste prompt for the next agent session (model: Fable). Replaced at the end of every session.

```
Convert the Proteus board in /home/jari/dev/tube_pi_fxloop_kicad to KiCad 10: Phase 1 transcription
(draw the 4 schematic sheets). The preparation is done: part map, symbols, skeleton, checks.

Read, in this order: PLAN.md, STATUS.md (especially "Phase 1 preparation" with the pinout table,
the valve unit decision and the "Transcription rules"; Findings; p2k candidates),
tools/p2k/CONVERSION_PLAYBOOK.md (section 3 "Phase 1" and section 5), tools/p2k/README.md.
Run tools/check_all.sh first and compare with STATUS.md "Last check output".
Render the PDF: pdftoppm -r 200 -png source/schematic_pdf/pi_fx_loop.PDF build/tmp/pdf/hi

Model for the sheet scripts: the power amp pilot ~/dev/tube_power_amp_kicad (READ ONLY; its
tools/sheets/sheet0N.py and its STATUS.md "Phase 1 transcription"). Helpers here:
tools/sheets/_common.py (term() for terminals, P() for PDF render coordinates, place_mirrored()
for mirrored transistors - pass ref_at/value_at, noval() for the 3 units of U4/U5 with the pin 9
no-connect flag) plus p2k.sheetkit.

Do: one script per sheet, tools/sheets/sheetNN.py (NN = PDF page), each rebuilding its
kicad/NN_*.kicad_sch from scratch (two runs byte-identical), in the suggested order
3 Phase inverter -> 1 FX loop driver -> 4 FX send and return -> 2 PI supply and FX switching.
Follow the transcription rules exactly: part-map symbols/values/refdes; named nets in IPC
spelling as global labels (PWR-GND, F, G, H, PWRH4, PWRH5, SEND, NOLLA, SWLOOP, A, C', D') and
HYPPY2 as a local label; the PDF's "send"/"nolla" are SEND/NOLLA; NO label on the terminals A, C',
D' (they are not on the nets A, C', D'); no-connect flags on U4-9, U5-9, SERIES_MIX 6-8; all three
valve units placed; grid 1.27 mm. After each sheet: tools/p2k/bin/p2k compare_netlists
--allow-missing --sheet N, tools/erc.sh, render (tools/p2k/bin/p2k render_sheet kicad/NN_*.kicad_sch)
and compare with build/tmp/pdf/hi-N.png; target 0 missing on that sheet, 0 compare errors,
0 ERC errors (explain warnings). After the last sheet drop --allow-missing in tools/check_all.sh;
Phase 1 is done when all 126 parts are present, 0 wrong-net pins, every IPC net complete, ERC 0
errors. Add one negative test (e.g. a label on a terminal) and record it.

Rules (PLAN.md section 5): don't change tools/p2k or its pin (board-local workarounds, noted in
STATUS.md "p2k candidates"); don't touch other repos; report design findings, don't fix them;
temporary files in build/tmp; never run the KiCad AppImage with --version (use tools/p2k/bin/kipy
and tools/p2k/bin/kicad-cli). You may commit after each finished sheet. At the end: STATUS.md
updated (per-sheet result table, check output, findings, p2k candidates), next_prompt.md replaced
with the Phase 2 (footprints) prompt, commit and push (git push origin main). If something needs a
user decision, stop, record it in STATUS.md, commit and push, and report it.
```
