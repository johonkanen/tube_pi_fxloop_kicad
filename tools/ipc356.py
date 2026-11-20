#!/usr/bin/env python3
"""p2k ipc356 with board-local pin id renaming (IPC_PIN_IDS in p2k_config.py).

Same arguments and output as `p2k ipc356` (--check, --ipc, --out). After the shared parser has read
the Proteus IPC-D-356A file, the pin ids of the refdes in IPC_PIN_IDS ({KiCad refdes: {Proteus pin:
KiCad pin}}) are renamed, so reference/ipc356_pads.json and the cheat sheets carry the KiCad pin ids
and every check that reads them (check_symbols, compare, check_footprints, check_board, ipc356_diff,
check_pin_order, ...) compares against those. Positions, nets and every other field stay as Proteus
wrote them. Fails unless every IPC pad of a listed refdes is renamed (and only those), the targets are
unique, and every listed refdes and Proteus pin exists.

Used for the relay SERIES_MIX: Proteus G5V-2(HI) pads 1-8 -> the physical Omron G5V-2 pins (user
decision 2026-11-20, Finding 15; STATUS.md "Design fixes 2026-11-20"). The shared tool has no such
key (STATUS.md "p2k candidates" 24).

Usage: python3 tools/ipc356.py [--check]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "p2k"))
from p2k import ipc356  # noqa: E402

RENAME = getattr(ipc356.CFG, "IPC_PIN_IDS", {}) or {}
_parse = ipc356.parse


def parse(path):
    net_names, pads = _parse(path)
    errors = []
    for ref, ren in RENAME.items():
        mine = [p for p in pads if p["kind"] == "pad" and p["refdes"] == ref]
        if not mine:
            errors.append(f"IPC_PIN_IDS: refdes {ref} not in the IPC file")
        pins = {p["pin"] for p in mine}
        if pins != set(ren):
            errors.append(f"IPC_PIN_IDS[{ref}]: IPC pins {sorted(pins)}, listed {sorted(ren)}")
        if len(set(ren.values())) != len(ren):
            errors.append(f"IPC_PIN_IDS[{ref}]: target pin ids not unique")
        for p in mine:
            p["pin"] = ren.get(p["pin"], p["pin"])
    if errors:
        raise SystemExit("ipc356: " + "; ".join(errors))
    return net_names, pads


ipc356.parse = parse
if __name__ == "__main__":
    rc = ipc356.main()
    if RENAME and rc == 0:
        print("ipc356: pin ids renamed (IPC_PIN_IDS): " + "; ".join(
            f"{r} " + " ".join(f"{a}->{b}" for a, b in ren.items()) for r, ren in RENAME.items()))
    sys.exit(rc)
