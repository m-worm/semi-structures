# Prompt gallery

What you can ask a coding assistant for, and the figure the package makes of
it. Every entry below is realised by a script in `examples/` (its output is in
`docs/figures/`), so the prompt, the code and the picture can be compared.
The prompts are written the way an author would type them. The assistant is
expected to answer with an editable script, not a pixel image.

Conventions the assistant should keep without being told: material colors
from the palette (color = material, never circuit role), text in points at
print width and never below 7 pt, the process DSL for device semantics,
provenance for any reference image, and a caption ending "Generated with
`examples/<script>.py`". Role or presentation colors are only used when the
prompt asks for them, in a separate script.

## Palette and style

| Prompt | Figure | Script |
|---|---|---|
| "Make a banner showing the package's range: a gate-all-around device, a 3D NAND memory-hole array, a package on a substrate, and a patterned 300 mm wafer, all on the solid backend at one camera." | `hero_banner` | `fig_hero_banner.py` |
| "Draw the material palette key: every material as a chip with its hex code and electron density, families grouped, alloy ramps for SiGe, AlGaN, InGaAs, InGaN. Two equal panels." | `material_palette` | `fig_material_palette.py` |
| "Make a one-page chart style guide: the line palette in order, the aspect-ratio menu, the heatmap colormap rules and the typography ladder." | `chart_style_guide` | `fig_chart_style_guide.py` |
| "Add SiC and Al2O3 (sapphire) as almost-transparent substrate materials, distinct from the doped-Si blues, and put them in the color table." | `material_palette` (transparent-crystals row), `optoelectronic_devices` (e), (f) | `fig_material_palette.py`, `fig_optoelectronic_devices.py` |
| "Show how film stress bows a wafer: a flat wafer with one film for reference, then compressive (dome) and tensile (bowl), single film and a multilayer stack, with dot-ended leaders for 'film' and 'wafer'." | `film_stress_bow` | `fig_film_stress_bow.py` |
| "Six representative layer stacks side by side -- high-k metal gate, Cu BEOL, GAA nanosheet, GaN-on-SiC HEMT, 3D-NAND ON stack, W/Si XRR mirror -- with thickness notes and repeat brackets." | `stack_gallery` | `fig_stack_gallery.py` |

## Logic devices

| Prompt | Figure | Script |
|---|---|---|
| "Planar, FinFET, GAAFET and CFET side by side: an isometric 3D view over a cross-section for each, materials coloured by the palette (TiN gate, SiGe PMOS S/D, Si:P NMOS S/D), one line noting how the gate wraps the channel." | `transistor_evolution` | `fig_transistor_evolution.py` |
| "The same line-up as true solids with ghosted gates so the fins and sheets inside stay visible." | `transistor_evolution_solid` | `fig_transistor_solid.py` |
| "Redraw the line-up in the colours of the classic evolution diagram -- gate green, PMOS blue, NMOS red, well pink, oxide and substrate grey -- with a PMOS/NMOS pair in every device, on the solid backend." | `transistor_evolution_rolecolor` | `fig_transistor_evolution_rolecolor.py` |

## Memory

| Prompt | Figure | Script |
|---|---|---|
| "A 3D DRAM concept written as a process flow: deposit a SiO2/Al laminate, etch comb slots and circular vias, fill them with Si:P and Cu, add W word-line rails; label the parts." | `dram3d` | `fig_dram3d.py` |
| "3D NAND: alternating W/SiO2 films, a hexagonal (close-packed) array of memory holes in two blocks with an oxide slit between them, and in every hole the blocking oxide, nitride trap, tunnel oxide, poly-Si channel and oxide core as nested fills; beside it the same model quarter-sectioned, at the same size." | `nand3d` | `fig_nand3d.py` |
| "A 100-pair SiO2/Si3N4 stack on Si is too tall to draw -- show the bottom 10 and top 5 pairs with a break, cut the slit and the memory holes at the break, and bracket it '×100 (85 not drawn)'. One vector panel, one solid panel, and the side-on 2D cross-section like the stack gallery." | `nand_stack_break` | `fig_nand_stack_break.py` |
| "Solid NAND: word-line plates drilled with real circular holes, concentric charge-trap shells, and a quarter-section cutaway exposing the shell stack." | `nand3d_solid`, `nand3d_cutaway` | `fig_nand_solid.py` |
| "Four memory archetypes -- planar DRAM, trench DRAM, vertical-BL 3D DRAM, BiCS 3D NAND -- as solid panels with exact Boolean trenches, channels and holes; print the source for each in the panel." | `memory_generations` | `fig_memory_generations.py` |
| "Draw the horizontal-capacitor 3D DRAM the way the vendor slide shows it: dark background, grey capacitor plates on both sides of a blue transistor spine, teal channel pillars and bit line, white callouts." | `dram3d_reference_colors` | `fig_dram3d_reference_colors.py` |
| "Two schematics in red/green/white: (a) vertical storage capacitors on access transistors over a bit-line array, (b) horizontal capacitors on a staircase bit-line." | `dram3d_capacitor_schematics` | `fig_dram3d_capacitor_schematics.py` |

## Compound semiconductors and power

