"""True solid-modelling backend for 3D semiconductor structures.

A small, LLM-readable API for real 3D structure diagrams:

* geometry and booleans: trimesh + the manifold3d engine (robust CSG --
  VTK's native boolean filter is notoriously fragile and is not used);
* rendering: PyVista/VTK with the book's diagram style (white
  background, parallel isometric camera, flat material colors from
  semi_structures.style, slate feature edges, and screen-facing callout labels).

    s = Scene()
    s.box((0, 0, 0), (10, 7, 0.9), "W")            # a word-line plate
    s.drill_hole(x=3, y=2, r=1.1)                   # real circular hole
    s.tube((3, 2), z0=0, r_out=1.0, r_in=0.8, h=5, material="SiO2")
    s.cylinder((3, 2), z0=0, r=0.25, h=6, material="Si")
    s.sphere((5, 3, 6), r=0.8, material="Cu")
    s.cut(handle, tool_mesh)                        # arbitrary boolean
    s.label("Cu feature", anchor=(5, 3, 6), position=(0.8, 0.3), size=8.2)
    s.render("out.png", print_width_in=6.3)         # 300 dpi at 6.3 in

Typography follows the book's law: every text size is given in POINTS AT
PRINT WIDTH, never in pixels. ``render()``/``render_array()`` take the
printed width of the image (``print_width_in``, default
``PRINT_TEXTWIDTH_IN``) and a ``dpi`` (default 300), derive the pixel window
from them, and convert point sizes to pixels internally. Sizes below
``MIN_PRINT_PT`` are refused.

Use semi_structures.iso for quick axis-aligned diagrams; use this backend when
real geometry -- circular holes, concentric shells, arbitrary cuts -- must be
visible. Materials are semi_structures.style.MATERIAL keys or raw hex.
"""
from __future__ import annotations

import warnings

import numpy as np
import pyvista as pv
import trimesh
from PIL import Image, ImageDraw, ImageFont
from vtkmodules.vtkRenderingCore import vtkCoordinate

from .style import (
    C_GREY, C_SLATE, MATERIAL, MIN_PRINT_PT, PRINT_TEXTWIDTH_IN, alpha_for,
)

_SECTIONS = 96     # circumferential resolution
DEFAULT_ASPECT = 0.78          # window height / width when derived from dpi
LABEL_PT = 8.2                 # callouts: the annotation rung of the ladder
TITLE_PT = 10.0                # panel titles
LEADER_PT = 0.6                # leader line width, in points

_CORNERS = {
    "upper_left": (0.0, 0.0, "la"), "upper_right": (1.0, 0.0, "ra"),
    "lower_left": (0.0, 1.0, "ld"), "lower_right": (1.0, 1.0, "rd"),
    "upper_edge": (0.5, 0.0, "ma"), "lower_edge": (0.5, 1.0, "md"),
}


def _color(material):
    return MATERIAL[material][0] if material in MATERIAL else material


def _radius(radius, diameter, what):
    """Accept a radius or a diameter, never both."""
    if (radius is None) == (diameter is None):
        raise ValueError(f"{what}: give exactly one of radius or diameter")
    value = float(radius if radius is not None else diameter / 2.0)
    if value < 0:
        raise ValueError(f"{what}: radius cannot be negative")
    return value


