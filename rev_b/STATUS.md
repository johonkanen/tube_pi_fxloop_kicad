# PI + FX loop rev B: status

## Fourth pass (2026-11-23): 500 V B+ electrolytics

User, 2026-11-23: B+ output electrolytics 500 V if they can be sourced. If a pass device fails
short, B+PI / B+FX go to the raw rail (up to 480 V). They can be sourced, so all five changed:

| Ref | Was | Now | Size (D x L), pitch | Rating | Source (2026-11-23) |
|---|---|---|---|---|---|
| C502, C505 (B+PI / B+FX reservoir) | 47u / 450 V (EG22WM470L26OTMO) | **47u / 500 V Nichicon UCY2H470MHD6** | 18 x 31.5 mm (33 mm seated), P7.5: same footprint `CP_Radial_D18.0mm_P7.50mm` | 105 °C, 12000 h, 440 mA at 120 Hz | DigiKey (448 in stock, about GBP 4.3 each), RS; second source Rubycon 500LXW47MEFR18X25 (18 x 25, 12000 h, DigiKey) |
| C507, C508, C509 (per-stage decoupling) | 22u / 450 V, Ø12.5 P5 (EWH2WM220L20C33T) | **22u / 500 V Nichicon UCY2H220MHD6** | 16 x 25 mm (26.5 mm seated), P7.5: footprint `CP_Radial_D16.0mm_P7.50mm` | 105 °C, 12000 h, 280 mA at 120 Hz | DigiKey (562 in stock, about GBP 2.8 each) |

- Neither part is at LCSC / JLC (only the 400 V UCY2G470MHD, C225862): hand-soldered, like the
  noval sockets. Long factory lead times (22-41 weeks) are listed, so buy from stock.
- Board area: the 47 µF footprints are unchanged; each 22 µF grows from Ø12.5 to Ø16 (+0.8 cm² of
  body outline each, about +2.4 cm² for the three). Height: 33 mm max against 66 mm free.
- No series pairs needed. The 2.2 µF / 630 V reference films and the 100 n / 630 V films were already
  ≥ 500 V.
- **Preamp equivalent (same regulator, for the preamp session):** C502 47u/450V → Nichicon
  UCY2H470MHD6 (same Ø18 P7.5 footprint); C510-C513 22u/450V (Ø12.5) → Nichicon UCY2H220MHD6
  (Ø16, P7.5). C501 (2.2 µF / 450 V on the zener-clamped 390 V reference) and C520 (VB90) do not see
  the raw rail in that fault and can stay.

## Third pass (2026-11-23)

Scope: the user's decisions of 2026-11-23 (the coordinator's decisions_1123 list; interfaces.md
IF-1.3). **252 parts, ERC 0 / 0, `verify.py` 168 nets with 0 mismatches, footprints on all parts,
`bom/bom.csv` 89 lines (37 with an LCSC number).**

### Changes

| # | Decision | Change |
|---|---|---|
| 1 | W24 = Molex Mini-Fit Jr, pin order unchanged (V5) | J201: `Conn_02x03_Top_Bottom`, footprint `Molex_Mini-Fit_Jr_5566-06A_2x03_P4.20mm_Vertical` (header Molex 39-28-1063 class, order code to confirm; receptacle 39-01-2060; as the coordinator set for both boards). KiCad has no single-row Mini-Fit Jr, so the 2x3 with position 6 unused: 1 GND, 2 DRV_A, 3 GND / 4 DRV_B, 5 GND, 6 NC. Every pin beside a drive pin is GND (DRV_A: 1, 3, 5; DRV_B: 1, 5); the two drive pins are only diagonal (6.9 mm). **The power amp must use the same 2x3 mapping** |
| 2 | Rf ≥ 68k on every channel, 47k option dropped, second grid 22n (V1) | Nothing to re-value: all three Rf are 100k ∥ 22p and C203 is 22n. The DNP step-network footprint (R327 / C319) stays as an empty footprint, noted "the Rf 47k + step option is dropped" |
| 3 | PI grid leaks to a fixed decoupled reference if they return to the tail (V1 list, item 16) | **They did** (R213 / R218, 1M to PTOP, the CCS top). Now to **PI_REF**: 2x 820k 2512 from B+PI decoupled (BPI_P, 386 V; 182 V per part) + 100k to GND = 22.2 V, 10 µF / 50 V (0.17 Hz). New R222-R224, C204. Tail top about 21 V, so the DN2540 keeps about 19 V of compliance. Simulated, below |
| 4 | Raw rail to 480 V as a transient / trip level, sustained ≤ 450 V, raw-rail parts ≥ 500 V (V7) | Checked, no change needed (below) |
| 5 | Normalled return at full level accepted (V15) | Simulated, no change (below); manual text proposed |
| 6 | P-J_FX and the pot-ribbon headers | Layout notes: J102 at the rear edge, **x 170-190** (the rear I/O jack board stands behind x 191-219); J302 / J303 / J304 at x 200-279 on the downward face near the front edge, in CL / CR / LD order |
| 7 | Power tubes 91k / 220 nF (V1) | Sheet 02 note: 91k leak, 220 nF film ≥ 630 V per tube, on the power amp; no longer OPEN |

