# semi-structures guide

How to create 2D/3D semiconductor structure diagrams in one consistent
publication style.
One device-authoring language, three renderers and one palette: every
material color comes from `semi_structures.style.MATERIAL`, so structure
figures obey the same laws as every other figure (hue = family, lightness =
electron density, saturation reserved for beams and fields).

A model can also be saved as a JSON process document and rebuilt from it, and
the same operations are available from the command line and over MCP. See
[`interfaces.md`](interfaces.md).

## Which interface to use

| Role | Module | Geometry | Look | Use when |
|---|---|---|---|---|
| Authoring | `semi_structures.process` | ordered fab operations and feature references | automatic | default for device structures and run sheets |
| Vector renderer | `semi_structures.iso` | axis-aligned boxes and vertical cylinders | flat isometric, vector PDF | safe rectilinear topology and abstract diagrams |
| Section renderer | `semi_structures.section` | x-z cut of the process model at a plane | 2D bands, vector PDF | side-on stacks, layer-order figures, tall stacks with breaks |
| Solid renderer | `semi_structures.solid` | true meshes and manifold3d booleans | PyVista parallel projection | etch/fill/implant, curved geometry, cutaways, assemblies |
| Serialization | `semi_structures.serialize` | the recipe, not the geometry | JSON | saving, diffing and exchanging a model |
| Shared operations | `semi_structures.mcp_tools` | validate, inspect, render, export | JSON in and out | behind the CLI and the MCP server |

The core installation provides process authoring, the vector renderer and
the section renderer. Add the solid renderer with `pip install -e ".[solid]"`
and the MCP server with `pip install -e ".[mcp]"`.

Device examples should use the process domain-specific language (DSL) and call `Wafer.render(...)` (one call
from model to picture, either backend) or `model(backend="auto")`. Direct
renderer primitives are intentional exceptions for backend regression tests,
package assemblies, annotations and abstract explanatory figures.

**Typography law (all renderers).** Every text size is *points at print
width*: author a figure at the width it will print (6.3 in for a full-width
figure) and nothing may go below `MIN_PRINT_PT` (7 pt). The vector engine
takes matplotlib points directly. The solid backend takes `size=` in points
and converts to pixels itself once you tell `render()` the printed width.
Both refuse sizes below the floor.

## `semi_structures.iso`: isometric renderer

World coordinates: x right-front, y left-front (depth), z up. The
projection shows the top, −y and −x faces. Faces are auto-shaded from
the material fill (top = fill, right −13 %, left −26 %).

```python
import matplotlib.pyplot as plt

from semi_structures.iso import Box, Pillar, slab_with_holes, draw_scene, iso
from semi_structures.style import MATERIAL

fig, ax = plt.subplots(figsize=(6.3, 3.5))
ax.set_aspect("equal")
ax.set_axis_off()

boxes = [
    Box((0, 0, 0), (10, 7, 1.5), MATERIAL["Si"][0], k=0,
        label=("right", "bulk Si")),          # face label, auto-rotated
    Pillar((5, 3, 1.5), radius=0.4, height=4, color=MATERIAL["Cu"][0]),
]
boxes += slab_with_holes((0, 0, 1.5), (10, 7, 0.8),
                         holes=[(4.5, 2.5, 1.0, 1.0)],   # x, y, dx, dy
                         color=MATERIAL["SiO2"][0])
draw_scene(ax, boxes, origin=(20, 30), scale=1.4)        # any mpl Axes
```

Key points:
- **Draw order**: automatic (bottom-up, then far-to-near). Use `k` to
  force layers when geometry alone is ambiguous (a gate straddling
  fins: fins `k=2`, gate `k=3`).
- **Labels**: `label=(face, text)` with face `top_x`, `top_y`, `right`,
  `left`. Text rotates with the face and flips to light text on dark
  fills. `label_size` defaults to 7.5 pt and may not go below 7 pt. For
  faces too small to carry that, use a matplotlib leader annotation
  targeting `origin + scale * iso(x, y, z)` (or `Wafer.render(labels=...)`).
- **Cutouts**: only axis-aligned rectangular holes, via
  `slab_with_holes` (decomposes into boxes, with no CSG).
- Limits: no spheres and no curved cuts, and occlusion is approximate for
  exotic interlocking, which is the solid backend's job.

## `semi_structures.process`: the process-flow DSL

Build structures the way a fab does. All verbs are LLM/engineer-readable:

