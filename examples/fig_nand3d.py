"""fig_nand3d.py -- DSL-authored 3D NAND charge-trap structure.

Alternating dielectric/word-line films are blanket-deposited; a close-packed
(hexagonal) array of circular memory holes is Boolean-etched in each of two
blocks separated by an oxide-filled slit, and nested etch/fill operations
create the blocking oxide, nitride trap, tunnel oxide, poly-Si channel and
oxide core in every hole. The hole arrangement follows the plan-view
geometry of real 3D NAND (staggered rows, slits between blocks). The DSL
selects the trimesh/manifold3d + PyVista backend automatically.

Panel (b) quarter-sections the same model with ``Scene.cutaway(x=, y=)``,
which subtracts a camera-facing corner from every part separately, so each
shell keeps its own material color on the exposed face. It also carries a
labelled x, y, z triad from ``Scene.axes()``.

Outputs: ../docs/figures/nand3d.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Circle, Rectangle, Wafer, hex_lattice
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

SIZE = (10.0, 7.2)
SLIT_W = 0.5                       # oxide-filled slit between the two blocks
BLOCKS = ((0.0, SIZE[0] / 2 - SLIT_W / 2), (SIZE[0] / 2 + SLIT_W / 2, SIZE[0]))
PITCH = 1.15                       # centre-to-centre hole spacing
SHELLS = (                         # radius, material, name (outer -> core)
    (0.46, "SiO2", "blocking oxide"),
    (0.37, "Si3N4", "charge-trap nitride"),
    (0.28, "SiO2", "tunnel oxide"),
    (0.20, "Si", "poly-Si channel"),
    (0.11, "SiO2", "oxide core"),
)


def hole_centers():
    """Hexagonal memory-hole array in each block, rows along y."""
    centers = []
    for x0, x1 in BLOCKS:
        centers += hex_lattice((x0, x1), (0.0, SIZE[1]), PITCH,
                               margin=0.55, axis="y")
    return centers


def build_wafer():
    wafer = Wafer(size=SIZE, substrate="Si", thickness=0.50)
    wafer.add_layer("SiO2", 0.35)
    wafer.add_multilayer([("W", 0.65), ("SiO2", 0.45)], repeats=4)
    stack_depth = wafer.top - wafer.substrate_top

    # slit between the two blocks, filled with oxide
    slit = wafer.etch(Rectangle((SIZE[0] / 2, SIZE[1] / 2), (SLIT_W, SIZE[1])),
                      depth=stack_depth, name="slit")
    wafer.fill(slit, "SiO2")

    centers = hole_centers()
    for radius, material, name in SHELLS:
        for center in centers:
            opening = wafer.etch(Circle(center, radius), depth=stack_depth,
                                 name=name)
            wafer.fill(opening, material)
    return wafer


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    # Two panels of identical size, side by side. Each is half the print
    # width, so every callout is two lines rather than one: at 3.1 in a
    # single-line "poly-Si channel" would eat a quarter of the panel and
    # leave the structure smaller than the cutaway beside it.
    print_width, gap = 6.3, 0.08
    panel_w = 0.5 * (print_width - gap)
    aspect = 0.82

    wafer = build_wafer()
    scene = wafer.model()  # circular holes + nested fills => solid backend
    z = wafer.top
    # the default camera looks from +x, +y: the nearest hole has the largest
    # x + y, and the visible side faces are +x and +y
    fx, fy = max(hole_centers(), key=lambda c: c[0] + c[1])
    # Both left-hand callouts point at the +y face, which is screen left at
    # this camera, so they stack in one column with the slit above the stack.
    scene.label("slit\n(oxide)", (SIZE[0] / 2, SIZE[1] - 0.2, z),
                via=(0.19, 0.44), position=(0.02, 0.44), size=8.2)
    scene.label("word\nlines (W)", (4.0, SIZE[1], 2.1),
                via=(0.19, 0.66), position=(0.02, 0.66), size=8.2)
    shells = [("blocking\nSiO2", -0.42), ("Si3N4\ntrap", -0.33),
              ("tunnel\nSiO2", -0.24), ("poly-Si\nchannel", -0.16),
              ("oxide\ncore", 0.0)]
    for i, (name, dx) in enumerate(shells):
        scene.label(name, (fx + dx, fy, z), via=(0.87, 0.30 + 0.145 * i),
                    position=(0.99, 0.30 + 0.145 * i), justify="right",
                    size=8.2)
    # Sizes above are points at the panel width declared here.
    image = scene.render_array(print_width_in=panel_w, aspect=aspect,
                               zoom=0.90, azimuth=-29, elevation=22)

    # (b) the same model, quarter-sectioned. A second model is built because
    # the Boolean cut consumes the parts of the first one.
    cut_width, cut_aspect = panel_w, aspect
    cut_scene = build_wafer().model()
    # Both planes land on hole centres, so the exposed faces cut through the
    # channels and show every concentric shell. At this camera +x runs
    # towards the viewer, so taking the second hole column past the slit
    # brings the cut forward and leaves most of the structure standing. A
    # plane between columns would show only the W/SiO2 stripes, and one at
    # the slit (x = SIZE[0]/2) a blank oxide wall.
    columns = sorted({x for x, _ in hole_centers()})
    rows = sorted({y for _, y in hole_centers()})
    far_block = [x for x in columns if x > SIZE[0] / 2]
    cut_scene.cutaway(x=far_block[1], y=min(rows, key=lambda r:
                                            abs(r - SIZE[1] / 2)))
    # A labelled triad on the sectioned panel, where the cut faces make the
    # orientation worth stating.
    # -y is screen left at this camera, so the triad clears the block there.
    cut_scene.axes(origin=(0.55 * SIZE[0], -0.55 * SIZE[1], 0.0),
                   length=0.20 * SIZE[0], size=8.2)
    cut_image = cut_scene.render_array(print_width_in=cut_width,
                                       aspect=cut_aspect, zoom=0.98,
                                       azimuth=-29, elevation=22)

    # Explicit inch budget: title band, the two panels, their (a)/(b) tags
    # and the process note.
    panel_h = panel_w * aspect
    title_h, tag_h, footer_h = 0.30, 0.26, 0.24
    total = title_h + panel_h + tag_h + footer_h
    fig = plt.figure(figsize=(print_width, total))

    for column, (panel, tag) in enumerate((
            (image, "(a) complete solid"),
            (cut_image, "(b) quarter-section cutaway"))):
        left = column * (panel_w + gap) / print_width
        ax = fig.add_axes([left, (footer_h + tag_h) / total,
                           panel_w / print_width, panel_h / total])
        ax.imshow(panel)
        ax.set_axis_off()
        ax.text(0.0, -0.02, tag, transform=ax.transAxes, fontsize=8.3,
                color=C_SLATE, weight="bold", va="top")

    fig.text(0.5, 1 - 0.5 * title_h / total,
             "3D NAND: Boolean memory holes and exact concentric fills",
             fontsize=10.2, color=C_SLATE, weight="bold", ha="center",
             va="center")
    fig.text(0.5, 0.008,
             "deposit(W/SiO$_2$ stack) $\\rightarrow$ etch(circular memory "
             "holes) $\\rightarrow$ nested fill(charge-trap stack)",
             fontsize=7.2, color=C_GREY, ha="center", va="bottom")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "nand3d"
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