### Result: where the PI grid leaks return (`sim/pi_burst/run_leak_ref.py` → `results/leak_ref.md`)

The master repo's burst test (copied from sim/pi_nfb at ca741ff, plus a divider option): 220n / 91k,
4x EL34, 400 V, Rf 100k, speaker; 300 ms of 100 Hz on a 1 kHz probe.

| Leak return | Burst | Power grid shift / back within 1 V | PI grid shift down / up / back within 1 V | Probe dip / back within 1 dB |
|---|---|---|---|---|
| tail top (second pass) | +13 dB | -11.8 V / 120 ms | -0.2 / **+39.3 V / not back after 1 s** | -1.1 dB / 19 ms |
| tail top (second pass) | +20 dB | -12.1 V / 115 ms | -0.1 / **+108.7 V / not back** | -0.6 dB / 45 ms |
| PI_REF divider 22 V (third pass) | +13 dB | -8.1 V / 78 ms | -1.3 / +1.2 V / 0 ms | -0.8 dB / 0 ms |
| PI_REF divider 22 V (third pass) | +20 dB | -16.8 V / 93 ms | -3.0 / +2.8 V / 11 ms | -1.4 dB (the probe stays about 1-1.4 dB low to the end of the run; the ideal 9 V reference gives exactly the same) |

The divider behaves like the study's ideal reference (identical figures). +13 dB is the real maximum
drive; +20 dB is beyond the PI-4 limit.

### Result: regulators at 430 / 450 / 480 V raw (`sim/preamp_supply/run_raw480.py` → `results/raw480.md`)

Part stress at 480 V: LND150N8 (500 V) sees 90 V (PI) / 150 V (FX), the full raw only if a zener
string fails short; STD4N80K5 (800 V) up to 480 V into a short; MMBTA42 (300 V) under 20 V; M7
(1000 V) up to 480 V reverse at power-up; R3 3x 270k 2512: 160 V each into a short (200 V); Rf 3x
330k: 130 V each (set by the reference); the 2.2 µF film is 630 V on the reference. No capacitor on
the raw rail itself on this board. All within rating.

| Raw | Q1 at 70 °C: limit B+PI / B+FX | at 85 °C | at 100 °C | Start-up and recovery after a short |
|---|---|---|---|---|
| 430 V | 19.5 / 20.0 mA | 17.5 / 17.5 mA | 16.0 / 15.5 mA | yes everywhere (27-100 °C) |
| 450 V | 18.5 / 18.5 mA | 16.5 / 16.0 mA | 14.5 / 14.0 mA | yes everywhere |
| 480 V | 16.5 / 16.0 mA | 14.5 / 14.0 mA | 12.5 / 11.5 mA | yes everywhere |

