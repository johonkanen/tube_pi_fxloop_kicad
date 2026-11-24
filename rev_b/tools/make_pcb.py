#!/usr/bin/env python3
"""Start the rev B board: rev_b/kicad/tube_pi_fxloop_revb.kicad_pcb from the schematic netlist.

Run with KiCad's python:  tools/p2k/bin/kipy rev_b/tools/make_pcb.py [--force | --settings-only]

Pattern: tube_preamp_kicad rev_b/tools/make_pcb.py. What it does (decisions: STATUS.md "Layout"):
- outline, mounting holes and noval positions of rev A (kicad/tube_pi_fxloop.kicad_pcb at the repo
  root, same frame): chassis = (154.87 - x, 182.08 - y) (rev_b/layout/placement.py);
- 4 copper layers (inner = low-voltage signal layers, no plane), net classes and the clearance rules (kicad_pro + kicad_dru; IPC-2221B B2);
- every schematic part with its footprint, nets and schematic link (UUID);
- the parts whose position is an interface or mechanical decision placed: V1 / V2, H2-H10, every
  connector and tab (placement.py: the agreed pin-1 positions, interfaces.md 12.5), the two pass
  devices and their foldback transistors on the regulator pours;
- every other part parked below the board, by sheet, for rev_b/layout/place.sh.
It refuses to overwrite a board with tracks unless --force.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
RB = os.path.dirname(HERE)
REPO = os.path.dirname(RB)
sys.path.insert(0, os.path.join(RB, "layout"))
import placement as P  # noqa: E402
import make_groups as MG  # noqa: E402

PROJECT = "tube_pi_fxloop_revb"
K = os.path.join(RB, "kicad")
PCB = os.path.join(K, PROJECT + ".kicad_pcb")
PRO = os.path.join(K, PROJECT + ".kicad_pro")
SCH = os.path.join(K, PROJECT + ".kicad_sch")
REVA = os.path.join(REPO, "kicad", "tube_pi_fxloop.kicad_pcb")
KICAD_CLI = os.path.join(REPO, "tools", "p2k", "bin", "kicad-cli")
STOCK = os.path.join(os.environ.get("KICAD_MOUNT") or open(f"/tmp/p2k_kicad_mount.{os.getuid()}").read().strip(),
                     "share", "kicad", "footprints")

X0, Y0, X1, Y1 = P.OUTLINE_BOARD          # board frame; y0 = rear edge, y1 = front edge

from netclasses import HV, MV, HEATER, HIZ  # noqa: E402
HIZ_POUR = 1.0

DRU_HEAD = """(version 1)
# PI + FX rev B clearance rules (tools/make_pcb.py). Standard: IPC-2221B table 6-1, B2 (external
# conductors, uncoated, sea level to 3050 m), the same basis as the preamp rev B (review N57);
# pollution degree 2, functional insulation only (no safety barrier on this board; the chassis
# is reached only through the unplated standoff holes).
#   HV = nets at 280-480 V (raw rail, regulators, B+PI / B+FX and their decoupled rails, the PI
#        plates on W24), MV = 100-260 V (string midpoints, PI_REF divider, the return plate).
#   301-500 V: 2.5 mm; 151-300 V: 1.25 mm; 51-150 V: 0.6 mm. HV to HV and MV to MV (different nets):
#   0.6 mm (net class clearance): every pair of HV nets is within 150 V in normal use (raw 430-480 V
#   to B+FX 328 V is the widest), and the split strings put <= 130 V across a part in normal use
#   (160 V across an R3 part only into a shorted output, a fault).
# Unconnected pads (open relay contacts, spare switch pins) are left out.
(rule "HV to LV"
  (condition "A.NetClass == 'HV' && B.NetClass != 'HV' && B.NetClass != 'MV' && B.NetName != 'unconnected-*' && B.Pad_Type != 'NPTH, mechanical'")
  (constraint clearance (min 2.5mm)))
(rule "HV to MV"
  (condition "A.NetClass == 'HV' && B.NetClass == 'MV'")
  (constraint clearance (min 1.25mm)))
(rule "MV to LV"
  (condition "A.NetClass == 'MV' && B.NetClass != 'HV' && B.NetClass != 'MV' && B.NetName != 'unconnected-*' && B.Pad_Type != 'NPTH, mechanical'")
  (constraint clearance (min 1.25mm)))
# Board edges and the standoffs (chassis potential through the metal standoff and screw): HV copper
# 2.5 mm from the edge and from an M3 head (5.5 mm) at a hole, MV 1.25 mm. (KiCad: the last matching
# rule wins, so the general standoff rule comes first.)
(rule "HV to board edge"
  (condition "A.NetClass == 'HV'")
  (constraint edge_clearance (min 2.5mm)))
