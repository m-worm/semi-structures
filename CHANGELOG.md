# Changelog

All notable changes to `semi-structures` are recorded here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-08-17

First public release. The package began as the figure toolkit for a
private X-ray monograph and was moved to its own repository, rewritten and
extended for release.

### Added

- **Tapered sidewalls in the process DSL.** `etch(shape, depth=...,
  taper=deg)` slopes the walls by a sidewall angle from vertical. The shape
  is the opening at the surface and the floor is inset by
  `depth * tan(taper)` on every side, so a circle cuts a truncated cone, an
  ellipse a truncated elliptical cone and a rectangle a truncated pyramid.
  Negative angles are re-entrant. `fill()` inherits the profile, and any
  `overfill` sits on top as a straight cap. A taper that would close the
  feature over its depth is refused at the `etch()` call, the angle is
  recorded in `EtchFeature.taper` and round-trips through JSON, and any
  taper selects the solid backend.
- **Materials.** One palette shared by every renderer: hue is the chemical
  family, lightness tracks electron density, alloys interpolate their
  endpoints, and doped variants keep the host hue (`style.MATERIAL`,
  `alloy_color()`, `doped()`, `validate_materials()`). Packaging materials
  (dark-gray laminate, PCB green, tin-gray solder) and transparent
  single-crystal substrates (`sapphire`, `SiC-wafer`) with a per-material
  drawing alpha (`MATERIAL_ALPHA`, `alpha_for()`) honored by all three
  renderers.
- **Typography law.** Every text size is points at print width, converted
  to pixels by the solid backend, and never below 7 pt.
- **Process DSL** (`semi_structures.process`). `Wafer` with blanket,
  repeated, backside and localized deposition, rectangle, circle and rotated
  ellipse etches with `depth`, `stop_on` and `through`, exact fills,
  implants and material replacement, `strip()`, mesas and `nm`/`um`/`mm`
  units. Feature references (`Layer`, `EtchFeature`, `FillFeature`,
  `RegionFeature`, `StackBreak`) are stable and carry names for
  `Wafer.find()`. Also square and hexagonal lattices, stack breaks that
  elide the middle of tall repeats and bracket the block, and circular
  wafers with an optional V-notch or major flat.
- **One-call rendering.** `Wafer.render()` drives either backend from the
  same model, with automatic feature callouts, optional stick-and-ball
  leaders and `view="section"` for a 2D cross-section.
- **JSON serialization** (`semi_structures.serialize`).
  `Wafer.to_dict()` / `to_json()` and `Wafer.from_dict()` / `from_json()`
  store the ordered DSL calls rather than the derived geometry, so a
  document is readable, editable and replays to the same model. Feature
  references are addressed by construction order and survive unnamed.
- **A command-line interface** (`semi-structures`). Query the palette,
  fetch built-in process patterns, and validate, inspect, render and export
  process documents. JSON in and out, `-` for standard input, exit status 1
  for an invalid document.
- **An MCP server** (`semi-structures-mcp`, `mcp` extra). The same
  operations as eight typed tools over stdio, for chatbots and coding
  agents. It executes no caller-supplied code, replays only an allowlist of
  DSL verbs, writes into one configured directory and bounds document size,
  repeat counts and image dimensions. Binds to MCP SDK 1.x or 2.x.
- **Three renderers.** Vector isometric (`iso`), 2D x-z section (`section`)
  and a true-solid Boolean backend (`solid`) built on trimesh/manifold3d
  and PyVista, with cutaways, shells, transparency, bowed slabs for
  film-stress figures, brackets, 3D-anchored routed labels and presentation
  overrides (`background=`, `edge_color=`).
- **Backend dispatch.** Rectilinear topology stays exact vector. Curved or
  rotated footprints, circular wafers, implants and sections go to the solid
  model, never silently losing an operation.
- **Examples and documentation.** 29 reproducible figure generators, a
  26-page LaTeX showcase, a prompt gallery, the guide (DSL, renderers and
  palette reference), the capability-status table and provenance for every
  supplied reference image.

### Known limitations

Conformal deposition, planarization, polygon footprints and a general
`Array` object, material-selective etching and a process-level `Style`
object are not implemented. See [`ROADMAP.md`](ROADMAP.md) for the full
status table.

[0.2.0]: https://github.com/m-worm/semi-structures/releases/tag/v0.2.0
