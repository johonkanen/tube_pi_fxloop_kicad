#!/usr/bin/env python3
"""Unlock the tracks and vias of the nets of some routing groups (routing.json): kipy unlock_groups.py BOARD GROUP..."""
import fnmatch
import json
import os
import sys

import pcbnew

cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "routing.json")))
pats = [p for g in sys.argv[2:] for p in cfg["groups"][g]]
b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for t in b.GetTracks():
    if any(fnmatch.fnmatchcase(t.GetNetname(), p) for p in pats):
        t.SetLocked(False)
        n += 1
b.Save(sys.argv[1])
print(f"unlocked {n} tracks / vias of {' '.join(sys.argv[2:])}")
