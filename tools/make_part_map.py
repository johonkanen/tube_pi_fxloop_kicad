#!/usr/bin/env python3
"""Generate lib/part_map.csv: refdes -> PDF page, symbol, value, Proteus device and package.

Adapted from the power amp pilot (~/dev/tube_power_amp_kicad/tools/make_part_map.py).
Sources (STATUS.md "Phase 1 preparation"):
  refdes   reference/ipc356_pads.json (`refdes` = KiCad name, `refdes_proteus` = Proteus name);
           every part of the PDF has pads (Phase 0), so there is no OFF_BOARD table
  value    schematic value from ROOT.DSN in source/poweri.pdsprj (= the PDF), read with the
           FULL refdes set
  device, package   layout record in ROOT.LYT, read with lyt_parts() below (board-local
           copy of p2k.pdsprj.lyt_parts, p2k candidate 5: the shared reader drops the
           one-character refdes `A` and Latin-1 strings and then fails with "two layout
           records for -6")
  sheet    PDF page whose text layer has the refdes; PAGE_OVERRIDES for the ambiguous ones
  lib_id   SYMBOL_BY_DEVICE (Proteus device -> lib/tube_pi_fxloop.kicad_sym symbol)

C1, C36, C37 (p2k candidate 1 of the pilot): value `22µF 450V` with a Latin-1 µ, which
p2k.pdsprj.dsn_values drops (None). The value is the PDF text (LATIN1_PARTS); the script
fails if dsn_values starts reading it (then drop the override). Device / package come from
the board-local lyt_parts(), which decodes Latin-1.

  tools/make_part_map.py           write lib/part_map.csv
  tools/make_part_map.py --check   fail if lib/part_map.csv is not up to date
"""
import csv
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "p2k"))  # proteus2kicad
from p2k import board, pdftext, pdsprj  # noqa: E402

PRJ = board.path("source", "poweri.pdsprj")
PDF = board.path("source", "schematic_pdf", "pi_fx_loop.PDF")
OUT = board.path("lib", "part_map.csv")
LIB = board.config().PROJECT

C, CP, R = "C", "C_Polarized", "R"
SYMBOL_BY_DEVICE = {
    "22N XICON": C, "47N XICON": C, "100N XICON": C, "MMK J04 5MM": C, "1UF SOLEN FAST": C,
    "HITEMP10U50V": CP,                 # C8, C28: Proteus pins + / -
    "22µF 450V": "C_Polarized_21",      # C1, C36, C37: package ELEC D16 R7.5 has pins + = 2, - = 1
    "MINRES100K": R, "METALFILM1K": R, "RES": R,
    "1N4148": "D", "1N4001": "D",
    "BZV85C12": "D_Zener", "1M180ZS5": "D_Zener", "1N4764A": "D_Zener",
    "2N3906": "2N3906", "J112": "J112", "IRF820": "IRF820",
    "12AX7": "12AX7",                   # U4 (value 12AT7) and U5
    "SW-SPDT": "SW_SPDT",
    "G5V-2(HI)": "G5V-2",
    "TERMINAL": "PIN",
}

# Values with a Latin-1 µ that p2k.pdsprj.dsn_values cannot read: PDF text (page 2).
LATIN1_PARTS = {
    "C1": "22µF 450V",
    "C36": "22µF 450V",
    "C37": "22µF 450V",
}

# Refdes whose PDF text-layer hits are ambiguous (resolved on the page renders):
PAGE_OVERRIDES = {
    "A": 2,     # terminal at R28 (page 2); "A" on pages 2 and 4 is also the net label A
    "C'": 2,    # terminal at R27; net label C' on pages 2 and 4
    "D'": 2,    # terminal at R29; net label D' on pages 2 and 4
}

FIELDS = ["refdes", "sheet", "lib_id", "value", "device", "package", "proteus_refdes"]


def _strings(data):
    """Like p2k.pdsprj._strings, but runs of one character and Latin-1 bytes are kept."""
    out = []
    for run in re.findall(rb"[\x20-\x7e\t\xa0-\xff]+", data):
        out += [t.decode("latin-1") for t in run.split(b"\t") if t]
    return out


