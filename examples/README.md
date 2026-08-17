# Examples

Install `semi-structures` from the project root before running these scripts.
Each generator writes its PDF and/or PNG output to `docs/figures`.

| Script | Backend | Demonstrates |
|---|---|---|
| `fig_hero_banner.py` | solid | The README banner: four structures across the package's range -- GAA nanosheets, a 3D NAND memory-hole array, a CoWoS-style package and a notched 300 mm wafer -- all on the solid backend at one camera |
| `fig_material_palette.py` | style | Material, alloy, field, and annotation colors |
| `fig_chart_style_guide.py` | style | Typography, line roles, figure sizes, and colormaps |
| `fig_dsl_feature_tour.py` | process + solid Boolean | Circular wafer with a V-notch, inherited films, rectangle, circle and rotated-ellipse etch/fill, and a 1D grating, as a six-step run sheet |
| `fig_rotated_ellipses.py` | process + solid / section | Elliptical etch + fill with the major axis at five angles; the same `Ellipse(rotation=)` drives the solid prisms and the section chords |
| `fig_wafer_notch.py` | process + solid | Bare 300 mm substrates, one with a V-notch and one with a major flat, cut through the substrate |
| `fig_serialization_roundtrip.py` | process + section | A damascene flow saved as a JSON document and rebuilt from it; the document is printed beside the two renderings, which are compared by SHA-256 |
| `fig_litho_flow.py` | process + section | Photolithography flow in six 2D cross-sections: deposition, resist, exposure (implant as material replacement, mask + light annotations), development, etch, `strip()` |
| `fig_litho_flow_3d.py` | process + solid | The same six litho states as solid 3D renders, with the mask and the exposure and etch beams as tapered `Scene.cone()` annotations |
| `fig_stack_gallery.py` | Matplotlib | Representative semiconductor layer stacks |
| `fig_film_stress_bow.py` | solid | Film stress bowing a wafer: flat reference, compressive (dome) and tensile (bowl) film, and the magnified bow of a multilayer, via `Scene.box(bow=)`; stick-and-ball callouts |
| `fig_transistor_evolution.py` | vector iso | Planar, FinFET, GAAFET, and CFET structures |
| `fig_transistor_solid.py` | solid + Matplotlib | Solid device views composed with vector cross-sections |
| `fig_memory_generations.py` | process + solid Boolean | Planar/trench DRAM, vertical 3D DRAM, and BiCS 3D NAND with exact etch/fill geometry |
| `fig_dram3d.py` | process + solid Boolean | Deposited laminate, Boolean comb/circular etches, exact fills, and patterned rails |
| `fig_nand3d.py` | process + solid Boolean | Hexagonal (close-packed) memory-hole array in two blocks with an oxide slit and nested concentric charge-trap fills, beside an equal-size quarter-section cutaway with a labelled x, y, z triad |
| `fig_nand_solid.py` | solid | Drilled word lines and a capped quarter-section cutaway |
| `fig_nand_stack_break.py` | process + vector / solid / section | 100-pair ON stack drawn as bottom 10 + top 5 with a stack break and "x100 (85 not drawn)" bracket; slit (vector), hexagonal holes (solid) and a 2D cross-section (section renderer), all cut at the break |
| `fig_optoelectronic_devices.py` | process + auto | Planar III-V/III-nitride stacks plus a Boolean-etched micro-LED mesa |
| `fig_sic_power_devices.py` | process + solid Boolean | SiC backside metal, replacement implants, nested trench fills, and non-overlapping fin gates |
| `fig_backside_power_delivery.py` | solid | Signal layers, transistors, buried rails, nTSVs, and backside power |
| `fig_backside_power_simple.py` | solid | The simplified backside-power block from a reference illustration: exploded Cu signal plates slotted around one W nTSV, transistor pads on thinned Si, a stepped Cu-in-SiO2 power block, Sn balls |
| `fig_hbm_labeled.py` | solid | HBM package (PCB substrate, neutral die gray) with 3D-anchored stick-and-ball callouts, every anchor on a face the camera can see |
| `fig_gpu_cowos_exploded.py` | solid + Matplotlib | Exploded CoWoS-style GPU package from two reference images: substrate with C4 field and capacitors, Si interposer with microbump fields, GPU die and six HBM towers; corner guide lines; assembled plan-view inset |
| `fig_gpu_cowos_assembled.py` | solid | The same GPU package assembled, with stick-and-ball callouts naming only the parts a camera can see once the bump fields are hidden |
| `fig_transistor_evolution_rolecolor.py` | solid + Matplotlib | The transistor line-up in the classic diagram's *role* colors (gate green, PMOS blue, NMOS red), true solids with opaque gates -- a presentation override, kept separate |
| `fig_dram3d_reference_colors.py` | solid | Horizontal-capacitor 3D DRAM in a vendor-style presentation scheme (dark background, role colors, light callouts) |
| `fig_dram3d_capacitor_schematics.py` | solid + Matplotlib | Vertical-capacitor array and staircase bit-line schematics in a red/green/white role scheme |

