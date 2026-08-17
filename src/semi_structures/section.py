"""2D cross-section renderer for the process model.

``draw_section(ax, wafer, y=...)`` draws the x-z section of a
:class:`semi_structures.process.Wafer` at the plane ``y`` (default: the
wafer centre) with plain matplotlib patches: films and local features as
bands, etches as gaps, fills and implants as inserts, all exact at the plane
for rectangles, circles and rotated ellipses (their chords), and stack
breaks as empty intervals bounded by zigzag break marks. Everything is vector
and follows the palette and typography rules; ``labels`` adds callouts and
``zscale`` exaggerates thickness for thin films.

    from semi_structures.section import draw_section
    draw_section(ax, wafer, y=None, labels="all", zscale=1.0)

Reachable through ``Wafer.render(ax, view="section", y=...)`` as well.
"""
from __future__ import annotations

from math import cos, radians, sin, sqrt

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import to_rgba

from .style import C_GREY, C_SLATE, MATERIAL, alpha_for, mix

BREAK_STYLE = "zigzag"      # or "gap" (no marks)


def _color(material):
    return MATERIAL[material][0] if material in MATERIAL else material


# ---- chord of a process shape with the plane y = y_cut ----------------------

def _polygon(shape, n=128):
    """Vertices of the shape outline (rotated rectangle / ellipse)."""
    from .process import Ellipse, Rectangle
    cx, cy = shape.center
    if isinstance(shape, Rectangle):
        dx, dy = shape.size
        pts = np.array([(-dx / 2, -dy / 2), (dx / 2, -dy / 2),
                        (dx / 2, dy / 2), (-dx / 2, dy / 2)])
    elif isinstance(shape, Ellipse):
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        pts = np.column_stack([shape.radii[0] * np.cos(t),
                               shape.radii[1] * np.sin(t)])
    else:
        raise TypeError(type(shape))
    a = radians(getattr(shape, "rotation", 0.0))
    rot = np.array([[cos(a), -sin(a)], [sin(a), cos(a)]])
    return pts @ rot.T + np.array([cx, cy])


def chord(shape, y):
    """``(x0, x1)`` where the plane ``y`` crosses ``shape``, or None."""
    from .process import Circle, Rectangle
    cx, cy = shape.center
    if isinstance(shape, Circle):
        d = shape.radius ** 2 - (y - cy) ** 2
        if d <= 0:
            return None
        h = sqrt(d)
        return (cx - h, cx + h)
    if isinstance(shape, Rectangle) and abs(shape.rotation) < 1e-12:
        dx, dy = shape.size
        if not (cy - dy / 2 <= y <= cy + dy / 2):
            return None
        return (cx - dx / 2, cx + dx / 2)
    pts = _polygon(shape)
    xs = []
    n = len(pts)
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        if (ya - y) * (yb - y) <= 0 and ya != yb:
            xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
    if len(xs) < 2:
        return None
    return (min(xs), max(xs))


# ---- rectangle minus cuts -----------------------------------------------------

def _cells(rect, cuts, eps=1e-9):
    """Axis-aligned rectangles covering ``rect`` minus the union of ``cuts``
    (all as (x0, x1, z0, z1)); rows of equal z are merged along x."""
    x0, x1, z0, z1 = rect
    xs = {x0, x1}
    zs = {z0, z1}
    for cx0, cx1, cz0, cz1 in cuts:
        xs.update(v for v in (cx0, cx1) if x0 < v < x1)
        zs.update(v for v in (cz0, cz1) if z0 < v < z1)
    xs, zs = sorted(xs), sorted(zs)
    out = []
    for za, zb in zip(zs, zs[1:]):
        zm = 0.5 * (za + zb)
        run = None
        for xa, xb in zip(xs, xs[1:]):
            xm = 0.5 * (xa + xb)
            covered = any(cx0 - eps <= xm <= cx1 + eps and
                          cz0 - eps <= zm <= cz1 + eps
                          for cx0, cx1, cz0, cz1 in cuts)
            if covered:
                if run:
                    out.append(run)
                    run = None
            elif run and abs(run[1] - xa) < eps:
                run = (run[0], xb, za, zb)
            else:
                if run:
                    out.append(run)
                run = (xa, xb, za, zb)
        if run:
            out.append(run)
    return out


