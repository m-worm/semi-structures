"""Lightweight vector-isometric engine for semiconductor structures.

Draws axis-aligned cuboids in a 30-degree isometric projection using plain
matplotlib patches: three visible faces per box (top, right = -y, left =
-x), shaded from the material fill via semi_structures.style.mix, painter-sorted
back-to-front with an explicit layer key for scenes where geometry alone
is ambiguous (a gate drawn over fins). Face labels rotate with the face.

Use with semi_structures.style.MATERIAL fills:

    boxes = [Box((0, 0, 0), (10, 7, 1.6), MATERIAL["Si"][0], k=0,
                 label=("front", "bulk Si"))]
    draw_scene(ax, boxes, origin=(20, 30), scale=1.5)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.patches import Polygon

from .style import C_SLATE, MIN_PRINT_PT, luminance, mix

_C, _S = np.cos(np.radians(30)), np.sin(np.radians(30))
FACE_SHADE = {"top": 0.0, "right": 0.13, "left": 0.26}
LABEL_ROT = {"top_x": -30.0, "top_y": 30.0, "right": 30.0, "left": -30.0}
LABEL_PT = 7.5     # face labels: the small-note rung; never below MIN_PRINT_PT


def iso(x, y, z):
    """Project 3D world coordinates to 2D screen coordinates."""
    return (x - y) * _C, (x + y) * _S + z


@dataclass
class Box:
    origin: tuple      # (x0, y0, z0)
    size: tuple        # (dx, dy, dz)
    color: str         # base fill (top face); right/left shaded from it
    k: int = 0         # explicit draw layer; higher draws later (in front)
    label: tuple = None    # (face, text) with face in
    #                        {top_x, top_y, right, left}
    label_size: float = LABEL_PT   # points at print width (>= MIN_PRINT_PT)
    edge_shade: float = 0.50
    alpha: float = 1.0     # face alpha; < 1 for the transparent crystals

    def faces(self):
        x0, y0, z0 = self.origin
        dx, dy, dz = self.size
        x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
        return {
            "top": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            "right": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1),
                      (x0, y0, z1)],
            "left": [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
        }

    def depth_key(self):
        # stack scenes render correctly bottom-up (low z first), then far
        # to near within a level (the viewer sits at -x, -y, so larger
        # x0+y0 is farther and draws first)
        x0, y0, z0 = self.origin
        return (self.k, z0, -(x0 + y0))


def _face_center(face, box):
    x0, y0, z0 = box.origin
    dx, dy, dz = box.size
    if face.startswith("top"):
        return (x0 + dx / 2, y0 + dy / 2, z0 + dz)
    if face == "right":
        return (x0 + dx / 2, y0, z0 + dz / 2)
    return (x0, y0 + dy / 2, z0 + dz / 2)


def slab_with_holes(origin, size, holes, color, k=0, alpha=1.0):
    """Decompose a slab with rectangular through-holes (drilled along z)
    into Boxes: a grid partition from the hole edges, emitting every cell
    that no hole covers. Axis-aligned cutouts need no CSG library."""
    x0, y0, z0 = origin
    dx, dy, dz = size
    xs = sorted({x0, x0 + dx, *(h[0] for h in holes),
                 *(h[0] + h[2] for h in holes)})
    ys = sorted({y0, y0 + dy, *(h[1] for h in holes),
                 *(h[1] + h[3] for h in holes)})
    out = []
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            cx, cy = 0.5 * (xa + xb), 0.5 * (ya + yb)
            covered = any(hx <= cx <= hx + hdx and hy <= cy <= hy + hdy
                          for hx, hy, hdx, hdy in holes)
            if not covered and xb > xa and yb > ya:
                cell = Box((xa, ya, z0), (xb - xa, yb - ya, dz), color, k,
                           alpha=alpha)
                cell.edge_shade = 0.30       # soften decomposition seams
                out.append(cell)
    return out


@dataclass
class Pillar:
    """Vertical cylinder: elliptical top, shaded body, painter-sorted
    with the boxes."""
    center: tuple      # (cx, cy, z0)
    radius: float
    height: float
    color: str
    k: int = 0
    alpha: float = 1.0

    def depth_key(self):
        cx, cy, z0 = self.center
        return (self.k, z0, -(cx + cy))


def _draw_pillar(ax, p, screen, scale):
    from matplotlib.patches import Ellipse
    cx, cy, z0 = p.center
    a = np.sqrt(2.0) * _C * p.radius * scale       # screen semi-axis (u)
    b = np.sqrt(2.0) * _S * p.radius * scale       # screen semi-axis (v)
    xb, yb = screen((cx, cy, z0))
    xt, yt = screen((cx, cy, z0 + p.height))
    side = mix(p.color, "#000000", 0.18)
    edge = mix(p.color, "#000000", 0.50)
    al = getattr(p, "alpha", 1.0)
    ax.add_patch(Polygon([(xb - a, yb), (xb + a, yb),
                          (xt + a, yt), (xt - a, yt)], closed=True,
                         facecolor=to_rgba(side, al), edgecolor="none"))
    ax.add_patch(Ellipse((xb, yb), 2 * a, 2 * b, facecolor=to_rgba(side, al),
                         edgecolor=edge, lw=0.45))
    ax.add_patch(Ellipse((xt, yt), 2 * a, 2 * b,
                         facecolor=to_rgba(p.color, al),
                         edgecolor=edge, lw=0.55))
    ax.plot([xb - a, xt - a], [yb, yt], color=edge, lw=0.45)
    ax.plot([xb + a, xt + a], [yb, yt], color=edge, lw=0.45)


def draw_scene(ax, boxes, origin=(0.0, 0.0), scale=1.0):
    """Draw boxes back-to-front at the given screen origin and scale.

    Face labels are matplotlib text in points, so they print at size when
    the figure is authored at print width; a label below MIN_PRINT_PT is
    refused -- use a leader annotation for faces too small to carry text.
    """
    ox, oy = origin
    for box in boxes:
        if getattr(box, "label", None) and box.label_size < MIN_PRINT_PT:
            raise ValueError(
                f"face label {box.label[1]!r} is {box.label_size:g} pt; the "
                f"print floor is {MIN_PRINT_PT:g} pt (use a leader instead)")

    def screen(p):
        u, v = iso(*p)
        return (ox + scale * u, oy + scale * v)

    for box in sorted(boxes, key=lambda b: b.depth_key()):
        if isinstance(box, Pillar):
            _draw_pillar(ax, box, screen, scale)
            continue
        edge = mix(box.color, "#000000", box.edge_shade)
        al = getattr(box, "alpha", 1.0)
        for name in ("left", "right", "top"):
            corners = [screen(p) for p in box.faces()[name]]
            # translucent materials (alpha < 1) keep an opaque-ish outline
            # so the silhouette still reads on the page
            ax.add_patch(Polygon(corners, closed=True,
                                 facecolor=to_rgba(mix(box.color, "#000000",
                                                       FACE_SHADE[name]), al),
                                 edgecolor=to_rgba(edge, min(1.0, al + 0.4)),
                                 linewidth=0.55, joinstyle="round"))
        if box.label:
            face, text = box.label
            base = "top" if face.startswith("top") else face
            cx, cy = screen(_face_center(base, box))
            shaded = mix(box.color, "#000000", FACE_SHADE[base])
            color = C_SLATE if luminance(shaded) > 0.30 else "#f4f6f8"
            ax.text(cx, cy, text, fontsize=box.label_size, color=color,
                    ha="center", va="center", rotation=LABEL_ROT[face],
                    rotation_mode="anchor")
