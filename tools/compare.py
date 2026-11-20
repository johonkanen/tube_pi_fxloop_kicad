#!/usr/bin/env python3
"""p2k compare_netlists with a type-safe sort key (board-local wrapper, STATUS.md p2k candidates).

p2k.compare_netlists.natkey() returns mixed lists (['SEND', 1, ''] for SEND1), and pinkey() appends
'-' and the pin: the terminal SEND (['SEND', '-', 1]) against SEND1 (['SEND', 1, '', '-', 1])
compares the str '-' with the int 1 and sorted() raises TypeError as soon as both parts are drawn.
Here every token becomes a (kind, value) pair, so numbers and text never meet. Same arguments and
output as `p2k compare_netlists` (--sheet N, --allow-missing, -v)."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "p2k"))
from p2k import compare_netlists as cn  # noqa: E402


def natkey(s):
    return [(0, int(t), "") if t.isdigit() else (1, 0, t) for t in re.split(r"(\d+)", str(s))]


def pinkey(rp):
    return natkey(rp[0]) + [(1, 0, "-")] + natkey(rp[1])


cn.natkey, cn.pinkey = natkey, pinkey
sys.exit(cn.main())
