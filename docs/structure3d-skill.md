---
name: structure3d
description: Create 2D/3D semiconductor structure diagrams using the semi_structures iso, process and solid toolchain.
---

# Semiconductor structure figures

Working directory: the repository root (the folder holding `pyproject.toml`).
Scripts in `examples/` write their outputs into `docs/figures/`. Full manual:
`docs/guide.md`. Always view the rendered PNG and fix collisions before
delivering.

## Rules that always apply

1. Colors come from `semi_structures.style.MATERIAL` - never invent material colors.
   Available: Si, SiP (Si:P), SiC, SiGe, Ge, AlAs, InP, AlGaAs, InGaAsP,
   GaAs, InGaAs, InAs, AlN, AlGaN, GaN, InGaN, InN,
   SiO2, Si3N4, Al2O3, HfO2, TiN, TaN, Al, Sn, Cu, W, vacuum, substrate,
   package, PCB, resist and the translucent crystals sapphire (bulk Al2O3)
   and SiC-wafer (drawn at their `MATERIAL_ALPHA` by every renderer, while SiC
   itself is the opaque silicon-carbide device color, Al2O3 the thin-film
   dielectric). Alloys: `alloy_color("Si", "Ge", x)`. Doped layers:
   `doped("Si", 0.1..0.3)`. Color = material, never circuit role.
2. Author at print width (figsize width 6.3 in for \textwidth), fonts
   from `semi_structures.style.PLOT_STYLE`, nothing below 7 pt. Solid-
   backend text is also in points: `Scene.label(size=8.2)`,
   `text2d(size=10)` and `render(print_width_in=<printed width>)`. The
   backend refuses smaller sizes. Prefer `Wafer.render(ax=..., labels=...)`
   for one-call output with automatic callouts.
3. Reference images: use them for composition, viewpoint and callouts and
   write a new package script (record provenance in `examples/REFERENCES.md`,
   never redistribute the image). Keep the material palette unless the
   author explicitly asks for the reference's role or presentation colors,
   then use raw hex fills (and `render(background=..., edge_color=...)`)
   in a separate, clearly labelled script.
4. Saturated colors stay reserved for beams and fields. Annotation text is
   slate `C_SLATE`, leaders thin gray.
5. A model can be saved and reloaded: `w.to_json(path)` /
   `Wafer.from_json(path)` store the ordered verb calls, not the
   geometry. The same operations are on the command line
   (`semi-structures validate|inspect|render|export`) and over MCP,
   see `docs/interfaces.md`.

## Author through the DSL, then choose the renderer

- Semiconductor device structure -> **semi_structures.process** by default
  (`Wafer`: blanket/repeated/backside/local deposition, `etch(Rectangle |
  Circle | Ellipse, ...)`, exact `fill`, replacement `implant`, `mesa`, and
  `model(backend="auto")`). Automatic dispatch keeps safe rectilinear flows
  vector and sends topology changes or curved footprints to true solids.
- Flat abstract diagram or explicit vector-backend test -> **semi_structures.iso**
  (`Box`, `Pillar`, `slab_with_holes`, `draw_scene`, forcing draw order
  with `k=` when a part straddles others).
- Package assembly, backend regression test, spheres, arbitrary cuts, or
  ghosted explanatory parts ->
  **semi_structures.solid** (`Scene`: `box`, `cylinder`, `tube`, `sphere`,
  `multilayer`, `drill_hole(x, y, r, only=)`, `cut(handle, trimesh)`,
  `opacity=0.45` for ghosted gates, and `render(path, zoom, azimuth=-30,
  elevation=-16)` or `render_array(transparent=True)` to embed in a
  matplotlib canvas with `imshow(extent=...)`).
  Needs `pyvista trimesh manifold3d`. NEVER use PyVista's native
  boolean filter, because `Scene.cut` uses the manifold engine.
  Publication callouts use `Scene.label(text, anchor=(x,y,z),
  position=(screen_x,screen_y), via=...)`. Screen coordinates are normalized
  from the upper-left. Use `Scene.text2d()` for a fixed title.

## Template (semi_structures.solid)

```python
from semi_structures.solid import Scene
s = Scene()
s.box((0, 0, 0), (10, 7, 0.5), "Si")                 # substrate
plates = [s.box((0.2, 0.2, z), (10.2, 6.8, 1.0), "W")
          for z in (0.7, 2.5, 4.3)]
s.drill_hole(3.1, 4.9, 1.06, only=plates)            # real hole
s.tube((3.1, 4.9), 0.45, 1.0, 0.8, 5.5, "SiO2")      # shell
s.cylinder((3.1, 4.9), 0.45, 0.26, 6.0, "Si")        # core
s.render("docs/figures/out.png", zoom=1.2)
```

## Delivery checklist

- [ ] materials/labels honest (label "gate", let TiN gold say the rest)
- [ ] viewed the PNG, with no label collisions and a camera that shows the
      gaps and sidewalls
      (start azimuth −30, elevation −16)
- [ ] leaders added in a matplotlib wrapper when face labels crowd
      (target `origin + scale * iso(x, y, z)` for vector scenes, or use
      `Scene.label()` directly for solid scenes)
- [ ] caption states what each panel shows and "(Generated with <script>)"
