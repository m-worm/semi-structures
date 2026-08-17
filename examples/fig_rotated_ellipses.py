"""fig_rotated_ellipses.py -- rotated elliptical etch and fill, 3D and section.

Five elliptical openings etched through an oxide to the Si with their major
axis at 0, 30, 60, 90 and -45 degrees to the die edge (``Ellipse(center,
(a, b), rotation=deg)``) and filled with Cu / W. The solid backend rotates
the elliptical prisms exactly; the 2D section at the row's centre line shows
the chord of each fill, which follows the rotation.

Outputs: ../docs/figures/rotated_ellipses.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Ellipse, Wafer, nm, um
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

ANGLES = (0, 30, 60, 90, -45)
ROW_Y = 1.0 * um


def build():
    wafer = Wafer(size=(3.0 * um, 2.0 * um), substrate="Si",
                  thickness=300 * nm, name="Si")
    wafer.add_layer("SiO2", 250 * nm, name="oxide")
    for i, angle in enumerate(ANGLES):
        opening = wafer.etch(
            Ellipse((0.45 * um + i * 0.52 * um, ROW_Y), (220 * nm, 110 * nm),
                    rotation=angle),
            stop_on="Si", name=f"ellipse {angle} deg")
        wafer.fill(opening, "Cu" if i % 2 == 0 else "W",
                   name=f"fill {angle} deg")
    return wafer


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    wafer = build()
    fig = plt.figure(figsize=(6.3, 4.6))
    ax3 = fig.add_axes([0.02, 0.36, 0.96, 0.53])
    wafer.render(ax=ax3, print_width_in=6.0, aspect=0.55, zoom=1.35,
                 azimuth=-32, elevation=40)
    ax3.set_title("(a) elliptical etch + fill with the major axis at 0, 30, "
                  "60, 90 and $-$45$^\\circ$ (solid backend)",
                  fontsize=8.3, color=C_SLATE, weight="bold", loc="left")
    axs = fig.add_axes([0.06, 0.03, 0.9, 0.30])
    wafer.render(ax=axs, view="section", y=ROW_Y,
                 labels=["Si", "oxide", "fill 30 deg"])
    axs.set_title("(b) section along the row: each chord follows the rotation",
                  fontsize=8.3, color=C_SLATE, weight="bold", loc="left")
    fig.text(0.5, 0.995, "Ellipse(center, (a, b), rotation=deg): the same "
             "shape object drives etch, fill and section",
             fontsize=7.4, color=C_GREY, ha="center", va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "rotated_ellipses"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
