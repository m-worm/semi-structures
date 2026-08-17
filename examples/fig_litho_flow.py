"""fig_litho_flow.py -- the photolithography process flow, six cross-sections.

Deposition, resist coating, exposure through a photomask, development,
etching and resist removal, each panel one ``Wafer`` state drawn by the 2D
section renderer (``render(view="section")``). Exposure is modelled as a
material replacement in the resist (``implant``, exposed resist a lighter
shade), development and the film etch as rectangular ``etch`` operations
through the same openings, resist removal with ``strip``. The photomask,
light and ions are annotations on the section; light uses the reserved
amber beam colour, matter stays in the palette (Si wafer, SiO2 film, resist).

Outputs: ../docs/figures/litho_flow.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle as MplRect

from semi_structures import Rectangle, Wafer
from semi_structures.style import (
    C_EVANESCENT, C_GREY, C_SLATE, MATERIAL, PLOT_STYLE, mix,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

W, D = 10.0, 6.0                       # wafer footprint (x, y)
T_SUB, T_FILM, T_RESIST = 1.5, 0.5, 1.0
EXPOSED = [(0.0, 2.0), (3.8, 6.2), (8.0, 10.0)]        # x ranges opened
RESIST_EXPOSED = mix(MATERIAL["resist"][0], "#FFFFFF", 0.5)


def state(step):
    """The wafer after litho step ``step`` (1..6)."""
    w = Wafer(size=(W, D), substrate="Si", thickness=T_SUB, name="wafer")
    w.add_layer("SiO2", T_FILM, name="etching material (SiO$_2$)")
    if step >= 2:
        w.add_layer("resist", T_RESIST, name="photoresist")
    if step >= 3:                                        # exposure
        for x0, x1 in EXPOSED:
            w.implant(Rectangle.from_corner(x0, 0.0, x1 - x0, D),
                      RESIST_EXPOSED, depth=T_RESIST, name="exposed resist")
    if step >= 4:                                        # development
        for x0, x1 in EXPOSED:
            w.etch(Rectangle.from_corner(x0, 0.0, x1 - x0, D),
                   depth=T_RESIST, name="developed")
    if step >= 5:                                        # etch the film
        for x0, x1 in EXPOSED:
            w.etch(Rectangle.from_corner(x0, 0.0, x1 - x0, D),
                   stop_on="wafer", name="etched")
    if step >= 6:                                        # resist removal
        w.strip("photoresist")
    return w


def annotate(ax, step, top):
    """Mask + light for exposure, ions for the etch."""
    if step == 3:
        z_mask, t_mask = top + 1.1, 0.3
        ax.add_patch(MplRect((-0.3, z_mask), W + 0.6, t_mask,
                             facecolor=MATERIAL["substrate"][0],
                             edgecolor=C_GREY, lw=0.5, zorder=3))
        for a, b in ((2.0, 3.8), (6.2, 8.0)):            # chrome pattern
            ax.add_patch(MplRect((a, z_mask + t_mask), b - a, 0.16,
                                 facecolor=MATERIAL["W"][0],
                                 edgecolor="none", zorder=4))
        for x0, x1 in EXPOSED:
            xm = 0.5 * (x0 + x1)
            ax.add_patch(FancyArrowPatch((xm, z_mask + 1.3), (xm, top + 0.05),
                                         arrowstyle="-|>", mutation_scale=7,
                                         color=C_EVANESCENT, lw=0.9,
                                         zorder=5))
        ax.text(W + 0.6, z_mask + t_mask / 2, "photomask", fontsize=7.0,
                color=C_SLATE, ha="left", va="center")
        ax.text(W + 0.6, z_mask + 1.25, "light", fontsize=7.0,
                color=C_EVANESCENT, ha="left", va="center")
        ax.set_ylim(top=z_mask + 1.7)
    elif step == 5:
        for x0, x1 in EXPOSED:
            xm = 0.5 * (x0 + x1)
            ax.add_patch(FancyArrowPatch((xm, top + 1.5), (xm, T_SUB + 0.05),
                                         arrowstyle="-|>", mutation_scale=7,
                                         color=C_GREY, lw=0.9, zorder=5))
        ax.text(W + 0.6, top + 1.2, "ions / etchant", fontsize=7.0,
                color=C_SLATE, ha="left", va="center")
        ax.set_ylim(top=top + 1.9)


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, axes = plt.subplots(2, 3, figsize=(6.3, 2.05))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.10,
                        wspace=0.06, hspace=0.75)
    top_max = T_SUB + T_FILM + T_RESIST
    captions = ["1  deposition", "2  resist coating", "3  exposure",
                "4  development", "5  etching", "6  resist removal"]
    for k, (ax, cap) in enumerate(zip(axes.flat, captions), start=1):
        w = state(k)
        labels = {1: ["wafer", "etching material (SiO$_2$)"],
                  2: ["photoresist"]}.get(k, False)
        w.render(ax=ax, view="section", labels=labels, label_size=7.0,
                 label_marker="dot")
        top = T_SUB + T_FILM + (T_RESIST if 2 <= k <= 5 else 0.0)
        annotate(ax, k, top)
        # one common frame for every panel so all six share a scale, with
        # room on the left for callouts and above for the mask and arrows
        ax.set_xlim(-4.4, W + 3.8)
        ax.set_ylim(-0.3, top_max + 2.0)
        ax.text(0.5, -0.02, cap, transform=ax.transAxes, fontsize=8.3,
                color=C_SLATE, weight="bold", ha="center", va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "litho_flow"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