```python
from semi_structures import Circle, Rectangle, Wafer, nm, um

w = Wafer(size=(2 * um, 1.3 * um), substrate="Si", thickness=180 * nm,
          name="Si")
w.add_multilayer([("SiO2", 64 * nm), ("Al", 110 * nm)], repeats=6,
                 name="plate")                     # laminate, "plate 1".."plate 12"
w.add_layer("SiO2", 64 * nm, name="cap")           # single blanket layer
slot = w.etch(Rectangle((360 * nm, 305 * nm), (720 * nm, 110 * nm)),
              stop_on="Si", name="slot")            # rectilinear: exact in vector
via = w.etch(Circle((930 * nm, 640 * nm), diameter=136 * nm),
             stop_on="Si", name="via")              # curved: needs solids
w.fill("via", "Cu", overfill=340 * nm, name="Cu via")   # by name or reference
w.add_pad("W", 740 * nm, 40 * nm, 110 * nm, 1.2 * um, 90 * nm, name="rail")
w.render(path="dram.png", labels=["cap", "Cu via", "rail"],
         print_width_in=6.3)                       # solid here (the circle)
```

- **Wafer notch / flat**: `Wafer(size=300*mm, shape="circle", notch="V"|"flat",
  notch_angle=270, notch_depth=..., flat_length=...)` cuts a 90-degree
  V-notch or a major flat from the substrate and every film that inherits
  the wafer footprint, front and backside. Local features and films with
  their own footprint are untouched. Defaults are exaggerated for figure
  scale (notch 3.5 % of the diameter, flat 32.5 %), and the angle runs from
  +x towards +y.
- **Rotated shapes**: `Rectangle(..., rotation=deg)` and
  `Ellipse(center, (a, b), rotation=deg)` etch, fill and section exactly
  with the axes at any in-plane angle.
- **Coordinates**: process shapes (`Rectangle`, `Circle`, `Ellipse`) are
  center-based. `add_pad(x, y, dx, dy)` and `drill(x, y, dx, dy)` are the
  two lower-left-corner conveniences, and `Rectangle.from_corner(...)`
  converts. `Circle` takes `radius=` or `diameter=`. `nm`, `um`, `mm` are
  plain multipliers (`nm = 1.0`), so scripts in arbitrary drawing units are
  unaffected.
- **Feature references**: every verb returns a stable object, one of `Layer`
  (films, backside films, local features), `EtchFeature`, `FillFeature` or
  `RegionFeature`, each with `name`, `kind`, `z0/z1/top`, `shape` and an
  `anchor` for callouts. Give any verb `name=` and get the feature back with
  `w.find(name)`. `w.features` lists them in process order, `etch(stop_on=)`
  and `fill()` accept a name or a reference, and `add_layer(label=)` is the
  old spelling of `name=` and is stored.
- `etch()` accepts rectangles, circles and rotated ellipses plus `depth`,
  `stop_on`, `through` and optional local `surface_z` semantics.
- **Tapered sidewalls**: `etch(shape, depth=..., taper=deg)` slopes the walls
  by `deg` from vertical. The shape is the opening at the surface and the
  floor is inset by `depth * tan(taper)` on every side, so a circle cuts a
  truncated cone, an ellipse a truncated elliptical cone and a rectangle a
  truncated pyramid. Positive is the ordinary profile (wider at the top),
  negative is re-entrant, and a taper that would close the feature over its
  depth is refused at the `etch()` call. Any taper selects the solid backend.
  `via = w.etch(Circle((5, 5), diameter=1.6), depth=1.0, taper=8)` followed by
  `w.fill(via, "W", overfill=0.2)` gives a sloped via with a matching plug.
- `fill()` reuses the exact opening shape, including its taper, and any
  `overfill` sits on top as a straight cap. `implant()` performs
  volume-conserving material replacement. `mesa()` etches the field around
  a rectangular active region and is straight-walled.
- `add_layer()`, `add_multilayer()`, `add_backside_layer()`, `add_feature()`
  and `add_pad()` cover blanket and localized deposition.
- `strip(layer_or_name)` removes a deposited layer everywhere (resist
  strip, sacrificial films), and the process surface drops if it was the
  top blanket film. See `fig_litho_flow.py` for the six-step litho sequence.