def lyt_parts(prj, refs):
    """p2k.pdsprj.lyt_parts with _strings() above (p2k candidate 5)."""
    toks = _strings(pdsprj._read(prj, "ROOT.LYT"))
    out = {}
    for k, t in enumerate(toks):
        if t not in ("EID", "EID_A"):
            continue
        tail = toks[k + 1:k + 20]
        pkg = next((b for a, b in zip(tail, tail[1:]) if a == "PACKAGE"), None)
        j = next((j for j in range(k - 1, max(-1, k - 600), -1)
                  if toks[j] in refs and j + 3 < k and (pkg is None or toks[j + 3].startswith(pkg))), None)
        if j is None:
            continue
        rec = [t.strip() for t in toks[j:k]]
        if rec[0] in out:
            raise ValueError(f"lyt_parts: two layout records for {rec[0]}")
        out[rec[0]] = {"value": rec[1], "device": rec[2], "package": pkg or rec[3],
                       "nets": [n.rstrip("\xff") for n in rec[4:]]}
    return out


def build():
    ipc = json.load(open(board.path("reference", "ipc356_pads.json")))
    kicad = {}
    for p in ipc["pads"]:
        if p["kind"] == "pad":
            kicad[p["refdes_proteus"]] = p["refdes"]
    refs = set(kicad)
    values = pdsprj.dsn_values(PRJ, refs)
    parts = lyt_parts(PRJ, refs)
    pages = pdftext.refdes_pages(pdftext.pdf_words(PDF), refs)
    errors = []
    rows = []
    for ref in sorted(refs):
        page = PAGE_OVERRIDES.get(ref)
        if page is None:
            if len(pages[ref]) != 1:
                errors.append(f"{ref}: PDF pages {pages[ref]} (add to PAGE_OVERRIDES)")
                continue
            page = pages[ref][0]
        elif page not in pages[ref]:
            errors.append(f"{ref}: PAGE_OVERRIDES page {page} not among the PDF hits {pages[ref]}")
        if ref not in parts:
            errors.append(f"{ref}: no layout record in ROOT.LYT")
            continue
        dev, pkg = parts[ref]["device"], parts[ref]["package"]
        if ref in LATIN1_PARTS:
            if values.get(ref) is not None:
                errors.append(f"{ref}: pdsprj now reads {values.get(ref)!r}: drop LATIN1_PARTS")
            if parts[ref]["value"] != LATIN1_PARTS[ref]:
                errors.append(f"{ref}: layout value {parts[ref]['value']!r} != LATIN1_PARTS")
            value = LATIN1_PARTS[ref]
        else:
            value = values.get(ref)
        if not value:
            errors.append(f"{ref}: no schematic value")
            continue
        if dev not in SYMBOL_BY_DEVICE:
            errors.append(f"{ref}: no symbol for Proteus device {dev!r}")
            continue
        rows.append({"refdes": kicad[ref], "sheet": page, "lib_id": f"{LIB}:{SYMBOL_BY_DEVICE[dev]}",
                     "value": value, "device": dev, "package": pkg,
                     "proteus_refdes": ref if ref != kicad[ref] else ""})
    for ref in sorted(set(PAGE_OVERRIDES) - refs):
        errors.append(f"PAGE_OVERRIDES: {ref} is not a refdes")
    for ref in sorted(set(LATIN1_PARTS) - refs):
        errors.append(f"LATIN1_PARTS: {ref} is not a refdes")
    for dev in sorted(set(SYMBOL_BY_DEVICE) - {r["device"] for r in rows}):
        errors.append(f"SYMBOL_BY_DEVICE: device {dev!r} is not used")
    if errors:
        sys.exit("make_part_map:\n  " + "\n  ".join(errors))
    key = lambda r: (r["sheet"], [(0, int(t), "") if t.isdigit() else (1, 0, t)
                                  for t in re.findall(r"\d+|\D+", r["refdes"])])
    rows.sort(key=key)
    buf = io.StringIO()
    buf.write("# Generated by tools/make_part_map.py - do not edit. sheet = Proteus PDF page;"
              " value = schematic value (ROOT.DSN; C1/C36/C37 from the PDF); device/package = Proteus layout record\n")
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue(), rows


def main():
    text, rows = build()
    rel = os.path.relpath(OUT, board.root())
    per = {}
    for r in rows:
        per[r["sheet"]] = per.get(r["sheet"], 0) + 1
    summary = f"{len(rows)} parts; per sheet " + " ".join(f"{s}:{n}" for s, n in sorted(per.items()))
    if "--check" in sys.argv:
        if not os.path.exists(OUT) or open(OUT, encoding="utf-8").read() != text:
            print(f"make_part_map: {rel} is out of date, run tools/make_part_map.py")
            return 1
        print(f"make_part_map: {rel} up to date, {summary}")
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    print(f"wrote {rel}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
