#!/usr/bin/env python3
"""Parametric layout + sanity checks for the dweilrobo chassis.

No dependencies. Run:  python3 cad/layout.py
Outputs a report to stdout and cad/layout_top.svg (1 px = 1 mm).

Frame: x forward, y left, origin = robot centre = midpoint of drive-wheel axle.
All values in mm / g / N. Every value marked VERIFY must be measured on the
real part before the CAD is frozen (see docs/01-engineering-study.md §11).
"""
import math

P = dict(
    body_r=175,            # round outline, Ø350
    wheel_d=65, wheel_w=26, wheel_y=135,          # VERIFY wheel + hub width
    drive_motor_len=70, drive_motor_d=25,         # JGA25-370 + encoder, VERIFY per ratio
    pad_d=130, pad_x=-85, pad_y=68,               # mop pads (self-made discs)
    mop_motor_d=25,                               # vertical JGA25-370 above pad
    caster_x=150,
    bumper_arc_deg=140,                           # front bumper coverage
    lidar_d=100, lidar_x=0,                       # LDS02RR turret footprint, VERIFY
    tank=dict(x0=-45, x1=35, y0=-50, y1=50, h=50),     # 80x100x50 box over the axle
    battery=dict(x0=-120, x1=-60, y0=-39, y1=39),       # 3S1P 18650 holder ~60x77, VERIFY
    electronics=dict(x0=45, x1=135, y0=-55, y1=55),
    spring_force_per_pad=3.0,  # N, adjustable preload (tune 2-5 N)
    mu_wheel_wet=0.4,          # rubber on wet tile, conservative
    mu_pad=0.5,                # microfiber on tile, conservative
    mop_rpm=150, cruise_v=0.2, # m/s
)

# mass items: (name, grams, x_mm). Pads/hubs are "floating": their weight goes
# straight to the floor through the mop, not through the chassis.
MASSES = [
    ("frame, decks, brackets, screws", 500, -10),
    ("drive motors x2", 200, 0),
    ("wheels + hubs x2", 60, 0),
    ("mop motors x2", 200, -85),
    ("pumps x2 + tubing", 110, -40),
    ("tank (empty)", 60, -5),
    ("battery 3S1P + holder + BMS", 190, -90),
    ("ESP32 + drivers + buck + wiring", 150, 90),
    ("LDS02RR lidar", 180, 0),
    ("bumper", 60, 160),
    ("caster", 25, 150),
]
FLOATING_PADS_G = 2 * 70   # disc + hub + wet cloth, per robot
WATER_FULL_G = 330
G = 9.81e-3  # N per gram


def loads(water_g):
    items = MASSES + [("water", water_g, -5)]
    m = sum(g for _, g, _ in items)
    x_cg = sum(g * x for _, g, x in items) / m
    W = m * G
    F_mop = 2 * P["spring_force_per_pad"]
    # chassis is supported by wheels (x=0), caster (x=caster_x) and the spring
    # reaction of the mops (x=pad_x, pushing the chassis UP).
    # moment about axle:  N_c*xc + F_mop*xp - W*x_cg = 0
    N_c = (W * x_cg - F_mop * P["pad_x"]) / P["caster_x"]
    N_w = W - F_mop - N_c
    return dict(mass_g=m + FLOATING_PADS_G, x_cg=x_cg, W=W, F_mop=F_mop,
                N_caster=N_c, N_wheels=N_w)


def pad_normal():
    return P["spring_force_per_pad"] + FLOATING_PADS_G / 2 * G


def pad_friction_torque():
    # uniform pressure disc: T = 2/3 * mu * N * R
    return 2 / 3 * P["mu_pad"] * pad_normal() * P["pad_d"] / 2e3  # N*m


def spinning_drag():
    # Sliding friction points along the local relative velocity. When the pad
    # spins much faster than the robot moves, the net force opposing
    # translation is roughly mu*N * v_robot / v_mean_slip. Rough, but the
    # right order of magnitude; measure on the real rig.
    v_mean = 2 / 3 * (P["pad_d"] / 2e3) * P["mop_rpm"] * 2 * math.pi / 60
    return 2 * P["mu_pad"] * pad_normal() * min(1.0, P["cruise_v"] / v_mean)