(rule "MV to board edge"
  (condition "A.NetClass == 'MV'")
  (constraint edge_clearance (min 1.25mm)))
(rule "LV to standoff"
  (condition "B.Pad_Type == 'NPTH, mechanical'")
  (constraint hole_clearance (min 1.2mm)))
(rule "MV to standoff"
  (condition "A.NetClass == 'MV' && B.Pad_Type == 'NPTH, mechanical'")
  (constraint hole_clearance (min 2.4mm)))
(rule "HV to standoff"
  (condition "A.NetClass == 'HV' && B.Pad_Type == 'NPTH, mechanical'")
  (constraint hole_clearance (min 3.65mm)))
# Inner layers: the copper is pulled back inside the laminate (no surface path to the screw); IPC-2221B
# B1 (internal conductors, 301-500 V: 0.25 mm), taken as 1.0 mm.
(rule "HV to standoff, inner layers"
  (layer inner)
  (condition "A.NetClass == 'HV' && B.Pad_Type == 'NPTH, mechanical'")
  (constraint hole_clearance (min 1.0mm)))
# High-impedance audio nets: ground pours keep away (stray capacitance; the preamp rule).
(rule "HIZ to pour"
  (condition "A.NetClass == 'HIZ' && B.Type == 'Zone'")
  (constraint clearance (min HIZ_POURmm)))
