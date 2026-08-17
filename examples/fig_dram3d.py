"""fig_dram3d.py -- Boolean-solid 3D DRAM concept written in the DSL.

The run-sheet deposits an alternating capacitor laminate, etches comb slots
and circular vertical vias, fills the vias, and patterns word-line rails.  The
etch/fill operations make ``Wafer.model()`` select the trimesh/manifold3d
backend automatically; PyVista renders the resulting watertight solids.

Outputs: ../docs/figures/dram3d.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Circle, Rectangle, Wafer
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"


def build_wafer():
    wafer = Wafer(size=(10.0, 6.4), substrate="Si", thickness=0.9)
    wafer.add_multilayer([("SiO2", 0.32), ("Al", 0.55)], repeats=6)
    wafer.add_layer("SiO2", 0.32)

    laminate = wafer.top - wafer.substrate_top
    for y_gap in (1.25, 2.55, 3.85, 5.15):
        wafer.etch(Rectangle((1.8, y_gap + 0.275), (3.6, 0.55)),
                   depth=laminate, name="left capacitor slot")
        wafer.etch(Rectangle((8.2, y_gap + 0.275), (3.6, 0.55)),
                   depth=laminate, name="right capacitor slot")

    vias = [
        wafer.etch(Circle((4.65, y), 0.34), depth=laminate, name=name)
        for y, name in zip((1.65, 3.20, 4.75),
                           ("channel via", "bit-line via", "channel via"))
    ]
    wafer.fill(vias[0], "SiP", overfill=0.9)
    wafer.fill(vias[1], "Cu", overfill=1.7)
    wafer.fill(vias[2], "SiP", overfill=0.9)

    wafer.add_pad("W", 3.70, 0.20, 0.55, 6.0, 0.45)
    wafer.add_pad("W", 5.75, 0.20, 0.55, 6.0, 0.45)
    return wafer


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    wafer = build_wafer()
    scene = wafer.model()  # etch/fill => automatic Boolean-solid dispatch
    top = wafer.top
    scene.label("capacitor plates (Al)", (9.6, 0.5, top - 1.0),
                position=(0.82, 0.46), size=8.2)
    scene.label("dielectric (SiO2)", (0.4, 0.5, 2.7),
                position=(0.08, 0.66), size=8.2)
    scene.label("word line (W)", (3.95, 0.4, top + 0.35),
                position=(0.10, 0.34), size=8.2)
    scene.label("channel (Si:P)", (4.65, 1.65, top + 0.75),
                position=(0.20, 0.18), size=8.2)
    scene.label("bit line (Cu)", (4.65, 3.20, top + 1.45),
                position=(0.67, 0.16), size=8.2)
    # Sizes above are points at the print width declared here; the image
    # band below is exactly that wide, with the title and note outside it.
    print_width, aspect = 6.3, 0.75
    image = scene.render_array(print_width_in=print_width, aspect=aspect,
                               zoom=0.88, azimuth=-24, elevation=18)

    band_h, top_h, bottom_h = print_width * aspect, 0.42, 0.34
    fig = plt.figure(figsize=(print_width, band_h + top_h + bottom_h))
    ax = fig.add_axes([0, bottom_h / fig.get_figheight(), 1,
                       band_h / fig.get_figheight()])
    ax.imshow(image)
    ax.set_axis_off()
    ax.set_title("3D DRAM concept, written as a process flow",
                 fontsize=11.0, color=C_SLATE, weight="bold", pad=7)
    fig.text(0.5, 0.012,
            "deposit multilayer $\\rightarrow$ etch(comb slots, circular vias) "
            "$\\rightarrow$ fill(Si:P, Cu) $\\rightarrow$ pattern(W rails)",
            fontsize=7.2, color=C_GREY, ha="center", va="bottom")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "dram3d"
    fig.savefig(f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
