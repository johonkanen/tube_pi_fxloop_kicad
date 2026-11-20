# Next prompt

Ready-to-paste prompt for the next agent session (model: Opus). Replaced at the end of every session.

```
Convert the Proteus board in /home/jari/dev/tube_pi_fxloop_kicad to KiCad 10: Phase 2 (footprints).
Phase 0 and Phase 1 are done: the 4 sheets are drawn (126/126 parts, compare 0 wrong-net pins,
71/71 nets complete, ERC 0 errors / 0 warnings).

Read, in this order: PLAN.md, STATUS.md (Phase 1 preparation: the pinout table; Phase 1
transcription; Findings 9, 10; the pad / drill families in the Phase 0 notes; p2k candidates),
tools/p2k/CONVERSION_PLAYBOOK.md (section 3 "Phase 2" and section 5), tools/p2k/README.md
(footprints, check_footprints, FOOTPRINT_PAD_SIZES). Run tools/check_all.sh first and compare with
STATUS.md "Last check output".

Model: the power amp pilot ~/dev/tube_power_amp_kicad (READ ONLY): its tools/gen_footprints.py
(RULES, PROJECT, derived and IPC-built footprints), its STATUS.md "Phase 2" and Findings 10, 11.
The finished reference ~/dev/tube_psu_kicad (READ ONLY) for the same steps.

Do:
1. tools/gen_footprints.py (board RULES + PROJECT on p2k.footprints) -> lib/footprint_map.csv and
   lib/tube_pi_fxloop.pretty, project fp-lib-table. Default FOOTPRINT_PAD_SIZES = "kicad" (pad
   centres on the Proteus positions). Parts: R (RES40 10.16 mm, 2 W metal film 19.05 mm), film caps
   (Xicon 22N / 47N / 100N, MMK 5 mm, Solen 1 uF 30.48 mm), electrolytics (ELEC-RAD10 2.54 mm with
   pins + / -, ELEC D16 R7.5 with pad 2 = +), DO-35 / DO-41 diodes (pins A / K), TO-92 (2N3906 E B C,
   J112 D S G, pitch 2.032 mm), TO-220 (IRF820 G D S), the 9-pin noval socket (U4, U5), the G5V-2
   relay with the Proteus numbers 1-8, SW-SPDT (3 holes), the 39 one-pad terminals (3.048 / 1.524),
   board-only footprints for the 10 plated 3.0 mm mounting holes.
2. p2k check_footprints (and kipy -m p2k.check_footprints --pcbnew): every part fits the IPC pads
   within 0.05 mm; reports/footprint_fit.csv.
3. Pin-order checks, reported in STATUS.md Findings: the noval socket against an ideal noval circle
   (the pilot's octal socket was mirrored: check the direction of pins 1 -> 9 seen from the top
   side), the relay's Proteus pins 1-8 against the Omron G5V-2 pads (1, 4, 6, 8, 9, 11, 13, 16) by
   position, SW-SPDT (NO = 1, NC = 2, COM = 3), TO-92 / TO-220 pad order, C1 / C36 / C37 pad 2 = +.
4. Sheet scripts fill the Footprint field from the map (sch_builder.footprint does it when
   lib/footprint_map.csv exists): re-run the 4 sheet scripts, tools/check_sheets.sh, ERC with the
   project fp-lib-table.
5. Add the new checks to tools/check_all.sh; negative-test each (move a pad 0.1 mm, swap two pad
   numbers) and record it.

Rules (PLAN.md section 5): don't change tools/p2k or its pin (board-local workarounds, noted in
STATUS.md "p2k candidates"); use tools/compare.py, not p2k compare_netlists (candidate 9); don't
touch other repos; report design findings, don't fix them; keep the Proteus pads, ids and sides;
temporary files in build/tmp; never run the KiCad AppImage with --version (use tools/p2k/bin/kipy
and tools/p2k/bin/kicad-cli). No symbol may use the no_connect pin type (check_all.sh greps).
At the end: STATUS.md updated (footprint table, check output, findings, p2k candidates, decisions),
next_prompt.md replaced with the Phase 3 (PCB) prompt, commit and push (git push origin main). If
something needs a user decision (e.g. Proteus pad sizes), stop, record it in STATUS.md, commit and
push, and report it.
```
