#!/usr/bin/env python3
"""Concept assembly v0 (envelopes only, NOT printable parts yet).

Run:  python3 cad/model/build.py
Writes cad/out/concept_v0.step and cad/out/concept_v0_{iso,top,side}.svg,
and prints geometric checks. Exits non-zero if a check fails.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(__file__))
from params import *  # noqa: F401,F403
import params as P

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
R = BODY_D / 2


def box(cx, cy, z0, lx, ly, h):
    return cq.Workplane("XY").box(lx, ly, h, centered=(True, True, False)).translate((cx, cy, z0))


def cyl_y(cx, cy, cz, d, length):
    """cylinder with axis along y, centred at (cx, cy, cz)"""
    return (cq.Workplane("XZ").circle(d / 2).extrude(length / 2, both=True)
            .translate((cx, cy, cz)))


def build():
    parts = {}
    plate = cq.Workplane("XY").circle(R).extrude(PLATE_T)
    c = WHEEL_WELL_CLEAR
    well_y0 = WHEEL_Y - WHEEL_W / 2 - c
    for s in (1, -1):  # wheel wells: slot from inside the wheel to the rim
        well = box(0, s * (well_y0 + R) / 2, -1, WHEEL_D + 2 * c, R - well_y0, PLATE_T + 2)
        plate = plate.cut(well)
    parts["base_plate"] = (plate.translate((0, 0, PLATE_Z)), "burlywood")
    axle_z = WHEEL_D / 2
    for s, tag in ((1, "L"), (-1, "R")):
        parts[f"wheel_{tag}"] = (cyl_y(0, s * WHEEL_Y, axle_z, WHEEL_D, WHEEL_W), "gray20")
        inner = WHEEL_Y - WHEEL_W / 2 - 3
        parts[f"drive_motor_{tag}"] = (
            cyl_y(0, s * (inner - DRIVE_MOTOR_L / 2), axle_z, DRIVE_MOTOR_D, DRIVE_MOTOR_L), "lightsteelblue")
    parts["caster"] = (cq.Workplane("XY").sphere(CASTER_D / 2).translate((CASTER_X, 0, CASTER_D / 2)), "gray30")

    for s, tag in ((1, "L"), (-1, "R")):
        parts[f"pad_{tag}"] = (cq.Workplane("XY").circle(PAD_D / 2).extrude(PAD_H)
                               .translate((PAD_X, s * PAD_Y, 0)), "lightskyblue")
        parts[f"mop_motor_{tag}"] = (cq.Workplane("XY").circle(DRIVE_MOTOR_D / 2).extrude(MOP_MOTOR_L)
                                     .translate((PAD_X, s * PAD_Y, PLATE_Z + PLATE_T)), "lightsteelblue")

    for name, d, col in (("tank", TANK, "lightblue"), ("battery", BATTERY, "gold"),
                         ("electronics", ELECTRONICS, "palegreen")):
        parts[name] = (box(d["x"], d["y"], PLATE_Z + PLATE_T, d["lx"], d["ly"], d["h"]), col)
    parts["top_deck"] = (cq.Workplane("XY").circle(R - 10).extrude(3).translate((0, 0, DECK_Z)), "wheat")
    parts["lidar"] = (cq.Workplane("XY").circle(LIDAR["d"] / 2).extrude(LIDAR["h"])
                      .translate((0, 0, DECK_Z + 3)), "firebrick")
    return parts


def checks(parts):
    res = []
    far = math.hypot(PAD_X, PAD_Y) + PAD_D / 2
    res.append(("pad inside outline", far <= R, f"{far:.1f} <= {R}"))
    gap = 2 * PAD_Y - PAD_D
    res.append(("gap between pads >= 4", gap >= 4, f"{gap:.1f} mm"))
    # boolean interference between all envelopes (cheap but exact)
    names = list(parts)
    solids = {n: parts[n][0].val() for n in names}
    bad = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            inter = solids[names[a]].intersect(solids[names[b]])
            if inter.Volume() > 1.0:
                bad.append(f"{names[a]} x {names[b]} ({inter.Volume():.0f} mm3)")
    res.append(("no envelope interference", not bad, "; ".join(bad) or "none"))
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = build()
    asm = cq.Assembly(name="dweilrobo_concept_v0")
    for n, (wp, col) in parts.items():
        asm.add(wp, name=n, color=cq.Color(col))
    asm.export(os.path.join(OUT, "concept_v0.step"))
    from render import render
    views = {"iso_front": (1.0, -1.2, 0.9), "iso_rear_below": (-1.0, -1.0, -0.6),
             "top": (0, 0, 1), "side": (0, -1, 0.001)}
    for tag, vdir in views.items():
        render(parts, os.path.join(OUT, f"concept_v0_{tag}.png"), view=vdir,
               title=f"dweilrobo concept v0 - {tag} (envelopes, dims mostly assumed)")
    ok = True
    print("Concept v0 checks (all dims with evidence A are assumptions!)")
    for name, passed, detail in checks(parts):
        ok &= passed
        print(f"  [{'OK ' if passed else 'FAIL'}] {name:32s} {detail}")
    n_a = sum(1 for _, e, _ in P.EVIDENCE.values() if e == "A")
    print(f"  evidence: {n_a}/{len(P.EVIDENCE)} parameters are still assumptions (A)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