def _outline(rects, nd=9):
    """Boundary segments of a union of rectangles (shared edges removed)."""
    seen = {}
    for x0, x1, z0, z1 in rects:
        for seg in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)),
                    ((x0, z1), (x1, z1)), ((x0, z0), (x0, z1))):
            key = tuple(sorted((tuple(round(v, nd) for v in seg[0]),
                                tuple(round(v, nd) for v in seg[1]))))
            seen[key] = seen.get(key, 0) + 1
    return [k for k, n in seen.items() if n == 1]


# ---- the section ------------------------------------------------------------------

def section_pieces(wafer, y=None):
    """Replay the process at the plane and return drawable pieces.

    Returns ``(pieces, breaks, bounds)`` where each piece is
    ``dict(feature=, color=, rects=[(x0, x1, z0, z1), ...])`` in draw
    order, ``breaks`` the wafer's StackBreaks, and ``bounds`` the x/z extent
    of everything drawn.
    """
    from .process import Layer, _shape_bounds
    wx0, wy0, wx1, wy1 = _shape_bounds(wafer.wafer_footprint)
    if y is None:
        y = 0.5 * (wy0 + wy1)
    solids = []
    for op, f in wafer._operations:
        if op == "layer":
            xr = chord(f.footprint, y)
            if xr:
                solids.append(dict(feature=f, color=_color(f.material),
                                   alpha=alpha_for(f.material),
                                   rect=(xr[0], xr[1], f.z0, f.z1), cuts=[]))
        elif op == "etch":
            xr = chord(f.shape, y)
            if xr:
                for s in solids:
                    s["cuts"].append((xr[0], xr[1], f.z0, f.z1))
        elif op == "fill":
            xr = chord(f.shape, y)
            if xr:
                solids.append(dict(feature=f, color=_color(f.material),
                                   alpha=alpha_for(f.material),
                                   rect=(xr[0], xr[1], f.z0, f.z1), cuts=[]))
        elif op == "replace":
            xr = chord(f.shape, y)
            if xr:
                region = (xr[0], xr[1], f.z0, f.z1)
                pieces = []
                for s in solids:
                    sx0, sx1, sz0, sz1 = s["rect"]
                    ix = (max(sx0, region[0]), min(sx1, region[1]),
                          max(sz0, region[2]), min(sz1, region[3]))
                    if ix[1] > ix[0] and ix[3] > ix[2]:
                        pieces.append(ix)
                        s["cuts"].append(region)
                for ix in pieces:
                    solids.append(dict(feature=f, color=_color(f.material),
                                   alpha=alpha_for(f.material),
                                       rect=ix, cuts=[]))
    # a stack break is a drawing elision, not a process step: it removes its
    # interval from everything, whenever that was deposited
    for brk in wafer.breaks:
        for s in solids:
            s["cuts"].append((-1e30, 1e30, brk.z0, brk.z1))
    pieces = []
    xs, zs = [], []
    for s in solids:
        rects = _cells(s["rect"], s["cuts"])
        if not rects:
            continue
        pieces.append(dict(feature=s["feature"], color=s["color"],
                           alpha=s.get("alpha", 1.0),
                           rects=rects))
        for x0, x1, z0, z1 in rects:
            xs += [x0, x1]
            zs += [z0, z1]
    bounds = ((min(xs), max(xs), min(zs), max(zs)) if xs
              else (wx0, wx1, 0.0, wafer.top))
    return pieces, tuple(wafer.breaks), bounds