def _frustum(r_bottom, r_top, height, sections=_SECTIONS):
    """A closed truncated cone about the z axis, base at z = 0.

    ``r_top = 0`` collapses the upper ring to an apex, which gives a true
    cone. Both radii zero is not a solid and is refused by the caller.
    """
    angle = np.linspace(0.0, 2.0 * np.pi, sections, endpoint=False)
    cos, sin = np.cos(angle), np.sin(angle)
    vertices = [np.column_stack([r_bottom * cos, r_bottom * sin,
                                 np.zeros(sections)])]
    faces = []

    if r_top > 0:
        vertices.append(np.column_stack([r_top * cos, r_top * sin,
                                         np.full(sections, height)]))
        verts = np.vstack(vertices)
        for i in range(sections):
            j = (i + 1) % sections
            lo_i, lo_j = i, j
            hi_i, hi_j = sections + i, sections + j
            faces += [[lo_i, lo_j, hi_j], [lo_i, hi_j, hi_i]]
        top_centre = len(verts)
        verts = np.vstack([verts, [[0.0, 0.0, height]]])
        for i in range(sections):
            j = (i + 1) % sections
            faces.append([sections + i, sections + j, top_centre])
    else:
        verts = vertices[0]
        apex = len(verts)
        verts = np.vstack([verts, [[0.0, 0.0, height]]])
        for i in range(sections):
            j = (i + 1) % sections
            faces.append([i, j, apex])

    bottom_centre = len(verts)
    verts = np.vstack([verts, [[0.0, 0.0, 0.0]]])
    for i in range(sections):
        j = (i + 1) % sections
        faces.append([j, i, bottom_centre])

    # The faces above are already wound counter-clockwise as seen from
    # outside, so the mesh needs no repair. Calling fix_normals() here would
    # drag in scipy, which is not a dependency of this package.
    return trimesh.Trimesh(vertices=verts, faces=np.asarray(faces))


def _to_pv(mesh):
    faces = np.hstack([np.full((len(mesh.faces), 1), 3), mesh.faces])
    return pv.PolyData(mesh.vertices, faces.ravel())


def _difference(a, b):
    return trimesh.boolean.difference([a, b], engine="manifold")


def _check_pt(size, what):
    size = float(size)
    if size < MIN_PRINT_PT:
        raise ValueError(
            f"{what} is {size:g} pt; the print floor is {MIN_PRINT_PT:g} pt "
            "(sizes are points at print width, not pixels)")
    return size


def _points(size, font_size, what):
    """Resolve the size argument, accepting the deprecated ``font_size``."""
    if font_size is not None:
        warnings.warn(
            f"{what}: 'font_size' is deprecated; pass 'size' in points at "
            "print width", DeprecationWarning, stacklevel=3)
        size = font_size
    return _check_pt(size, what)


