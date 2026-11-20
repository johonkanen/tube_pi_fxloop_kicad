#!/usr/bin/env python3
"""Generate lib/tube_pi_fxloop.kicad_sym, the project symbol library (helpers: p2k.symgen).

Adapted from the power amp pilot. Pin numbers equal the IPC pin ids of reference/ (the Proteus ids,
except SERIES_MIX: Omron ids, IPC_PIN_IDS) (STATUS.md
"Phase 1 preparation"). All symbols are copied from the KiCad 10 standard library (flattened,
pins renumbered where needed). The Proteus pin definitions in ROOT.DSN (device `$PINSHORT` /
`$PINDEFAULT` records and the `*PINOUT` package tables, read by hand: p2k candidate 4 of the
pilot) are:
  2N3906 (TO92, no *PINOUT)      E=1 B=2 C=3            = KiCad Transistor_BJT:2N3906 (Q_PNP_EBC)
  J112 (TO92, no *PINOUT)        D=1 S=2 G=3            = KiCad Device:Q_NJFET_DSG (no KiCad J112)
  IRF820 (*PINOUT TO220)         G=1 D=2 S=3            = KiCad Transistor_FET:IRF740 (BUZ11, G D S)
  12AX7 (*PINOUT 9-PIN BELTON NOVAL)  A1=1 G1=2 K1=3 H1=4 H2=5 A2=6 G2=7 K2=8 HCT=9
                                 = KiCad Valve:ECC83 numbering (unit 1: 6 7 8, unit 2: 1 2 3,
                                   unit 3 heater: 4 5 9); the device symbol's own $PINDEFAULT
                                   numbers (A2=1 A1=6 ...) are overridden by the package table
  SW-SPDT (*PINOUT SPDT HOLES)   NO=1 NC=2 COM=3        KiCad Switch:SW_SPDT has 1=A (blade rests
                                   on it), 2=B (common), 3=C: renumbered 1->2, 2->3, 3->1
  G5V-2(HI) (*PINOUT G5V-2(HI))  AC1=1 COM1=2 NC1=3 DC1=4 DC2=5 COM2=6 NC2=7 AC2=8
                                   (AC = normally open, as the PDF draws pole 1; DC = coil)
                                 KiCad Relay:G5V-2 (Omron numbering 1/16 coil, 4/6/8 = COM/NC/NO
                                   pole 1, 13/11/9 pole 2), NOT renumbered since the design fixes
                                   2026-11-20 (user decision, Finding 15): the IPC pin ids of
                                   SERIES_MIX are renamed to the physical Omron pins instead
                                   (p2k_config.py IPC_PIN_IDS, tools/ipc356.py): Proteus 1-8 =
                                   Omron 9 13 11 16 1 4 6 8, i.e. the used pole is pole 2
  diodes, zeners                 A, K
  HITEMP10U50V (C8, C28)         +, -
  22µF 450V (C1, C36, C37; *PINOUT ELEC D16 R7.5)  + = 2, - = 1   -> symbol C_Polarized_21
  resistors, film capacitors     1, 2
  TERMINAL (*PINOUT C-120-60)    1
No power symbols: the IPC has no =POWER nets.

Valve pins are all `passive` (pilot candidate 9: KiCad's anode `output`, cathode `bidirectional`,
grid `input`, heater `power_in` give pin_to_pin / undriven ERC errors on resistor-only nets).
Pin 9 (HCT) is N/C on both tubes and the relay's pins 4 / 6 / 8 (Omron pole 1) are N/C: they stay
`passive` and get a no-connect flag in the schematic (as Proteus marks them N/C).

Run:  tools/gen_symbols.py           (needs the AppImage mount for the std libs)
      tools/gen_symbols.py --check   (fail if lib/tube_pi_fxloop.kicad_sym is not up to date)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "p2k"))  # proteus2kicad
from p2k.symgen import *  # noqa: E402,F401,F403
from p2k.symgen import run  # noqa: E402


def valve():
    # KiCad Valve:ECC83 (extends ECC81) has the noval numbers already; names -> the Proteus
    # names (KiCad: A/G/K per unit, heater F1 F1 F2); every pin passive.
    nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    names = {"1": "A1", "2": "G1", "3": "K1", "4": "H1", "5": "H2", "6": "A2", "7": "G2", "8": "K2", "9": "HCT"}
    sym = from_std("Valve", "ECC83", "12AX7", "U", "12AX7",
                   desc="12AX7 / 12AT7 noval dual triode; Proteus pin ids A1=1 G1=2 K1=3 H1=4 H2=5 "
                        "A2=6 G2=7 K2=8 HCT=9; unit 1 = triode 2 (6 7 8), unit 2 = triode 1 (1 2 3), "
                        "unit 3 = heater (4 5 9)",
                   pins={n: n for n in nums}, names=names, pin_types={"*": PAS})
    return sym


def build():
    return [
        from_std("Device", "R", "R", "R", "R"),
        from_std("Device", "C", "C", "C", "C"),
        from_std("Device", "C_Polarized", "C_Polarized", "C", "C", desc="Polarized capacitor, Proteus pins +/-",
                 pins={"1": "+", "2": "-"}, names={"+": "+", "-": "-"}),
        from_std("Device", "C_Polarized", "C_Polarized_21", "C", "C",
                 desc="Polarized capacitor, Proteus pins + = 2, - = 1 (package ELEC D16 R7.5)",
                 pins={"1": "2", "2": "1"}, names={"2": "+", "1": "-"}),
        from_std("Device", "D", "D", "D", desc="Diode, Proteus pins A/K", pins={"1": "K", "2": "A"}),
        from_std("Device", "D_Zener", "D_Zener", "D", desc="Zener diode, Proteus pins A/K", pins={"1": "K", "2": "A"}),
        from_std("Transistor_BJT", "2N3906", "2N3906", "Q", "2N3906",
                 desc="PNP transistor TO-92 (2N3906), Proteus ids 1=E 2=B 3=C"),
        from_std("Device", "Q_NJFET_DSG", "J112", "Q", "J112",
                 desc="N-channel JFET switch TO-92 (J112), Proteus ids 1=D 2=S 3=G"),
        from_std("Transistor_FET", "IRF740", "IRF820", "Q", "IRF820",
                 desc="500 V N-channel power MOSFET TO-220 (IRF820), Proteus ids 1=G 2=D 3=S"),
        valve(),
        from_std("Switch", "SW_SPDT", "SW_SPDT", "SW", "SW-SPDT",
                 desc="SPDT switch (Proteus SW-SPDT, package SPDT HOLES): 1=NO 2=NC 3=COM",
                 pins={"1": "2", "2": "3", "3": "1"}, names={"1": "NO", "2": "NC", "3": "COM"}),
        from_std("Relay", "G5V-2", "G5V-2", "K", "G5V-2(HI)",
                 desc="Omron G5V-2 DPDT relay, Omron pin numbers (coil 1 / 16, pole 1 COM 4 NC 6 NO 8, "
                      "pole 2 COM 13 NC 11 NO 9); KiCad Relay:G5V-2 unchanged"),
        from_std("Connector", "TestPoint", "PIN", "J", "PIN",
                 desc="Proteus TERMINAL: one pad (package C-120-60)"),
    ]


if __name__ == "__main__":
    sys.exit(run(build))
