#!/usr/bin/env python3
"""Per-part drawings (front / side / top) with overall dimensions -> eve/out/drawings.html.

Outlines come from slicing the real CAD solids at many heights, so they match model.py.
"""
import html
import math
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

PARTS = [  # key in model.build(), display name, quantity, note
    ("head", "Hoofd", 1, "Bol met afgeplatte onderkant. Zweeft 14 mm boven het lijf."),
    ("visor", "Vizier", 1, "Dunne zwarte schaal, volgt de voorkant van het hoofd (≈1 mm dik)."),
    ("eye_L", "Oog", 2, "Ovaal plaatje op het vizier. Rechteroog is gespiegeld."),
    ("body", "Lijf", 1, "Eivorm, breedst op ⅔ hoogte, platte bovenkant."),
    ("arm_L", "Arm", 2, "Druppelvorm, ronde punt. Rechterarm is gespiegeld."),
    ("leg_L", "Been", 2, "Zelfde druppelvorm als de arm, groter. Punt raakt de vloer."),
]
N = 70


def slices(solid):
    bb = solid.BoundingBox()
    rows = []
    for i in range(N + 1):
        z = bb.zmin + (bb.zmax - bb.zmin) * (i + 0.5) / (N + 1)
        slab = cq.Solid.makeBox(1000, 1000, 0.2, cq.Vector(-500, -500, z - 0.1))
        try:
            s = solid.intersect(slab)
            if s.Volume() < 1e-6:
                continue
            b = s.BoundingBox()
            rows.append((z, b.xmin, b.xmax, b.ymin, b.ymax))
        except Exception:
            continue
    return bb, rows


def outline(rows, lo, hi, zmin, zmax):
    """closed polygon (u, z) from per-height extents, capped at top/bottom"""
    left = [(r[lo], r[0]) for r in rows]
    right = [(r[hi], r[0]) for r in rows]
    mid_b = (rows[0][lo] + rows[0][hi]) / 2
    mid_t = (rows[-1][lo] + rows[-1][hi]) / 2
    return [(mid_b, zmin)] + right + [(mid_t, zmax)] + left[::-1]


def svg_view(poly, u0, u1, v0, v1, label, dims, scale, flip_v=True):
    pad_l, pad_b, pad_t, pad_r = 34, 34, 22, 40
    w = (u1 - u0) * scale + pad_l + pad_r
    h = (v1 - v0) * scale + pad_t + pad_b
    X = lambda u: pad_l + (u - u0) * scale  # noqa: E731
    Y = (lambda v: pad_t + (v1 - v) * scale) if flip_v else (lambda v: pad_t + (v - v0) * scale)  # noqa: E731
    pts = " ".join(f"{X(u):.1f},{Y(v):.1f}" for u, v in poly)
    out = [f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{label}">',
           f'<polygon points="{pts}" class="part"/>',
           f'<line x1="{X((u0+u1)/2):.1f}" y1="{pad_t-6}" x2="{X((u0+u1)/2):.1f}" y2="{h-pad_b+6:.1f}" class="axis"/>']
    # horizontal dimension (bottom)
    yb = h - 14
    out += [f'<line x1="{X(u0):.1f}" y1="{yb}" x2="{X(u1):.1f}" y2="{yb}" class="dim" marker-start="url(#a)" marker-end="url(#a)"/>',
            f'<line x1="{X(u0):.1f}" y1="{Y(v0) if flip_v else Y(v1):.1f}" x2="{X(u0):.1f}" y2="{yb+4}" class="ext"/>',
            f'<line x1="{X(u1):.1f}" y1="{Y(v0) if flip_v else Y(v1):.1f}" x2="{X(u1):.1f}" y2="{yb+4}" class="ext"/>',
            f'<text x="{X((u0+u1)/2):.1f}" y="{yb-4}" class="dt">{dims[0]:.0f}</text>']
    # vertical dimension (right)
    xr = w - 16
    out += [f'<line x1="{xr:.1f}" y1="{Y(v1):.1f}" x2="{xr:.1f}" y2="{Y(v0):.1f}" class="dim" marker-start="url(#a)" marker-end="url(#a)"/>',
            f'<line x1="{X(u1):.1f}" y1="{Y(v1):.1f}" x2="{xr+4:.1f}" y2="{Y(v1):.1f}" class="ext"/>',
            f'<line x1="{X(u1):.1f}" y1="{Y(v0):.1f}" x2="{xr+4:.1f}" y2="{Y(v0):.1f}" class="ext"/>',
            f'<text x="{xr-5:.1f}" y="{(Y(v0)+Y(v1))/2:.1f}" class="dt" transform="rotate(-90 {xr-5:.1f} {(Y(v0)+Y(v1))/2:.1f})">{dims[1]:.0f}</text>']
    out.append("</svg>")
    return f'<figure class="view">{"".join(out)}<figcaption>{label}</figcaption></figure>'