[`../docs/prompt-gallery.md`](../docs/prompt-gallery.md) gives, for each
script, the natural-language prompt that produces it.

The scripts are scientific schematics rather than fabrication drawings.
Their structural precedents and DOI links are collected in
[`REFERENCES.md`](REFERENCES.md). That file also traces the supplied HBM,
nTSV, simplified-backside-power, 3D X-DRAM, GPU-package,
transistor-evolution and capacitor-schematic reference images
to their sources. The generated
examples are independent redrawings rather than reproductions.

Six generators are the reference-image workflow in action: a multimodal
assistant used a supplied image for composition, viewpoint and callouts and
wrote a new package script. `fig_gpu_cowos_assembled.py`,
`fig_gpu_cowos_exploded.py` and `fig_backside_power_simple.py` keep the
package's material palette. The other three reproduce their reference's *role*
or presentation colors on request. Raw hex fills are allowed by both
renderers, but such overrides are deliberate exceptions to the palette law
and are kept as separate scripts so the material-colored figures remain the
defaults.

## Feature coverage

| API feature | Example coverage |
|---|---|
| Material lookup, alloys, and doped shades | material palette, stack gallery, optoelectronics, SiC power |
| `Box`, `Pillar`, painter ordering, and face projection | transistor evolution and backend/assembly examples |
| Rectangular/square/circular wafers and inherited film footprints | solid DSL tour |
| `Wafer`, `add_layer`, `add_multilayer`, and `add_backside_layer` | DSL tour, memory generations, optoelectronics, SiC power |
| Rectangle, circle, and rotated-ellipse Boolean etches | solid DSL tour, rotated ellipses |
| Wafer notch / flat (`Wafer(notch=...)`) | wafer notch, DSL tour |
| `hex_lattice` / `square_lattice` arrays | 3D NAND memory holes, stack-break example |
| Stack breaks (`add_multilayer(show=(b, t))`, `add_break`, `Scene.bracket`) | stack-break example |
| 2D cross-section renderer (`render(view="section")`) | stack-break example, panel (c); litho flow |
| `strip()` (resist / sacrificial-film removal) | litho flow |
| Exact-shape `fill` and `overfill` | solid DSL tour |
| Conservative vector/solid backend selection | solid DSL tour and API tests |
| Patterned `add_feature` / `add_pad` features | memory, optoelectronic, and SiC device galleries |
| Material-replacement `implant` | planar and trench SiC MOSFETs plus API volume tests |
| Rectangular `mesa` | micro-LED and API geometry tests |
| Solid boxes, cylinders, tubes, spheres, and arrays | solid transistor, solid NAND, backside power, HBM |
| Bowed slabs (`Scene.box(bow=)`, `multilayer(bow=)`) | film-stress bow |
| Stick-and-ball callouts (`marker="dot"`, `render(label_marker=)`) | film-stress bow |
| Boolean holes, rectangular cuts, and capped cutaways | solid DSL tour and solid NAND |
| Transparency and mixed raster/vector composition | solid transistor and backside power |
| 3D anchors, routed callouts, and fixed 2D text | backside power, labeled HBM, GPU package |
| Exploded views (empty world-space labels as 3D guide lines, `explode=` parameter) | GPU package |
| JSON serialization (`to_json` / `from_json`) | serialization round-trip |
| Solid backend across the whole range, one camera | hero banner |
| Transparent crystals (`sapphire`, `SiC-wafer`: per-material alpha in every renderer) | palette key; optoelectronic devices (e), (f) |
| Presentation overrides: raw hex role colors, dark `background=`, `edge_color=` | role-color transistors, reference-color 3D DRAM, capacitor schematics |
| Rotated trimesh primitives via `Scene.add()` (horizontal cylinders) | capacitor schematics |

Run one example:

```text
python examples/fig_nand3d.py
```

Run the complete gallery:

```text
python examples/run_all.py
```

The solid examples require the optional dependencies installed by
`python -m pip install -e ".[solid]"`.