- **Arrays**: `square_lattice(x_range, y_range, pitch, margin=)` and
  `hex_lattice(..., axis="x"|"y")` return center lists. Loop over them
  with `etch(Circle(c, r))`/`fill`, `add_feature` or `Scene.cylinder`.
  The hexagonal (close-packed) lattice is the memory-hole arrangement of
  3D NAND (`fig_nand3d.py`: two blocks of staggered holes and a slit).
- **Cross-sections**: `w.render(ax, view="section", y=..., zscale=...)`
  (or `semi_structures.section.draw_section`) draws the x-z cut at plane
  `y` (default the wafer center): films as bands, etches as gaps, fills and
  implants as inserts, all exact at the plane (chords of rectangles,
  circles and rotated ellipses), stack breaks with zigzag marks and the
  bracket, callouts on the left. Pure vector, the stack-gallery idiom
  generated from the model.
- **Stack breaks**: `add_multilayer(pair, repeats=100, show=(10, 5),
  gap=..., unit="pairs")` deposits only the first 10 and last 5 repeats
  with an empty break between them (`add_break()` does the same by hand).
  Films, holes and fills crossing the break are cut there by both
  renderers, layer names keep their true indices, and `render()` marks
  the block with a bracket, "x100 ON pairs (85 not drawn)"
  (`Scene.bracket()` is the underlying primitive, and `breaks=False` hides
  it). See `fig_nand_stack_break.py`.
- **Dispatch**: `w.model()`/`w.render()` use the vector engine for every
  rectilinear flow (axis-aligned films, etches of *any* depth, fills and
  mesas) and draw it exactly by splitting each solid at the etch limits (an
  etch into an earlier fill cuts that fill too). Curved or rotated shapes,
  tapered sidewalls, circular wafers and implants select the Boolean solid
  model. Pass `backend="solid"` to force a shaded render of a rectilinear
  flow.
- **`w.render(ax=None, path=None, *, backend, labels, label_size,
  label_marker, print_width_in, dpi, origin, scale, extent, **camera)`** draws into a
  matplotlib axes (vector at `origin`/`scale`, or a solid `imshow` at
  `extent`) or straight to a file. `labels` is `False`, `"all"` or a list
  of names and references. Callouts anchor at each feature's visible face
  and are laid out automatically in two columns, and `label_marker="dot"`
  gives stick-and-ball leaders in every backend. It returns the boxes or the
  `Scene` for further annotation.
- Worked examples: `fig_dram3d.py`, `fig_nand3d.py`,
  `fig_memory_generations.py`, `fig_sic_power_devices.py` and
  `fig_optoelectronic_devices.py` (mixed vector/solid panels through one
  `render()` call).

## `semi_structures.solid`: true solid modeling

Geometry and CSG by trimesh with the manifold3d engine. Do not use VTK's
native booleans, which fail on exactly these shapes. Rendering is by
PyVista with the package's diagram style: white background, parallel
isometric camera, flat colors, slate feature edges.

```python
from semi_structures.solid import Scene

import trimesh

s = Scene()
plate = s.box((0, 0, 0), (10, 7, 1.0), "W")        # keep the handle
s.drill_hole(x=3.1, y=4.9, r=1.06)                 # real circular hole
s.tube((3.1, 4.9), z0=0, r_out=1.0, r_in=0.8,      # annular shell
       h=5.5, material="SiO2")
s.cylinder((3.1, 4.9), z0=0, r=0.26, h=6.0, material="Si")
s.sphere((7, 2, 3), r=0.8, material="Cu")
s.multilayer((0, 0, 1.0), (10, 7),                  # repeating stack
             [("W", 0.2), ("Si", 0.3)], repeats=6)
s.box((2, 1, 1), (3, 4, 4), "TiN", opacity=0.45)   # ghosted part
s.cut(plate, trimesh.creation.box(extents=(2, 2, 8)))   # any boolean
s.render("out.png", print_width_in=6.3, zoom=1.2,   # 300 dpi at 6.3 in
         azimuth=-30, elevation=-16)
img = s.render_array(print_width_in=3.0)             # RGBA for imshow
```

### Solid-backend labels

`Scene.label()` attaches a publication callout to a 3D feature. The anchor is
always a world-space point. Give the label position as normalized screen
coordinates for stable page layout, where `(0, 0)` is the upper-left corner.
Optional `via` points route elbowed leaders around the structure.

```python
s.label("GPU die", anchor=(14.0, 2.3, 3.42),
        via=(0.76, 0.47), position=(0.95, 0.47),
        justify="right", size=8.2)              # points at print width
s.text2d("High-bandwidth memory", position="upper_left", size=10.0)
```