def checks():
    out, ok = [], True
    r = P["pad_d"] / 2
    # pad inside outline
    far = math.hypot(P["pad_x"], P["pad_y"]) + r
    out.append(("pad inside body outline", far <= P["body_r"], f"{far:.1f} <= {P['body_r']}"))
    # pad-pad gap
    gap = 2 * P["pad_y"] - P["pad_d"]
    out.append(("gap between pads >= 4", gap >= 4, f"{gap:.1f} mm"))
    # pad vs wheel rectangle
    wx0, wx1 = -P["wheel_d"] / 2, P["wheel_d"] / 2
    wy0 = P["wheel_y"] - P["wheel_w"] / 2
    dx = max(wx0 - P["pad_x"], 0, P["pad_x"] - wx1)
    dy = max(wy0 - P["pad_y"], 0)
    clr = math.hypot(dx, dy) - r
    out.append(("pad-to-wheel clearance >= 5", clr >= 5, f"{clr:.1f} mm"))
    # wheel inside outline
    wf = math.hypot(P["wheel_d"] / 2, P["wheel_y"] + P["wheel_w"] / 2)
    out.append(("wheel inside outline", wf <= P["body_r"], f"{wf:.1f} <= {P['body_r']}"))
    # drive motors don't collide in the middle
    inner = P["wheel_y"] - P["wheel_w"] / 2 - 3 - P["drive_motor_len"]
    out.append(("drive motors clear each other", inner > 5, f"inner end at y=±{inner:.0f}"))
    for name, water in (("full tank", WATER_FULL_G), ("empty tank", 0)):
        L = loads(water)
        stalled = 2 * P["mu_pad"] * pad_normal()  # pads not spinning (fault case)
        trac = P["mu_wheel_wet"] * L["N_wheels"]
        out.append((f"[{name}] caster keeps contact", L["N_caster"] > 0.5,
                    f"N_caster={L['N_caster']:.1f} N"))
        out.append((f"[{name}] traction > spinning-pad drag x2", trac > 2 * spinning_drag(),
                    f"traction {trac:.1f} N vs drag {spinning_drag():.1f} N (N_wheels={L['N_wheels']:.1f} N)"))
        out.append((f"[{name}] (info) traction vs stalled pads", True,
                    f"{trac:.1f} N vs {stalled:.1f} N -> stalled mop must stop the drive"))
    for _, passed, _ in out:
        ok &= passed
    return out, ok


def svg():
    s = []
    R = P["body_r"]
    W = H = 2 * R + 40
    c = R + 20
    X = lambda x: c - x  # noqa: E731  (screen: forward = up)
    Y = lambda y: c - y  # noqa: E731
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="monospace" font-size="9">')
    s.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    s.append(f'<circle cx="{c}" cy="{c}" r="{R}" fill="#f4f4f4" stroke="#333"/>')
    def rect(x0, x1, y0, y1, fill, label):
        s.append(f'<rect x="{Y(y1)}" y="{X(x1)}" width="{y1-y0}" height="{x1-x0}" '
                 f'fill="{fill}" stroke="#333" fill-opacity="0.8"/>')
        s.append(f'<text x="{Y((y0+y1)/2)}" y="{X((x0+x1)/2)}" text-anchor="middle">{label}</text>')
    for sgn in (1, -1):
        wy = sgn * P["wheel_y"]
        rect(-P["wheel_d"]/2, P["wheel_d"]/2, wy - P["wheel_w"]/2, wy + P["wheel_w"]/2, "#555", "")
        inner = P["wheel_y"] - P["wheel_w"]/2 - 3
        y0, y1 = sorted((sgn * inner, sgn * (inner - P["drive_motor_len"])))
        rect(-P["drive_motor_d"]/2, P["drive_motor_d"]/2, y0, y1, "#9ab", "drive")
        s.append(f'<circle cx="{Y(sgn*P["pad_y"])}" cy="{X(P["pad_x"])}" r="{P["pad_d"]/2}" '
                 f'fill="#6af" fill-opacity="0.35" stroke="#06c"/>')
        s.append(f'<circle cx="{Y(sgn*P["pad_y"])}" cy="{X(P["pad_x"])}" r="{P["mop_motor_d"]/2}" '
                 f'fill="#9ab" stroke="#333"/>')
    t, b, e = P["tank"], P["battery"], P["electronics"]
    rect(t["x0"], t["x1"], t["y0"], t["y1"], "#bdf", "tank")
    rect(b["x0"], b["x1"], b["y0"], b["y1"], "#fc8", "3S batt")
    rect(e["x0"], e["x1"], e["y0"], e["y1"], "#bea", "ESP32/drivers")
    s.append(f'<circle cx="{c}" cy="{X(P["lidar_x"])}" r="{P["lidar_d"]/2}" fill="none" '
             f'stroke="#c30" stroke-dasharray="4 3"/>')
    s.append(f'<text x="{c}" y="{X(P["lidar_x"]) - P["lidar_d"]/2 + 10}" text-anchor="middle" fill="#c30">lidar (top deck)</text>')
    s.append(f'<circle cx="{c}" cy="{X(P["caster_x"])}" r="8" fill="#333"/>')
    a = math.radians(P["bumper_arc_deg"] / 2)
    x1, y1 = R * math.cos(a), R * math.sin(a)
    s.append(f'<path d="M {Y(y1)} {X(x1)} A {R} {R} 0 0 1 {Y(-y1)} {X(x1)}" fill="none" stroke="#e80" stroke-width="5"/>')
    s.append(f'<text x="{c}" y="14" text-anchor="middle">FRONT (bumper)  -  dweilrobo top view, 1px = 1mm, Ø{2*R}</text>')
    s.append('</svg>')
    return "\n".join(s)


if __name__ == "__main__":
    import os
    res, ok = checks()
    print("Geometry / load checks")
    for name, passed, detail in res:
        print(f"  [{'OK ' if passed else 'FAIL'}] {name:45s} {detail}")
    for name, water in (("full", WATER_FULL_G), ("empty", 0)):
        L = loads(water)
        print(f"  mass ({name} tank) = {L['mass_g']:.0f} g, chassis CG x = {L['x_cg']:.1f} mm")
    print(f"  mop friction torque per pad ≈ {pad_friction_torque()*100/9.81:.2f} kg·cm")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layout_top.svg")
    with open(path, "w") as f:
        f.write(svg())
    print(f"  wrote {path}")
    raise SystemExit(0 if ok else 1)
