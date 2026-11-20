# PI + FX loop rev B: status

2026-11-21 session (scope: initial schematic, interface viability check, what has been missed; no
layout). Designed to docs/interfaces.md **IF-1 / IF-1.1** as it stands; the changes this board
needs are proposals (below), not applied.

## Done

- Simulations in `sim/` (README.md "Simulations"): open-load PI loop margins; FX loop levels with
  the rear pots and pad, input, noise, W23 coupling; PI-4 attenuator.
- Generated schematic, five sheets, 235 parts, ERC 0 / 0, netlist verified (README.md).

## Connector refs (interfaces.md section 2)

| Ref | Cable end | Part | Pinout |
|---|---|---|---|
| J101 | W22-b | 1x3 Lock-2.54 | 1 PRE_IN, 2 GND, 3 GND (shield, solid here) |
| J102 | W23-a | 2x8 IDC | IF-1.1: 2 SEND_SRC, 6 RETURN_SIG, 10 PAD_A, 12 PAD_B = GND, 14 / 16 NC, others GND |
| J201 | W24-a | 1x5 Lock-3.96 | 1 GND_DRV, 2 DRV_A, 3 GND_DRV, 4 DRV_B, 5 GND_DRV (GND_DRV soft-tied to AGND) |
| J301 | W25-b | 1x2 Lock-3.96 | 1 FB_8R, 2 FB_RTN |
| J302, J303, J304 | W30-b, W31-b, W32-b | 2x5 IDC | interfaces.md 11.2 (CL, CR, LD) |
| J401 | W13-b | 2x7 IDC | template 6.1 (ribbon ground = GNDD) |
| J501 | W03-b | 2x 4.8 mm tabs | 1 BP_RAW, 2 GND |
| J502 | W07-b | 2x 6.3 mm tabs | HTR1, HTR2 (in) |
| J503 | W08-a | 2x 6.3 mm tabs | HTR1, HTR2 (out to the preamp's J502) |

## Rail currents (interfaces.md 3.2)

| Rail | Steady | Peak | Notes |
|---|---|---|---|
| Raw HV (RAW_SS) | about 11 mA | limits 25 + 27 mA (+ 2x 2.5 mA reference) | B+PI 2.9 mA (PI 2.07 mA + 470k bleed), B+FX 3.1 mA (CF 1.35 + return stage 1.04 + bleed), 2x about 2 mA zener CCS, 2x 0.5 mA foldback divider |
| Heaters 6.3 V | 0.6 A own | — | **1.5 A through J502** (0.9 A passed to the preamp on J503) |
| +5 V | 32 mA at 0 dB (one feedback relay + logic) | **152 mA** at the 15 dB step (4 attenuator relays + 1 feedback relay) | G6K-2 coil taken as 30 mA (confirm with the part number); 2 attenuator relays at 18 dB, 3 at 7 / 11 / 13 / 14 dB |
| +15 V | < 1 mA | < 1 mA | 3x DG412 V+ |
| -15 V | about 1 mA | about 1 mA | 300 µA per active JFET switch pair (at most 3: dry, wet, one network) + pad pull 15 µA + DG412 V- |
| -80 V | — | — | |

## Interface check (one row per item touching this board)

36 rows: 27 OK, 5 problems (17, 20, 24, 32, 33), 4 questions (13, 16, 19, 36).

| # | Item (interfaces.md section) | Result |
|---|---|---|
| 1 | W03-b raw HV tabs BP_RAW / GND, 4.8 mm, insulated (2.1, 4.1, 4.3) | OK |
| 2 | RAW_SS 100 mA slow fuse (4.2) against two regulators (limits 25 + 27 mA) | OK. In a shorted output the foldback current (8-10 mA) never blows it: the pass device dissipates 3.5-4.3 W until the fault is cleared, so it needs the heatsink / chassis mount (missed item 6) |
| 3 | W07-b / W08-a heater tabs 6.3 mm, daisy chain to the preamp (2.1, 4.3) | OK (1.5 A through the board) |
| 4 | No heater reference on this board (5); Vhk at 0 / +90 V | OK: cathodes at 31 V (CF), about 22 V (PI), 1.6 V (return stage): worst Vhk 88 V with the elevated option, 12AX7 max 180 V |
| 5 | W13-b template 2x7 pinout (6.1) | OK |
| 6 | 5 V logic, SPI mode 0, 1 MHz, no I2C (6.2, 6.5) | OK (MCP23S17, 74LVC1G11 and DG412 VL at 5 V) |
| 7 | MCP23S17 address 000, HAEN 0, INTA / INTB unused (6.1) | OK |
| 8 | Fail-safe: card absent / reset / ribbon unplugged = muted (6.2) | OK: 100k pull-downs, branch enables low → both FX branches shunted; feedback JFETs shunted; relays off (attenuator 0 dB, no feedback network) |
| 9 | -15 V missing = muted (6.2) | OK: every gate at 0 V → series and shunt JFETs on → mixer branches shorted to GND; the feedback node is grounded (no feedback while muted) |
| 10 | MUTE_ALL_N forces both FX branches off (6.2, 8) | OK (74LVC1G11, hardware path) |
| 11 | Expander map (7.2) | OK, as listed; GPB6 / GPB7 spare (NC) |
| 12 | Loop modes and the permanent second-grid return (7.2) | OK: Rbot 4.7k on the common node; "no feedback" = relay and JFETs off |
| 13 | Channel-change sequence (7.4): break-before-make inside 30 ms | **Question**: about 12 ms by estimate (relay release about 3 ms, JFET gate RC 100k / 10n about 5 ms to settle, relay operate + bounce about 4 ms); confirm the operate / release times with the relay part number, then simulate the clicks (missing simulation 2) |
| 14 | W22-b mirror of J507, Lock-2.54 1x3 (2.3) | OK |
| 15 | Input ≥ 1 Mohm (10, note 1) | OK: 1.52 Mohm at 1 kHz (2.2M ∥ the bootstrapped follower); the preamp output loses 0.7 dB |
| 16 | ≤ 50 pF total on the preamp output (10, note 1) | **Question**: the board side is about 8 pF (follower, stopper, pad and trace), so the cable may have about 40 pF: about 40 cm of 100 pF/m shielded lead. -3 dB of the input at about 25 kHz. The two boards are 16 mm apart, but J507 is at the far end of the preamp from J101: confirm the cable route is short |
| 17 | W23 2x8 pinout, SEND_SRC beside RETURN_SIG with grounds between (10.1, IF-1.1) | **Problem**: see proposal P1. With the IF-1.1 pinout (pins 2 and 6, one ground pin between them in the header) the SEND_SRC (full preamp level) to RETURN_SIG (up to 25 kohm at the return pot's middle) coupling is the limit: the dry leak in series mode is -53 dB at 1 kHz / -33 dB at 10 kHz with 0.3 pF and -43 / -23 dB with 1 pF at mid pot settings (results/fx_revb.md) |
| 18 | PAD_A / PAD_B as switch contacts, pad resistors here (10.1) | OK as wired, with a different meaning on this side (proposal P2): PAD_A is a DC line, the switch still grounds it |
| 19 | RETURN LEVEL pot taper OPEN (10.1) | **Question → proposal P3**: 100 kohm log (A) |
| 20 | RETURN_SIG load "≥ 1 Mohm class" (10) | **Problem** (minor): the return input is 220n + 100k into 1M ∥ the mixer: about 230 kohm with the pad off, 110 kohm with it on. A 1 Mohm input would need a buffer and there is no spare triode; the loading is in the simulated return law. Proposal P4: change the text to "≥ 100 kohm" |
| 21 | SEND_SRC about 1 kohm, AC-coupled, 0 V DC (10) | OK: about 1.6 kohm (follower + 1k), 4.7 µF + 1M |
| 22 | FX jack sleeves = this board's AGND through the W23 grounds (5, 10.1) | OK |
| 23 | W24-a 1x5 3.96 mm, DRV_A / DRV_B with the plate DC, coupling caps on the power amp (2.3, 10) | OK |
| 24 | W24 plate DC "about 200-250 V" (10) | **Problem** (document value): the plates sit at about 280 V (B+PI 388 V - 2.2k decoupling - 100k at 1.04 mA) and reach 388 V when the PI doesn't conduct (cold, tube missing): the power amp's coupling caps need ≥ 450 V (630 V preferred). Proposal P5 |
| 25 | W24 ground: soft tie at this (sending) end (5) | OK (10R ∥ 100n) |
| 26 | W25-b FB_8R / FB_RTN, Lock-3.96; FB_RTN referenced only here (2.3, 5) | OK (FB_RTN 0R to AGND at the network; footprint for a soft tie instead) |
| 27 | W30-W32-b 10-pin presence / resonance pinout; 22n parts here; pots 50k rev-log / 250k log (11.2) | OK |
| 28 | Every ribbon G-S-G, no control lines with audio (5) | OK on J302-J304 and J401; J102 OK except proposal P2 puts a static DC line (PAD_A) on the audio ribbon, filtered, which is the same as today's switch contact |
| 29 | Grounding: one AGND entry (W03 return), DGND island + one soft tie, FB_RTN (5, grounding.md) | OK |
| 30 | Rail budget row (3.2) | OK, within the PROPOSED row (figures above) |
| 31 | Relay family: 5 V G6K class (3.1) | OK (8 relays; part number OPEN with the preamp) |
| 32 | Power coupling grid leak "100k (all types)" (10) against pi_nfb's simulated 220k | **Problem**: pi_nfb ran 47n with the power stage's default 220k grid leak; with 100k the corner is 34 Hz instead of 15 Hz, the feedback at 1 kHz drops from 6.6 to 5.6 dB and the open-load LF margin from 28° to 23° (open_load.md). The power amp session and the coordinating session should settle one value (proposal P6) |
| 33 | PI-3 open-load LF margin (14, SAFE-5) | **Problem**: see proposal P6 |
| 34 | PI-4: PI input under 18 V peak (SPEC PI-4) | OK: at most 13 V at 20 V preamp |
| 35 | FX-4: mixer nodes under 2 V peak at 0 V DC | OK: dry node 1.55 V at 20 V preamp; the wet node passes 2 V only beyond the return stage's clipping (4 V at the return jack) |
| 36 | Chassis envelope: rev A outline 225 x 72 mm, U4 / U5 sockets, 9 of 10 holes (12, [FIT]) | **Question**: see missed item 5 (tall parts and the 15 mm standoffs, heatsinking, area for 235 parts) |

## Interface changes proposed (to the coordinating session)

| # | What | Why | Boards | interfaces.md |
|---|---|---|---|---|
| P1 | W23 pinout: put RETURN_SIG at the far end from SEND_SRC: 2 SEND_SRC, 4 GND, 6 RSVD1, 8 PAD_A, 10 PAD_B (GND), 12 RSVD2, 14 GND, 16 RETURN_SIG (odd pins GND as now) | Send-to-return coupling (row 17): SEND_SRC is at full preamp level and RETURN_SIG is up to 25 kohm; with pins 2 and 6 the dry leak in series mode is -33 to -53 dB at 10 kHz for 0.3 pF. Pins 2 and 16 are 17.8 mm apart in the header with 11 grounded or quiet conductors between them in the ribbon (< 0.01 pF: about -83 dB at 1 kHz). Neither board has started. Fallback: a separate shielded lead for RETURN_SIG. The rear I/O layout must also keep the send and return copper apart (pots, jacks) | PI + FX, rear I/O | 10.1, 13 (IF-1.2; strictly a pin move = IF-2, but no board exists) |
| P2 | PAD_A becomes a DC line: pulled to -15 V through 1M on the PI + FX, 100n at the connector; the rear switch closes it to PAD_B (GND) for -20 dB; open or unplugged = 0 dB | The IF-1.1 wiring puts the pad's shunt leg on PAD_A: with the switch open PAD_A is a 60-70 kohm audio node on the ribbon (a second coupling victim). Rear I/O wiring unchanged (an SPST between PAD_A and PAD_B); the contact switches 15 µA at 15 V | PI + FX, rear I/O (note only) | 10.1 |
| P3 | RETURN LEVEL pot: 100 kohm log (A), same part as the SEND LEVEL pot | Log spreads the return from -30 to +14 dB re unity over the rotation, with unity at 0.6-0.7 for a 1-2 V return; linear crams it (-7 dB at 10 %, +7 dB at 50 %) (fx_revb.md) | rear I/O | 10.1 |
| P4 | RETURN_SIG load text: "≥ 100 kohm (230 kohm pad off, 110 kohm pad on)" instead of "≥ 1 Mohm class" | Row 20 | PI + FX, rear I/O | 10 |
| P5 | W24 DC: "about 280 V, up to 390 V with the PI cold; the power amp's coupling caps ≥ 450 V" | Row 24 | PI + FX, power amp | 10 |
| P6 | Open-load margin (PI-3, SAFE-5): power coupling caps **100n** with **220k** grid leaks (and settle 100k vs 220k) | With 47n the open-load LF margin is 23-28° and the gain margin 8 dB (pi_drive's problem case was 7-9 dB); 100n / 220k gives 37° / 11.7 dB, loaded 61-67° / 15-17 dB. Costs blocking recovery (pi_nfb point 9/12: 0.1 µF recovers slower than 47n): the user's trade, or a different fix (LF shelf in the feedback network, next step). Not this board's decision: the caps are on the power amp | power amp, PI + FX | 10, 14 |
| P7 | Rail row PI + FX: raw HV 11 mA, heaters 0.6 A (+0.9 A through), +5 V 32 / 152 mA, +15 V < 1 mA, -15 V about 1 mA | Real figures | — | 3.2 |
| P8 | Connector refs J101, J102, J201, J301-J304, J401, J501-J503 (table above) | Assigned | — | 2 |

## Missed items, ranked

1. **Open-load LF stability (SAFE-5 / PI-3)**: 23-28° / 8 dB with the decided 47n caps (P6). Also
   the open-load large-signal case is not simulated at all: full drive into no load gives the
   highest plate voltages (OT flyback) and the feedback loop gain jumps to 26-28 dB.
2. **W23 send-to-return coupling** (P1, P2): with the IF-1.1 pinout the dry leak around the effects
   unit can be -23 to -53 dB at 10 kHz; and PAD_A as wired is a high-impedance audio node.
3. **The overall gain from the preamp output to the PI input is not specified anywhere.** The
   preamp delivers up to 20 V peak and the PI must stay under 18 V at the 0 dB attenuator step, so
   the loop needs ≤ -1 dB; drawn at -3.8 dB (requirement R1).
4. **Grid leak 100k (interfaces.md) vs 220k (pi_nfb)** and the **W24 DC level / cap rating** (P5,
   row 32).
5. **Mechanics of the kept outline:** the boards hang 15 mm under the plate with the component
   side toward it, so 47 µF / 450 V electrolytics (Ø16-18 mm), the 2.2 µF / 630 V film caps,
   the 5 W zeners and any heatsink do not fit standing on that side: they go on the other side
   (66 mm free below) or lie down. Rev A had the noval sockets on the bottom side: which side faces
   the plate in rev B, and where the tubes point, needs the user's confirmation. 235 parts plus
   the HV parts in 162 cm² is plausible with SMD but not checked (no layout in this session).
6. **Regulator heatsinking:** a shorted B+ output dissipates 3.5-4.3 W in the pass device
   indefinitely (the 100 mA fuse doesn't blow at the 8-10 mA foldback current). Proposed: insulated
   TO-220F clamped to the chassis plate through a 15 mm aluminium spacer, or a lower foldback.
7. **No RETURN-jack detect:** in series mode with nothing plugged into RETURN the amp goes silent.
   No pin or bit for a jack switch (requirement R6).
8. **DC on the effects unit's output** reaches the rear RETURN pot (scratchy pot); this board
   blocks it (220n) but the rear I/O should AC-couple at the jack.
9. **Send at full into a 10 kohm line input clips** (1.2 % at 9 V preamp, 15 % at 17 V): the
   follower can't drive 10 V peak into 11 kohm. Fine below about 6 V peak at the jack; the send pot
   at full is +16 dBu, beyond any line input. Documented, not fixed (requirement R3).
10. **Unplugged W25 (feedback lead):** the amp runs open loop (about 6 dB louder, more distortion),
    undetected (requirement R11).
11. **CCS spread:** DN2540 Vgs(off) 1.5-3.5 V moves the tail current 2:1 with a fixed source
    resistor: select or trim; the real-model run is missing.
12. **Heater pass-through current** (1.5 A on J502) and the 430 V creepage on a board that also
    carries ribbons: no requirement states either (R15, R17).

## (a) Simulations that should exist before the values or topology freeze

| # | Simulation | Question it answers | Input it needs |
|---|---|---|---|
| S1 | PI loop with a real DN2540 SPICE model (and its spread) | Tail current spread, CCS noise and capacitance, PI balance and clipping (pi_nfb Next); here only a 1 Mohm / 30 pF equivalent was used | DN2540 model (Microchip / Supertex), 12AX7 spread fits |
| S2 | Feedback network switching clicks: relay + JFET T sequence, break-before-make, inside the 30 ms mute; also FX mode switching with signal | Click amplitude at the speaker; whether the 100k / 10n / 1M gate timing and the sequence fit 30 ms | Relay operate / release / bounce times (part number), JFET model, the firmware order of 7.4 |
| S3 | PI-4 relay steps outside the mute (power-pot moves, 1 dB per 50 ms) | Zipper / click at each step with signal present | Relay timing, the attenuator, the PI + power stage |
| S4 | Open-load large-signal transient (no speaker, full and over-drive) | Plate voltage peaks on the OT (flyback), PI and power-tube grid behaviour, whether the loop oscillates when clipping recovers | power_stage with the OT leakage, the rev B loop |
| S5 | Loop margins with the measured OT (winding capacitance, PI-6) and each channel's own Rf (D18) | HF margin per channel; Cf and the step network values | 1650TA measurement or a ring test |
| S6 | An LF shelf in the feedback network as the alternative to bigger power coupling caps | Open-load LF margin without slowing the blocking recovery | this board's networks |
| S7 | W23 ribbon capacitance (field solve or a measurement) and the rear I/O layout coupling | The real Ccpl for row 17 / P1 | ribbon type and length, rear I/O layout |
| S8 | Mute depth: PRE_IN → PI input with both branches shunted, at 20 V peak in, plus board-level crosstalk from J101 / SEND_SRC to the PI input and from W24 / W25 (A class) to the input | Whether the mute and the layout reach -80 dB | layout (crosstalk bench) |
| S9 | Tube spread (three 12AX7 fits) on the rev B loop: unity between dry and wet, the overall -3.8 dB, the PI balance | FX-1 level match, PI-4 accuracy | existing fits |
| S10 | B+ decoupling and motorboating with the regulators (about 20 ohm) and the per-stage RC, PI and FX together | LF stability of the B+ network (preamp_regulator open item 4) | regulator model, stage currents |
| S11 | PI input blocking with the rev B drive (attenuator source impedance, 10n, at most 13 V) | Recovery after bursts at the real maximum drive | run_blocking with the FX loop output model |
| S12 | Return stage headroom options (plate current, load) | The return stage clips 7-9 dB over the unity point (sim/fx_loop had 15 dB with the old levels) | — |

## (b) Requirements missing from SPECIFICATION.md (proposed wording)

| # | Topic | Proposed wording |
|---|---|---|
| R1 | Loop gain | "The gain from the preamp output (J507, open-circuit) to the PI grid, with the PI-4 attenuator at 0 dB and the loop in bypass, is -4 ± 1 dB, so the preamp's 20 V peak maximum reaches the PI at no more than 13 V peak." |
| R2 | Open-load stability (SAFE-5) | "With no speaker load, at every power setting, channel and control position, the feedback loop keeps a gain margin of at least 10 dB and a phase margin of at least 35° at every crossing; with a load, at least 15 dB and 45°." |
| R3 | Send level | "SEND jack: up to 2 V peak with ≤ 1 % THD into ≥ 10 kohm ∥ 1 nF, and up to 15 V peak into ≥ 100 kohm, for any preamp level up to 17 V peak; the send is AC-coupled (no DC on the pot or the jack)." |
| R4 | Return level | "The loop reaches unity gain (series level = bypass level) for return-jack levels from 0.45 V to 8 V peak (pad off / on); return-path THD ≤ 2 % at 3 dB over the unity point." |
| R5 | Dry leak | "In series mode the dry signal reaching the PI around the effects unit is at least 60 dB below the wet signal from 20 Hz to 10 kHz, at any pot settings." |
| R6 | Missing return plug | Needs the user: "With no plug in RETURN in series mode the loop (a) is silent, or (b) passes the send signal (the RETURN jack's normalling contact joins it to the SEND pot's wiper on the rear I/O board)." Proposed default (b) |
| R7 | Mute depth | "Muted (FX_UNMUTE or MUTE_ALL_N low): at least 80 dB from the PI + FX input to the PI grid, 20 Hz-20 kHz." |
| R8 | Fail-safe state of this board | "Card absent, reset or -15 V missing: both FX branches shunted, no feedback network connected, the attenuator at 0 dB with every relay off; the firmware writes the attenuator step and the feedback network before it unmutes." |
| R9 | Feedback switching | "A feedback network changes only inside the channel-change mute, break-before-make (old relay open, JFETs, new relay closed), with no audible click (target under 10 mV at the speaker)." |
| R10 | W24 levels | "The PI outputs carry its plate DC, about 280 V and up to 390 V with the PI cold; the power amp's coupling caps are rated ≥ 450 V." |
| R11 | Unplugged feedback lead | "With W25 unplugged the amp runs open loop and stays stable; no detection required." (or detection, if the user wants it) |
| R12 | CCS tail | "PI tail current 2.0 ± 0.2 mA (selected or trimmed source resistor)." |
| R13 | Regulator fault | "A shorted small-signal B+ output is survived indefinitely: pass device on a heatsink or the chassis rated for the foldback dissipation (4.3 W at 430 V raw)." |
| R14 | Input capacitance | Already in interfaces.md (≤ 50 pF); add to SPEC: "W22 cable ≤ 40 pF (about 40 cm)". |
| R15 | Heater pass-through | "The PI + FX board passes the preamp's heater current: heater path rated ≥ 2 A (tabs, traces)." |
| R16 | Ambient | "Boards under the plate are rated for 60 °C ambient with the tubes running" (no figure exists; parts derating needs one). |
| R17 | HV creepage | "On boards with raw HV (430 V): ≥ 2.5 mm creepage / clearance from 430 V nets to low-voltage and ribbon nets, ≥ 1.5 mm between HV nets of different potential (functional insulation; no safety barrier on these boards)." |

## Open questions (for the user / coordinating session)

1. P6: power coupling 100n / 220k (better open-load margin, slower blocking recovery) or keep 47n
   and accept 8 dB / 23-28° with no speaker, or try an LF shelf (S6) first.
2. P1: W23 pin move (both boards unstarted) or a separate shielded return lead.
3. R6: behaviour with nothing in RETURN (silent, or normalled to the send).
4. Which board side faces the plate in rev B and where the tubes point (missed item 5).
5. Relay part number (shared with the preamp): coil current and operate / release times feed the
   +5 V figure and the 30 ms sequence.

## Next steps

1. The simulations S1-S4 and S6 (the ones that can change values here), then freeze the CCS, the
   gate timing, and with the power amp the coupling caps.
2. After the coordinating session's answer: W23 pinout (P1 / P2) in `draw_all.py`.
3. Footprints, then a layout feasibility pass in the rev A outline (tall parts side, heatsink).
4. Feedback amount per channel (D18): all three start at Rf 100k ∥ 22p; proposal after S5.
