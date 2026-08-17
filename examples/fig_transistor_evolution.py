"""fig_transistor_evolution.py -- planar / FinFET / GAAFET in the book style.

Recreation of the classic transistor-evolution diagram using the material
color system and the semi_structures.iso engine: color means material, not
circuit role. Gate = TiN (its real gold), S/D epi = SiGe blue, well and
channel = the doped-Si shade, isolation = SiO2 sand, substrate = Si.
Authored at print width (6.3 in) per the typography law.

Outputs: ../docs/figures/transistor_evolution.pdf (+ .png)

Structural precedents include D. Hisamoto et al., IEEE Trans. Electron
Devices 47, 2320--2325 (2000), https://doi.org/10.1109/16.887014, and
N. Loubet et al., VLSI Technology (2017),
https://doi.org/10.23919/VLSIT.2017.7998183.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.iso import Box, draw_scene, iso
from semi_structures.style import C_GREY, C_SLATE, MATERIAL, PLOT_STYLE, doped

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

SI = MATERIAL["Si"][0]
OX = MATERIAL["SiO2"][0]
GATE = MATERIAL["TiN"][0]
SD = MATERIAL["SiGe"][0]
WELL = doped("Si", 0.14)
EDGE = "#aab1b7"


def planar_boxes():
    return [
        Box((0, 0, 0), (10, 7, 1.5), SI, 0, ("right", "bulk Si")),
        Box((0, 0, 1.5), (10, 7, 1.0), OX, 1, ("left", "SiO$_2$")),
        Box((0.7, 0.5, 2.5), (8.6, 6.0, 0.55), WELL, 2),
        Box((0.7, 0.5, 3.05), (2.4, 6.0, 1.15), SD, 3),
        Box((3.55, 0.5, 3.05), (2.9, 6.0, 1.7), GATE, 3,
            ("top_y", "gate")),
        Box((6.9, 0.5, 3.05), (2.4, 6.0, 1.15), SD, 3),
    ]


def finfet_boxes():
    boxes = [
        Box((0, 0, 0), (10, 7, 1.5), SI, 0, ("right", "bulk Si")),
        Box((0, 0, 1.5), (10, 7, 0.8), OX, 1, ("left", "SiO$_2$")),
    ]
    for y_fin in (1.5, 4.3):
        boxes += [
            Box((0.6, y_fin, 2.3), (3.3, 1.1, 2.3), SD, 2),
            Box((3.9, y_fin, 2.3), (2.2, 1.1, 2.3), WELL, 2),
            Box((6.1, y_fin, 2.3), (3.3, 1.1, 2.3), SD, 2),
        ]
    # The fin top face is too small for a legal (>= 7 pt) face label; the
    # S/D callout is a leader annotation in make_figure() instead.
    boxes.append(Box((3.9, 0.4, 2.3), (2.2, 6.2, 3.0), GATE, 3,
                     ("top_y", "gate")))
    return boxes


def cfet_boxes():
    """CFET: NMOS nanosheets stacked over PMOS, one gate, one footprint.
    Materials tell the two devices apart: PMOS S/D = SiGe epi, NMOS S/D =
    heavily doped Si:P (darker blue)."""
    sd_n = doped("Si", 0.28)
    boxes = [
        Box((1.6, 0, 0), (6.8, 7, 1.5), SI, 0, ("right", "bulk Si")),
        Box((1.6, 0, 1.5), (6.8, 7, 0.8), OX, 1, ("left", "SiO$_2$")),
    ]
    for z_rib, sd in [(2.6, SD), (3.4, SD), (4.2, SD),
                      (5.4, sd_n), (6.2, sd_n), (7.0, sd_n)]:
        boxes += [
            Box((2.0, 2.2, z_rib), (2.0, 2.6, 0.45), sd, 2),
            Box((4.0, 2.2, z_rib), (2.0, 2.6, 0.45), WELL, 2),
            Box((6.0, 2.2, z_rib), (2.0, 2.6, 0.45), sd, 2),
        ]
    boxes.append(Box((4.0, 1.5, 2.3), (2.0, 4.0, 5.6), GATE, 3,
                     ("top_y", "gate")))
    return boxes


def gaafet_boxes():
    boxes = [
        Box((0.6, 0, 0), (8.8, 7, 1.5), SI, 0, ("right", "bulk Si")),
        Box((0.6, 0, 1.5), (8.8, 7, 0.8), OX, 1, ("left", "SiO$_2$")),
    ]
    for z_rib in (2.9, 4.0, 5.1):
        boxes += [
            Box((0.9, 2.1, z_rib), (3.0, 2.8, 0.5), SD, 2),
            Box((3.9, 2.1, z_rib), (2.2, 2.8, 0.5), WELL, 2),
            Box((6.1, 2.1, z_rib), (3.0, 2.8, 0.5), SD, 2),
        ]
    boxes.append(Box((3.9, 1.4, 2.3), (2.2, 4.2, 3.9), GATE, 3,
                     ("top_y", "gate")))
    return boxes


def cross_section(ax, cx, kind):
    def rect(x, y, w, h, color, label=None, label_color=C_SLATE):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                                   edgecolor=EDGE, lw=0.5))
        if label:
            ax.text(x + w / 2, y + h / 2, label, fontsize=7.0,
                    color=label_color, ha="center", va="center")

    if kind == "planar":
        # Cut along the channel, not across it: the across-channel cut of a
        # planar device is only a stack of layers, with no source, no drain
        # and no channel. The active region spans the footprint bracket
        # below, so the 1x reference is unchanged.
        rect(cx - 8, 11.0, 16, 2.4, SI, "Si")
        rect(cx - 8, 13.4, 16, 4.0, WELL)
        ax.text(cx, 14.3, "well", fontsize=7.0, color=C_SLATE,
                ha="center", va="center")
        rect(cx - 8, 14.6, 2.5, 2.8, OX)                 # isolation
        rect(cx + 5.5, 14.6, 2.5, 2.8, OX)
        rect(cx - 5.5, 15.2, 3.3, 2.2, SD)               # source
        rect(cx + 2.2, 15.2, 3.3, 2.2, SD)               # drain
        rect(cx - 2.6, 17.4, 5.2, 0.35, OX)              # gate oxide
        rect(cx - 2.6, 17.75, 5.2, 3.2, GATE, "gate")
        note, width_note = "gate controls one face", "1$\\times$"
        x_b, w_b = cx - 5.5, 11.0
    elif kind == "fin":
        rect(cx - 8, 11.0, 16, 2.6, SI, "Si")
        rect(cx - 6, 13.6, 12, 12.6, GATE, None)
        ax.text(cx, 24.6, "gate", fontsize=7.0, color=C_SLATE,
                ha="center")
        for dx in (-3.4, 1.2):
            rect(cx + dx, 13.6, 2.2, 9.2, WELL)
        note, width_note = "gate wraps 3 sides", "$\\frac{1}{2}\\times$"
        x_b, w_b = cx - 3.4, 6.8
    elif kind == "gaa":
        rect(cx - 6, 11.0, 12, 2.6, SI, "Si")
        rect(cx - 4.4, 13.6, 8.8, 14.2, GATE, None)
        ax.text(cx, 25.6, "gate", fontsize=7.0, color=C_SLATE,
                ha="center")
        for y0 in (15.2, 18.6, 22.0):
            rect(cx - 2.9, y0, 5.8, 2.0, WELL)
        note, width_note = "gate wraps 4 sides", "$\\frac{1}{4}\\times$"
        x_b, w_b = cx - 2.9, 5.8
    else:
        rect(cx - 5, 11.0, 10, 2.2, SI, "Si")
        rect(cx - 3.6, 13.2, 7.2, 20.4, GATE, None)
        ax.text(cx, 31.2, "gate", fontsize=7.0, color=C_SLATE,
                ha="center")
        for y0 in (14.6, 17.2, 19.8):
            rect(cx - 2.3, y0, 4.6, 1.6, WELL)
        for y0 in (23.6, 26.2, 28.8):
            rect(cx - 2.3, y0, 4.6, 1.6, WELL)
        ax.text(cx + 4.4, 17.8, "p", fontsize=7.0, color=C_SLATE)
        ax.text(cx + 4.4, 26.8, "n", fontsize=7.0, color=C_SLATE)
        note, width_note = "two devices, one footprint", \
            "$\\frac{1}{4}\\times$"
        x_b, w_b = cx - 2.3, 4.6

    ax.text(cx, 8.6, note, fontsize=7.0, color=C_SLATE, ha="center")
    ax.plot([x_b, x_b, x_b + w_b, x_b + w_b],
            [7.2, 6.5, 6.5, 7.2], color=C_GREY, lw=0.7)
    ax.text(x_b + w_b / 2, 4.6, width_note + " footprint width",
            fontsize=7.0, color=C_GREY, ha="center")


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=(6.3, 5.9))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.set_axis_off()

    titles = [("Planar", "(pre 2011)", 12.5, "planar", planar_boxes),
              ("FinFET", "(2011$-$2023)", 37.5, "fin", finfet_boxes),
              ("GAAFET", "(2023$-$)", 62.5, "gaa", gaafet_boxes),
              ("CFET", "(2032?)", 87.5, "cfet", cfet_boxes)]
    iso_origin_y, scale = 54.0, 1.16
    for name, years, cx, kind, builder in titles:
        ax.text(cx, 96.8, name, fontsize=9.0, color=C_SLATE, ha="center",
                weight="bold")
        ax.text(cx, 93.2, years, fontsize=7.2, color=C_GREY, ha="center")
        draw_scene(ax, builder(), origin=(cx - 2.0, iso_origin_y),
                   scale=scale)
        cross_section(ax, cx, kind)

    # leader labels where face labels would collide
    for cx0, world, text, xytext in [
            (10.5, (1.9, 3.5, 4.2), "source", (5.5, 80.5)),
            (10.5, (8.1, 3.5, 4.2), "drain", (23.0, 80.5)),
            (10.5, (7.5, 0.5, 2.8), "well (Si)", (25.5, 50.5)),
            (35.5, (2.25, 2.05, 4.6), "S/D", (30.5, 80.5)),
            (85.5, (7.0, 3.5, 7.2), "NMOS (Si:P)", (96.5, 84.0)),
            (85.5, (7.0, 3.5, 2.8), "PMOS (SiGe)", (95.5, 50.5))]:
        u, v = iso(*world)
        ax.annotate(text, xy=(cx0 + scale * u, iso_origin_y + scale * v),
                    xytext=xytext, fontsize=7.0, color=C_SLATE,
                    ha="center",
                    arrowprops=dict(arrowstyle="-", color=C_GREY, lw=0.7))

    for y, lab in [(72.0, "3D view"), (18.0, "cross-\nsection")]:
        ax.text(2.2, y, lab, fontsize=7.6, color=C_SLATE, ha="center",
                va="center", rotation=90)
    ax.plot([6.5, 99], [41.0, 41.0], color=C_GREY, lw=0.7, ls=(0, (4, 3)))
    ax.text(50, 1.2, "color = material: Si blues (channel doped shade, "
            "PMOS S/D SiGe, NMOS S/D Si:P), TiN gate gold, SiO$_2$ sand",
            fontsize=7.0, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "transistor_evolution"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
