# PI + FX loop rev B: first-draft schematic

The next PI + FX loop board of the 3-channel all-tube head, designed from the simulations and
documents of [tube_amplifier_kicad](https://github.com/johonkanen/tube_amplifier_kicad):
`sim/pi_nfb` (the reference for the PI and the feedback), `sim/fx_loop`, `docs/preamp_regulator.md`
and the interface contract `docs/interfaces.md` (IF-1, IF-1.1 for W23). Rev A (the 2010 board,
converted) at the repo root is not touched; `rev_b/` is its own p2k board root
(`p2k_config.py`, PROJECT `tube_pi_fxloop_revb`), the same pattern as tube_preamp_kicad `rev_b/`.

Status and the interface check: [STATUS.md](STATUS.md).

## Build

```
python3 rev_b/tools/make_lib.py          # lib/ from KiCad's stock symbol libraries (flattened)
python3 rev_b/tools/make_project.py      # project, root sheet, empty sub-sheets
python3 rev_b/tools/sheets/draw_all.py   # draws the five sheets (overwrites them)
python3 rev_b/tools/verify.py            # KiCad's netlist == the intended connections
rev_b/../tools/p2k/bin/kicad-cli sch erc rev_b/kicad/tube_pi_fxloop_revb.kicad_sch
```

The sheets are generated: edit `tools/sheets/draw_all.py`, not the `.kicad_sch` files, until the
draft is frozen. Drawing style is netlist-first (parts on a grid, a stub and a label on every pin),
exact for ERC and the netlist; a tidy layout pass comes later. **ERC: 0 errors, 0 warnings**
(KiCad 10). `verify.py`: 154 intended nets, 0 mismatches. **235 parts**: 124 R, 53 C, 21
transistors / JFETs, 9 diodes, 8 relays, 7 ICs, 11 connectors, 2 tubes. Footprints not assigned.

| Sheet | Contents |
|---|---|
| 01 | J101 PRE IN (W22-b); 2.2M + 100n into the send cathode follower (V1 pins 1-3), whose grid is the >= 1 Mohm input buffer; SEND_SRC (1k) and the dry divider 47k / 4.7k; J102 FX ribbon (W23-a); return input 220n + 100k, the 0 / -20 dB pad (11k shunt switched by a JFET from the rear switch on PAD_A); series-shunt JFET mixer (100k branches, 220k); return stage (V1 pins 6-8, 680R unbypassed); 470n to the attenuator |
| 02 | PI-4 attenuator: five L-sections (1, 2, 4, 8, 16 dB, Z0 49.9k) on G6K-2 relays, energised = section in; PI: 10n input, 12AX7 LTP (V2), DN2540 CCS tail with a selected source resistor, equal 100k plates, 22n second-grid cap to the feedback node; J201 DRIVE (W24-a) with the soft-tied ground |
| 03 | J301 FB (W25-b), FB_RTN 0R to AGND (the OT secondary's one reference); per channel: relay at the 8 ohm end (both poles in parallel), 1M bleed, Rf 100k + Cf 22p, Cres 22n, presence 1k and 22n, the 10-pin pot ribbon J302-J304 (W30-W32-b), NJFET T-switch (series, series, shunt) to the common node; Rbot 4.7k and a DNP step network on the common node |
| 04 | J401 CONTROL (W13-b, template); MCP23S17 (map of interfaces.md 7.2); 2x 74LVC1G11 (branch enable = FX_x AND FX_UNMUTE AND MUTE_ALL_N); 3x DG412 (10 of 12 switches: series gates pulled to -15 V and switched to GND, shunt gates pulled to GND and switched to -15 V); ULN2803A for the 8 relays; DGND island (GNDD) and its soft tie |
| 05 | J501 RAW HV (W03-b); B+PI (3x 130 V, about 388 V) and B+FX (150 + 180 V, about 328 V) regulators as preamp_regulator.md; RC decoupling (2.2k / 22u PI; 10k / 22u per FX triode); heater tabs J502 in (W07-b), J503 out (W08-a), floating; tube heaters |

## Simulations (rev_b/sim, copies of the master repo's sim folders with the rev B changes)

- `sim/pi_nfb/run_open_load.py` → `results/open_load.md`: the PI loop margins with the rev B caps,
  the CCS tail and equal plates, with the speaker, an 8 ohm resistor, **no load** and a 100 ohm
  safety load. Result: loaded margins are as pi_nfb found (LF 56-61°, gain margin 15-17 dB), but
  **with no speaker the LF phase margin drops to 23-28° and the gain margin to about 8 dB** (the
  loop gain jumps to 26-28 dB at 1 kHz). 100n power coupling caps (220k grid leaks) give 37° /
  11.7 dB; a larger second-grid cap alone gives little (27° / 10 dB); a 100 ohm safety load little.
- `sim/fx_loop/run_fx_revb.py` → `results/fx_revb.md`: the FX loop re-derived for the 140 kohm
  preamp source and the rear pots / pad (IF-1.1): bypass gain preamp → PI input -3.8 dB (-3 dB at
  6 Hz and 21.5 kHz), input 1.5 Mohm at 1 kHz, send law, return law (log vs linear), headroom,
  noise (95 dB re nominal at every return-pot position), W23 send-to-return coupling (the leak is
  -43 dB at 1 kHz with 1 pF at mid pot settings: see STATUS.md), and the PI-4 attenuator steps
  (error ≤ 0.16 dB).

## Draft decisions (this board's own)

- **Input buffer = the send cathode follower.** Its bootstrapped grid gives 1.5 Mohm and a few pF;
  2.2M to GND defines the line. No pad in front of it, so the preamp sees no extra load.
- **Overall gain -3.8 dB** (preamp out → PI input, attenuator 0 dB): 20 V peak from the preamp
  reaches the PI at 13 V, under the 18 V limit of PI-4; 10 V nominal gives 6.4 V, +7 dB over the
  5 % onset at 400 V. Set by the dry divider (P = -22 dB) and the return stage's 680R unbypassed.
- **Series JFET gates: 100k / 10n, then 1M to the gate.** With the gate held at AC ground by the
  10n the gate junction conducts on the negative peaks (3 % THD at 9 V in); with the 1M the gate
  floats with the channel (1 % at 9 V, as fx_loop). Used in the mixer and the feedback T-switches.
- **Pad on a JFET, PAD_A as a DC line.** The rear switch grounds PAD_A (pulled to -15 V through 1M
  here, 100n at the connector); the JFET switches the 11k shunt. No audio node crosses the ribbon
  on PAD_A, and the rear I/O still sees a plain switch between PAD_A and PAD_B (GND).
- **PI-4 attenuator: relays** (decided here, interfaces.md 7.2 asks this board): the node carries
  up to 13 V peak (JFETs need under 2-8 V), JFETs after a fixed pad would cost the PI drive
  headroom, and latching relays would need 10 control lines (2 spare). Five G6K-2 relays,
  energised = section in, so 0 dB (full power) has all five off.
- **CCS: DN2540** (LND150's Idss can be under 2 mA), source resistor selected for 2.0 mA.
- **Regulator pass devices: insulated TO-220F (STF4N80K5 class)**, so they can be clamped to the
  chassis plate through a spacer: a shorted output dissipates 3.5-4.3 W continuously (foldback
  current 8-10 mA does not blow the 100 mA RAW_SS fuse).
