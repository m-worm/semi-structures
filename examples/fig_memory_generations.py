"""fig_memory_generations.py -- planar and 3D memories built with the DSL.

Every device panel is authored with process operations.  Rectangular planar
features can use either renderer; topology-changing circular etches and nested
fills automatically select the trimesh/manifold3d Boolean backend used here.

The schematic archetypes follow Dennard (1968), Mandelman et al. (2002), Oh
et al. (2024), and Tanaka et al. (2007); see examples/REFERENCES.md.

Outputs: ../docs/figures/memory_generations.pdf (+ .png)
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


def planar_dram():
    wafer = Wafer(size=(8.0, 5.2), substrate="Si", thickness=0.9)
    wafer.add_layer("SiO2", 0.22, label="gate oxide")
    wafer.add_pad("W", 2.4, 0.4, 0.9, 4.4, 0.42)
    wafer.add_pad("Cu", 0.4, 2.15, 7.2, 0.55, 0.30)
    z = wafer.top
    wafer.add_feature("TiN", Rectangle((6.1, 1.7), (1.8, 1.8)),
                      0.22, z0=z)
    wafer.add_feature("HfO2", Rectangle((6.1, 1.7), (1.4, 1.4)),
                      0.28, z0=z + 0.22)
    wafer.add_feature("TiN", Rectangle((6.1, 1.7), (0.9, 0.9)),
                      0.45, z0=z + 0.50)
    return wafer.scene("solid")


def trench_dram():
    wafer = Wafer(size=(8.0, 5.2), substrate="Si", thickness=2.7)
    wafer.add_layer("SiO2", 0.20)
    for x in (1.65, 4.00, 6.35):
        outer = wafer.etch(Circle((x, 2.35), 0.58), depth=2.40,
                           name="deep trench")
        wafer.fill(outer, "HfO2")
        inner = wafer.etch(Circle((x, 2.35), 0.36), depth=2.40,
                           name="storage electrode opening")
        wafer.fill(inner, "TiN", overfill=0.28)
    wafer.add_pad("W", 0.4, 4.05, 7.2, 0.48, 0.35)
    scene = wafer.model()
    scene.cutaway(y=2.35)
    return scene


def vertical_dram():
    wafer = Wafer(size=(8.0, 5.2), substrate="Si", thickness=0.65)
    wafer.add_multilayer([("SiO2", 0.28), ("W", 0.34)], repeats=5)
    depth = wafer.top - wafer.substrate_top
    for x in (1.55, 4.0, 6.45):
        opening = wafer.etch(Circle((x, 2.35), 0.34), depth=depth,
                              name="vertical bit-line channel")
        wafer.fill(opening, "SiP")
    wafer.add_pad("Cu", 0.65, 2.10, 6.7, 0.50, 0.30)
    scene = wafer.model()
    scene.cutaway(y=2.35)
    return scene


def nand_bics():
    wafer = Wafer(size=(8.0, 5.2), substrate="Si", thickness=0.55)
    wafer.add_layer("SiO2", 0.20)
    wafer.add_multilayer([("W", 0.42), ("SiO2", 0.38)], repeats=5)
    depth = wafer.top - wafer.substrate_top
    centers = ((1.7, 1.5), (4.0, 1.5), (6.3, 1.5),
               (1.7, 3.7), (4.0, 3.7), (6.3, 3.7))
    for radius, material, name in (
            (0.50, "SiO2", "blocking oxide"),
            (0.35, "Si3N4", "charge-trap nitride"),
            (0.20, "Si", "vertical channel")):
        openings = [wafer.etch(Circle(center, radius), depth=depth,
                               name=name) for center in centers]
        for opening in openings:
            wafer.fill(opening, material)
    return wafer.model()


def draw_panel(ax, scene, title, feature, source, *, zoom=1.08,
               azimuth=-31, elevation=20):
    image = scene.render_array(window=(900, 720), zoom=zoom,
                               azimuth=azimuth, elevation=elevation)
    ax.imshow(image, extent=(0.0, 1.0, 0.30, 0.92), aspect="auto")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_axis_off()
    ax.text(0.02, 0.985, title, transform=ax.transAxes, fontsize=8.9,
            color=C_SLATE, weight="bold", va="top")
    ax.text(0.02, 0.105, feature, transform=ax.transAxes, fontsize=7.0,
            color=C_SLATE)
    ax.text(0.02, 0.035, source, transform=ax.transAxes, fontsize=7.0,
            color=C_GREY)


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, axes = plt.subplots(2, 2, figsize=(6.5, 6.1))
    fig.subplots_adjust(left=0.035, right=0.985, top=0.91, bottom=0.035,
                        hspace=0.17, wspace=0.07)
    fig.suptitle("Memory structures: planar cells to vertical arrays",
                 fontsize=11.5, color=C_SLATE, weight="bold")
    fig.text(0.5, 0.925,
             "DSL-authored schematic geometry; dimensions chosen for legibility",
             fontsize=7.6, color=C_GREY, ha="center")

    draw_panel(axes[0, 0], planar_dram(), "(a) Planar 1T1C DRAM",
               "patterned word/bit lines + stacked capacitor",
               "Dennard, US 3,387,286 (1968)")
    draw_panel(axes[0, 1], trench_dram(), "(b) Deep-trench DRAM",
               "circular deep etch + exact dielectric/electrode fills",
               "Mandelman et al., IBM JRD 46 (2002)",
               azimuth=35, elevation=5)
    draw_panel(axes[1, 0], vertical_dram(), "(c) Vertical-BL 3D DRAM",
               "repeated stack + circular depth etch + Si:P fill",
               "Oh et al., IEEE VLSI (2024)", azimuth=35, elevation=5)
    draw_panel(axes[1, 1], nand_bics(), "(d) BiCS 3D NAND",
               "word-line stack + nested charge-trap fills",
               "Tanaka et al., IEEE VLSI (2007)")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "memory_generations"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
