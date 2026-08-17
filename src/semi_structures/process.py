"""Backend-neutral process-flow DSL for semiconductor figures.

Structures are built the way a fab builds them, with verbs an LLM or a
process engineer can read directly:

    w = Wafer(size=(10, 6.4), substrate="Si", thickness=1.0)
    w.add_layer("SiO2", 0.35)                  # blanket deposition
    w.add_layer("Al", 0.6)
    slot = w.etch(Circle((x, y), radius=r))     # stops on substrate by default
    w.fill(slot, "Cu", overfill=1.0)           # damascene fill
    w.add_pad("W", x, y, dx, dy, 0.5)          # patterned feature on top
    w.implant(Rectangle((x, y), (dx, dy)), "SiP", depth=0.4)
    scene = w.scene()                           # auto-selects the solid backend

Materials are :mod:`semi_structures.style` keys (or raw hex). ``backend="auto"``
uses the dependency-light vector representation for every rectilinear flow --
axis-aligned films, etches of any depth, fills, mesas -- which it draws
exactly by splitting each solid at the etch limits. Curved or rotated shapes,
non-rectangular wafers and implants select the trimesh/manifold3d solid model,
rendered by PyVista. An explicitly requested vector backend rejects those
operations instead of silently drawing an approximation. ``Wafer.render()``
is the one-call route from model to picture with either backend.
"""
from __future__ import annotations

import functools
import inspect
import warnings
from dataclasses import dataclass, field
from math import cos, radians, sin, sqrt, tan
from typing import Union

from .iso import Box, slab_with_holes
from .style import MATERIAL, alpha_for

# ---- units ------------------------------------------------------------------
# Model coordinates are plain floats; these multipliers make nanometre-based
# scripts read naturally (Wafer(size=(2 * um, 1.5 * um)), etch depth 40 * nm).
# Existing scripts that use arbitrary drawing units are unaffected.
nm = 1.0
um = 1_000.0 * nm
mm = 1_000_000.0 * nm


def _records(method):
    """Record a DSL verb call on the wafer's replayable script.

    Only the outermost call is recorded, so a convenience verb that is built
    from other verbs -- ``add_multilayer`` from ``add_layer``, ``mesa`` from
    ``etch``, ``add_pad`` from ``add_feature`` -- stores the call the author
    actually wrote rather than the primitives it expands into. Arguments left
    at their defaults are omitted, which keeps a saved document close to the
    source that produced it. See :mod:`semi_structures.serialize`.
    """
    signature = inspect.signature(method)
    defaults = {name: parameter.default
                for name, parameter in signature.parameters.items()
                if parameter.default is not inspect.Parameter.empty}

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if getattr(self, "_recording_depth", 0):
            return method(self, *args, **kwargs)
        self._recording_depth = 1
        try:
            result = method(self, *args, **kwargs)
        finally:
            self._recording_depth = 0
        bound = signature.bind(self, *args, **kwargs)
        bound.apply_defaults()
        arguments = {name: value for name, value in bound.arguments.items()
                     if name != "self"
                     and not (name in defaults and value == defaults[name])}
        index = len(self._script)
        self._script.append((method.__name__, arguments))
        # Remember where each produced feature came from, so a later verb can
        # reference it (etch(stop_on=...), fill(hole), strip(layer)) without
        # depending on names.
        if isinstance(result, (list, tuple)):
            for item, feature in enumerate(result):
                self._produced.setdefault(id(feature),
                                          {"op": index, "item": item})
        elif result is not None:
            self._produced.setdefault(id(result), {"op": index})
        return result

    # Marks this method as replayable. Deserialization uses the mark as an
    # allowlist, so a document can never reach a public method that merely
    # happens to exist (to_json would otherwise write a file of its choosing).
    wrapper._dsl_verb = True
    return wrapper


def _fill_color(material):
    return MATERIAL[material][0] if material in MATERIAL else material


@dataclass
class Layer:
    """A deposited solid: blanket film, backside film, or local feature.

    Returned by :meth:`Wafer.add_layer`, :meth:`Wafer.add_backside_layer`,
    :meth:`Wafer.add_feature` and :meth:`Wafer.add_pad`; pass it to
    ``etch(stop_on=...)`` or look it up again with :meth:`Wafer.find`.
    """

    z0: float
    dz: float
    material: str
    extent: tuple                  # (x0, y0, dx, dy)
    footprint: object = None       # Rectangle / Circle / Ellipse
    holes: list = field(default_factory=list)   # vector-path bookkeeping
    name: str | None = None
    kind: str = "layer"            # "layer" | "backside" | "feature"

    @property
    def z1(self):
        return self.z0 + self.dz

    @property
    def top(self):
        """Height of the upper surface (what an etch stops on)."""
        return self.z1

    @property
    def shape(self):
        return self.footprint

    def anchor_for(self, front="-y"):
        """A visible 3D point for callout leaders.

        Local features anchor at their top-face centre. Blanket films anchor
        at the middle of the side face that faces the camera -- ``front`` is
        ``"-y"`` for the vector-isometric engine (viewer at -x, -y) and
        ``"+y"`` for the solid backend's default camera (viewer at +x, +y) --
        so the leader lands on the film however many films sit above it.
        """
        x0, y0, x1, y1 = _shape_bounds(self.footprint)
        if self.kind == "feature":
            return (0.5 * (x0 + x1), 0.5 * (y0 + y1), self.z1)
        y_face = y1 if front == "+y" else y0
        return (0.5 * (x0 + x1), y_face, self.z0 + 0.5 * self.dz)

    @property
    def anchor(self):
        return self.anchor_for("-y")


def _positive_pair(values, what):
    values = tuple(float(value) for value in values)
    if len(values) != 2 or any(value <= 0 for value in values):
        raise ValueError(f"{what} must contain two positive values")
    return values


@dataclass(frozen=True)
class Rectangle:
    """A rectangular process region defined by center and full x/y size.

    Use :meth:`from_corner` when a lower-left corner is more natural.
    """

    center: tuple[float, float]
    size: tuple[float, float]
    rotation: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "center", tuple(float(v) for v in self.center))
        object.__setattr__(self, "size", _positive_pair(self.size, "size"))
        if len(self.center) != 2:
            raise ValueError("center must contain two coordinates")

    @classmethod
    def from_corner(cls, x, y, dx, dy, rotation=0.0):
        """Rectangle from its lower-left corner ``(x, y)`` and size."""
        return cls((x + dx / 2.0, y + dy / 2.0), (dx, dy), rotation)

    @property
    def corner(self):
        """Lower-left corner ``(x, y)`` (ignores rotation)."""
        return (self.center[0] - self.size[0] / 2.0,
                self.center[1] - self.size[1] / 2.0)


@dataclass(frozen=True)
class Circle:
    """A circular process region, by ``radius`` or ``diameter``."""

    center: tuple[float, float]
    radius: float | None = None
    diameter: float | None = None

    def __post_init__(self):
        object.__setattr__(self, "center", tuple(float(v) for v in self.center))
        if (self.radius is None) == (self.diameter is None):
            raise ValueError("circle requires exactly one of radius, diameter")
        radius = float(self.radius if self.radius is not None
                       else self.diameter / 2.0)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "diameter", 2.0 * radius)
        if len(self.center) != 2 or radius <= 0:
            raise ValueError("circle requires a 2D center and positive radius")