Against loads of 2.9 / 3.1 mA (bleed included) the limit keeps a margin of 4x or more, and unlike
B+PRE (15 mA, no start at 480 V above 85 °C) both regulators start and recover even with the raw rail
**held** at 480 V up to Q1 = 100 °C. Into a short at 480 V the current is lower than at 430 V (4.6 /
5.6 mA at 27 °C, near zero above 70 °C). Fault note (not a raw-rail part): if a pass device fails
short, B+PI / B+FX go to the raw rail, and the 450 V outputs and decoupling electrolytics (C502 /
C505, C507-C509) would then see up to 480 V; 500 V parts would cover that case too (optional).

### Result: normalled return at 17 V peak (`sim/fx_loop/run_normalled.py` → `results/normalled.md`)

Series mode, both rear pots full, nothing plugged in: 300 ms of 1 kHz at 17 V peak on RETURN_SIG
with a 0.3 V / 3 kHz probe.

| RETURN_SIG | Pad | Return grid current peak / average | Wet node / mixer node peak | Return plate | Loop output (PI input, 0 dB) | Probe after the burst |
|---|---|---|---|---|---|---|
| 17 V | 0 dB | 1.5 / 0.08 µA | 6.6 / 2.7 V | 202-252 V | 30 V peak | -26 dB at 10-50 ms, back (±0.1 dB) by 50 ms |
| 17 V | -20 dB | 0.3 / 0.08 µA | 1.5 / 0.6 V | 201-226 V | 12.7 V peak | no dip |
| 9 V | 0 dB | 0.9 / 0.08 µA | 3.7 / 1.5 V | 201-243 V | 24.7 V peak | no dip |

Nothing latches and no part rating is exceeded: return grid current is negligible (the 1M / 220k
network), DC shifts (return grid +0.6 V, cathode +0.3 V, wet node +1.5 V) decay within about 200 ms,
JFET and film-cap voltages far below their ratings. What it does: with the pad off the wet series
JFET and the mixer are driven past their 2 V limit (FX-4) and the loop output reaches about 30 V peak
at the PI input, beyond the PI-4 18 V limit: heavy distortion, and the PI then blocks like the +20 dB
burst above (recovers within about 0.1 s with PI_REF). No damage. **Manual text proposed:** "With
nothing plugged into SEND / RETURN the effects loop passes the send signal straight back. Set RETURN
LEVEL to about half, or switch the pad to -20 dB: with both rear pots at full the loop overdrives the
power amp's input stage (loud, distorted, no harm). Bypass the loop if you don't use it."

### New or changed items for the coordinator

- J201 / W24 2x3 mapping (position 6 unused) must match on the power amp's W24-b.
- PI_REF adds four parts and 0.22 mA on B+PI (rail figures unchanged at this resolution).
- The B+ output electrolytics at 450 V: fine in normal use; 500 V parts only if the pass-device
  short is to be covered (decision for the user, optional).
- Manual text for the normalled return (above).

## Second pass (2026-11-23)

Scope: bring the schematic into line with interfaces.md **IF-1.2** and the decisions since the
first pass (abf2c2b), assign footprints, first BOM. Still no layout. Result: **248 parts, five
sheets, ERC 0 errors / 0 warnings, `verify.py` 166 nets with 0 mismatches, footprints on all 248
parts, `bom/bom.csv` 87 lines.** The first-pass record (2026-11-21) follows below, unchanged.

### What changed and why (decision by decision)