`size` and `line_width` are points at the print width you declare in
`render()`/`render_array()` (`print_width_in`, default 6.3 in). The backend
converts to pixels for whatever window it renders and refuses sizes below
7 pt. All screen text, meaning callouts, titles and the text of world-mode
labels, is drawn through one PIL path with a portable Arial / DejaVu Sans
stack. Pass `Scene(font="MyFont.ttf", font_bold=...)` to choose another
face.
A three-element label position remains available for a world-space label,
whose leader is a 3D line that geometry can occlude. Screen-space labels
are preferable for finished figures because their text stays horizontal and
their placement is independent of camera projection.

API summary:

| Call | Notes |
|---|---|
| `box(origin, size, material, opacity=None, bow=None)` | origin = min corner; `opacity=None` takes the material's default alpha (`style.alpha_for`: 1.0 except the transparent crystals `sapphire`, `SiC-wafer`); `bow=(sx, sy)` bends the slab (edge-to-centre sagitta, + dome / − bowl), films drawn with the same `bow` stay conformal |
| `cylinder(center_xy, z0, r, h, material, opacity=None, diameter=None)` | vertical; give `r` or `diameter` |
| `cone(center_xy, z0, h, material, r_bottom=, r_top=, d_bottom=, d_top=, opacity=None)` | vertical truncated cone; each end takes a radius or a diameter, and a top radius of zero gives a true cone |
| `tube(center_xy, z0, r_out, r_in, h, material, opacity=None)` | annulus, no boolean needed |
| `sphere(center, r, material, opacity=None)` | |
| `multilayer(origin, xy_size, layers, repeats, bow=None)` | `[(material, t), ...]`; `bow` bends every layer |
| `drill_hole(x, y, r, z0, z1, only=[handles])` | drills every part whose footprint contains the hole unless `only` is given |
| `cut(handle, tool)` | subtract any trimesh from one part |
| `cutaway(x, y, z, only=)` | quarter/half-section: removes the camera-facing region (X > x and Y > y and Z > z; give any subset — one plane = half-section, two = quarter). Cut faces are capped, so the interior shows in material colors |
| `label(text, anchor, position, via=, size=8.2, marker=None, ...)` | screen-facing callout tied to a 3D feature; 2D positions are normalized screen coordinates, 3D positions are world coordinates; `size` in points at print width; `marker="dot"` ends the leader in a filled dot at the anchor (stick and ball, `marker_size` pt) |
| `axes(origin=None, length=None, labels=("x", "y", "z"), ...)` | labelled x, y, z triad; with no arguments it sizes itself from the model and sits just outside the minimum corner. The arms are 3D lines, so geometry occludes them, and the labels carry a white outline so they stay readable over a structure |
| `text2d(text, position=, size=10, bold=)` | fixed screen-space title or note; `position` is a corner name or normalized `(x, y)` |
| `bracket(text, lo, hi, dx=, tick=, size=)` | screen bracket embracing the span between two 3D points (or the rightmost of several candidate edges), text beside it; flips to the left silhouette when the right has no room |
| `bounds()` | `(min, max)` corners over live parts |
| `add(mesh, material, opacity=None)` | bring your own trimesh; `None` = the material's default alpha |
| `render(path, *, print_width_in=6.3, dpi=300, window=None, aspect=0.78, zoom, azimuth, elevation, edges, background="white", edge_color=slate)` | PNG file; the window is `print_width_in × dpi` wide unless given; `background`/`edge_color` allow presentation-style renders (dark background, light edges and label colors) |
| `render_array(*, print_width_in, dpi, ...)` | RGBA array, transparent background — embed in a matplotlib figure with `ax.imshow(img, extent=...)`; pass the printed panel width so text lands at its point size (see `examples/fig_transistor_solid.py`) |

Camera guide: the projection is always parallel. Start from
`azimuth=-30, elevation=-16`, a three-quarter view showing gaps and
sidewalls. More negative elevation gives a lower camera, and `zoom` frames
the result. The default camera looks from +x, +y. `azimuth=-120` looks from
+x, -y with low-y features front-left, and `azimuth=150` from -x, -y.
Render a small contact sheet of candidate azimuths when matching a
reference view. Non-vertical primitives (e.g. horizontal cylinders) are
rotated trimesh meshes passed to `Scene.add()`, as in
`fig_dram3d_capacitor_schematics.py`.
Opacity: `opacity<1` enables depth peeling automatically, and 0.4 to 0.5
reads well for ghosted gates over channels. The transparent crystals
(`sapphire`, `SiC-wafer`) are translucent by default in every backend
(`style.MATERIAL_ALPHA`, and the vector and section renderers use the same
alpha), so a GaN-on-sapphire LED shows its clear substrate without any
per-part `opacity=`. Pass `opacity=1.0` to force an opaque wafer.