| Prompt | Figure | Script |
|---|---|---|
| "Six III-V / III-nitride emitters as small isometric stacks: GaAs homojunction laser, AlGaAs/GaAs DH laser, InP/InGaAsP DFB with a grating, GaAs/AlGaAs VCSEL with DBRs, InGaN/GaN blue LED, and a micro-LED with an etched mesa; cite the origin of each." | `optoelectronic_devices` | `fig_optoelectronic_devices.py` |
| "Four 4H-SiC power devices: Schottky diode with backside metal (cut away), planar DMOS with p-body and n+ implants, trench MOSFET with nested oxide/gate fills, and a tri-gate MOSFET; doped regions keep the SiC hue." | `sic_power_devices` | `fig_sic_power_devices.py` |

## Interconnect and packaging

| Prompt | Figure | Script |
|---|---|---|
| "Backside power delivery: wide backside Cu, W nano-TSVs up to buried W rails, a transistor tier, frontside Cu signal layers; make the thinned Si semi-transparent so the TSVs show; label everything." | `backside_power_delivery` | `fig_backside_power_delivery.py` |
| *(with a reference image)* "Simplified backside power example: signal layers exploded above as plates, a power block below with one nTSV running through, transistors on the thinned Si, solder balls underneath." | `backside_power_simple` | `fig_backside_power_simple.py` |
| "An HBM package: PCB substrate, Sn solder balls, Si interposer, GPU die, logic die and an eight-high DRAM stack with Cu bond layers; dies and interposer in the neutral die grey, logic dies one shade darker; stick-and-ball callouts with a dot on each named part." | `hbm_labeled` | `fig_hbm_labeled.py` |
| *(with two reference images)* "A modern GPU with six HBM stacks around the GPU die on an interposer on a substrate, as an exploded CoWoS view like this one; add an assembled plan view." | `gpu_cowos_exploded` | `fig_gpu_cowos_exploded.py` |
| *(with a reference image)* "Now the same GPU package assembled rather than exploded, with a dot on each named part and leaders dark enough to read against grey dies." | `gpu_cowos_assembled` | `fig_gpu_cowos_assembled.py` |

## Process-DSL demonstrations

| Prompt | Figure | Script |
|---|---|---|
| "Save a process model to JSON, read it back, and show that the two render identically." | `serialization_roundtrip` | `fig_serialization_roundtrip.py` |
| "Draw the photolithography process flow as six side-on cross-sections: deposition, resist coating, exposure through a photomask with light arrows, development, etching with ions, resist removal." | `litho_flow` | `fig_litho_flow.py` |
| "Show the same photolithography flow in 3D on the solid backend, with the mask above and the light and ion beams as cones." | `litho_flow_3d` | `fig_litho_flow_3d.py` |
| "Show the process DSL step by step on a circular wafer: inherited circular films, then rectangular, circular and rotated-elliptical etches with exact fills, ending with a 1D grating, one panel per step." | `dsl_feature_tour` | `fig_dsl_feature_tour.py` |
| "Etch five elliptical openings through the oxide with the major axis at 0, 30, 60, 90 and -45 degrees, fill them with Cu and W, and show the 3D view over a section along the row." | `rotated_ellipses` | `fig_rotated_ellipses.py` |
| "Two bare 300 mm substrates side by side, one with a V-notch and one with a major flat, no films and no callouts." | `wafer_notch` | `fig_wafer_notch.py` |

## Prompts that need no new script

These are answered by the API directly. The assistant writes a few lines and
calls `Wafer.render()`.

| Prompt | What the assistant writes |
|---|---|
| "A Si wafer with 50 nm oxide, a 300 nm-diameter Cu via down to the Si with 40 nm overfill, and an Al pad; label the oxide, the plug and the pad." | `Wafer(...)`, `add_layer(..., name=)`, `etch(Circle(..., diameter=), stop_on="Si")`, `fill(...)`, `add_pad(...)`, `render(path=..., labels=[...])` -- solid because of the circle |
| "Same, but a rectangular trench instead of the via." | identical flow with `Rectangle`; stays exact **vector** PDF |
| "A 300 mm wafer with its notch, 50 nm oxide, and a row of vias." | `Wafer(size=300*mm, shape="circle", notch="V", notch_angle=270)`, films inherit the notched footprint |
| "Etch elliptical trenches at 30° to the die edge and fill them with W." | `etch(Ellipse(c, (a, b), rotation=30))` + `fill(...)` -- exact rotated prisms in 3D and exact chords in the section |
| "A hexagonal field of 0.4 µm pillars at 1 µm pitch on a 10 × 8 µm die." | `hex_lattice((0, 10*um), (0, 8*um), 1*um)` and `add_feature(..., Circle(c, radius=0.2*um), ...)` per centre |
| "A 60-period W/Si mirror; only draw the first and last few periods." | `add_multilayer([("W", 2*nm), ("Si", 3*nm)], repeats=60, show=(4, 3), name="W/Si", unit="periods")` |
| "Just the side-on stack diagram of that, labelled." | `wafer.render(ax, view="section", labels="all", zscale=...)` -- the 2D cross-section renderer, vector output |
| "Put a dark background behind that render." | `Scene.render(background="#0E1B3D", edge_color="#3B4B72")` with light label colours -- a presentation override, kept in its own script |

## Reference-image prompts

With a multimodal assistant, attach the image and say what it is: "This is a
manufacturer illustration of a package, draw the same composition
with the package (substrate, tile groups, stacked dies, bridges),
labels like the original." The assistant should (1) use the image only for
composition, viewpoint and callouts, (2) write a new script, (3) add a
provenance row to `examples/REFERENCES.md`, and (4) keep the material palette
unless you ask for the reference's own colors. See the last section of the
showcase and `README.md`, "Authoring from reference images".