| # | Decision / source | Change on this board |
|---|---|---|
| 1 | W23 pinout IF-1.2 (user U8, 2026-11-22; interfaces.md 10.1; was this board's P1) | J102: 2 SEND_SRC, 4 GND, 6 RSVD1 (NC), 8 PAD_A, 10 PAD_B = GND, 12 RSVD2 (NC), 14 GND, 16 RETURN_SIG; odd pins GND. Was IF-1.1 (6 RETURN_SIG, 10 PAD_A, 12 PAD_B) |
| 2 | PAD_A as a DC line (U8; was P2) | Unchanged circuit (it was drawn this way): 1M to -15 V, 100n at J102, 100k / 10n to the pad JFET gate; switch closed = -20 dB, open / unplugged = 0 dB |
| 3 | No floating node with W23 unplugged (interfaces.md 10.1, X4 / N28) | **New R131 2.2M from RETURN_SIG to GND at J102** (the ribbon side of the 220n floated before). 2.2M, not 1M: 1M would take the pad-on RETURN_SIG load to 99 kΩ, under the ≥ 100 kΩ of interfaces.md 10; with 2.2M it is about 105 kΩ (pad on) / 210 kΩ (pad off). Return law moves ≤ 0.1 dB (fx_revb re-run). SEND_SRC is bled by the 1M after the 4.7 µF through the 1k (unchanged) |
| 4 | RETURN LEVEL 100 kΩ log (U11), return jack normalled to the send (U10) | Nothing to draw here; the simulations already use log. With no plug, series mode passes the send signal set by both pots (dry and wet in phase in parallel mode, so no cancellation; no loop is closed) |
| 5 | Relay Omron G6K-2F-Y 5 V, 21.1 mA; datasheet pinout coil + 1 / - 8, pole 1 COM 3 NC 4 NO 2, pole 2 COM 6 NC 5 NO 7 | **The first pass had NO / NC swapped on all eight relays** (read from KiCad's G6K-2 drawing, whose resting arms point at 2 and 7). As drawn in abf2c2b an unpowered board would have had all five attenuator sections in (-31 dB) and **all three feedback networks connected at once**: the fail-safe rows 8 / 9 of the first check were wrong. Now: attenuator pole 1 COM 3 / NC 4 shorts the series resistor, pole 2 COM 6 / NO 7 connects the shunt (energised = section in, unpowered = 0 dB); feedback relays both poles COM 3 / NO 2 and COM 6 / NO 7 (unpowered = network open). Local symbol `G6K-2F-Y` = KiCad's G6K-2 with the arms redrawn onto 4 / 5, so the sheet shows the unpowered state truthfully; footprint `Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y` |
| 6 | B+ regulators: rev B reference (preamp_regulator.md); 70 °C design temperature (U17) | STD4N80K5 DPAK (was STF4N80K5 TO-220F for a chassis clamp), MMBTA42 on its pour (thermal foldback), LND150N8 SOT-89, SMA zeners (1SMA5952B x3; 1SMA5953B + 1SMA5955B), HV strings split for 200 V parts: Rf 3x 330k (390 V across it during the soft start), R3 3x 270k, bleed 3x 150k (was 470k). Rs 20R / 16R unchanged; **no drain resistor**: re-simulated with this board's loads (`sim/preamp_supply`): passes at 70 °C |
| 7 | No fuse in the RAW_SS feed (user U19, 2026-11-23; interfaces.md 4.2, 8) | Sheet text corrected (it said "through the HV supplies' 100 mA fuse"). Downstream protection = the regulators' foldback: a steady short settles at 0.5-0.7 W, junction 93-97 °C at 70 °C. A short ahead of the regulators (tab, feed traces) is the PSU's to stop: keep the BP_RAW copper short, ≥ 2.5 mm from everything else (N57) |
| 8 | Presence / resonance headers at the right-hand end x about 200-279; W23 header at the rear edge x 170-230 (rear I/O now behind this board, parallel to the rear panel) | Layout notes on sheets 01 and 03; no circuit change |
| 9 | Power-tube grid leak / coupling cap OPEN (U7, simulation running in the master repo) | Not on this board (they are on the power amp). Kept as simulated in `sim/pi_nfb/run_open_load.py`, where they are parameters; marked OPEN on sheet 02 |
| 10 | Preamp output about 140 kΩ; input ≥ 1 MΩ, ≤ 50 pF total | Unchanged: 1.52 MΩ at 1 kHz, about 8 pF board side |
| 11 | Components down, about 66 mm below the board, sockets on the solder side | Tallest parts: 47 µF / 450 V (Ø18, about 35-40 mm), 2.2 µF / 630 V film (31.5 x 17 x about 29 mm): fit. The first pass's missed item 5 is closed |
| 12 | Footprints and BOM (this pass's scope) | `lib/footprint_map.csv` and `bom/bom.csv` generated by draw_all.py (README "Build"); part type changes for footprints: generic Q_NMOS / Q_NPN replaced by numbered-pin symbols (Q_NMOS_GDS, DN2540N8-G, MMBTA42) so the pins match the pads; Cres / presence 22n now C0G 1206 50 V (they see under 19 V) |

Refs: sheets 01-04 keep their first-pass refs except the new R131; sheet 05's refs moved (the split
resistors are drawn after each regulator's other parts: R509-R514 and R523-R528 are the second
and third parts of each string).

### Interface check against IF-1.2

40 rows: **33 OK, 3 problems (30, 33, 38), 4 questions (13, 32, 37, 39).**

| # | Item (interfaces.md section) | Result |
|---|---|---|
| 1 | W03-b raw HV tabs BP_RAW / GND, 4.8 mm, insulated (2.1, 4.1, 4.3) | OK (placeholder footprint until the tab part is drawn) |
| 2 | RAW_SS without fuse, protection in three layers (3.1, 4.2, 8) | OK: foldback downstream of each regulator, steady short 0.5-0.7 W (rev_b/sim/preamp_supply) |
| 3 | W07-b / W08-a heater tabs 6.3 mm, daisy chain (2.1, 4.3) | OK (1.5 A through the board) |
| 4 | No heater reference here; Vhk at 0 / +90 V (5) | OK (worst 88 V, 12AX7 180 V) |
| 5 | W13-b template 2x7 (6.1) | OK |
| 6 | 5 V logic, SPI mode 0, 1 MHz, no I2C (6.2, 6.5) | OK |
| 7 | MCP23S17 address 000, HAEN 0, INTA / INTB unused (6.1) | OK |
| 8 | Fail-safe: card absent / reset / unplugged = muted (6.2) | OK, now true: both FX branches shunted, feedback JFETs shunted, every relay unpowered = attenuator 0 dB, no feedback network (first pass: wrong, see change 5) |
| 9 | -15 V missing = muted (6.2) | OK |
| 10 | MUTE_ALL_N forces both FX branches off (6.2, 8) | OK |
| 11 | Expander map (7.2) | OK, GPB6 / GPB7 spare |
| 12 | Loop modes, permanent second-grid return (7.2) | OK |
| 13 | Channel-change sequence inside 30 ms (7.4) | **Question:** about 12 ms by estimate (G6K operate / release about 3 ms each by the datasheet class, to confirm on the G6K-2F-Y sheet; JFET gate settling about 5 ms); simulation M30 still missing |
| 14 | W22-b mirror of J507 (2.3) | OK |
| 15 | Input ≥ 1 MΩ (10, note 1) | OK: 1.52 MΩ |
| 16 | ≤ 50 pF on the preamp output (10, note 1) | OK on this side (about 8 pF): leaves about 40 pF, about 40 cm of 100 pF/m lead (N60) |
| 17 | W23 pinout IF-1.2 (10.1) | OK (drawn) |
| 18 | PAD_A DC line, 1M to -15 V, 100n, JFET pad (10.1) | OK |
| 19 | RETURN LEVEL 100 kΩ log (10.1) | OK |
| 20 | RETURN_SIG load ≥ 100 kΩ (10) | OK: about 210 kΩ pad off, 105 kΩ pad on (with the 2.2M bleed) |
| 21 | SEND_SRC about 1 kΩ, AC-coupled, bleed (10, 10.1) | OK (1.6 kΩ, 4.7 µF, 1M) |
| 22 | SEND_SRC load ≥ 9.9 kΩ at full send (10) | OK as a load; the follower's clipping into it (1.2 % at 9 V, 15 % at 17 V) stays open with M10 |
| 23 | FX jack sleeves = this board's AGND (5, 10.1) | OK |
| 24 | W24-a 1x5 3.96 mm, plate DC on the line, caps on the power amp (2.3, 10) | OK |
| 25 | W24 DC about 280 V, up to 390 V cold (10) | OK (now in interfaces.md) |
| 26 | W24 soft tie at the sending end (5) | OK |
| 27 | W25-b FB_8R / FB_RTN, FB_RTN referenced only here (2.3, 5) | OK |
| 28 | W30-W32-b pinout, 22n parts here, pots on the front panel (11.2) | OK |
| 29 | P-J_PR_* at the right-hand end x about 200-279; P-J_FX at the rear edge x 170-230 (12.3) | OK (layout notes) |
| 30 | Rail row PI + FX (3.2) | **Problem (document value):** the row still says 10-20 mA raw, 40 / 160 mA on +5 V with relays; real figures below (+5 V 25 / 115 mA with the 21.1 mA coils). Proposal P9 |
| 31 | Relay G6K-2F-Y, NO / NC check (3.1, the OPEN check) | OK for this board: every relay on NO per the datasheet pinout given (sheets 02, 03); unpowered = safe |
| 32 | Power coupling cap / grid leak OPEN (10, 14) | **Question:** not this board's parts; waiting for the master repo's no-speaker simulation |
| 33 | PI-3 / SAFE-5 open-load LF margin (14) | **Problem** until 32 is decided: 23-28° / 8 dB with 47n (first pass) |
| 34 | PI-4: PI input under 18 V peak | OK: 13 V at 20 V preamp |
| 35 | FX-4: mixer nodes under 2 V peak | OK |
| 36 | Envelope, components down, 66 mm (12.1, 12.2) | OK for height (change 11); area for 248 parts in the rev A outline is checked only at layout |
| 37 | 70 °C under the plate (SPEC ENV-2) | **Question:** regulators pass (sim); electrolytics 105 °C, MCP23S17-E, DG412DY (-40 to 85 °C), 74LVC1G11, G6K (to 85 °C) fine; the ULN2803A's rated range must be checked on the part bought (some sources give -20 to 70 °C for the family; ULQ-class or an 85 °C grade if so) |
| 38 | W24 header rated ≥ 450 V between adjacent pins (10, OPEN check) | **Problem:** the Lock-3.96 families (Molex KK-396, JST VH) are, as far as I know, rated 250 V by their makers (confirm on the datasheets); 390 V sits between DRV_A / DRV_B and the GND pins next to them. Proposal P10 |
| 39 | "a 100 kΩ return grid leak" on the PI + FX (10.1) | **Question (wording):** the 100k here is the pad's series resistor; the return path is held by the 1M on the pad node, the 220k on the mixer / return grid and now the 2.2M on RETURN_SIG. Proposal P11 (text only) |
| 40 | Grounding: one AGND entry, DGND island + soft tie, W22 solid here (5, grounding.md) | OK |

### Rail currents (interfaces.md 3.2)

| Rail | Steady | Peak | Notes |
|---|---|---|---|
| Raw HV (RAW_SS) | about 10 mA | limits 25 + 27 mA cold (19.5 + 20 mA with Q1 at 70 °C) | B+PI 2.9 mA (PI 2.07 + 450k bleed 0.86), B+FX 3.1 mA (CF 1.35 + return 1.04 + bleed 0.73), 2x about 2 mA zener CCS, foldback strings about 0.1 mA |
| Heaters 6.3 V | 0.6 A own | — | 1.5 A through J502 (0.9 A on to the preamp on J503) |
| +5 V | about 25 mA (0 dB, one feedback relay) | about 115 mA at the 15 dB step (4 attenuator + 1 feedback relay x 21.1 mA, ULN inputs, logic) | about 3 mA with every relay off; 2 relays at 18 dB, 3 at 7 / 11 / 13 / 14 dB |
| +15 V | < 1 mA | < 1 mA | 3x DG412 V+ |
| -15 V | about 1 mA | about 1 mA | gate pulls, pad pull, DG412 V- |
| -80 V | — | — | |

### Connector refs (unchanged)

J101 W22-b, J102 W23-a, J201 W24-a, J301 W25-b, J302 / J303 / J304 W30-b / W31-b / W32-b, J401 W13-b,
J501 W03-b, J502 W07-b, J503 W08-a (pinouts in the first-pass table below; J102 now IF-1.2).

### Interface changes proposed (new in this pass)

| # | What | Why | Boards | interfaces.md |
|---|---|---|---|---|
| P9 | Rail row PI + FX: raw HV about 10 mA (limits 25 / 27 mA), heaters 0.6 A (+0.9 A through), +5 V 25 / 115 mA, +15 V < 1 mA, -15 V about 1 mA | Real figures with the 21.1 mA G6K-2F-Y coil (the row still has 40 / 160 mA) | — (control board +5 V budget) | 3.2, 3.3 |
| P10 | W24: either confirm a Lock-3.96 part rated ≥ 450 V DC between pins, or move W24 to a family rated 600 V (Molex Mini-Fit Jr class, 4.2 mm) or a 1x5 3.96 mm housing with the GND pins removed (DRV_A and DRV_B then 7.9 mm from anything) | 390 V on the line, 250 V typical rating of the KK-396 / VH families | PI + FX, power amp | 2.3, 10 |
| P11 | 10.1 text: "the PI + FX has a 1 MΩ bleed after its send capacitor and a 2.2 MΩ bleed on RETURN_SIG (the return grid is held by 1 MΩ on the pad node and 220 kΩ on the mixer)" instead of "a 100 kΩ return grid leak" | The 100k is the pad series resistor; a 100k leak on RETURN_SIG would load the return pot's wiper | PI + FX, rear I/O (none) | 10.1 |

The first pass's P1-P5 and P8 were accepted (IF-1.2, review section 2); P6 is the open U7; P7 is
replaced by P9.

### Still open

1. Power coupling cap / grid leak (U7) and with it the open-load margin (rows 32, 33).
2. W24 header voltage rating (row 38, P10).
3. Channel-change timing and clicks (row 13, M30); G6K-2F-Y operate / release / bounce from the
   datasheet.
4. ULN2803A temperature grade (row 37).
5. CCS: DN2540 spread (select Rs for 2.0 mA, R221 "1k (select)"); real-model run M4.
6. Send follower into the full-send load (M10); return stage headroom 7-9 dB (M11).
7. Footprints to finalise at layout: the power tabs (placeholders), the noval socket (rev A's
   Belton footprint), the 2.2 µF / 630 V film's real body; candidate parts without an LCSC number
   (51 lines) need sourcing; no stock check run.
8. Preamp side, for information: preamp_regulator.md asks for Rf ≥ 500 V rated (2x 470k); this
   board uses 3x 330k 2512 for the 390 V across Rf during the soft start.

### Missing simulations (still)

S1 / M4 DN2540 real model and spread; S2 / M30 feedback switching clicks; S3 / M31 PI-4 steps
outside the mute; S4 / M2 open-load large-signal; S5 / M3 measured OT per channel; S6 / M1 LF shelf
vs coupling caps (master repo running the no-speaker matrix); S7 / M12 W23 field solve; S8 / M14
mute depth and board crosstalk (layout); S9 / M7 tube spread; S10 / M8 B+ decoupling with the
regulators; S11 / M9 PI input blocking; S12 / M11 return stage headroom; M10 send follower load.
Done in this pass: regulator thermal foldback with this board's loads; FX return law with the
RETURN_SIG bleed.

### Requirements still missing from SPECIFICATION.md

From the first pass (now N-numbers in review section 6): N15 loop gain -4 ± 1 dB (open item in
interfaces.md 14), N16 open-load margins, N18 W24 levels, N19 feedback switching, N20 unplugged W25,
N21 CCS tail, N22 mute depth, N23 fail-safe state, N24 send, N25 return, N26 dry leak, N28 W23
unplugged, N57 creepage, N60 cable lengths. New: "every relay function on the NO contacts; an
unpowered relay is the safe state" (FX / PI fail-safe wording, N23).

### Next steps

1. When U7 is decided: re-run `sim/pi_nfb/run_open_load.py` with the chosen values (feedback per
   channel, D18, after M3).
2. M30 click simulation with the G6K-2F-Y timing; M4 with a DN2540 model.
3. Layout feasibility in the rev A outline: J102 at the rear edge x 170-230, J302-J304 at the right
   end, HV copper and creepage, the regulator pours (about 30-50 K/W each), Q503 / Q506 on them.
4. Source the 51 BOM lines without an LCSC number; stock check.

---

## First pass (2026-11-21)

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
