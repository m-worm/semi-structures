# Roadmap and status

What is implemented, what is not, and what happens next. This file replaces
the earlier `TODO.md`, `docs/dev/plan.md` and `docs/process-language.md`.

- [Release checklist](#release-checklist): the work before and around 0.2.0
- [Capability status](#capability-status): the audited implemented and
  planned table
- [Design targets](#design-targets): where the process language is heading

Items marked **(author)** need a human decision or an account action. The
rest are mechanical.

---

## Release checklist

### Blocking

- [ ] **(author) Confirm the five reference-image provenance rows.**
      `examples/REFERENCES.md` still says *"source to be confirmed by the
      author"* or *"source page to be added"* for the chiplet CPU package
      illustration, the simplified backside-power illustration, the H100
      package photograph and CoWoS graphic, the transistor-evolution diagram
      (Zhihu watermark, `@Tommy哥`), and the two-panel 3D DRAM capacitor
      schematic. The figures are independent redrawings and no image is
      redistributed, but each row should name its source or say plainly that
      the origin could not be established. This is the one item with real
      consequences for a public repository.

### First release

- [ ] **Watch the CI run.** The Linux jobs render through VTK/OSMesa via
      `pyvista/setup-headless-display-action`, which has never been exercised
      for this package, so the solid-backend tests and
      `examples/run_all.py` are the likeliest to need adjustment. Windows, the CLI entry points and the
      distribution build are verified locally.
- [ ] **(author) Repository settings:** description, topics (`semiconductor`,
      `visualization`, `matplotlib`, `pyvista`, `process-flow`, `materials`),
      and make it public so the CI badge resolves.
- [ ] **Tag and release `v0.2.0`** once CI is green.

### Documentation and metadata

- [x] ~~**(author) Add an author email to `pyproject.toml`.**~~ Done.
- [ ] **Swap README images to absolute URLs *only if* publishing to PyPI.**
      Relative paths are correct for GitHub. PyPI does not resolve them, so
      the hero and gallery would render broken on a project page.
- [x] ~~**Add `CITATION.cff`** so the package can be cited from a paper.~~
      Done: `CITATION.cff` carries the 0.2.0 metadata.
- [ ] **Check every DOI and external link in `examples/REFERENCES.md`
      resolves.** They were written from knowledge of the literature and have
      not been fetched.
- [x] ~~**Silence the VTK deprecation warning.**~~ Done: a narrow
      `filterwarnings` entry in `pyproject.toml` (matched by message *and*
      module, under pytest only) drops about a thousand third-party warnings
      per run to zero, while the package's own deprecations still surface.
- [x] ~~**Decide on Python 3.13.**~~ Supported: the classifier is present
      and CI tests 3.13 on Linux and Windows alongside 3.10 to 3.12.
- [x] ~~**Reconcile `requirements.txt` with `pyproject.toml`.**~~ Done:
      `requirements.txt` is now `-e .[all]`, so the versions are declared
      once, in `pyproject.toml`.

---

## Capability status

`Implemented` means public and exercised by a test or an example. `Partial`
means a narrower operation exists but the intended semantics or backend
coverage is incomplete. `Planned` means the behaviour is specified below but
not exposed.

| Capability | Status | Implementation or gap |
|---|---|---|
| Shared material palette | Implemented | Every renderer uses `style.MATERIAL`, including `package`, `PCB`, `Sn` and the translucent crystals `sapphire` / `SiC-wafer`, whose `MATERIAL_ALPHA` all three renderers apply. |
| Serializable process document | Implemented | `Wafer.to_dict()` / `to_json()` and `from_dict()` / `from_json()` store the ordered verb calls; references are addressed by construction order. A round-trip reproduces the model and its rendered pixels. |
| Command-line interface | Implemented | `semi-structures` validates, inspects, renders and exports documents, and prints the palette; JSON in and out, `-` for stdin. |
| MCP server | Implemented | `semi-structures-mcp` exposes eight typed tools over stdio (SDK 1.x or 2.x). No code execution, one writable directory, bounded documents and images. |
| Substrate construction | Implemented | Rectangular, square and circular wafers; circular ones take `notch="V"\|"flat"` with angle, depth and flat length, cut through the substrate and every inheriting film. |
| Footprint inheritance | Implemented | Blanket films inherit the wafer footprint; `add_layer(shape=...)` overrides it. |
| Blanket, repeated and backside deposition | Implemented | `add_layer()`, `add_multilayer()`, `add_backside_layer()`. |
| Conservative backend selection | Implemented | Rectilinear flows stay exact vector; curved or rotated shapes, tapered sidewalls, circular wafers and implants select the solid model. A forced vector request for geometry it cannot draw exactly raises. |
| Etching | Implemented | `etch(shape, depth=/stop_on=/through=)` for rectangle, circle and rotated ellipse, at any depth, plus `surface_z=` to start from a local feature. The vector engine splits solids at the etch limits, so partial etches are exact there too. |
| Tapered sidewalls | Implemented | `etch(..., taper=deg)` slopes the walls by a sidewall angle from vertical: a truncated cone from a circle, a truncated elliptical cone from an ellipse and a truncated pyramid from a rectangle. `fill()` inherits the profile. Selects the solid backend. `mesa()` stays straight-walled. |
| Fill and overfill | Implemented | `fill()` reuses the exact etch shape, including any taper, and accepts an overfill height that sits on top as a straight cap. |
| Local patterned features | Implemented | `add_feature()` (rectangle, circle, ellipse) and the rectangular `add_pad()`. |
| Material replacement / implant | Implemented | `implant()` intersects a 3D region with existing solids and conserves volume. |
| Mesa etch | Implemented | `mesa()` decomposes the field around an axis-aligned rectangle into four Boolean etches. |
| Strip | Implemented | `strip(layer_or_name)` removes a deposited layer everywhere and drops the process surface if it was the top film. |
| Stack breaks | Implemented | `add_multilayer(show=(bottom, top), gap=)` elides the middle of a tall repeat; every renderer cuts what crosses the gap and `render()` brackets the block. |
| Lattices | Implemented | `square_lattice()` and `hex_lattice()` return centre lists. |
| Units | Implemented | `nm`, `um`, `mm` multipliers; coordinates stay plain floats. |
| Feature references and history | Implemented | Every verb returns `Layer` / `EtchFeature` / `FillFeature` / `RegionFeature` with `name`, `kind`, `z0/z1/top`, `shape`, `anchor`; `name=` on every verb, `find()`, `features`. |
| Round primitives | Implemented | `cylinder()`, `tube()`, `sphere()` and `cone()`, the last a truncated cone taking a radius or a diameter at each end. |
| Coordinate axes | Implemented | `Scene.axes()` draws a labelled x, y, z triad that sizes and places itself from the model, or takes an explicit origin and length. |
| Labels | Implemented | `render(labels=False\|"all"\|[names])` with automatic two-column leaders in every backend; `Scene.label()` adds 3D anchors, elbows and stick-and-ball markers. |
| 2D cross-section renderer | Implemented | `render(view="section", y=)` cuts the model at a plane: films as bands, etches as gaps, fills and implants as inserts, exact chords for curved shapes, stack breaks with zigzag marks. |
| Typography law | Implemented | All sizes are points at print width; every backend refuses below `MIN_PRINT_PT`. |
| One-call rendering | Implemented | `Wafer.render(ax=None, path=None, ...)` dispatches, places the result and returns the boxes, `Scene` or section pieces. |
| Backend-neutral `Process` object | Partial | `Wafer` records ordered operations and emits either model, but there is no separate `Process` class. |
| Shapes | Partial | Rectangle, circle and rotated ellipse are implemented; polygons and a general `Array` shape are not. |
| Etch selectivity | Partial | `depth`, `stop_on` and `through` work; material selectivity does not. |
| Planarize | Planned | `strip()` exists; planarization does not. |
| Conformal deposition | Planned | No top/sidewall/cavity coating operation. |
| Oxidation and bonding | Planned | `implant()` covers material replacement; growth kinetics, oxidation and wafer bonding are future work. |
| Repeated process blocks | Partial | Repeated multilayers exist; arbitrary repeated operation blocks do not. |
| Process-level `Style` | Partial | The solid backend takes opacity, `background=` and `edge_color=`, and raw hex is a documented override, but material identity and presentation are not separated by an object. |

---

## Design targets

### Architecture

One ordered process language produces a backend-neutral feature model, which
any renderer draws. Process semantics are never reimplemented inside a
renderer.

```text
Process DSL -> operations and feature references
                    |-- vector-isometric renderer
                    |-- solid-Boolean renderer
                    `-- 2D cross-section renderer
```

### Proposed operations

Verbs beyond the current set, in the shape they should take. These do
not exist yet, so the block is not runnable code:

```text
p.planarize(stop_on=oxide)
p.deposit(material="Al2O3", thickness=8 * nm, mode="conformal")
p.pattern(feature, mask)
```

- `planarize(height=None, stop_on=None)`
- `deposit(..., mode="conformal")` coats every accessible exposed surface by
  the given normal thickness, with `step_coverage`, `coat_top`,
  `coat_sidewalls` and `coat_bottom` controls. Exact conformal geometry
  belongs to the solid backend. The vector renderer may offer a documented
  rectilinear approximation.
- `pattern(feature, mask)`, plus oxidation, bonding and repeated blocks.

Shapes should grow `Polygon(points)` and `Array(shape, count, pitch)`, shared
by deposition, etch, implant and annotation alike. An etch must keep exactly
one unambiguous stopping rule. Later controls can add sidewall angle, mask
bias, undercut and material selectivity.

### Materials and appearance

`material` keeps its scientific meaning and selects the palette, including a
default drawing alpha (`style.alpha_for`, where only the transparent
crystals are below 1). Presentation overrides belong in a separate `Style`,
for example `Style(opacity=0.4)`. Explicit colors must never silently
redefine a material.

### MCP, next steps

The stdio server is implemented. Remaining:

- an authenticated Streamable HTTP deployment with bounded rendering
  resources and artifact storage, for web-based clients,
- resources (not just tools) so a client can browse the palette and patterns
  without a tool call,
- `validate_process` returning structured diagnostics with operation indices
  rather than a single message.
