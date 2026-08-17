"""fig_wafer_notch.py -- bare circular wafers with a V-notch and a major flat.

``Wafer(size=300*mm, shape="circle", notch="V")`` and ``notch="flat"``: the
orientation feature is Boolean-cut from the substrate itself. Nothing is
deposited here, so the two panels show the starting point of every flow in
this document. ``notch_angle`` positions the feature (default 270 degrees,
the -y edge) and ``notch_depth`` / ``flat_length`` set its size (defaults
exaggerated for legibility: 3.5 % and 32.5 % of the diameter).

The substrate thickness is exaggerated as well. A 775 um wafer is invisibly
thin beside a 300 mm diameter, so the disc is drawn thicker to give the edge
and the notch a visible face.

Outputs: ../docs/figures/wafer_notch.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Wafer, mm
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

THICKNESS = 9 * mm          # exaggerated: a real 300 mm wafer is 775 um


def build(kind):
    """A bare Si wafer carrying only its orientation feature."""
    return Wafer(size=300 * mm, shape="circle", substrate="Si",
                 thickness=THICKNESS, notch=kind, notch_angle=270, name="Si")


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.1))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02,
                        wspace=0.04)
    for ax, kind, title in ((axes[0], "V", '(a) notch="V"'),
                            (axes[1], "flat", '(b) notch="flat"')):
        build(kind).render(ax=ax, print_width_in=3.1, aspect=0.9, zoom=1.05,
                           azimuth=-32, elevation=30, labels=False)
        ax.set_title(title, fontsize=8.3, color=C_SLATE, weight="bold",
                     loc="left", pad=3)
    fig.text(0.5, 0.965, "300 mm wafers with an orientation feature cut "
             "from the substrate",
             fontsize=7.4, color=C_GREY, ha="center", va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "wafer_notch"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
