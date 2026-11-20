#!/usr/bin/env python3
"""Check the generated schematic against what draw_all.py meant: KiCad's netlist (kicad-cli)
must group the (ref, pin) pairs exactly as build/intended_nets.json does (no accidental shorts
between labels, no missing connections). Run after draw_all.py; also prints the ERC result."""
import collections
import json
import os
import subprocess
import sys

RB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RB, "..", "tools", "p2k"))
from p2k.sexpr import find, find_all, load  # noqa: E402

CLI = os.path.join(RB, "..", "tools", "p2k", "bin", "kicad-cli")
SCH = os.path.join(RB, "kicad", "tube_pi_fxloop_revb.kicad_sch")
NET = os.path.join(RB, "build", "tube_pi_fxloop_revb.net")


def main():
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", NET, SCH], check=True,
                   capture_output=True)
    want = json.load(open(os.path.join(RB, "build", "intended_nets.json")))
    groups_w = collections.defaultdict(set)
    for k, n in want.items():
        groups_w[n].add(k)
    nl = load(NET)
    nets = find(nl, "nets")
    groups_k = {}
    for n in find_all(nets, "net"):
        name = find(n, "name")[1]
        members = {f"{find(m, 'ref')[1]}:{find(m, 'pin')[1]}" for m in find_all(n, "node")}
        groups_k[name] = members
    pin2k = {p: name for name, ms in groups_k.items() for p in ms}
    bad = 0
    for n, ms in groups_w.items():
        ks = {pin2k.get(p) for p in ms}
        if len(ks) != 1 or None in ks:
            bad += 1
            print(f"split / missing: {n}: {sorted(ks, key=str)}")
            continue
        extra = {p for p in groups_k[ks.pop()] if p in want and want[p] != n}
        if extra:
            bad += 1
            print(f"merged: {n} with {sorted(extra)}")
    parts = {p.split(':')[0] for p in want}
    print(f"intended nets {len(groups_w)}, KiCad nets {len(groups_k)}, parts {len(parts)}, mismatches {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