def draw_section(ax, wafer, *, y=None, zscale=1.0, labels=False,
                 label_size=None, breaks=True, break_style=BREAK_STYLE,
                 edge_lw=0.55, frame=True, marker=None, marker_size=2.6):
    """Draw the x-z section of ``wafer`` at plane ``y`` into ``ax``.

    ``zscale`` multiplies thickness (use it for thin films on thick
    substrates); ``labels`` is ``False``, ``"all"`` or a list of feature
    names/refs (callouts in a left-hand column); stack breaks are drawn as
    empty intervals with zigzag marks and a right-hand bracket. Returns the
    pieces drawn (see :func:`section_pieces`).
    """
    from .iso import LABEL_PT
    from .process import Layer, StackBreak, _shape_bounds
    if y is None:
        _, wy0, _, wy1 = _shape_bounds(wafer.wafer_footprint)
        y = 0.5 * (wy0 + wy1)
    pieces, brks, (bx0, bx1, bz0, bz1) = section_pieces(wafer, y)
    zs = lambda z: z * zscale                                   # noqa: E731
    W = max(bx1 - bx0, 1e-9)

    for piece in pieces:
        polys = [[(x0, zs(z0)), (x1, zs(z0)), (x1, zs(z1)), (x0, zs(z1))]
                 for x0, x1, z0, z1 in piece["rects"]]
        ax.add_collection(PolyCollection(
            polys, facecolors=to_rgba(piece["color"], piece.get("alpha", 1.0)),
            edgecolors="none", zorder=2))
        segs = [[(a[0], zs(a[1])), (b[0], zs(b[1]))]
                for a, b in _outline(piece["rects"])]
        ax.add_collection(LineCollection(
            segs, colors=mix(piece["color"], "#000000", 0.45),
            linewidths=edge_lw, zorder=3))

    size = label_size or LABEL_PT
    if breaks:
        for brk in brks:
            gap = brk.z1 - brk.z0
            if break_style == "zigzag":
                amp, step = 0.16 * gap, 0.35 * gap
                xx = np.arange(bx0 - 0.03 * W, bx1 + 0.03 * W + step, step)
                for z_edge, sign in ((brk.z0, 1), (brk.z1, -1)):
                    zz = zs(z_edge) + sign * amp * zscale * \
                        np.where(np.arange(len(xx)) % 2, 1.0, 0.0)
                    ax.plot(xx, zz, color=C_GREY, lw=0.7, zorder=4,
                            solid_capstyle="round")
            lo = brk.span[0] if brk.span[0] is not None else brk.z0
            hi = brk.span[1] if brk.span[1] is not None else brk.z1
            xb = bx1 + 0.05 * W
            tick = 0.015 * W
            ax.plot([xb - tick, xb, xb, xb - tick],
                    [zs(lo), zs(lo), zs(hi), zs(hi)], color=C_GREY, lw=0.7,
                    zorder=4)
            ax.text(xb + tick, zs(0.5 * (lo + hi)), brk.caption,
                    fontsize=size, color=C_SLATE, ha="left", va="center")

    feats = wafer._label_features(labels)
    if feats:
        H = max(bz1 - bz0, 1e-9)
        items = []
        for f in feats:
            if isinstance(f, StackBreak):
                continue
            xr = chord(f.shape, y) if f.shape is not None else None
            x0, x1 = xr or (bx0, bx1)
            if isinstance(f, Layer):
                z = 0.5 * (f.z0 + f.z1)
                items.append((f.name, x0, z))
            else:
                items.append((f.name, 0.5 * (x0 + x1), f.z1))
        items.sort(key=lambda t: t[2])
        min_gap = 0.06 * H
        ys = []
        for name, xa, z in items:
            yt = z if not ys else max(z, ys[-1] + min_gap)
            ys.append(yt)
        for (name, xa, z), yt in zip(items, ys):
            ax.annotate(name, xy=(xa, zs(z)), xytext=(bx0 - 0.06 * W, zs(yt)),
                        fontsize=size, color=C_SLATE, ha="right", va="center",
                        arrowprops=dict(arrowstyle="-", color=C_GREY, lw=0.6,
                                        shrinkA=0, shrinkB=0), zorder=5)
            if marker == "dot":
                ax.plot(xa, zs(z), marker="o", ms=marker_size, color=C_SLATE,
                        markeredgewidth=0, zorder=6)

    ax.set_aspect("equal")
    ax.set_axis_off()
    pad_x = 0.36 * W if (breaks and brks) or feats else 0.06 * W
    left = 0.30 * W if feats else 0.06 * W
    ax.set_xlim(bx0 - left, bx1 + pad_x)
    ax.set_ylim(zs(bz0) - 0.05 * zs(bz1 - bz0), zs(bz1) + 0.05 * zs(bz1 - bz0))
    return pieces
