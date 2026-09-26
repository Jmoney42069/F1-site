"""Dependency-light shaded renderer (numpy + Pillow, painter's algorithm).

Good enough to review concept layouts; not photo-realistic. Used by build.py.
"""
import numpy as np
from PIL import Image, ImageDraw
from cadquery import Color


def _rgb(name):
    c = Color(name).toTuple()
    return np.array(c[:3]) * 255


def render(parts, path, view=(1.0, -1.2, 0.9), size=(1000, 700), tol=0.5, title=""):
    """parts: dict name -> (Workplane, colorname). view: camera direction (toward origin)."""
    d = np.array(view, float); d /= np.linalg.norm(d)
    up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.99 else np.array([1.0, 0, 0])
    right = np.cross(up, d); right /= np.linalg.norm(right)
    cam_up = np.cross(d, right)
    light = np.array([0.4, -0.3, 1.0]); light /= np.linalg.norm(light)
    tris, cols = [], []
    for _, (wp, col) in parts.items():
        verts, faces = wp.val().tessellate(tol)
        V = np.array([(p.x, p.y, p.z) for p in verts])
        F = np.array(faces)
        if len(F) == 0:
            continue
        T = V[F]
        tris.append(T)
        cols.append(np.repeat(_rgb(col)[None, :], len(F), 0))
    T = np.concatenate(tris); C = np.concatenate(cols)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    facing = (n @ d) > 0
    n[~facing] *= -1  # two-sided lighting
    shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    X = T @ right; Y = T @ cam_up; Z = T @ d
    order = np.argsort(-Z.mean(1))  # far first (camera looks along -d... farthest = most negative dot)
    order = np.argsort(Z.mean(1))
    W, H = size
    xs, ys = X.ravel(), Y.ravel()
    sc = 0.9 * min(W / (xs.max() - xs.min()), H / (ys.max() - ys.min()))
    cx, cy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
    img = Image.new("RGB", size, (250, 250, 250))
    dr = ImageDraw.Draw(img)
    for i in order:
        pts = [(W / 2 + (X[i, k] - cx) * sc, H / 2 - (Y[i, k] - cy) * sc) for k in range(3)]
        c = tuple(int(v) for v in np.clip(C[i] * shade[i], 0, 255))
        dr.polygon(pts, fill=c, outline=c)
    if title:
        dr.text((10, 10), title, fill=(0, 0, 0))
    img.save(path)