class Scene:
    def __init__(self, font=None, font_bold=None):
        """``font``/``font_bold`` are optional TrueType file names or paths
        tried before the portable Arial / DejaVu Sans fallback stack."""
        self.parts = []          # [trimesh, color hex, opacity]
        self.labels = []         # callouts tied to 3D anchors
        self.text_overlays = []  # screen-space titles and notes
        self.brackets = []       # span brackets between two 3D points
        self.triads = []         # labelled x, y, z coordinate axes
        self.font = font
        self.font_bold = font_bold

    # -- primitives ----------------------------------------------------------

    def add(self, mesh, material, opacity=None):
        """Add a trimesh part. ``opacity=None`` takes the material's default
        (``style.alpha_for``: 1.0 except for the transparent crystals such as
        ``"sapphire"`` and ``"SiC-wafer"``); pass a number to override."""
        if opacity is None:
            opacity = alpha_for(material)
        self.parts.append([mesh, _color(material), float(opacity)])
        return len(self.parts) - 1

    def box(self, origin, size, material, opacity=None, bow=None):
        """Axis-aligned box; ``origin`` is the minimum (x, y, z) corner.

        ``bow=(sx, sy)`` bends the slab: the top and bottom surfaces take
        the parabolic displacement ``w = -sx*((x-cx)/(dx/2))**2 -
        sy*((y-cy)/(dy/2))**2`` so ``sx``, ``sy`` are the edge-to-centre
        sagittas along x and y -- positive bows the slab into a dome
        (centre high, as a compressive film bows a wafer), negative into a
        bowl (tensile). Films drawn with the same ``bow`` on top of a bowed
        wafer stay conformal to it. A scalar ``bow`` applies to both axes;
        the mesh is subdivided so the bend is smooth.
        """
        mesh = trimesh.creation.box(extents=size)
        mesh.apply_translation([o + s / 2 for o, s in zip(origin, size)])
        if bow:
            sx, sy = (bow, bow) if np.isscalar(bow) else bow
            dx, dy = float(size[0]), float(size[1])
            mesh = mesh.subdivide_to_size(0.04 * max(dx, dy))
            cx, cy = origin[0] + dx / 2, origin[1] + dy / 2
            v = mesh.vertices.copy()
            v[:, 2] -= (sx * ((v[:, 0] - cx) / (dx / 2)) ** 2 +
                        sy * ((v[:, 1] - cy) / (dy / 2)) ** 2)
            mesh = trimesh.Trimesh(vertices=v, faces=mesh.faces, process=False)
        return self.add(mesh, material, opacity)

    def cylinder(self, center_xy, z0, r=None, h=None, material=None,
                 opacity=None, *, diameter=None):
        """Vertical cylinder. Give ``r`` or ``diameter``."""
        radius = _radius(r, diameter, "cylinder")
        mesh = trimesh.creation.cylinder(radius=radius, height=h,
                                         sections=_SECTIONS)
        mesh.apply_translation([center_xy[0], center_xy[1], z0 + h / 2])
        return self.add(mesh, material, opacity)

    def cone(self, center_xy, z0, h, material, *, r_bottom=None, r_top=None,
             d_bottom=None, d_top=None, opacity=None):
        """Vertical truncated cone (frustum) standing on ``z0``.

        Each end takes a radius or a diameter, so a tapered via can be
        written either way::

            s.cone((x, y), z0=0, h=2.0, material="W", r_bottom=0.6, r_top=0.3)
            s.cone((x, y), z0=0, h=2.0, material="W", d_bottom=1.2, d_top=0.0)

        A top radius of zero gives a true cone. The two ends may not both be
        zero, and a negative radius is refused.
        """
        bottom = _radius(r_bottom, d_bottom, "cone bottom")
        top = _radius(r_top, d_top, "cone top")
        if bottom <= 0 and top <= 0:
            raise ValueError("cone needs a positive radius at one end")
        height = float(h)
        if height <= 0:
            raise ValueError("cone height must be positive")
        if bottom == 0:                      # point down: build it inverted
            mesh = _frustum(top, 0.0, height)
            mesh.apply_transform(trimesh.transformations.rotation_matrix(
                np.pi, [1, 0, 0]))
            mesh.apply_translation([0.0, 0.0, height])
        else:
            mesh = _frustum(bottom, top, height)
        mesh.apply_translation([center_xy[0], center_xy[1], z0])
        return self.add(mesh, material, opacity)

    def tube(self, center_xy, z0, r_out, r_in, h, material, opacity=None):
        """Annular shell, built directly -- no boolean needed."""
        mesh = trimesh.creation.annulus(r_min=r_in, r_max=r_out, height=h,
                                        sections=_SECTIONS)
        mesh.apply_translation([center_xy[0], center_xy[1], z0 + h / 2])
        return self.add(mesh, material, opacity)

    def sphere(self, center, r, material, opacity=None):
        mesh = trimesh.creation.icosphere(subdivisions=3, radius=r)
        mesh.apply_translation(center)
        return self.add(mesh, material, opacity)

    def sphere_array(self, x_range, y_range, pitch, z, r, material):
        """Grid of spheres for solder balls or microbumps."""
        handles = []
        for bx in np.arange(x_range[0], x_range[1] + 1e-9, pitch):
            for by in np.arange(y_range[0], y_range[1] + 1e-9, pitch):
                handles.append(self.sphere((bx, by, z), r, material))
        return handles

    def multilayer(self, origin, xy_size, layers, repeats=1, bow=None):
        """Repeating stack of blanket boxes from `origin` upward:
        layers = [(material, thickness), ...] repeated `repeats` times.
        Returns the handles. s.multilayer((0, 0, 0.5), (10, 7),
        [("W", 0.2), ("Si", 0.3)], repeats=6) builds an XRR mirror.
        ``bow`` bends every layer conformally (see :meth:`box`)."""
        x0, y0, z = origin
        handles = []
        for _ in range(repeats):
            for material, thickness in layers:
                handles.append(self.box((x0, y0, z),
                                        (xy_size[0], xy_size[1],
                                         thickness), material, bow=bow))
                z += thickness
        return handles

    # -- boolean operations --------------------------------------------------

    def _live(self, handle):
        mesh = self.parts[handle][0]
        return mesh is not None and not mesh.is_empty

    def cut(self, target, tool):
        """Boolean-subtract a trimesh tool from one part (by handle)."""
        if not self._live(target):
            return
        result = _difference(self.parts[target][0], tool)
        self.parts[target][0] = None if result is None or result.is_empty \
            else result

    def _targets(self, only):
        handles = range(len(self.parts)) if only is None else only
        return [h for h in handles if self._live(h)]

    def drill_rect(self, x, y, dx, dy, z0=-1e3, z1=1e3, only=None):
        """Cut a rectangular notch or trench through selected parts."""
        tool = trimesh.creation.box(extents=(dx, dy, z1 - z0))
        tool.apply_translation([x + dx / 2, y + dy / 2,
                                0.5 * (z0 + z1)])
        for i in self._targets(only):
            (xmin, ymin, _), (xmax, ymax, _) = self.parts[i][0].bounds
            if xmin < x + dx and xmax > x and ymin < y + dy and ymax > y:
                self.cut(i, tool)

    def cutaway(self, x=None, y=None, z=None, only=None):
        """Remove a camera-facing half-space or corner of the model.

        One supplied plane gives a half-section; two give a quarter-section.
        Every part is cut separately so exposed section faces remain capped
        in their material colors.
        """
        if x is None and y is None and z is None:
            raise ValueError("cutaway requires at least one cutting plane")
        big = 1.0e3
        x0, x1 = (-big if x is None else x, big)
        y0, y1 = (-big if y is None else y, big)
        z0, z1 = (-big if z is None else z, big)
        cutter = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
        cutter.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2,
                                  (z0 + z1) / 2])
        for i in self._targets(only):
            self.cut(i, cutter)

    def drill_hole(self, x, y, r, z0=-1e3, z1=1e3, only=None):
        """Drill a vertical circular hole through parts (all parts whose
        footprint contains the hole, or the handles in `only`)."""
        tool = trimesh.creation.cylinder(radius=r, height=z1 - z0,
                                         sections=_SECTIONS)
        tool.apply_translation([x, y, 0.5 * (z0 + z1)])
        for i in self._targets(only):
            (xmin, ymin, _), (xmax, ymax, _) = self.parts[i][0].bounds
            if xmin - r < x < xmax + r and ymin - r < y < ymax + r:
                self.cut(i, tool)

    def bounds(self):
        """(min, max) corners over all live parts, or None if empty."""
        live = [self.parts[h][0] for h in self._targets(None)]
        if not live:
            return None
        lo = np.min([m.bounds[0] for m in live], axis=0)
        hi = np.max([m.bounds[1] for m in live], axis=0)
        return lo, hi

    # -- labels --------------------------------------------------------------

    def label(self, text, anchor, position=None, *, via=None,
              color=C_SLATE, size=LABEL_PT, bold=False,
              line=True, line_color=C_GREY, line_width=LEADER_PT,
              justify="left", marker=None, marker_size=2.6, font_size=None):
        """Add a screen-facing callout tied to a 3D point.

        ``anchor`` is always a world-space feature point. A two-element
        ``position`` places the text in normalized screen coordinates
        (0, 0 is the upper-left corner); this is the preferred publication
        mode because the label layout stays stable while the 3D anchor follows
        the camera. A three-element ``position`` places text in world space
        and draws the leader as a 3D line that geometry can occlude. ``via``
        may contain matching 2D or 3D points to route an elbowed leader.

        ``size`` and ``line_width`` are points at print width (see
        ``render``); ``size`` may not go below ``MIN_PRINT_PT``.
        ``marker="dot"`` ends the leader in a filled dot at the anchor
        ("stick and ball"), ``marker_size`` its diameter in points, drawn in
        the label ``color``.
        """
        anchor = np.asarray(anchor, dtype=float)
        position = anchor if position is None else np.asarray(position,
                                                               dtype=float)
        if anchor.shape != (3,) or position.shape not in ((2,), (3,)):
            raise ValueError("label anchor must be 3D; position must be 2D or 3D")
        mode = "screen" if position.shape == (2,) else "world"
        point_dim = 2 if mode == "screen" else 3
        if via is None:
            via_points = []
        else:
            via_array = np.asarray(via, dtype=float)
            if via_array.shape == (point_dim,):
                via_points = [via_array]
            elif via_array.ndim == 2 and via_array.shape[1] == point_dim:
                via_points = [point for point in via_array]
            else:
                raise ValueError("label via points must match position dimensions")
        if justify not in ("left", "right", "center"):
            raise ValueError("justify must be left, right, or center")
        self.labels.append({
            "text": str(text), "anchor": anchor, "position": position,
            "via": via_points, "mode": mode, "color": color,
            "size": _points(size, font_size, f"label {text!r}"),
            "bold": bool(bold), "line": bool(line),
            "line_color": line_color, "line_width": float(line_width),
            "justify": justify, "marker": marker,
            "marker_size": float(marker_size),
        })
        return len(self.labels) - 1

    def axes(self, origin=None, length=None, labels=("x", "y", "z"), *,
             color=C_SLATE, size=LABEL_PT, line_width=1.4, offset=0.14,
             pad=0.35):
        """Add a labelled x, y, z triad to the scene.

        With no ``origin`` the triad is placed just outside the model's
        minimum corner so it sits beside the structure rather than inside it,
        and ``length`` defaults to a fifth of the largest span. Pass either
        explicitly to place it by hand. ``labels`` may be any three strings,
        or None to draw the arms unlabelled.

        The arms are 3D lines, so the model occludes them like any other
        geometry. ``size`` is points at print width, as everywhere else, and
        ``pad`` moves each label beyond the tip of its arm in units of the
        label size.
        """
        if origin is None or length is None:
            bounds = self.bounds()
            if bounds is None:
                raise ValueError(
                    "axes() needs geometry to size itself, or an explicit "
                    "origin and length")
            low, high = bounds
            span = float(np.max(high - low))
            if length is None:
                length = 0.20 * span
            if origin is None:
                origin = (float(low[0] - offset * span),
                          float(low[1] - offset * span), float(low[2]))
        origin = np.asarray(origin, dtype=float)
        if origin.shape != (3,):
            raise ValueError("axes origin must be a 3D point")
        length = float(length)
        if length <= 0:
            raise ValueError("axes length must be positive")
        if labels is not None and len(labels) != 3:
            raise ValueError("axes labels must be three strings, or None")
        self.triads.append({
            "origin": origin, "length": length,
            "labels": None if labels is None else [str(t) for t in labels],
            "color": color, "size": _check_pt(size, "axes labels"),
            "line_width": float(line_width), "pad": float(pad),
        })
        return len(self.triads) - 1

    def bracket(self, text, lo, hi, *, dx=0.035, tick=0.012,
                size=LABEL_PT, color=C_SLATE, line_color=C_GREY,
                line_width=LEADER_PT):
        """A screen bracket embracing the span between 3D points ``lo`` and
        ``hi`` (drawn beside their projections, ``dx`` of the image width to
        the right, ticks ``tick`` wide pointing at the structure) with
        ``text`` beside it -- e.g. "x100 repeats (85 not drawn)" next to an
        elided stack. ``size`` is points at print width."""
        lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
        if lo.ndim == 1:
            lo, hi = lo[None, :], hi[None, :]
        if lo.shape != hi.shape or lo.shape[1:] != (3,):
            raise ValueError("bracket endpoints must be 3D points, or equal "
                             "lists of candidate 3D point pairs")
        # several candidate edges may be given (e.g. the four vertical
        # edges of a block); the one that projects furthest right is used,
        # so the bracket sits beside the silhouette for any camera.
        self.brackets.append({
            "text": str(text), "lo": lo, "hi": hi, "dx": float(dx),
            "tick": float(tick), "size": _check_pt(size, f"bracket {text!r}"),
            "color": color, "line_color": line_color,
            "line_width": float(line_width),
        })
        return len(self.brackets) - 1

    def text2d(self, text, position="upper_left", *, color=C_SLATE,
               size=TITLE_PT, bold=False, font_size=None, shadow=None):
        """Add fixed screen-space text such as a figure title.

        ``position`` is a corner name (``upper_left``, ``upper_right``,
        ``lower_left``, ``lower_right``, ``upper_edge``, ``lower_edge``) or a
        normalized ``(x, y)`` pair with (0, 0) at the upper-left; ``size`` is
        points at print width.
        """
        if shadow is not None:
            warnings.warn("text2d: 'shadow' is ignored", DeprecationWarning,
                          stacklevel=2)
        if isinstance(position, str):
            if position not in _CORNERS:
                raise ValueError(f"unknown text position {position!r}")
        else:
            position = tuple(float(v) for v in position)
            if len(position) != 2:
                raise ValueError("text position must be a corner name or (x, y)")
        self.text_overlays.append({
            "text": str(text), "position": position, "color": color,
            "size": _points(size, font_size, f"text {text!r}"),
            "bold": bool(bold),
        })
        return len(self.text_overlays) - 1

    def _screen_font(self, size_px, bold=False):
        """Load the callout font: user choice first, then Arial, then DejaVu."""
        names = [self.font_bold if bold else self.font]
        names += (["arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else
                  ["arial.ttf", "DejaVuSans.ttf"])
        for name in names:
            if not name:
                continue
            try:
                return ImageFont.truetype(name, size=size_px)
            except OSError:
                pass
        return ImageFont.load_default(size=size_px)

    def _overlay_text(self, image, pl, px_per_pt):
        """Composite every text item onto the rendered pixels.

        Screen-mode callouts get their anchor projected from 3D and a leader
        drawn in 2D; world-mode callouts already have a 3D leader from
        ``_plot`` and only receive their text here, at the projected position;
        titles are placed by corner or normalized coordinate.
        """
        if not (self.labels or self.text_overlays or self.brackets
                or self.triads):
            return image
        pil = Image.fromarray(image)
        draw = ImageDraw.Draw(pil)
        width, height = pil.size

        def project(world):
            coord = vtkCoordinate()
            coord.SetCoordinateSystemToWorld()
            coord.SetValue(*world)
            ax, ay = coord.GetComputedDisplayValue(pl.renderer)
            return (int(round(ax)), int(round(height - ay)))

        def to_px(point):
            return (int(round(point[0] * width)),
                    int(round(point[1] * height)))

        for item in self.labels:
            size_px = max(1, int(round(item["size"] * px_per_pt)))
            font = self._screen_font(size_px, item["bold"])
            anchor = {"left": "lm", "right": "rm", "center": "mm"}[
                item["justify"]]
            align = item["justify"] if item["justify"] != "center" else "center"
            spacing = max(2, size_px // 5)
            anchor_px = project(item["anchor"])
            if item.get("marker") == "dot":
                r = 0.5 * item["marker_size"] * px_per_pt
                draw.ellipse([anchor_px[0] - r, anchor_px[1] - r,
                              anchor_px[0] + r, anchor_px[1] + r],
                             fill=item["color"])
            if item["mode"] == "screen":
                position_px = to_px(item["position"])
                bbox = draw.multiline_textbbox(position_px, item["text"],
                                               font=font, anchor=anchor,
                                               align=align, spacing=spacing)
                # Stop the leader at the nearest edge of the text box instead
                # of drawing it through the label itself.
                routed = [project(item["anchor"]),
                          *(to_px(v) for v in item["via"])]
                px, py = routed[-1]
                left, top, right, bottom = bbox
                if px < left:
                    endpoint = (left, min(max(py, top), bottom))
                elif px > right:
                    endpoint = (right, min(max(py, top), bottom))
                elif py < top:
                    endpoint = (min(max(px, left), right), top)
                else:
                    endpoint = (min(max(px, left), right), bottom)
                if item["line"]:
                    draw.line([*routed, endpoint], fill=item["line_color"],
                              width=max(1, int(round(item["line_width"] *
                                                   px_per_pt))),
                              joint="curve")
            else:
                position_px = project(item["position"])
            draw.multiline_text(position_px, item["text"], font=font,
                                fill=item["color"], anchor=anchor, align=align,
                                spacing=spacing)

        for triad in self.triads:
            if triad["labels"] is None:
                continue
            size_px = max(1, int(round(triad["size"] * px_per_pt)))
            font = self._screen_font(size_px, False)
            base = project(triad["origin"])
            for axis, text in enumerate(triad["labels"]):
                tip = triad["origin"].copy()
                tip[axis] += triad["length"]
                x, y = project(tip)
                # push the label a little further along the arm's own screen
                # direction, so it clears the line end at any camera angle
                dx, dy = x - base[0], y - base[1]
                norm = max(1.0, (dx * dx + dy * dy) ** 0.5)
                reach = triad["pad"] * size_px
                # a thin white outline keeps the letter readable where an
                # arm passes in front of the structure
                draw.text((x + reach * dx / norm, y + reach * dy / norm), text,
                          font=font, fill=triad["color"], anchor="mm",
                          stroke_width=max(1, size_px // 7),
                          stroke_fill="#FFFFFF")

        for item in self.brackets:
            pairs = [(project(lo), project(hi))
                     for lo, hi in zip(item["lo"], item["hi"])]
            tick_px = item["tick"] * width
            size_px = max(1, int(round(item["size"] * px_per_pt)))
            font = self._screen_font(size_px, False)
            spacing = max(2, size_px // 5)
            text_w = draw.multiline_textbbox((0, 0), item["text"], font=font,
                                             spacing=spacing)[2]
            # beside the rightmost silhouette edge, unless the left side has
            # more room for the text (mirrored bracket, right-aligned text)
            right = max(pairs, key=lambda p: max(p[0][0], p[1][0]))
            left = min(pairs, key=lambda p: min(p[0][0], p[1][0]))
            room_right = width - max(right[0][0], right[1][0])
            room_left = min(left[0][0], left[1][0])
            need = item["dx"] * width + 0.8 * tick_px + text_w
            if room_right >= need or room_right >= room_left:
                (xl, yl), (xh, yh) = right
                xb = max(xl, xh) + item["dx"] * width
                side = 1
            else:
                (xl, yl), (xh, yh) = left
                xb = min(xl, xh) - item["dx"] * width
                side = -1
            lw = max(1, int(round(item["line_width"] * px_per_pt)))
            draw.line([(xb - side * tick_px, yl), (xb, yl), (xb, yh),
                       (xb - side * tick_px, yh)], fill=item["line_color"],
                      width=lw, joint="curve")
            draw.multiline_text((int(round(xb + side * 0.8 * tick_px)),
                                 int(round(0.5 * (yl + yh)))), item["text"],
                                font=font, fill=item["color"],
                                anchor="lm" if side > 0 else "rm",
                                align="left" if side > 0 else "right",
                                spacing=spacing)

        margin = int(round(0.02 * width))
        for item in self.text_overlays:
            size_px = max(1, int(round(item["size"] * px_per_pt)))
            font = self._screen_font(size_px, item["bold"])
            pos = item["position"]
            if isinstance(pos, str):
                fx, fy, anchor = _CORNERS[pos]
                x = margin + fx * (width - 2 * margin)
                y = margin + fy * (height - 2 * margin)
                align = {"l": "left", "r": "right", "m": "center"}[anchor[0]]
            else:
                x, y = pos[0] * width, pos[1] * height
                anchor, align = "la", "left"
            draw.multiline_text((int(round(x)), int(round(y))), item["text"],
                                font=font, fill=item["color"], anchor=anchor,
                                align=align, spacing=max(2, size_px // 5))
        return np.asarray(pil)

    # -- rendering -----------------------------------------------------------

    def _plot(self, window, zoom, azimuth, elevation, edges, px_per_pt,
              background="white", edge_color=C_SLATE):
        pl = pv.Plotter(off_screen=True, window_size=list(window))
        pl.set_background(background)
        if any(part[2] < 1.0 for part in self.parts):
            pl.enable_depth_peeling(number_of_peels=8)
        for mesh, color, opacity in self.parts:
            if mesh is None or mesh.is_empty:
                continue
            pvm = _to_pv(mesh)
            pl.add_mesh(pvm, color=color, smooth_shading=False,
                        specular=0.08, diffuse=0.75, ambient=0.35,
                        opacity=opacity)
            if edges:
                fe = pvm.extract_feature_edges(feature_angle=38)
                if fe.n_points:
                    pl.add_mesh(fe, color=edge_color, line_width=1.4,
                                opacity=max(opacity, 0.55))
        # Axis arms are added before the camera is fitted, so a triad
        # placed outside the model is still inside the frame.
        for i, triad in enumerate(self.triads):
            origin, length = triad["origin"], triad["length"]
            for axis in range(3):
                tip = origin.copy()
                tip[axis] += length
                pl.add_lines(np.array([origin, tip]), color=triad["color"],
                             width=max(1.0, triad["line_width"] * px_per_pt),
                             connected=True, name=f"axis-{i}-{axis}")
        pl.enable_parallel_projection()
        pl.view_isometric()
        pl.camera.azimuth = azimuth
        pl.camera.elevation = elevation
        pl.camera.zoom(zoom)
        for i, item in enumerate(self.labels):
            if item["mode"] != "world" or not item["line"]:
                continue
            points = [item["anchor"], *item["via"], item["position"]]
            if not np.allclose(points[0], points[-1]):
                pl.add_lines(np.asarray(points), color=item["line_color"],
                             width=max(1.0, item["line_width"] * px_per_pt),
                             connected=True, name=f"label-leader-{i}")
        return pl

    @staticmethod
    def _window(window, print_width_in, dpi, aspect):
        pw = float(print_width_in or PRINT_TEXTWIDTH_IN)
        if pw <= 0 or dpi <= 0:
            raise ValueError("print_width_in and dpi must be positive")
        if window is None:
            w = int(round(pw * dpi))
            window = (w, int(round(w * aspect)))
        px_per_pt = window[0] / (pw * 72.0)
        return tuple(int(v) for v in window), px_per_pt

    def _render_pixels(self, *, print_width_in, dpi, window, aspect, zoom,
                       azimuth, elevation, edges, transparent,
                       background="white", edge_color=C_SLATE):
        window, px_per_pt = self._window(window, print_width_in, dpi, aspect)
        pl = self._plot(window, zoom, azimuth, elevation, edges, px_per_pt,
                        background, edge_color)
        pl.render()
        img = pl.screenshot(None, transparent_background=transparent,
                            return_img=True)
        img = self._overlay_text(img, pl, px_per_pt)
        pl.close()
        return img

    def render(self, path, *, print_width_in=None, dpi=300, window=None,
               aspect=DEFAULT_ASPECT, zoom=1.0, azimuth=-32.0,
               elevation=24.0, edges=True, background="white",
               edge_color=C_SLATE):
        """Render to a PNG file.

        ``print_width_in`` is the width at which the image will be printed
        (default ``PRINT_TEXTWIDTH_IN``); with ``window=None`` the pixel size
        is ``print_width_in * dpi`` wide by ``aspect`` times that high. All
        text is sized in points at that print width. ``background`` and
        ``edge_color`` (feature edges) default to the book's white/slate;
        pass a dark background and light edges/label colors for
        presentation-style renders.
        """
        img = self._render_pixels(
            print_width_in=print_width_in, dpi=dpi, window=window,
            aspect=aspect, zoom=zoom, azimuth=azimuth, elevation=elevation,
            edges=edges, transparent=False, background=background,
            edge_color=edge_color)
        Image.fromarray(img).save(path)
        return path

    def render_array(self, *, print_width_in=None, dpi=300, window=None,
                     aspect=DEFAULT_ASPECT, zoom=1.0, azimuth=-32.0,
                     elevation=24.0, edges=True, transparent=True,
                     background="white", edge_color=C_SLATE):
        """Render to an RGBA numpy array (transparent background by
        default) for embedding into matplotlib figures with imshow. Pass the
        printed width of the panel as ``print_width_in`` so text lands at
        its point size on the page."""
        return self._render_pixels(
            print_width_in=print_width_in, dpi=dpi, window=window,
            aspect=aspect, zoom=zoom, azimuth=azimuth, elevation=elevation,
            edges=edges, transparent=transparent, background=background,
            edge_color=edge_color)