@dataclass(frozen=True)
class Ellipse:
    """An elliptical process region with optional in-plane rotation."""

    center: tuple[float, float]
    radii: tuple[float, float]
    rotation: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "center", tuple(float(v) for v in self.center))
        object.__setattr__(self, "radii", _positive_pair(self.radii, "radii"))
        if len(self.center) != 2:
            raise ValueError("center must contain two coordinates")


Shape = Union[Rectangle, Circle, Ellipse]


def _shape_bounds(shape):
    """Return the axis-aligned x/y bounds of a public process shape."""
    cx, cy = shape.center
    if isinstance(shape, Circle):
        rx = ry = shape.radius
    elif isinstance(shape, Ellipse):
        angle = radians(shape.rotation)
        rx0, ry0 = shape.radii
        rx = sqrt((rx0 * cos(angle)) ** 2 + (ry0 * sin(angle)) ** 2)
        ry = sqrt((rx0 * sin(angle)) ** 2 + (ry0 * cos(angle)) ** 2)
    else:
        angle = radians(shape.rotation)
        dx, dy = shape.size
        rx = 0.5 * (abs(dx * cos(angle)) + abs(dy * sin(angle)))
        ry = 0.5 * (abs(dx * sin(angle)) + abs(dy * cos(angle)))
    return cx - rx, cy - ry, cx + rx, cy + ry


def _notch_tool(footprint, notch, z0, z1):
    """Trimesh cutter for a V-notch or flat on a circular footprint."""
    import trimesh
    from math import atan2

    cx, cy = footprint.center
    r = footprint.radius
    a = radians(notch["angle"])
    ux, uy = cos(a), sin(a)                      # outward unit vector
    vx, vy = -uy, ux                             # tangent
    height = float(z1) - float(z0)
    if notch["kind"] == "V":
        depth = notch["depth"]
        apex = (cx + (r - depth) * ux, cy + (r - depth) * uy)
        # 90-degree opening: half-width equals distance from the apex; the
        # base sits well outside the rim so the cut runs clean through
        out = 2.5 * depth
        base_c = (cx + (r - depth + out) * ux, cy + (r - depth + out) * uy)
        p1 = (base_c[0] + out * vx, base_c[1] + out * vy)
        p2 = (base_c[0] - out * vx, base_c[1] - out * vy)
        import numpy as np
        mesh = trimesh.creation.extrude_triangulation(
            np.array([apex, p1, p2], dtype=float), np.array([[0, 1, 2]]),
            height)
        mesh.apply_translation((0.0, 0.0, float(z0)))
        return mesh
    # flat: everything beyond the chord at distance r - depth from centre
    half = 0.5 * notch["flat_length"]
    depth = r - sqrt(max(r * r - half * half, 0.0))
    box = trimesh.creation.box(extents=(2 * r, 4 * r, height))
    box.apply_translation((r + (r - depth), 0.0, 0.5 * (z0 + z1)))
    box.apply_transform(trimesh.transformations.rotation_matrix(
        a, (0.0, 0.0, 1.0)))
    box.apply_translation((cx, cy, 0.0))
    return box


def _shape_outline(shape, inset=0.0, sections=96):
    """Boundary polygon of ``shape`` about its own center, pulled in by
    ``inset`` on every side and returned counter-clockwise.

    A rectangle loses ``inset`` from each of its four sides, and a circle or
    ellipse loses it from each radius, so the sidewall angle is exact for a
    rectangle or a circle and is the natural reading for an ellipse.
    """
    import numpy as np

    if isinstance(shape, Rectangle):
        dx, dy = shape.size[0] - 2.0 * inset, shape.size[1] - 2.0 * inset
        points = np.array([(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]) / 2.0
        angle = radians(shape.rotation)
    elif isinstance(shape, Circle):
        r = shape.radius - inset
        t = np.linspace(0.0, 2.0 * np.pi, sections, endpoint=False)
        points = np.column_stack([r * np.cos(t), r * np.sin(t)])
        angle = 0.0
    elif isinstance(shape, Ellipse):
        rx, ry = shape.radii[0] - inset, shape.radii[1] - inset
        t = np.linspace(0.0, 2.0 * np.pi, sections, endpoint=False)
        points = np.column_stack([rx * np.cos(t), ry * np.sin(t)])
        angle = radians(shape.rotation)
    else:
        raise TypeError(f"unsupported process shape: {type(shape).__name__}")
    if angle:
        points = points @ np.array([[cos(angle), sin(angle)],
                                    [-sin(angle), cos(angle)]])
    return points


def _min_halfwidth(shape):
    """Smallest distance from a shape's center to its boundary."""
    if isinstance(shape, Rectangle):
        return 0.5 * min(shape.size)
    if isinstance(shape, Circle):
        return shape.radius
    if isinstance(shape, Ellipse):
        return min(shape.radii)
    raise TypeError(f"unsupported process shape: {type(shape).__name__}")


def _tapered_prism(shape, z0, z1, taper):
    """A frustum whose top cross-section is ``shape``.

    ``taper`` is the sidewall angle from vertical, in degrees. Positive is the
    ordinary etch profile, wider at the top, and the floor is inset by
    ``height * tan(taper)`` on every side. Negative is re-entrant.
    """
    import numpy as np
    import trimesh

    height = float(z1) - float(z0)
    inset = height * tan(radians(taper))
    if inset >= _min_halfwidth(shape):
        raise ValueError(
            f"taper of {taper} deg closes the feature over a depth of "
            f"{height:g}; reduce the taper, the depth or both")
    top = _shape_outline(shape)
    bottom = _shape_outline(shape, inset)
    n = len(top)
    verts = np.vstack([
        np.column_stack([bottom, np.full(n, float(z0))]),
        np.column_stack([top, np.full(n, float(z1))]),
        [[0.0, 0.0, float(z1)], [0.0, 0.0, float(z0)]],
    ])
    top_centre, bottom_centre = 2 * n, 2 * n + 1
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [[i, j, n + j], [i, n + j, n + i],       # sidewall
                  [n + i, n + j, top_centre],             # top cap
                  [j, i, bottom_centre]]                  # floor
    # Wound counter-clockwise from outside already, as in solid._frustum, so
    # no normal repair (and no scipy dependency) is needed.
    mesh = trimesh.Trimesh(vertices=verts, faces=np.asarray(faces))
    mesh.apply_translation((*shape.center, 0.0))
    return mesh


def _shape_prism(shape, z0, z1, taper=0.0):
    """Create the exact trimesh prism used for both etch and fill.

    A non-zero ``taper`` gives sloped sidewalls instead: a truncated cone from
    a circle, a truncated elliptical cone from an ellipse and a truncated
    pyramid from a rectangle.
    """
    import trimesh

    height = float(z1) - float(z0)
    if height <= 0:
        raise ValueError("shape prism requires z1 greater than z0")
    if taper:
        return _tapered_prism(shape, z0, z1, taper)
    if isinstance(shape, Rectangle):
        mesh = trimesh.creation.box(extents=(*shape.size, height))
        rotation = shape.rotation
    elif isinstance(shape, Circle):
        mesh = trimesh.creation.cylinder(radius=shape.radius, height=height,
                                         sections=96)
        rotation = 0.0
    elif isinstance(shape, Ellipse):
        mesh = trimesh.creation.cylinder(radius=1.0, height=height,
                                         sections=96)
        mesh.apply_scale((shape.radii[0], shape.radii[1], 1.0))
        rotation = shape.rotation
    else:
        raise TypeError(f"unsupported process shape: {type(shape).__name__}")
    if rotation:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(
            radians(rotation), (0.0, 0.0, 1.0)))
    mesh.apply_translation((*shape.center, 0.5 * (z0 + z1)))
    return mesh