Exploded views: open a gap between levels (an `explode=` parameter in
the build function) and tie levels together with empty world-space
labels, `s.label("", anchor=p_top, position=p_bottom, line_width=0.5)`,
which draw as thin 3D guide lines that geometry occludes, as in
`fig_gpu_cowos_exploded.py`.

Performance: `_SECTIONS = 96` sets cylinder smoothness and booleans are
fast under manifold. Renders are raster, so declare the printed width, let
`dpi=300` size the window and embed at that width. Parts that a Boolean
cuts away entirely become `None` and are skipped by later operations.

## Composing multi-panel figures

Panels that mix 3D renders with 2D content (cross-sections, plots)
follow `examples/fig_transistor_solid.py`: one matplotlib canvas at print width,
`render_array()` panels placed with `imshow(extent=...)`, typography and
leaders from the normal figure rules. Vector output survives: the PDF
embeds the raster panels at 300+ dpi.

## Worked examples

| Script | Shows |
|---|---|
| `examples/fig_transistor_evolution.py` | vector: 4-device line-up, face labels, leaders |
| `examples/fig_dram3d.py` | DSL: laminate + Boolean comb/via etch + fill + pads |
| `examples/fig_nand3d.py` | DSL: circular memory holes + nested charge-trap fills |
| `examples/fig_nand_solid.py` | solid: drilled plates, ring cross-sections, and a `cutaway()` quarter-section exposing the shell stack (`nand3d_cutaway.png`) |
| `examples/fig_transistor_solid.py` | solid + composition + ghosted gates |
| `examples/fig_hbm_labeled.py` | solid: HBM package, sphere arrays, and backend-native callout labels |
| `examples/fig_transistor_evolution_rolecolor.py` | solid: role-colored line-up (raw hex fills), opaque gates, per-panel `print_width_in` callouts |
| `examples/fig_backside_power_simple.py` | solid: simplified backside-power block, `drill_rect` step and plate slots, one W nTSV, Sn balls |
| `examples/fig_gpu_cowos_exploded.py` | solid: exploded CoWoS-style GPU package (`explode=` gap between levels, empty world-space labels as corner guide lines), sphere-array bump fields, six HBM towers, plan-view inset from a second camera |
| `examples/fig_dram3d_reference_colors.py` | solid: presentation-style render (`background=`, `edge_color=`, light callouts) |
| `examples/fig_dram3d_capacitor_schematics.py` | solid: two role-colored panels, rotated trimesh cylinders via `Scene.add()` |

## Palette reference

The source of truth is `src/semi_structures/style.py`. The values below
are its output. Alloys are computed by `mix()` / `alloy_color()` at
x = 0.5 unless noted.

### Material fills (pale, with lightness tracking electron density)

