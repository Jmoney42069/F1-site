#!/usr/bin/env python3
"""EVE-style balancing robot - shape study v0 (CadQuery).

Run: python3 eve/model.py  -> eve/out/eve_v0.glb + eve/out/eve_v0.step
Frame: z up, x forward, ground at z=0. mm.
Shape only: no internals yet.
"""
import math
import os

import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# --- parameters ---------------------------------------------------------------
WHEEL_D, WHEEL_W = 65, 26          # same wheel class as the ordered JGA25 motors
BODY_BOTTOM_Z = 100
BODY_H, BODY_R = 170, 70           # egg body
HEAD_GAP = 14                      # "floating" gap between body and head
HEAD_R, HEAD_H = 54, 42            # half-width, half-height of head spheroid
LIMB_R = 26                        # max radius of arm/leg teardrop
ARM_LEN, LEG_LEN = 135, 160


def revolve_profile(pts):
    """pts: list of (r, z) from bottom axis point to top axis point; revolved around z."""
    wp = cq.Workplane("XZ").moveTo(0, pts[0][1]).spline(pts[1:-1], includeCurrent=True)
    wp = wp.lineTo(0, pts[-1][1]).close()
    return wp.revolve(360, (0, 0, 0), (0, 1, 0))


def body():
    z0, h, r = BODY_BOTTOM_Z, BODY_H, BODY_R
    prof = [(0, z0), (34, z0 + 7), (54, z0 + 32), (66, z0 + 75), (r, z0 + 120),
            (r - 3, z0 + h - 14), (r - 14, z0 + h - 2), (0, z0 + h)]
    return revolve_profile(prof)


def head():
    zc = BODY_BOTTOM_Z + BODY_H + HEAD_GAP + HEAD_H * 0.8
    pts = [(HEAD_R * math.cos(t), zc + HEAD_H * math.sin(t))
           for t in [math.radians(a) for a in range(-90, 91, 15)]]
    pts[0] = (0, pts[0][1]); pts[-1] = (0, pts[-1][1])
    h = revolve_profile(pts)
    # flatten the underside a little, like EVE
    h = h.cut(cq.Workplane("XY").box(200, 200, 40, centered=(True, True, False))
              .translate((0, 0, zc - HEAD_H - 40 + 8)))
    return h, zc


def visor(zc):
    shell = revolve_profile([(0, zc - HEAD_H - 1)] +
                            [(1.015 * HEAD_R * math.cos(math.radians(a)),
                              zc + 1.015 * HEAD_H * math.sin(math.radians(a))) for a in range(-75, 76, 15)] +
                            [(0, zc + HEAD_H + 1)])
    # keep only a front window
    window = (cq.Workplane("YZ").ellipse(40, 24).extrude(200).translate((0, 0, zc + 2)))
    return shell.intersect(window)


def eye(zc, side):
    y = side * 17
    e = cq.Workplane("YZ").ellipse(11, 7).extrude(6)
    x = math.sqrt(max(HEAD_R ** 2 * (1 - (y / HEAD_R) ** 2) - 0, 1)) * 1.0
    return e.rotate((0, 0, 0), (1, 0, 0), side * -12).translate((x - 3.5, y, zc + 4))


def teardrop(top, length, radius, tilt_deg=0.0, flat=0.92):
    """smooth limb: round top, pointed bottom. top = (x, y, z) of the top point."""
    n = 16
    wires = []
    tx, ty, tz = top
    for i in range(n + 1):
        s = 0.01 + 0.98 * i / n
        tip = 0.32 * radius
        if s < 0.25:          # round top
            r = radius * math.sin(math.pi / 2 * s / 0.25)
        elif s < 0.85:        # smooth taper
            u = (s - 0.25) / 0.6
            r = radius + (tip - radius) * (3 * u * u - 2 * u ** 3)
        else:                 # round tip, no point
            r = tip * math.cos(math.pi / 2 * (s - 0.85) / 0.15)
        r = max(r, 0.8)
        z = tz - s * length
        y = ty + math.tan(math.radians(tilt_deg)) * s * length
        wires.append(cq.Wire.makeEllipse(r, r * flat, cq.Vector(tx, y, z), cq.Vector(0, 0, 1),
                                         cq.Vector(1, 0, 0)))
    return cq.Workplane().add(cq.Solid.makeLoft(wires, ruled=False))


def build():
    parts = {}
    parts["body"] = (body(), (0.86, 0.88, 0.9))
    h, zc = head()
    parts["head"] = (h, (0.86, 0.88, 0.9))
    parts["visor"] = (visor(zc), (0.03, 0.03, 0.05))
    for s, t in ((1, "L"), (-1, "R")):
        parts[f"eye_{t}"] = (eye(zc, s), (0.2, 0.6, 1.0))
        parts[f"arm_{t}"] = (teardrop((0, s * (BODY_R + 8), BODY_BOTTOM_Z + BODY_H - 18),
                                      ARM_LEN, LIMB_R * 0.85, tilt_deg=s * 8), (0.86, 0.88, 0.9))
        hip_z = BODY_BOTTOM_Z + 60
        parts[f"leg_{t}"] = (teardrop((0, s * 38, hip_z), hip_z, LIMB_R, tilt_deg=s * 4), (0.86, 0.88, 0.9))
    return parts


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = build()
    asm = cq.Assembly(name="eve_v0")
    for n, (wp, col) in parts.items():
        asm.add(wp, name=n, color=cq.Color(*col))
    asm.export(os.path.join(OUT, "eve_v0.glb"))
    asm.export(os.path.join(OUT, "eve_v0.step"))
    bb = cq.Compound.makeCompound([wp.val() for wp, _ in parts.values()]).BoundingBox()
    print(f"size: {bb.xlen:.0f} x {bb.ylen:.0f} x {bb.zlen:.0f} mm (x,y,z)")


if __name__ == "__main__":
    main()
