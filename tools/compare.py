#!/usr/bin/env python3
"""p2k compare_netlists with a type-safe sort key (board-local wrapper, STATUS.md p2k candidates).

p2k.compare_netlists.natkey() returns mixed lists (['SEND', 1, ''] for SEND1), and pinkey() appends
'-' and the pin: the terminal SEND (['SEND', '-', 1]) against SEND1 (['SEND', 1, '', '-', 1])
compares the str '-' with the int 1 and sorted() raises TypeError as soon as both parts are drawn.
Here every token becomes a (kind, value) pair, so numbers and text never meet. Same arguments and
output as `p2k compare_netlists` (--sheet N, --allow-missing, -v).

Phase 4 addition: compare_netlists treats every pin of a KiCad net named `unconnected-(...)` as a
singleton, so two no-connect pins wired to each other (KiCad then puts both in ONE such net) pass
as two N/C pins (negative test: SERIES_MIX pins 7 and 8 joined by a wire -> "compare: OK"). Here the
netlist is also required to have exactly one pin in every `unconnected-(...)` net."""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "p2k"))
from p2k import compare_netlists as cn  # noqa: E402


def natkey(s):
    return [(0, int(t), "") if t.isdigit() else (1, 0, t) for t in re.split(r"(\d+)", str(s))]


def pinkey(rp):
    return natkey(rp[0]) + [(1, 0, "-")] + natkey(rp[1])


_load_kicad, _joined = cn.load_kicad, []


def load_kicad(path):
    for net in ET.parse(path).getroot().iter("net"):
        nodes = [(n.get("ref"), n.get("pin")) for n in net.findall("node")]
        if net.get("name", "").startswith("unconnected-(") and len(nodes) != 1:
            _joined.append((net.get("name"), nodes))
    return _load_kicad(path)


cn.natkey, cn.pinkey, cn.load_kicad = natkey, pinkey, load_kicad
rc = cn.main()
for name, nodes in _joined:
    print(f"compare: ERROR KiCad net {name} joins {len(nodes)} pins: "
          + " ".join(f"{r}-{p}" for r, p in sorted(nodes, key=pinkey)) + " (no-connect pins wired together)")
if _joined:
    print("compare: FAILED (unconnected-(...) nets with more than one pin)")
sys.exit(1 if _joined else rc)