def ellipse_poly(cx, cy, rx, ry, n=72):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def part_card(key, name, qty, note, solid, scale):
    bb, rows = slices(solid)
    front = outline(rows, 3, 4, bb.zmin, bb.zmax)   # looking along -x: horizontal = y
    side = outline(rows, 1, 2, bb.zmin, bb.zmax)    # looking along +y: horizontal = x
    widest = max(rows, key=lambda r: (r[4] - r[3]) * (r[2] - r[1]))
    top = ellipse_poly((widest[1] + widest[2]) / 2, (widest[3] + widest[4]) / 2,
                       (widest[2] - widest[1]) / 2, (widest[4] - widest[3]) / 2)
    top = [(y, x) for x, y in top]
    views = [
        svg_view(front, bb.ymin, bb.ymax, bb.zmin, bb.zmax, "Vooraanzicht", (bb.ylen, bb.zlen), scale),
        svg_view(side, bb.xmin, bb.xmax, bb.zmin, bb.zmax, "Zijaanzicht", (bb.xlen, bb.zlen), scale),
        svg_view(top, bb.ymin, bb.ymax, bb.xmin, bb.xmax, "Bovenaanzicht", (bb.ylen, bb.xlen), scale),
    ]
    vol = solid.Volume() / 1000
    widest_z = widest[0] - bb.zmin
    facts = [("Aantal", f"{qty}"), ("B × D × H", f"{bb.ylen:.0f} × {bb.xlen:.0f} × {bb.zlen:.0f} mm"),
             ("Breedste punt", f"{widest_z:.0f} mm boven onderkant"), ("Volume (massief)", f"{vol:.0f} cm³")]
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)
    return (f'<article class="card" id="{key}"><header><h2>{html.escape(name)}</h2>'
            f'<p>{html.escape(note)}</p></header><dl>{dl}</dl><div class="views">{"".join(views)}</div></article>')


CSS = """
:root{--bg:#f3f5f6;--paper:#ffffff;--ink:#1c2429;--muted:#5f6d75;--line:#d4dbdf;--part:#dfe7ec;--stroke:#2b3a42;--dim:#0f7c8c;
--sans:"Barlow",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12181b;--paper:#1a2226;--ink:#e3eaee;--muted:#93a3ab;--line:#2d393f;--part:#2a353b;--stroke:#c9d4da;--dim:#4cc1d0;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#12181b;--paper:#1a2226;--ink:#e3eaee;--muted:#93a3ab;--line:#2d393f;--part:#2a353b;--stroke:#c9d4da;--dim:#4cc1d0;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);padding-inline:16px;padding-block:24px 40px}
main{max-width:1100px;margin:0 auto;display:grid;gap:18px}
h1{font-size:26px;margin:0;text-wrap:balance}
.lead{margin:6px 0 0;color:var(--muted);max-width:65ch;line-height:1.45}
.card{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:16px;display:grid;gap:12px}
.card header{display:grid;gap:4px}
h2{margin:0;font-size:19px}
.card header p{margin:0;color:var(--muted)}
dl{display:flex;flex-wrap:wrap;gap:8px 24px;margin:0}
dl div{display:grid}
dt{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
dd{margin:0;font:13px var(--mono);font-variant-numeric:tabular-nums}
.views{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;overflow-x:auto}
.view{margin:0;display:grid;gap:4px;justify-items:center}
.view svg{max-width:100%;height:auto}
figcaption{font-size:12px;color:var(--muted)}
.part{fill:var(--part);stroke:var(--stroke);stroke-width:1.2}
.axis{stroke:var(--muted);stroke-width:.6;stroke-dasharray:8 3 2 3}
.dim{stroke:var(--dim);stroke-width:.9;fill:none}
.ext{stroke:var(--dim);stroke-width:.5;opacity:.7}
.dt{fill:var(--dim);font:11px var(--mono);text-anchor:middle}
.toc{display:flex;flex-wrap:wrap;gap:8px}
.toc a{color:var(--ink);border:1px solid var(--line);border-radius:999px;padding:4px 10px;text-decoration:none;font-size:13px}
.toc a:focus-visible{outline:2px solid var(--dim)}
"""


def main():
    built = model.build()
    scale = 1.35
    cards = []
    for key, name, qty, note in PARTS:
        solid = built[key][0].val()
        cards.append(part_card(key, name, qty, note, solid, scale))
    toc = "".join(f'<a href="#{k}">{html.escape(n)}</a>' for k, n, _, _ in PARTS)
    page = f"""<title>EVE-bot onderdelen</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&family=JetBrains+Mono&display=swap">
<style>{CSS}</style>
<svg width="0" height="0" style="position:absolute"><defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#0f7c8c"/></marker></defs></svg>
<main>
<header><h1>EVE-bot: tekeningen per onderdeel</h1>
<p class="lead">Buitenvorm van elk onderdeel, op dezelfde schaal, maten in mm. Dit zijn nog massieve vormen: wanddikte, verbindingen en de binnenkant volgen zodra we weten hoe hij gaat staan.</p></header>
<nav class="toc" aria-label="Onderdelen">{toc}</nav>
{''.join(cards)}
</main>"""
    out = os.path.join(HERE, "out", "drawings.html")
    open(out, "w").write(page)
    print("wrote", out)


if __name__ == "__main__":
    main()