@dataclass(frozen=True)
class EtchFeature:
    """Stable handle describing a void produced by :meth:`Wafer.etch`.

    ``z0`` is the etch floor and ``z1`` the surface it was cut from.
    ``taper`` is the sidewall angle from vertical in degrees, zero for the
    straight-walled default.
    """

    shape: Shape
    z0: float
    z1: float
    name: str | None = None
    kind: str = "etch"
    taper: float = 0.0

    @property
    def top(self):
        return self.z1

    @property
    def anchor(self):
        """The rim center of the opening."""
        cx, cy = self.shape.center
        return (cx, cy, self.z1)

    def __getitem__(self, key):
        """Version 0.1 dictionary-style access; use the attributes instead."""
        warnings.warn(
            "EtchFeature[...] is deprecated; use .shape, .z0, .z1, .name or "
            "shape_bounds()", DeprecationWarning, stacklevel=2)
        x0, y0, x1, y1 = _shape_bounds(self.shape)
        values = {
            "x": x0, "y": y0, "dx": x1 - x0, "dy": y1 - y0,
            "z0": self.z0, "z1": self.z1, "shape": self.shape,
            "name": self.name,
        }
        return values[key]


@dataclass(frozen=True)
class FillFeature:
    """A solid deposited into an etched void by :meth:`Wafer.fill`."""

    opening: EtchFeature
    material: str
    overfill: float = 0.0
    name: str | None = None
    kind: str = "fill"
    holes: list = field(default_factory=list)   # vector-path bookkeeping

    @property
    def shape(self):
        return self.opening.shape

    @property
    def taper(self):
        """The plug inherits the sidewall angle of the void it fills."""
        return self.opening.taper

    @property
    def z0(self):
        return self.opening.z0

    @property
    def z1(self):
        return self.opening.z1 + self.overfill

    @property
    def top(self):
        return self.z1

    @property
    def anchor(self):
        cx, cy = self.shape.center
        return (cx, cy, self.z1)


@dataclass(frozen=True)
class RegionFeature:
    """A material-replacement region produced by :meth:`Wafer.implant`."""

    shape: Shape
    z0: float
    z1: float
    material: str
    name: str | None = None
    kind: str = "implant"

    @property
    def top(self):
        return self.z1

    @property
    def anchor(self):
        cx, cy = self.shape.center
        return (cx, cy, self.z1)


@dataclass(frozen=True)
class StackBreak:
    """An elided interval of a tall stack: nothing is drawn between ``z0``
    and ``z1`` (films, holes and fills crossing it are cut), and ``render``
    marks the block with a bracket such as "x100 ON pairs (85 not drawn)".

    ``span`` is the drawn z-extent of the whole repeated block (first layer
    bottom to last layer top) so the bracket can embrace it.
    """

    z0: float
    z1: float
    hidden: int
    total: int
    unit: str = "repeats"
    name: str | None = None
    span: tuple = (None, None)
    kind: str = "break"

    @property
    def top(self):
        return self.z1

    @property
    def anchor(self):
        return (0.0, 0.0, 0.5 * (self.z0 + self.z1))

    @property
    def caption(self):
        head = f"\u00d7{self.total} {self.unit}"
        if self.name:
            head = f"\u00d7{self.total} {self.name} {self.unit}"
        return f"{head}\n({self.hidden} not drawn)"


Feature = Union[Layer, EtchFeature, FillFeature, RegionFeature, StackBreak]


def shape_bounds(shape):
    """Axis-aligned ``(x0, y0, x1, y1)`` bounds of a process shape."""
    return _shape_bounds(shape)


# ---- lattices: centres for arrays of holes, pillars, pads -----------------