# Exceptions inside a part (generated: the part's own pad spacing is below the class rule;
# the part's rating covers it). One rule per part, at its own pad gap.
"""


def cls(n):
    base = n.split("/")[-1]
    for c, names in (("HV", HV), ("MV", MV), ("HEATER", HEATER), ("HIZ", HIZ)):
        if base in names:
            return c
    return "Default"


def need(ca, cb, na, nb):
    """Class rule between two different nets (mm), or 0."""
    if na == nb or na.startswith("unconnected") or nb.startswith("unconnected"):
        return 0.0
    s = {ca, cb}
    if s in ({"HV"}, {"MV"}):
        return 0.6
    if "HV" in s:
        return 1.25 if "MV" in s else 2.5
    if "MV" in s:
        return 0.0 if s == {"MV"} else 1.25
    return 0.0


def _outline(p):
    lay = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    ps = p.GetEffectivePolygon(lay)
    o = ps.Outline(0)
    return [(pcbnew.ToMM(o.CPoint(i).x), pcbnew.ToMM(o.CPoint(i).y)) for i in range(o.PointCount())]


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def pad_gap(a, b):
    """Edge-to-edge distance of two pads (polygon outlines), mm."""
    oa, ob = _outline(a), _outline(b)
    d = min(_seg_dist(p, ob[i], ob[(i + 1) % len(ob)]) for p in oa for i in range(len(ob)))
    return min(d, min(_seg_dist(p, oa[i], oa[(i + 1) % len(oa)]) for p in ob for i in range(len(oa))))


def own_pad_exceptions(board):
    out = []
    for f in board.GetFootprints():
        pads = [p for p in f.Pads() if p.GetNetname()]
        worst = None
        for i, a in enumerate(pads):
            for b in pads[i + 1:]:
                r = need(cls(a.GetNetname()), cls(b.GetNetname()), a.GetNetname(), b.GetNetname())
                if not r:
                    continue
                g = pad_gap(a, b)
                if g < r and (worst is None or g < worst[0]):
                    worst = (g, r, a.GetNetname().split("/")[-1], b.GetNetname().split("/")[-1])
        if worst:
            g, r, na, nb = worst
            ref = f.GetReference()
            out.append(f'# {ref} ({f.GetValue()}): {na} to {nb} {g:.2f} mm inside the part (class rule {r} mm)\n'
                       f'(rule "{ref} own pads"\n  (condition "A.memberOfFootprint(\'{ref}\') && B.memberOfFootprint(\'{ref}\')")\n'
                       f'  (constraint clearance (min {max(0.15, math.floor((g - 0.02) * 100) / 100):.2f}mm)))\n')
    return out


def stock(lib):
    return os.path.normpath(os.path.join(STOCK, lib + ".pretty"))


def netlist():
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "n.xml")
        subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", out, SCH],
                       check=True, capture_output=True)
        return ET.parse(out)


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def seg(board, x0, y0, x1, y1, layer, w=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(x0, y0))
    s.SetEnd(pt(x1, y1))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def box(board, x0, y0, x1, y1, layer, w=0.1):
    for a, b, c, d in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        seg(board, a, b, c, d, layer, w)


def note(board, s, x, y, size=1.2, layer=pcbnew.Cmts_User):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)


def _ring(board, x, y, r, layers, vias):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    o = z.Outline()
    o.NewOutline()
    for i in range(32):
        a = 2 * math.pi * i / 32
        o.Append(mm(x + r * math.cos(a)), mm(y + r * math.sin(a)))
    board.Add(z)


def hole_keepouts(board, x, y):
    """Track / via keep-outs round a standoff hole: outer layers 5.3 mm (HV copper 2.5 mm from the M3 head;
    the router does not apply class-scoped hole rules), inner layers 2.9 mm (LV only there)."""
    _ring(board, x, y, 5.3, (pcbnew.F_Cu, pcbnew.B_Cu), True)
    _ring(board, x, y, 2.9, (pcbnew.In1_Cu, pcbnew.In2_Cu), False)


def project_settings(board=None):
    pro = json.load(open(PRO))
    classes = [
        {"name": "Default", "clearance": 0.2, "track_width": 0.3, "via_diameter": 0.8, "via_drill": 0.3, "priority": 2147483647},
        {"name": "HV", "clearance": 0.6, "track_width": 0.5, "via_diameter": 1.0, "via_drill": 0.4, "priority": 0},
        {"name": "MV", "clearance": 0.6, "track_width": 0.4, "via_diameter": 0.9, "via_drill": 0.4, "priority": 1},
        {"name": "HEATER", "clearance": 0.4, "track_width": 1.5, "via_diameter": 1.2, "via_drill": 0.6, "priority": 2},
        {"name": "HIZ", "clearance": 0.2, "track_width": 0.3, "via_diameter": 0.8, "via_drill": 0.3, "priority": 3},
    ]
    for c in classes:
        c.update({"pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"})
    pats = [{"netclass": c, "pattern": p} for c, names in (("HV", HV), ("MV", MV), ("HEATER", HEATER), ("HIZ", HIZ))
            for n in names for p in (n, "*/" + n)]
    pro["net_settings"] = {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                           "netclass_assignments": None, "netclass_patterns": pats}
    json.dump(pro, open(PRO, "w"), indent=2)
    dru = DRU_HEAD.replace("HIZ_POUR", f"{HIZ_POUR}")
    if board is not None:
        dru += "".join(own_pad_exceptions(board))
    open(os.path.join(K, PROJECT + ".kicad_dru"), "w").write(dru)


def load_fp(lib_id):
    lib, name = lib_id.split(":")
    path = os.path.join(RB, "lib", PROJECT + ".pretty") if lib == PROJECT else stock(lib)
    f = pcbnew.FootprintLoad(path, name)
    if f is None:
        raise SystemExit(f"footprint {lib_id} not found in {path}")
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    return f


def crtyd(f):
    c = f.GetCourtyard(pcbnew.F_CrtYd if not f.IsFlipped() else pcbnew.B_CrtYd)
    b = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
    return [pcbnew.ToMM(v) for v in (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom())]


def place_pin1(f, rot, pin1_chassis):
    f.SetOrientationDegrees(rot)
    f.SetPosition(pt(0, 0))
    p1 = [p for p in f.Pads() if p.GetNumber() == "1"][0].GetPosition()
    tx, ty = P.to_board(*pin1_chassis)
    f.SetPosition(pcbnew.VECTOR2I(mm(tx) - p1.x, mm(ty) - p1.y))


def place_at(f, rot, chassis_xy):
    f.SetOrientationDegrees(rot)
    f.SetPosition(pt(*P.to_board(*chassis_xy)))


def main():
    if "--settings-only" in sys.argv:
        b = pcbnew.LoadBoard(PCB) if os.path.exists(PCB) else None
        project_settings(b)
        print(f"{PRO}, {PROJECT}.kicad_dru written")
        return
    if os.path.exists(PCB) and "--force" not in sys.argv:
        b = pcbnew.LoadBoard(PCB)
        if len(b.GetTracks()):
            raise SystemExit(f"{PCB} has tracks: not overwritten (use --force)")
    project_settings()
    reva = pcbnew.LoadBoard(REVA)
    rev_a = {f.GetReference(): f for f in reva.GetFootprints()}
    board = pcbnew.NewBoard(PCB)
    board.SetCopperLayerCount(4)   # 2 outer (2 oz option) + 2 inner signal layers, no plane (STATUS: why 4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_MinClearance = mm(0.2)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.5)
    ds.m_HoleClearance = mm(0.3)
    ds.m_HoleToHoleMin = mm(0.5)
    box(board, X0, Y0, X1, Y1, pcbnew.Edge_Cuts, 0.1)

    t = netlist()
    nets = {}
    for n in t.iter("net"):
        ni = pcbnew.NETINFO_ITEM(board, n.get("name"))
        board.Add(ni)
        for nd in n.iter("node"):
            nets[(nd.get("ref"), nd.get("pin"))] = ni

    parked, fps = {}, {}
    for c in t.iter("comp"):
        ref = c.get("ref")
        f = load_fp(c.findtext("footprint"))
        f.SetReference(ref)
        f.SetValue(c.findtext("value"))
        sym = {fld.get("name"): fld.text or "" for fld in c.iter("field")}
        for fd in f.GetFields():
            if fd.GetName() in ("Datasheet", "Description"):
                fd.SetText(sym.get(fd.GetName(), ""))
        sp = c.find("sheetpath")
        f.SetPath(pcbnew.KIID_PATH(sp.get("tstamps") + c.findtext("tstamps")))
        f.SetSheetname(sp.get("names"))
        f.SetSheetfile(c.find("property[@name='Sheetfile']").get("value"))
        if any(p.get("name") == "dnp" for p in c.iter("property")) or "DNP" in (c.findtext("value") or ""):
            f.SetDNP(True)
        for p in f.Pads():
            ni = nets.get((ref, p.GetNumber()))
            if ni is not None:
                p.SetNet(ni)
        board.Add(f)
        fps[ref] = f
        parked.setdefault(sp.get("names"), []).append(f)

    fixed = set()
    for v, a in (("V1", "U4"), ("V2", "U5")):            # rev A sockets: solder side, 180 deg
        f, ra = fps[v], rev_a[a]
        f.SetPosition(ra.GetPosition())
        f.Flip(ra.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientation(ra.GetOrientation())
        fixed.add(v)
    # V2 uses the socket variant with pin 6 on a 3.8 mm pad (make_lib.py): 3.66 mm from H3, 2.52 mm from an M3 head
    for h, (bx, by) in P.HOLES_BOARD.items():
        if h in P.HOLE_DROPPED:
            continue
        m = load_fp("MountingHole:MountingHole_3.2mm_M3")
        m.SetReference(h)
        m.SetValue("M3 (3.2 NPTH, no net)")
        m.SetPosition(pt(bx, by))
        m.SetBoardOnly(True)
        board.Add(m)
        hole_keepouts(board, bx, by)
    for ref, (_cable, _mate, _lib, _name, side, rot, pin1, _note) in P.CONNECTORS.items():
        place_pin1(fps[ref], rot, pin1)
        fixed.add(ref)
    for ref, (rot, xy) in P.PINNED.items():
        place_at(fps[ref], rot, xy)
        fixed.add(ref)
    for ref, (rot, xy) in P.PINNED_PIN1.items():
        place_pin1(fps[ref], rot, xy)
        fixed.add(ref)

    bside = {r for _n, refs, _z, _near, _w in MG.B_GROUPS for r in refs}
    for r in bside:                                # LV 0603 parts on the plate side (make_groups.B_GROUPS)
        fps[r].Flip(fps[r].GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    # parked: below the board (board y > Y1 is in front of the front edge in the chassis), by sheet
    y = Y1 + 12.0
    for sheet in sorted(parked):
        items = sorted((f for f in parked[sheet] if f.GetReference() not in fixed),
                       key=lambda f: (str(f.GetFPID().GetLibItemName()), f.GetReference()))
        if not items:
            continue
        note(board, f"Sheet {sheet.strip('/')}: to place", X0, y - 4.0, 2.0)
        x, rowh = X0, 0.0
        for f in items:
            f.SetOrientationDegrees(0)
            l, t_, r, b = crtyd(f)
            w, h = r - l, b - t_
            if x + w > X1:
                x, y = X0, y + rowh + 4.0
                rowh = 0.0
            p = f.GetPosition()
            f.SetPosition(pcbnew.VECTOR2I(p.x + mm(x - l), p.y + mm(y - t_)))
            x += w + 4.0
            rowh = max(rowh, h)
        y += rowh + 12.0

    for name, (cx0, cy0, cx1, cy1), text in P.ZONES:
        bx0, by0, bx1, by1 = P.rect_board(cx0, cy0, cx1, cy1)
        box(board, bx0, by0, bx1, by1, pcbnew.Cmts_User, 0.15)
        note(board, name, bx0 + 0.5, by0 + 1.5, 1.2)
    project_settings(board)
    hvrefs = sorted({f.GetReference() for f in board.GetFootprints() for p in f.Pads()
                     if cls(p.GetNetname()) in ("HV", "MV") and f.GetReference()[0] not in "JVH"})
    json.dump(hvrefs, open(os.path.join(RB, "layout", "hv_refs.json"), "w"))   # for make_groups' edge strips
    pcbnew.SaveBoard(PCB, board)
    print(f"{PCB}: {len(fps)} parts ({len(fixed)} placed), {len(nets)} pin-net links")


if __name__ == "__main__":
    main()
