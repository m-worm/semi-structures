"""fig_transistor_solid.py -- transistor evolution on the solid backend.

The planar / FinFET / GAAFET / CFET line-up rebuilt with semi_structures.solid
(trimesh geometry, PyVista render): true solids, consistent parallel
isometric cameras, and semi-transparent gates on the wrap-gate devices
so the fins and nanosheets inside stay visible. The 2D cross-section row
and layout are shared with fig_transistor_evolution. Colors are
semi_structures.style materials: TiN gate gold, PMOS S/D SiGe, NMOS S/D Si:P,
channel the doped-Si shade.

Outputs: ../docs/figures/transistor_evolution_solid.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.solid import Scene
from semi_structures.style import C_GREY, C_SLATE, MATERIAL, PLOT_STYLE, doped
from fig_transistor_evolution import cross_section

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

WELL = doped("Si", 0.14)
SD_P = "SiGe"
SD_N = doped("Si", 0.28)
GATE_ALPHA = 0.45


def planar_scene():
    s = Scene()
    s.box((0, 0, 0), (10, 7, 1.5), "Si")
    s.box((0, 0, 1.5), (10, 7, 1.0), "SiO2")
    s.box((0.7, 0.5, 2.5), (8.6, 6.0, 0.55), WELL)
    s.box((0.7, 0.5, 3.05), (2.4, 6.0, 1.15), SD_P)
    s.box((3.55, 0.5, 3.05), (2.9, 6.0, 1.7), "TiN")
    s.box((6.9, 0.5, 3.05), (2.4, 6.0, 1.15), SD_P)
    return s


def finfet_scene():
    s = Scene()
    s.box((0, 0, 0), (10, 7, 1.5), "Si")
    s.box((0, 0, 1.5), (10, 7, 0.8), "SiO2")
    for y_fin in (1.5, 4.3):
        s.box((0.6, y_fin, 2.3), (3.3, 1.1, 2.3), SD_P)
        s.box((3.9, y_fin, 2.3), (2.2, 1.1, 2.3), WELL)
        s.box((6.1, y_fin, 2.3), (3.3, 1.1, 2.3), SD_P)
    s.box((3.9, 0.4, 2.3), (2.2, 6.2, 3.0), "TiN", opacity=GATE_ALPHA)
    return s


def gaafet_scene():
    s = Scene()
    s.box((0.6, 0, 0), (8.8, 7, 1.5), "Si")
    s.box((0.6, 0, 1.5), (8.8, 7, 0.8), "SiO2")
    for z_rib in (2.9, 4.0, 5.1):
        s.box((0.9, 2.1, z_rib), (3.0, 2.8, 0.5), SD_P)
        s.box((3.9, 2.1, z_rib), (2.2, 2.8, 0.5), WELL)
        s.box((6.1, 2.1, z_rib), (3.0, 2.8, 0.5), SD_P)
    s.box((3.9, 1.4, 2.3), (2.2, 4.2, 3.9), "TiN", opacity=GATE_ALPHA)
    return s


def cfet_scene():
    s = Scene()
    s.box((1.6, 0, 0), (6.8, 7, 1.5), "Si")
    s.box((1.6, 0, 1.5), (6.8, 7, 0.8), "SiO2")
    for z_rib, sd in [(2.6, SD_P), (3.4, SD_P), (4.2, SD_P),
                      (5.4, SD_N), (6.2, SD_N), (7.0, SD_N)]:
        s.box((2.0, 2.2, z_rib), (2.0, 2.6, 0.45), sd)
        s.box((4.0, 2.2, z_rib), (2.0, 2.6, 0.45), WELL)
        s.box((6.0, 2.2, z_rib), (2.0, 2.6, 0.45), sd)
    s.box((4.0, 1.5, 2.3), (2.0, 4.0, 5.6), "TiN", opacity=GATE_ALPHA)
    return s


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=(6.3, 5.9))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.set_axis_off()

    panels = [("Planar", "(pre 2011)", 12.5, "planar", planar_scene, 1.5),
              ("FinFET", "(2011$-$2023)", 37.5, "fin", finfet_scene, 1.5),
              ("GAAFET", "(2023$-$)", 62.5, "gaa", gaafet_scene, 1.5),
              ("CFET", "(2032?)", 87.5, "cfet", cfet_scene, 1.35)]
    for name, years, cx, kind, builder, zoom in panels:
        ax.text(cx, 96.8, name, fontsize=9.0, color=C_SLATE, ha="center",
                weight="bold")
        ax.text(cx, 93.2, years, fontsize=7.2, color=C_GREY, ha="center")
        img = builder().render_array(window=(1400, 1100), zoom=zoom,
                                     azimuth=-30.0, elevation=-16.0)
        h = 24.6 * img.shape[0] / img.shape[1]
        ax.imshow(img, extent=(cx - 12.3, cx + 12.3, 64.5 - h, 64.5),
                  zorder=3)
        cross_section(ax, cx, kind)

    ax.text(87.5, 70.5, "gates ghosted to show\nthe stacked channels",
            fontsize=7.0, color=C_GREY, ha="center")
    for y, lab in [(56.0, "3D view"), (18.0, "cross-\nsection")]:
        ax.text(1.2, y, lab, fontsize=7.6, color=C_SLATE, ha="center",
                va="center", rotation=90)
    ax.plot([6.5, 99], [41.0, 41.0], color=C_GREY, lw=0.7, ls=(0, (4, 3)))
    ax.text(50, 1.2, "solid backend (semi_structures.solid): true geometry, "
            "semi-transparent TiN gates; Si blues, PMOS S/D SiGe, "
            "NMOS S/D Si:P, SiO$_2$ sand",
            fontsize=7.0, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "transistor_evolution_solid"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