def square_lattice(x_range, y_range, pitch, *, margin=0.0):
    """Centres of a square array filling ``x_range`` x ``y_range``.

    Points are laid out with the given ``pitch`` and centred in the range;
    ``margin`` keeps that distance from the range edges. Returns a list of
    ``(x, y)`` tuples, row by row.
    """
    x0, x1 = float(x_range[0]) + margin, float(x_range[1]) - margin
    y0, y1 = float(y_range[0]) + margin, float(y_range[1]) - margin
    nx = max(1, int((x1 - x0) // pitch) + 1)
    ny = max(1, int((y1 - y0) // pitch) + 1)
    ox = x0 + 0.5 * ((x1 - x0) - (nx - 1) * pitch)
    oy = y0 + 0.5 * ((y1 - y0) - (ny - 1) * pitch)
    return [(ox + i * pitch, oy + j * pitch)
            for j in range(ny) for i in range(nx)]


def hex_lattice(x_range, y_range, pitch, *, margin=0.0, axis="x"):
    """Centres of a hexagonal (close-packed) array filling the range.

    Neighbouring points are ``pitch`` apart; successive rows are offset by
    half a pitch and spaced ``pitch * sqrt(3) / 2`` -- the memory-hole
    arrangement of 3D NAND, or any close-packed via/pillar field. ``axis``
    is the direction of the straight rows (``"x"`` or ``"y"``); ``margin``
    keeps that distance from the range edges. Returns ``(x, y)`` tuples.
    """
    if axis == "y":
        pts = hex_lattice(y_range, x_range, pitch, margin=margin, axis="x")
        return [(x, y) for y, x in pts]
    x0, x1 = float(x_range[0]) + margin, float(x_range[1]) - margin
    y0, y1 = float(y_range[0]) + margin, float(y_range[1]) - margin
    row_pitch = pitch * sqrt(3.0) / 2.0
    ny = max(1, int((y1 - y0) // row_pitch) + 1)
    oy = y0 + 0.5 * ((y1 - y0) - (ny - 1) * row_pitch)
    # one x origin for the whole lattice (centred, allowing for the half-pitch
    # stagger) so every neighbour distance is exactly the pitch
    nx = max(1, int(((x1 - x0) - 0.5 * pitch) // pitch) + 1)
    ox = x0 + 0.5 * ((x1 - x0) - (nx - 1) * pitch - 0.5 * pitch)
    out = []
    for j in range(ny):
        shift = 0.5 * pitch if j % 2 else 0.0
        out += [(ox + shift + i * pitch, oy + j * row_pitch)
                for i in range(nx)]
    return out


def _as_shape(value, what):
    if not isinstance(value, (Rectangle, Circle, Ellipse)):
        raise TypeError(f"{what} must be a Rectangle, Circle, or Ellipse")
    return value


def _rectilinear(shape):
    """True for an axis-aligned Rectangle: exact in the vector engine."""
    return isinstance(shape, Rectangle) and abs(shape.rotation) < 1e-12


def _solid_bounds(solid):
    """x/y bounds of a Layer or FillFeature."""
    if isinstance(solid, Layer):
        x0, y0, dx, dy = solid.extent
        return x0, y0, x0 + dx, y0 + dy
    return _shape_bounds(solid.shape)


def _solid_z(solid):
    return (solid.z0, solid.z1)


def _z_segments(z0, z1, holes, breaks=(), eps=1e-9):
    """Split ``[z0, z1]`` at every hole and break limit; yield
    ``(za, zb, holes_xy)`` with the x/y rectangles of the holes that span
    the whole segment. Segments inside a stack break are skipped."""
    cuts = {z0, z1}
    for hole in holes:
        cuts.update(z for z in hole[4:6] if z0 < z < z1)
    for brk in breaks:
        cuts.update(z for z in (brk.z0, brk.z1) if z0 < z < z1)
    zs = sorted(cuts)
    for za, zb in zip(zs, zs[1:]):
        mid = 0.5 * (za + zb)
        if any(b.z0 - eps <= mid <= b.z1 + eps for b in breaks):
            continue
        active = [h[:4] for h in holes
                  if h[4] <= za + eps and h[5] >= zb - eps]
        yield za, zb, active


def _solid_boxes(solid, origin_xy, size_xy, color, breaks=(), alpha=1.0):
    """Boxes for one layer/fill: whole slabs where no hole reaches, holed
    slabs elsewhere -- an exact vector picture of a rectilinear etch --
    with stack-break intervals left empty."""
    x0, y0 = origin_xy
    dx, dy = size_xy
    z0, z1 = _solid_z(solid)
    out = []
    for za, zb, holes in _z_segments(z0, z1, solid.holes, breaks):
        if holes:
            out += slab_with_holes((x0, y0, za), (dx, dy, zb - za), holes,
                                   color, alpha=alpha)
        else:
            out.append(Box((x0, y0, za), (dx, dy, zb - za), color,
                           alpha=alpha))
    return out


class Wafer:
    """An ordered process model: substrate, deposits, etches, fills, implants.

    Coordinate convention: process shapes (``Rectangle``, ``Circle``,
    ``Ellipse``) are **center-based**; the two lower-left-corner conveniences
    are ``add_pad(x, y, dx, dy)`` and ``drill(x, y, dx, dy)``, and
    ``Rectangle.from_corner`` converts between the two. Every verb returns a
    stable feature reference (:class:`Layer`, :class:`EtchFeature`,
    :class:`FillFeature`, :class:`RegionFeature`) and accepts ``name=`` so the
    feature can be labelled or found again with :meth:`find`.
    """

    def __init__(self, size=(10.0, 7.0), substrate="Si", thickness=1.5,
                 shape="rectangle", *, footprint=None, name="substrate",
                 notch=None, notch_angle=270.0, notch_depth=None,
                 flat_length=None):
        """Create a rectangular/square chip or circular full wafer.

        ``size`` is ``(x, y)`` for a rectangle and a scalar diameter for a
        circle or square; ``shape`` names the kind. Pass a ``Rectangle`` or
        ``Circle`` as ``footprint`` when a custom center is required (a
        shape object passed as ``shape`` is still accepted for 0.1 scripts).

        Circular wafers can carry an orientation feature: ``notch="V"`` (a
        90-degree V-notch) or ``notch="flat"`` (a major flat), at
        ``notch_angle`` degrees from +x towards +y (default 270: the -y
        edge, which faces the default solid camera). ``notch_depth``
        (default 3.5 % of the diameter -- exaggerated from the real
        ~0.35 % so it reads at figure scale) sets the V-notch depth;
        ``flat_length`` (default 32.5 % of the diameter, the 100 mm-wafer
        proportion) sets the flat's chord. The substrate and every film that
        inherits the wafer footprint (front and backside) are cut; local
        features and films with their own footprint are not.
        """
        # The arguments exactly as written, kept for to_dict()/to_json().
        given = {"size": size, "substrate": substrate, "thickness": thickness,
                 "shape": shape, "footprint": footprint, "name": name,
                 "notch": notch, "notch_angle": notch_angle,
                 "notch_depth": notch_depth, "flat_length": flat_length}
        if footprint is None and isinstance(shape, (Rectangle, Circle,
                                                    Ellipse)):
            footprint, shape = shape, None
        if footprint is not None:
            footprint = _as_shape(footprint, "footprint")
        else:
            if isinstance(size, (int, float)):
                sx = sy = float(size)
            else:
                sx, sy = _positive_pair(size, "size")
            kind = str(shape).lower()
            if kind in {"rectangle", "rect"}:
                footprint = Rectangle((sx / 2, sy / 2), (sx, sy))
            elif kind == "square":
                if abs(sx - sy) > 1e-12:
                    raise ValueError("a square wafer requires equal x/y size")
                footprint = Rectangle((sx / 2, sy / 2), (sx, sy))
            elif kind in {"circle", "circular", "cylinder"}:
                if abs(sx - sy) > 1e-12:
                    raise ValueError("a circular wafer requires one diameter")
                footprint = Circle((sx / 2, sy / 2), sx / 2)
            else:
                raise ValueError("shape must be rectangle, square, or circle")
        x0, y0, x1, y1 = _shape_bounds(footprint)
        self.sx, self.sy = x1 - x0, y1 - y0
        self.wafer_footprint = footprint
        self.notch = None
        if notch:
            if not isinstance(footprint, Circle):
                raise ValueError("a notch or flat needs a circular wafer")
            key = str(notch).lower()
            if key in {"v", "notch", "true"}:
                kind = "V"
            elif key == "flat":
                kind = "flat"
            else:
                raise ValueError("notch must be 'V' or 'flat'")
            d = footprint.diameter
            self.notch = {
                "kind": kind,
                "angle": float(notch_angle),
                "depth": float(notch_depth) if notch_depth is not None
                else 0.035 * d,
                "flat_length": float(flat_length) if flat_length is not None
                else 0.325 * d,
            }
        base = Layer(0.0, float(thickness), substrate,
                     (x0, y0, self.sx, self.sy), footprint, name=name,
                     kind="substrate")
        self.layers = [base]
        self.substrate = base
        self.substrate_top = float(thickness)
        self.top = float(thickness)
        self.bottom = 0.0
        self._etches = []
        self._fills = []
        self._regions = []
        self._breaks = []
        self._operations = [("layer", base)]
        # Replayable recipe: the constructor call, then one entry per verb.
        # The substrate is addressed as operation -1 by later references.
        if given["footprint"] is None and isinstance(given["shape"],
                                                     (Rectangle, Circle,
                                                      Ellipse)):
            given["footprint"], given["shape"] = given["shape"], None
        if given["footprint"] is not None:
            given.pop("size")
        _ctor_defaults = {"substrate": "Si", "thickness": 1.5,
                          "shape": "rectangle", "footprint": None,
                          "name": "substrate", "notch": None,
                          "notch_angle": 270.0, "notch_depth": None,
                          "flat_length": None, "size": (10.0, 7.0)}
        self._wafer_arguments = {
            key: value for key, value in given.items()
            if key not in _ctor_defaults or value != _ctor_defaults[key]}
        self._script = []
        self._produced = {id(base): {"op": -1}}
        self._recording_depth = 0

    # -- feature bookkeeping -------------------------------------------------

    @property
    def etches(self):
        return tuple(self._etches)

    @property
    def fills(self):
        return tuple(self._fills)

    @property
    def regions(self):
        return tuple(self._regions)

    @property
    def breaks(self):
        return tuple(self._breaks)

    @property
    def features(self):
        """Every feature reference, in process order (stripped layers are
        no longer listed)."""
        return tuple(feature for op, feature in self._operations
                     if op != "strip")

    def named(self):
        """``{name: feature}`` for every named feature (later wins)."""
        return {f.name: f for f in self.features if f.name}

    def find(self, name):
        """The feature called ``name`` (KeyError if there is none)."""
        try:
            return self.named()[name]
        except KeyError:
            raise KeyError(f"no feature named {name!r}; known: "
                           f"{sorted(self.named())}") from None

    def _record_layer(self, layer):
        self.layers.append(layer)
        self._operations.append(("layer", layer))
        return layer

    # -- deposition ----------------------------------------------------------

    @_records
    def add_layer(self, material, thickness, label=None, shape=None, *,
                  name=None):
        """Deposit a blanket film; by default it inherits the wafer footprint.

        ``name`` (or its older alias ``label``) is stored on the returned
        :class:`Layer` and used by ``render(labels=...)``.
        """
        thickness = float(thickness)
        if thickness <= 0:
            raise ValueError("film thickness must be positive")
        footprint = self.wafer_footprint if shape is None else \
            _as_shape(shape, "film shape")
        x0, y0, x1, y1 = _shape_bounds(footprint)
        layer = self._record_layer(Layer(
            self.top, thickness, material, (x0, y0, x1 - x0, y1 - y0),
            footprint, name=name or label))
        self.top += thickness
        return layer

    @_records
    def add_backside_layer(self, material, thickness, shape=None, *,
                           name=None):
        """Deposit a blanket film below the substrate without moving the top."""
        thickness = float(thickness)
        if thickness <= 0:
            raise ValueError("film thickness must be positive")
        footprint = self.wafer_footprint if shape is None else \
            _as_shape(shape, "film shape")
        x0, y0, x1, y1 = _shape_bounds(footprint)
        layer = self._record_layer(Layer(
            self.bottom - thickness, thickness, material,
            (x0, y0, x1 - x0, y1 - y0), footprint, name=name,
            kind="backside"))
        self.bottom -= thickness
        return layer

    @_records
    def add_break(self, gap, *, hidden, total, unit="repeats", name=None,
                  span=(None, None)):
        """Leave an empty ``gap`` at the current surface standing for
        ``hidden`` of ``total`` repeats that are not drawn.

        Films, holes and fills that cross the gap are cut there by both
        renderers, and ``render()`` marks the block with a bracket. Returns
        the :class:`StackBreak`.
        """
        gap = float(gap)
        if gap <= 0:
            raise ValueError("break gap must be positive")
        brk = StackBreak(self.top, self.top + gap, int(hidden), int(total),
                         unit, name, tuple(span))
        self._breaks.append(brk)
        self._operations.append(("break", brk))
        self.top += gap
        return brk

    @_records
    def add_multilayer(self, layers, repeats=1, *, name=None, show=None,
                       gap=None, unit="repeats"):
        """Deposit a repeating stack and return its :class:`Layer` list.

        ``layers = [(material, thickness), ...]`` is repeated ``repeats``
        times; ``w.add_multilayer([("SiO2", 0.32), ("Al", 0.55)],
        repeats=6)`` builds the DRAM laminate in one call. With ``name``,
        the layers are named ``"<name> 1"``, ``"<name> 2"``, ...

        Tall stacks can be elided: ``show=(bottom, top)`` deposits only the
        first ``bottom`` and last ``top`` repeats with an empty break of
        height ``gap`` between them (default: 1.5 repeat pitches); the
        break records how many repeats are hidden and ``render()`` labels
        the block, e.g. ``"x100 ON repeats (85 not drawn)"``. Layer names
        keep their true indices.
        """
        pitch = sum(float(t) for _, t in layers)
        out = []

        def deposit(repeat_indices):
            for r in repeat_indices:
                for i, (material, thickness) in enumerate(layers):
                    idx = r * len(layers) + i + 1
                    label = f"{name} {idx}" if name else None
                    out.append(self.add_layer(material, thickness, name=label))

        if show is None or repeats <= sum(show):
            deposit(range(repeats))
            return out
        bottom, top = (int(v) for v in show)
        if bottom < 0 or top < 0:
            raise ValueError("show=(bottom, top) needs non-negative counts")
        z_block0 = self.top
        deposit(range(bottom))
        z_break0 = self.top
        self.add_break(gap if gap is not None else 1.5 * pitch,
                       hidden=repeats - bottom - top, total=repeats,
                       unit=unit, name=name)
        deposit(range(repeats - top, repeats))
        brk = self._breaks[-1]
        # record the drawn block extent for the bracket
        self._breaks[-1] = StackBreak(brk.z0, brk.z1, brk.hidden, brk.total,
                                      brk.unit, brk.name,
                                      (z_block0, self.top))
        for k, (op, feature) in enumerate(self._operations):
            if feature is brk:
                self._operations[k] = ("break", self._breaks[-1])
        return out

    @_records
    def add_feature(self, material, shape, thickness, z0=None, *, name=None):
        """Add a localized patterned solid at ``z0`` or the current surface.

        Unlike blanket deposition this does not change the global process
        surface, which makes it suitable for pads, electrodes, and local
        capacitor stacks.
        """
        shape = _as_shape(shape, "feature shape")
        thickness = float(thickness)
        if thickness <= 0:
            raise ValueError("feature thickness must be positive")
        z0 = self.top if z0 is None else float(z0)
        x0, y0, x1, y1 = _shape_bounds(shape)
        return self._record_layer(Layer(
            z0, thickness, material, (x0, y0, x1 - x0, y1 - y0), shape,
            name=name, kind="feature"))

    @_records
    def add_pad(self, material, x, y, dx, dy, thickness, z0=None, *,
                name=None):
        """Add a rectangular patterned feature; ``x, y`` is the lower-left
        corner (see :meth:`Rectangle.from_corner` for the center form)."""
        footprint = Rectangle.from_corner(x, y, dx, dy)
        return self.add_feature(material, footprint, thickness, z0=z0,
                                name=name)

    @_records
    def implant(self, shape, material, *, depth=None, z0=None, z1=None,
                name=None):
        """Replace existing material inside a patterned 3D region.

        This is the DSL operation for implants, diffusion regions, and other
        composition changes that must not overlap the original solid. Specify
        either a depth measured from the current surface or explicit ``z0``
        and ``z1`` bounds.
        """
        shape = _as_shape(shape, "implant shape")
        if depth is not None:
            if z0 is not None or z1 is not None:
                raise ValueError("choose depth or explicit z0/z1 bounds")
            depth = float(depth)
            if depth <= 0:
                raise ValueError("implant depth must be positive")
            z1 = self.top
            z0 = z1 - depth
        elif z0 is None or z1 is None:
            raise ValueError("implant requires depth or both z0 and z1")
        z0, z1 = float(z0), float(z1)
        if z1 <= z0:
            raise ValueError("implant z1 must be greater than z0")
        region = RegionFeature(shape, z0, z1, material, name)
        self._regions.append(region)
        self._operations.append(("replace", region))
        return region

    @_records
    def etch(self, shape, *, depth=None, stop_on=None, through=False,
             surface_z=None, taper=0.0, name=None):
        """Boolean-etch ``shape`` from the current surface.

        Specify at most one stopping rule. With no rule, the etch stops on the
        substrate surface. ``through=True`` is the explicit way to cut to the
        bottom of the modeled stack. ``surface_z`` starts an etch from a local
        patterned feature instead of the blanket-film top.

        ``taper`` is the sidewall angle from vertical, in degrees. ``shape`` is
        then the opening at the surface and the floor is inset by
        ``depth * tan(taper)`` on every side, so a circle cuts a truncated
        cone, an ellipse a truncated elliptical cone and a rectangle a
        truncated pyramid. Negative values give a re-entrant profile. Any
        taper needs the solid backend, and :meth:`fill` reuses the same
        profile so a plug matches its void.
        """
        shape = _as_shape(shape, "etch shape")
        taper = float(taper)
        if abs(taper) >= 90.0:
            raise ValueError("taper must be a sidewall angle between -90 and "
                             "90 degrees from vertical")
        z_surface = self.top if surface_z is None else float(surface_z)
        rules = int(depth is not None) + int(stop_on is not None) + int(through)
        if rules > 1:
            raise ValueError("choose only one of depth, stop_on, or through")
        if depth is not None:
            depth = float(depth)
            if depth <= 0:
                raise ValueError("etch depth must be positive")
            z_stop = max(self.bottom, z_surface - depth)
        elif through:
            z_stop = self.bottom
        elif stop_on is None or stop_on == "substrate":
            z_stop = self.substrate_top
        elif isinstance(stop_on, str):
            z_stop = self.find(stop_on).top
        elif hasattr(stop_on, "top"):
            z_stop = float(stop_on.top)      # any feature reference
        else:
            raise ValueError("stop_on must be 'substrate', a feature name, "
                             "or a feature reference")
        if z_stop >= z_surface:
            raise ValueError("etch stop must be below the current surface")

        feature = EtchFeature(shape, z_stop, z_surface, name=name,
                              taper=taper)
        if taper:
            # Fail here rather than at render time, where the message would
            # be far from the call that caused it.
            _tapered_prism(shape, z_stop, z_surface, taper)
        self._etches.append(feature)
        self._operations.append(("etch", feature))

        # Vector-path bookkeeping: an axis-aligned rectangular etch is exact
        # in x/y, so record it as a hole with a z-extent on every solid that
        # exists now -- layers and earlier fills alike -- clipped to that
        # solid; boxes() splits each solid at the hole's z limits.
        if not taper and _rectilinear(shape):
            x0, y0, x1, y1 = _shape_bounds(shape)
            for solid in (*self.layers, *self._fills):
                sx0, sy0, sx1, sy1 = _solid_bounds(solid)
                sz0, sz1 = _solid_z(solid)
                if sz1 <= z_stop or sz0 >= z_surface:
                    continue
                hx0, hx1 = max(x0, sx0), min(x1, sx1)
                hy0, hy1 = max(y0, sy0), min(y1, sy1)
                if hx1 > hx0 and hy1 > hy0:
                    solid.holes.append((hx0, hy0, hx1 - hx0, hy1 - hy0,
                                        max(sz0, z_stop),
                                        min(sz1, z_surface)))
        return feature

    @_records
    def drill(self, x, y, dx, dy, depth=None, *, name=None):
        """Etch a rectangular hole down from the surface (full depth if
        depth is None). This is the version 0.1 lower-left-coordinate alias;
        new code should use :meth:`etch` with an explicit shape."""
        shape = Rectangle.from_corner(x, y, dx, dy)
        return self.etch(shape, depth=depth, through=depth is None, name=name)

    @_records
    def fill(self, hole, material, overfill=0.0, name=None):
        """Fill an etched void (damascene); overfill extends above the
        surface for contacts and pillars. ``hole`` is the
        :class:`EtchFeature` from :meth:`etch` or its name."""
        if isinstance(hole, str):
            hole = self.find(hole)
        if not isinstance(hole, EtchFeature):
            raise TypeError("fill requires the EtchFeature returned by etch()")
        overfill = float(overfill)
        if overfill < 0:
            raise ValueError("overfill cannot be negative")
        fill = FillFeature(hole, material, overfill, name)
        self._fills.append(fill)
        self._operations.append(("fill", fill))
        return fill

    @_records
    def strip(self, target):
        """Remove a deposited layer entirely (resist strip, sacrificial film).

        ``target`` is a :class:`Layer` or its name. The layer and whatever is
        left of it after etches disappear from every renderer; if it was the
        topmost blanket film the process surface drops back to its bottom.
        The removal is recorded as a ``("strip", layer)`` operation.
        """
        layer = self.find(target) if isinstance(target, str) else target
        if not isinstance(layer, Layer) or layer not in self.layers:
            raise ValueError("strip needs a Layer of this wafer (or its name)")
        self.layers.remove(layer)
        self._operations = [(op, f) for op, f in self._operations
                            if not (op == "layer" and f is layer)]
        self._operations.append(("strip", layer))
        if layer.kind == "layer" and abs(layer.z1 - self.top) < 1e-9:
            self.top = layer.z0
        return layer

    @_records
    def mesa(self, shape, *, depth=None, stop_on=None, name=None):
        """Etch the field around an axis-aligned rectangular mesa.

        The four non-overlapping field rectangles are ordinary DSL etches, so
        automatic renderer selection and Boolean semantics remain unchanged.
        """
        if not isinstance(self.wafer_footprint, Rectangle):
            raise ValueError("mesa currently requires a rectangular wafer")
        if not isinstance(shape, Rectangle) or abs(shape.rotation) >= 1e-12:
            raise ValueError("mesa currently requires an unrotated Rectangle")
        wx0, wy0, wx1, wy1 = _shape_bounds(self.wafer_footprint)
        mx0, my0, mx1, my1 = _shape_bounds(shape)
        if mx0 < wx0 or my0 < wy0 or mx1 > wx1 or my1 > wy1:
            raise ValueError("mesa must lie inside the wafer footprint")

        fields = [
            (wx0, wy0, mx0 - wx0, wy1 - wy0),
            (mx1, wy0, wx1 - mx1, wy1 - wy0),
            (mx0, wy0, mx1 - mx0, my0 - wy0),
            (mx0, my1, mx1 - mx0, wy1 - my1),
        ]
        handles = []
        for index, (x, y, dx, dy) in enumerate(fields):
            if dx <= 0 or dy <= 0:
                continue
            field = Rectangle((x + dx / 2, y + dy / 2), (dx, dy))
            handles.append(self.etch(
                field, depth=depth, stop_on=stop_on,
                name=f"{name or 'mesa'}-field-{index + 1}",
            ))
        return handles

    # -- serialization -------------------------------------------------------

    def to_dict(self):
        """The process recipe as a plain, JSON-ready dictionary.

        What is stored is the ordered list of DSL calls, not the derived
        geometry, so replaying the document rebuilds every layer, hole, fill
        and break. See :mod:`semi_structures.serialize` for the format.
        """
        from .serialize import wafer_to_dict

        return wafer_to_dict(self)

    def to_json(self, path=None, *, indent=2):
        """Serialize to a JSON string; with ``path``, also write it there."""
        from .serialize import wafer_to_json

        return wafer_to_json(self, path, indent=indent)

    @classmethod
    def from_dict(cls, data):
        """Rebuild a wafer from a :meth:`to_dict` document."""
        from .serialize import wafer_from_dict

        return wafer_from_dict(data, cls)

    @classmethod
    def from_json(cls, source):
        """Rebuild a wafer from a JSON string, a path, or an open file."""
        from .serialize import wafer_from_json

        return wafer_from_json(source, cls)

    @property
    def requires_solid(self):
        """Whether the model needs Boolean solids.

        Axis-aligned rectangular geometry -- footprints, etches (any depth),
        fills, mesas -- is exact in the vector engine, which splits every
        solid at the etch limits. Curved or rotated shapes, sloped sidewalls,
        non-rectangular wafers and material-replacement regions need the solid
        backend.
        """
        curved_layer = any(not _rectilinear(l.footprint) for l in self.layers)
        curved_etch = any(not _rectilinear(e.shape) for e in self._etches)
        tapered = any(e.taper for e in self._etches)
        return bool(self._regions or curved_layer or curved_etch or tapered)

    def select_backend(self, backend="auto"):
        """Return ``vector`` or ``solid`` using conservative dispatch."""
        if backend not in {"auto", "vector", "solid"}:
            raise ValueError("backend must be 'auto', 'vector', or 'solid'")
        selected = "solid" if backend == "auto" and self.requires_solid else backend
        if selected == "auto":
            selected = "vector"
        if selected == "vector" and self.requires_solid:
            raise ValueError(
                "vector backend cannot render curved/rotated geometry or "
                "implants; use backend='auto' or backend='solid'"
            )
        return selected

    def scene(self, backend="auto"):
        """Build a true solid scene when selected by automatic dispatch."""
        selected = self.select_backend(backend)
        if selected != "solid":
            raise ValueError("planar vector processes should be rendered with boxes()")
        try:
            from .solid import Scene
        except ImportError as exc:
            raise ImportError(
                "solid process geometry requires the optional dependencies; "
                "install semi-structures[solid]"
            ) from exc

        scene = Scene()
        active = []

        def intersects(mesh, tool):
            mesh_min, mesh_max = mesh.bounds
            tool_min, tool_max = tool.bounds
            return all(
                mesh_max[i] > tool_min[i] and tool_max[i] > mesh_min[i]
                for i in range(3)
            )

        def cut_active(tool):
            for handle in tuple(active):
                mesh = scene.parts[handle][0]
                if mesh is not None and not mesh.is_empty and intersects(mesh, tool):
                    scene.cut(handle, tool)

        wafer_layers = []                 # handles of footprint-inheriting films
        for operation, feature in self._operations:
            if operation == "layer":
                mesh = _shape_prism(feature.footprint, feature.z0,
                                    feature.z0 + feature.dz)
                handle = scene.add(mesh, feature.material)
                active.append(handle)
                if feature.footprint is self.wafer_footprint:
                    wafer_layers.append((handle, feature))
            elif operation == "etch":
                tool = _shape_prism(feature.shape, feature.z0, feature.z1,
                                    feature.taper)
                cut_active(tool)
            elif operation == "fill":
                opening = feature.opening
                if opening.taper and feature.overfill:
                    # The plug matches the sloped void, and the overfill sits
                    # on top of it as a straight cap of the opening size.
                    import trimesh

                    plug = _shape_prism(opening.shape, opening.z0, opening.z1,
                                        opening.taper)
                    cap = _shape_prism(opening.shape, opening.z1,
                                       opening.z1 + feature.overfill)
                    mesh = trimesh.boolean.union([plug, cap],
                                                 engine="manifold")
                else:
                    mesh = _shape_prism(opening.shape, opening.z0,
                                        opening.z1 + feature.overfill,
                                        opening.taper)
                active.append(scene.add(mesh, feature.material))
            elif operation == "replace":
                import trimesh

                tool = _shape_prism(feature.shape, feature.z0, feature.z1)
                replacements = []
                for handle in tuple(active):
                    mesh = scene.parts[handle][0]
                    if mesh is None or mesh.is_empty or not intersects(mesh, tool):
                        continue
                    overlap = trimesh.boolean.intersection(
                        [mesh, tool], engine="manifold")
                    if overlap is not None and not overlap.is_empty:
                        replacements.append(overlap)
                cut_active(tool)
                for mesh in replacements:
                    active.append(scene.add(mesh, feature.material))
        # wafer notch / flat: cut the substrate and every film that inherits
        # the wafer footprint (front and backside); nothing else
        if self.notch:
            for handle, feature in wafer_layers:
                if scene.parts[handle][0] is None:
                    continue
                scene.cut(handle, _notch_tool(self.wafer_footprint, self.notch,
                                              feature.z0 - 1e-6,
                                              feature.z1 + 1e-6))
        # stack breaks: remove the elided interval from everything drawn
        if self._breaks:
            import trimesh
            x0, y0, x1, y1 = _shape_bounds(self.wafer_footprint)
            pad = 0.1 * max(x1 - x0, y1 - y0) + 1.0
            for brk in self._breaks:
                tool = trimesh.creation.box(extents=(
                    x1 - x0 + 2 * pad, y1 - y0 + 2 * pad, brk.z1 - brk.z0))
                tool.apply_translation((0.5 * (x0 + x1), 0.5 * (y0 + y1),
                                        0.5 * (brk.z0 + brk.z1)))
                cut_active(tool)
        return scene

    def model(self, backend="auto"):
        """Return the representation selected by conservative dispatch.

        Rectilinear flows return vector boxes; curved/rotated geometry and
        implants return a Boolean-solid :class:`semi_structures.solid.Scene`.
        """
        selected = self.select_backend(backend)
        return self.scene("solid") if selected == "solid" else self.boxes()

    # -- one call from model to picture -------------------------------------

    def _label_features(self, labels):
        """Resolve ``labels`` to the features that get a callout."""
        if labels is False or labels is None:
            return []
        if labels is True or labels == "all":
            return [f for f in self.features
                    if f.name and not isinstance(f, StackBreak)]
        if isinstance(labels, str):
            return [self.find(labels)]
        return [self.find(n) if isinstance(n, str) else n for n in labels]

    def _label_columns(self, features):
        """Two-column callout layout: features whose anchor sits to the
        viewer's right of the wafer centre (screen u = x - y in the isometric
        convention) go in the right column, the rest in the left -- blanket
        films (u = 0) go right; each column is ordered top-down by anchor
        height. Returns ``[(feature, side, row_frac)]`` with ``row_frac`` in
        0 (top) .. 1 (bottom)."""
        wx, wy = self.wafer_footprint.center
        columns = {"left": [], "right": []}
        for f in features:
            x, y, _ = f.anchor
            u = (x - wx) - (y - wy)
            columns["right" if u >= -1e-9 else "left"].append(f)
        out = []
        for side, items in columns.items():
            items.sort(key=lambda f: -f.anchor[2])
            n = len(items)
            for i, f in enumerate(items):
                frac = 0.5 if n == 1 else 0.12 + 0.76 * i / (n - 1)
                out.append((f, side, frac))
        return out

    def render(self, ax=None, path=None, *, backend="auto", labels=False,
               label_size=None, print_width_in=None, dpi=300,
               origin=(0.0, 0.0), scale=1.0, extent=None, breaks=True,
               view="3d", y=None, zscale=1.0, label_marker=None,
               **solid_kwargs):
        """Draw the process model with whichever backend it needs.

        * vector (planar/rectilinear flows): boxes are drawn into ``ax`` with
          :func:`semi_structures.iso.draw_scene` at ``origin``/``scale``; with
          ``path`` and no ``ax`` a print-width figure is created and saved.
        * solid: a :class:`semi_structures.solid.Scene` is built and either
          rendered to ``path`` (PNG) or drawn into ``ax`` with ``imshow``
          (``extent`` optional). ``solid_kwargs`` (``zoom``, ``azimuth``,
          ``elevation``, ``edges``, ``aspect``, ``window``) go to the scene.

        ``labels`` is ``False``, ``"all"`` (every named feature), or an
        iterable of feature names/references; callouts anchor at each
        feature's ``anchor`` and are laid out automatically in two columns.
        ``label_size`` is points at print width; ``label_marker="dot"`` ends
        every leader in a filled dot at its anchor. With ``breaks=True`` every
        stack break is marked by a bracket embracing its block ("x100 ON
        repeats (85 not drawn)"). ``view="section"`` draws the 2D x-z
        cross-section at plane ``y`` instead (``zscale`` exaggerates
        thickness), via :mod:`semi_structures.section`. Returns the boxes
        list, the Scene, or the section pieces, so callers can add their
        own annotations afterwards.
        """
        if ax is None and path is None:
            raise ValueError("render needs an axes (ax=) or an output path")
        if view == "section":
            # 2D x-z cut at plane y (default: wafer centre): exact chords for
            # every shape, breaks with zigzag marks, callouts on the left
            import matplotlib.pyplot as plt
            from .section import draw_section
            from .style import PRINT_TEXTWIDTH_IN, PLOT_STYLE
            own = ax is None
            if own:
                plt.rcParams.update(PLOT_STYLE)
                width = float(print_width_in or PRINT_TEXTWIDTH_IN)
                fig, ax = plt.subplots(figsize=(width, 0.5 * width))
            pieces = draw_section(ax, self, y=y, zscale=zscale, labels=labels,
                                  label_size=label_size, breaks=breaks,
                                  marker=label_marker)
            if own:
                fig.savefig(path)
                plt.close(fig)
            return pieces
        if view != "3d":
            raise ValueError("view must be '3d' or 'section'")
        selected = self.select_backend(backend)
        callouts = self._label_columns(self._label_features(labels))
        pw = float(print_width_in) if print_width_in else None

        if selected == "solid":
            from .solid import LABEL_PT
            scene = self.scene("solid")
            size = label_size or LABEL_PT
            for f, side, frac in callouts:
                x_text = 0.97 if side == "right" else 0.03
                x_via = 0.78 if side == "right" else 0.22
                anchor = f.anchor_for("+y") if isinstance(f, Layer) \
                    else f.anchor
                scene.label(f.name, anchor=anchor, via=(x_via, frac),
                            position=(x_text, frac), size=size,
                            justify=side, marker=label_marker)
            if breaks:
                # candidates: the four vertical edges of the block; the
                # bracket is drawn beside whichever projects rightmost
                bx0, by0, bx1, by1 = _shape_bounds(self.wafer_footprint)
                corners = [(bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1)]
                for brk in self._breaks:
                    lo = brk.span[0] if brk.span[0] is not None else brk.z0
                    hi = brk.span[1] if brk.span[1] is not None else brk.z1
                    scene.bracket(brk.caption,
                                  [(cx, cy, lo) for cx, cy in corners],
                                  [(cx, cy, hi) for cx, cy in corners],
                                  size=size)
            if ax is None:
                scene.render(path, print_width_in=pw, dpi=dpi,
                             **solid_kwargs)
                return scene
            image = scene.render_array(print_width_in=pw, dpi=dpi,
                                       **solid_kwargs)
            if extent is None:
                ax.imshow(image)
            else:
                ax.imshow(image, extent=extent, aspect="auto")
            ax.set_axis_off()
            return scene

        # ---- vector ---------------------------------------------------------
        import matplotlib.pyplot as plt
        from .iso import LABEL_PT, draw_scene, iso
        from .style import C_GREY, C_SLATE, PRINT_TEXTWIDTH_IN, PLOT_STYLE

        boxes = self.boxes()
        ox, oy = origin

        def screen(p):
            u, v = iso(*p)
            return (ox + scale * u, oy + scale * v)

        pts = []
        for b in boxes:
            x0, y0, z0 = b.origin
            dx, dy, dz = b.size
            for cx in (x0, x0 + dx):
                for cy in (y0, y0 + dy):
                    for cz in (z0, z0 + dz):
                        pts.append(screen((cx, cy, cz)))
        us = [p[0] for p in pts]
        vs = [p[1] for p in pts]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)

        own_figure = ax is None
        if own_figure:
            plt.rcParams.update(PLOT_STYLE)
            width = pw or PRINT_TEXTWIDTH_IN
            span_u = (u1 - u0) * (1.6 if callouts else 1.1)
            height = width * (v1 - v0) * 1.15 / span_u
            fig, ax = plt.subplots(figsize=(width, height))
            pad_u, pad_v = 0.05 * (u1 - u0), 0.07 * (v1 - v0)
            side_room = 0.3 * (u1 - u0) if callouts else 0.0
            ax.set_xlim(u0 - pad_u - side_room, u1 + pad_u + side_room)
            ax.set_ylim(v0 - pad_v, v1 + pad_v)
            ax.set_aspect("equal")
            ax.set_axis_off()
        draw_scene(ax, boxes, origin=origin, scale=scale)

        size = label_size or LABEL_PT
        if breaks:
            # bracket beside the right-hand front corner (x1, y0) of the block
            bx0, by0, bx1, by1 = _shape_bounds(self.wafer_footprint)
            for brk in self._breaks:
                lo = brk.span[0] if brk.span[0] is not None else brk.z0
                hi = brk.span[1] if brk.span[1] is not None else brk.z1
                (ux, vlo), (_, vhi) = screen((bx1, by0, lo)), screen((bx1, by0, hi))
                xb = ux + 0.04 * (u1 - u0)
                tick = 0.015 * (u1 - u0)
                ax.plot([xb, xb + tick, xb + tick, xb], [vlo, vlo, vhi, vhi],
                        color=C_GREY, lw=0.7, solid_capstyle="round")
                ax.text(xb + 2.2 * tick, 0.5 * (vlo + vhi), brk.caption,
                        fontsize=size, color=C_SLATE, ha="left", va="center")
        for f, side, frac in callouts:
            xy = screen(f.anchor)
            x_text = u1 + 0.22 * (u1 - u0) if side == "right" \
                else u0 - 0.22 * (u1 - u0)
            y_text = v1 - frac * (v1 - v0)
            ax.annotate(f.name, xy=xy, xytext=(x_text, y_text),
                        fontsize=size, color=C_SLATE,
                        ha="left" if side == "right" else "right",
                        va="center",
                        arrowprops=dict(arrowstyle="-", color=C_GREY,
                                        lw=0.6, shrinkA=0, shrinkB=0))
            if label_marker == "dot":
                ax.plot(*xy, marker="o", ms=2.6, color=C_SLATE, zorder=6,
                        markeredgewidth=0)
        if own_figure:
            fig.savefig(path)
            plt.close(fig)
        return boxes

    def boxes(self):
        """Vector-isometric primitives for the planar/rectilinear model.

        Every box keeps the default draw layer (``k=0``) so the painter sort
        is purely geometric: lower z first, then far to near. A fill that
        starts at an etch floor therefore sorts among the cells of the layer
        it sits in, and anything deposited later (higher z) covers it -- a
        buried via or a buried pad no longer shows through the film above.
        """
        if self._regions:
            raise ValueError("material replacement requires scene()")
        out = []
        for layer in self.layers:
            if not _rectilinear(layer.footprint):
                raise ValueError("curved or rotated films require scene()")
            lx, ly, ldx, ldy = layer.extent
            out += _solid_boxes(layer, (lx, ly), (ldx, ldy),
                                _fill_color(layer.material), self._breaks,
                                alpha_for(layer.material))
        for fill in self._fills:
            if not _rectilinear(fill.shape):
                raise ValueError("curved or rotated fills require scene()")
            x0, y0, x1, y1 = _shape_bounds(fill.shape)
            out += _solid_boxes(fill, (x0, y0), (x1 - x0, y1 - y0),
                                _fill_color(fill.material), self._breaks,
                                alpha_for(fill.material))
        return out