| Material | Hex | rho_e (e/A^3) | Family |
|---|---|---|---|
| vacuum / air | `#FFFFFF` | 0 | neutral (outlined chip) |
| SiO2 | `#F2EAD8` | 0.66 | dielectric sands |
| Si | `#ADD8E6` | 0.70 | group-IV blues |
| Si:P (doped Si) | `#A0C8D6` | 0.71 | group-IV blues (doped shade) |
| Al | `#DADDE0` | 0.78 | metal greys |
| Si3N4 | `#E5CFA3` | 0.95 | dielectric sands |
| SiC (silicon carbide, all polytypes; opaque device color) | `#92C3CB` | 0.96 | group-IV blues (cyan lean) |
| SiC wafer (`SiC-wafer`, bulk crystal) | `#ECEDD8`, alpha 0.45 | 0.96 | transparent crystals (near-clear, drawn translucent) |
| AlN | `#C2E4DE` | 0.96 | III-nitride teals |
| Si0.7Ge0.3 | `#91BDD2` | 0.91 | group-IV blues (common 30% Ge alloy) |
| Si0.5Ge0.5 | `#7EACC6` | 1.06 | group-IV blues (Vegard mix) |
| AlAs | `#C4DFC5` | 1.11 | III-V greens |
| Al2O3 (thin-film dielectric) | `#DEC6A6` | 1.18 | dielectric sands |
| sapphire (`sapphire`, bulk Al2O3) | `#DDE5F2`, alpha 0.35 | 1.18 | transparent crystals (near-clear, drawn translucent) |
| InP | `#AFD5B9` | 1.27 | III-V greens |
| AlGaAs | `#A4CFAE` | 1.31 | III-V greens (alloy) |
| Al0.5Ga0.5N | `#A2D2CB` | 1.32 | III-nitride teals (Vegard mix) |
| InGaAsP | `#9DCAAA` | 1.36 | III-V greens (quaternary alloy) |
| Ge | `#4F7FA5` | 1.41 | group-IV blues (dark endpoint) |
| GaAs | `#93C6A1` | 1.42 | III-V greens |
| InGaAs | `#8DC09C` | 1.45 | III-V greens (alloy) |
| TiN | `#E5C766` | 1.47 | barrier gold-olive |
| InAs | `#78AD8C` | 1.56 | III-V greens |
| GaN | `#82BFB7` | 1.68 | III-nitride teals |
| InGaN | `#7EBCB4` | 1.71 | III-nitride teals (alloy) |
| Sn | `#B7BBC0` | 1.85 | metal grey; default solder balls |
| InN | `#65A9A2` | 1.90 | III-nitride teals |
| Cu | `#D5A292` | 2.46 | metal (native salmon) |
| HfO2 | `#C6A886` | 2.88 | dielectric sands |
| TaN | `#9C8F62` | 3.39 | barrier gold-olive |
| W | `#8A929C` | 4.67 | metal greys |
| generic substrate | `#DCE0E4` | - | neutral |
| package | `#50565D` | - | dark grey package laminate / mould compound (semantic; darker than W, never black) |
| PCB | `#2F7D4F` | - | printed-circuit-board solder-mask green (semantic; packaging figures) |
| photoresist | `#EBD3E0` | 0.40 | neutral |

Transparent crystals: `style.MATERIAL_ALPHA` holds the drawing alpha (`alpha_for(name)`, 1.0 for every other material and for raw hex). The vector, section and solid renderers all apply it, so a `Wafer(substrate="sapphire")` or `Scene.box(..., "SiC-wafer")` is see-through unless an explicit `opacity=` overrides it. They are separate entries from the opaque device color `SiC` and the dielectric `Al2O3`.

### Chart lines, in order

| # | Name | Hex | Role |
|---|---|---|---|
| 1 | blue | `#255C99` | the result the panel is about |
| 2 | red | `#B33A3A` | the contrasting case |
| 3 | green | `#3F7D5B` | 3rd series |
| 4 | amber | `#C98A2D` | 4th series |
| 5 | purple | `#7B5EA7` | 5th series (rare) |
| - | grey | `#8A949C` | context / reference |
| - | black | `#000000` | analytic ground truth only |

### Reserved (beams, wavefields and annotation, never fills)

| Use | Hex |
|---|---|
| incident beam (crimson) | `#B0304A` |
| specular / reflected R_s | `#255C99` |
| Bragg-diffracted R_h | `#3F7D5B` |
| evanescent / absorbed | `#C98A2D` |
| annotation slate | `#3D4852` |
| structural grey (plates, edges) | `#687078` |
| light edge on fills | `#AAB1B7` |

Heatmaps: viridis (fields) / inferno (log counts) / RdBu_r (signed,
symmetric limits) / twilight (phase) / gray (radiographs),
https://matplotlib.org/stable/users/explain/colors/colormaps.html

## Troubleshooting

- Boolean returns empty or strange geometry: make sure the tool overlaps
  the target. Meshes from `trimesh.creation` are watertight, so keep them
  that way.
- VTK warnings about orientation: you are on the old VTK boolean path, so
  use `Scene.cut` (manifold), never `pyvista.boolean_difference`.
- Off-screen render fails: PyVista needs OpenGL, so on a headless machine
  set `pv.start_xvfb()` (Linux) or render on a desktop session.
- Vector occlusion looks wrong: the painter sort is lower-z first, then
  far-to-near. Give the offending parts explicit `k` layers only as an
  override, and if it needs more than two `k` values, move to the solid
  backend.
- A label raises `ValueError ... print floor`: the size is below 7 pt at
  print width, so enlarge it or use a leader for a face that is too small.
