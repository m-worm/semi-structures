"""fig_film_stress_bow.py -- film stress bows the wafer: single film and stack.

A flat wafer with one film for reference, then the wafer bowed by film
stress: a compressive film bows the pair into a dome, a tensile film into a
bowl, and a tall multilayer (an ON stack, as in 3D NAND) magnifies the
effect. Drawn with ``Scene.box(..., bow=(sx, sy))``: every slab takes the
same parabolic displacement, so films stay conformal to the wafer. Bows are
exaggerated for legibility. Wafer Si, film Si3N4, stack SiO2/Si3N4 -- the
palette, not role colors. The composition follows a common film-stress
figure; the geometry is the package's own.

Outputs: ../docs/figures/film_stress_bow.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.solid import Scene
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

SIZE = (10.0, 7.0)          # slab footprint (model units)
WAFER_T, FILM_T = 1.2, 0.5
STACK = [("SiO2", 0.28), ("Si3N4", 0.28)]
BOW = 0.9                    # edge-to-centre sagitta of the exaggerated bow
CAM = dict(zoom=1.25, azimuth=-30.0, elevation=22.0)


def sample(bow, stack=False, labels=False):
    s = Scene()
    s.box((0, 0, 0), (SIZE[0], SIZE[1], WAFER_T), "Si", bow=bow)
    if stack:
        s.multilayer((0, 0, WAFER_T), SIZE, STACK, repeats=3, bow=bow)
    else:
        s.box((0, 0, WAFER_T), (SIZE[0], SIZE[1], FILM_T), "Si3N4", bow=bow)
    if labels:
        # this camera looks from +x, +y: the near faces are x = SIZE[0]
        # (bottom-left on screen) and y = SIZE[1] (right)
        s.label("film", anchor=(4.0, 3.5, WAFER_T + FILM_T),
                via=(0.16, 0.20), position=(0.04, 0.20), size=8.2,
                marker="dot")
        s.label("wafer", anchor=(SIZE[0], 3.0, 0.5 * WAFER_T),
                via=(0.16, 0.86), position=(0.04, 0.86), size=8.2,
                marker="dot")
    return s


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(6.3, 3.6))
    grid = fig.add_gridspec(2, 3, width_ratios=(1.15, 1, 1), left=0.01,
                            right=0.99, top=0.90, bottom=0.02, wspace=0.04,
                            hspace=0.12)
    panel_w = 6.3 / 3.1
    ax0 = fig.add_subplot(grid[:, 0])
    ax0.imshow(sample(None, labels=True).render_array(
        print_width_in=panel_w, aspect=1.0, zoom=1.0, azimuth=CAM["azimuth"],
        elevation=CAM["elevation"]))
    ax0.set_axis_off()
    ax0.set_title("wafer + film, no stress", fontsize=8.3, color=C_SLATE,
                  weight="bold", loc="left", pad=3)

    cells = [((0, 1), +BOW, False, "compressive film"),
             ((1, 1), -BOW, False, "tensile film"),
             ((0, 2), +BOW, True, "compressive stack"),
             ((1, 2), -BOW, True, "tensile stack")]
    for (r, c), bow, stack, title in cells:
        ax = fig.add_subplot(grid[r, c])
        ax.imshow(sample((bow, 0.6 * bow), stack).render_array(
            print_width_in=panel_w, aspect=0.75, **CAM))
        ax.set_axis_off()
        ax.set_title(title, fontsize=8.3, color=C_SLATE, weight="bold",
                     loc="left", pad=3)

    fig.text(0.5, 0.975, "Film stress bows the wafer: compressive films dome "
             "it, tensile films bowl it; a tall stack magnifies the bow "
             "(exaggerated)", fontsize=7.4, color=C_GREY, ha="center",
             va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "film_stress_bow"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
